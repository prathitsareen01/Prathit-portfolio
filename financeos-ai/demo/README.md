# Synthetic demonstration data
Northstar Cloud is fictional. All figures are generated with a fixed random seed (42), in USD, January–September 2026. The demo contains 126 monthly account/scenario rows across four departments and seven accounts.

Late-period subscription revenue is below its synthetic budget, cloud infrastructure expense is above budget, and September marketing expense is above budget. These are deliberately injected numerical patterns, not evidence of real pricing, customer, vendor or campaign events. The app never promotes these patterns to verified business causes.

Run `python demo/generate_demo.py` from the project root to recreate CSV/XLSX. The dirty demo intentionally contains a duplicate and invalid rows to show the validation gate. The small CSV template contains one complete month. Forecasting needs at least three months.
