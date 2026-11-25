# NBA 3.1 Kerendia NBRx / NRx / TRx and Competitor Drug NBRx Share Features: Changes

This file lists the recommended changes for NBA 3.1: which features to prune, which to add, how the competitor share notebook should be updated, and what new product mapping we are using. How the NBA 3.0 features are built is in the companion file `11_nbrx_nrx_trx_and_competitor_share_features_analysis.md`. References written as "Analysis x" point to sections in that file.

NBA 3.1 scope: the model target is the HCP's **Kerendia NBRx in the 30-day prediction window**. Kerendia now covers **T2D with CKD, T1D with CKD and HF with LVEF >= 40%**. The HCP universe is expanded from ~222K (NBA 3.0) to **294,727 HCPs** (`kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/`), with cohort flags C1-C5 for the expanded indication groups.

SHAP ranks and shares referenced from `Final NBA 3.0 Modeling Features.xlsx` (752 features, mean absolute SHAP).

---

## 1. Summary of recommended changes

| # | Feature group | Action | Reason |
| --- | --- | --- | --- |
| 1 | Product Group pivot (all 3 notebooks) | **Filter to v4 KEEP groups** (85 → ~75 groups) | 19 product groups marked DROP in v4 mapping (obsolete, withdrawn, near-zero volume). Removes ~75 feature columns × 5 lag/running columns per notebook |
| 2 | Diuretics dimension split | **Apply v4 reclassification** (DIURETICS AND COMBOS → LOOP / THIAZIDE / K-SPARING) | Loop diuretics are a strong HF signal. The combined group dilutes this signal. v4 already defines the split |
| 3 | HF drug groups | **Add 3 new product groups** (HF RATE CONTROL, HF VASODILATORS, CARDIAC GLYCOSIDES) | HF-GDMT drugs (ivabradine, hydralazine/isosorbide, digoxin) are reclassified from OTHERS in v4. They capture HF prescribing intensity |
| 4 | T1D product groups | **Add T1D-specific groups** (T1D DISEASE-MODIFY, GLUCAGON RESCUE, insulin families, CGM systems, insulin pumps) | T1D expansion requires insulin/CGM/pump features. These are reclassified from OTHERS or newly added in v4 |
| 5 | INDICATION_GROUP dimension | **Derive from DIAGNOSIS_CODE** using the final product mapping | T1D is not a separate indication group in V6. The expanded scope needs T1D vs T2D vs HF distinction. Use `DM_TYPE` from `Kerendia_Dx_Final_Product_Mapping.csv` (see section 2) |
| 6 | Running totals for low-priority groups | **Drop running totals for P5-P6 groups** | Running totals grow unboundedly and add little signal beyond the 12-month window for low-prevalence products. Keeps running totals only for P1-P4 groups |
| 7 | Lag windows for sparse groups | **Reduce to 1 and 12-month windows for P5-P6 groups** | 3 and 6-month windows are highly correlated with 1 and 12-month for sparse products. Reduces ~40% of lag columns for low-priority groups |
| 8 | Competitor share: SGLT2i set | **Add Inpefa** to the 4-competitor SGLT2i set | Inpefa (sotagliflozin) is approved for HF and is in the v4 KEEP list and the final product mapping. It is a direct SGLT2i competitor in the HF space |
| 9 | Competitor share: MRA share | **Add MRA competitor share** (Kerendia vs spironolactone vs eplerenone) | Kerendia is an MRA. An MRA share feature captures Kerendia's position in the MRA market, distinct from SGLT2i share |
| 10 | Competitor share: HF drug share | **Add HF drug share** (Entresto, Verquvo, Kerendia, Inpefa) | For the HF indication, Kerendia competes with ARNI (Entresto) and sGC stimulators (Verquvo). An HF drug share captures Kerendia's HF market position |
| 11 | Competitor share: key column | **Switch from NPI_NUMBER to PROVIDER_ID** | Aligns with the rest of the pipeline (26/27/28 use PROVIDER_ID). Avoids the NPI-to-PROVIDER_ID mapping in the combine step |
| 12 | Competitor share: lag windows | **Add 1, 3, 6-month windows** (currently only 12-month) | Shorter windows capture recent shifts in competitor share. The 12-month window alone misses rapid market changes |
| 13 | HCP universe | **Use the updated NBA 3.1 universe** (294,727 HCPs) | The expanded scope includes HCPs treating T1D and HF patients. The old universe (~222K) misses these HCPs |
| 14 | 11 pivot dimensions | **Keep all 11 V6 pivot dimensions** (PRODUCT_GROUP, SPECIALTY_GROUP, SWITCH_FROM, ADD_ON_TO, AGE_GROUP, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL, INDICATION_GROUP, HYPERTENSION_FLAG, GENDER) | V6 has all 11 dimensions pre-computed. No switch to raw claims is needed. SWITCH_FROM and ADD_ON_TO are available in V6. Only the PRODUCT_GROUP pivot is updated (DROP/split/add/prune); INDICATION_GROUP is augmented with T1D; the other 9 dimensions are kept as-is |
| 15 | Cohorts | **Use the NBA 3.1 claims-type cohorts** (`kerendia_nba_3_1_volume/cohorts/claims/`) | NBA 3.1 generates 28 cohorts (c1-c28) via the `00_cohort_generation` helper notebook. Claims feature family uses offset 0, 12-month lookback, 1-month data lag. The NBRx/NRx/TRx and competitor share notebooks must join on `HCP_COHORT_ID` and read each cohort's `lookback_start_date` / `lookback_end_date` from `cohorts.parquet` |
| 16 | Product mapping | **Use the final product mapping** from `kerendia_nba_3_1_volume/final_product_mapping/` | The v4 mapping (`Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`) maps 487 products to 85 groups with actions KEEP (340), RECLASSIFY (70), DROP (19), ADD (3). The merged mapping CSVs add clinical metadata (TREATMENT_CATEGORY, DM_TYPE, HF_TYPE, CKD_STAGE) and volume metrics (providers_total, nbrx_total). See section 2 |

---

## 2. Product mapping: NBA 3.0 vs NBA 3.1

### 2.1 Where the 3.1 product mapping comes from

NBA 3.0 used the IQVIA LAAD LRx V6 table (`KERENDIA_LAAD_BASED_LRX_V6`) as the primary data source, with product mapping embedded in V6's pre-computed `PRODUCT_GROUP` column (~74 groups). **NBA 3.1 keeps V6 as the only data source** and supplements it with a new product mapping at:

`/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/final_product_mapping/`

| File | Rows | What it maps |
| --- | --- | --- |
| `Kerendia_Rx_Final_Product_Mapping.csv` | 367 | NDC-to-product-group with drug class, condition, and volume metrics |
| `Kerendia_Dx_Final_Product_Mapping.csv` | 240 | ICD-10-to-condition with CKD stage, DM type, HF type |
| `Kerendia_Px_Final_Product_Mapping.csv` | 145 | CPT/HCPCS-to-procedure-group with dialysis flags |
| `Kerendia_Lab_Final_Product_Mapping.csv` | 28 | LOINC-to-test-type with CKD staging cutoffs |
| `Kerendia_Dx_Flag_Additions.csv` | 116 | Expanded ICD-10 codes for T1D/T2D flag-level features |

The NDC-to-product-group mapping is defined by the v4 mapping (`Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`): 487 products mapped to 85 product groups with actions KEEP (340), RECLASSIFY (70), DROP (19), ADD (3) and priorities P1-P6.

### 2.2 New mapping columns (not in V6)

The V6 table has **11 pivot dimensions**: PRODUCT_GROUP, SPECIALTY_GROUP, SWITCH_FROM, ADD_ON_TO, AGE_GROUP, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL, INDICATION_GROUP, HYPERTENSION_FLAG, GENDER. All 11 are kept in NBA 3.1. The 3.1 mapping supplements V6 with the following useful columns:

| New column | File | What it provides | How it is used |
| --- | --- | --- | --- |
| `TREATMENT_CATEGORY` | Rx | Drug class (SGLT2, MRA, ACE/ARB, Diuretic_NON_MRA, Insulin) | Directly drives competitor share grouping (#8-#10). Replaces manual drug-class lookups |
| `CONDITION` | Rx, Dx, Px | Maps each product/code to a condition (T2D, CKD, HF, HTN, T1D, etc.) | Replaces V6 INDICATION_GROUP. Provides condition-level grouping across all event types |
| `DM_TYPE` | Dx | T1D, T2D, OTHER per diagnosis code | **Critical for T1D expansion.** V6 had no T1D. Directly distinguishes T1D from T2D prescribers |
| `HF_TYPE` | Dx | HFPEF_PROXY, HFREF_PROXY, COMBINED, UNKNOWN | Distinguishes HFpEF (Kerendia target) from HFrEF. V6 had no HF type |
| `CKD_STAGE` | Dx | CKD stage 0-5 (0 = unknown, 5 = ESRD) | Enables stage-specific features. V6 had no CKD staging |
| `CKD_SUBSTAGE` | Dx | CKD substage 3a, 3b | Further granularity within stage 3 (Kerendia target range) |
| `FLAG` | Dx | Additional flags: PROTEINURIA, DIALYSIS, KIDNEY_CV, HF | Enables flag-level features. V6 had no flag column |
| `ACTIVE_STAGING` | Dx | Y/N: whether the code is used for CKD staging | Controls which diagnosis codes contribute to CKD stage classification |
| `PX_GROUP` | Px | Procedure group: ESRD_MONTHLY, DIALYSIS_SESSION, DIALYSIS_ACCESS, DIALYSIS_DRUG | Procedure grouping for dialysis features. V6 had no procedure group |
| `ACTIVE_DIALYSIS` | Px | Y/N: whether the procedure is a dialysis session | Direct dialysis flag for feature engineering |
| `TEST_TYPE` | Lab | GFR, UACR, POTASSIUM, HBA1C | Classifies lab tests by clinical purpose. V6 had no lab test type |
| `STAGE_CUTOFFS` | Lab | CKD staging cutoffs (e.g., eGFR `15:5|30:4|60:3|90:2|else:1`, UACR `30:1|300:2|else:3`) | Enables lab-based CKD staging from eGFR and UACR values |
| `TEST_FAMILY` | Lab | Test family (eGFR, UACR, Potassium, HbA1c) | Groups related lab tests for feature engineering |
| `PRIORITY` | Rx, Lab | Priority ranking P1-P6 (Rx) or 1-3 (Lab) | Guides feature pruning - low-priority groups get fewer lag windows (#6, #7) |
| `providers_total`, `nbrx_total` | Rx | Provider count and NBRx count per product | Volume-based filtering of low-volume products before pivoting |
| `ACTIVE_JOURNEY` | Rx | Y/N: whether the product is in the patient journey view | Filters to clinically relevant products |
| `IS_DEFINING` | Dx, Px | Y/N: whether the code is a defining diagnosis/procedure | Identifies primary vs secondary codes for condition classification |

### 2.3 New product groups added (not in V6)

| New product group | Products | Priority | Why added for 3.1 |
| --- | --- | --- | --- |
| T1D DISEASE-MODIFYING | Tzield (teplizumab) | P4 | Only T1D disease-modifying agent. New for T1D expansion |
| GLUCAGON RESCUE | Baqsimi, Gvoke, Zegalogue | P4 | T1D/insulin-treated hypoglycemia rescue. High-specificity T1D signal |
| LANTUS INSULIN GLARGINE FAMILY | Lantus, Basaglar, Toujeo | P3 | Long-acting insulin. Higher T1D prevalence than T2D |
| HUMALOG INSULIN LISPRO | Humalog, Ademolog | P3 | Rapid-acting insulin. T1D and T2D |
| NOVOLOG INSULIN ASPART | Novolog, Fiasp | P3 | Rapid-acting insulin. T1D and T2D |
| TRESIBA INSULIN DEGLUDEC | Tresiba | P3 | Ultra-long-acting insulin |
| LEVEMIR INSULIN DETEMIR | Levemir | P3 | Long-acting insulin. More T1D-specific than Lantus |
| FREESTYLE LIBRE CGM | FreeStyle Libre variants | P4 | CGM used primarily by insulin-treated patients |
| DEXCOM CGM SYSTEM | Dexcom G6/G7 | P4 | CGM. T1D signal |
| OMNIPOD INSULIN PUMP | OmniPod variants | P4 | Insulin pump. Almost exclusively T1D |
| TANDEM INSULIN PUMP | Tandem variants | P4 | Insulin pump. Almost exclusively T1D |
| LOOP DIURETICS | Furosemide, Bumetanide, Torsemide, Ethacrynic Acid, Furoscix, Soaanz | P4 | Split from DIURETICS AND COMBOS. Loop diuretics are a primary HF signal |
| THIAZIDE DIURETICS | Hydrochlorothiazide, Chlorthalidone, Metolazone, Indapamide, Chlorothiazide | P5 | Split from DIURETICS AND COMBOS. Hypertension/CKD signal |
| K-SPARING DIURETICS | Amiloride, Triamterene, Dyazide, Maxzide, Dyrenium | P5 | Split from DIURETICS AND COMBOS. K-sparing overlaps with MRA mechanism |
| HF RATE CONTROL | Corlanor, Ivabradine HCL | P4 | HF-GDMT for elevated heart rate. Reclassified from OTHERS |
| HF VASODILATORS | Bidil, Isosorbide/Hydralazine | P4 | HF-GDMT for NYHA III-IV. Reclassified from OTHERS |
| INPEFA | Inpefa (sotagliflozin) | P1 | SGLT2i approved for HF. New direct competitor to Kerendia |
| GLP-1 brands | Mounjaro, Zepbound, Wegovy, Wegovy HD | P2-P3 | New GLP-1/GIP agonists not in V6 as separate groups |

### 2.4 Product groups dropped (in V6, removed in 3.1)

| Dropped group | Products | Why dropped |
| --- | --- | --- |
| BEXAGLIFLOZIN | Bexagliflozin | 42 HCPs, 48 TRx. SGLT2i withdrawn from US market |
| ADLYXIN | Adlyxin | 21 HCPs, 31 TRx. Lixisenatide discontinued US 2023 |
| CYCLOSET | Cycloset | No CKD/HF/CVD mechanistic link |
| MIGLITOL | Miglitol, Glyset | No CKD/HF/CVD link, niche |
| TEKTURNA | Tekturna, Tekturna HCT | Direct renin inhibitor, largely withdrawn |
| ACTOS | Actos, Pioglitazone HCL | 0.2% prevalence, generic captures same molecule |
| PIOGLITAZONE_ACTOS COMBOS | Actoplus Met, Avandia, Duetact | 71 HCPs, near-dead TZD combos |
| Obsolete sulfonylureas | Chlorpropamide, Diabeta | 3 HCPs, 3 TRx. Obsolete first-gen |
| Obsolete others | Tanzeum, Tolbutamide | Discontinued GLP-1 / obsolete sulfonylurea |

### 2.5 Products reclassified (moved between groups)

| Product | 3.0 group | 3.1 group | Why |
| --- | --- | --- | --- |
| Corlanor, Ivabradine HCL | OTHERS | HF RATE CONTROL | HF-GDMT, reclassified for HF signal specificity |
| Bidil, Isosorbide/Hydralazine | OTHERS | HF VASODILATORS | HF-GDMT, reclassified for HF signal specificity |
| Furosemide, Bumetanide, etc. | DIURETICS AND COMBOS | LOOP DIURETICS | Split for HF signal specificity |
| Hydrochlorothiazide, etc. | DIURETICS AND COMBOS | THIAZIDE DIURETICS | Split for hypertension/CKD specificity |
| Amiloride, Triamterene, etc. | DIURETICS AND COMBOS | K-SPARING DIURETICS | Split, K-sparing overlaps MRA mechanism |
| Spironolactone combos (Aldactazide, Carospir) | DIURETICS AND COMBOS | MINERALOCORTICOID RECEPTOR ANTAGONISTS | Reclassified to MRA group |
| Tzield | OTHERS | T1D DISEASE-MODIFYING | Only T1D disease-modifying agent |
| Baqsimi, Gvoke, Zegalogue | OTHERS | GLUCAGON RESCUE | T1D/insulin hypoglycemia rescue |
| GLYXAMBI | OTHERS | EMPAGLIFLOZIN_JARDIANCE COMBOS | Empagliflozin/linagliptin combo |
| SEGLUROMET | OTHERS | ERTUGLIFLOZIN_STEGLATRO COMBOS | Ertugliflozin/metformin combo |
| JANUMET, JANUMET XR | OTHERS | JANUVIA | Sitagliptin/metformin combo to parent molecule |
| Cinacalcet, Parsabiv, Sensipar | OTHERS | CALCIMIMETICS | CKD-SHPT calcimimetics |
| XPHOZAH | OTHERS | PHOSPHATE BINDERS | Tenapanor phosphate absorption inhibitor |
| KORSUVA | OTHERS | CKD SYMPTOM MGMT | Difelikefalin for CKD pruritus |

### 2.6 Why the 3.1 mapping is better

| Dimension | 3.0 (V6) | 3.1 (final product mapping) | Improvement |
| --- | --- | --- | --- |
| Product groups | ~74, many obsolete | 85 (v4), 19 dropped, 11+ new, 70 reclassified | Removes noise; adds T1D/HF-specific signal |
| Drug class | Not available | `TREATMENT_CATEGORY` (SGLT2, MRA, ACE/ARB) | Direct competitor share grouping |
| T1D distinction | Not in INDICATION_GROUP | `DM_TYPE` (T1D, T2D, OTHER) | T1D prescribers visible as separate group |
| HF type | HF only (no subtype) | `HF_TYPE` (HFPEF_PROXY, HFREF_PROXY, COMBINED) | Distinguishes HFpEF (Kerendia target) from HFrEF |
| CKD staging | Not available | `CKD_STAGE` (0-5), `CKD_SUBSTAGE` (3a, 3b) | Stage-specific features. Stage 3 separable |
| Lab staging | Not available | `STAGE_CUTOFFS` for eGFR and UACR | Lab-based CKD staging from raw lab results |
| Diuretics | One group | Three groups (Loop, Thiazide, K-sparing) | Loop diuretics = direct HF signal, no longer diluted |
| HF drugs | Hidden in OTHERS | Separate groups (HF RATE CONTROL, HF VASODILATORS) | HF prescribing intensity is a direct feature |
| Insulin/CGM/pumps | Not separate groups | 11 new groups | T1D prescribing signal captured |
| Volume metrics | Not in mapping | `providers_total`, `nbrx_total` | Data-driven filtering of low-volume products |
| Product priority | Not available | P1-P6 per product group | Guides feature pruning (fewer lag windows for low priority) |
| Obsolete products | Included | Dropped (19 products, 7 groups) | Removes ~105 noise feature columns |
| Diagnosis flags | Not available | `FLAG` (PROTEINURIA, DIALYSIS, KIDNEY_CV, HF) | Additional clinical flags for features |
| Dialysis procedures | Not grouped | `PX_GROUP` + `ACTIVE_DIALYSIS` | Direct dialysis feature flag |
| Cohort integration | Single COHORT_MONTH | 28 cohorts (c1-c28) via CohortGenerator | Same notebook produces all training/testing/holdout features |

---

## 3. NBRx / NRx / TRx features: what to prune

### 3.1 Drop product groups marked DROP in v4 (#1)

The v4 mapping marks 19 product names for DROP, covering 7 product groups:

| Dropped group | Products | Reason |
| --- | --- | --- |
| BEXAGLIFLOZIN | Bexagliflozin | 42 HCPs, 48 TRx. SGLT2i approved then immediately withdrawn from US market |
| ADLYXIN | Adlyxin | 21 HCPs, 31 TRx. Lixisenatide — discontinued in US 2023 |
| CYCLOSET | Cycloset | 1,643 HCPs, 24,659 TRX. Bromocriptine for T2D — no CKD/HF/CVD mechanistic link |
| MIGLITOL | Miglitol, Glyset | 1,225 HCPs, 12,685 TRX. Alpha-glucosidase inhibitor — no CKD/HF/CVD link, niche |
| TEKTURNA | Tekturna, Tekturna HCT | 1,331 HCPs, 6,672 TRX. Direct renin inhibitor — largely withdrawn internationally |
| ACTOS | Actos, Pioglitazone HCL | 483 HCPs, 3,141 TRX. Brand pioglitazone — 0.2% prevalence. Generic captures same molecule |
| PIOGLITAZONE_ACTOS COMBOS | Actoplus Met, Avandia, Duetact | 71 HCPs, 587 TRX. Brand TZD combos, near-dead |
| SULFONYLUREAS (obsolete) | Chlorpropamide, Diabeta | 3 HCPs, 3 TRX. Obsolete first-gen sulfonylureas |
| OTHERS (obsolete) | Tanzeum, Tolbutamide | GLP-1 RA discontinued 2018 / obsolete first-gen sulfonylurea |

**Impact**: removes ~7 product group columns × 5 (4 lag + 1 running) × 3 notebooks = ~105 feature columns. These groups have near-zero signal and waste feature selection capacity.

**Implementation**: filter the V6 query `WHERE PRODUCT_GROUP NOT IN ('BEXAGLIFLOZIN', 'ADLYXIN', 'CYCLOSET', 'MIGLITOL', 'TEKTURNA', 'ACTOS', 'PIOGLITAZONE_ACTOS COMBOS', 'SULFONYLUREAS')` before pivoting. If using the raw claims table, apply the v4 mapping and exclude DROP groups.

### 3.2 Drop running totals for low-priority groups (#6)

The v4 mapping assigns priorities P1-P6 to each product group. Running totals (`RUNNING_TOTAL_...`) grow unboundedly across the full history and are highly correlated with the 12-month lag for any group with stable prescribing.

| Priority | Groups | Keep running total? | Keep all 4 lag windows? |
| --- | --- | --- | --- |
| P1 (19 groups: core SGLT2i, MRA, Kerendia) | Yes | Yes (1, 3, 6, 12) |
| P2 (24 groups: GLP-1, ACE, ARB, beta blockers) | Yes | Yes |
| P3 (106 products: DPP-4, insulin, CGM, secondary) | Yes | Yes |
| P4 (89 products: HF drugs, glucagon, calcimimetics) | Yes | Yes |
| P5 (129 products: generics, combos, older agents) | No | 1 and 12 only |
| P6 (120 products: deprecated, niche, devices) | No | 1 and 12 only |

**Impact**: drops ~40% of running total columns and ~40% of 3/6-month lag columns. For P5-P6 groups, running totals add no signal beyond the 12-month window, and 3/6-month windows are highly correlated with 1-month.

### 3.3 Diuretics split (#2)

The v4 mapping splits `DIURETICS AND COMBOS` into three groups:

| New group | Products | Why |
| --- | --- | --- |
| LOOP DIURETICS | Furosemide, Bumetanide, Torsemide, Ethacrynic Acid, Furoscix, Soaanz | Loop diuretics are a primary HF signal. Furosemide alone has high prevalence in HF patients |
| THIAZIDE DIURETICS | Hydrochlorothiazide, Chlorthalidone, Metolazone, Indapamide, Chlorothiazide | Thiazides are hypertension/CKD signals, distinct from loop diuretics |
| K-SPARING DIURETICS | Amiloride, Triamterene, Dyazide, Maxzide, Dyrenium | K-sparing diuretics overlap with MRA mechanism. Separating avoids confusion |

The old combined `DIURETICS AND COMBOS` group dilutes the HF signal from loop diuretics. The split is already defined in v4 and should be applied in the pivot.

**Impact**: replaces 1 pivot column with 3, adding ~10 feature columns (3 groups × ~3 lag/running columns after pruning) per notebook. Net signal gain is significant because loop diuretic volume is a direct HF intensity proxy.

---

## 4. NBRx / NRx / TRx features: what to add

### 4.1 HF drug product groups (#3)

The v4 mapping reclassifies several HF-GDMT drugs from OTHERS into dedicated groups:

| New group | Products | Priority | Signal |
| --- | --- | --- | --- |
| HF RATE CONTROL | Corlanor, Ivabradine HCL | P4 | Ivabradine is HF-GDMT for elevated heart rate despite max beta-blocker. Highly specific to HF patients |
| HF VASODILATORS | Bidil, Isosorbide/Hydralazine | P4 | Hydralazine/isosorbide is HF-GDMT for NYHA III-IV. Specific to advanced HF |
| CARDIAC GLYCOSIDES | Digoxin (already in v4 mapping) | P4 | Digoxin is used for AF + HF. Captures AF/HF overlap patients |

These groups are currently hidden inside the `OTHERS` catch-all in V6. Adding them as separate pivot dimensions gives the model direct HF prescribing intensity signals.

### 4.2 T1D product groups (#4)

The expanded T1D scope requires features for insulin, CGM, and T1D-specific products:

| New group | Products | Priority | Signal |
| --- | --- | --- | --- |
| T1D DISEASE-MODIFYING | Tzield (teplizumab) | P4 | Only T1D disease-modifying agent. Highly specific to T1D |
| GLUCAGON RESCUE | Baqsimi, Gvoke, Zegalogue | P4 | Glucagon rescue is used by insulin-treated patients (T1D primarily). High-specificity T1D signal |
| LANTUS INSULIN GLARGINE FAMILY | Lantus, Basaglar, Toujeo | P3 | Long-acting insulin. Used by both T1D and T2D, but higher T1D prevalence |
| HUMALOG INSULIN LISPRO | Humalog, Ademolog | P3 | Rapid-acting insulin. T1D and T2D |
| NOVOLOG INSULIN ASPART | Novolog, Fiasp | P3 | Rapid-acting insulin. T1D and T2D |
| TRESIBA INSULIN DEGLUDEC | Tresiba | P3 | Ultra-long-acting insulin. T1D and T2D |
| LEVEMIR INSULIN DETEMIR | Levemir | P3 | Long-acting insulin. More T1D-specific than Lantus |
| FREESTYLE LIBRE CGM | FreeStyle Libre variants | P4 | CGM is used primarily by insulin-treated patients. T1D signal |
| DEXCOM CGM SYSTEM | Dexcom G6/G7 | P4 | CGM. T1D signal |
| OMNIPOD INSULIN PUMP | OmniPod variants | P4 | Insulin pump. Almost exclusively T1D |
| TANDEM INSULIN PUMP | Tandem variants | P4 | Insulin pump. Almost exclusively T1D |

These product groups are already defined in v4 as reclassifications from OTHERS or as new groups. The V6 table does not have them as separate product groups. To include them, either:
* Use the v4 mapping to remap NDC codes in the raw claims table (if using `STG_CAR_IQV_LAAD_FCT_RX`)
* Or create a derived product group column in the V6 query using CASE WHEN logic on the existing `PRODUCT_GROUP` values

**Impact**: adds ~11 new product group columns × ~3 lag columns (1 and 12-month + running) = ~33 feature columns per notebook. These are the highest-value additions because they capture the T1D prescribing signal that was previously invisible.

### 4.3 INDICATION_GROUP from diagnosis codes (#5)

The V6 table has an `INDICATION_GROUP` column with 16 values (T2D, CKD, HF, CVD and their combinations), but **T1D is not a separate indication group**. For NBA 3.1, the indication distinction is critical.

**Approach**: derive indication group from `DIAGNOSIS_CODE` (ICD-10) in the raw claims table using the mapping in `Kerendia_Dx_Code_Analysis.xlsx`:

| ICD-10 code range | Indication group |
| --- | --- |
| E10.x | T1D |
| E11.x | T2D |
| N18.x, N28.x | CKD |
| I50.x | HF |
| I10-I15.x | Hypertension |
| E10.x + N18.x | T1D + CKD |
| E11.x + N18.x | T2D + CKD |
| E10.x + I50.x | T1D + HF |
| E11.x + I50.x | T2D + HF |

This adds T1D as a new indication group value and enables the model to distinguish T1D-prescribers from T2D-prescribers. The V6 `INDICATION_GROUP` already covers T2D, CKD, HF, CVD combinations but not T1D.

**Note**: this requires the raw claims table (`STG_CAR_IQV_LAAD_FCT_RX`) which has `DIAGNOSIS_CODE` and `ICD_VERSION_TYPE`. The V6 table's `INDICATION_GROUP` is pre-computed and cannot be modified.

### 4.4 HYPERTENSION_FLAG from diagnosis codes (#5)

The V6 table has `HYPERTENSION_FLAG` (HTN or null), but in the raw claims table this must be derived from ICD-10 codes I10-I15. This is straightforward: set `HYPERTENSION_FLAG = 'HTN'` when `DIAGNOSIS_CODE LIKE 'I1%'`.

---

## 5. Competitor Drug NBRx Share: updated competitor groups (#8-#12)

### 5.1 Current state

The NBA 3.0 notebook (31) computes NBRx share among 4 SGLT2i competitors: Farxiga, Invokana, Jardiance, Steglatro. It uses NPI as the key, only a 12-month lag window, and does not filter to the HCP universe.

### 5.2 Updated SGLT2i competitor set (#8)

Add **Inpefa** (sotagliflozin) to the SGLT2i competitor set. Inpefa is a dual SGLT1/SGLT2 inhibitor approved for HF (2023). It is in the v4 KEEP list and the final product mapping. It is a direct competitor to Kerendia in the HF space.

| Competitor | Product group | Indication | Status |
| --- | --- | --- | --- |
| Farxiga | FARXIGA BRAND + FARXIGA GENERICS | T2D + CKD + HF | Keep (consolidate brand + generic) |
| Invokana | INVOKANA | T2D + CKD | Keep |
| Jardiance | JARDIANCE | T2D + CKD + HF | Keep |
| Steglatro | STEGLATRO | T2D + CKD | Keep |
| **Inpefa** | **INPEFA** | **HF** | **Add** |

Brenzavvy (bexagliflozin) is dropped per v4 mapping (withdrawn from US market).

The SGLT2i share formula becomes: `PERC_{DRUG}_NBRX_SHARE = {drug}_12m_nbrx / total_5_competitor_12m_nbrx`.

### 5.3 New MRA competitor share (#9)

Kerendia (finerenone) is an MRA. The other MRAs in the market are spironolactone and eplerenone. An MRA share feature captures Kerendia's position in the MRA market, which is distinct from the SGLT2i market.

| MRA competitor | Product group | Notes |
| --- | --- | --- |
| Kerendia | KERENDIA | Target product |
| Spironolactone | MINERALOCORTICOID RECEPTOR ANTAGONISTS (spironolactone brands + generic) | v4 reclassifies spironolactone combos into MRA group |
| Eplerenone | MINERALOCORTICOID RECEPTOR ANTAGONISTS (Inspra, Eplerenone) | Same product group as spironolactone in v4 |

**Feature**: `PERC_KERENDIA_MRA_SHARE = Kerendia_12m_nbrx / total_MRA_12m_nbrx`.

**Note**: the v4 mapping puts all MRAs in one product group (`MINERALOCORTICOID RECEPTOR ANTAGONISTS`). To separate Kerendia from spironolactone/eplerenone in the share, filter on `PRODUCT_GROUP = 'KERENDIA'` vs `PRODUCT_GROUP = 'MINERALOCORTICOID RECEPTOR ANTAGONISTS'` at the NDC level. This requires the raw claims table with the v4 NDC-to-product-group mapping.

### 5.4 New HF drug share (#10)

For the HF indication, Kerendia competes with:

| HF competitor | Product group | Drug class |
| --- | --- | --- |
| Entresto | ENTRESTO | ARNI (sacubitril/valsartan) |
| Verquvo | VERQUVO | sGC stimulator (vericiguat) |
| Kerendia | KERENDIA | MRA (finerenone) |
| Inpefa | INPEFA | SGLT2i (sotagliflozin) |
| Farxiga | FARXIGA BRAND + FARXIGA GENERICS | SGLT2i (dapagliflozin) |
| Jardiance | JARDIANCE | SGLT2i (empagliflozin) |

**Feature**: `PERC_KERENDIA_HF_DRUG_SHARE = Kerendia_12m_nbrx / total_HF_drug_12m_nbrx`.

This share captures Kerendia's position among the drugs used specifically for HF management. A high share means the HCP prefers Kerendia over ARNI or SGLT2i for HF patients.

### 5.5 Key column alignment (#11)

Switch the competitor notebook from `NPI_NUMBER` to `PROVIDER_ID`. This aligns with notebooks 26/27/28 and avoids the NPI-to-PROVIDER_ID mapping in the combine step. The raw claims table and V6 table both have `PROVIDER_ID`.

### 5.6 Additional lag windows (#12)

Add 1, 3, and 6-month windows to the competitor share notebook. Currently only 12-month is used. Shorter windows capture recent shifts in market share (e.g., a new product launch or formulary change).

| Window | Current | Proposed |
| --- | --- | --- |
| 1-month | No | Yes |
| 3-month | No | Yes |
| 6-month | No | Yes |
| 12-month | Yes | Yes |

This produces 4 share features × 4 windows × 3 share groups (SGLT2i, MRA, HF) = **48 competitor share features** (up from 4).

---

## 6. NBA 3.1 Cohorts: using the claims-type cohorts

NBA 3.1 uses a cohort-based pipeline. The cohorts are generated by the `00_cohort_generation` helper notebook in `00_Helper_Notebooks/`, which reads its parameters from the `00_cohort_config` notebook. The cohort schedule follows `NBA_3.1_Model_Architecture_and_Cohorts.xlsx`.

### 6.1 Cohort structure

| Parameter | Value |
| --- | --- |
| Cohort 1 prediction month | 2024-07-01 |
| Total cohorts | 28 (c1-c28) |
| Training | c1-c24 |
| Testing | c25-c26 |
| Holdout (backtesting) | c27-c28 |
| Lookback window | 12 months |
| Data lag | 1 month (4-week lag for claims) |

### 6.2 Feature families and offsets

| Family | Features | Offset | Status |
| --- | --- | --- | --- |
| `claims` | Rx, Dx, Px, Lab | 0 days (month boundaries) | Active |
| `promotional` | Calls, iRep, DTC, Digital, Samples, Speaker, FTP, HQ Emails, ClickStream | 17 days | Active |
| `mmit` | MMIT | TBD | Pending |
| `laad_lrx` | LAAD-based LRx | TBD | Pending |

The NBRx/NRx/TRx and competitor share features use the **claims** feature family (offset 0, month boundaries).

### 6.3 Claims cohort fields

Each cohort row has:

| Field | Description |
| --- | --- |
| `cohort_id` | `c1` through `c28` |
| `prediction_month` | 1st of the month, c1 = 2024-07-01, incremented monthly |
| `dataset` | Training, Testing, or Holdout (Backtesting) |
| `offset_days` | 0 for claims |
| `lookback_start_date` | 12 months before `lookback_end_date` |
| `lookback_end_date` | `prediction_month` minus (`DATA_LAG_MONTHS` + 1) months, day 1 |

**Example**: for cohort c1, `prediction_month` = 2024-07-01, `lookback_end_date` = 2024-05-01 (July minus 2 months), `lookback_start_date` = 2023-06-01.

### 6.4 How the notebooks use the cohorts

The saved claims cohorts are at:

`/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet`

The 4 notebooks must:
1. Read the claims cohorts parquet (28 rows, one per cohort).
2. Cross-join the HCP universe (294,727 HCPs) with the 28 cohorts to produce 294,727 x 28 = ~8.25M rows.
3. For each cohort, filter the claims data to `lookback_start_date` <= `SVC_DT` <= `lookback_end_date`.
4. Build lag features (1/3/6/12-month) within each cohort's lookback window, using `lookback_end_date` as the reference point.
5. Save per-cohort output keyed on `HCP_COHORT_ID` (the combination of `PROVIDER_ID` and `cohort_id`).

This replaces the NBA 3.0 approach where each notebook used a single `COHORT_MONTH` parameter and a hardcoded scoring month. The cohort-based approach ensures that the same notebook logic produces features for all 28 cohorts in one pass.

### 6.5 Cohort generation helper notebooks

| Notebook | Path | Purpose |
| --- | --- | --- |
| `00_cohort_config` | `00_Helper_Notebooks/00_cohort_config` | Global parameters, cohort assignment functions, validation/production filters, HCP feature helpers |
| `00_cohort_generation` | `00_Helper_Notebooks/00_cohort_generation` | Builds and saves the 28 cohorts for each feature family. Provides the `CohortGenerator` API |

Feature notebooks use `%run "../00_Helper_Notebooks/00_cohort_config"` to load the cohort config, then read the saved `cohorts.parquet` directly or via `CohortGenerator('claims')`.

---

## 7. Where each change is implemented

| Change | Notebook | What to change |
| --- | --- | --- |
| Drop product groups (#1) | `05_NBRx_NRx_TRx/26_Features_NBRx`, `27_Features_NRx`, `28_Features_TRx` | Filter V6 query `WHERE PRODUCT_GROUP NOT IN (...)` for DROP groups, or apply v4 mapping with DROP exclusion if using raw claims |
| Diuretics split (#2) | Same 3 notebooks | Apply v4 reclassification: DIURETICS AND COMBOS → LOOP / THIAZIDE / K-SPARING. Use v4 NDC-to-group mapping or CASE WHEN on existing product names |
| HF drug groups (#3) | Same 3 notebooks | Add HF RATE CONTROL, HF VASODILATORS as new pivot values. Reclassify from OTHERS using v4 mapping |
| T1D product groups (#4) | Same 3 notebooks | Add T1D DISEASE-MODIFYING, GLUCAGON RESCUE, insulin families, CGM systems, insulin pumps as new pivot values. Reclassify from OTHERS using v4 mapping |
| INDICATION_GROUP (#5) | Same 3 notebooks (if using raw claims) | Derive from DIAGNOSIS_CODE using `DM_TYPE` and `HF_TYPE` from `Kerendia_Dx_Final_Product_Mapping.csv`. Add T1D as a new indication group value. Not needed if using V6 (V6 indication groups are pre-computed) |
| Running total pruning (#6) | Same 3 notebooks | After `step3_lag`, drop `RUNNING_TOTAL_...` columns for P5-P6 product groups. Keep for P1-P4 |
| Lag window reduction (#7) | Same 3 notebooks | For P5-P6 product groups, keep only `_IN_LAST_1_MONTH` and `_IN_LAST_12_MONTH`. Drop 3 and 6-month for these groups |
| SGLT2i competitor update (#8) | `31_Competitor_drugs_NBRX_share` (or NBA 3.1 equivalent) | Add Inpefa to the competitor set. Update share formula to divide by 5-competitor total. Consolidate Farxiga brand + generic |
| MRA share (#9) | Same competitor notebook | Add MRA share computation: Kerendia NBRx / (Kerendia + Spironolactone + Eplerenone) NBRx. Requires NDC-level filtering within MRA product group |
| HF drug share (#10) | Same competitor notebook | Add HF drug share: Kerendia NBRx / (Kerendia + Entresto + Verquvo + Inpefa + Farxiga + Jardiance) NBRx |
| Key column (#11) | Same competitor notebook | Change from NPI_NUMBER to PROVIDER_ID. Join to V6 or raw claims on PROVIDER_ID |
| Lag windows (#12) | Same competitor notebook | Change `last_i_month_list = [12]` to `last_i_month_list = [1, 3, 6, 12]` |
| HCP universe (#13) | All 4 notebooks | Change universe path to `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/` (294,727 HCPs). Inner-join on PROVIDER_ID |
| Cohorts (#15) | All 4 notebooks | Read claims cohorts from `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` (28 cohorts, c1-c28). Use `CohortGenerator('claims')` from `00_cohort_generation` or read the parquet directly. Cross-join HCP universe with cohorts, left-join features, fill 0. Key on `PROVIDER_ID`, `cohort_id`, `HCP_COHORT_ID` |
| Final product mapping (#16) | All 4 notebooks | Use the merged mapping CSVs from `kerendia_nba_3_1_volume/final_product_mapping/` as the primary product/code mapping. Apply v4 NDC-to-product-group mapping with DROP exclusion |

---

## 8. Estimated feature count impact

| Change | Columns added | Columns removed | Net |
| --- | --- | --- | --- |
| Drop product groups (#1) | 0 | ~105 (7 groups × 5 × 3 notebooks) | -105 |
| Diuretics split (#2) | ~30 (3 groups × ~3 × 3) | ~15 (1 group × 5 × 3) | +15 |
| HF drug groups (#3) | ~45 (3 groups × 5 × 3) | 0 | +45 |
| T1D product groups (#4) | ~99 (11 groups × 3 × 3) | 0 | +99 |
| Running total pruning (#6) | 0 | ~240 (P5-P6 running totals × 3) | -240 |
| Lag window reduction (#7) | 0 | ~360 (P5-P6 3/6-month × 3) | -360 |
| Competitor share updates (#8-#12) | +44 (new share features) | -4 (old 4 features) | +40 |
| **Total per notebook** | | | **~-70 avg** |

The net effect is a reduction in total columns (from ~1,337 to ~1,100 per notebook) while adding higher-signal features for T1D and HF. The pruning focuses on low-value sparse product groups and redundant lag/running columns. The additions focus on disease-specific prescribing signals.

---

## 9. Spark Connect compatibility: code patterns and fixes (learned during job runs)

The NBA 3.1 notebooks run on serverless compute with Spark Connect, which differs from classic Spark in several ways. The following errors were encountered and fixed during the job pipeline test and full universe runs. **When generating or regenerating notebooks from these change recommendations, apply all of these patterns to avoid repeating the same failures.**

### 9.1 One %run per cell

**Error:** `Failed to parse %run command: string matching regex '$[\w_]+' expected but '%' found`

**Cause:** Databricks `%run` cell magic only supports ONE notebook per cell. Multiple `%run` commands in the same cell cause a parse error.

**Fix:** Put each `%run` in its own cell, as the very first line of that cell (no comments before it). Example:

```
Cell 1: %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
Cell 2: %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
Cell 3: %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function"
Cell 4: # Configuration cell (imports, constants, widgets)
```

### 9.2 StorageLevel import path

**Error:** `ImportError: cannot import name 'StorageLevel' from 'pyspark.sql'`

**Cause:** In Spark Connect, `StorageLevel` is not available in `pyspark.sql`.

**Fix:** Import from `pyspark.storagelevel`:
```python
from pyspark.storagelevel import StorageLevel
```

### 9.3 HCP universe is parquet, not Delta

**Error:** `DELTA_MISSING_TRANSACTION_LOG: Incompatible format detected`

**Cause:** The HCP universe at `HCP_Universe_without_call_hcps/` is stored as parquet files, not as a Delta table.

**Fix:** Use `spark.read.parquet(HCP_UNIVERSE_PATH)`, not `spark.read.format("delta").load(HCP_UNIVERSE_PATH)`.

### 9.4 PERIOD_ID is a DATE column

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
- `WHERE PERIOD_ID >= '20200101'` in the SQL query (causes a cast error because PERIOD_ID is a DATE and '20200101' is not a valid date string)

### 9.5 Python sum() intercepted by Spark Connect

**Error:** `PySparkTypeError: Argument 'col' should be Column or str, got generator`

**Cause:** In Spark Connect, the built-in `sum()` function is intercepted as `F.sum()` (Spark SQL aggregate function), which expects a single Column or str, not a generator of columns. The NBA 3.0 competitor notebook used `sum(when(col(c).isNotNull(), col(c)).otherwise(0) for c in col_list)` for row-wise column addition.

**Fix:** Use `reduce()` with `+` and `F.coalesce()`:
```python
from functools import reduce
df = df.withColumn('TOTAL', reduce(lambda a, b: a + b, [F.coalesce(col(c), F.lit(0)) for c in col_list]))
```

### 9.6 Do not unpersist cached DataFrames before all downstream uses

**Error:** `CACHE_DATAFRAME_ACCESS_AFTER_UNCACHE: This DataFrame, or a DataFrame it was derived from, has been uncached and can no longer be accessed`

**Cause:** The NBA 3.1 code called `hcp_lrx_claims.unpersist()` after building `df_spine` from pivot DataFrames derived from `hcp_lrx_claims`. When `step2_fill_missing(df_spine, ...)` later tried to materialize `df_spine`, it needed to recompute from `hcp_lrx_claims` lineage, which was already uncached.

**Fix:** Do NOT call `unpersist()` on a cached DataFrame until ALL downstream DataFrames derived from it have been fully materialized (written to disk). Simply remove the `unpersist()` call -- the cache is cleaned up when the notebook ends.

### 9.7 Clean column names after pivot (Delta compatibility)

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

### 9.8 Helper notebook paths and 00_cohort_config

The NBA 3.0 helper notebooks are used as-is from the 3.0 dev folder (they are NOT in the 3.1 dev folder):

| Helper | Path |
| --- | --- |
| 00_connection | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection` |
| 00_config | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config` |
| 00_step23_function | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function` |

The `00_cohort_config` notebook is NOT needed for the feature notebooks -- cohorts are loaded directly from `cohorts.parquet` at `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet`. Do NOT add `%run` for `00_cohort_config`.

### 9.9 Summary table: errors and fixes

| # | Error | Root cause | Fix |
| --- | --- | --- | --- |
| 1 | `Failed to parse %run command` | Multiple %run in one cell | One %run per cell, first line of cell |
| 2 | `ImportError: StorageLevel from pyspark.sql` | Wrong import path | `from pyspark.storagelevel import StorageLevel` |
| 3 | `DELTA_MISSING_TRANSACTION_LOG` | HCP universe is parquet, not Delta | `spark.read.parquet()` |
| 4 | `CAST_INVALID_INPUT: '20200101' cannot be cast to DATE` | PERIOD_ID is DATE type; substring on literal string; SQL date filter | `F.trunc(col("PERIOD_ID"), 'month')`; remove SQL date filter |
| 5 | `PySparkTypeError: sum() got generator` | Spark Connect intercepts sum() as F.sum() | `reduce(lambda a, b: a + b, [F.coalesce(col(c), F.lit(0)) for c in col_list])` |
| 6 | `CACHE_DATAFRAME_ACCESS_AFTER_UNCACHE` | unpersist() called before downstream use | Remove unpersist() call |
| 7 | `DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES` | Spaces in pivot column names | Apply clean_col_name() after pivot; clean group names for matching |
| 8 | `File not found: 00_cohort_config` | Not needed; cohorts loaded from parquet | Remove %run 00_cohort_config; read cohorts.parquet directly |
