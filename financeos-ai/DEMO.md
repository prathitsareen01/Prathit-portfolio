# Five-minute hiring-manager demonstration

## Before the meeting
- Run the app locally using README.md. Keep the full project folder and the sample reports available.
- In Data studio, use **Load a fresh synthetic demo** if the current dataset is a user upload. It creates a new version and preserves history.
- Use January–September 2026 and All departments. Everything shown is fictional Northstar Cloud data.
- Leave the optional model checkbox off unless you have configured and independently tested an OpenAI model. The offline evidence workflow is complete and requires no network access.

## 0:00–0:45 — Lead with the finance problem
“Month-end finance work is often a chain of manual data preparation, variance analysis, investigation and reporting. FinanceOS connects that workflow while keeping the calculations auditable.”

Show Overview. State that this is synthetic data. Across January–September:

| Metric | Actual | Budget | Actual minus budget |
|---|---:|---:|---:|
| Revenue | $7,716,331.73 | $7,882,560.00 | −$166,228.27 |
| Gross profit | $4,649,961.78 | $4,876,416.00 | −$226,454.22 |
| Operating expenses | $3,165,605.87 | $3,133,440.00 | +$32,165.87 |
| EBITDA | $1,484,355.91 | $1,742,976.00 | −$258,620.09 |

“The EBITDA gap is larger than the revenue gap, so I would investigate both revenue and the cost base.” Change the chart metric to EBITDA.

## 0:45–1:30 — Narrow the investigation
Set FROM and THROUGH to September 2026. Filters apply automatically; the button can reapply them.

September EBITDA is **$90,856.33** versus **$209,328.00** budget, a **$118,471.67 unfavorable** variance. Revenue is $63,444.31 below budget, and operating expenses are $32,162.25 above budget.

Show What moved EBITDA and the account table. Click an account to inspect actual and budget source rows. Explain why expense increases reduce EBITDA even though their raw dollar variance is positive.

## 1:30–2:30 — Demonstrate the evidence boundary
Open Investigation agent, ask **“What contributed to the EBITDA budget gap?”**, then run the investigation.

“The workflow selects the filtered dataset, checks actual/budget coverage, calculates variances and ranks contributors. Each finding has an evidence reference linked to the original input row.”

Open E1 source evidence. Show dataset ID, record IDs, input row numbers and amounts. Reconcile actual minus budget.

“This tells me which accounts explain the arithmetic gap. It does not prove churn, vendor price inflation or campaign overspend. The app explicitly asks for operational evidence before attributing a cause.”

Ask **“What is the stock price?”** to show unsupported-question handling. Then rerun the EBITDA question if you want it attached to a report.

## 2:30–3:30 — Explore an explicit downside
Set FROM back to January, THROUGH September, All departments. This clears previously scoped analysis. Open Forecast & scenarios and click **Downside preset**:

- Monthly revenue growth: −1%.
- One-time revenue shift: −5%.
- COGS / revenue: +2 percentage points.
- Fixed operating expenses: +5%.
- Horizon: six months, October 2026–March 2027.

Expected six-month EBITDA: **$216,899.58** versus the flat base case of **$670,689.66**. The incremental downside is **$453,790.08**. Explain the assumptions rather than calling the result a certain prediction.

Show the historical baseline revenue backtest: six holdout months, **$29,540.35 monthly revenue MAE**. It tests the trailing mean rule, not the user-selected downside scenario. Inspect baseline source rows to show that the latest three actual months drive the model.

## 3:30–4:15 — Demonstrate clean ingestion
Open Data studio. Select `demo/dirty_upload_demo.csv` and validate. Show the two invalid rows, exact duplicate warning and disabled save button. The invalid file creates no dataset.

Then select `demo/northstar_synthetic.xlsx`, validate and inspect the cleaned preview. Save if time permits. Show the newly created dataset version, SHA-256, input totals and SQL-backed source ledger. Original datasets remain in the selector.

## 4:15–5:00 — Deliver the management pack
Return to a clearly labeled synthetic demo. Set the desired scope, rerun its investigation and scenario, then open Management reports.

Download the HTML management report and Excel evidence pack. Open the HTML file in a browser and use Print → Save as PDF if needed. Show the Excel summary, source ledger, evidence mapping, scenario and assumptions tabs.

“I built the financial logic and the data lineage into the workflow, so the report can be checked rather than simply trusted.”

## Questions to prepare for
**Where is the AI?** Offline mode is explicit automation. Optional model mode uses structured output only to choose an approved analysis intent. Financial numbers and displayed findings come from local code. The LLM cannot execute arbitrary SQL or invent commentary.

**What is the business value?** Fewer manual handoffs between file validation, variance calculations, drilldown and reporting. Do not claim a measured time saving without running a comparative study.

**Why SQLite?** Simple, durable local storage with no cloud setup. A multi-user production deployment would need authentication, role-based access, retention controls and a managed storage/deployment plan.

**What does it not do?** It does not establish operational causes, ingest arbitrary ERP formats, reconcile a balance sheet, forecast cash flow or provide investment recommendations. Forecasts are transparent driver scenarios.

**What would you build next?** ERP adapters with explicit account mapping, invoice/payroll drilldown, reviewer-approved cause annotations, chart-of-accounts completeness checks and stronger forecast methods benchmarked against this simple baseline.

## Portfolio description
Built FinanceOS AI, a local FP&A application that validates CSV/Excel financial data, stores versioned records in SQL, calculates budget variances, traces findings to source evidence, models driver scenarios, and exports management reports. Designed a constrained optional AI planner so financial statements remain reproducible and unsupported causes remain explicit.
