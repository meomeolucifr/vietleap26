# Rate Cut Lab: simulating lending-rate cuts

VietLeap Hackathon 2026, From Data to Decision · Team 1 · [Bản tiếng Việt](README_VI.md)

**Live dashboard:** https://meomeolucifr.github.io/vietleap26/ (add `#en` for English, `#vi` for Vietnamese)

The dashboard helps a bank's ALCO and CFO decide how far to cut lending rates. For a cut of s basis points (10 bp = 0.1%) it shows how much borrowers save, and whether profit after tax, the capital adequacy ratio (CAR) and provision coverage stay within safe limits. Sample: 25 listed Vietnamese commercial banks, consolidated annual financial statements 2016–2025 (FiinPro-X), with macro data from FiinX.

- Method, models, variables and data sources: [docs/METHODOLOGY.md](docs/METHODOLOGY.md)
- Submission document (Word, Track Changes on): [docs/Team1_Documentation.docx](docs/Team1_Documentation.docx) ([Vietnamese version](docs/Team1_Documentation_VI.docx))
- AI prompts used: [prompts/PROMPTS.md](prompts/PROMPTS.md)

## Repository layout

```
Data/                    FiinPro-X financial statement exports, one file per bank
Data/sample/banks.csv    Study sample: 25 banks, exchange, reasons for excluding others
Data/macro/macro_vn.csv  Annual macro data 2015–2025 from FiinX (GDP, average CPI, deposit rate, credit growth), %
scripts/
  build_dataset.py       Reads Data/*.xlsx into a bank × year panel; --xlsx writes the Excel panel with formulas
  export_dashboard_data.py  -> dashboard/data.js   (base figures in VND bn, repricing table)
  analysis.py            Builds the panel variables used by econometrics.py; -> dashboard/analysis.js (not shown)
  econometrics.py        -> dashboard/econ.js and dashboard/panel.js (panel FE regressions, listed in MODELS)
  run_pipeline.py        Runs all steps, then checks accounting identities
  test_regress.js        Checks that dashboard/regress.js (in-browser regressions) matches Python: node scripts/test_regress.js
  validate_dataset.py    Compares the merged panel with the template file (local only)
dashboard/               Static site (index.html, regress.js and generated .js data files). This is what gets deployed
Output/                  Excel panel with formulas
docs/                    Methodology and submission documents
prompts/                 AI prompts
.github/workflows/       Re-runs the pipeline and deploys to GitHub Pages on every push to main
```

## Run locally

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py            # regenerate dashboard/*.js and run the data checks
node scripts/test_regress.js              # in-browser regressions must match Python
python -m http.server 8000 -d dashboard   # open http://localhost:8000
```

Opening `dashboard/index.html` directly in a browser also works.

## Adding or changing a regression model

Edit the `MODELS` list at the top of [scripts/econometrics.py](scripts/econometrics.py): dependent variable, regressors, bank/year fixed effects, standard-error type, and the auto-generated takeaway. Re-run `python scripts/econometrics.py`; results go to `dashboard/econ.js`, and the dashboard's "Run your own regression" panel picks up the new model. Available variables are built in `panel()` in [scripts/analysis.py](scripts/analysis.py).

Macro scenarios (Favourable / Base / Adverse) are defined in `SCENARIOS` in the same file: each is the macro change between two actual years, passed through the `llp_macro` model to a change in the provision rate, which the simulator then applies.

Note: macro variables (GDP, CPI…) are identical across banks in a year, so year fixed effects absorb them. Models with macro variables must set `time=False` and should use `cov='kernel'` (Driscoll-Kraay).

## Deployment

On every push to `main`, GitHub Actions installs the packages, runs `run_pipeline.py` (stops if a data check fails), checks the in-browser regressions against Python, and publishes `dashboard/` to https://meomeolucifr.github.io/vietleap26/. Add or update data and push: the regressions and the dashboard update automatically.
