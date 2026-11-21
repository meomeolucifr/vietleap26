# Methodology: simulating lending-rate cuts and bank safety indicators

For the team and the judging panel. [Bản tiếng Việt](METHODOLOGY_VI.md). Figures reflect the `scripts/run_pipeline.py` run of 21/11/2026; when the data changes, the dashboard updates automatically, but the numbers in this document must be edited by hand.

## 1. The decision question

The user is the ALCO (Asset-Liability Committee) or CFO of a commercial bank. The question: **if the bank cuts its lending rate by s basis points (10 bp = 0.1 pp), does it still meet its safety thresholds?** Four indicators answer it:

| Indicator | Threshold on the dashboard | Why it matters |
|---|---|---|
| Profit after tax kept relative to the base year | Target set by the ALCO, default 90% (85/90/95% selectable) | Source of capital and dividends |
| Capital adequacy ratio (CAR) | At least 8% (SBV Circular 41/2016/TT-NHNN) | Legal requirement |
| Provision coverage = pre-provision profit / provision expense | ≥ 2×: thick; 1–2×: thin; < 1×: pre-tax loss | Buffer against credit losses |
| Borrower savings | — | The benefit of the programme |

The dashboard's headline result is the **maximum cut** that still meets the profit target, together with CAR and provision coverage at that cut. The 90% target is a management choice, not a regulation.

## 2. Sample

- **25 commercial banks** listed or traded on HOSE (22), HNX (1) or UPCoM (2) with full consolidated financial statements for **the 10 years 2016–2025** (250 bank-year observations).
- Excluded: Agribank and BaoViet Bank (not listed); ABBank (2016 missing); Bac A Bank and PVcomBank (no data file).
- The list, exchanges (checked in FiinX) and reasons are in [Data/sample/banks.csv](../Data/sample/banks.csv). Edit that file to change the sample; the whole pipeline reads it.

## 3. Proposed model: two layers

**Layer 1, accounting formulas.** The impact of a cut s is computed directly on the base-year financial statements, without regression, because the ALCO needs numbers for its own bank that trace back to statement lines.

```
E      = α × Σ (loans in repricing band i × mᵢ / 12)        loans at the new rate, time-weighted over 12 months
         mᵢ = 11.5 / 10 / 7.5 / 3 months for bands <1 / 1–3 / 3–6 / 6–12 months; over 1 year, overdue: 0
         (no repricing table: E = loans × α × months / 12)
T      = E × s / 10,000                                     borrower savings = interest income lost
ΔPBT   = T × (1 − φ) + ΔProv                                φ: share recovered through lower deposit rates
ΔPAT   = ΔPBT × (1 − tax)                                   tax = 20%
New CAR = base CAR − ΔPAT × k / RWA                         k: share of profit retained; RWA unchanged
Coverage = (pre-provision profit − T × (1 − φ)) / (base provisions + ΔProv)
Max cut = [(1 − target) × base PAT − ΔProv × (1 − tax)] / [E × (1 − φ) × (1 − tax)] × 10,000
```

**Source of E.** The repricing table in the notes to the financial statements (FiinPro-X "interest rate risk" sheet) splits customer loans by time to first repricing. This is the repricing-gap model used in interest-rate risk management: only loans that reprice within 12 months carry the new rate, and only for the remaining months. 231 of 250 bank-years have a table whose buckets match gross loans within ±10%; the other 19 use manually set months (default 12, an upper bound) and are flagged on the dashboard. This is the same method as the team's ALCO proposal for Vietcombank.

**Layer 2, econometrics.** Layer 1 needs parameters that one year of statements cannot provide. Layer 2 estimates them with panel regressions on 25 banks × 10 years using `linearmodels` (PanelOLS). Each model tests one link:

| Link | Question | Model | Result | What it means for the safety indicators |
|---|---|---|---|---|
| Funding-cost offset φ | When one bank lowers its yield, how much does its funding cost fall? | `pass_bank`: Δfunding cost ~ Δasset yield + bank FE + year FE, clustered SE | **0.39** (p < 0.001; n = 193). If the whole market moves (`pass_mkt`, no year FE): 0.98 | Default φ = 39%. Profit loss, CAR and provision buffer all depend directly on φ |
| Lost NIM → lost ROA | The simulator assumes 1 bp of NIM lost = 0.8 bp of ROA lost. True? | `roa_det`: ROA ~ NIM + CIR + NPL + equity/assets + size + loans/assets + bank FE + year FE | **0.30** (p < 0.001; n = 186) | Banks offset part of it; the profit loss shown is an **upper bound** |
| Do risk-weighted assets rise? | Does a bank that cuts rates grow its loan book faster, raising RWA and lowering CAR? | `loan_resp`: loan growth ~ Δasset yield + bank FE + year FE | 0.01 (**p = 0.99**; n = 192) | No evidence; consistent with SBV credit-growth quotas. Holding RWA fixed is justified |
| Profit → CAR | How much does lower profit cut CAR? Is the simulator's formula right? | `car_resp`: ΔCAR ~ ROA + loan growth + bank FE + year FE, clustered SE; CAR = regulatory capital / RWA; where this contradicts both reported CAR figures by more than 0.3 pp (source data errors, e.g. VPB 2022–2023) reported CAR is used, and missing years from 2020 (all banks on Circular 41) are filled with reported CAR | ROA +1 pt → CAR **+0.65** pt (p = 0.066; Driscoll-Kraay p < 0.001; n = 115, 24 banks; CI −0.04–1.34). The formula implies 1 / (RWA / total assets) = 1.21 | Inside the confidence interval, and above the estimate: CAR moves less than the formula in practice, so the dashboard's CAR fall is conservative. Earlier years are not filled because reported CAR before 2020 used Circular 36 |
| Lower rates → fewer bad loans? | Does a cut help borrowers repay, lowering next year's NPLs? | `npl_resp`: Δ NPL ratio next year ~ Δasset yield + bank FE + year FE | Not significant (p = 0.81) | No such benefit added; the simulator stays conservative |
| Weaker economy → more provisions | How much do provisions rise when GDP growth slows? | `llp_macro`: provisions / average loans ~ GDP + CPI + loan growth + prior-year NPL + size + bank FE, Driscoll-Kraay SE | GDP −1 pp → provisions **+2.2 bp** of loans (p < 0.001; but p ≈ 0.36 with clustered SE) | Drives the Adverse scenario (like 2019→2021, GDP −4.4 pp: provisions +9.7 bp) and the Favourable one (−2.0 bp) |
| Macro → NIM | Do macro conditions move NIM? | `nim_macro`: NIM ~ deposit rate + GDP + CPI + loan growth + NPL + size + bank FE, Driscoll-Kraay SE | No macro coefficient significant at 5% | Channel not added; avoids double counting with the rate-cut channel |

Example, Vietcombank, base year 2025, 25 bp cut, φ = 39%, Base scenario: E = VND 1,066,318 bn (64% of loans), borrowers save VND 2,666 bn, profit after tax falls 3.7%, CAR 11.56% → 11.49%, provision coverage 14.8× → 14.3×. The bank can cut by up to 67 bp (55–86 bp across the confidence interval of φ) and keep 90% of profit; 42 bp in the Adverse scenario. With φ = 0, as in the ALCO proposal, the result is 41 bp, with profit −6.1% at 25 bp and −12.1% at 50 bp, matching the proposal.

On the dashboard (Method & data tab), the four main models, one per safety indicator (`pass_bank`, `roa_det`, `car_resp`, `llp_macro`), are drawn as added-variable plots. Each dot is a bank-year after removing fixed effects and controls; the slope of the fitted line equals the coefficient, shown next to the assumption the simulator uses. Users can switch year effects, trimming and standard errors; the regressions re-run in the browser (`dashboard/regress.js`, matching linearmodels to about 1e-8, checked by `node scripts/test_regress.js`). The "Run your own regression" panel lets users pick any variables.

### Why these choices

- **Year fixed effects** absorb everything common to the whole system in a given year (policy rate, credit quotas, the cycle). The remaining coefficient measures how a single bank responds, which is the ALCO's situation when it decides to cut on its own. The drop from 0.98 to 0.39 shows how much this choice matters.
- **Macro variables** are identical across banks in a year, so models that use them cannot include year fixed effects and have only about 10 time points. They use Driscoll-Kraay standard errors (robust to correlation across banks within a year) and also report bank-clustered p-values to show the uncertainty.
- **1% of each tail is trimmed** to limit the influence of a few unusual bank-years (e.g. banks with very thin profits).
- The Hausman FE/RE test is reported on the dashboard; for the two macro models the statistic is negative, so the test is not usable, and FE is kept because it is always consistent.

### Limitations

- Results are the incremental 12-month effect versus the base year, not a forecast.
- The impact is linear in the size of the cut (Vietcombank 2025: each 10 bp costs about 1.5% of profit). Reality may curve: the funding offset may change with the size of the cut, and lower rates may help borrowers repay and reduce provisions. Annual data cannot estimate the curvature; instead, the dashboard draws an uncertainty band from the 95% confidence interval of φ (26–52%), giving Vietcombank 2025 a maximum cut of 55–86 bp.
- Within each repricing band the repricing date is assumed to be the midpoint (as in the ALCO proposal); fixed-rate loans that mature are assumed to roll over at the new rate. Years without the table use manually set months. The 90% profit target is a management choice, not a regulation; the dashboard offers 85/90/95%.
- Coefficients are conditional correlations, not causal effects. φ is a historical pattern, not a commitment by depositors.
- The GDP coefficient in `llp_macro` is sensitive to the choice of standard errors; loan-restructuring forbearance in 2020–2021 (Circular 01/2020) may have delayed provisioning.

## 4. Variables, formulas and data sources

Bank data: audited consolidated annual financial statements. Freely available on each bank's investor-relations site or the HOSE/HNX disclosure portals; standardised versions are on FiinPro-X (the team used exports dated 13/10/2026, folder `Data/`). Unit: VND bn. Statement line names are given in Vietnamese as they appear in the source.

### 4.1 Raw items

| Variable | Symbol | Statement line |
|---|---|---|
| Customer loans (gross, before provisions) | `loans` | Balance sheet · "Cho vay khách hàng" |
| Interest income | `ii` | Income statement · "Thu nhập lãi và các khoản thu nhập tương tự" |
| Interest expense | `ie` | Income statement · "Chi phí lãi và các chi phí tương tự" |
| Net interest income | `nii` | Income statement · "Thu nhập lãi thuần" |
| Total operating income; operating expenses | `toi`, `opex` | Income statement |
| Pre-provision profit | `ppop` | Income statement · "Lợi nhuận thuần từ hoạt động kinh doanh trước chi phí dự phòng rủi ro tín dụng" |
| Credit-loss provision expense | `prov` | Income statement |
| Profit before tax; corporate income tax; profit after tax | `pbt`, `tax`, `pat` | Income statement |
| Total assets; liabilities; equity; customer deposits | `ta`, `liab`, `equity`, `deposits` | Balance sheet |
| Regulatory capital; risk-weighted assets; CAR | `vtc`, `rwa`, `car` | Notes, "Tỷ lệ an toàn vốn"; risk disclosure report (Circular 41) on the bank's website |
| Loans by debt group 1–5 | `N1..N5` | Notes, "Phân tích chất lượng nợ cho vay" |
| Customer loans by repricing band | `rp` | Notes, interest-rate risk table (FiinPro "Rủi ro lãi suất") |

### 4.2 Derived variables

"Average" = (opening + closing) / 2.

| Variable | Symbol | Formula |
|---|---|---|
| Asset yield | `yield` | ii / average total assets |
| Funding cost | `cost` | ie / average liabilities |
| NIM | `nim` | nii / average total assets |
| ROA | `roa` | pat / average total assets |
| Cost / income | `cir` | opex / toi |
| NPL ratio | `npl` | (N3 + N4 + N5) / (N1 + … + N5) |
| Provision rate | `llp` | prov / average loans |
| Loan growth | `loang` | loans<sub>t</sub> / loans<sub>t−1</sub> − 1 |
| Equity / assets; size | `cap`, `size` | equity / ta; ln(ta) |
| Loans / assets | `loans_ta` | loans / ta |
| Provision coverage | `cov` | ppop / prov |
| CAR | `car` | vtc / rwa (checked against reported CAR; if they differ by more than 0.3 pp, reported CAR is used and RWA is implied) |
| Year-on-year change | `Δx` | x<sub>t</sub> − x<sub>t−1</sub> |

### 4.3 Macro

File [Data/macro/macro_vn.csv](../Data/macro/macro_vn.csv), % a year, retrieved through FiinX (originally from GSO and the SBV).

| Variable | Symbol | Definition | Original source |
|---|---|---|---|
| Real GDP growth | `gdp_growth` | Constant prices, year on year | General Statistics Office (nso.gov.vn), annual Q4 socio-economic release |
| Average CPI inflation | `cpi_avg` | 12-month average of year-on-year CPI | General Statistics Office, same release (annual average published directly) |
| Deposit rate above 12 months | `deposit_rate_12m` | Midpoint of the range published by the SBV, December | State Bank of Vietnam (sbv.gov.vn), interest-rate statistics |
| System credit growth | `credit_growth` | December outstanding credit, year on year | State Bank of Vietnam, monetary statistics |

## 5. Reproducing the results

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py --xlsx     # data -> Excel panel -> dashboard/*.js -> checks
node scripts/test_regress.js
python -m http.server 8000 -d dashboard
```

Model specifications are in the `MODELS` list of [scripts/econometrics.py](../scripts/econometrics.py); the takeaways on the dashboard are generated from the regression results.
