# Kerendia NBRx / NRx / TRx and Competitor Share Features in NBA 3.1: Readiness Plan

**Group:** HCP-level claims features (prescription volume, competitor share)  
**Purpose:** one plan for how NBRx, NRx, TRx and competitor share features go into NBA 3.1: what we keep from 3.0, what we prune, what we add, from which data, in which order, how we test it, and when it is ready  
**Builds on:** the NBA 3.0 feature analysis (`11_nbrx_nrx_trx_and_competitor_share_features_analysis.md`), the NBA 3.1 change recommendations (`12_nbrx_nrx_trx_competitor_share_features_nba31_changes.md`), the product group mapping v4 (`Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`), the final product mapping CSVs (`kerendia_nba_3_1_volume/final_product_mapping/`), and the cohort helper notebooks (`00_Helper_Notebooks/00_cohort_config` and `00_cohort_generation`)  
**Data source:** the same V6 LAAD LRx table used in NBA 3.0 (`KERENDIA_LAAD_BASED_LRX_V6`). No switch to raw claims.  
**Status:** draft for review with the NBA and data engineering teams  
**Date:** November 4, 2026

---

## 1. In short

* **NBA 3.0 produced ~1,337 columns per notebook from 11 pivot dimensions.** Three notebooks (26, 27, 28) each pivot the V6 table by 11 dimensions (PRODUCT_GROUP, SPECIALTY_GROUP, SWITCH_FROM, ADD_ON_TO, AGE_GROUP, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL, INDICATION_GROUP, HYPERTENSION_FLAG, GENDER) and apply 4 lag windows (1, 3, 6, 12 months) + running totals. The competitor share notebook (31) adds 4 SGLT2i share features with 12-month lag only.
* **NBA 3.1 keeps all 11 pivot dimensions and the V6 data source.** The V6 table already has all 11 dimensions pre-computed. No switch to raw claims is needed. All 11 dimensions remain in the output.
* **What changes for NBA 3.1:** (1) prune 7 obsolete product groups from the PRODUCT_GROUP pivot; (2) split diuretics into Loop/Thiazide/K-sparing; (3) add 18 new product groups for T1D and HF to the PRODUCT_GROUP pivot; (4) augment INDICATION_GROUP with T1D (keep V6's pre-computed values, add T1D as a new value); (5) apply priority-based pruning to the PRODUCT_GROUP pivot only (P5-P6: 1 and 12-month windows, no running totals); (6) update the competitor share notebook with Inpefa, MRA share, HF drug share, PROVIDER_ID key, and 1/3/6/12-month windows; (7) switch to the 28-cohort pipeline; (8) use the NBA 3.1 HCP universe (294,727 HCPs).
* **The other 10 pivot dimensions (SPECIALTY_GROUP, SWITCH_FROM, ADD_ON_TO, AGE_GROUP, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL, HYPERTENSION_FLAG, GENDER, INDICATION_GROUP) are kept unchanged from NBA 3.0.** They use V6's pre-computed values as-is.
* **Output is saved to the NBA 3.1 volume** at `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/notebook_output/hcp_features/`.

---

## 2. What we learned (the evidence behind this plan)

| Topic | Finding | Consequence for NBA 3.1 | Source |
| --- | --- | --- | --- |
| NBA 3.0 model | NBRx/NRx/TRx notebooks produce ~1,337 columns each from 11 pivot dimensions; competitor share adds 4 features | Keep all 11 dimensions; apply 3.1 changes to PRODUCT_GROUP and competitor share only | `11_...` Analysis 1-5 |
| V6 product groups | 74 groups including obsolete products (Bexagliflozin, Adlyxin, Cycloset, Tekturna, etc.) | Drop 7 groups (19 products); saves ~105 feature columns per notebook | `12_...` section 2.4 |
| V6 INDICATION_GROUP | 16 values (T2D, CKD, HF, CVD and combinations) but no T1D | T1D is invisible. Derive DM_TYPE from `Kerendia_Dx_Final_Product_Mapping.csv` | `12_...` section 2.2 |
| V6 diuretics | Single `DIURETICS AND COMBOS` group dilutes HF signal from loop diuretics | Split into LOOP / THIAZIDE / K-SPARING (v4 already defines the split) | `12_...` section 3.3 |
| V6 HF drugs | Ivabradine, hydralazine/isosorbide and other HF-GDMT drugs hidden in OTHERS | Reclassify into dedicated HF RATE CONTROL, HF VASODILATORS groups | `12_...` section 2.5 |
| V6 insulin/CGM/pumps | Insulin products, CGM systems and insulin pumps not separate groups in V6 | Add 11 new T1D product groups from v4 mapping | `12_...` section 2.3 |
| Competitor share (3.0) | Only 4 SGLT2i competitors (Farxiga, Invokana, Jardiance, Steglatro); 12-month lag only; uses NPI_NUMBER | Add Inpefa (SGLT2i for HF), MRA share, HF drug share; add 1/3/6-month windows; switch to PROVIDER_ID | `11_...` Analysis 4, `12_...` section 5 |
| Product group priority | V6 has no priority; all groups get all 5 lag/running columns | Apply P1-P6 from v4 mapping; P5-P6 groups get only 1 and 12-month windows and no running totals | `12_...` section 3.2 |
| V6 pivot dimensions | 11 dimensions: PRODUCT_GROUP, SPECIALTY_GROUP, SWITCH_FROM, ADD_ON_TO, AGE_GROUP, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL, INDICATION_GROUP, HYPERTENSION_FLAG, GENDER — all pre-computed in V6 | Keep all 11; no raw claims switch needed; SWITCH_FROM and ADD_ON_TO are available in V6 | NBA 3.0 notebook 26 |
| step2_fill_missing | NBA 3.0 fills missing months per PROVIDER_ID using `step2_fill_missing` from `00_step23_function` | Keep using step2_fill_missing; same function, same approach | NBA 3.0 notebook 26, cell 49 |
| step3_lag | NBA 3.0 creates lag features using `step3_lag` from `00_step23_function` with `last_i_month_list = [1, 3, 6, 12]` | Keep using step3_lag; add priority-based pruning after step3_lag (drop P5-P6 running totals and 3/6-month columns) | NBA 3.0 notebook 26, cell 53 |
| HCP universe | NBA 3.0: ~222K HCPs; NBA 3.1: 294,727 HCPs with C1-C5 cohort flags | Expanded scope includes T1D and HF prescribers | `12_...` section 1 (#13) |
| Cohorts | NBA 3.0: single COHORT_MONTH parameter; NBA 3.1: 28 cohorts (c1-c28) via CohortGenerator | Same notebook produces features for all training/testing/holdout cohorts | `12_...` section 6 |
| Product mapping | V6 PRODUCT_GROUP is pre-computed; 3.1 supplements V6 with merged CSVs (TREATMENT_CATEGORY, DM_TYPE, HF_TYPE, CKD_STAGE, volume metrics) | V6 remains primary source; merged CSVs used for DROP exclusion, T1D identification, and competitor share grouping | `12_...` section 2 |

---

## 3. Decisions taken (from the analysis)

| # | Decision | Effect on the plan |
| --- | --- | --- |
| 1 | Drop 7 product groups marked DROP in v4 mapping (obsolete/withdrawn products) | Filter V6 query or v4 mapping to exclude DROP groups before pivoting |
| 2 | Split DIURETICS AND COMBOS into LOOP / THIAZIDE / K-SPARING | Apply v4 reclassification in the pivot dimension |
| 3 | Add 3 HF drug groups (HF RATE CONTROL, HF VASODILATORS, CARDIAC GLYCOSIDES) | Reclassify from OTHERS using v4 mapping |
| 4 | Add 11 T1D product groups (insulin families, CGM, pumps, glucagon rescue, T1D disease-modifying) | Reclassify from OTHERS or newly add using v4 mapping |
| 5 | Augment INDICATION_GROUP with T1D from DM_TYPE in `Kerendia_Dx_Final_Product_Mapping.csv` | Keep V6's pre-computed INDICATION_GROUP; add T1D as a new value where DM_TYPE = T1D |
| 6 | Drop running totals for P5-P6 groups | After lag step, remove RUNNING_TOTAL columns for low-priority groups |
| 7 | Reduce to 1 and 12-month windows for P5-P6 groups | Drop 3 and 6-month columns for low-priority groups |
| 8 | Add Inpefa to the SGLT2i competitor set (5 competitors) | Update share formula to divide by 5-competitor total |
| 9 | Add MRA competitor share (Kerendia vs spironolactone vs eplerenone) | New share feature: Kerendia NBRx / total MRA NBRx |
| 10 | Add HF drug share (Kerendia, Entresto, Verquvo, Inpefa, Farxiga, Jardiance) | New share feature: Kerendia NBRx / total HF drug NBRx |
| 11 | Switch competitor notebook from NPI_NUMBER to PROVIDER_ID | Aligns with notebooks 26/27/28; avoids NPI mapping in combine step |
| 12 | Add 1, 3, 6-month windows to competitor share (currently only 12-month) | 4 share features x 4 windows x 3 share groups = 48 features (up from 4) |
| 13 | Use the updated NBA 3.1 HCP universe (294,727 HCPs) | Inner-join on PROVIDER_ID |
| 14 | Keep all 11 V6 pivot dimensions (including SWITCH_FROM and ADD_ON_TO) | V6 has all 11 dimensions pre-computed; no raw claims switch needed
| 15 | Use the NBA 3.1 claims-type cohorts (28 cohorts, c1-c28) | Join on HCP_COHORT_ID; filter claims to each cohort's lookback window |
| 16 | Use the final product mapping from `kerendia_nba_3_1_volume/final_product_mapping/` | Supplements V6 with merged CSVs for DROP exclusion, T1D identification, and competitor share grouping |
| 17 | Keep using `step2_fill_missing` and `step3_lag` from `00_step23_function` | Same computation engine as NBA 3.0; apply priority-based pruning after step3_lag |
| 18 | Use V6 as the only data source (same as NBA 3.0) | No switch to raw claims; all 11 pivot dimensions available from V6 |
| 19 | Save output to `kerendia_nba_3_1_volume/notebook_output/hcp_features/` | All feature outputs in the NBA 3.1 volume |

---

## 4. Target design: what we build

All notebooks share these rules: **V6 as the only data source** (same as NBA 3.0); **PROVIDER_ID** as HCP key; **all 11 V6 pivot dimensions kept**; lag windows (1, 3, 6, 12 months) via `step3_lag` from `00_step23_function`; `step2_fill_missing` to fill missing months; running totals only for P1-P4 PRODUCT_GROUP groups (all other 10 dimensions keep running totals for all values).

### 4.1 Overview: 11 pivot dimensions (all kept from NBA 3.0)

| # | Pivot dimension | V6 column | 3.1 changes | Columns (approx.) |
| --- | --- | --- | --- | --- |
| 1 | PRODUCT_GROUP | `PRODUCT_GROUP` | DROP 7 groups; split diuretics; add 3 HF + 11 T1D groups; priority pruning | ~530 (was ~370) |
| 2 | SPECIALTY_GROUP | `SPECIALTY_GROUP` | None — kept as-is | ~100 |
| 3 | SWITCH_FROM | `SWITCH_FROM` | None — kept as-is | ~100 |
| 4 | ADD_ON_TO | `ADD_ON_TO` | None — kept as-is | ~100 |
| 5 | AGE_GROUP | `AGE_GROUP` | None — kept as-is | ~25 |
| 6 | PAY_TYPE | `PAY_TYPE` | None — kept as-is | ~15 |
| 7 | SOURCE_OF_BUSINESS | `SOURCE_OF_BUSINESS` | None — kept as-is | ~80 |
| 8 | RX_CHANNEL | `RX_CHANNEL` | None — kept as-is | ~20 |
| 9 | INDICATION_GROUP | `INDICATION_GROUP` | Augment with T1D (add T1D as new value) | ~85 (was ~80) |
| 10 | HYPERTENSION_FLAG | `HYPERTENSION_FLAG` | None — kept as-is | ~10 |
| 11 | GENDER | `GENDER` | None — kept as-is | ~10 |
| | | | **Total per notebook** | **~1,075** |

### 4.2 NBRx / NRx / TRx notebooks (26, 27, 28)

| Area | Change | Columns added | Columns removed | Net |
| --- | --- | --- | --- | --- |
| Drop product groups (#1) | Filter out 7 obsolete groups (Bexagliflozin, Adlyxin, Cycloset, Miglitol, Tekturna, Actos, obsolete sulfonylureas) | 0 | ~105 | -105 |
| Diuretics split (#2) | DIURETICS AND COMBOS -> LOOP / THIAZIDE / K-SPARING | ~30 | ~15 | +15 |
| HF drug groups (#3) | Add HF RATE CONTROL, HF VASODILATORS, CARDIAC GLYCOSIDES | ~45 | 0 | +45 |
| T1D product groups (#4) | Add 11 groups (insulin families, CGM, pumps, glucagon rescue, T1D disease-modifying) | ~99 | 0 | +99 |
| Running total pruning (#6) | Drop running totals for P5-P6 groups | 0 | ~240 | -240 |
| Lag window reduction (#7) | Keep only 1 and 12-month for P5-P6 groups | 0 | ~360 | -360 |
| 10 other dimensions (#14) | All kept unchanged from 3.0 (SPECIALTY_GROUP, SWITCH_FROM, ADD_ON_TO, AGE_GROUP, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL, HYPERTENSION_FLAG, GENDER, INDICATION_GROUP) | 0 | 0 | 0 |
| **Total per notebook** | | | | **~-255** |

**Column naming convention (same as NBA 3.0):**
- PRODUCT_GROUP: `TOTAL_HCP_{METRIC}_CLAIMS_{PRODUCT_GROUP}_IN_LAST_{1,3,6,12}_MONTH`
- SPECIALTY_GROUP: `TOTAL_HCP_{METRIC}_CLAIMS_SPECIALTY_GROUP_{value}_IN_LAST_{1,3,6,12}_MONTH`
- SWITCH_FROM: `TOTAL_HCP_{METRIC}_CLAIMS_SWITCH_FROM_{value}_IN_LAST_{1,3,6,12}_MONTH`
- ADD_ON_TO: `TOTAL_HCP_{METRIC}_CLAIMS_ADD_ON_TO_{value}_IN_LAST_{1,3,6,12}_MONTH`
- AGE_GROUP: `TOTAL_HCP_{METRIC}_CLAIMS_AGE_GROUP_{value}_IN_LAST_{1,3,6,12}_MONTH`
- PAY_TYPE: `TOTAL_HCP_{METRIC}_CLAIMS_PAY_TYPE_{value}_IN_LAST_{1,3,6,12}_MONTH`
- SOURCE_OF_BUSINESS: `TOTAL_HCP_{METRIC}_CLAIMS_SOB_{value}_IN_LAST_{1,3,6,12}_MONTH`
- RX_CHANNEL: `TOTAL_HCP_{METRIC}_CLAIMS_CHANNEL_{value}_IN_LAST_{1,3,6,12}_MONTH`
- INDICATION_GROUP: `TOTAL_HCP_{METRIC}_CLAIMS_INDICATION_GROUP_{value}_IN_LAST_{1,3,6,12}_MONTH`
- HYPERTENSION_FLAG: `TOTAL_HCP_{METRIC}_CLAIMS_{...}_HYPERTENSION_FLAG_{value}_IN_LAST_{1,3,6,12}_MONTH`
- GENDER: `TOTAL_HCP_{METRIC}_CLAIMS_{...}_GENDER_{value}_IN_LAST_{1,3,6,12}_MONTH`
- Running totals: `{column}_RUNNING_TOTAL` (P1-P4 PRODUCT_GROUP only; all other 10 dimensions keep running totals)

### 4.4 Competitor share notebook (31)

| Area | Change | Features added | Features removed | Net |
| --- | --- | --- | --- | --- |
| SGLT2i set (#8) | Add Inpefa (5 competitors) | +1 | -4 (old 4) | -3 |
| MRA share (#9) | New: Kerendia / (Kerendia + Spironolactone + Eplerenone) | +4 (4 windows) | 0 | +4 |
| HF drug share (#10) | New: Kerendia / (Kerendia + Entresto + Verquvo + Inpefa + Farxiga + Jardiance) | +4 (4 windows) | 0 | +4 |
| Key column (#11) | NPI_NUMBER -> PROVIDER_ID | 0 | 0 | 0 |
| Lag windows (#12) | Add 1, 3, 6-month (currently only 12) | +35 (3 windows x 3 share groups + SGLT2i) | 0 | +35 |
| **Total** | | | | **+40** |

### 4.3 INDICATION_GROUP derivation (#5)

V6's INDICATION_GROUP is pre-computed (T2D, CKD, HF, CVD and combinations). T1D is NOT in V6. We keep V6's values and add T1D:

| DM_TYPE (from Dx mapping) | HF_TYPE (from Dx mapping) | INDICATION_GROUP (new value) |
| --- | --- | --- |
| T1D | (none) | T1D |
| T1D | any | T1D + HF |
| (existing V6 values kept) | | (T2D, CKD, HF, T2D + CVD, etc.) |

This is applied by identifying PROVIDER_IDs with T1D diagnosis codes (from `Kerendia_Dx_Final_Product_Mapping.csv` where `DM_TYPE = T1D`) and setting their INDICATION_GROUP to include T1D.

---

## 5. Data readiness

| Data | Location | Coverage / key | Status | Gap / action | Owner |
| --- | --- | --- | --- | --- | --- |
| V6 LAAD LRx table | `KERENDIA_LAAD_BASED_LRX_V6` | 11 pivot dimensions pre-computed; PROVIDER_ID; NBRX, NRX, TRX; PERIOD_ID; WEEK_ENDING_DATE | **Ready** | Primary and only data source; same as NBA 3.0. Filter PRODUCT_GROUP to exclude DROP groups. | NBA team |
| step23 function helper | `00_Helper_Notebooks/00_step23_function` | step2_fill_missing, step3_lag functions | **Ready** | Load via %run; same as NBA 3.0 | NBA team |
| Connection helper | `00_Helper_Notebooks/00_connection` | Spark session, imports | **Ready** | Load via %run | NBA team |
| Config helper | `00_Helper_Notebooks/00_config` | Global config, date parameters | **Ready** | Load via %run | NBA team |
| Product group mapping v4 | `Product_Group_Mapping/Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv` | 487 products -> 85 groups; KEEP (340), RECLASSIFY (70), DROP (19), ADD (3); P1-P6 | **Ready** | Apply DROP exclusion and RECLASSIFY rules before pivoting | NBA team |
| Final product mapping | `kerendia_nba_3_1_volume/final_product_mapping/` | 5 merged CSVs: Rx (367 rows/18 cols), Dx (240/19), Px (145/16), Lab (28/15), Dx Flag Additions (116/15) | **Ready** | Use for DROP exclusion, T1D identification, and competitor share grouping | NBA team |
| HCP universe | `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/` | 294,727 HCPs; PROVIDER_ID; C1-C5 flags | **Ready** | Inner-join on PROVIDER_ID | NBA team |
| Claims cohorts | `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` | 28 cohorts (c1-c28); cohort_id, prediction_month, lookback_start_date, lookback_end_date | **Ready** | Cross-join with HCP universe; filter claims to each cohort's lookback window | NBA team |
| Cohort helper notebooks | `00_Helper_Notebooks/00_cohort_config`, `00_cohort_generation` | Parameters, CohortGenerator API | **Ready** | Load via %run in feature notebooks | NBA team |
| TREATMENT_CATEGORY | `Kerendia_Rx_Final_Product_Mapping.csv` column | Drug class per product (SGLT2, MRA, ACE/ARB, etc.) | **Ready** | Use for competitor share grouping (#8-#10) | NBA team |
| DM_TYPE / HF_TYPE | `Kerendia_Dx_Final_Product_Mapping.csv` columns | T1D, T2D, OTHER per diagnosis code; HFPEF_PROXY, HFREF_PROXY per HF code | **Ready** | Use for INDICATION_GROUP derivation with T1D (#5) | NBA team |
| CKD staging | `Kerendia_Dx_Final_Product_Mapping.csv` columns | CKD_STAGE (0-5), CKD_SUBSTAGE (3a, 3b) | **Ready** | Enables stage-specific features (not yet a recommendation; future enhancement) | NBA team |
| Lab staging | `Kerendia_Lab_Final_Product_Mapping.csv` columns | STAGE_CUTOFFS for eGFR and UACR | **Ready** | Enables lab-based CKD staging (future enhancement) | NBA team |
| Volume metrics | `Kerendia_Rx_Final_Product_Mapping.csv` columns | providers_total, nbrx_total per product | **Ready** | Use for filtering low-volume products before pivoting | NBA team |

---

## 6. Work plan

Each phase ends with a gate (section 8). Phases 2 and 3 can run in parallel with phase 1.

| Phase | Content | Main tasks | Experiments | Depends on |
| --- | --- | --- | --- | --- |
| **0. Foundations** | Set up helpers, mappings, and cohort pipeline | %run 00_connection, 00_config, 00_step23_function, 00_cohort_config; load V6 table; load v4 mapping and final product mapping CSVs; load HCP universe and 28 cohorts; cross-join HCP universe with cohorts | E0, E1 | Helpers loaded; mappings reviewed |
| **1. PRODUCT_GROUP pivot update** | Apply all 3.1 changes to PRODUCT_GROUP pivot only | Drop 7 obsolete groups; split diuretics; reclassify HF drugs from OTHERS; add 11 T1D product groups; apply P1-P6 priority-based running total and lag window pruning after step3_lag | E2, E3 | Phase 0 |
| **2. INDICATION_GROUP augmentation** | Add T1D to INDICATION_GROUP | Identify PROVIDER_IDs with T1D diagnosis codes from `Kerendia_Dx_Final_Product_Mapping.csv`; add T1D as new INDICATION_GROUP value | E4 | Phase 0 (parallel with phase 1) |
| **3. Competitor share update** | Update notebook 31 | Add Inpefa to SGLT2i set (5 competitors); add MRA share; add HF drug share; switch NPI_NUMBER to PROVIDER_ID; add 1/3/6-month windows; use step2_fill_missing and step3_lag | E5, E6 | Phase 0 (parallel with phase 1) |
| **4. All 11 pivots + cohort integration** | Wire all 11 pivot dimensions and 28-cohort pipeline | Pivot by all 11 V6 dimensions (same as 3.0); combine into df_spine; call step2_fill_missing; call step3_lag with [1, 3, 6, 12]; apply priority pruning to PRODUCT_GROUP columns; for each cohort, select features at cohort lookback_end_date; join with HCP x cohort; save keyed on HCP_COHORT_ID | E7, E8 | Phases 1, 2, 3 |
| **5. Freeze** | Final block and documentation | Feature list frozen in config; inference run reproduces training columns; documentation updated | G5 | Phase 4 |

---

## 7. How NBRx/NRx/TRx and competitor share fit in the model

| | NBRx/NRx/TRx (notebooks 26/27/28) | Competitor share (notebook 31) |
| --- | --- | --- |
| What it measures | HCP's prescription volume per dimension (product group, specialty, switch, add-on, age, pay type, source of business, channel, indication, hypertension, gender) | Kerendia's market share vs competitors (SGLT2i, MRA, HF drugs) |
| Grain | PROVIDER_ID x SVC_DT_M (month level) -> joined to HCP_COHORT_ID | PROVIDER_ID x SVC_DT_M -> joined to HCP_COHORT_ID |
| Pivot dimensions | 11 (all from V6) | 1 (PRODUCT_GROUP for competitor grouping) |
| Lag windows | 1, 3, 6, 12 months (P1-P4); 1, 12 months (P5-P6, PRODUCT_GROUP only) | 1, 3, 6, 12 months (all share groups) |
| Running totals | P1-P4 only (PRODUCT_GROUP); all groups (other 10 dimensions) | Not applicable (share is a ratio) |
| Computation engine | step2_fill_missing + step3_lag from 00_step23_function | step2_fill_missing + step3_lag from 00_step23_function |
| Output size | ~1,075 columns per notebook | ~24 share features |
| Key to model | PROVIDER_ID -> HCP_COHORT_ID (cross-join with cohorts) | PROVIDER_ID -> HCP_COHORT_ID |
| Output path | `kerendia_nba_3_1_volume/notebook_output/hcp_features/{nbrx,nrx,trx}_features/` | `kerendia_nba_3_1_volume/notebook_output/hcp_features/competitor_share_features/` |

---

## 8. Experiments and readiness gates

All experiments use the NBA 3.1 HCP-level model, target and validation split; only the NBRx/NRx/TRx and competitor share block changes.

| Exp. | Block | Question |
| --- | --- | --- |
| E0 | NBA 3.0 block (V6, 11 dimensions, 74 groups, ~1,337 cols per notebook, 4 competitor features) | Baseline |
| E1 | E0 with v4 DROP exclusion and RECLASSIFY applied | Effect of pruning obsolete products and reclassifying |
| E2 | E1 + diuretics split + T1D/HF new product groups | Does disease-specific grouping add value? |
| E3 | E2 + P5-P6 running total and lag window pruning | Does reducing low-priority columns improve or hurt? |
| E4 | E2 + INDICATION_GROUP with T1D (from DM_TYPE) | Does T1D distinction add value? |
| E5 | E0 competitor block + Inpefa + MRA share + HF drug share | Do new competitor shares add value? |
| E6 | E5 + 1/3/6-month windows + PROVIDER_ID key | Do shorter windows and key alignment improve? |
| E7 | Best NBRx/NRx/TRx + best competitor share, all 28 cohorts, all 11 dimensions | Does the cohort pipeline reproduce training columns? |
| E8 | Best so far, trained on different cohort splits | Is importance stable across time folds? |

**Measures:** NBA 3.1 validation metric; SHAP share of NBRx/NRx/TRx families; rank of the best NBRx and competitor share features; number of features kept; stability of importance across time folds; and, for each kept feature, whether it maps to a product group, drug class or share group the business recognises.

| Gate | Ready when |
| --- | --- |
| G0 | Product mapping v4 reviewed; DROP and RECLASSIFY applied; final_product_mapping CSVs loaded; CohortGenerator configured; E0 and E1 run |
| G1 | Pruning and reclassification applied to all 3 notebooks; diuretics split verified; T1D/HF groups added; E2 and E3 compared with E0 |
| G2 | INDICATION_GROUP with T1D derived; DM_TYPE and HF_TYPE joined from final product mapping; HYPERTENSION_FLAG derived; E4 run |
| G3 | Competitor share notebook updated with Inpefa, MRA share, HF drug share; PROVIDER_ID key; 1/3/6-month windows; E5 and E6 run |
| G4 | All 28 cohorts wired; per-cohort output verified; training columns reproduced at inference; E7 run |
| **G5 (freeze)** | E8 run; stability checked; final feature list frozen in config; documentation updated |

---

## 9. Roles

| Area | NBA team | Data engineering | Brand team |
| --- | --- | --- | --- |
| V6 table, helpers, step2/step3 | Uses as-is from 3.0 | Maintains |  |
| Product mapping v4, DROP/RECLASSIFY rules | Builds and applies | Reviews |  |
| Final product mapping CSVs | Uses for T1D and competitor grouping | Maintains in volume |  |
| T1D/HF product group additions | Builds the new pivot columns |  | Confirms clinical relevance |
| INDICATION_GROUP derivation | Implements from DM_TYPE/HF_TYPE |  |  |
| Competitor share updates (Inpefa, MRA, HF) | Builds the new share features |  | Confirms competitor set |
| Cohort pipeline integration | Implements CohortGenerator cross-join | Configures cohort parameters |  |
| Experiments, gates, freeze | Owns | Reviews | Reviews results |

---

## 10. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| T1D product groups are sparse (insulin/CGM/pumps) | Many near-zero columns in PRODUCT_GROUP pivot | Let feature selection drop them; P4 priority ensures they get full lag windows |
| New product groups increase PRODUCT_GROUP columns before pruning | Temporary column bloat in PRODUCT_GROUP pivot | Pruning (P5-P6 running totals and lag windows) offsets additions; net is ~-255 per notebook |
| Competitor share with 5 SGLT2i is unstable for small HCPs | Inflated or zero share | Apply minimum volume threshold (e.g., total NBRx >= 10) before computing share |
| Cohort cross-join produces ~8.25M rows (294K x 28) | Memory and compute pressure | Process per-cohort in a loop; save intermediate parquet per cohort |
| Product mapping CSVs use LIST type with pipe-separated values | Requires parsing to expand clubbed products | Parse at load time; join on CLUB_ID for clubbed rows and MATCH_VALUE for NAME rows |
| INDICATION_GROUP T1D augmentation requires joining with Dx mapping | Additional join step | Join on DIAGNOSIS_CODE; identify T1D PROVIDER_IDs from the Dx mapping |
| V6 table is very large (3.2B+ rows) | Compute pressure | Filter to HCP universe early; process per-cohort |

---

## 11. Next actions

| # | Action | Owner |
| --- | --- | --- |
| 1 | Review this plan with the NBA and data engineering teams | NBA team |
| 2 | Load helpers: 00_connection, 00_config, 00_step23_function, 00_cohort_config | NBA team |
| 3 | Load V6 table and apply DROP exclusion to PRODUCT_GROUP | NBA team |
| 4 | Split DIURETICS AND COMBOS into LOOP / THIAZIDE / K-SPARING using v4 mapping | NBA team |
| 5 | Add 11 T1D product groups and 3 HF drug groups from v4 mapping to PRODUCT_GROUP | NBA team |
| 6 | Apply P1-P6 priority-based running total and lag window pruning to PRODUCT_GROUP | NBA team |
| 7 | Augment INDICATION_GROUP with T1D from DM_TYPE in `Kerendia_Dx_Final_Product_Mapping.csv` | NBA team |
| 8 | Pivot by all 11 V6 dimensions; combine into df_spine; call step2_fill_missing and step3_lag | NBA team |
| 9 | Update competitor share notebook: add Inpefa, MRA share, HF drug share, PROVIDER_ID, 1/3/6-month windows | NBA team |
| 10 | Wire all 4 notebooks to the 28-cohort pipeline via CohortGenerator | NBA team |
| 11 | Save output to `kerendia_nba_3_1_volume/notebook_output/hcp_features/` | NBA team |
| 12 | Run E0-E8 experiments and compare with NBA 3.0 baseline | NBA team |
| 13 | Freeze final feature list in config and update documentation | NBA team |

---

## 12. Spark Connect compatibility: code patterns and fixes (learned during job runs)

The NBA 3.1 notebooks run on serverless compute with Spark Connect, which differs from classic Spark in several ways. The following errors were encountered and fixed during the job pipeline test and full universe runs. **When regenerating notebooks from this plan, apply all of these patterns to avoid repeating the same failures.**

### 12.1 %run must be one per cell

**Error:** `Failed to parse %run command: string matching regex '$[\w_]+' expected but '%' found`

**Cause:** Databricks `%run` cell magic only supports ONE notebook per cell. Multiple `%run` commands in the same cell cause a parse error.

**Fix:** Put each `%run` in its own cell, as the very first line of that cell (no comments before it). Example:

```
Cell 1: %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
Cell 2: %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
Cell 3: %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function"
Cell 4: # Configuration cell (imports, constants, widgets)
```

### 12.2 StorageLevel import

**Error:** `ImportError: cannot import name 'StorageLevel' from 'pyspark.sql'`

**Cause:** In Spark Connect, `StorageLevel` is not available in `pyspark.sql`.

**Fix:** Import from `pyspark.storagelevel`:
```python
from pyspark.storagelevel import StorageLevel
```

### 12.3 HCP universe is parquet, not Delta

**Error:** `DELTA_MISSING_TRANSACTION_LOG: Incompatible format detected`

**Cause:** The HCP universe at `HCP_Universe_without_call_hcps/` is stored as parquet files, not as a Delta table.

**Fix:** Use `spark.read.parquet(HCP_UNIVERSE_PATH)`, not `spark.read.format("delta").load(HCP_UNIVERSE_PATH)`.

### 12.4 PERIOD_ID is a DATE column

**Error:** `CAST_INVALID_INPUT: The value '20200101' of the type STRING cannot be cast to DATE` and `CANNOT_PARSE_TIMESTAMP: Text '2023-10-27' could not be parsed at index 4`

**Cause:** The V6 table's `PERIOD_ID` column is a DATE type (stored as `2023-10-27`), not a string in `yyyyMMdd` format. The NBA 3.0 code used `substring('PERIOD_ID', 1, 4)` which passed a literal string instead of a column reference, and `F.to_date(F.unix_timestamp(...).cast('timestamp'))` which fails in Spark Connect.

**Fix:** Use `F.trunc()` directly on the DATE column:
```python
hcp_lrx_claims = hcp_lrx_claims.withColumn("SVC_DT_M", F.trunc(col("PERIOD_ID"), 'month'))
```
Do NOT use:
- `substring('PERIOD_ID', 1, 4)` (passes a literal string, not a column)
- `F.to_date(F.unix_timestamp(col, 'yyyyMMdd').cast('timestamp'))` (fails in Spark Connect)
- `F.to_date(col('PERIOD_ID').cast('string'), 'yyyyMMdd')` (PERIOD_ID is already a DATE, not yyyyMMdd string)

Also, do NOT add `WHERE PERIOD_ID >= '20200101'` to the SQL query -- this causes a cast error because PERIOD_ID is a DATE and '20200101' is not a valid date string.

### 12.5 Python sum() intercepted by Spark Connect

**Error:** `PySparkTypeError: Argument 'col' should be Column or str, got generator`

**Cause:** In Spark Connect, the built-in `sum()` function is intercepted as `F.sum()` (Spark SQL aggregate function), which expects a single Column or str, not a generator of columns. The NBA 3.0 competitor notebook used `sum(when(col(c).isNotNull(), col(c)).otherwise(0) for c in col_list)` for row-wise column addition.

**Fix:** Use `reduce()` with `+` and `F.coalesce()`:
```python
from functools import reduce
df = df.withColumn('TOTAL', reduce(lambda a, b: a + b, [F.coalesce(col(c), F.lit(0)) for c in col_list]))
```

### 12.6 Do not unpersist cached DataFrames before all downstream uses

**Error:** `CACHE_DATAFRAME_ACCESS_AFTER_UNCACHE: This DataFrame, or a DataFrame it was derived from, has been uncached and can no longer be accessed`

**Cause:** The NBA 3.1 code called `hcp_lrx_claims.unpersist()` after building `df_spine` from pivot DataFrames derived from `hcp_lrx_claims`. When `step2_fill_missing(df_spine, ...)` later tried to materialize `df_spine`, it needed to recompute from `hcp_lrx_claims` lineage, which was already uncached.

**Fix:** Do NOT call `unpersist()` on a cached DataFrame until ALL downstream DataFrames derived from it have been fully materialized (written to disk). Simply remove the `unpersist()` call -- the cache is cleaned up when the notebook ends.

### 12.7 Clean column names after pivot (Delta compatibility)

**Error:** `DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES: Found invalid character(s) among ' ,;{}()\n\t=' in the column names`

**Cause:** Pivot column names from V6's `PRODUCT_GROUP` dimension contain spaces (e.g., `CANAGLIFLOZIN_INVOKANA COMBOS`, `MINERALOCORTICOID RECEPTOR ANTAGONISTS`). After `step3_lag` processes these, the lag columns inherit the spaces (e.g., `CANAGLIFLOZIN_INVOKANA COMBOS_IN_LAST_1_MONTH`). Delta does not allow spaces in column names.

**Fix:** Apply a `clean_col_name()` function to all pivot column names immediately after pivoting, before any downstream processing:
```python
def clean_col_name(c):
    return c.replace(", ", " ").replace("+", "and").replace("/", " or ").replace("-", "_").replace(" ", "_").replace("__", "_").replace("(", "").replace(")", "").replace("&", "").upper()

df_pivot = df_pivot.select([F.col(c).alias(clean_col_name(c)) if c not in index_cols else col(c) for c in df_pivot.columns])
```
Also clean the competitor group names used for column matching:
```python
cleaned_groups = [clean_col_name(c) for c in all_competitor_groups]
cols = [c for c in df.columns if any(cg in c for cg in cleaned_groups)]
```

### 12.8 Helper notebook paths

The NBA 3.0 helper notebooks are used as-is (they are not copied to the 3.1 dev folder):

| Helper | Path |
| --- | --- |
| 00_connection | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection` |
| 00_config | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config` |
| 00_step23_function | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function` |

The `00_cohort_config` notebook is NOT needed for the feature notebooks -- cohorts are loaded directly from `cohorts.parquet` at `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet`.

### 12.9 Summary table: errors and fixes

| # | Error | Root cause | Fix |
| --- | --- | --- | --- |
| 1 | `Failed to parse %run command` | Multiple %run in one cell | One %run per cell |
| 2 | `ImportError: StorageLevel from pyspark.sql` | Wrong import path | `from pyspark.storagelevel import StorageLevel` |
| 3 | `DELTA_MISSING_TRANSACTION_LOG` | HCP universe is parquet, not Delta | `spark.read.parquet()` |
| 4 | `CAST_INVALID_INPUT: '20200101' cannot be cast to DATE` | PERIOD_ID is DATE type; substring on literal string | `F.trunc(col("PERIOD_ID"), 'month')` |
| 5 | `PySparkTypeError: sum() got generator` | Spark Connect intercepts sum() as F.sum() | `reduce(lambda a, b: a + b, [...])` |
| 6 | `CACHE_DATAFRAME_ACCESS_AFTER_UNCACHE` | unpersist() called before downstream use | Remove unpersist() call |
| 7 | `DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES` | Spaces in pivot column names | Apply clean_col_name() after pivot |
| 8 | `File not found: 00_cohort_config` | Not needed; cohorts loaded from parquet | Remove %run 00_cohort_config |
