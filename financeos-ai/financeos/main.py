import io
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import analysis, agent, data, reports, hosting


@asynccontextmanager
async def lifespan(app):
    hosting.validate_startup()
    data.init_db()
    if not data.datasets():
        demo=data.ROOT/'demo'/'northstar_synthetic.csv'
        data.save_dataset(demo.read_bytes(),demo.name,synthetic=True)
    yield


app=FastAPI(title='FinanceOS AI',version='1.0.0',lifespan=lifespan)
STATIC=Path(__file__).parent/'static'
app.mount('/static',StaticFiles(directory=STATIC),name='static')


@app.exception_handler(ValueError)
async def value_error(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=400,content={'detail':str(exc)})


@app.middleware('http')
async def security_headers(request, call_next):
    # Exact host allowlist; hosted mode adds authentication to all app/data routes.
    host=hosting.request_host(request.headers.get('host',''))
    if host not in hosting.allowed_hosts():
        return Response('Host is not allowed',status_code=403)
    if hosting.hosted() and request.url.path!='/api/health':
        if not hosting.authorized(request.headers.get('authorization','')):
            return Response('Sign in to the FinanceOS portfolio demo',status_code=401,
                            headers={'WWW-Authenticate':'Basic realm="FinanceOS portfolio demo", charset="UTF-8"',
                                     'Cache-Control':'no-store'})
    origin=request.headers.get('origin')
    expected_origin='https://' if hosting.hosted() else 'http://'
    if request.method in ('POST','PUT','DELETE','PATCH') and origin and origin!=expected_origin+request.headers.get('host',''):
        return Response('Cross-origin writes are disabled',status_code=403)
    length=request.headers.get('content-length')
    if length:
        try:
            if int(length)>11*1024*1024 or int(length)<0:
                return Response('Request exceeds the upload limit',status_code=413)
        except ValueError:
            return Response('Invalid request length',status_code=400)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Cache-Control']='no-store'
    if hosting.hosted():
        response.headers['Strict-Transport-Security']='max-age=31536000'
    return response


@app.get('/')
def index(): return FileResponse(STATIC/'index.html')


@app.get('/api/health')
def health(): return {'status':'ok'}


@app.get('/api/config')
def app_config():
    return {'model_configured':bool(os.environ.get('OPENAI_API_KEY') and os.environ.get('OPENAI_MODEL')),
            'hosted':hosting.hosted(),
            'ephemeral':os.environ.get('FINANCEOS_EPHEMERAL','false').lower()=='true'}


@app.get('/api/datasets')
def list_datasets(): return data.datasets()


@app.post('/api/demo')
def load_demo():
    path=data.ROOT/'demo'/'northstar_synthetic.csv'
    dataset_id,validation=data.save_dataset(path.read_bytes(),path.name,True)
    return {'id':dataset_id,'validation':validation}


@app.get('/api/template')
def template(format:Literal['csv','xlsx']='csv'):
    if format=='csv':
        return Response((data.ROOT/'demo'/'upload_template.csv').read_bytes(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="upload_template.csv"'})
    return FileResponse(data.ROOT/'demo'/'northstar_synthetic.xlsx',filename='northstar_synthetic.xlsx')


@app.post('/api/upload')
async def upload(file:UploadFile=File(...), preview:bool=True):
    raw=await file.read(10*1024*1024+1)
    try:
        if preview:
            rows,validation=data.parse_file(raw,file.filename or '')
            return {'validation':validation,'preview':rows[:20]}
        dataset_id,validation=data.save_dataset(raw,file.filename or '')
        if not dataset_id:
            return {'id':None,'validation':validation}
        return {'id':dataset_id,'validation':validation}
    except (ValueError,KeyError) as exc:
        raise ValueError(str(exc)) from exc
    except Exception as exc:
        raise ValueError('Could not parse the file. Check UTF-8 CSV or a valid, unencrypted XLSX first worksheet.') from exc


class Scope(BaseModel):
    start:str|None=None
    end:str|None=None
    department:str|None=None


@app.get('/api/datasets/{dataset_id}/summary')
def get_summary(dataset_id:str,start:str|None=None,end:str|None=None,department:str|None=None):
    return analysis.summary(dataset_id,start,end,department)


@app.get('/api/datasets/{dataset_id}/records')
def get_records(dataset_id:str,start:str|None=None,end:str|None=None,department:str|None=None):
    return data.records(dataset_id,start,end,department)


class InvestigationRequest(Scope):
    question:str=Field(min_length=3,max_length=1000)
    use_model:bool=False


@app.post('/api/datasets/{dataset_id}/investigate')
def investigate(dataset_id:str,request:InvestigationRequest):
    intent,mode,notice=agent.plan(request.question,request.use_model)
    if intent=='unsupported':
        return {'unsupported':True,'mode':mode,'notice':notice,'headline':'I can investigate monthly revenue, COGS, operating expense, EBITDA and department variances. This ledger cannot answer that question reliably.','evidence':[],'claims':[],'unknowns':['Try “What contributed to the EBITDA budget gap?” Filters above define the investigation scope.'],'trace':[]}
    scope=request.model_dump(include={'start','end','department'})
    return analysis.investigate(dataset_id,request.question,scope,intent,mode,notice)


class ForecastRequest(Scope):
    growth:float=Field(default=0,ge=-20,le=20,allow_inf_nan=False)
    revenue_shock:float=Field(default=0,ge=-50,le=50,allow_inf_nan=False)
    cogs_shift:float=Field(default=0,ge=-20,le=20,allow_inf_nan=False)
    opex_shift:float=Field(default=0,ge=-50,le=50,allow_inf_nan=False)
    horizon:int=Field(default=6,ge=1,le=24)


@app.post('/api/datasets/{dataset_id}/forecast')
def forecast(dataset_id:str,request:ForecastRequest):
    scope=request.model_dump(include={'start','end','department'})
    return analysis.forecast(dataset_id,scope,**request.model_dump(exclude={'start','end','department'}))


@app.get('/api/datasets/{dataset_id}/history')
def history(dataset_id:str):
    data.metadata(dataset_id)
    result={}
    with data.connection() as db:
        for table in ('investigations','scenarios'):
            result[table]=[{'id':r['id'],'created':r['created']} for r in db.execute(f'SELECT id,created FROM {table} WHERE dataset_id=? ORDER BY created DESC LIMIT 20',(dataset_id,))]
    return result


@app.get('/api/results/{kind}/{result_id}')
def result(kind:Literal['investigations','scenarios'],result_id:str):
    return data.saved_result(kind,result_id)


@app.get('/api/datasets/{dataset_id}/report')
def report(dataset_id:str,format:Literal['html','xlsx','csv']='html',start:str|None=None,end:str|None=None,department:str|None=None,investigation_id:str|None=None,scenario_id:str|None=None):
    s=analysis.summary(dataset_id,start,end,department)
    investigation=data.saved_result('investigations',investigation_id) if investigation_id else None
    scenario=data.saved_result('scenarios',scenario_id) if scenario_id else None
    for attached in (investigation,scenario):
        if attached and (attached['dataset_id']!=dataset_id or attached['scope']!=s['scope']):
            raise ValueError('Saved analysis scope does not match this report. Run it again for the current filters.')
    if format=='xlsx':
        content=reports.workbook(s,investigation,scenario)
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif format=='csv': content,mime=reports.csv_export(s),'text/csv'
    else: content,mime=reports.html_report(s,investigation,scenario),'text/html'
    return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="FinanceOS-management-{dataset_id}.{format}"'})
