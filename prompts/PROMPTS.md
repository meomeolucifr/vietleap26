# AI prompts — Rate Cut Lab (Team 1)

[Bản tiếng Việt](PROMPTS_VI.md)

The prompts the team used with an AI assistant (Claude, through Claude Code in VS Code) to build the product, in the order of the work. The assistant could read and write the project folder, run Python and Node, use the FiinX MCP server and the GitHub CLI.

---

## 0. Shared context (sent at the start of the session)

```
Our team is competing in VietLeap Hackathon 2026 "From Data to Decision". Scoring: Product 40, Presentation 40,
Teamwork 20. We must submit: the product, a document with edit history (research problem, data and limitations,
results, record of AI use, division of work), open-source code, the AI prompts, and an English presentation with a
Vietnamese summary. Repo: https://github.com/w-nhannt/vietleap26 (code, data, product, documents, prompts).

Topic: simulate a bank cutting its lending rate by s basis points (10 bp = 0.1%) and show the effect on
(1) % change in profit after tax, (2) how much borrowers save, (3) provision coverage, (4) CAR.
The users are the bank's ALCO and CFO; follow Proposal_Giam_lai_suat_cho_vay_VCB.docx (25/50 bp scenarios,
keep 90% of profit after tax). The team chooses the topic and decides the conclusions; you help with data, code,
the dashboard and critical review.
```

---

## 1. Data

### 1.1 Merge financial statements into a panel

```
Data/ holds one FiinPro-X export per bank (sheets: balance sheet, income statement, notes, capital adequacy report;
unit VND bn). Merge them into one table in exactly the format of the template "Copy of DL_KLTN_...xlsx"
(sheet "DỮ LIỆU TỪ 2013 kltn"): one row per bank-year, columns as in the template, unit VND million. Handle
duplicate labels in FiinPro (match on label + occurrence), store expenses/provisions as positive numbers like the
template, skip Excel lock files (~$), and merge the two VBB files. Write scripts/build_dataset.py, output
Output/VietLeap26_Bank_Panel_with_ratios.xlsx, plus a script that checks overlapping rows against the template.
```

### 1.2 Ratios as Excel formulas

```
The ratio columns (log z, Z-Score, SIZE, ROA std. dev., ROA, ROE, CAP, CAR, CIR, LDR, 1-HHI, NPL, LIQ, LEV, NM, NIM)
must be Excel formulas computed from the data cells, not hard-coded numbers. Add columns for loans by debt group 1–5
(notes), reported CAR, regulatory capital and risk-weighted assets (capital adequacy report). CAR = regulatory capital
/ RWA: verify it matches reported CAR in the years that have it, then apply the formula to the empty cells. Add a
GIAI_THICH sheet documenting each formula.
```

### 1.3 Study sample

```
Use the FiinX MCP to list the banks in ICB sector 8355 with their exchanges. Choose a sample of 25 commercial banks
listed or traded on HOSE/HNX/UPCoM with full 2016–2025 statements; save the list and the reasons for exclusion in
Data/sample/banks.csv, and make every script read the sample from that file.
```

### 1.4 Macro data

```
Use the FiinX MCP to get 2015–2025: real GDP growth, monthly year-on-year CPI (average it per year), the deposit rate
above 12 months (midpoint, December), and system credit growth (December). Save to Data/macro/macro_vn.csv.
```

### 1.5 Repricing table

```
The "Rủi ro lãi suất" sheet in each FiinPro file splits customer loans by repricing band. Export the four bands that
reprice within 12 months (under 1, 1–3, 3–6, 6–12 months) and the remainder for each bank-year; flag it as usable
when the bands add up to gross loans on the balance sheet within ±10%. Check that Vietcombank 2025 gives VND 2,666 bn
at 25 bp, as in the ALCO proposal.
```

---

## 2. Simulation model

```
Write a simulation function for one bank-year, on the base-year statements, for the 12 months after the decision
(VND bn):
- Effective loans E = α × Σ loans in repricing band × months at the new rate / 12, with 11.5 / 10 / 7.5 / 3 months
  for bands under 1 / 1–3 / 3–6 / 6–12 months, and 0 for over one year and overdue. Without the table,
  E = loans × α × months / 12 (default 12, an upper bound).
- Borrower savings T = E × s / 10,000; depositors bear φ × T; profit before tax falls by T(1 − φ); tax 20%;
  shareholders bear the rest.
- New CAR = base CAR − fall in profit after tax × k / RWA (k = 100%, RWA unchanged). If capital/RWA differs from
  reported CAR by more than 0.3 pp, use reported CAR and imply RWA, labelled as estimated.
- Provision coverage = (pre-provision profit − fall in profit before tax) / provision expense.
- Closed-form maximum cut that keeps q% of profit after tax, and the break-even cut.
- Macro scenario: add Δ(provisions / loans) × loans to provision expense, kept separate from the rate-cut channel.
Handle loss-making banks and missing capital data. Check: with φ = 0, Vietcombank 2025 must give 41 bp and
profit −6.1% at 25 bp.
```

---

## 3. Econometrics

```
Write scripts/econometrics.py using linearmodels PanelOLS on 25 banks × 2016–2025, trimming 1% of each tail.
Declare the models in a MODELS list (id, VI/EN title, y, x, bank FE, year FE, SE type, takeaway generated from
the coefficients):
1. pass_mkt: Δ funding cost ~ Δ asset yield, bank FE, clustered SE.
2. pass_bank: the same with year FE (a single bank's own response) → the simulator's default φ.
3. roa_det: ROA ~ NIM + CIR + NPL + equity/assets + size + loans/assets, two-way FE (compare with 0.8).
4. car_resp: ΔCAR (capital/RWA) ~ ROA + loan growth, two-way FE (compare with 1 / (RWA / total assets)).
5. loan_resp: loan growth ~ Δ asset yield, two-way FE.
6. npl_resp: Δ next-year NPL ratio ~ Δ asset yield, two-way FE.
7. nim_macro: NIM ~ deposit rate + GDP + CPI + loan growth + NPL + size, bank FE, Driscoll-Kraay SE.
8. llp_macro: provisions / average loans ~ GDP + CPI + loan growth + prior-year NPL + size, bank FE, Driscoll-Kraay.
Macro models also report bank-clustered p-values; run a Hausman test (report a negative χ² as not usable).
Build macro scenarios from the change between two actual years: Favourable 2024→2025, Adverse 2019→2021, passed
through the llp_macro macro coefficients with p < 0.10. Export dashboard/econ.js and dashboard/panel.js (panel data
for the in-browser regressions).
```

---

## 4. Dashboard

```
Build a static HTML dashboard (dashboard/index.html, loading data.js, econ.js, panel.js, regress.js) for an ALCO/CFO,
looking like a professional data dashboard: Be Vietnam Pro font, rounded blue/navy cards, light and dark mode
(remembered, defaulting to the OS setting), bilingual VI/EN (toggle button, #en/#vi links), using the full screen
width. Colour-blind-checked categorical palette, no dual y-axes, tooltips on every chart, status shown with an icon
plus text.

Header: one line naming the user and the decision question; a title that is the computed conclusion
("VCB can cut lending rates by up to X bp and keep 90% of profit"); a one-sentence subtitle; bank and base-year
pickers (with an "All years" option).

Simulator tab:
- Control panel: large bp input + slider + 0/10/25/50/100 buttons; share of loans repriced; repricing timing with
  "From statements" / "12 months (upper bound)" buttons; funding-cost offset with "Data (φ from pass_bank)" /
  "Worst 0%" buttons; profit target 85/90/95% with the note "set by management"; macro scenario buttons. When the
  panel scrolls out of view, show a compact sticky control bar at the top, synced both ways.
- Four KPI cards: borrower savings (highlighted card), profit after tax (meter against the target), provision
  coverage, CAR (0–20% gauge with an 8% mark). Each has a status badge and a "How it's computed" button showing the
  formula with real numbers (the savings card shows the repricing table).
- Chart "How far can rates be cut before missing the profit target?": % of profit kept by bp, green zone meeting the
  target, target line, shaded band from the 95% CI of φ, dashed lines for the other two macro scenarios; the
  description states the cost per 10 bp and the range of the maximum cut; hover to read each level, click to select.
- 25-bank comparison (Δ profit / max cut / coverage / CAR after): horizontal bars, threshold lines per metric
  (10% loss, the bp under review, 1× and 2×, 8%), a median line, failing bars in red and thin ones in amber;
  a takeaway "x of 25 banks…" comparing the selected bank with the median and giving the ROA reason; banks with
  very thin profits listed separately.
- Macro scenario × 0/25/50 bp matrix (cell: % of profit kept ✓/!, CAR, coverage; click to select) and a table of
  commonly considered cuts.
- "All years" mode: KPI cards with small per-year bar charts, one sensitivity line per year, a bank × year heatmap
  coloured by rank, and a per-year table where clicking a row opens that year.

Method & data tab:
- "Proposed model" table: each link from the rate cut to a safety indicator, the model that tests it, what it means.
- Four model cards (pass_bank, roa_det, car_resp, llp_macro): added-variable plot (slope = coefficient), the
  simulator's assumption line, an auto-generated takeaway, a significance badge; buttons to switch year FE,
  trimming 0/1/5% and clustered/Driscoll-Kraay SE that re-estimate instantly. The provision card shows GDP and
  provisions by year (two small charts, no dual axis).
- "Run your own regression": pick a ready-made model or choose variables, FE, SE and sample; coefficient table with
  CI bars and a chart; macro variables lock when year FE is on.
- Variables table (formula, statement line, GSO/SBV source), source data traced to statement lines, data-quality
  checks, formulas, assumptions and limitations, glossary (hover dotted terms for definitions).
Write text as short natural sentences; keep technical detail in tooltips. Test in a browser and take screenshots to
check for overlapping labels, overflow and console errors.
```

### 4.1 In-browser regressions

```
Write dashboard/regress.js reproducing linearmodels PanelOLS: pandas-style quantile trimming, one- and two-way FE
demeaning, bank-clustered, Driscoll-Kraay (Bartlett, lag ⌊4(T/100)^(2/9)⌋) and robust SE, the n/(n − d − k)
adjustment as in auto_df, t-distribution p-values, within R², plus added-variable plot data. Write
scripts/test_regress.js comparing against econ.js for every model (coefficients within 1e-6, SE within 1e-4).
```

---

## 5. Infrastructure

```
Write scripts/run_pipeline.py running in order: merge data → data.js → analysis → econometrics, then checking the
accounting identities (pre-provision profit − provisions = PBT; PBT − tax = PAT) and stopping if any fails. Add
requirements.txt, README and .gitignore. GitHub Actions: on every push to main, run the pipeline, run
test_regress.js, then deploy the dashboard folder to GitHub Pages. Make the repo public and enable Pages.
```

---

## 6. Documents and presentation

```
Write docs/METHODOLOGY.md: the decision question, sample, two-layer model, regression table, reasons for the FE/SE
choices, limitations, and a variables table with statement lines and sources.
```

```
Write the Word file Team1_Documentation.docx (English, plus a Vietnamese version) with Track Changes on: research
problem, data and limitations, method, results (Vietcombank 2025, 25 banks, regressions, reconciliation with the ALCO
proposal), record of AI use, division of work, version history.
```

```
Write an English pitch script of about 6 minutes for the judges (international academics, FiinGroup) and students.
Follow five questions: why banks cut rates, who pays, what "safe" means and why 90%, why the numbers can be trusted
(a coffee-shop example for φ 39% vs 98%), and how much to cut. Include a three-step demo, slide titles that are
conclusions, a Q&A bank with one-sentence answers, and a Vietnamese summary.
```
