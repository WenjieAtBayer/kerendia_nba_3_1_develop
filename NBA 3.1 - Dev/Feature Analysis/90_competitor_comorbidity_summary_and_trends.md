# Competitor & Comorbidity Features: Summary, Trends, and NBA 3.1 Opportunities

> **Data source update (Nov 2026):** NBA 3.1 now reads `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (LAAD-based LRx V7, weekly, history from Dec 2021) instead of `KERENDIA_LAAD_BASED_LRX_V6` and `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021`. Read V6 references below as V7. V7 `WEEK_ENDING_DATE` / `PERIOD_ID` are DATEs, and `PRODUCT_GROUP` uses the shorter lrx_nbrx names. Numbers in this document were computed on V6.

This document summarises the two feature families most directly tied to the Kerendia indication landscape: (1) **comorbidity / patient-panel features** (how many patients with kidney disease, diabetic CKD, or cardio-renal CKD an HCP sees each month) and (2) **competitor drug NBRx share features** (how the HCP’s SGLT2 prescribing is distributed across Farxiga, Invokana, Jardiance, and Steglatro). It covers the NBA 3.0 status of each, what the data shows over the two years to October 2026, structural issues identified, and the highest-value NBA 3.1 improvements.

Detailed per-family analysis and change specs are in files `01–02` (comorbidity) and `09–10` (competitor). The adoption-speed features (Invokana / Farxiga adoption, files `03–04`) are adjacent to the competitor family and are summarised briefly here.

*This document was updated in November 2026 to incorporate competitive intelligence from the internal CI Report (Joshua Buffington, 9/24/26), which provides the market context for why the existing features are insufficient and what new signals NBA 3.1 should capture.*

---

## 0. Why the Existing Features Are Insufficient: Competitive Context

NBA 3.0's competitor and comorbidity features were designed around a static picture of the CKD market in 2022–2023. The competitive landscape in 2026 has changed materially on five dimensions, each pointing to specific feature gaps.

### 0.1 The SGLT2 market was restructured by generic dapagliflozin (April 2026 LOE)

Farxiga lost exclusivity on April 6, 2026. Generic dapagliflozin entered at roughly \$40/month, pulling SGLT2 out-of-pocket costs sharply lower. Our trend data (Section 2) confirms this: Farxiga NBRx surged from ~90K to ~373K in a single month, then stabilised above 280K — purely from generic volume, not new brand prescribing.

**Feature impact.** NBA 3.0's `PERC_FARXIGA_NBRX_SHARE` now blends brand advocacy (early SGLT2 adopter signal) with generic cost-driven prescribing (very different HCP behaviour). An HCP who shifted their T2D patients to cheap generic dapagliflozin will look identical in the feature to one who has used brand Farxiga for CKD patients for years. Neither is distinguished by the current feature because (a) no indication-group filter separates CKD from T2D use, and (b) the IQVIA labels `FARXIGA BRAND` and `FARXIGA GENERICS` are collapsed into one group.

**Positive signal for Kerendia.** The CI report notes this as a HIGH-impact opportunity: lower polypharmacy cost reduces the objection to adding Kerendia. An HCP's patients whose SGLT2i cost just fell by \$100+/month now have more budget headroom for Kerendia. A feature tracking the OOP cost environment or the generic transition timing for the HCP's patients could eventually quantify this.

### 0.2 Entresto went generic (July 2025) — a new HF adoption signal

Entresto (sacubitril/valsartan) lost exclusivity in July 2025, with generics available at ~\$40/month. HCPs who adopted Entresto early — before the LOE, when it was expensive — are archetypal early adopters of evidence-based HF therapy. These are exactly the HCPs NBA 3.1 needs to identify for its new HF (LVEF ≥ 40%) indication.

NBA 3.0 built the `TIME_TO_ADOPT_FARXIGA` adoption feature (rank 13, 1.10% SHAP) which proved very powerful. The same logic applied to Entresto captures the HF-practice dimension that the current feature set entirely lacks.

### 0.3 Baxfendy (baxdrostat) is now a live competitor — and NBA 3.0 cannot see it

AstraZeneca's baxdrostat (Baxfendy) was approved for resistant hypertension in May 2026. As of the CI report date:
- 4,712 HCPs have prescribed it; 898 weekly NBRx and climbing
- 71% of prescribers are PCPs, 41% are outside our targeted segment
- Sits at Step 4 (resistant HTN after three first-line agents fail) — **later-line than Kerendia today**
- AstraZeneca's BaxDuo-CKD trial (baxdrostat + dapagliflozin) reads out ~Feb 2028; BaxDuo-Pacific (5,000 patients) ~2029

Baxfendy prescribers fall into two NBA-relevant groups: (a) Kerendia-segment HCPs who are already managing aldosterone-pathway disease — a high-propensity group — and (b) non-target PCPs outside our footprint who may accumulate MRA-class experience. NBA 3.0 has no Baxfendy feature whatsoever. By the time NBA 3.2 is trained, Baxfendy could have a CKD indication, making this gap more serious.

**Steroidal MRA parallel.** The CI report confirms that the ACC ECDP HFpEF algorithm allows steroidal MRAs (spironolactone, eplerenone) as a cost/tolerance alternative to nsMRAs. HCPs who already prescribe spironolactone or eplerenone for CKD/HF patients are the closest analogue to Kerendia adopters — exactly the signal the adoption-speed recommendations (file 04) propose. The CI report validates this direction independently.

### 0.4 EASi-KIDNEY failed — but the ASI threat resurfaces in 2028

Boehringer's vicadrostat EASi-KIDNEY trial was discontinued for **futility** on September 15, 2026. This is a clear near-term positive: no ASI holds hard-outcome CKD data. Kerendia has an uncontested runway until roughly February 2028 (BaxDuo-CKD readout). However:
- Three Boehringer EASi studies continue in HF (EASi-HF Preserved, EASi-HF Reduced, EASi-PROTKT)
- ASI trials **exclude MRAs from enrollment**, affecting 19% of US zip codes and 54,100 patients globally
- NBRx in affected zip codes is currently tracking non-affected areas (low drag), but this could change if an ASI reaches a hard endpoint

**Geographic feature implication.** The CI report identifies a geographic trial enrollment effect. A zip-code-level trial enrollment flag (is the HCP's practice area an active ASI trial site?) could serve as a risk/opportunity signal in NBA 3.1.

### 0.5 GLP-1 guideline upgrades create an incretin competitor for the HFpEF prescribing moment

The 2026 ESC and ACC guidelines both recommend semaglutide or tirzepatide in HFpEF at BMI ≥ 30, though neither carries an FDA HF indication — prescribing remains off-label. Wegovy OOP cost has risen above \$490/90 days, constraining adoption. Finerenone's Class I FDA-approved HF indication (LVEF ≥ 40%) is a stronger positioning.

**Feature implication.** HCPs who prescribe GLP-1 (Ozempic, Wegovy, Mounjaro/Zepbound) in HF-relevant patient populations are treating the same comorbid profile (obese HFpEF with T2D) that Kerendia now covers. Tracking GLP-1 prescribing with HF-linked indications is a new signal NBA 3.0 cannot see.

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

1. **Farxiga generic surge (Farxiga LOE: April 6, 2026).** Generic dapagliflozin entered at ~\$40/month, causing Farxiga NBRx to surge from ~90K to ~373K in May 2026, then stabilise above 280K. The NBA 3.0 notebook uses `LIKE '%FARXIGA%'` capturing both `FARXIGA BRAND` and `FARXIGA GENERICS`, so the raw count reflects this growth. However, the share denominator now includes massive generic volume, mechanically depressing the Jardiance share even if Jardiance prescribing was flat. More critically, the feature no longer distinguishes brand Farxiga advocacy (early CKD SGLT2 adopter) from generic dapagliflozin cost-switching (broad T2D use).

2. **Jardiance relatively stable.** Monthly NBRx ranges from ~93K (Sep 2026, which appears partially incomplete) to ~191K. The seasonal dip in Q2 and Q4 is consistent across years. Jardiance is consistently the largest single branded SGLT2 in the market.

3. **Kerendia growing modestly.** Monthly NBRx grew from ~6.3K (Nov 2024) to ~9.4K (Aug 2026), a ~49% increase over two years. HCPs writing Kerendia grew from ~17.8K to ~28.3K over the same period. This growth is meaningful but from a very small base relative to Jardiance (≈6% of Jardiance’s volume).

4. **Invokana and Steglatro declining to near-zero.** Invokana dropped from 1.6K to <0.5K per month; Steglatro from 1.3K to <0.3K. Both remain in the NBA 3.0 feature denominator, diluting it without signal.

5. **Baxfendy (baxdrostat) is absent from all features.** As of the CI report (9/24/26), 4,712 HCPs have prescribed Baxfendy (898 weekly NBRx, growing). It is not in `KERENDIA_LAAD_BASED_LRX_V6` under any of the four tracked product groups. NBA 3.0 has no visibility into this emerging MRA-class competitor.

6. **Indication scope caveat.** For Oct 2025–Sep 2026, the INDICATION_GROUP breakdown shows:
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

### New features motivated by the CI report

The CI report (Section 0) identifies five competitive developments that translate directly into new feature candidates. These are additive to the priority list above.

| # | Feature / Signal | Source | CI motivation | Effort |
| --- | --- | --- | --- | --- |
| C1 | `PERC_FARXIGA_BRAND_NBRX_SHARE_CKD` vs `PERC_FARXIGA_GENERIC_NBRX_SHARE_CKD` | LRx (`FARXIGA BRAND` / `FARXIGA GENERICS` separately, CKD-scoped) | Farxiga LOE Apr 2026 mixed the brand-adoption signal with generic cost-switching. Splitting by IQVIA label recovers the early-adopter signal | Quick win (label split already in data) |
| C2 | `TIME_TO_ADOPT_ENTRESTO` and `MIN_DAYS_TO_PRESCRIBE_ENTRESTO_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP` | LAAD Rx (`Rx_01_new`) | Entresto LOE Jul 2025. HCPs who adopted Entresto early are archetypal evidence-based HF adopters. Same logic as `TIME_TO_ADOPT_FARXIGA` (rank 13, 1.10% SHAP) applied to the HF indication population (already included in adoption file 04) | Quick win (adoption notebook already extended) |
| C3 | `PERC_BAXFENDY_NBRX_SHARE` / `TIME_TO_ADOPT_BAXFENDY` | LRx (`BAXFENDY` or `BAXDROSTAT`) | 4,712 HCPs already prescribing Baxfendy (898 weekly NBRx). Early Baxfendy adopters are MRA-class-aware; 20% are in Kerendia Segment A. NBA 3.0 cannot see them at all. By the time NBA 3.2 is trained, Baxfendy may have a CKD indication | Medium (confirm product in LRx feed first) |
| C4 | GLP-1 NBRx with HF-labeled indication | LRx (semaglutide, tirzepatide, INDICATION_GROUP contains HF) | ESC/ACC 2026 guidelines both name semaglutide/tirzepatide in HFpEF. HCPs prescribing GLP-1 in HF patients treat the same obese HFpEF + T2D profile now covered by Kerendia's new HF indication | Medium |
| C5 | ASI trial zip-code enrollment flag | ClinicalTrials.gov zip codes joined to HCP zip | ASI trials exclude MRAs, affecting 19% of US zip codes. Flagging HCPs in active trial zones identifies either at-risk patients (temporarily ineligible) or post-trial opportunity pools | Low (requires external data) |

*C1 and C2 are the highest-priority CI-motivated additions and both reuse existing infrastructure.*

---

## 6. Summary Table: NBA 3.0 → NBA 3.1 Column Change

| Family | NBA 3.0 columns | Drop | Rebuild / keep | Add new | NBA 3.1 target |
| --- | --- | --- | --- | --- | --- |
| Comorbidity / Dx | 39 | 30 | 2 (running totals, fixed window) + 1 (12M share, rebuilt) | 12 (indication mix × NUM+PCT, stage shares, log-ratio) | ~15 |
| Competitor NBRx share | 9 | 3 (Invokana/Steglatro shares + total count) | 3 (Jardiance + Farxiga 12M share + count, CKD-scoped) | ~14 (CKD scope, 3M window, steroidal MRA, brand/generic split [C1], Baxfendy [C3], GLP-1 HF [C4]) | ~17 |
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
| Q6 | Is Baxfendy (baxdrostat) yet visible in `KERENDIA_LAAD_BASED_LRX_V6` as a PRODUCT_GROUP? Approved May 2026; 4,712 HCPs prescribing per CI report. If not yet in the feed, when is the first expected data date? | Data engineering |
| Q7 | For the Entresto adoption-speed feature (C2): should the clock start from the Entresto FDA approval date (2015) or from the HF-specific indication? Given LAAD data starts Jan 2021, both would be left-censored; the `MIN_DAYS...ANY_HCP` variant (feature #3 in file 04) avoids the launch-date issue. | Modelling team |
| Q8 | CI report notes Baxfendy Segment A overlap is 20% (932 of 4,712 prescribers). Can the field team confirm whether those 932 HCPs are Kerendia writers and whether Baxfendy prescribing preceded or followed Kerendia adoption? | Field / BA |

*Source for sections 0 and 5 (CI items): CI Report, Joshua Buffington PharmD, September 24, 2026 (internal). IQVIA LAAD; 2026 ESC Heart Failure Guidelines; 2025 AHA/ACC BP Guideline; ClinicalTrials.gov NCT06268873, NCT06742723, NCT06677060, NCT06424288; Boehringer EASi-KIDNEY statement Sept 15 2026.*
