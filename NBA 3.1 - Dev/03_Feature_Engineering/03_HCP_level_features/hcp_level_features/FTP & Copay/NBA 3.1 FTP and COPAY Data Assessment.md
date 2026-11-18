# NBA 3.1 FTP and Copay: Data Assessment of the UC Tables

Date: 2026-11-18. Assessment only: no notebook or table was changed.

This document assesses the two Unity Catalog claims tables that NBA 3.1 will use for FTP and copay features, against the 3.1 HCP universe (294,727 providers). It covers what is in the tables, how well they cover the universe, and how the information can be used.

All numbers come from queries run on 2026-11-18 against the tables as rebuilt on 2026-11-16 (`REFRESH_TS`). A "fill" is one row of a claims table, which is one original claim (`ORGN_CLM_AUTH_NUM`). Unless stated otherwise, "in the universe" means that the fill's `PRSC_NPI` matches the NPI of a universe provider.

---

## Summary by section

Overview: we checked the two new Unity Catalog claims tables (FTP and copay) that 3.1 will use: what is in them, how well they cover the 3.1 HCP universe, and how to use them for features.

### Section 1: NBA 3.1 data assessment

**1a. Where things are**
* Two input tables: `market_access.kerendia_ftp_claims` and `market_access.kerendia_copay_claims`.
* Built from the Bayer data warehouse copay source (`stg_gtn_copay`), loaded weekly.
* Monthly raw snapshots are kept next to them, so any number can be traced back to the source.

**1b. How the tables are built**
* FTP and copay are split by program group number.
* Reversed (cancelled) claims are removed; each original claim keeps exactly one row.
* Clawed-back benefits are netted and flagged.
* Dates and numbers are typed; the prescriber is matched to HCP master data (Bayer ID, specialty).
* Rebuilt weekly with built-in quality checks (the refresh fails on duplicates, stale data, or a row drop of more than 5%).

**1c. Size and date range**
* About 106K claims in each table; about 16K prescribers (FTP) and 9.4K (copay).
* About 68K patients in FTP and 20K in copay.
* Data runs from late 2021 to November 2026, covering all 28 cohorts of 3.1.
* About 63% of FTP fills are new prescriptions vs 31% for copay: copay is mostly refills.

**1d. Link to the HCP universe**
* The universe has 294,727 providers and no NPI, so it is linked through the existing provider → NPI mapping.
* About 99.5% of all FTP and copay fills belong to universe HCPs: the link is practically lossless.
* Linking on NPI or on Bayer ID gives the same result.

**1e. Coverage per cohort**
* Key message: only 1.9–2.7% of the universe has any FTP or copay fill in a 12-month window; about 97% of HCPs will show zero.
* Copay is growing (HCPs about 3.2K to 5.0K, fills doubled); FTP is flat at about 3.5–4K HCPs.
* FTP is essentially one fill per patient; copay averages about 4.5 fills per patient.
* The two programs reach mostly different HCPs: only about 1,000 HCPs per cohort have both.

**1f. Trend over time**
* FTP volume dropped sharply in 2023 and has been stable at about 2,000–2,400 fills per quarter since mid-2024.
* Copay rose steadily to about 8,500 fills per quarter.
* Training and holdout cohorts therefore see a somewhat different FTP / copay mix.

**1g. Distribution per HCP**
* Very skewed: 67% of FTP HCPs have only one fill, while a few have more than 100. The median copay HCP has 4 fills.
* Counts should be capped, log-transformed, or banded.

**1h. What the data contains**
* Strength is mostly 10 mg; 20 mg is about 21% of FTP and 41% of copay.
* Days supply is almost always 30; about 12% of copay fills are 90-day fills.
* FTP benefit is roughly the drug price (about 600–720 USD); copay benefit varies widely (30–700 USD), a usable affordability signal.
* Patient out-of-pocket is effectively always zero and carries no information.

**1i. Column-by-column review**
* Of 83 columns, 4 are keys, 4 are dates, and about 16 can feed HCP features.
* The rest are constants, admin fields, names or addresses, or text duplicates of typed columns.

**1j. Possible features**
* Five features per program: has any FTP / copay fill, fills per window, new-Rx fills, days since last fill, and (copay only) average copay before the card.
* Only FTP fills per window is the same as 3.0 (now by fill date); the rest are new in 3.1.
* Other ideas (persistence, trend, dose, patient-days, access lag, payer, patient and pharmacy mix) are deprioritised.

**Conclusion:** the data is reliable and ready to use. Open questions: how much signal these features add given the low coverage, and confirming a few code meanings (payer codes, BINs).

---

## 1. NBA 3.1 data assessment

### 1a. Where things are

| Item | Location |
| --- | --- |
| FTP claims (NBA 3.1 input) | `ph-com-ai-us-prod-catalog-2553213839599380.market_access.kerendia_ftp_claims` |
| Copay claims (NBA 3.1 input) | `ph-com-ai-us-prod-catalog-2553213839599380.market_access.kerendia_copay_claims` |
| Raw source rows (monthly snapshots) | `market_access.kerendia_ftp_claims_snapshot`, `market_access.kerendia_copay_claims_snapshot` |
| Build notebooks | `/Users/wenjie.chen@bayer.com/kerendia_data_needs/Copay_FTP/` (`00_common` = logic, `02_refresh_copay_ftp` = weekly refresh + QC) |
| Source | `phcdw.phcdw_stg_common.stg_gtn_copay` (Snowflake `PHCDW.PHCDW_STG_COMMON.STG_GTN_COPAY` through Lakehouse Federation), `SRC_SYS_CD = 'PRM'`, loaded weekly (Sundays) |
| 3.1 HCP universe | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1.input_hcp_universe` |
| 3.1 cohorts | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1.input_claims_cohorts` (c1–c28) |
| Provider → NPI / Bayer ID mapping | volume `kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping` (the default `NPI_BHID_MAPPING_PATH` in the 3.1 `00_cohort_config`) |

### 1b. How the UC tables are built (`00_common`)

* **Program split:** by `GRP_NUM`. FTP = 7 groups ending in `WF` (`101194196WF`, `112194196WF`, `151194196WF`, `161194196WF`, `171194196WF`, `181194196WF`, `191194196WF`). Copay = `1BJEOFSFLDF`, `121194196DF`, `131194196DF`.
* **Sales filter:** `USE_SLS = 'Y'`.
* **Reversals:** per `ORGN_CLM_AUTH_NUM`, the net `DAY_SUPPLY` is summed; claims with net supply ≤ 0 (approval cancelled by its reversal) are dropped.
* **One row per original claim:** the row kept is the approval row (`DAY_SUPPLY` > 0) with the highest benefit, then the earliest load. Duplicate rows of the same claim are gone.
* **Benefit clawbacks:** a second positive-supply row with a negative benefit is netted into the money columns (`NET_*`) and flagged (`IS_BENEFIT_CLAWED_BACK`).
* **Typed / derived columns:** dates parsed from text (`RX_FILL_DATE`, `FILL_MONTH`, `RX_WRITTEN_DATE`, `INSERT_TS`), numbers cast (`DAY_SUPPLY_NUM`, `QTY_NUM`, `RX_REFILLS_NUM`, `FILL_NUMBER`), new prescription flag (`IS_NEW_RX` = `NEW_REFILL_CD = '00'`).
* **Prescriber:** `BH_ID`, `MDM_FIRST_NAME`, `MDM_LAST_NAME`, `MDM_SPECIALTY` from MDM (`phcdw.phcdw_stg.mdm_stg_hcp_prfl`, `RECORD_TYPE = 'VOD'`), matched on `PRSC_NPI`.
* **Refresh:** the claims tables are **overwritten** every week. The snapshot tables keep the raw source rows, one partition per month (only `SNAPSHOT_MONTH = 2026-11-01` exists today: 136,074 FTP rows, 120,329 copay rows).
* **QC in the refresh:** the run fails on duplicate claims, non-positive supply, unparsed fill dates, rows outside the program groups, a source older than 21 days, or a row drop of more than 5%.

### 1c. Table size and date ranges

| | FTP | Copay |
| --- | --- | --- |
| Rows (= original claims) | 105,995 | 106,029 |
| Columns | 83 | 83 |
| Distinct prescriber NPIs | 16,016 | 9,446 |
| Distinct `BH_ID` | 16,008 | 9,442 |
| Distinct patients (`MMBR_ID`) | 67,891 | 19,783 |
| Distinct patients (`SHLD_ID`) | 67,842 | 19,002 |
| Fill date (`RX_FILL_DATE`) | 2021-10-11 to 2026-11-06 | 2021-08-04 to 2026-11-06 |
| Written date (`RX_WRITTEN_DATE`) from | 2021-01-13 | 2021-07-29 |
| Latest load (`INSERT_TS`) | 2026-11-09 | 2026-11-09 |
| Rebuilt (`REFRESH_TS`) | 2026-11-16 | 2026-11-16 |
| New prescriptions (`IS_NEW_RX`) | 67,100 (63.3%) | 32,767 (30.9%) |
| Clawed-back claims (`IS_BENEFIT_CLAWED_BACK`) | 1,328 (1.25%) | 7,212 (6.80%) |
| Claims with net benefit ≤ 0 (`IS_ZERO_NET_BENEFIT`) | 1,327 | 7,287 |
| Source rows netted into the claims (`N_SOURCE_ROWS`) | 107,322 | 113,232 |

Both tables cover every 3.1 cohort: the first lookback starts on 2023-06-01 (c1), and the last cutoff is 2026-08-31 (c28).

### 1d. The 3.1 HCP universe and how it links to the claims

| | Value |
| --- | --- |
| Providers (`PROVIDER_ID`, one row each) | 294,727 |
| Found in the provider → NPI / Bayer ID mapping | 294,578 |
| With an NPI | 294,553 (294,542 distinct NPIs) |
| Distinct Bayer IDs | 294,540 |

The universe has no NPI or Bayer ID, so it has to be linked through the mapping: `PROVIDER_ID` → `NPI_NUMBER` → claims `PRSC_NPI`.

| Link check | FTP | Copay |
| --- | --- | --- |
| All fills | 105,995 | 106,029 |
| Fills of universe HCPs (on NPI) | 105,562 (99.59%) | 105,408 (99.41%) |
| NPIs in the universe / all NPIs | 15,722 / 16,016 | 9,259 / 9,446 |
| Fills of universe HCPs (on `BH_ID` instead) | 105,556 | 105,393 |
| Fills where the NPI and `BH_ID` links disagree | 6 | 15 |
| Fills with no `PRSC_NPI` | 47 | 43 |
| Fills with no `BH_ID` | 55 | 54 |

**Result:** almost every FTP and copay fill belongs to a universe HCP. Linking on NPI or on `BH_ID` gives practically the same result.

### 1e. Coverage of the universe per cohort

For each cohort, these are the universe HCPs with at least one fill picked up in the 12-month lookback (`lookback_start_date` to the last day of the `lookback_end_date` month), plus the counts for the last 3 months before the cutoff. Patients = distinct `MMBR_ID`.

| Cohort | Set | Cutoff | FTP HCPs | Copay HCPs | Either | Both | % of universe (either) | FTP HCPs, last 3 m | Copay HCPs, last 3 m | FTP fills | Copay fills | FTP patients | Copay patients |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | Training | 2024-05-31 | 4,780 | 3,156 | 6,569 | 1,367 | 2.23 | 707 | 1,261 | 11,453 | 15,401 | 11,370 | 6,305 |
| c2 | Training | 2024-06-30 | 4,556 | 3,213 | 6,452 | 1,317 | 2.19 | 1,033 | 1,616 | 10,742 | 15,871 | 10,635 | 6,598 |
| c3 | Training | 2024-07-31 | 4,378 | 3,311 | 6,383 | 1,306 | 2.17 | 1,142 | 1,841 | 10,338 | 16,774 | 10,203 | 6,836 |
| c4 | Training | 2024-08-31 | 4,174 | 3,391 | 6,306 | 1,259 | 2.14 | 1,163 | 1,957 | 9,736 | 17,624 | 9,567 | 6,986 |
| c5 | Training | 2024-09-30 | 4,008 | 3,444 | 6,256 | 1,196 | 2.12 | 1,162 | 2,029 | 9,269 | 18,550 | 9,069 | 7,097 |
| c6 | Training | 2024-10-31 | 3,840 | 3,503 | 6,171 | 1,172 | 2.09 | 1,215 | 2,122 | 8,827 | 19,452 | 8,597 | 7,170 |
| c7 | Training | 2024-11-30 | 3,635 | 3,503 | 6,050 | 1,088 | 2.05 | 1,274 | 2,160 | 8,426 | 20,106 | 8,165 | 7,068 |
| c8 | Training | 2024-12-31 | 3,442 | 3,461 | 5,864 | 1,039 | 1.99 | 1,298 | 2,181 | 8,145 | 21,006 | 7,858 | 6,753 |
| c9 | Training | 2025-01-31 | 3,255 | 3,448 | 5,713 | 990 | 1.94 | 1,238 | 2,280 | 7,791 | 21,696 | 7,474 | 6,257 |
| c10 | Training | 2025-02-28 | 3,241 | 3,419 | 5,713 | 947 | 1.94 | 1,269 | 2,358 | 7,897 | 22,803 | 7,541 | 5,563 |
| c11 | Training | 2025-03-31 | 3,472 | 3,609 | 6,064 | 1,017 | 2.06 | 1,289 | 2,215 | 8,721 | 25,288 | 8,331 | 5,910 |
| c12 | Training | 2025-04-30 | 3,572 | 3,769 | 6,290 | 1,051 | 2.13 | 1,322 | 2,299 | 9,053 | 27,119 | 8,710 | 6,147 |
| c13 | Training | 2025-05-31 | 3,594 | 3,877 | 6,404 | 1,067 | 2.17 | 1,270 | 2,360 | 9,136 | 27,758 | 8,797 | 6,235 |
| c14 | Training | 2025-06-30 | 3,565 | 3,983 | 6,473 | 1,075 | 2.20 | 1,163 | 2,433 | 9,028 | 28,289 | 8,706 | 6,360 |
| c15 | Training | 2025-07-31 | 3,543 | 4,054 | 6,513 | 1,084 | 2.21 | 1,086 | 2,439 | 8,913 | 28,564 | 8,602 | 6,437 |
| c16 | Training | 2025-08-31 | 3,536 | 4,118 | 6,576 | 1,078 | 2.23 | 1,071 | 2,457 | 8,860 | 28,753 | 8,560 | 6,508 |
| c17 | Training | 2025-09-30 | 3,550 | 4,158 | 6,649 | 1,059 | 2.26 | 1,111 | 2,483 | 8,911 | 29,056 | 8,607 | 6,527 |
| c18 | Training | 2025-10-31 | 3,536 | 4,232 | 6,726 | 1,042 | 2.28 | 1,213 | 2,543 | 8,935 | 29,164 | 8,639 | 6,561 |
| c19 | Training | 2025-11-30 | 3,531 | 4,286 | 6,779 | 1,038 | 2.30 | 1,260 | 2,562 | 8,846 | 29,281 | 8,555 | 6,600 |
| c20 | Training | 2025-12-31 | 3,577 | 4,248 | 6,811 | 1,014 | 2.31 | 1,281 | 2,566 | 8,825 | 29,592 | 8,537 | 6,465 |
| c21 | Training | 2026-01-31 | 3,638 | 4,358 | 6,977 | 1,019 | 2.37 | 1,314 | 2,705 | 8,924 | 29,697 | 8,634 | 6,576 |
| c22 | Training | 2026-02-28 | 3,652 | 4,438 | 7,072 | 1,018 | 2.40 | 1,357 | 2,820 | 8,866 | 30,009 | 8,576 | 6,703 |
| c23 | Training | 2026-03-31 | 3,637 | 4,531 | 7,169 | 999 | 2.43 | 1,372 | 2,709 | 8,810 | 30,388 | 8,529 | 6,811 |
| c24 | Training | 2026-04-30 | 3,682 | 4,609 | 7,306 | 985 | 2.48 | 1,348 | 2,831 | 8,778 | 30,785 | 8,496 | 6,767 |
| c25 | Testing | 2026-05-31 | 3,727 | 4,710 | 7,428 | 1,009 | 2.52 | 1,304 | 2,936 | 8,842 | 31,059 | 8,538 | 6,823 |
| c26 | Testing | 2026-06-30 | 3,794 | 4,794 | 7,579 | 1,009 | 2.57 | 1,308 | 3,009 | 9,015 | 31,421 | 8,689 | 6,911 |
| c27 | Holdout | 2026-07-31 | 3,886 | 4,881 | 7,720 | 1,047 | 2.62 | 1,324 | 3,070 | 9,205 | 31,683 | 8,873 | 6,984 |
| c28 | Holdout | 2026-08-31 | 3,951 | 4,992 | 7,889 | 1,054 | 2.68 | 1,358 | 3,102 | 9,279 | 32,057 | 8,943 | 7,084 |

What the table shows:

* **Coverage is low and stable:** only 1.9%–2.7% of the universe has any FTP or copay fill in a 12-month lookback. About 97% of the universe will have 0 in every FTP and copay feature.
* **Copay is growing, FTP is flat:** copay HCPs grow from 3,156 (c1) to 4,992 (c28), and copay fills double (15,401 to 32,057). FTP HCPs fall from 4,780 to 3,241 (c10), then recover to 3,951.
* **FTP is one fill per patient; copay is repeat fills:** FTP fills ≈ FTP patients (9,279 fills, 8,943 patients in c28). Copay has about 4.5 fills per patient (32,057 / 7,084).
* **Overlap is small:** about 1,000–1,400 HCPs per cohort have both, so the two programs reach mostly different HCPs.
* **c1 recent window is thin for FTP** (707 HCPs in the last 3 months vs ≈1,000–1,400 elsewhere), because FTP fills were at their lowest in the first half of 2024 (table 1f).

### 1f. Fills per quarter (universe HCPs, by fill date)

| Quarter | FTP | Copay |
| --- | --- | --- |
| 2021-Q3 | 0 | 154 |
| 2021-Q4 | 5,447 | 632 |
| 2022-Q1 | 14,202 | 1,141 |
| 2022-Q2 | 15,393 | 1,997 |
| 2022-Q3 | 11,422 | 2,778 |
| 2022-Q4 | 14,095 | 3,252 |
| 2023-Q1 | 8,691 | 3,681 |
| 2023-Q2 | 4,291 | 4,116 |
| 2023-Q3 | 3,583 | 4,049 |
| 2023-Q4 | 3,557 | 4,591 |
| 2024-Q1 | 1,819 | 2,828 |
| 2024-Q2 | 1,783 | 4,403 |
| 2024-Q3 | 2,110 | 6,728 |
| 2024-Q4 | 2,433 | 7,047 |
| 2025-Q1 | 2,395 | 7,110 |
| 2025-Q2 | 2,090 | 7,404 |
| 2025-Q3 | 1,993 | 7,495 |
| 2025-Q4 | 2,347 | 7,583 |
| 2026-Q1 | 2,380 | 7,906 |
| 2026-Q2 | 2,295 | 8,437 |
| 2026-Q3 | 2,248 | 8,551 |
| 2026-Q4 (to 2026-11-06) | 988 | 3,525 |

FTP volume fell sharply in 2023 and has been about 2,000–2,400 fills per quarter since mid-2024. Copay rose steadily. The 2024-Q1 dip in copay (2,828) is visible in the data; its cause was not checked. Because the level changes over time, the training cohorts (c1–c24) do not all see the same FTP / copay mix as the holdout cohorts.

### 1g. HCP-level distribution (c28 lookback, 2025-09-01 to 2026-08-31, universe HCPs)

| | FTP | Copay |
| --- | --- | --- |
| HCPs with ≥ 1 fill | 3,951 | 4,992 |
| Fills per HCP: p25 / median / p75 / p90 / p99 | 1 / 1 / 2 / 4 / 23 | 2 / 4 / 8 / 13 / 45 |
| Max fills for one HCP | 156 | 308 |
| HCPs with exactly 1 fill | 67.3% | 23.9% |
| Patients per HCP: median / p90 | 1 / 4 | 1 / 3 |
| Total fills | 9,279 | 32,057 |

The distributions are very skewed: most FTP HCPs have a single fill, while a few HCPs have dozens. Counts should be capped or log-transformed, or turned into bands.

### 1h. What the main columns contain (whole table)

| Topic | FTP | Copay |
| --- | --- | --- |
| Strength (NDC `50419-0540` = 10 mg, `-0541` = 20 mg, `-0542` = 40 mg) | 10 mg 83,533; 20 mg 22,361; 40 mg 101 | 10 mg 62,694; 20 mg 43,006; 40 mg 329 |
| Days supply (`DAY_SUPPLY_NUM`): p10 / median / p90 | 30 / 30 / 30 | 30 / 30 / 90 |
| Share of fills with ≥ 84 days supply | 0.0% | 11.6% |
| Fill number (`FILL_NUMBER`, 0 = new Rx): median / p90 | 0 / 2 | 1 / 6 |
| Written → fill days: median / p90 | 12 / 81 | 75 / 245 |
| Fill → load (`INSERT_TS`) days: median / p90 / p95 | 5 / 10 / 14 | 5 / 8 / 11 |
| Share loaded within 14 days of the fill | 95.1% | 96.9% |
| Fills with a fill date before the written date | 0 | 0 |
| Program benefit per fill (`NET_PTNT_BNFT`, USD): p10 / median / p90 | 597.55 / 627.48 / 721.04 | 30.00 / 265.00 / 698.21 |
| Total program benefit (USD) | 67,968,215 | 38,835,144 |
| Patient out-of-pocket (`NET_PATOOP`): median / p90 | 0 / 0 (a single value in the whole table) | 0 / 0 |
| Other coverage code (`OTHR_CVRG_CD`) | `00` 101,140; `03` 2,483; `01` 2,372 | `08` 87,191; `03` 18,838 |
| Patient gender (`PAT_GNDR`) | M 59,263; F 46,732 | M 65,999; F 40,027; U 3 |
| Patient age (`PAT_AGE`): p10 / median / p90 | 53 / 68 / 77 | 45 / 59 / 67 |
| Distinct pharmacies (`PHMCY_NABP`) | 21,848 | 8,031 |
| Dispense as written (`DAW`) | `0` 102,428; `1` 3,391; other 176 | `0` 102,342; `1` 3,367; other 320 |
| Submission method (`SBMSSN_MTHD`) | `E` 105,995 | `E` 106,007; `M` 22 |
| Program group (`GRP_NUM`) | `151194196WF` 28,157; `171194196WF` 26,319; `101194196WF` 22,004; `191194196WF` 19,670; `161194196WF` 9,263; `112194196WF` 333; `181194196WF` 249 | `1BJEOFSFLDF` 96,885; `121194196DF` 7,426; `131194196DF` 1,718 |
| Source rows per claim (`N_SOURCE_ROWS`) | 1: 104,669; 2: 1,325; 3: 1 | 1: 98,826; 2: 7,203 |
| Top MDM specialties | NEP 40,811; FM 22,240; IM 17,834; END 11,693; CD 5,308 | NEP 40,372; FM 24,518; IM 15,579; END 14,845; GP 5,141 |

Patient IDs: `MMBR_ID` and `SHLD_ID` give almost the same patient counts (1c). The build notes say `SHLD_ID` is program-specific, so an FTP patient cannot be followed into copay.

### 1i. All columns: fill rate and how to use them

Fill % = share of rows that are not null and not an empty string. Distinct counts are approximate (`approx_count_distinct`) and are shown only where they matter. Use category:

* **Key**: links the claim to an HCP, patient or claim.
* **Date**: timing.
* **Feature**: can be turned into an HCP feature.
* **Filter / QC**: already applied in the build, or only useful for checks.
* **Do not use**: constant, admin, free text, or a leakage risk.

| Column | Type | FTP fill % | Copay fill % | Use | Notes |
| --- | --- | --- | --- | --- | --- |
| `PROGRAM` | string | 100.00 | 100.00 | Do not use | Constant per table (`FTP` / `COPAY`) |
| `TRNS_ID` | string | 100.00 | 100.00 | Filter / QC | Source transaction ID |
| `INSRT_DT` | string | 100.00 | 100.00 | Do not use | Text version of `INSERT_TS` |
| `EXCLD_CD` | string | 100.00 | 100.00 | Do not use | 1 value |
| `USE_SLS` | string | 100.00 | 100.00 | Filter / QC | Always `Y` (filter already applied) |
| `SHLD_ID` | string | 100.00 | 100.00 | Key | Program-specific patient ID |
| `HCP_ID` | string | 99.88 | 99.88 | Do not use | Source HCP ID; use `PRSC_NPI` |
| `ACCT_ID` | string | 99.88 | 99.88 | Do not use | Source account ID |
| `CLM_AUTH_NUM` | string | 100.00 | 100.00 | Filter / QC | Claim number of the kept row |
| `ORGN_CLM_AUTH_NUM` | string | 100.00 | 100.00 | Key | Original claim: one row each |
| `RX_NUM` | string | 100.00 | 100.00 | Feature | Prescription number: fills per prescription (persistence) |
| `RX_FILL_DT` | string | 100.00 | 100.00 | Do not use | Text version of `RX_FILL_DATE` |
| `RX_DT` | string | 100.00 | 99.98 | Do not use | Text version of `RX_WRITTEN_DATE` |
| `DAY_SUPPLY` | string | 100.00 | 100.00 | Do not use | Text version of `DAY_SUPPLY_NUM` |
| `DAW` | string | 100.00 | 100.00 | Do not use | ~97% `0` |
| `NDC_NUM` | string | 100.00 | 100.00 | Feature | Strength (10 / 20 / 40 mg) and pack (30 / 90) |
| `DRG_DESC` | string | 100.00 | 100.00 | Filter / QC | Same as NDC in words (7 values) |
| `NEW_REFILL_CD` | string | 100.00 | 100.00 | Do not use | Text version of `FILL_NUMBER` |
| `RX_REFILLS` | string | 100.00 | 100.00 | Do not use | Text version of `RX_REFILLS_NUM` |
| `OTHR_CVRG_CD` | string | 100.00 | 100.00 | Feature | Payer situation of the patient; code meanings not checked |
| `GRP_NUM` | string | 100.00 | 100.00 | Filter / QC | Program group (defines `PROGRAM`) |
| `MMBR_ID` | string | 100.00 | 100.00 | Key | Patient ID: distinct patients per HCP |
| `PAT_GNDR` | string | 100.00 | 100.00 | Feature | Patient mix (share female) |
| `PAT_AGE` | string | 85.05 | 98.55 | Feature | Patient mix (share 65+); text, cast needed |
| `PHMCY_NABP` | string | 100.00 | 100.00 | Feature | Pharmacy ID: number of pharmacies per HCP |
| `PHMCY_NM` | string | 100.00 | 100.00 | Do not use | Free text |
| `PHMCY_ADDR_1` | string | 100.00 | 100.00 | Do not use | Free text |
| `PHMCY_ADDR_2` | string | 9.22 | 3.55 | Do not use | Mostly empty |
| `PHMCY_CTY` | string | 100.00 | 100.00 | Do not use | Free text |
| `PHMCY_STATE` | string | 100.00 | 100.00 | Filter / QC | State is already available for the HCP elsewhere |
| `PHMCY_ZIP` | string | 100.00 | 100.00 | Filter / QC | Possible pharmacy-distance work later |
| `PRSC_NPI` | string | 99.96 | 99.96 | Key | Join key to the universe (through the mapping) |
| `PRSC_NM` | string | 99.98 | 99.90 | Do not use | Name |
| `PRSC_FIRST_NM` | string | 99.94 | 99.88 | Do not use | Name |
| `PRSC_MID_INT_NM` | string | 62.64 | 22.37 | Do not use | Name |
| `PRSC_LAST_NM` | string | 99.98 | 99.90 | Do not use | Name |
| `PRSC_SFFX` | string | 0.18 | 0.06 | Do not use | Almost empty |
| `PRSC_PRFSN_DSG` | string | 68.39 | 23.86 | Do not use | Patchy (MD / NP / PA); use HCP master data instead |
| `PRSC_SPCLTY_1` | string | 95.77 | 90.49 | Do not use | Specialty comes from HCP master data in 3.1 |
| `PRSC_SPCLTY_2` | string | 11.99 | 4.51 | Do not use | Mostly empty |
| `PRSC_ADDR_1` | string | 99.93 | 99.88 | Do not use | Address |
| `PRSC_ADDR_2` | string | 41.61 | 15.55 | Do not use | Address |
| `PRSC_CTY` | string | 99.93 | 99.88 | Do not use | Address |
| `PRSC_STATE` | string | 99.93 | 99.88 | Do not use | Address |
| `PRSC_ZIP` | string | 99.94 | 99.88 | Do not use | Address |
| `SBMSSN_MTHD` | string | 100.00 | 100.00 | Do not use | Almost all `E` |
| `QTY` | string | 100.00 | 100.00 | Do not use | Text version of `QTY_NUM` |
| `PTNT_BNFT` | string | 100.00 | 100.00 | Do not use | Use `NET_PTNT_BNFT` (clawbacks netted) |
| `PTNT_COPAY` | string | 100.00 | 100.00 | Do not use | Use `NET_PTNT_COPAY` |
| `PATOOP` | string | 100.00 | 100.00 | Do not use | Use `NET_PATOOP` |
| `PHMCY_TRANS_FEE` | double | 100.00 | 100.00 | Do not use | Program fee, no HCP meaning |
| `OTHR_PYR_BIN_NM_PRMY` | string | 4.33 | 27.34 | Do not use | Patchy; primary payer name |
| `CO_B_PRMY_OTHR_PYR_ID_BIN` | string | 2.34 | 100.00 | Feature (copay only) | Primary payer BIN of copay patients: payer mix per HCP; mapping BIN → payer not checked |
| `DATA_DT` | string | 100.00 | 100.00 | Do not use | 1 value |
| `BU_NM` | string | 100.00 | 100.00 | Do not use | 1 value |
| `SRC_SYS_CD` | string | 100.00 | 100.00 | Do not use | 1 value (`PRM`) |
| `PROD_CD` | string | 100.00 | 100.00 | Do not use | 1 value |
| `BTCHADT_ID_SK` | decimal | 100.00 | 100.00 | Do not use | 1 value |
| `JOBADT_ID_SK` | decimal | 100.00 | 100.00 | Do not use | 1 value |
| `CRTD_DT` | string | 100.00 | 100.00 | Do not use | 1 value |
| `MDFD_DT` | string | 100.00 | 100.00 | Do not use | 1 value |
| `RX_FILL_DATE` | date | 100.00 | 100.00 | Date | **Feature date** (pickup); use ≤ cutoff |
| `FILL_MONTH` | date | 100.00 | 100.00 | Date | Month of `RX_FILL_DATE` |
| `RX_WRITTEN_DATE` | date | 100.00 | 99.98 | Date / Feature | Not a feature date (leakage); usable for written → fill lag |
| `INSERT_TS` | timestamp | 100.00 | 100.00 | Date | Load time: point-in-time check (fill known by the cutoff) |
| `DAY_SUPPLY_NUM` | double | 100.00 | 100.00 | Feature | Patient-days on therapy; 90-day share |
| `QTY_NUM` | double | 100.00 | 100.00 | Do not use | Tablets; same information as supply |
| `RX_REFILLS_NUM` | int | 100.00 | 100.00 | Feature | Refills authorized: intended length of therapy |
| `FILL_NUMBER` | int | 100.00 | 100.00 | Feature | 0 = new, 1..n = refill number: refill share, persistence |
| `IS_NEW_RX` | boolean | 100.00 | 100.00 | Feature | New-patient starts |
| `N_SOURCE_ROWS` | bigint | 100.00 | 100.00 | Filter / QC | Rows netted into the claim; do not use as a weight |
| `N_BENEFIT_ADJ_ROWS` | bigint | 100.00 | 100.00 | Filter / QC | Clawback rows |
| `NET_PTNT_BNFT` | double | 100.00 | 100.00 | Feature (careful) | Benefit paid (USD); netted with clawbacks known at rebuild time |
| `NET_PTNT_COPAY` | double | 100.00 | 100.00 | Feature (careful) | For copay: copay before the card (affordability) |
| `NET_PATOOP` | double | 100.00 | 100.00 | Do not use | FTP: a single value; copay: median and p90 are 0 |
| `NET_PHMCY_TRANS_FEE` | double | 100.00 | 100.00 | Do not use | Program fee |
| `IS_BENEFIT_CLAWED_BACK` | boolean | 100.00 | 100.00 | Do not use as a feature | No date for the clawback: leakage |
| `IS_ZERO_NET_BENEFIT` | boolean | 100.00 | 100.00 | Do not use as a feature | Same reason |
| `BH_ID` | string | 99.95 | 99.95 | Key | Alternative join key (same result as NPI, 1d) |
| `MDM_FIRST_NAME` | string | 99.95 | 99.95 | Do not use | Name |
| `MDM_LAST_NAME` | string | 99.95 | 99.95 | Do not use | Name |
| `MDM_SPECIALTY` | string | 99.95 | 99.95 | Do not use as a feature | Current MDM snapshot, not as of the cohort date |
| `REFRESH_TS` | timestamp | 100.00 | 100.00 | Filter / QC | Rebuild time (1 value) |

**In short:** of 83 columns, 4 are keys (`ORGN_CLM_AUTH_NUM`, `PRSC_NPI` / `BH_ID`, `MMBR_ID` / `SHLD_ID`), 4 are dates, and about 16 can feed HCP features. The rest is constant, admin, name or address text, or a text copy of a typed column.

### 1j. Possible features

Built per program (FTP and copay), on windows of 3 and 12 months ending at the cutoff.

| Feature | Columns | Programs | New in 3.1 / same as 3.0 | Why it is kept |
| --- | --- | --- | --- | --- |
| Has any FTP / copay fill | `RX_FILL_DATE` | FTP, copay | New in 3.1 | Separates "no program activity" from "low activity" for the large majority of HCPs with no fill |
| Fills per window | `RX_FILL_DATE` | FTP, copay | FTP: same as 3.0 (`TOTAL_RX_FTP_IN_LAST_*_MONTH`), now by fill date and 1 per claim. Copay: new in 3.1 (not in the 3.0 model) | Core program volume |
| New-Rx fills per window | `IS_NEW_RX` | FTP, copay | New in 3.1 | New-patient starts through the programs |
| Days since last fill | `RX_FILL_DATE` | FTP, copay | New in 3.1 | Recency of program use |
| Average copay before the card | `NET_PTNT_COPAY` | Copay only | New in 3.1 | Patient affordability; not available from any other 3.1 source |

Other ideas (persistence, trend, dose, patient-days, written → fill lag, payer mix, patient mix, pharmacy count) are deprioritised.

---

## Summary

* **Same data, cleaner form:** at the 3.0 load cut-off, the UC tables hold exactly the same number of claims that 3.0 kept (105,361 FTP, 103,983 copay), already de-duplicated, with typed dates and netted money.
* **Same HCPs:** the 3.1 universe adds 73,733 providers, but almost no FTP or copay HCPs (29 FTP, 9 copay in c28). About 2.7% of the 3.1 universe has any program fill.
* **Main change for features:** pickup date instead of written date. For copay this roughly triples the number of HCPs with a fill in a given month.
* **New features (1j):** a "has any FTP / copay" flag, fills per window (by fill date), new-Rx fills, days since last fill, and the average copay before the card (copay only). Only the FTP fill counts were in the 3.0 model, and there they were counted by written date.
