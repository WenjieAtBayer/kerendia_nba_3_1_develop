# NBA 3.1 — FTP & Copay: new feature ideas from the claims tables

Date: 2026-11-17. Ideas only: nothing was built, no notebook or table was changed.
Builds on `NBA_3_1_FTP_Copay_3_0_Feasibility.md` (the 3.0-to-new-table comparison, same folder).

**In one line:** the new claims tables have enough columns to go well beyond the 3.0 feature set. The highest-value additions are new-patient starts, patient counts, recency, persistence, and a combined FTP + copay view per doctor.

## Where to find things

| Item | Location |
| --- | --- |
| New tables | `ph-com-ai-us-prod-catalog-2553213839599380.market_access.kerendia_ftp_claims` / `...kerendia_copay_claims` |
| 3.1 cohorts | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1.input_claims_cohorts` (28 rows) |
| 3.1 FTP draft notebook | `/Users/patricio.guledjian.ext@bayer.com/kerendia_nba_3_1_develop/NBA 3.1 - Dev/04_Promotional_Features/FTP_and_Copay/19_ftp_features` |
| 3.1 copay draft notebook | same folder, `22_copay_features` |
| 3.0 feasibility doc | `NBA_3_1_FTP_Copay_3_0_Feasibility.md` (this folder) |

---

## 1. Where the 3.1 FTP / copay notebooks stand today

I read both draft notebooks.

* **FTP (`19_ftp_features`):** reads a Snowflake sales table (`CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_SALES_ALIGNED`, `SALE_TYP = 'FTP'`), not the new claims table. It uses the 3.0 inference anchor file with one cohort, not the 3.1 cohort config.
* **Copay (`22_copay_features`):** still a placeholder with the 3.0 code and a TODO marker. The planned source (`CPH_DB_PROD.MODEL_V2.TRMN_CSMR_PROF_MDM`) is a consumer-profile table with no doctors or fills.
* In the 3.1 Git folder (`kerendia_nba_3_1_develop_pg`) the old path `NBA 3.1 - Dev/04_Promotional_Features` no longer resolves. The folder listing I read was truncated, so other locations in that folder were not fully checked.

So the proposals below start from the 3.0 logic (feasibility doc) and the 3.1 cohort framework.

---

## 2. The 3.1 cohort framework all features must follow

Source: `input_claims_cohorts`.

* 28 cohorts c1–c28, calendar months. Example c24: lookback 2025-05-01 to end of April 2026, prediction month 2026-06.
* c1–c24 Training, c25–c26 Testing, c27–c28 Holdout (backtesting).
* Prediction month = lookback end + 2 months (one gap month between the cutoff and the target).
* **Cutoff** = last day of the lookback end month. Every feature must use only fills picked up (`RX_FILL_DATE`) on or before the cutoff.
* Windows: last 1, 3, 6 and 12 months ending at the cutoff (the windows used by the other 3.1 HCP notebooks per earlier work; not re-checked here). Key = `BH_ID` + cohort.

---

## 3. Rules that apply to every feature (leakage prevention)

| Rule | Why | Evidence |
| --- | --- | --- |
| Use pickup date (`RX_FILL_DATE`), not prescription date (`RX_WRITTEN_DATE`) | Prescription date lets future fills leak into past windows | Feasibility doc: 554 FTP and 8,979 copay fills written before and picked up after the 3.0 run date |
| Optional: also require `INSERT_TS` ≤ cutoff + fixed lag (e.g. 14 days) | The table is rebuilt from today’s data, so a fill that arrived late shows up in a window it was not in at run time | In the c24 window (through 2026-04-30): 187 FTP / 641 copay fills have an `INSERT_TS` after the cutoff; 95% of fills arrive within 14 / 11 days |
| Treat clawback flags and netted money as **known only when the table was last built** | There is no date column that says when the clawback happened; the flag reflects the 2026-11-16 rebuild | Columns `MDFD_DT`, `DATA_DT`, `CRTD_DT` exist but their meaning was not checked |
| Count 1 per fill, not `N_SOURCE_ROWS` | 3.0 counted the correction record of a clawback as a second fill; that was a mistake (see feasibility doc) | Removing the weight makes the rebuild worse, confirming 3.0 counted it |
| Do not use `MDM_*` fields as time-varying features | Those are current-state snapshots of the doctor, not how the doctor looked at each fill | — |

**Why these features might help the model.** FTP and copay are Bayer-supported Kerendia fills, so they show that a doctor is writing Kerendia and how much access friction their patients face. Whether they add signal beyond the Kerendia prescription features already in 3.1 (NB01 / NB05) is **not measured yet**; that needs a feature-importance check after building.

---

## 4. FTP features

### What 3.0 had

6 features: free-trial fill counts in the last 1–6 months (30-day steps). Rebuilt at 99.97%. Issues: clawbacks counted twice, prescription-date leakage, its own anchor windows.

### Coverage in c24 (fills 2025-05-01 to 2026-04-30, doctors with Bayer IDs)

3,722 doctors, 8,541 patients, 8,827 fills, 8,023 new Rx, 458 clawbacks, 48 fills at 40 mg (NDC 50419-0542-xx), 0 fills ≥ 84 days supply; 1,360 doctors with a fill in the last 3 months.

### Proposed features

| # | Feature (1/3/6/12-month windows unless noted) | What it counts | Which columns | What it tells us | Leakage risk |
| --- | --- | --- | --- | --- | --- |
| F1 | `FTP_CLAIMS_<w>M` | Fills in the window (1 per fill, clawbacks included) | `RX_FILL_DATE`, `BH_ID` | Replacement of the 3.0 count, on the correct date | Low |
| F2 | `FTP_NEW_STARTS_<w>M` | Fills where `IS_NEW_RX` = true | `IS_NEW_RX` | New patients put on Kerendia through FTP (8,023 of 8,827 c24 fills are new Rx) | Low |
| F3 | `FTP_PATIENTS_<w>M` | Distinct patients | `MMBR_ID` | How many different patients, not just how many fills | Low |
| F4 | `DAYS_SINCE_LAST_FTP` | Cutoff − most recent fill date (null if no FTP history) | `RX_FILL_DATE` | Recency: a doctor who filled last month is more likely to fill next month | Low |
| F5 | `DAYS_SINCE_FIRST_FTP` | Cutoff − earliest fill date | `RX_FILL_DATE` | Tenure: separates new adopters from long-time FTP users | Low; left-censored before 2021-10 (earliest fill in the table) |
| F6 | `FTP_TREND_3M` | Fills in the last 3 months minus fills in the 3 months before | `RX_FILL_DATE` | Momentum: is the doctor ramping up or down? | Low |
| F7 | `FTP_REFILL_SHARE_<w>M` | Fills with `FILL_NUMBER` > 0 / all fills | `FILL_NUMBER` | Share of patients continuing on FTP (21,116 fills have fill number 1, 14,791 have 2) | Low |
| F8 | `FTP_HIGH_DOSE_SHARE_<w>M` | Fills at 20 mg or 40 mg / all fills (by NDC) | `NDC_NUM` or `DRG_DESC` | Titration: doctors who prescribe higher doses are experienced with the drug | Low; NDC-to-strength map must be confirmed |
| F9 | `FTP_WRITTEN_TO_FILL_DAYS_MED_<w>M` | Median days from prescription to pickup, among fills in the window | `RX_WRITTEN_DATE`, `RX_FILL_DATE` | Access friction (overall median 12 days, p90 81 days) | Low (both dates ≤ cutoff) |
| F10 | `FTP_OTHER_COVERAGE_SHARE_<w>M` | Fills with `OTHR_CVRG_CD` ≠ '00' / all | `OTHR_CVRG_CD` | Payer mix of the doctor's patients (values 00 / 01 / 03) | Low; code meanings not checked |
| F11 | `FTP_CLAWBACK_SHARE_<w>M` | Clawed-back fills / all | `IS_BENEFIT_CLAWED_BACK` | Benefit later reversed | **High**: no clawback date exists in the table, so using the flag reveals information from the future |

---

## 5. Copay features

### What 3.0 had

15 features: monthly counts, 1–6-month sums, running total, 7 percentages. Rebuilt at 99.84%. Issues: clawbacks counted twice, prescription-date leakage, copay amount loaded but not used, percentages empty 93% of the time.

### Coverage in c24 (same window as FTP)

4,668 doctors, 6,797 patients, 30,938 fills, 9,187 new Rx, 3,173 clawbacks, 4,089 fills with ≥ 84 days supply, 115 fills at 40 mg; 2,856 doctors with a fill in the last 3 months.

### Proposed features

| # | Feature (1/3/6/12-month windows unless noted) | What it counts | Which columns | What it tells us | Leakage risk |
| --- | --- | --- | --- | --- | --- |
| C1 | `COPAY_CLAIMS_<w>M` | Fills in the window (1 per fill) | `RX_FILL_DATE`, `BH_ID` | Clean replacement of the 3.0 counts; the percentage features are dropped | Low |
| C2 | `COPAY_NEW_PATIENTS_<w>M` | Fills where `IS_NEW_RX` = true | `IS_NEW_RX` | New Kerendia patients with commercial coverage | Low |
| C3 | `COPAY_ACTIVE_PATIENTS_AT_CUTOFF` | Distinct patients whose last fill + supply days extends to within 30 days of the cutoff | `MMBR_ID`, `RX_FILL_DATE`, `DAY_SUPPLY_NUM` | Patients currently on therapy: they need refills, which keeps the doctor prescribing | Low |
| C4 | `COPAY_LAPSED_PATIENTS_<w>M` | Patients with a fill earlier in the window but whose supply ran out more than 30 days ago | same | Drop-off: patients who stopped | Low |
| C5 | `COPAY_DAYS_SUPPLY_<w>M` | Sum of `DAY_SUPPLY_NUM` | `DAY_SUPPLY_NUM` | Volume in patient-days (30-day and 90-day fills count differently than in C1) | Low |
| C6 | `COPAY_90DAY_SHARE_<w>M` | Fills with ≥ 84 days supply / all | `DAY_SUPPLY_NUM` | Maintenance therapy (4,089 of 30,938 c24 fills) | Low |
| C7 | `COPAY_FILLS_PER_PATIENT_<w>M` | Fills / distinct patients | `MMBR_ID` | Persistence: more fills per patient means patients stay on the drug | Low |
| C8 | `COPAY_BENEFIT_PER_CLAIM_<w>M` | Average of `PTNT_BNFT` (the gross benefit Bayer paid at the time of the fill) | `PTNT_BNFT` | Size of the cost barrier Bayer covers | Low with the gross value; **high** with the netted value `NET_PTNT_BNFT` (netting is only known at rebuild time) |
| C9 | `COPAY_PATIENT_OOP_PER_CLAIM_<w>M` | Average of `PATOOP` (patient out-of-pocket) | `PATOOP` | What patients still pay after the copay card (mean $1.35 on normal fills) | Low (gross value) |
| C10 | `COPAY_SECONDARY_COVERAGE_SHARE_<w>M` | Fills with `OTHR_CVRG_CD` = '03' / all (copay has values 08 and 03) | `OTHR_CVRG_CD` | Payer situation; in group 1BJEOFSFLDF, code-03 fills average $629 benefit vs $313 for code 08 | Low; code meanings not checked |
| C11 | `COPAY_GROUP_<GRP>_SHARE_<w>M` | Share by `GRP_NUM` (3 values; 1BJEOFSFLDF has 96,885 of 106,029 fills) | `GRP_NUM` | Program variant | Low; group meanings not checked |
| C12 | `DAYS_SINCE_LAST_COPAY`, `COPAY_TREND_3M` | Same as F4 / F6 but for copay | `RX_FILL_DATE` | Recency and momentum | Low |
| C13 | `COPAY_CLAWBACK_SHARE_<w>M` | Clawed-back fills / all | `IS_BENEFIT_CLAWED_BACK` | Benefit later reversed (copay clawbacks only exist from 2024 onward) | **High** (no known clawback date in the table) |

---

## 6. Features that combine both programs (per doctor)

| # | Feature | What it counts | Why | Leakage risk |
| --- | --- | --- | --- | --- |
| X1 | `FTP_TO_COPAY_RATIO_<w>M` | FTP fills / (FTP + copay fills) | Shows whether the doctor's patients are mostly trialing or mostly on ongoing copay support; 5,147 doctors appear in both tables | Low |
| X2 | `HAS_FTP_AND_COPAY_<w>M` | 1 if the doctor has both FTP and copay fills in the window | Uses both programs | Low |

Patient-level FTP-to-copay conversion ("how many patients move from trial to copay") is **not possible**: the two tables share 0 patient IDs.

---

## 7. What to build first

The safest path is to start with the features that use only fill counts and dates (low leakage, easy to verify), and leave the cost and flag features for later:

1. **FTP:** F1 (count), F2 (new starts), F3 (patients), F4 (recency), F6 (trend).
2. **Copay:** C1 (count), C2 (new patients), C3 (active patients), C5 (days supply), C6 (90-day share), C7 (fills per patient), C12 (recency + trend).
3. **Cross:** X1 (ratio), X2 (flag).
4. Run SHAP / ablation on c25–c26 to see which ones the model actually uses.
5. Then decide on F8 (dose), F9 / F10 (access friction / payer), C8 / C9 (benefit / OOP), C10 / C11 (coverage / group).
6. F11 and C13 (clawback share) only if a clawback date becomes available.

---

## 8. Not checked yet / open points

| # | Point | What is needed | Effect |
| --- | --- | --- | --- |
| 1 | Do these features add value beyond existing 3.1 Kerendia Rx features? | Build the low-risk set, run SHAP on c25–c26 | Decides which features stay |
| 2 | Meaning of `OTHR_CVRG_CD` and `GRP_NUM` values | Ask the market-access data owner | Needed before C10, C11, F10 |
| 3 | Clawback date | Ask whether the source system records when the clawback happened | Would make F11, C13, and the netted money columns usable |
| 4 | `INSERT_TS` lag rule | Decide: fixed lag, no filter, or match the inference pipeline | Ensures training and inference see the same data |
| 5 | NDC-to-strength mapping | Confirm with the product master | Needed for F8 |
| 6 | Doctor→provider-ID mapping | Use the 3.1 pipeline mapping | Needed for joins with other 3.1 feature tables |
