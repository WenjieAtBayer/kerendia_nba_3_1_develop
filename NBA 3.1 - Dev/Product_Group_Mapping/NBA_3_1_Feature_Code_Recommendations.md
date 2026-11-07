# Kerendia NBA 3.1 — Product, Dx, Px and Lab Code Recommendations

> **Data source update (Nov 2026):** NBA 3.1 LRx features now read `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` instead of `KERENDIA_LAAD_BASED_LRX_V6`. The product basket NBA 3.1 uses is the **V7 mapping** (67 product groups in 22 classes), documented in Sections 1.2 and 1.3. The v4 proposal (`Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`) was not adopted; it is kept in Sections 1.4 and 1.5 for reference.

**Date:** 2026-10-22 (Section 1 updated 2026-11-07 to the V7 product mapping)
**Context:** T1D + HF indication expansion for Kerendia NBA 3.1

**Analysis window:** last 24 months. **Indication context:** point-in-time patient flags from `pace_ker_in_house_schema.indication_table` (T1D / T2D / HF / CKD).

**Tier definitions (used in all four workbooks):**

| Tier | Meaning |
| --- | --- |
| TIER_1_DROP | Safe to remove — trivial volume and/or no indication signal |
| TIER_2_DROP | Conditional — high-volume but non-discriminative, or low-volume variants |
| TIER_3_REVIEW | Manual decision — moderate volume, inconclusive signal |
| KEEP | Indication-defining or high-volume with strong signal |

---

## Summary

| Domain | NBA 3.0 | Remove (T1 / T2 / T3) | Keep | Main additions for 3.1 |
| --- | --- | --- | --- | --- |
| Product basket | 71 product groups (V6), 458 drugs with NBRx | None at group level in V7 (drug tiers 74 / 33 / 22 apply only to drug-level features) | 67 V7 product groups, 22 classes | Entresto generic, Baxfendy, Exenatide, Liraglutide generic added; most of OTHERS split into NBA groups (METFORMIN, SULFONYLUREAS, DPP4, insulin, CGM, CCB, CKD SUPPORTIVE, VERQUVO, INPEFA). v4's 13 new groups not adopted |
| Dx | 414 ICD codes | 92 / 16 / 13 codes | 293 codes | Roll up retinopathy to parent, ICD-9 to ICD-10 mapping, hyperkalemia |
| Px | 153 CPT/HCPCS codes | 6 / 10 / 10 codes | 127 codes | Dialysis/transplant, cardiac device, CGM/pump, retinal exam codes |
| Lab | 2 test types (GFR, UACR), PCP-only | 17 / 2 / 6 LOINCs | 20 LOINCs | Potassium, HbA1c, all specialties, value-based features |

---

## 1. Product Basket

### 1.1 What NBA 3.0 used

* **Source:** LAAD V6 pipeline (`kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6`), mapped with `Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v3.xlsx` (483 rows, 73 groups in the mapping; 71 present in V6 data).
* **Drugs with NBRx in the 24-month window:** 458 (102.4M NBRx claims, 1.35M providers) in `pt_lvl_nbrx`.
* **Volume concentration:** top 20 drugs = ~80% of patients; top 112 = ~99%; bottom 346 drugs = <1% (long tail).
* **Data-quality issue:** the `OTHERS` group in `pt_lvl_nbrx` contains 264 of 458 drugs (58%) — no therapeutic coherence, and several gold-standard HF/CKD/T1D markers are buried inside it.

**NBA 3.0 product groups (71, V6):**
ACARBOSE; ACE INHIBITORS AND COMBOS; ACTOS; ADLYXIN; ALISKIREN HEMIFUM; ALOGLIPTIN_NESINA COMBOS; ANGIOTENSIN II RECEPTOR ANTAGONISTS AND COMBOS; BASAL (LONG-ACTING) INSULIN; BETA BLOCKERS AND COMBOS; BEXAGLIFLOZIN; BRENZAVVY; BYDUREON; BYETTA; CALCIUM CHANNEL BLOCKERS AND COMBOS; CANAGLIFLOZIN_INVOKANA COMBOS; CGM AND SUPPLIES; CYCLOSET; DAPAGLIFLOZIN_FARXIGA COMBOS; DIURETICS AND COMBOS; EMPAGLIFLOZIN_JARDIANCE COMBOS; ENTRESTO; ERTUGLIFLOZIN_STEGLATRO COMBOS; ERYTHROPOIESIS STIMULATING AGENTS; FARXIGA BRAND; FARXIGA GENERICS; GLIMEPIRIDE; GLIPIZIDE; GLIPIZIDE COMBOS; GLYBURIDE; GLYBURIDE COMBOS; INPEFA; INSULIN GLAR M SOL; INVOKANA; IRON DEFICIENCY DRUG; JANUVIA; JARDIANCE; KERENDIA; METFORMIN; MIGLITOL; MINERALOCORTICOID RECEPTOR ANTAGONISTS; MOUNJARO; NESINA; ONGLYZA; OTHERS; OZEMPIC; PHOSPHATE BINDERS; PIOGLITAZONE_ACTOS COMBOS; PRANDIN; PRE-MIXED INSULIN; RAPID-ACTING INSULIN; REZVOGLAR KWIKPEN; RYBELSUS; SAXAGLIPTIN HYDROCHLORIDE; SAXAGLIPTIN_ONGLYZA COMBOS; SAXENDA; SHORT-ACTING HUMAN INSULIN; SOLIQUA; STEGLATRO; SULFONYLUREAS; SYMLINPEN; TEKTURNA; TRADJENTA; TRULICITY; VERQUVO; VICTOZA; VITAMIN D ANALOG DRUG; WEGOVY; XULTOPHY; ZEPBOUND; ZITUVIMET; ZITUVIO

### 1.2 Product groups NBA 3.1 uses (V7 mapping)

**Source:** `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (`PRODUCT_GROUP`, `PRODUCT_CLASS`), built by `kerendia_data_needs/LAAD based LRx Pipeline/Ops Pipeline V7`. Drug-level mapping: `Kerendia_Market_Basket_Product_Group_Mapping_V7.csv` in this folder (543 rows, one per LAAD product name × V6 group; columns: V6 group, V7 class / group, NBRx group, mapping source, added-in-V7 flag, NDC count, TRx Oct 2024 – Sep 2026). It is a Nov 2026 snapshot of the V7 claims staging table and matches V7 TRx totals; regenerate it (same logic as `07_V6_vs_V7_Product_Crosswalk`) if the basket or `NBA_OTHERS_SPLIT` changes.

**How the mapping is built (per NDC):**
1. **Basket** = V6 market basket (`Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v3.xlsx`) + `V7_EXTRA_BASKET` in `00_V7_Params`: Entresto generic (SACUBITRIL/VALSART), BAXFENDY, EXENATIDE, LIRAGLUTIDE 5-PAK and a few minor ARB / beta-blocker / diuretic brands. No drugs are removed.
2. **lrx_nbrx product map first:** if the NDC has a level-4 product in `VIEW_PHA_LRX_TRANSITION_PRODUCT_MAPPING_FINAL_OCT_09`, V7 uses that name and class (same as `pace_ker_in_house_schema.lrx_nbrx`). Farxiga and Entresto are split into brand / generic groups but each counts NBRx as one product.
3. **NBA split for the rest:** NDCs the lrx_nbrx map leaves unmapped get an NBA group from their V6 group (`NBA_OTHERS_SPLIT` in `00_V7_Params`). Anything not listed stays `OTHERS`.
4. NBRx / NRx are counted on these groups (new to the group in 365 days).

**V7 product groups and where the NBA 3.0 (V6) groups went** (TRx claims, Oct 2024 – Sep 2026):

| V7 class | V7 `PRODUCT_GROUP` | NBA 3.0 (V6) groups mapped here | TRx (24 mo) |
| --- | --- | --- | --- |
| KERENDIA | KERENDIA | KERENDIA | 1.8M |
| SGLT2 | JARDIANCE, FARXIGA BRAND, FARXIGA GENERIC, SYNJARDY, SYNJARDY XR, TRIJARDY XR, GLYXAMBI, XIGDUO XR, DAPAGLIFLOZIN/METFORMIN H, QTERN, INVOKANA, INVOKAMET, INVOKAMET XR, STEGLATRO, STEGLUJAN, SEGLUROMET, BRENZAVVY, BEXAGLIFLOZIN | JARDIANCE, FARXIGA BRAND, FARXIGA GENERICS, INVOKANA, STEGLATRO, BRENZAVVY, BEXAGLIFLOZIN, the four SGLT2 `_COMBOS` groups; GLYXAMBI and SEGLUROMET came out of V6 OTHERS | 78.4M |
| GLP1 | MOUNJARO, OZEMPIC, ZEPBOUND, TRULICITY, WEGOVY, WEGOVY HD, RYBELSUS, VICTOZA, LIRAGLUTIDE, BYDUREON BCISE, BYDUREON PEN, BYETTA, EXENATIDE, SAXENDA, SOLIQUA 100/33, XULTOPHY 100/3.6, SYMLINPEN 60, SYMLINPEN 120 (ADLYXIN, BYDUREON only in older history) | MOUNJARO, OZEMPIC, ZEPBOUND, TRULICITY, WEGOVY, RYBELSUS, VICTOZA, BYDUREON, BYETTA, SAXENDA, SOLIQUA, XULTOPHY, SYMLINPEN, ADLYXIN | 183.0M |
| ACE | ACE | ACE INHIBITORS AND COMBOS | 193.8M |
| ARB | ARB | ANGIOTENSIN II RECEPTOR ANTAGONISTS AND COMBOS | 250.2M |
| BB | BB | BETA BLOCKERS AND COMBOS | 271.0M |
| DIURETICS | DIURETICS | DIURETICS AND COMBOS (loop, thiazide and K-sparing stay together) | 167.1M |
| sMRA | SPIRONOLACTONE, EPLERENONE, ALDACTONE, INSPRA, ALDACTAZIDE, CAROSPIR | MINERALOCORTICOID RECEPTOR ANTAGONISTS, plus spironolactone NDCs from DIURETICS AND COMBOS and CAROSPIR from OTHERS | 51.5M |
| DRI | ALISKIREN, TEKTURNA, TEKTURNA HCT | ALISKIREN HEMIFUM, TEKTURNA | 0.1M |
| ENTRESTO BRAND / ENTRESTO GENERICS | ENTRESTO BRAND, ENTRESTO GENERIC | ENTRESTO (generic sacubitril/valsartan added in V7) | 7.1M / 6.6M |
| BAXFENDY | BAXFENDY | new in V7 | <0.1M |
| METFORMIN | METFORMIN | METFORMIN | 145.2M |
| SULFONYLUREAS | SULFONYLUREAS | GLIMEPIRIDE, GLIPIZIDE, GLIPIZIDE COMBOS, GLYBURIDE, GLYBURIDE COMBOS, SULFONYLUREAS | 41.4M |
| DPP4 | DPP4 | JANUVIA, TRADJENTA, ZITUVIO, ZITUVIMET, NESINA, ALOGLIPTIN_NESINA COMBOS, ONGLYZA, SAXAGLIPTIN HYDROCHLORIDE, SAXAGLIPTIN_ONGLYZA COMBOS | 14.3M |
| INSULIN | BASAL INSULIN | BASAL (LONG-ACTING) INSULIN, REZVOGLAR KWIKPEN, INSULIN GLAR M SOL | 47.2M |
| INSULIN | OTHER INSULIN | RAPID-ACTING INSULIN (incl. AFREZZA, LYUMJEV, FIASP), PRE-MIXED INSULIN, SHORT-ACTING HUMAN INSULIN | 31.5M |
| CGM | CGM | CGM AND SUPPLIES (incl. Omnipod and iLet pumps) | 52.2M |
| CCB | CCB | CALCIUM CHANNEL BLOCKERS AND COMBOS | 216.6M |
| CKD SUPPORTIVE | CKD SUPPORTIVE | VITAMIN D ANALOG DRUG, PHOSPHATE BINDERS, ERYTHROPOIESIS STIMULATING AGENTS, IRON DEFICIENCY DRUG | 6.8M |
| VERQUVO | VERQUVO | VERQUVO | 0.2M |
| INPEFA | INPEFA | INPEFA (own class, kept out of SGLT2 so the HCP Universe SGLT2/GLP1 pool still matches lrx_nbrx) | <0.1M |
| OTHERS | OTHERS | ACARBOSE, ACTOS, CYCLOSET, MIGLITOL, PIOGLITAZONE_ACTOS COMBOS, PRANDIN, and the rest of V6 OTHERS | 21.3M |

**What is still in V7 `OTHERS` (47 drugs, 21.3M TRx):** pioglitazone and its combos (11.5M), JANUMET / JANUMET XR (3.1M), cinacalcet / SENSIPAR / PARSABIV (1.3M), repaglinide / nateglinide (1.3M), ivabradine / CORLANOR (0.65M), acarbose (0.6M), NOVOLOG MIX 70/30 (0.63M), glucagon (BAQSIMI, GVOKE, ZEGALOGUE, 1.4M), JENTADUETO / XR (0.5M), XPHOZAH (0.15M), isosorbide dinitrate/hydralazine / BIDIL (0.09M), V-GO 20/30/40 (0.05M), sodium ferric gluconate, CARNITOR / levocarnitine, TZIELD, KORSUVA, CYCLOSET, MIGLITOL and other small brands.

**Not in the V7 basket at all:** digoxin (DIGOXIN, DIGITEK, LANOXIN) and omecamtiv mecarbil. To use them, add the LAAD product names to `V7_EXTRA_BASKET` and rerun `06_V7_History_Backfill`.

### 1.3 v4 proposal vs. V7 (status)

| v4 proposal | Status in V7 |
| --- | --- |
| Dissolve 11 groups | **Not applied** — no drugs are dropped. ACTOS, CYCLOSET, MIGLITOL, PIOGLITAZONE_ACTOS COMBOS → OTHERS; CALCIUM CHANNEL BLOCKERS → CCB; SULFONYLUREAS → SULFONYLUREAS; TEKTURNA → DRI; BEXAGLIFLOZIN → SGLT2; ADLYXIN → GLP1; INSULIN GLAR M SOL → BASAL INSULIN; OTHERS is mostly split up but still exists (21.3M TRx) |
| Split DIURETICS AND COMBOS into LOOP / THIAZIDE / K-SPARING | **Not applied** — one `DIURETICS` group (lrx_nbrx class); only spironolactone moves to sMRA |
| 13 new groups (T1D DISEASE-MODIFYING, GLUCAGON RESCUE, INSULIN DELIVERY DEVICES, HF VASODILATORS, HF RATE CONTROL, CARDIAC GLYCOSIDES, CARDIAC MYOSIN ACTIVATORS, CALCIMIMETICS, CKD SYMPTOM MGMT, CKD SUPPORTIVE, LOOP / THIAZIDE / K-SPARING DIURETICS) | **Not applied.** TZIELD, glucagon, V-GO, BIDIL / isosorbide-hydralazine, CORLANOR / ivabradine, cinacalcet / SENSIPAR / PARSABIV, KORSUVA and CARNITOR / levocarnitine are in OTHERS; the diuretics are in DIURETICS; digoxin and omecamtiv are not in the basket. V7 `CKD SUPPORTIVE` exists but means vitamin D analogs + phosphate binders + ESAs + iron, not carnitine |
| Move HF high-signal drugs out of OTHERS | VERQUVO and INPEFA have their own groups. CORLANOR and isosorbide-hydralazine stay in OTHERS |
| Move CKD high-signal drugs | Phosphate binders (incl. VELPHORO), ESAs and vitamin D analogs (incl. RAYALDEE) → CKD SUPPORTIVE. XPHOZAH stays in OTHERS |
| Move T1D high-signal drugs | LYUMJEV, FIASP, NOVOLOG etc. → OTHER INSULIN; Omnipod 5 and iLet → CGM |
| Move T2D combos | GLYXAMBI, SEGLUROMET → SGLT2. JANUMET / JANUMET XR and JENTADUETO / XR stay in OTHERS (not DPP4) |
| Entresto brand + generic | Separate `PRODUCT_GROUP`s (ENTRESTO BRAND, ENTRESTO GENERIC) but NBRx is counted on one Entresto group |
| AFREZZA | In OTHER INSULIN |
| Final basket: 414 products in 74 groups | V7: all basket drugs in 67 groups / 22 classes (`Kerendia_Market_Basket_Product_Group_Mapping_V7.csv`) |

**Changing a group:** groups come from `V7_EXTRA_BASKET` / `NBA_OTHERS_SPLIT` in `Ops Pipeline V7/00_V7_Params`. `NBA_OTHERS_SPLIT` works on V6 group names, so moving single drugs out of V6 OTHERS (e.g. JANUMET → DPP4, CORLANOR → HF RATE CONTROL) needs a drug-level rule in `build_claims_v7`. Every change needs `06_V7_History_Backfill` so history uses the same groups.

### 1.4 v4 proposal (Oct 2026, not adopted) — what we could remove

> Kept for reference. V7 does not apply these removals (see 1.3). The drug-level tiers are still useful for drug-level features.

**Group-level removals (v4 mapping, user-approved):** 11 groups dissolved

| Group | Reason |
| --- | --- |
| ACTOS | Brand pioglitazone, 0.2% prevalence; generic captures the molecule |
| ADLYXIN | Lixisenatide discontinued in US (2023) |
| BEXAGLIFLOZIN | Withdrawn from US market |
| CALCIUM CHANNEL BLOCKERS AND COMBOS | Lowest-variance high-prevalence group; hypertension background, not indication-discriminative |
| CYCLOSET | Bromocriptine for T2D, no CKD/HF/CVD link |
| INSULIN GLAR M SOL | Likely duplicate of BASAL (LONG-ACTING) INSULIN |
| MIGLITOL | Alpha-glucosidase inhibitor, no CKD/HF/CVD link |
| OTHERS | Dumping ground — products redistributed into named groups (see 1.3) |
| PIOGLITAZONE_ACTOS COMBOS | Brand TZD combos, near-zero volume |
| SULFONYLUREAS | Obsolete first-gen sulfonylureas |
| TEKTURNA | Direct renin inhibitor, largely withdrawn |

`DIURETICS AND COMBOS` is also dissolved, but it is **split** (LOOP / THIAZIDE / K-SPARING + MRA), not removed.

**Drug-level removals (Product Basket workbook):**

**TIER_1_DROP — 74 drugs (safe to remove)**
* *<20 patients total (58):* NIFEDIAC CC, OMNIPOD 5 G7 INTRO KIT (G, ROCALTROL, ENBUMYST, ACTOS, FREESTYLE LIBRE/READER/FL, GLUCOTROL XL, GUARDIAN SENSOR 3, NIFEDICAL XL, ZEMPLAR, CARDIZEM, DYRENIUM, MIRCERA, GUARDIAN SENSOR (3), EDECRIN, LEVOCARNITINE, QUINAPRIL HCL, KOMBIGLYZE XR, PROPRANOLOL HCL ER, SIMPLERA SYNC SENSOR, SENSIPAR, PRESTALIA, ALDACTAZIDE, METFORMIN HCL ER, LOTENSIN HCT, GUARDIAN LINK 3 TRANSMITT, ACCURETIC, FUROSCIX READYFLOW, TEKTURNA HCT, VASERETIC, TENORETIC 50, BYDUREON PEN, GLUCOTROL, ZIAC, PRINIVIL, RENAGEL, SACUBITRIL/VALSART, TAZTIA XT, LABETALOL HCL, SULAR, BRYNOVIN, LASIX ONYU, GLIPIZIDE/METFORMIN HCL, PARSABIV, ACTOPLUS MET, CHLOROTHIAZIDE, CALAN SR, OMNIPOD DASH INTRO KIT (G, BUMEX, DUETACT, TENORETIC 100, ZEBETA, DEMADEX, KAZANO, PHOSLO, OMNIPOD CLASSIC PODS (GEN, GLUCOPHAGE, HUMALOG MIX 50/50
* *Zero indication signal + <50 patients (16):* ACEBUTOLOL HCL, LEVAMLODIPINE, MYXREDLIN, MAXZIDE-25, FREESTYLE LIBRE/SENSOR/FL, VERELAN PM, ACEON, AFEDITAB CR, INDERAL, PROPRANOLOL HCL LA, LANTUS FOR OPTICLIK, PROPRANOLOL/HYDROCHLOROTH, SIMPLERA SYSTEM, CLEVIPREX, TEVETEN HCT, SDAMLO

**TIER_2_DROP — 33 drugs (conditional)**
* *ACE brands with weak HF/CKD signal (3):* BENAZEPRIL HCL/HYDROCHLOR, BENAZEPRIL HCL, ZESTORETIC
* *ARB brands with weak HF/CKD signal (8):* DIOVAN HCT, MICARDIS HCT, AVAPRO, MICARDIS, EXFORGE, HYZAAR, AVALIDE, AMLODIPINE/VALSARTAN/HCTZ
* *Hypertension workhorses (2):* HYDROCHLOROTHIAZIDE, INDAPAMIDE
* *Low-volume insulin variants (6):* BASAGLAR TEMPO PEN, INSULIN ASPART PENFILL, FIASP PENFILL, HUMALOG TEMPO PEN, LYUMJEV TEMPO PEN, LEVEMIR FLEXTOUCH
* *Low-volume device variants (12):* TANDEM MOBI AUTOSOFT XC 1, EVERSENSE 365 SENSOR/HOLD, ILET INSULIN PUMP, TANDEM T:SLIM ASFT 30 PK1, EVERSENSE 365 SMART TRANS, MINIMED INSTINCT GLUCOSE, V-GO 20, GUARDIAN 4 TRANSMITTER KI, V-GO 40, V-GO 30, FREESTYLE LIBRE 2, OMNIPOD 5 G7 PODS (GEN 5)
* *Pack/kit variants (2):* ILET STARTER KIT - CONTAC, GLUCAGON EMERGENCY KIT

**TIER_3_REVIEW — 22 drugs (manual decision, low volume):** TIMOLOL MALEATE, FERRLECIT, NICARDIPINE HYDROCHLORIDE, ARBLI, LOPRESSOR, NICARDIPINE HCL, INNOPRAN XL, ESMOLOL HCL, CAPTOPRIL/HYDROCHLOROTHIA, ATACAND, INDERAL LA, INDERAL XL, TENORMIN, CARDIZEM LA, EPANED, CARDIZEM CD, CARNITOR, TIAZAC, DILTIAZEM CD, CHLOROTHIAZIDE SODIUM, ENALAPRILAT, NYMALIZE

> **Caveat — drug drops vs. group mapping:** several Tier 1/3 drugs (SENSIPAR, PARSABIV, ZEMPLAR, BUMEX, DEMADEX, EDECRIN, KAZANO, KOMBIGLYZE XR, SACUBITRIL/VALSART, CARNITOR, V-GO 20/30/40) were proposed to be **reclassified into named v4 groups** (in V7 they sit in OTHERS, DIURETICS or ENTRESTO GENERIC — see 1.3). NBA features are built at product-group level, so keep them in the mapping (they add volume to the group) and only exclude them from any drug-level features. HYDROCHLOROTHIAZIDE (Tier 2) is the anchor of THIAZIDE DIURETICS — keep it in the mapping.

### 1.5 v4 proposal (Oct 2026, not adopted) — what we could add

> Kept for reference. None of the 13 groups below exist in V7; see 1.3 for where their products are.

**New product groups (13, v4):**

| New group | Priority | Products | Indication signal |
| --- | --- | --- | --- |
| T1D DISEASE-MODIFYING | P2 | TZIELD | T1D |
| GLUCAGON RESCUE | P4 | BAQSIMI, GVOKE, ZEGALOGUE | T1D (BAQSIMI 33–41% T1D) |
| INSULIN DELIVERY DEVICES | P6 | V-GO 20/30/40 | T1D/T2D insulin users |
| HF VASODILATORS | P3 | BIDIL, ISOSORBIDE DI/HYDRALAZIN | HF (100% HF) |
| HF RATE CONTROL | P3 | CORLANOR, IVABRADINE HCL | HF (100% HF) |
| CARDIAC GLYCOSIDES | P3 | DIGOXIN, DIGITEK, LANOXIN | HF — **absent from V6; needs pipeline re-run** |
| CARDIAC MYOSIN ACTIVATORS | P3 | OMECAMTIV MECARBIL | HF (promoted from MONITOR) |
| CALCIMIMETICS | P4 | SENSIPAR, PARSABIV, CINACALCET HCL | CKD (cinacalcet 55% CKD) |
| CKD SYMPTOM MGMT | P4 | KORSUVA | CKD |
| CKD SUPPORTIVE | P6 | L-CARNITINE, CARNITOR | CKD / dialysis |
| LOOP DIURETICS | P4 | Furosemide, bumetanide, torsemide + brands (11) | HF (bumetanide 52%, torsemide 51% HF) |
| THIAZIDE DIURETICS | P4 | HCTZ, chlorthalidone, metolazone + brands (13) | Hypertension / HF (metolazone 52% HF) |
| K-SPARING DIURETICS | P4 | Amiloride, triamterene + combos (8) | Background |

**High-signal drugs to pull out of OTHERS into existing groups (Product Basket `Indication_Specific` sheet):**
* *HF (100% HF prevalence):* CORLANOR, VERQUVO, ISOSORBIDE DINITRATE/HYDR. INPEFA (53% HF) is its own group.
* *CKD (100% CKD prevalence):* SEVELAMER CARBONATE/HCL, CALCIUM ACETATE, VELPHORO, LANTHANUM CARBONATE, XPHOZAH → PHOSPHATE BINDERS. PROCRIT, RETACRIT, EPOGEN, ARANESP → ESA (66–70% CKD). PARICALCITOL, CALCITRIOL, RAYALDEE → VITAMIN D ANALOG DRUG.
* *T1D (>40% T1D prevalence):* LYUMJEV, FIASP, HUMALOG JUNIOR, INSULIN LISPRO JUNIOR, NOVOLOG → RAPID-ACTING INSULIN. OMNIPOD 5 DEXCOM, ILET → CGM AND SUPPLIES.
* *T2D combos:* JANUMET / JANUMET XR → JANUVIA; JENTADUETO / XR → TRADJENTA; GLYXAMBI → EMPAGLIFLOZIN_JARDIANCE COMBOS; SEGLUROMET → ERTUGLIFLOZIN_STEGLATRO COMBOS.

**Other product actions:**
* ENTRESTO brand (494K patients) and generic sacubitril/valsartan (601K) — both 100% HF. Collapse to one ENTRESTO group, or keep brand/generic separate only if the generic transition itself is a feature.
* Verify AFREZZA (25% T1D) volume in Snowflake before deciding whether it gets its own feature.

**Final active basket (v4 proposal, not adopted):** 414 products in 74 product groups. See `Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`. NBA 3.1 uses the V7 mapping instead: 67 product groups in 22 classes (Section 1.2).

---

## 2. Diagnosis (Dx) Codes

### 2.1 What NBA 3.0 used

* **Source:** `dx_input_claims_all_events_features_input`, built from Snowflake `STG_CAR_IQV_LAAD_FACT_DX` + `STG_CAR_IQV_LAAD_DIM_DIAG` and filtered to `dx_event_list`.
* **414 diagnosis codes**, almost all ICD-10, plus 3 ICD-9 legacy codes.
* **275 indication-defining** (any ICD-based T1D/T2D/HF/CKD flag), 139 non-defining comorbidities.

| ICD chapter | Codes |
| --- | --- |
| Endocrine/Metabolic (E00–E89) | 249 |
| Circulatory (I00–I99) | 101 |
| Musculoskeletal (M00–M99, gout) | 22 |
| Factors/Status (Z00–Z99) | 12 |
| Genitourinary (N00–N99) | 10 |
| Blood/Immune (D50–D89, anemia) | 8 |
| Pregnancy (O00–O9A) | 5 |
| Injury/Toxic (S00–T88) | 3 |
| ICD-9 legacy | 3 |
| Symptoms/Signs (R00–R99) | 1 |

Largest parent families: E11 (81), E08 (64), E10 (52), I70 (49), E13 (34), I50 (23), M10 (22), E78 (15), N18 (10), I42 (8), D64 (7).

**Indication-defining coverage:** T1D 52 codes · T2D 182 · HF 27 · CKD 29.
**Volume concentration:** I10, E78.5, E11.9, E78.2 = ~45% of patient volume; bottom 188 codes = <1%.

### 2.2 What we can remove

**TIER_1_DROP — 92 codes (safe)**
* *Oversplit diabetic retinopathy variants (69):* E11.3523, E10.3213, E11.3319, E11.3559, E08.311, E10.3311, E10.3211, E10.3312, E13.3293, E11.3533, E10.3212, E11.3499, E10.3413, E08.3213, E08.3393, E08.3513, E11.3419, E11.3542, E10.3522, E13.311, E10.3521, E08.3553, E08.3291, E11.3541, E08.3313, E08.3292, E10.3532, E08.3211, E08.3593, E13.3299, E10.3531, E10.3523, E13.3393, E11.3543, E08.3299, E08.3311, E08.3511, E11.3539, E08.3413, E08.3212, E13.3291, E10.3533, E08.3512, E13.3292, E13.3213, E08.3493, E08.3312, E08.3599, E08.3391, E08.3392, E08.3592, E08.3591, E08.3219, E13.3211, E11.3529, E13.3212, E08.3519, E13.3399, E08.3399, E08.3411, E13.3391, E08.3319, E13.3219, E13.3392, E08.3412, E08.3491, E11.3549, E08.3492, E10.3539
* *Oversplit atherosclerosis bypass-graft codes (5):* I70.311, I70.312, I70.313, I70.318, I70.319
* *Trivial volume (18):* E08.3499, Z91.15, E08.3419, E10.3529, E08.329, D64.8, I73.8, I50.8, E08.321, E11.352, E13.329, E08.339, E08.351, E11.353, E08.341, plus ICD-9 legacy **585.6, 428.9, 285.21** (<5 patients each)

**TIER_2_DROP — 16 codes (conditional, non-discriminative)**
* *Essential hypertension (1):* I10. 46.5M patients; almost every T2D/CKD/HF patient has it.
* *Hyperlipidemia (15):* E78.5, E78.2, E78.00, E78.01, E78.1, E78.3, E78.4, E78.41, E78.49, E78.6, E78.70, E78.79, E78.81, E78.89, E78.9

**TIER_3_REVIEW — 13 codes (low volume, inconclusive)**
* *Gout (M10.x, 9):* M10.021, M10.031, M10.032, M10.041, M10.042, M10.062, M10.471, M10.472, M10.49
* *Other:* I70.228, I70.298, D64.0, I73.1

> **Keep, even though non-defining:** anemia (D64.9, 7.6M patients), PAD, long-term insulin use (Z79.4), oral hypoglycemic use (Z79.84). They carry strong indication skew in the patient-level tags and are high-value comorbidity features.

### 2.3 What we can add / change

* **Roll up retinopathy to parent instead of dropping outright:** collapse the 128 retinopathy sub-codes (median ~1.9K patients each) to parent families (E11.35x, E10.35x, E11.32x, …). This keeps the microvascular-complication signal while removing about 100 sparse columns.
* **ICD-9 → ICD-10 mapping:** the pipeline is not mapping 585.6 (ESRD), 428.9 (HF) and 285.21 (anemia in CKD). Map them to N18.6 / I50.9 / D63.1, or drop them.
* **HF expansion (NBA 3.1):** HF is covered by 27 codes, mostly I50.x, and the HFpEF codes (I50.3x) are already present. Real HFpEF identification needs echo + diastolic Dx combinations, which is upstream work rather than a code-list change.
* **Candidate additions not in the current 414-code list.** These are clinically motivated and need volume/signal validation before inclusion:
  * **E87.5 Hyperkalemia.** Kerendia safety; flagged as a gap in the feature review.
  * **Z94.0 Kidney transplant status.** CKD.
  * **I48.x Atrial fibrillation.** Common HF comorbidity.
* **Use I10 / E78.x as patient context, not features:** if dropped as features, they can still serve as denominators or filters (e.g., hypertensive T2D patients).

---

## 3. Procedure (Px) Codes

### 3.1 What NBA 3.0 used

* **Source:** `px_input_claims_all_events_features_input`, built from Snowflake `STG_CAR_IQV_LAAD_FACT_PX` + `STG_CAR_IQV_LAAD_DIM_PRCDR_CD` and filtered to `Kerendia NBA 3.0 - Px Event List.csv`.
* **153 procedure codes** (5-character CPT/HCPCS strings). 20 echo codes are relabelled with `PROCEDURE_DESCRIPTION = 'echo_tests'`.
* **39 of 153 indication-defining.** The top 3 codes (lipid panel 80061, HbA1c 83036, creatinine 82570) are ~45% of volume.

| Category | Codes |
| --- | --- |
| Lab tests coded as procedures (CPT 8xxxx) | 37 |
| Dialysis / Nephrology | 11 |
| Vascular / Dialysis access | 13 |
| Cardiology (CPT 93xxx, echo, BNP) | 16 |
| HCPCS supplies (CGM, insulin pump, DME) | 17 + 4 E-codes |
| HCPCS J-codes (ESA, iron, cinacalcet, vitamin D) | 22 |
| HCPCS C / G / Q codes | 10 / 4 / 3 |
| Category II performance measures (HbA1c thresholds) | 5 |
| Other / surgery / E&M | 11 |

### 3.2 What we can remove

**TIER_1_DROP — 6 codes (safe):** J1921 (labetalol inj.), 0439T (echo, 393 pts), K0553, K0554 (CGM receiver/supply, <50 pts), S0171, Q9972

**TIER_2_DROP — 10 codes (conditional, non-specific lab panels that duplicate the Lab table)**

| Code | Description | Reason |
| --- | --- | --- |
| 80061 | Lipid panel | Universal screening (27.5M pts) |
| 80048 | Basic metabolic panel | Universal |
| 80050 | General health panel | Background screening |
| 80076 | Hepatic function panel | Not Kerendia-specific |
| 84460 | ALT | Hepatic enzyme |
| 84450 | AST | Hepatic enzyme |
| 82248 | Direct bilirubin | Hepatic marker |
| 83721 | LDL direct | Lipid screening |
| 3044F | HbA1c <7% | Well-controlled; non-discriminative |
| 3045F | HbA1c 7–9% (legacy) | Non-discriminative |

Dropping these removes ~30% of Px patient volume while preserving nearly all modelling signal.

**TIER_3_REVIEW — 10 codes (low volume):** 84206, 83700, 83701, J1805, J1610, J1611, E2102, C8923, C8925, C8927

### 3.3 What we can add / change

**Keep and prioritise (validated in the Px analysis):**
* Dialysis / ESRD services (90935, 90937, 90945, 90947, 90960–90966, 99512) and dialysis access (36800, 36831–36833, 36901–36909) are the cleanest CKD markers in the whole pipeline (97–100% CKD by patient). Keep them all, even at low volume.
* BNP / natriuretic peptide (83880): 2.0M patients, 54% HF. This is the **only HF biomarker in the pipeline**, because the Lab source has no BNP.
* High-A1C Category II codes (3051F, 3052F, 3046F) mark uncontrolled diabetes. Keep them.
* CGM supply codes (A4239, A4238, E2103) and insulin-pump supplies (A4230, A4232) carry strong T1D signal (~80% T1D by patient for pump supplies).

**Indication-flag list corrections (from the Px indication mapping):**
* Remove HbA1c (83036 / 83037) from the **T1D** code flag. It inflates T1D about 50x (24.1M by code vs 0.48M by patient); keep it for T2D only.
* Remove stress echo (93350 / 93351) from the **HF** code flag (9x over-count). Treat TTE (93306) as a weak HF signal, since it is 3.4x over the patient-level HF count.
* Add 90999 (unlisted dialysis, ~100% CKD) to the **CKD** flag.
* Add A4230 / A4232 (insulin-pump supplies) to the **T1D** flag.

**New codes to add to the Px event list.** These are absent from the 3.0 list; we need a re-pull from the raw `STG_CAR_IQV_LAAD_FACT_PX` to size them:

| Indication | Codes | Description |
| --- | --- | --- |
| CKD | 50300–50380 | Kidney transplant (only 50360 present today) |
| CKD | 50200, 50205 | Kidney biopsy |
| CKD | 36147, 36810–36870 (missing subset) | Additional AV fistula / graft / dialysis-catheter codes |
| CKD | 90951–90959, 90963–90970 (missing subset) | Additional ESRD monthly service codes |
| HF | 93451, 93453, 93456, 93457, 93460, 93461 | Right heart catheterisation |
| HF | 75557, 75559, 75561, 75563 | Cardiac MRI |
| HF | 33224–33231, 33240–33249, 33262–33264 | CRT / ICD placement |
| HF | 33975–33980, 33990–33993 | VAD insertion / removal |
| T1D | 95249, 95250, 95251 | Professional CGM |
| T1D | 95990, 95991 | Insulin pump refill / management |
| T2D | 92227, 92228, 92229 | Diabetic retinal imaging |

---

## 4. Lab Codes

### 4.1 What NBA 3.0 used

* **Source:** `lab_input_claims_12M_and_first_occ_features_input`, built from Snowflake `STG_CAR_IQV_QUEST_TO_LAAD_HIST`.
* **Only 2 test types** (`TEST_TYPE`), derived by name matching on `LCL_LAB_TEST_NM_CLEAN`:
  * `GFR`: name LIKE `%GFR%` or `%GLOMERULAR%`
  * `UACR`: name LIKE `%ALB%` or `%RATIO%`
* **Filters applied:**
  * Unit in (`ML/MIN/1.73M2`, `MCG/MGCREAT`, `MG/G{CREAT}`, `MG/GCREAT`, `MG/GCR`).
  * Numeric results only.
  * **Primary-care specialties only** (FM, FPG, GP, GPM, IFP, IM, IMG, IPM, NRP, PHA). This excludes the nephrology, cardiology and endocrinology ordering HCPs.
* **No LOINC code** was carried into the feature table. `MEDIAN_TEST_RESULT` is loaded but no feature uses it.
* Volume: GFR 201M rows / 65.3M patients; UACR 36.9M rows / 16.4M patients.

**Raw-source profile (24 months, all specialties, used for the Lab analysis):**
* 378M test rows, 69.5M patients.
* 45 LOINC × test-name combinations; `LOINC_CD` null rate 1.8%.
* Only 4 clinical test families present: **eGFR, UACR, HbA1c, Potassium**. There are no BNP, troponin, glucose or T1D antibody labs.

### 4.2 What we can remove

**TIER_1_DROP — 17 LOINCs (safe, trivial volume or unidentified)**
* *Microbiology / unrelated tests with no TEST_NAME:* 29577-4, 10704-5, 17934-1, 9787-3, 20932-0, 10656-7, 12276-2, 13655-6, 32701-5, 249-3, 35863-0, 32378-2, 655-1
* *Trivial-volume rows of known tests:* 98980-6 (unnamed row), 34535-5, 14958-3 (unnamed row), 2160-0

**TIER_2_DROP — 2 (conditional, data quality):**
* 61151-7: serum albumin mislabelled as UACR.
* Null-LOINC / null-name row.
* Resolve the names upstream before deciding.

**TIER_3_REVIEW — 6 (low-volume LOINC variants; roll up rather than model separately)**
* *UACR variants:* 14683-7, 19153-6, 13362-9, 49023-5
* *eGFR variants:* 33914-3, 88294-4

### 4.3 What we can add / change

**New test families (not used in NBA 3.0):**

| Family | LOINC | Patients (24m) | Why |
| --- | --- | --- | --- |
| Potassium (Kerendia safety) | 2823-3 | 27.8M | Only potassium-monitoring signal in the pipeline; hyperkalemia monitoring was flagged as a gap |
| HbA1c (diabetes control) | 4548-4 | 18.3M | Diabetes control; complements Px 83036 with actual values |

**Expanded LOINC coverage for existing families (roll up to one feature per family):**
* **eGFR:** 98979-8 (CKD-EPI 2021, 67.0M pts — primary), 50210-4 (0.37M), 48642-3, 62238-1, 88293-6, 88294-4, 98980-6 (creatinine + cystatin C), 33914-3. Also add a **name-based fallback for null-LOINC eGFR rows (4.6M patients)**.
* **UACR:** 9318-7 (primary, 16.1M), 14957-5 (urine microalbumin), 2161-8 (urine creatinine), 1754-1, 14958-3, 35674-1, 14683-7.

**Pipeline changes:**
* **Remove the PCP-only specialty filter.** The all-specialty pull (`lab_input_claims_all_specialties_v31`) has 285M rows / 71.3M patients vs 238M / 66.0M.
* **Build value-based features from `MEDIAN_TEST_RESULT`:**
  * eGFR <60 / 45 / 30
  * UACR ≥30 / ≥300 mg/g
  * K+ >5.0 / >5.5 mmol/L
  * HbA1c ≥7 / ≥9%
  * eGFR slope
  * eGFR-tested alone is a near-universal screen (67M by code vs 17.7M CKD by patient), so only low values indicate CKD.
* **Roll up by test family** (`eGFR_tested`, `UACR_tested`, `HbA1c_tested`, `K_tested` + value bands). LOINC granularity spreads signal across sparse columns.
* **Don't use `LCL_LAB_TEST_NM_CLEAN` for classification.** It mislabels urine creatinine (2161-8) and microalbumin (14957-5) as "Albumin/Creatinine ratio". Classify by LOINC instead.
* **Indication-flag correction:** remove HbA1c from the **T1D** code flag (18.3M by code vs 0.16M T1D by patient), the same issue as in Px.
* **HF labs:** BNP / NT-proBNP / troponin are not in the Quest-to-LAAD extract. Use Px 83880 as the HF biomarker proxy, or source BNP from a different lab feed.

---

## 5. Open Items / Dependencies

| Item | Owner | Blocking |
| --- | --- | --- |
| Re-run LAAD V6 pipeline with v4 mapping (11 groups removed, 13 added) | wenjie.chen@bayer.com | All product-group features |
| Verify DIGOXIN / DIGITEK / LANOXIN NDCs in IQVIA DIM_PRD (absent from V6) | LAAD pipeline team | CARDIAC GLYCOSIDES group |
| AFREZZA volume check in Snowflake | Data science | RAPID-ACTING INSULIN split |
| Re-pull raw Px without event-list filter to size new CKD/HF/T1D codes | Data science | Px additions (3.3) |
| Validate candidate Dx additions (E87.5, Z94.0, I48.x) | Data science | Dx additions (2.3) |
| Update NBA 3.1 notebooks 26/27/28 (NBRx/NRx/TRx) to v4 mapping | Data science | Rx features |
| Lab value-band features + specialty-filter removal joined into model base table | Data science | Lab additions (4.3) |
| Only 53% of lab patients and 73% of Px patients match `indication_table`. Patient-level indication percentages are lower bounds. | — | Interpretation |
