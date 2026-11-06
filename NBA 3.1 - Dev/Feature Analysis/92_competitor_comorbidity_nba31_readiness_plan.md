# Kerendia NBA 3.1 — Competitor, Comorbidity & Market-Event Features: Readiness Plan

> **Data source update (Nov 2026):** NBA 3.1 now reads `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (LAAD-based LRx V7, weekly, history from Dec 2021) instead of `KERENDIA_LAAD_BASED_LRX_V6` and `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021`. Read V6 references below as V7. V7 `WEEK_ENDING_DATE` / `PERIOD_ID` are DATEs, and `PRODUCT_GROUP` uses the shorter lrx_nbrx names. Numbers in this document were computed on V6.

**Owner:** NBA modelling team (Wenjie)  
**Date:** November 2026  
**Status:** Draft. Nothing built yet. Includes decisions from the CI meeting with Josh Buffington (Nov 2026).  
**Scope:** Four feature families: comorbidity / Dx panel (files 01–02), competitor NBRx share (09–10), adoption speed (03–04) and market-event labels (new). Prior-writing (07–08) and IQVIA channel (05–06) are out of scope.

**Inputs this plan is built on**

| Doc | What it contributes |
| --- | --- |
| `01` / `02` comorbidity analysis + changes | NBA 3.0 audit (3 of 39 columns kept), Dx building blocks, backtest AUCs, 12 new columns |
| `03` / `04` adoption speed analysis + changes | 3 features × 5 drug groups = 14 columns, backtest by drug |
| `09` / `10` competitor share analysis + changes | Indication-scope problem, cohort leakage, drug list, windows |
| `90` summary and trends | 2-year market trends, priority list H1–H5, M1–M6, L1–L3, C1–C5 |
| `91` Josh briefing, Section 9 | CI meeting decisions (build / defer / drop) |
| CI Report (J. Buffington, 9/24/26) | Event dates: Farxiga LOE, Entresto LOE, Baxfendy, EASi-KIDNEY, GLP-1 guidelines |

---

## 1. Readiness summary

| Family | NBA 3.0 today | NBA 3.1 target | Readiness | Main blocker |
| --- | --- | --- | --- | --- |
| Comorbidity / Dx panel | 39 cols, 3 kept (0.54% SHAP). CKD only. Stage 3 codes missing | ~15 cols: indication mix (incl. HF, T1D), stage 3/4 shares, 24M counts, growth log-ratio | **Spec ready** | HF LVEF >= 40% proxy needs Medical sign-off (V3) |
| Competitor NBRx share | 9 cols, all indications mixed, static build (leakage) | CKD-scoped + all-indication shares, Farxiga brand/generic split, 3M + 12M, steroidal MRA, GLP-1 (T2D + HF) | **Spec ready, data checks pending** | Dx coverage in LAAD (V1), GLP-1 products in LRx feed (V7) |
| Adoption speed | 2 cols, 1 kept (`TIME_TO_ADOPT_FARXIGA`, rank 13, 1.10% SHAP) | 14 cols across Farxiga, Jardiance, steroidal MRA, Entresto, Invokana + Entresto brand-adopter flag | **Notebook started** (`11_adoption_features`) | Entresto brand vs generic split (V6) |
| Market-event labels | None | `DAYS_SINCE_*` for Farxiga LOE and Entresto LOE, plus Farxiga post/pre log-ratio | **Design agreed** | Enough post-event training rows (V9) |

---

## 2. Grain and shared conventions

* **Grain:** one row per `HCP_COHORT_ID` (HCP × cohort `lookback_end_date`). Every feature in this plan is built per cohort and capped at `lookback_end_date`. No static builds (fixes the NBA 3.0 leakage in competitor and adoption features).
* **Cohorts:** `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` for Dx and Rx features. `kerendia_nba_3_1_volume/cohorts/lrx/cohorts.parquet` for LRx (NBRx) features.
* **Join key:** `HCP_COHORT_ID` in `99_Combine_Physician_Data`, replacing `PROVIDER_ID` / `NPI_NUMBER` + `SVC_DT_M`.
* **Universe:** NBA 3.1 universe, 314,920 HCPs, 6,704 writers, base rate 2.13%.
* **Dx panel:** distinct patients with any Dx event-list claim where the HCP is the referring (else rendering) doctor. Patient flags come from claims by any provider in the lookback.
* **Null policy:** `NUM_*` = 0 when nothing qualifies. `PCT_*` / shares are empty when the denominator is empty. `MIN_DAYS_*` is empty when the HCP never prescribed the drug.
* **Evaluation metrics (same as the backtests):** AUC, AUC within HCP size band ("in size"), AUC on new writers.

---

## 3. Phase 0 — Data validations (must pass before build)

| # | Validation | How | Pass criterion | Owner |
| --- | --- | --- | --- | --- |
| V1 | Diagnosis coverage behind indication groups in LAAD (meeting caveat) | Share of SGLT2, steroidal MRA and Entresto NBRx with a non-empty `INDICATION_GROUP` / attached Dx, by month and drug | Coverage known and stable over time. If coverage drifts, CKD-scoped features need a coverage-normalised version | NBA team |
| V2 | CKD stage 3 codes (N18.30/31/32) present after the Dx list update | Count stage 3 patients in the new `Dx_03` vs NBA 3.0 (26,200) | Large increase, consistent with stage 3 being the main CKD population | NBA team |
| V3 | HF LVEF >= 40% proxy (`I50.3x` and no `I50.2x`) | Medical review of the proxy definition | Signed off, or replacement definition agreed | Medical / BA |
| V4 | CKD-containing `INDICATION_GROUP` values in `KERENDIA_LAAD_BASED_LRX_V6` | `SELECT DISTINCT INDICATION_GROUP` | Agreed list (CKD, T2D+CKD, T2D+CKD+CVD, T2D+CKD+HF, T2D+CKD+CVD+HF, CKD+CVD, CKD+HF, CKD+CVD+HF, plus any others found) | NBA team / BA |
| V5 | Farxiga brand vs generic labels | Monthly NBRx by `PRODUCT_GROUP` (`FARXIGA BRAND`, `FARXIGA GENERICS`) | Generic volume starts around 2026-04-06. Labels stable, no third label | NBA team |
| V6 | Entresto brand vs generic in Rx / LRx | Product names for sacubitril/valsartan generics in `Rx_01_new` and LRx | Generics captured and separable from brand. LOE date confirmed (Jul 2025, full generic expected 2027) | NBA team / Josh |
| V7 | GLP-1 products in the LRx feed | Check semaglutide and tirzepatide brands and their indication groups (T2D, HF) | Products present with usable volume in T2D and HF groups | Data engineering |
| V8 | Cohort parity vs NBA 3.0 | Rebuild NBA 3.0 competitor features per cohort, compare to the static output | Differences explained by leakage only | NBA team |
| V9 | Training support for event labels | Rows and writers per cohort after each event date in the training window | Enough post-event rows to learn from (Farxiga, Entresto). Events with too few rows wait for NBA 3.2 | NBA team |
| V10 | Pre-LOE Entresto prescriber specialty mix (Q8 from the briefing, not answered in the meeting) | Specialty split of brand Entresto writers 2023–2024 vs Kerendia target segment | Overlap known. It decides whether the brand-adopter flag is a target-segment signal | NBA team |

---

## 4. Phase 1 — Comorbidity / Dx panel

| # | Item | Columns | Evidence | Source ref |
| --- | --- | --- | --- | --- |
| CM1 | Replace `FIN_DIAG_CD` with the NBA 3.1 Dx event list (adds N18.30/31/32, T1D `E10*`, HF `I50*`) | Input change | Stage 3 almost empty in NBA 3.0 | H1, file 02 §1.5 |
| CM2 | Indication mix: T2D+CKD, T1D+CKD, HF proxy, CKD+HF, any indication (NUM + PCT) | 9 | New-writer AUC 0.54–0.59 vs 0.505 for the best NBA 3.0 feature | H2, file 02 §2.1 |
| CM3 | CKD stage 3 and stage 4 shares | 2 | Highest in-size AUC of all Dx features (0.704 stage 4, 0.685 stage 3) | H3, file 02 §2.2 |
| CM4 | Replace running totals with fixed 24-month distinct-patient counts | 2 | Removes data-start dependence | M1 |
| CM5 | Drop rolling averages, single-month counts, 1/3/6M window shares | Removes ~30 | None in the 752; redundant | M2, L1 |
| CM6 | Growth log-ratio of indicated patients (3M vs prior 9M) | 1 | AUC 0.629, in size 0.578, new writers 0.525. Keep only if selection keeps it | M3 |

**Notebook:** port `09_claim_comorbidity` into `NBA 3.1 - Dev/03_HCP_Level_Features`; input from `00_Write_HCP_Inputs_31` (`Dx_03`).

---

## 5. Phase 2 — Competitor NBRx share

| # | Item | Columns | Notes | Source ref |
| --- | --- | --- | --- | --- |
| CP1 | Rebuild per LRx cohort (no static build) | — | Fixes leakage | H5 |
| CP2 | Two scopes: CKD-scoped (primary) and all-indication (fallback) | ×2 | Meeting: CKD scoping confirmed (SGLT2 is second-line in T2D-only). Dx coverage is weak, so keep the all-indication version and let selection choose | H4, D1 |
| CP3 | Farxiga brand vs generic as separate shares | +2–4 | Generic launch Apr 2026 confounds the combined Farxiga share | C1 |
| CP4 | 3-month window next to 12-month | ×2 | Momentum | M5 |
| CP5 | Steroidal MRA (spironolactone + eplerenone) NBRx in CKD scope | 1–2 | Nearest therapeutic predecessor to Kerendia | M4 |
| CP6 | GLP-1 (semaglutide, tirzepatide) NBRx share in T2D and HF scopes | 2–4 | Meeting: same-population signal, not a replacement; risk is cost-driven prioritisation | C4, D5 |
| CP7 | Invokana, Steglatro: keep counts, low selection priority | 2 | Near-zero by 2026 | L2 |

**Interpretation rule (D8):** ACC/AHA pairs SGLT2 + Kerendia as first-line in HF. A high CKD-scoped SGLT2 share is expected to be **positive** for Kerendia. Flag any model that learns the opposite for review.

**Notebook:** replace `31_Competitor_drugs_NBRX_share` with a cohort-based version in `NBA 3.1 - Dev/03_HCP_Level_Features`. Confirm the LRx pull keeps `INDICATION_GROUP` and `PRODUCT_GROUP`.

---

## 6. Phase 3 — Adoption speed

| # | Item | Columns | Evidence | Source ref |
| --- | --- | --- | --- | --- |
| AD1 | `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_CKD_DIAGNOSIS`, `HCP_TIME_TO_ADOPT_{DRUG}`, `MIN_DAYS_..._POST_FIRST_CKD_DIAGNOSIS_ANY_HCP` for Farxiga, Jardiance, steroidal MRA, Entresto, Invokana | 14 | Jardiance #3: AUC 0.679 / in size 0.659. Spironolactone #3: 0.643 / 0.623 / 0.574 | M6, file 04 |
| AD2 | Entresto: brand and generic together (V6) | — | Meeting: Entresto is often prescribed for HF before Kerendia | C2, D6 |
| AD3 | `ENTRESTO_BRAND_ADOPTER_FLAG` (first Entresto Rx before the LOE date) | 1 | Pre-LOE adopter chose an expensive HF drug on evidence. Value depends on V10 | Briefing 5.6 |

**Notebook:** `NBA 3.1 - Dev/03_HCP_Level_Features/11_adoption_features` (exists). Input `Rx_01_new` with `RX_ADOPTION_ONLY = True`.

---

## 7. Phase 4 — Market-event labels

Shared event-date reference table (one row per event). Feature notebooks read dates from it, so a new event is a new row, not a code change.

| # | Event | Date | Feature(s) | NBA 3.1 status |
| --- | --- | --- | --- | --- |
| EV1 | Farxiga generic launch | 2026-04-06 | `DAYS_SINCE_FARXIGA_LOE`; Farxiga NBRx log-ratio (3M post / 3M pre) | **Build** |
| EV2 | Entresto generic (amorphous form) | 2025-07 | `DAYS_SINCE_ENTRESTO_LOE`; used by AD3 | **Build** |
| EV3 | GLP-1 in HFpEF guidelines (ESC / ACC) | 2026-08 (approx.) | `DAYS_SINCE_GLP1_HF_GUIDELINE` | Conditional on V9 (likely too few post-event rows) |
| EV4 | Baxfendy approval | 2026-05 | `DAYS_SINCE_BAXFENDY_APPROVAL` | Deferred (no Baxfendy feature to interact with) |
| EV5 | Entresto full generic (crystalline form) | 2027 (expected) | `DAYS_SINCE_ENTRESTO_FULL_GENERIC` | Add row when date is confirmed |
| EV6 | Direct nsMRA competitor launch | TBD (readout expected April) | Launch flag | Add row at launch |

**Design choice:** `DAYS_SINCE_*` (continuous, negative before the event) is preferred over a 0/1 flag because the tree can learn that a market settles over time. The 0/1 flag is tested as the alternative in E4.

---

## 8. Deferred and dropped

| Item | Decision | Reason | Revisit |
| --- | --- | --- | --- |
| Baxfendy / ASI class features (C3) | Deferred | Not a direct competitor (hyperkalemia overlap, mainly HTN). About 6 months on market, volume too low | Monitor with the weekly Baxfendy dashboard in Databricks. Add lorundrostat and other ASIs as they launch. NBA 3.2 |
| Balcinrenone + dapagliflozin | Deferred | Not on market. May affect Jardiance in about 2 years | NBA 3.2+ |
| Direct nsMRA competitor | Deferred | No data, not on market | Event row at launch (EV6) |
| ASI trial zip-code flag (C5) | Dropped | Josh's study mapping showed no meaningful link with Kerendia providers. Zip codes only | — |
| DPP-4 inhibitors | Dropped | Largely replaced by GLP-1, appear mutually exclusive with GLP-1 | — |
| IQVIA channel features in this family (05–06) | Dropped | Superseded by `1_Additional_HCP_level_features` (already in the 752) | — |

---

## 9. Experiments

Each experiment adds one block to the previous one and is scored on the same NBA 3.1 train / validation split.

| # | Experiment | Question | Success signal |
| --- | --- | --- | --- |
| E0 | Baseline: NBA 3.0 versions of these families, rebuilt per cohort on the 3.1 universe | What does the old family give once leakage is removed? | Reference AUC / in size / new writers |
| E1 | + Comorbidity (CM1–CM6) | Do HF, T1D and stage features add lift? | New-writer AUC up; stage shares kept by selection |
| E2 | + Competitor, CKD scope vs all-indication vs both | Which scope survives, given weak Dx coverage? | Pick scope by lift and SHAP stability |
| E3 | + Adoption speed (AD1–AD3) | Do Jardiance, MRA, Entresto add beyond Farxiga? | Lift over E2; Entresto helps HF segment |
| E4 | + Event labels: `DAYS_SINCE_*` vs 0/1 flags vs none | Do event labels fix the post-LOE Farxiga confounding? | Farxiga feature SHAP more stable across pre/post cohorts; lift on post-LOE cohorts |
| E5 | GLP-1 share with and without payer / OOP-cost features | Does GLP-1 work as a cost-interaction signal? | Interaction visible in SHAP; lift in obese / HF segment |
| E6 | Segment read-out (new writers, HF-heavy panels, stage 3/4 panels, specialty) | Do narrow signals help specific segments even if overall lift is small? | Segment-level lift supports tailored suggestions (meeting point on segment signals) |

---

## 10. Gates

| Gate | Criteria | Sign-off |
| --- | --- | --- |
| G0 — Data ready | V1–V7 pass; V3 signed off by Medical | NBA team, Medical |
| G1 — Features built | All Phase 1–4 build items run per cohort; V8 parity explained; null rates documented | NBA team |
| G2 — Value shown | E0–E4 complete; each kept block shows lift or segment value (E6) | NBA team, BA |
| G3 — Ready for training | Final feature list; interpretation check (D8); competitor/event features reviewed with Josh | NBA team, BA, Josh (CI) |

---

## 11. Decisions log

| # | Decision | Source |
| --- | --- | --- |
| D1 | CKD-scoped competitor shares are primary; all-indication kept as fallback because Dx coverage in LAAD is weak | CI meeting, Nov 2026 |
| D2 | Baxfendy / ASI features deferred; monitor via the weekly Baxfendy dashboard | CI meeting |
| D3 | DPP-4 not tracked | CI meeting |
| D4 | ASI trial zip-code flag dropped | CI meeting |
| D5 | GLP-1 tracked in T2D and HF, treated as same-population / cost signal | CI meeting |
| D6 | Entresto tracked as brand + generic for HF adoption | CI meeting |
| D7 | Market events enter the model as labels (`DAYS_SINCE_*`), starting with Farxiga and Entresto LOE | Wenjie, Nov 2026 |
| D8 | SGLT2 adoption is read as complementary to Kerendia | CI meeting (ACC/AHA first-line pairing) |

---

## 12. Open questions

| # | Question | Owner |
| --- | --- | --- |
| Q1 | Is `Kerendia NBA 3.1 - Dx Event List.csv` the authoritative replacement for `FIN_DIAG_CD`? | Data engineering |
| Q2 | HF LVEF >= 40% proxy: approve `I50.3x` and no `I50.2x`, or provide an alternative? (V3) | Medical / BA |
| Q3 | Final list of CKD-containing `INDICATION_GROUP` values (V4) | BA / Medical |
| Q4 | Which competitor share features are in the NBA 3.0 752-feature list (`Final NBA 3.0 Modeling Features.xlsx`)? | NBA team |
| Q5 | Where is the weekly Baxfendy dashboard, and who owns it? | Josh |
| Q6 | Exact Entresto LOE dates (amorphous 2025, crystalline 2027) for the event table | Josh |
| Q7 | Are payer / OOP-cost features available at HCP-cohort grain for the GLP-1 interaction test (E5)? | NBA team |
| Q8 | Is the cortisol / MRA-class differentiation message landing with specific specialties? (carried from briefing Q6) | Josh |
| Q9 | Which Unity Catalog schema should hold registered NBA features, and who grants `CREATE FEATURE`? (Feature Views pilot, FV6) | NBA team / platform admin |

---

## 13. Timeline

| Step | Owner | When |
| --- | --- | --- |
| Phase 0 validations V1–V10 | NBA team, Data engineering, Medical | Nov 2026 |
| G0 | NBA team, Medical | End Nov 2026 |
| Phase 1 comorbidity build | NBA team | Nov–Dec 2026 |
| Phase 2 competitor build | NBA team | Nov–Dec 2026 |
| Feature Views pilot (Section 15), decision before G1 | NBA team | Dec 2026 |
| Phase 3 adoption build | NBA team | Dec 2026 |
| Phase 4 event table + labels | NBA team | Dec 2026 |
| G1, experiments E0–E6, G2 | NBA team, BA | Jan 2027 |
| G3 review with Josh, final feature list | NBA team, BA, Josh | Jan 2027 |
| NBA 3.1 training | NBA team | Q1 2027 |

---

## 14. Notebook map

| Notebook (NBA 3.1 - Dev/...) | Phases | Change |
| --- | --- | --- |
| `00_Helper_Notebooks/00_Write_HCP_Inputs_31` | All | Dx event list, `Rx_01_new` adoption products, LRx pull with `INDICATION_GROUP` / `PRODUCT_GROUP`, GLP-1 products |
| `03_HCP_Level_Features/09_claim_comorbidity` (to port) | 1 | Cohort-based distinct-patient counts, new building blocks |
| `03_HCP_Level_Features/31_Competitor_drugs_NBRX_share` (to replace) | 2 | Cohort loop, scopes, windows, brand/generic, MRA, GLP-1 |
| `03_HCP_Level_Features/11_adoption_features` (exists) | 3 | 14 columns + Entresto brand-adopter flag |
| New: event reference table + event features | 4 | `DAYS_SINCE_*`, log-ratio |
| `99_Combine_Physician_Data` | All | Join on `HCP_COHORT_ID` |

---

## 15. Feature Views pilot (optional, runs alongside Phase 2)

**What it is.** Feature Views (Databricks, Public Preview) define a feature once as source table + calculation + entity + date column + time window. The same definition builds a point-in-time training set and the batch scoring data, and the feature is registered in Unity Catalog with lineage.

**Why pilot it here.** It addresses three problems in this plan directly: static-build leakage (point-in-time joins), hand-written cohort loops over `lookback_end_date`, and keeping training and monthly inference consistent. It is not a reason to rebuild all ~750 NBA features for 3.1.

### 15.1 Fit by family

| Family | Fit | Notes |
| --- | --- | --- |
| Competitor NBRx counts (CP1–CP7) | **Strong** | `Sum` of NBRx by NPI over 90 / 365-day windows, with `filter_condition` on `INDICATION_GROUP` and `PRODUCT_GROUP`. Shares (drug / SGLT2 total) are a small post-step, not built in |
| Comorbidity counts (CM2–CM4, CM6) | Partial | Patient flags (T2D+CKD etc., from claims by any provider) must be prepared first in a patient-level table. Distinct patients are approximate (`ApproxCountDistinct`, no exact distinct count) and will differ slightly from the backtests. "3M vs prior 9M" maps to a window with `delay` |
| Adoption speed (AD1–AD3) | Weak | Multi-step patient-level logic. Keep in `11_adoption_features` |
| Market-event labels (EV1–EV6) | Not needed | Depend only on the cohort date. One column on the cohort table |

### 15.2 Pilot scope

* **Features:** Jardiance and Farxiga (brand, generic) NBRx in CKD scope and all-indication scope, 3M and 12M windows (8–12 features). Shares computed after the join.
* **Labelled input:** LRx cohort table with `NPI_NUMBER` (entity), `lookback_end_date` (date column) and the Kerendia NBRx label.
* **Source:** `KERENDIA_LAAD_BASED_LRX_V6` written as a Delta table in Unity Catalog (Feature Views do not read volume parquet).
* **Compute:** serverless or DBR 17.0 ML+, `databricks-feature-engineering >= 0.16.0`.
* **Stores:** offline only. No online store (NBA scores monthly in batch).

### 15.3 Pilot checks

| # | Check | Pass criterion |
| --- | --- | --- |
| FV1 | Values vs the hand-built cohort version of CP1 (doubles as V8) | Counts match exactly for `Sum`; any difference explained |
| FV2 | Date boundary: is `lookback_end_date` treated as inclusive or exclusive in the training-set join? | Same convention as the cohort notebooks, or the label input is shifted to match |
| FV3 | Data lag: inference only sees LRx up to the last loaded week | Window `delay` set so training sees only what inference would see |
| FV4 | Run time and cost for the full 3.1 universe × all cohorts | Comparable to or faster than the notebook build |
| FV5 | Batch scoring with the same definitions on the latest cohort | Matches FV1 values for that cohort |
| FV6 | Permissions | `CREATE FEATURE` on the target schema; `READ FEATURE` for consumers |

### 15.4 Decision after the pilot

| Outcome | Next step |
| --- | --- |
| FV1–FV5 pass | Build the competitor family in Feature Views for NBA 3.1. Consider comorbidity counts next (needs the patient-flag table) |
| FV1 or FV2 fail and cannot be fixed | Keep the notebook build for 3.1. Revisit Feature Views for NBA 3.2 |
| Pass but slower or costlier | Keep notebooks for 3.1. Use Feature Views only for new families |

Adoption speed and event labels stay outside Feature Views in all outcomes.
