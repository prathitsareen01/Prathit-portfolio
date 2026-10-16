"""All reported financial statements are computed here, never by a language model."""
from collections import defaultdict
from statistics import mean
from . import data

SIGNS = {'revenue': 1, 'cogs': -1, 'opex': -1}


def aggregate(rows, field='account'):
    groups = defaultdict(list)
    for r in rows:
        groups[(r[field], r['category'] if field == 'account' else '')].append(r)
    result = []
    for (label, category), group in sorted(groups.items()):
        actual = sum(r['cents'] for r in group if r['scenario']=='actual')
        budget = sum(r['cents'] for r in group if r['scenario']=='budget')
        keys = defaultdict(set)
        for r in group:
            keys[(r['period'],r['department'],r['account'])].add(r['scenario'])
        complete = all(len(v)==2 for v in keys.values())
        delta = actual-budget if complete else None
        contribution = sum(SIGNS[r['category']]*r['cents']*(1 if r['scenario']=='actual' else -1) for r in group) if complete else None
        result.append({'label':label, 'category':category, 'actual':actual/100, 'budget':budget/100,
                       'variance':delta/100 if delta is not None else None,
                       'variance_pct':delta/abs(budget)*100 if complete and budget else None,
                       'ebitda_impact': contribution/100 if contribution is not None else None,
                       'favorable':contribution>=0 if contribution is not None else None,
                       'complete':complete, 'record_ids':[r['id'] for r in group]})
    return result


def summary(dataset_id, start=None, end=None, department=None):
    rows = data.records(dataset_id,start,end,department)
    if not rows:
        raise ValueError('No rows match these filters.')
    accounts = aggregate(rows)
    complete = all(r['complete'] for r in accounts)
    cents = {s:{c:sum(r['cents'] for r in rows if r['scenario']==s and r['category']==c) for c in SIGNS} for s in ('actual','budget')}
    for scenario in cents:
        cents[scenario]['gross_profit'] = cents[scenario]['revenue']-cents[scenario]['cogs']
        cents[scenario]['ebitda'] = cents[scenario]['gross_profit']-cents[scenario]['opex']
    totals = {s:{k:v/100 for k,v in amounts.items()} for s,amounts in cents.items()}
    for scenario in totals:
        totals[scenario]['margin'] = cents[scenario]['ebitda']/cents[scenario]['revenue']*100 if cents[scenario]['revenue'] else None
    kpis = []
    for name in ('revenue','gross_profit','opex','ebitda'):
        a,b = totals['actual'][name],totals['budget'][name]
        kpis.append({'name':name,'actual':a,'budget':b,'variance':(cents['actual'][name]-cents['budget'][name])/100 if complete else None,
                     'variance_pct':(cents['actual'][name]-cents['budget'][name])/abs(cents['budget'][name])*100 if complete and b else None,
                     'favorable':(a<=b if name=='opex' else a>=b) if complete else None})
    months=[]
    for period in sorted(set(r['period'] for r in rows)):
        subset=[r for r in rows if r['period']==period]
        months.append({'period':period, 'present':{s:any(r['scenario']==s for r in subset) for s in ('actual','budget')}, **{s: {c:sum(r['cents'] for r in subset if r['scenario']==s and r['category']==c)/100 for c in SIGNS} for s in ('actual','budget')}})
        for s in ('actual','budget'):
            months[-1][s]['ebitda']=sum(SIGNS[r['category']]*r['cents'] for r in subset if r['scenario']==s)/100
    return {'dataset':data.metadata(dataset_id), 'scope':{'start':start,'end':end,'department':department},
            'complete':complete,'row_count':len(rows),'kpis':kpis,'totals':totals,
            'accounts':accounts,'departments':aggregate(rows,'department'), 'months':months,
            'bridge':sorted([r for r in accounts if r['complete']],key=lambda x:x['ebitda_impact']),
            'methodology':'Amounts in USD. Revenue, COGS and operating expenses normally positive. EBITDA = revenue − COGS − operating expenses. Variance = actual − budget; expense favorability is inverted. Unpaired data has no variance. This model excludes depreciation, amortization, interest and tax.'}


def investigate(dataset_id, question, scope, intent='ebitda', mode='offline automation', notice=None):
    s=summary(dataset_id,**scope)
    candidates=s['accounts'] if intent!='department' else s['departments']
    if intent in ('revenue','cogs','opex'):
        candidates=[r for r in candidates if r['category']==intent]
    ranked=sorted([r for r in candidates if r['complete']],key=lambda x:abs(x['ebitda_impact']),reverse=True)[:5]
    evidence=[]
    for i,r in enumerate(ranked,1):
        evidence.append({'ref':f'E{i}',**r,'formula':'Actual − budget; multiply by +1 for revenue, −1 for expenses to get EBITDA impact.'})
    if not s['complete']:
        headline='Incomplete actual/budget coverage: an overall variance conclusion is unavailable.'
    else:
        metric=intent if intent in ('revenue','cogs','opex') else 'ebitda'
        a,b=s['totals']['actual'][metric],s['totals']['budget'][metric]
        k={'name':metric,'actual':a,'budget':b,'variance':round(a-b,2)}
        headline=f"{k['name'].replace('_',' ').upper()} is ${k['actual']:,.2f} against ${k['budget']:,.2f} budget; variance ${k['variance']:+,.2f}."
    claims=[f"[{e['ref']}] {e['label']}: actual ${e['actual']:,.2f}, budget ${e['budget']:,.2f}; EBITDA contribution ${e['ebitda_impact']:+,.2f}." for e in evidence]
    # Do not generate causal text from ledger labels or freeform model output.
    return data.store_result('investigations',dataset_id,{'dataset_id':dataset_id,'question':question,'intent':intent,'mode':mode,'notice':notice,
        'scope':scope,'headline':headline,'claims':claims,'evidence':evidence,
        'unknowns':['These are arithmetic contributors, not verified business causes.',
                    'Pricing, volume, headcount, vendor changes and timing cannot be established from this monthly ledger.',
                    'Request invoice, payroll or sales volume evidence and discuss with the accountable department owner before attributing causes.'],
        'trace':[{'tool':'select_scope','result':f"{s['row_count']} source rows; immutable dataset {dataset_id}"},
                 {'tool':'check_pair_coverage','result':'Complete' if s['complete'] else 'Incomplete; headline variance suppressed'},
                 {'tool':'calculate_variances','result':'Integer-cent arithmetic; actual minus budget'},
                 {'tool':'rank_contributors','result':f'{len(evidence)} evidence groups; source row IDs attached'}]})


def forecast(dataset_id, scope, growth=0.0, revenue_shock=0.0, cogs_shift=0.0, opex_shift=0.0, horizon=6):
    s=summary(dataset_id,**scope)
    # Only actual months; missing calendar months block time-series modeling.
    actual_rows=data.records(dataset_id,**scope)
    months=[m for m in s['months'] if any(r['period']==m['period'] and r['scenario']=='actual' for r in actual_rows)]
    if len(months)<3:
        raise ValueError('Forecasting requires at least three actual months in the selected scope.')
    for previous,current in zip(months,months[1:]):
        if next_month(previous['period'])!=current['period']:
            raise ValueError('Actual month history has gaps. Upload missing periods before forecasting.')
    # A changing account universe can look like growth: require consistent monthly coverage.
    universes=[{(r['department'],r['account']) for r in actual_rows if r['period']==m['period'] and r['scenario']=='actual'} for m in months]
    if any(u!=universes[0] for u in universes[1:]):
        raise ValueError('Actual account/department coverage changes by month. Align coverage before forecasting.')
    tail=months[-3:]
    rev=mean(m['actual']['revenue'] for m in tail)
    if rev<=0:
        raise ValueError('Forecast requires positive trailing revenue.')
    cogs_ratio=sum(m['actual']['cogs'] for m in tail)/sum(m['actual']['revenue'] for m in tail)
    if not 0<=cogs_ratio+cogs_shift/100<=1:
        raise ValueError('Adjusted COGS/revenue ratio must lie between 0% and 100%.')
    fixed=mean(m['actual']['opex'] for m in tail)
    points=[]
    period=months[-1]['period']
    for step in range(1,horizon+1):
        period=next_month(period)
        base_rev=rev
        scen_rev=rev*(1+revenue_shock/100)*(1+growth/100)**step
        base_cogs=base_rev*cogs_ratio
        scen_cogs=scen_rev*(cogs_ratio+cogs_shift/100)
        scen_opex=fixed*(1+opex_shift/100)
        points.append({'period':period,'base_revenue':round(base_rev,2),'revenue':round(scen_rev,2),
                       'cogs':round(scen_cogs,2),'opex':round(scen_opex,2),
                       'base_ebitda':round(base_rev-base_cogs-fixed,2),'ebitda':round(scen_rev-scen_cogs-scen_opex,2)})
    errors=[]
    for i in range(3,len(months)):
        predicted=mean(m['actual']['revenue'] for m in months[i-3:i])
        errors.append(abs(predicted-months[i]['actual']['revenue']))
    source_ids=[r['id'] for r in actual_rows if r['scenario']=='actual' and r['period'] in [m['period'] for m in tail]]
    return data.store_result('scenarios',dataset_id,{'dataset_id':dataset_id,'scope':scope,'horizon':horizon,'points':points,
        'assumptions':{'monthly_revenue_growth_pct':growth,'one_time_revenue_shift_pct':revenue_shock,'cogs_ratio_change_pp':cogs_shift,'fixed_opex_change_pct':opex_shift},
        'baseline':{'periods':[m['period'] for m in tail],'revenue':round(rev,2),'cogs_ratio_pct':round(cogs_ratio*100,4),'opex':round(fixed,2),'record_ids':source_ids},
        'backtest':{'method':'Rolling three-month revenue mean; each prediction uses only preceding actual months. No scenario assumptions in backtest.',
                    'observations':len(errors),'revenue_mae':round(mean(errors),2) if errors else None},
        'limitations':['Driver-based scenario, not a probability-weighted prediction. No statistical confidence interval.',
                       'Trailing three-month mean; COGS varies with revenue, operating expenses are fixed. No seasonality, cash flow, tax or balance sheet model.']})


def next_month(period):
    y,m=map(int,period.split('-'))
    return f'{y+1 if m==12 else y:04d}-{1 if m==12 else m+1:02d}'
