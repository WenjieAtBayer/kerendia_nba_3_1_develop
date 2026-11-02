# Competitor & Comorbidity Features: Summary, Trends, and NBA 3.1 Opportunities

This document summarises the two feature families most directly tied to the Kerendia indication landscape: (1) **comorbidity / patient-panel features** (how many patients with kidney disease, diabetic CKD, or cardio-renal CKD an HCP sees each month) and (2) **competitor drug NBRx share features** (how the HCP’s SGLT2 prescribing is distributed across Farxiga, Invokana, Jardiance, and Steglatro). It covers the NBA 3.0 status of each, what the data shows over the two years to October 2026, structural issues identified, and the highest-value NBA 3.1 improvements.

Detailed per-family analysis and change specs are in files `01–02` (comorbidity) and `09–10` (competitor). The adoption-speed features (Invokana / Farxiga adoption, files `03–04`) are adjacent to the competitor family and are summarised briefly here.

---

## 1. NBA 3.0 Status at a Glance

### 1.1 Comorbidity features (notebook `09_claim_comorbidity`)

**What they measure.** For every HCP and calendar month, the number of patients the HCP billed a kidney-related diagnosis for, split into three groups:
- `KD`: kidney disease only (CKD stages, hypertensive CKD, ESRD, dialysis)
- `DB-KD`: diabetic kidney disease (T2D with CKD/nephropathy)
- `CV-KD`: hypertensive heart and CKD (cardio-renal)

**Feature families built (39 columns total):**

| Family | Columns | NBA 3.0 model kept | SHAP share |
| --- | --- | --- | --- |
| Monthly patient count | 4 | 0 | 0.00% |
| Rolling average (1/3/6/12M) | 16 | 0 | 0.00% |
| Running total (since 2021) | 4 | 2 | 0.29% |
| Group share (1/3/6/12M) | 15 | 1 | 0.25% |
| **Total** | **39** | **3** | **0.54%** |

**Features in the final 752-feature model:**

| SHAP rank | Feature | Note |
| --- | --- | --- |
| 88 | `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` | Inverse signal: high CV-KD share → fewer Kerendia writers (small panel effect) |
| 133 | `RUNNING_TOTAL_DX_PATIENTS_DB_KD` | Total patient-months of diabetic CKD since 2021 |
| 237 | `RUNNING_TOTAL_DX_PATIENTS_KD` | Total patient-months of kidney disease since 2021 |

**Source:** `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX` + `PHCDW.PHCDW_SANDBOX.FIN_DIAG_CD` grouping table

---

### 1.2 Competitor NBRx share features (notebook `31_Competitor_drugs_NBRX_share`)

**What they measure.** For every HCP and calendar month, the 12-month rolling NBRx count and percentage share for four SGLT2 drugs (Farxiga, Invokana, Jardiance, Steglatro). Shares sum to 1 per HCP.

**Feature list (9 columns output):**
- `TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` (total of 4 drugs)
- `TOTAL_NBRX_CLAIMS_{DRUG}_IN_LAST_12_MONTH` for each of 4 drugs
- `PERC_{DRUG}_NBRX_SHARE` for each of 4 drugs

**Model importance:** Not confirmed against the 752-feature Excel for this document. Feature names to verify: `PERC_FARXIGA_NBRX_SHARE`, `PERC_JARDIANCE_NBRX_SHARE`, `TOTAL_NBRX_CLAIMS_*_IN_LAST_12_MONTH`.

**Source:** `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` (IQVIA projected weekly NBRx, all indication groups)

---

### 1.3 Adoption-speed features (notebook `11_adoption_features_inv_far`)

**What they measure.** For every HCP, the minimum number of days from a patient’s first CKD diagnosis (from this HCP) to the patient’s first Invokana or Farxiga Rx from this HCP. A low value signals a fast SGLT2 adopter.

| SHAP rank | Feature | SHAP share |
| --- | --- | --- |
| 13 | `TIME_TO_ADOPT_FARXIGA` | **1.10%** — one of the strongest HCP-level claim features in the model |

Invokana was dropped (only 17,529 HCPs have a value; too sparse).

---

## 2. Competitor Drug Market Trend (Nov 2024 – Sep 2026)

Data source: `KERENDIA_LAAD_BASED_LRX_V6`, PERIOD_TYPE = W, all indication groups. Monthly NBRx in thousands.

| Month | Farxiga (K) | Jardiance (K) | Kerendia (K) | Invokana (K) | Steglatro (K) |
| --- | --- | --- | --- | --- | --- |
| Nov 2024 | 93.6 | 162.5 | 6.3 | 1.6 | 1.3 |
| Feb 2025 | 128.5 | 190.6 | 7.1 | 2.5 | 1.4 |
| May 2025 | 96.5 | 173.8 | 6.9 | 1.3 | 1.2 |
| Aug 2025 | 93.6 | 164.9 | 7.5 | 1.1 | 1.1 |
| Nov 2025 | 89.8 | 159.1 | 8.7 | 1.0 | 0.9 |
| Feb 2026 | 147.4 | 136.7 | 6.6 | 0.7 | 0.7 |
| May 2026 | **373.3** | 162.0 | 8.7 | 0.8 | 0.7 |
| Aug 2026 | 290.9 | 133.6 | 9.4 | 0.7 | 0.5 |
| Sep 2026 | 195.6 | 93.4 | 7.1 | 0.5 | 0.3 |

**Key observations:**

1. **Farxiga generic surge.** Farxiga (brand + generic) volume roughly doubled from late 2025 into 2026, driven by the generic dapagliflozin launch. The NBA 3.0 notebook uses `LIKE '%FARXIGA%'` which captures both `FARXIGA BRAND` and `FARXIGA GENERICS`, so the feature correctly reflects this growth. However, the share denominator now includes a much larger Farxiga volume, which mechanically depresses the Jardiance share even if Jardiance prescribing did not change.

2. **Jardiance relatively stable.** Monthly NBRx ranges from ~93K (Sep 2026, which appears partially incomplete) to ~191K. The seasonal dip in Q2 and Q4 is consistent across years. Jardiance is consistently the largest single branded SGLT2 in the market.

3. **Kerendia growing modestly.** Monthly NBRx grew from ~6.3K (Nov 2024) to ~9.4K (Aug 2026), a ~49% increase over two years. HCPs writing Kerendia grew from ~17.8K to ~28.3K over the same period. This growth is meaningful but from a very small base relative to Jardiance (≈6% of Jardiance’s volume).

4. **Invokana and Steglatro declining to near-zero.** Invokana dropped from 1.6K to <0.5K per month; Steglatro from 1.3K to <0.3K. Both remain in the NBA 3.0 feature denominator, diluting it without contributing signal.

5. **Indication scope caveat.** For Oct 2025–Sep 2026, the INDICATION_GROUP breakdown shows:
   - Jardiance: ~15% of NBRx labeled CKD-containing; ~40% T2D+CVD or T2D, ~12% HF-related
   - Farxiga: ~32% labeled CKD-containing; ~40% T2D+CVD or T2D, ~16% HF (CVD+HF, T2D+CVD+HF, CKD+CVD+HF)
   - Kerendia: ~57% labeled CKD-containing + multi-indication; ~24% T2D alone or T2D+CVD
   This means NBA 3.0’s competitor share features are heavily influenced by non-CKD prescribing. A Jardiance share of 0.6 could mean either an active CKD Jardiance user or simply a high-volume T2D prescriber.

---

## 3. Comorbidity Feature Trend (Nov 2024 – Jun 2026)

Data source: NBA 3.0 comorbidity output at `/Volumes/.../kerendia_nba_3_hcp_model_claim_comorbidity_for_inference`. 228,582 HCPs. Monthly averages over HCPs with a non-null value.

| Month | Avg total Dx (12M) | Avg DB-KD (12M) | Avg KD (12M) | Avg CV-KD (12M) | Avg CV-KD share (12M) |
| --- | --- | --- | --- | --- | --- |
| Nov 2024 | 9.19 | 3.85 | 7.24 | 2.14 | 0.422 |
| Feb 2025 | 9.15 | 3.87 | 7.19 | 2.14 | 0.429 |
| May 2025 | 9.27 | 3.93 | 7.28 | 2.17 | 0.431 |
| Aug 2025 | 9.37 | 3.98 | 7.35 | 2.19 | 0.431 |
| Nov 2025 | 9.45 | 4.00 | 7.41 | 2.20 | 0.432 |
| Feb 2026 | 9.56 | 4.06 | 7.49 | 2.22 | 0.432 |
| May 2026 | 9.65 | 4.09 | 7.56 | 2.23 | 0.431 |
| Jun 2026 | 9.67 | 4.11 | 7.57 | 2.23 | 0.431 |

**Key observations:**

1. **Slow, steady growth across all groups.** The average HCP’s kidney-patient panel grew by ~5% over 19 months (9.19 → 9.67 total Dx patients per active month). This reflects both growing diagnosis rates and HCP practice expansion.

2. **DB-KD (diabetic CKD) growing the fastest in absolute terms** (+0.26 patients/month, ~7% increase). This is the core Kerendia T2D+CKD indication group and is on an upward trend, supporting the hypothesis that more HCPs are identifying and coding T2D+CKD patients.

3. **CV-KD share is stable at ~0.43** (the model’s top comorbidity feature, rank 88, with inverse signal: a higher share correlates with fewer Kerendia writers). This stability means the signal from this feature will not change materially with a data refresh, but also that the underlying practice pattern is not shifting.

4. **CKD stage 3 is significantly under-represented.** The `FIN_DIAG_CD` table used in NBA 3.0 is missing ICD-10 codes N18.30, N18.31, N18.32 (CKD stage 3a and 3b), which have been the correct billing codes since October 2020. The NBA 3.0 data shows only 23,981 patients coded as stage 3 (N18.3 only), against 10.47M for stage 4 group. Most stage 3 patients appear only through their hypertensive CKD or diabetic CKD codes.

---

## 4. Structural Issues and Root Causes

### 4.1 Comorbidity

| Issue | Severity | Root cause |
| --- | --- | --- |
| CKD stage 3 almost absent (26,200 patients vs 10.47M for stage 4) | High | `FIN_DIAG_CD` missing N18.30/31/32 codes (post-2020 billing standard) |
| No HF or T1D groups — invisible to the model | High | `FIN_DIAG_CD` only groups kidney codes. HF and T1D codes are not included |
| Rolling averages skip empty months (inflation for low-volume HCPs) | Medium | `step3_lag_avg` uses `AVG` which ignores nulls, not a sum over a fixed period |
| Windows are one month longer than named (`_IN_LAST_12_MONTH` = 13 months) | Medium | `rowsBetween(-i, 0)` counts current row + i prior rows |
| Shares can be above 1.0 (1,862 HCPs for CV-KD 12M share) | Medium | Numerator and denominator skip different empty months; groups also overlap |
| Running totals grow every run and are not comparable across cohorts | Medium | Fixed data start date (Jan 2021) + unbounded window |
| Single-month counts are noisy (0.96 correlation with 1M rolling avg) | Low | Calendar timing, not prescribing pattern |

### 4.2 Competitor NBRx share

| Issue | Severity | Root cause |
| --- | --- | --- |
| All indication groups, not CKD-specific | High | No `INDICATION_GROUP` filter in the LRx query |
| Static build — potential training data leakage | High | No cohort window; uses full claims history for every training cohort |
| Denominator is only 4 SGLT2s, not the full CKD therapeutic landscape | Medium | Drug list limited to SGLT2 competitors; no MRA, RAAS, or other drug classes |
| Invokana and Steglatro near-zero by 2026 | Medium | Market dynamics; both drugs declined sharply after generic competition |
| Only 12-month window, no shorter trend feature | Medium | `last_i_month_list = [12]` hard-coded |
| Farxiga share volatile due to generic launch in 2025–2026 | Medium | Farxiga generic volumes entered the denominator abruptly; share now partly reflects generic vs brand dynamics, not only prescribing preference |

---

## 5. NBA 3.1 Improvements: Priority List

### High priority (quick wins with expected model lift)

| # | Improvement | Family | Expected value |
| --- | --- | --- | --- |
| H1 | Add CKD stage 3 codes (N18.30/31/32) to the Dx event list | Comorbidity | CKD stage 3 share is the top Dx feature in the backtest for within-size signal (AUC in size 0.685). Currently the entire stage 3 population is mis-classified as stage 4 or only captured through their comorbidity codes |
| H2 | Add indication-mix features (T2D+CKD, T1D+CKD, HF proxy, any indication) | Comorbidity | New writer AUC 0.54–0.59 vs 0.505 for the best NBA 3.0 comorbidity feature. The model sees HF and T1D for the first time |
| H3 | Add CKD stage 4 share | Comorbidity | Highest AUC in size of all Dx features (0.704) |
| H4 | Rebuild competitor share features with CKD-filtered indication scope | Competitor | Currently ~85% of Jardiance and ~68% of Farxiga NBRx in the feature comes from non-CKD patients. A CKD-scoped Jardiance share should be a better Kerendia adoption signal |
| H5 | Fix competitor feature static build — use cohort windows | Competitor | Prevents leakage; makes training and inference consistent |

### Medium priority (worth building; model selection will decide)

| # | Improvement | Family | Expected value |
| --- | --- | --- | --- |
| M1 | Replace running totals with fixed 24-month distinct-patient counts | Comorbidity | Removes data-start dependence; better signal for new writers (AUC 0.53 vs 0.50) |
| M2 | Replace rolling averages with distinct patients in 90 and 365 days | Comorbidity | Semantics become clear (“patients” not “patient-months”); drops 14 redundant columns |
| M3 | Add log-ratio of indicated patients (3M vs prior 9M) | Comorbidity | Growth signal for a rising indicated panel (AUC 0.629, in size 0.578) |
| M4 | Add steroidal MRA (spironolactone + eplerenone) NBRx share in CKD scope | Competitor | HCPs who already prescribe MRAs for CKD are the closest to adding Kerendia; signal 0.64 AUC for the adoption-speed version |
| M5 | Add 3-month window for competitor Jardiance/Farxiga share | Competitor | Captures momentum changes from label updates or promotional activity |
| M6 | Expand adoption-speed to Jardiance, steroidal MRA, and Entresto (fix 03–04) | Adoption speed | Jardiance #3 AUC 0.679; Entresto best for new writers (0.585) |

### Lower priority

| # | Improvement | Family | Note |
| --- | --- | --- | --- |
| L1 | Drop single-month Dx counts (4 columns) and 1/3/6M window shares (9 columns) | Comorbidity | None are in the 752; high correlations with remaining features |
| L2 | Drop Invokana and Steglatro from competitor denominator, or mark as low-priority in selection | Competitor | Both near-zero by 2026. Keep in drug list for completeness but set low selection priority |
| L3 | Drop this notebook’s IQVIA channel features (05–06) | Channel | Superseded 0.94–0.99 by `1_Additional_HCP_level_features`, which is already in the 752 |

---

## 6. Summary Table: NBA 3.0 → NBA 3.1 Column Change

| Family | NBA 3.0 columns | Drop | Rebuild / keep | Add new | NBA 3.1 target |
| --- | --- | --- | --- | --- | --- |
| Comorbidity / Dx | 39 | 30 | 2 (running totals, fixed window) + 1 (12M share, rebuilt) | 12 (indication mix × NUM+PCT, stage shares, log-ratio) | ~15 |
| Competitor NBRx share | 9 | 3 (Invokana/Steglatro shares + total count) | 3 (Jardiance + Farxiga 12M share + count, CKD-scoped) | ~12 (CKD scope, 3M window, steroidal MRA) | ~15 |
| Adoption speed | 2 | 1 (TIME_TO_ADOPT_INVOKANA) | 1 (TIME_TO_ADOPT_FARXIGA, renamed + cohort-fixed) | 13 (3 variants × 4–5 drugs) | 14 |

---

## 7. Open Questions

| ID | Question | Owner |
| --- | --- | --- |
| Q1 | Confirm the `FIN_DIAG_CD` staging table is updated or replaced. Is `Kerendia NBA 3.1 - Dx Event List.csv` the authoritative replacement? | Data engineering |
| Q2 | Should the HF LVEF ≥ 40% proxy (I50.3x and no I50.2x) be approved by Medical before building? | Medical / BA |
| Q3 | Are the competitor share features currently in the 752-feature model? (check `Final NBA 3.0 Modeling Features.xlsx`) | Modelling team |
| Q4 | For the CKD-scoped competitor features, which INDICATION_GROUP values should be included? Proposed list: CKD, T2D+CKD, T2D+CKD+CVD, T2D+CKD+HF, T2D+CKD+CVD+HF, CKD+CVD, CKD+HF, CKD+CVD+HF. Any others? | BA / Medical |
| Q5 | Should generic dapagliflozin be explicitly added to the Farxiga product group in the LRx pull, or is the LIKE '%FARXIGA%' filter sufficient? (Currently `FARXIGA GENERICS` is the IQVIA label; check if this changes again with wider generic availability.) | Data engineering |
