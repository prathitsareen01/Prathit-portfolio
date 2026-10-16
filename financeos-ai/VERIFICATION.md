# Verification record

Verified on October 16, 2026, on macOS with Python 3.14. The deliverable is a local single-user app, not a hosted service.

## Automated checks
- **37 tests passed** using isolated temporary SQLite databases.
- Browser JavaScript syntax check passed with Node.js 24.
- Synthetic CSV and XLSX both import as 126 accepted source rows.
- EBITDA and variance arithmetic checked against independently specified expected values.
- Invalid file imports are atomic; no partial datasets are saved.
- Evidence IDs are constrained to the requested dataset/scope.
- Saved investigations/scenarios round-trip through SQL.
- Forecast zero-driver base case, downside impact, backtesting, insufficient history, gaps and coverage checks pass.
- HTML/XLSX/CSV report generation passes, including workbook sheet/source-row counts, HTML escaping and report attachment scope checks.
- SQL filter injection and unexpected Host / cross-origin write attempts are rejected or safely parameterized.

The installed Starlette test adapter emits one deprecation warning about its current `httpx` compatibility layer. It does not cause a test failure. The tested environment is captured in `requirements.lock.txt`.

## Real browser workflow
Started Uvicorn on loopback and opened the dashboard in the Codex browser. Verified:
1. Populated KPIs, trend chart, account contributions and department filters.
2. Investigation execution with evidence references, a four-step tool trace and explicit cause limitations.
3. Evidence dialog showing linked record IDs, original file row numbers and amounts.
4. Downside scenario execution, baseline source rows, six forecast months and six historical holdout observations.
5. Report inclusion of a saved investigation/scenario and a successful Excel evidence-pack browser download.
6. Dirty CSV validation: two row errors, exact duplicate warning and disabled save.
7. Valid synthetic XLSX: 126 rows accepted, explicit save, new dataset version and retained prior dataset.
8. Final dashboard rendering after browser code fixes. Screenshot saved as `dashboard-preview.png`.

A JavaScript syntax error found during browser testing was corrected; the final file passes the syntax check. The final build also distinguishes an absent monthly scenario from an observed zero in chart rendering.

## Reproducible financial outputs
January–September synthetic EBITDA is $1,484,355.91 versus $1,742,976.00 budget, a $258,620.09 unfavorable gap. The downside scenario in DEMO.md produces $216,899.58 six-month EBITDA versus $670,689.66 base case. Revenue baseline backtest MAE is $29,540.35 over six holdout months.

Sample reports were generated from the same synthetic dataset and methods as the app. Their HTML, Excel and CSV are included in `sample-reports/`.

## Verification limits
- No live OpenAI request was made without a user-provided API key/model. Request structure, allowlisted model output, invalid output and provider failures were tested with mocks. Default offline automation was exercised end to end.
- Browser QA used the available desktop viewport. Responsive styling is included; a comprehensive device/browser matrix was not run.
- Python 3.14/macOS was exercised. Other Python 3.11+ installations are documented but were not independently tested.
- HTML reports and Excel workbooks were generated and structurally inspected. Native Excel rendering and browser print-to-PDF pagination were not tested.
- No multi-user, production load, external penetration or formal accounting certification testing was performed.

To repeat the checks, follow README.md and run `python -m pytest -q` at the project root.

## Hosted-demo update
Added mandatory Basic authentication in hosted mode, exact domain allowlisting, same-origin HTTPS write checks, a request-length guard, no-store responses, a synthetic shared-workspace notice and a Render free-plan deployment blueprint. Three additional automated tests verify auth protection, the hosted analysis workflow and fail-closed startup. Deployment status is not implied by passing these local tests.

## Browser sign-in repair
Replaced the browser-level Basic authentication popup with a regular HTML sign-in form and signed, expiring HTTPS cookies. Kept the password and domain boundary, added a sign-out action and login attempt throttling, and tested cookie-authenticated investigation, forecasting and report export. Five new tests cover sign-in page behavior, cookie workflows, CSRF restrictions, session tampering/expiry/password rotation and login rate limits. Local verification: 37 tests pass. Direct hosted browser inspection remains blocked by the browser environment policy; a Render live deployment alone does not prove that the user's browser can reach it.
