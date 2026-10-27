# NBA 3.1 – HCP Claims Features: Recommendations

**Companion to:** `NBA_3_1_HCP_Claims_Features_Analysis.md` (evidence, EDA numbers, and description of what 3.0 does). Section numbers match that file.

**Scope:** patient journey notebooks 01–06 and HCP claim notebooks NB01–NB06 (`03_Feature_Engineering/03_HCP_Level_Features/`). Recommendations apply to the 3.1 cohort versions of these notebooks (`claim_*_cohort` outputs) and the 3.1 validation tables (`kerendia_nba_3_1_*_validation`).

**Priority legend**
* **P0** – correctness fix. The 3.0 feature is wrong or misleading; fix before 3.1 training.
* **P1** – high-value change or addition backed by EDA / SHAP evidence.
* **P2** – cleanup or optional addition; do if time allows.

**Headline**
1. Fix the patient-journey CKD stage mapping (stage 3 and stage 5 are essentially missing), the eligibility-rule bug in 06_combine (every unknown-stage patient is "eligible"), and the NB04 family C fan-out (≈ 8× over-count). These P0 items have the largest downstream effect.
2. Cut the claims feature footprint substantially. 97% of the 9,617 current columns are never selected and 71 of the 277 selected ones have a near-duplicate (|r| ≥ 0.95).
3. Shift from "claims sliced many ways" to "patient panel" features aligned to the Kerendia label (T2D + CKD; plus the HF indication): eligible patients, guideline-pillar coverage, and white space.

---

## 0. Cross-cutting recommendations

| # | Priority | Recommendation | Evidence / rationale |
| --- | --- | --- | --- |
| X1 | P1 | **Drop BASE and PCT_BASE columns** from every notebook | 100% value-identical to `_IN_LAST_1_MONTH` in NB01–NB05; 0 of ~1,700 selected. Removes ~1,750 columns |
| X2 | P1 | **Bound RUNNING_** to a fixed trailing window (e.g. `_IN_LAST_24_MONTH`) or a fixed start equal to the 3.1 data start | RUNNING_ is the most selected NB01 window (52 features, 6.1% SHAP) but grows monotonically with calendar time, so training cohorts (2022–2025) and scoring cohorts see different scales. A trailing 24M keeps the long-memory signal without drift |
| X3 | P1 | **Keep windows 3/6/12 (+24 or bounded RUNNING); keep 1M only for volume and starts** | 3M vs 6M r = 0.92–0.99 and 6M vs 12M r = 0.93–0.98. 1M carries independent signal only for a few features (e.g. rank 18 patient-treatment 1M) |
| X4 | P1 | **Pre-selection de-duplication**: inside the claims block, compute pairwise correlation and, for any pair with absolute correlation ≥ 0.98, keep only one feature before Boruta runs | 71 of the 277 selected features have a partner with absolute correlation ≥ 0.95 (e.g. SGLT2 vs SGLT2_WO_INVOKANA_300MG r = 1.0, 6 pairs both kept). Duplicates split SHAP and make interpretation unstable |
| X5 | P0 | **Fill structural zeros with 0, keep null only for "no data"** | NB05 has 1,014,149 filled months with null instead of 0; `TOTAL_NEW_PATIENT_START` is null for HCPs without starts. Tree models treat null and 0 differently |
| X6 | P0 | **Align feature month with the 3.1 cohort anchor** | Patient tables and HCP features are calendar-month (`date_trunc('MM')`). 3.1 cohorts with offset anchors need either as-of-date windows (`SVC_DT ≤ LOOKBACK_END_DATE`) or the feature month must be the last *complete* month before the anchor, to avoid partial-month leakage |
| X7 | P1 | **Update the product mapping (CKD_PRODUCT_MAPPING)** | Add tirzepatide (Mounjaro) and semaglutide as a separate GLP-1 brand; add finerenone so that patient-therapy features can say "already on Kerendia"; add sotagliflozin (Inpefa) under SGLT2; move Spironolactone/HCTZ to a consistent class; remove the never-populated `Diuretic + MRA` brand |
| X8 | P1 | **Prefer distinct patients over claim counts** for panel-type features | Claim counts are dominated by refill cadence (refill 52.8% of claims) and days supply; patient counts measure panel size, which is what NBA targeting needs. Keep claim counts only where the claim itself is the behaviour (payer, rejection, days supply) |
| X9 | P2 | **Name features by meaning** | `..._PATIENT_WITH_DX_GFR_STAGE_...` in NB04 is a patient-journey stage (Dx or lab), not a Dx claim; rename to `..._PATIENT_STAGE_...` |
| X10 | P2 | **Pull filter lists into one config** (brand list, class list, age bins, payer groups) | The same hard-coded lists appear in NB01, NB04, NB05 and diverge (e.g. Diuretic+MRA present in NB01/NB04 but not NB05) |

### 0.1 Column footprint and how to slim it

| Notebook | 3.0 columns | 3.0 used | How |
| --- | --- | --- | --- |
| NB01 | 5,411 | 172 | X1–X4; collapse age, gender, payer; drop SGLT2_WO, AVG, DIFF |
| NB02 | 116 | 0 | Rebuild as patient-based testing features (Section 3) |
| NB03 | 127 | 3 | Patient counts by corrected stage + progression events |
| NB04 | 3,691 | 89 | Drop family B; fix and slim family C |
| NB05 | 188 | 14 | Fix nulls; add pillar add-on starts |
| NB06 | 84 | 1 | Redefine eligibility; add white space |
| **Total** | **9,617** | **277** | |

---

## 1. Patient journey (foundation)

| # | Priority | Recommendation | Evidence / rationale |
| --- | --- | --- | --- |
| PJ1 | **P0** | **Re-map Dx CKD stage from ICD-10 codes, not description text.** N18.1 → 1, N18.2 → 2, N18.30/N18.31/N18.32 (and legacy N18.3) → 3 (keep 3a/3b as sub-stage), N18.4 → 4, N18.5 → 5, N18.6 / Z99.2 → ESRD/dialysis. E11.22, I12.9, I13.x keep stage 0 (CKD, stage unknown) | Since 2025-01, stage-3 text matches only 4,632 rows vs 7.26M for stage 4; no stage 5 rows. Stage 3 is the core Kerendia population (eGFR 25–60). Dx stage feeds NB03, NB04 A/C and NB06 |
| PJ2a | **P0** | **Fix the eligibility condition in 06_combine**: test `STAGE_ELIGIBLE == -1` (not `GFR_UACR_DX_STAGE == -1`) | The raw stage is never -1, so the unknown-stage exclusion never fires; 89% of eligible patient-months are STAGE_UNKNOWN |
| PJ2 | **P0** | **Make SGLT2_FLAG and DIABETIC_FLAG time-aware** (flag = 1 only from the first qualifying event date onward) | `SGLT2_FLAG` is a lifetime patient flag joined to every month, so once PJ2a is fixed a patient who starts SGLT2 in 2026 would count as eligible in 2023 training months (look-ahead). `DIABETIC_FLAG` is joined but unused |
| PJ3 | P0 | **Use the lab journey output (forward-filled) in 06_combine**, not the raw lab query output, and keep the 3.1 fix for `na.fill(LAST_TEST_DATE)` | 06 reads `kerendia_nba_3_0_lab_query_output`, so lab stage exists only in the test month; the forward fill built in 01 is not used. 3.0 bug drops the last test's carry-forward |
| PJ4 | P1 | **Combine GFR stage with a recency limit** (e.g. carry a lab/Dx stage forward for at most 24 months) | Forward fill without expiry keeps stale stages indefinitely; 72% of patient-months are still null, so expiry will not lose much coverage but will improve precision |
| PJ5 | P1 | **Stop exploding CATEGORY × BRAND** in `pat_uacr_stage_and_treatment_category_new`. Keep arrays and use `array_contains` / boolean columns (`ON_SGLT2`, `ON_GLP1`, `ON_MRA`, `ON_ACE_ARB`, `ON_FINERENONE`) | 3.98 rows per patient-month cause the NB04 family C over-count (Section 5) |
| PJ6 | P1 | **Replace the daily explode in 03_rx with interval logic** (month overlap between `[SVC_DT, SVC_DT + DAYS_SUPPLY + 7]` and each month) | 3.3–3.5B-row intermediate; month-level output only needs `months_between`-based sequence. Large runtime saving |
| PJ7 | P1 | **Add a T2D + CKD label flag and an HF flag per patient-month** | Kerendia label is CKD associated with T2D, and since 2025 also HF with LVEF ≥ 40%. DIABETIC_FLAG is built but never used; there is no HF flag. Claims cannot see LVEF, so use HF Dx (I50.x) as the proxy |
| PJ8 | P2 | **Add `STAGE_SOURCE` (lab / dx / both) and `STAGE_KNOWN` flags** | Allows features that distinguish "staged" patients from CKD-unknown ones; today unknown stage is 85–91% of every stage pivot |
| PJ9 | P2 | **Document the lab left-censoring** (lab data starts 2021-11-30) and exclude cohorts whose 12M lookback precedes it from lab-dependent features, or rely on the 3.1 data start (2023) | |
| PJ10 | P2 | **Dialysis**: also use Dx Z99.2 / N18.6 and procedure CPT codes rather than `%DIALYSIS%` description match; handle transplant (Z94.0) | Description match can include access procedures and training |

---

## 2. NB01 – `01_claim_rx_monthly`

### 2.1 Keep

| Family | Why |
| --- | --- |
| Payer × class | Highest-SHAP NB01 family (35 features, 4.3%); rank 14 and 31 are `RUNNING_..._COMMERCIAL` |
| Duration (days supply) × class | 27 features, 3.3% SHAP; 90-day share is a proxy for mail-order / Medicare stable patients |
| Category/brand volume | Core volume; keep 3/6/12 and bounded RUNNING |
| Refill / new Rx | `PCT_..._NEW_PRESCRIPTION_IN_LAST_6_MONTH` rank 61 |
| Patient treatment buckets | Rank 18 (`..._WITH_1_ACTIVE_TREATMENT_IN_LAST_1_MONTH`); cheap (88 cols) |
| Rejected | Small family, 4 selected; rejection is a payer-friction signal also relevant for Kerendia access |

### 2.2 Change

| # | Priority | Change | Evidence / rationale |
| --- | --- | --- | --- |
| R1 | P1 | **Collapse age to 4 bins**: < 50, 50–64, 65–74, ≥ 75, plus `UNKNOWN` | 1,991 age columns, 39 used; 458 age columns non-zero for < 1% of HCPs. `AGE_GROUP_10_0` is an invalid label with 0 claims; 0–10 / 10–20 bins are irrelevant to CKD/T2D. 65 is the Medicare break |
| R2 | P1 | **Collapse payer to 5 groups**: Commercial, Medicare Part D (+ Medicare), Medicaid (FFS + Managed), Cash, Other/Unknown | Medicare non-Part D is 0.15% of claims; Medicaid FFS/Managed are similar in meaning. Cuts payer columns by ~30% |
| R3 | P1 | **Gender: keep only `PCT_..._F` per class** (drop M and U) | `PCT_F + PCT_M = 1.000` for every HCP; U is 0.01% of claims. 561 → ~60 columns |
| R4 | P1 | **Cross-products at most two-way** (class × one attribute). Do not build brand × attribute for brands with < 1% of class volume (Invokana 100/300) | The 3-way structure creates most of the 5,411 columns; Modeling Selection 3.2% |
| R5 | P1 | **Drop the SGLT2_WO_INVOKANA_300MG family** (187 cols) | r ≈ 1.0 with SGLT2 counterparts (Invokana 300 ≈ 0.4% of SGLT2 claims); 6 duplicate pairs in the 752 |
| R6 | P2 | **Drop AVG / patient-count family as features** (keep TOTAL_PATIENT_COUNT as a denominator) | 24 columns, 0 selected, high fill — pure volume duplicate |
| R7 | P2 | **Drop DIFF and RATIO** (keep one trend feature per class: 3M vs prior 3M ratio on patients, not claims) | 0 DIFF and 1 RATIO selected |
| R8 | P0 | **Remove `Diuretic + MRA` columns**; fix Spironolactone/HCTZ class | Brand never occurs; class/brand disagree for 377K claims |
| R9 | P2 | **Drop `UNKNOWN_DAYS_SUPPLY` columns** | DAYS_SUPPLY null share ≈ 0.0003% |

### 2.3 Add

| # | Priority | Feature | Rationale |
| --- | --- | --- | --- |
| A1 | P1 | `TOTAL_PATIENTS_<class>_IN_LAST_{3,6,12}_MONTH` (distinct patients per class) and share of panel on each class | X8; panel breadth is more stable than claims and is what NBA targets |
| A2 | P1 | GLP-1 split: semaglutide, tirzepatide, other GLP-1 | GLP-1 is 48.6M claims/yr, currently one brand bucket and missing tirzepatide entirely; semaglutide now has kidney-outcome evidence and is a direct competitor for CKD-in-T2D share of voice |
| A3 | P1 | Payer share overall at HCP level: `PCT_TOTAL_RX_CLAIMS_MEDICARE_PART_D`, `_COMMERCIAL`, `_MEDICAID` in 12M | Already partly selected (`PCT_TOTAL_RX_CLAIMS_MEDICARE_PART_D_IN_LAST_12_MONTH` rank 156); make it a clean, explicit 3-feature block instead of 1,122 cross-products |
| A4 | P2 | SGLT2 rejection rate and Farxiga/Jardiance rejection rate (rejected / submitted) in 6/12M | Payer friction on the closest analog brand; rejection counts are selected but rates are cleaner |
| A5 | P2 | 90-day supply share for SGLT2 and ACE/ARB | Duration family carries signal mostly through 90-day patterns |

---

## 3. NB02 – `02_claim_lab_monthly`

**Decision:** retire the current 116-column lab-claim volume block (0 selected) and replace it with a small patient-based testing block.

| # | Priority | Recommendation | Evidence / rationale |
| --- | --- | --- | --- |
| L1 | P1 | **Build UACR / eGFR testing features from LAAD Px (CPT 82043, 82570, 80047/80048/80053 + eGFR)** in addition to Quest | Quest-only data covers 43.5% of HCPs. In the patient-level pipeline, `FREQ_ALBUMIN__URINE_EG_MICROALBUMIN_QUANTITATIVE_IN_LAST_12_MONTH_PX` is rank 20 — the UACR-testing signal is strong when sourced from Px |
| L2 | P1 | `TOTAL_PATIENTS_UACR_TESTED_IN_LAST_12_MONTH` and `PCT_T2D_PATIENTS_UACR_TESTED_IN_LAST_12_MONTH` | Guideline adherence (annual UACR for T2D) is a behavioural precursor to Kerendia use |
| L3 | P1 | `TOTAL_PATIENTS_UACR_GE_30_IN_LAST_12_MONTH` (A2 + A3) and `TOTAL_PATIENTS_EGFR_25_60_IN_LAST_12_MONTH` | Directly counts label-eligible lab profiles; A2/A3 are 4.1% of lab claims today and hidden inside stage pivots |
| L4 | P2 | Use `lab_input_claims_all_specialties_v31` (no specialty filter) | Already built for 3.1; increases HCP coverage |
| L5 | P2 | Drop stage-text column names (`STAGE_2_MILD` etc.); use numeric stage | Special-character handling |

---

## 4. NB03 – `03_claim_diagnosis_monthly`

| # | Priority | Recommendation | Evidence / rationale |
| --- | --- | --- | --- |
| D1 | **P0** | Rebuild on the corrected ICD-based stage (PJ1) | Stage 3 = 0.0% and no stage 5 today; unspecified = 90.1% |
| D2 | P1 | Switch to distinct patients: `TOTAL_DX_PATIENTS_CKD_STAGE_{1_2, 3A, 3B, 4, 5_ESRD, UNKNOWN}` in 6/12M | Claim counts are volume proxies (the 3 selected features are all volume-like); patient counts by stage are the target-population measure |
| D3 | P1 | Progression events: `TOTAL_PATIENTS_PROGRESSED_TO_STAGE_{3,4}_IN_LAST_{6,12}_MONTH` (stage increase only; ignore decreases and stage flicker) | The current NEW_CKD_STAGE counts any change, including downgrades and unknown ↔ known flicker |
| D4 | P1 | `TOTAL_DX_PATIENTS_T2D_AND_CKD`, `TOTAL_DX_PATIENTS_HF` (I50.x), `TOTAL_DX_PATIENTS_T2D_CKD_HF` in 12M | Label-aligned panel counts. Check overlap with `09_claim_comorbidity` (`RUNNING_TOTAL_DX_PATIENTS_DB_KD` rank 133, `..._KD` rank 237) and keep only one implementation |
| D5 | P2 | Drop PCT_ and RUNNING_ versions | 0 selected |

---

## 5. NB04 – `04_claims_monthly`

| # | Priority | Recommendation | Evidence / rationale |
| --- | --- | --- | --- |
| C1 | **P0** | **Fix family C fan-out.** Join each claim to one patient-month row and test therapy with `array_contains` (or the boolean columns from PJ5); count each claim once per therapy flag | Family C class columns sum to a median 8.1× total claims (p10 5.9×, p90 11.2×); vs NB01 class volume: SGLT2 14.8×, Farxiga 16.3× |
| C2 | P1 | **Re-express family C as distinct patients**: `TOTAL_PATIENTS_STAGE_<s>_ON_<therapy>` with stage in {3, 4, 2, unknown} after PJ1 and therapy in {SGLT2, GLP-1, MRA, ACE/ARB, finerenone} | 81 family C features carry 4.8% SHAP, but 31 of them are STAGE_UNKNOWN (≈ "patients on drug X"). Patient counts by stage × therapy are the meaningful version |
| C3 | P1 | **Drop family B (same-day lab × drug)** | 1,705 columns, 0 selected, median non-zero 0.04%; same-day pharmacy-fill vs lab-draw match is structurally rare |
| C4 | P1 | **Drop GFR × UACR combinations in family A** until UACR coverage improves; keep GFR stage only | UACR null for 98.5% of patient-months; `GFR_STAGE_4` vs `GFR_STAGE_4_AND_UACR_STAGE_UNKNOWN` r = 0.999 |
| C5 | P2 | Drop `TOTAL_RX_CLAIMS` (duplicate of NB01), unused `Dx_03` load and `recency_window` | Code hygiene |
| C6 | P2 | Rename `_DX_` → `_PATIENT_STAGE_` | X9 |

### 5.1 Add (pillar coverage / white space – can live in NB04 or the rebuilt NB06)

| # | Priority | Feature | Rationale |
| --- | --- | --- | --- |
| C7 | P1 | `TOTAL_PATIENTS_T2D_CKD_ON_ACE_ARB_AND_SGLT2_NO_MRA` (12M) | Patients on two guideline pillars without an ns-MRA are the most direct Kerendia add-on candidates |
| C8 | P1 | `PCT_T2D_CKD_PATIENTS_ON_SGLT2`, `_ON_GLP1`, `_ON_ACE_ARB` | Pillar adoption rates per HCP; normalises panel size |
| C9 | P2 | `TOTAL_PATIENTS_STAGE_3_4_ON_SPIRONOLACTONE_OR_EPLERENONE` | Steroidal-MRA users are switch candidates; MRA volume is selected today (`RUNNING_TOTAL_RX_CLAIMS_MRA` rank 217) |

---

## 6. NB05 – `05_claim_rx_nps_monthly`

| # | Priority | Recommendation | Evidence / rationale |
| --- | --- | --- | --- |
| N1 | P0 | Fill 0 for visits/starts in filled months; `TOTAL_NEW_PATIENT_START` = 0 when no starts | 1,014,149 null months (X5) |
| N2 | P0 | **Washout rule**: a start is valid only if the patient has ≥ 12 months of LAAD history before it (no claim for that class) | Left-censoring spike at the start of history; Rx_05 starts 2019-11, so starts before 2020-11 are unreliable. With 3.1 data start in 2023 this mostly protects RUNNING_ |
| N3 | P1 | **Add add-on starts**: `TOTAL_PATIENTS_START_SGLT2_ON_ACE_ARB`, `TOTAL_PATIENTS_START_GLP1_ON_SGLT2`, `TOTAL_PATIENTS_START_MRA` among T2D+CKD patients | Highest Modeling Selection (%) of the six notebooks (7.4%); SGLT2 starts 6M is rank 19. Sequencing of pillars is closer to the Kerendia decision than any-start |
| N4 | P1 | Add semaglutide / tirzepatide brand starts (with X7) | Competitor uptake in the same patients |
| N5 | P2 | Tie-break shared first-day starts (credit the HCP with the earliest claim timestamp or split 0.5) | 34 of 16,195 checked starts double credited; small but avoidable |
| N6 | P2 | Keep `TOTAL_PATIENTS_VISIT` as denominator only (0 selected) and define it as distinct patients in the window, not a sum of monthly distinct counts | Sum of monthly distincts overstates panel size for windows > 1 month |

---

## 7. NB06 – `06_claim_eligible_hcp`

| # | Priority | Recommendation | Evidence / rationale |
| --- | --- | --- | --- |
| E1 | **P0** | **Fix the rule bug (PJ2a), then redefine eligibility to the label**: T2D (time-aware) AND CKD stage 1–4 (or eGFR ≥ 25) AND (UACR ≥ 30 when known) AND not on dialysis / ESRD. Separate flag for the HF indication (HF Dx, not ESRD) | 89% of today's "eligible" patient-months have unknown stage; eligible count correlates r = 0.976 with total Rx claims, i.e. eligibility ≈ "active patient" |
| E2 | P0 | Use time-aware SGLT2 / T2D flags (PJ2) | Look-ahead in current flag |
| E3 | P1 | Use the same window semantics as other notebooks: distinct eligible patients seen in the trailing window (sum/distinct), not `step3_lag_avg` averages | `_IN_LAST_1_MONTH` ≠ base month in NB06 only; mixed semantics across notebooks |
| E4 | P1 | Add white-space features: `TOTAL_ELIGIBLE_PATIENTS_NOT_ON_FINERENONE`, `TOTAL_NEW_ELIGIBLE_PATIENTS_IN_LAST_6_MONTH` (newly meeting criteria), `PCT_PANEL_ELIGIBLE` | Aligns the eligible-patient concept with targeting; the stage-4 eligible count survives selection only as a volume duplicate today |
| E5 | P2 | Drop `DIALYSIS_FLAG` as an HCP feature; replace with `TOTAL_DIALYSIS_PATIENTS_IN_LAST_12_MONTH` (or drop) | Flag = 1 for 43% of HCPs |
| E6 | P2 | Drop UACR stage pivots until UACR coverage improves | UACR unknown 99.7% of eligible counts |

---

## 8. Summary table

| Notebook | Action | P0 items | Main additions |
| --- | --- | --- | --- |
| Patient journey | Fix and slim | PJ1 stage mapping, PJ2a eligibility bug, PJ2 time-aware flags, PJ3 lab journey | T2D+CKD and HF flags, therapy booleans |
| NB01 | Keep, simplify | R8 Diuretic+MRA | Distinct patients per class, GLP-1 split, payer share block |
| NB02 | Replace | – | UACR testing rate, UACR ≥ 30 patients (Px + Quest) |
| NB03 | Rebuild | D1 | Patients by stage, progression, T2D+CKD/HF counts |
| NB04 | Fix and slim | C1 fan-out | Stage × therapy patient counts, pillar white space |
| NB05 | Keep, fix | N1 nulls, N2 washout | Add-on starts, GLP-1 brand starts |
| NB06 | Redefine | E1 label eligibility, E2 | White space, new-eligible |

---

## 9. Validation checklist for 3.1

1. Stage distribution after PJ1: stage 3 should be the largest known Dx stage; stage 5/ESRD non-zero.
2. NB04 family C: sum over stages of `TOTAL_RX_CLAIMS_PATIENT_STAGE_*_ON_<X>` ≤ total claims for patients on X (ratio ≤ 1.0).
3. No BASE columns; no column identical to another (exact-duplicate scan).
4. Null vs 0: no null in count columns for HCPs present in the spine.
5. No look-ahead: for a 2023 cohort month, recompute eligibility using only data ≤ lookback end and compare.
6. Re-run the funnel (produced → Boruta → final) and SHAP per notebook; compare against 3.0 (277 features, 25.1% SHAP).
7. Spot-check 10 HCPs end to end (journey → HCP feature) for one stage × therapy feature.

---

## 10. Caveats

* SHAP shares reflect the 3.0 model; some families with low SHAP (e.g. NB06) may gain value once the definition is fixed, so they should be re-evaluated rather than permanently removed.
* The stage 3 / 5 gap behind PJ1 is confirmed in `00_Write_Input_Files` (cell 71): the `pat_journey_dx` code list has N18.3 but not N18.30/N18.31/N18.32, N18.5 or N18.6. PJ1 needs those codes added to the pull as well as the code-based mapping.
* HF indication features use Dx-based HF as a proxy; LVEF is not observable in claims.
* Overlap with other HCP notebooks (`09_claim_comorbidity`, `21_kerendia_claims`, `26/27/28_Features_NBRx/NRx/TRx`, `31_Competitor_drugs_NBRX_share`) should be checked before adding new panel counts, to avoid re-creating duplicates.
