# FinanceOS AI
**Financial clarity, with evidence.** A working local FP&A portfolio application, built with Python/FastAPI, SQLite and an offline vanilla JavaScript dashboard. No frontend build, cloud database or API key is needed for the demo.

## Start on your Mac
Requires Python **3.11+** (tested with Python 3.14), a terminal, and internet access for the initial package installation.

1. Unzip the project. Open its `FinanceOS-AI` folder in VS Code (**File → Open Folder**).
2. Open **Terminal → New Terminal** in VS Code. Run from the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn financeos.main:app --host 127.0.0.1 --port 8000
```

3. Open **http://127.0.0.1:8000** in your browser. Synthetic data loads automatically on the first run.
4. Stop with **Control+C**. Restart with the last command. Your uploaded datasets and saved analysis remain in `data/financeos.db`.

In VS Code, run **Python: Select Interpreter** and choose `.venv/bin/python`. The included launch configuration starts the app with F5 after installing the Microsoft Python and Python Debugger extensions. Alternatively, `./run.sh` starts an already configured environment.

If `python3` is unavailable, install Python from https://www.python.org/downloads/macos/ and restart the terminal. If port 8000 is in use, change `--port 8000` to `--port 8001` and use that URL. An import error usually means the virtual environment is inactive or the terminal is outside the project root.

## What works
- CSV and XLSX ingestion, validation preview, explicit save, immutable dataset versions and source file SHA-256 hashes.
- Whitespace/casing/amount normalization, exact duplicate removal, conflicting duplicate rejection, account mapping checks, currency checks, month checks, formula rejection, signed corrections and coverage warnings.
- Interactive scope filters, revenue/EBITDA/expense charts, favorability-aware variance tables, department drilldown and source evidence dialogs.
- Investigation workflow with a tool execution trace, evidence references, source record IDs, reproducible calculations, unsupported-question handling and persisted results.
- Driver-based forecasts with a baseline, scenario controls, historical rolling backtest and source-linked assumptions; saved scenarios can be restored.
- Management report (standalone HTML, printable to PDF), formatted Excel evidence workbook, and variance CSV downloads.
- SQLite stores financial rows, dataset metadata/validation, investigations and scenarios. API docs: http://127.0.0.1:8000/docs.

## The AI boundary
The default investigation mode is **offline rule-based automation**, clearly labeled in the UI. It is a deterministic investigation workflow, not a pretend language model. It chooses a supported analysis, selects source data, checks pair coverage, calculates variances, ranks contributors, and returns evidence-backed statements.

Optional **OpenAI model planning** is implemented through the Responses API with a strict JSON schema. Configure on the server before starting:

```sh
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="your-supported-responses-model-id"
```

Select an available model in your OpenAI project that supports structured outputs. The app deliberately does not hardcode a model. Enable **Use optional OpenAI tool planner** in Investigation. Only the question is sent to OpenAI; dataset rows, balances and filenames are not sent. Anything you type in the question is sent, so use synthetic questions during a portfolio demo. API usage may incur provider charges. Keys remain in the server environment; do not place them in source files.

The model only chooses among six allowlisted analysis intents. It cannot write SQL, change financial data, or author displayed financial statements. Invalid output or a provider error falls back to the disclosed local planner. The UI filters, not dates or departments inferred from prose, define scope. An unsupported question receives an explicit limitation.

**No fabricated causes:** an unfavorable revenue variance is evidence of a numerical shortfall, not proof of churn, price discounting or lost customers. Every investigation labels arithmetic contributors and lists the missing operational evidence required to verify a cause. The headline is calculated from the selected P&L, and its account findings link to stored source rows.

Live OpenAI calls were not exercised without a user-provided key. Routing, structured request construction, schema allowlisting and provider-failure fallback are tested with mocked provider responses.

Implementation references: [FastAPI uploads](https://fastapi.tiangolo.com/tutorial/request-files/) and [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Upload format
The first row must contain headers. XLSX uses its **first worksheet**. CSV uses UTF-8. Required columns:

| Column | Contract | Example |
|---|---|---|
| period | YYYY-MM, 2000–2099 | 2026-09 |
| department | Plain label, up to 100 characters | Commercial |
| account | Consistent category across the entire dataset | Subscription revenue |
| category | revenue / cogs / opex | revenue |
| scenario | actual / budget | actual |
| amount | USD, up to 2 decimal places | 734552.12 |
| currency | Optional; defaults to USD; other currencies rejected | USD |

Aliases `month`/`date` → `period`, `dept` → `department`, `type` → `scenario`, `value` → `amount` are supported. Excel date objects normalize to their month; date strings must use YYYY-MM. Extra columns are ignored. Budget and actual are in a single table. Merge separate source files into this contract before uploading. This is a monthly P&L input, not a universal financial-statement parser or raw transaction reconciliation system.

Revenue, COGS and operating expenses normally use positive amounts. Negative entries are retained and flagged as signed corrections. `$1,234.50` and `(123.45)` amounts are accepted. Numeric amounts are stored as **integer cents**. Formula cells are rejected rather than trusting cached values. Mixed currencies are rejected; no exchange rates are assumed.

Unique grain: `period + department + account + scenario`. Exact financial duplicates are removed with a warning. Conflicting rows block the entire import; pre-aggregate transaction-level data to the monthly grain. An upload with any error writes no dataset. Source row numbers retain the original input row positions.

The app checks pair coverage for every month/department/account in the union of actual and budget data. It cannot detect an account omitted from **both** scenarios without an external chart of accounts. Missing pairs produce unavailable variances; no silent zero budgets. Zero budget means a dollar variance but no percentage variance. Use Data studio to inspect validation and reconciliation totals. Source totals sum revenue and expense lines; they are not profit.

Limits: 10 MB compressed input, 50 MB expanded XLSX, 50,000 input rows, one currency (USD). Designed for small local portfolio datasets.

## Financial methodology
- Gross profit = revenue − COGS.
- EBITDA = revenue − COGS − operating expenses. Excludes depreciation, amortization, interest and tax; classify your input accordingly. No balance sheet/cash flow model.
- Dollar variance = actual − budget.
- Percentage variance = (actual − budget) / abs(budget) × 100; unavailable for zero budget.
- EBITDA contribution = revenue variance, or negative expense variance.
- Expense decreases are favorable; revenue/profit increases are favorable. Missing pair coverage suppresses overall KPI variances; matched groups remain inspectable.

### Forecast mechanics
Uses the latest three actual months **within the selected filters**. The entire selected actual history must be consecutive with consistent account/department coverage. Budget coverage is not needed for the forecast. At least three actual months and positive trailing revenue are required.

Baseline revenue = three-month mean. Baseline COGS ratio = sum(COGS) / sum(revenue) over those months. Baseline opex = three-month mean. Base case holds those assumptions constant.

For month `t`, scenario revenue = baseline revenue × (1 + one-time shift) × (1 + monthly growth)^t. COGS = scenario revenue × (baseline COGS ratio + percentage-point change). Opex = baseline opex × (1 + expense shift). The adjusted COGS ratio must be 0–100%. Amounts are rounded for display/export.

Backtest is a rolling one-step revenue prediction from each preceding three-month mean, with no look-ahead. Reports include the number of holdout observations and mean absolute error (MAE). This evaluates the baseline revenue rule only, not the user-selected scenario or EBITDA prediction. No probabilistic confidence bounds, seasonality, causal model or guarantee is claimed.

## Demo and presentation
See **DEMO.md** for the five-minute hiring-manager script, expected results and questions to prepare for. All Northstar Cloud records are synthetic, clearly labeled, and reproducible from `demo/generate_demo.py`. `demo/dirty_upload_demo.csv` intentionally fails validation. The included one-month template is for upload practice; use the nine-month XLSX to demonstrate forecasting.

Reports follow the current scope. Changing filters clears attached analysis in the UI. The server also rejects report attachments whose dataset or scope does not match. Saved histories restore their own scope before displaying evidence. Downloads contain the source evidence appendix/index and dataset identity, so findings can be independently checked.

## Tests
From the activated environment at the project root:

```sh
python -m pytest -q
```

Tests use isolated temporary databases; they do not alter your local portfolio datasets. Coverage includes cent arithmetic, signed corrections, zero budgets, cleaning/deduplication, atomic invalid imports, CSV/XLSX, formula cells, incomplete coverage, filtering, SQL injection attempts, evidence IDs, unsupported requests, provider mocks/fallback, forecasting/backtests, report integrity and source escaping, persistence, and local origin/host controls. If Node.js is installed, check browser code syntax with `node --check financeos/static/app.js`.

`requirements.txt` pins direct packages used for this build. `requirements.lock.txt` captures the full tested Python 3.14 environment; use it when recreating that exact environment. For other supported Python versions, start with the direct requirements. See **VERIFICATION.md** for the checks actually performed and their limits.

## Architecture and operating limits
```
Local browser → FastAPI endpoints → validation / analysis / reports
                              ↘ SQLite (integer-cent ledger + run history)
Optional question → OpenAI intent planner → allowlisted analysis → local calculations
```

- `financeos/data.py`: input contract, SQL schema and immutable dataset versions.
- `financeos/analysis.py`: financial calculations, investigation evidence and forecast model.
- `financeos/agent.py`: offline routing and optional structured model planner.
- `financeos/reports.py`: safe standalone HTML, XLSX and CSV exports.
- `financeos/main.py`: local API, uploads, result history and report routes.
- `financeos/static/`: custom responsive dashboard; no external fonts, scripts or chart CDN.

The default mode is a **single-user, loopback-only portfolio application**. A separate **hosted shared-demo mode** now adds mandatory password authentication and an exact hostname allowlist. See DEPLOYMENT.md and render.yaml. It still has no per-user workspace isolation, role-based team access or encryption-at-rest layer. Host validation and cross-origin write checks protect the local demo boundary. Use hosted mode for the synthetic portfolio demo. A business production service would additionally need per-user authorization, durable deployment storage, monitoring and backups. Input workbooks are parsed locally; only normalized rows and their validation metadata/hash are persisted, not the original binary file. Keep original uploads separately if formal source retention is needed. SQLite is an audit trail for a portfolio demo, not a tamper-proof accounting ledger.

To use another database location, set `FINANCEOS_DB` to a local SQLite path before running. Retain the default database to keep dataset versions. Start with a new path to get a clean demo without deleting history.
