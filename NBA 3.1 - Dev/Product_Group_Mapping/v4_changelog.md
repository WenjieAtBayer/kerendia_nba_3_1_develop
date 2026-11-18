# Kerendia Market Basket Product Group Mapping — v4 Changelog

**Source:** `Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v3.xlsx`
**Output:** `Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`
**Date:** 2026-10-15
**Context:** T1D + HF indication expansion for Kerendia NBA 3.1

---

## 1. Summary Counts

| Metric | Count |
| --- | --- |
| **Total rows (v4)** | 487 |
| v3 original rows | 483 |
| Rows added (ADD + MONITOR) | 4 |
| **KEEP** (unchanged) | 340 |
| **RECLASSIFY** (moved between groups) | 70 |
| **REVIEW** (needs domain input) | 54 |
| **DROP** (recommended for removal) | 19 |
| **ADD** (new products) | 3 |
| **MONITOR** (watch for future addition) | 1 |
| **v3 distinct product groups** | 73 |
| **v4 distinct product groups** | 85 |
| New groups created | 13 |
| Groups dissolved | 1 (DIURETICS AND COMBOS → split into 3 + MRA) |

---

## 2. All New Groups Created

| New Group | Priority | # Products | Rationale |
| --- | --- | --- | --- |
| CARDIAC GLYCOSIDES | P3 | 3 | Digoxin (HF symptom management, ACC/AHA Class IIb). Absent from v3. Matches ENTRESTO tier. |
| T1D DISEASE-MODIFYING | P2 | 1 | Teplizumab (TZIELD) — only T1D disease-modifying agent. P2 matches specialty drug tier (GLP-1s). |
| GLUCAGON RESCUE | P4 | 3 | Hypoglycemia rescue meds (BAQSIMI, GVOKE, ZEGALOGUE). P4 for high-specificity T1D signal — prescribing is almost exclusive to insulin-treated patients at hypoglycemia risk. |
| INSULIN DELIVERY DEVICES | P6 | 3 | V-Go patch pumps. Device category, matches CGM AND SUPPLIES at P6. |
| HF VASODILATORS | P3 | 2 | BIDIL + generic hydralazine/isosorbide. HF-GDMT (NYHA III-IV, esp. Black patients). Matches ENTRESTO tier. |
| HF RATE CONTROL | P3 | 2 | Ivabradine (CORLANOR + generic). HF-GDMT for elevated HR despite max beta-blocker. Matches ENTRESTO tier. |
| CALCIMIMETICS | P4 | 3 | Cinacalcet/etelcalcetide for CKD-SHPT. Matches PHOSPHATE BINDERS/ESA tier. |
| CKD SYMPTOM MGMT | P4 | 1 | Difelikefalin (KORSUVA) for CKD pruritus. Matches PHOSPHATE BINDERS tier. |
| CKD SUPPORTIVE | P6 | 2 | Carnitine (L-CARNITINE, CARNITOR) for dialysis patients. Lower clinical priority. |
| LOOP DIURETICS | P4 | 11 | Furosemide, bumetanide, torsemide + brands. Split from DIURETICS AND COMBOS for HF signal specificity. Inherits P4. |
| THIAZIDE DIURETICS | P4 | 13 | HCTZ, chlorthalidone, metolazone + brands. Split from DIURETICS AND COMBOS. Inherits P4. |
| K-SPARING DIURETICS | P4 | 8 | Amiloride, triamterene, dyazide + brands. Split from DIURETICS AND COMBOS. Inherits P4. |
| CARDIAC MYOSIN ACTIVATORS | P3 | 1 | Placeholder for omecamtiv mecarbil (MONITOR status, pending FDA approval). |

---

## 3. All Reclassifications (70 products)

### 3.1 T1D Subset — from OTHERS (7 products)

| Product | From | To | Priority |
| --- | --- | --- | --- |
| TZIELD | OTHERS | T1D DISEASE-MODIFYING | P2 |
| BAQSIMI | OTHERS | GLUCAGON RESCUE | P4 |
| GVOKE | OTHERS | GLUCAGON RESCUE | P4 |
| ZEGALOGUE | OTHERS | GLUCAGON RESCUE | P4 |
| VGO 20 | OTHERS | INSULIN DELIVERY DEVICES | P6 |
| VGO 30 | OTHERS | INSULIN DELIVERY DEVICES | P6 |
| VGO 40 | OTHERS | INSULIN DELIVERY DEVICES | P6 |

### 3.2 HF Subset — from OTHERS (4 products)

| Product | From | To | Priority |
| --- | --- | --- | --- |
| BIDIL | OTHERS | HF VASODILATORS | P3 |
| ISOSORBIDE DI/HYDRALAZIN | OTHERS | HF VASODILATORS | P3 |
| CORLANOR | OTHERS | HF RATE CONTROL | P3 |
| IVABRADINE HCL | OTHERS | HF RATE CONTROL | P3 |

### 3.3 CKD Comorbidity Subset — from OTHERS (8 products)

| Product | From | To | Priority |
| --- | --- | --- | --- |
| PARSABIV | OTHERS | CALCIMIMETICS | P4 |
| SENSIPAR | OTHERS | CALCIMIMETICS | P4 |
| CINACALCET HCL | OTHERS | CALCIMIMETICS | P4 |
| KORSUVA | OTHERS | CKD SYMPTOM MGMT | P4 |
| L-CARNITINE | OTHERS | CKD SUPPORTIVE | P6 |
| CARNITOR | OTHERS | CKD SUPPORTIVE | P6 |
| XPHOZAH | OTHERS | PHOSPHATE BINDERS (existing) | P4 |
| SOD FERRIC GLUC CPLX | OTHERS | IRON DEFICIENCY DRUG (existing) | P3 |
| CAROSPIR | OTHERS | MINERALOCORTICOID RECEPTOR ANTAGONISTS (existing) | P4 |

### 3.4 Loop Diuretic Split — from DIURETICS AND COMBOS (34 products)

**LOOP DIURETICS (11):** BUMETANIDE, BUMEX, DEMADEX, EDECRIN, ETHACRYNIC ACID, FUROSCIX, FUROSEMIDE, FUROSEMIDE C-JECT, LASIX, SOAANZ, TORSEMIDE

**THIAZIDE DIURETICS (13):** CHLOROTHIAZIDE, CHLOROTHIAZIDE SOD, CHLORTHALIDONE, DIURIL, HYDROCHLOROTHIAZIDE, HYDRODIURIL, HYGROTON, INDAPAMIDE, METHYCLOTHIAZIDE, METOLAZONE, MICROZIDE, THALITONE, ZAROXOLYN

**K-SPARING DIURETICS (8):** AMILORIDE HCL, AMILORIDE HCL/HCTZ, DYAZIDE, DYRENIUM, MAXZIDE, MAXZIDE 25, TRIAMTERENE, TRIAMTERENE/HCTZ

**→ MRA (2):** ALDACTAZIDE, SPIRONOLACTONE/HCT → MINERALOCORTICOID RECEPTOR ANTAGONISTS

All inherit P4 from the dissolved DIURETICS AND COMBOS group.

### 3.5 T2D Combo Reclassifications — from OTHERS (11 products)

| Product | From | To | Priority |
| --- | --- | --- | --- |
| JANUMET | OTHERS | JANUVIA | P2 |
| JANUMET XR | OTHERS | JANUVIA | P2 |
| JENTADUETO | OTHERS | TRADJENTA | P4 |
| JENTADUETO XR | OTHERS | TRADJENTA | P4 |
| KAZANO | OTHERS | ALOGLIPTIN_NESINA COMBOS | P5 |
| OSENI | OTHERS | ALOGLIPTIN_NESINA COMBOS | P5 |
| KOMBIGLYZE XR | OTHERS | SAXAGLIPTIN_ONGLYZA COMBOS | P4 |
| GLYXAMBI | OTHERS | EMPAGLIFLOZIN_JARDIANCE COMBOS | P1 |
| SEGLUROMET | OTHERS | ERTUGLIFLOZIN_STEGLATRO COMBOS | P1 |
| NATEGLINIDE | OTHERS | PRANDIN | P4 |
| TRANDOL/VERAP HCL | OTHERS | ACE INHIBITORS AND COMBOS | P3 |

### 3.6 Insulin Misclassifications — from OTHERS (5 products)

| Product | From | To | Priority |
| --- | --- | --- | --- |
| NOVOLIN N | OTHERS | SHORT-ACTING HUMAN INSULIN | P6 |
| NOVOLIN N FLEXPEN | OTHERS | SHORT-ACTING HUMAN INSULIN | P6 |
| NOVOLOG FLXPEN MIX 70/30 | OTHERS | PRE-MIXED INSULIN | P6 |
| NOVOLOG MIX 70/30 | OTHERS | PRE-MIXED INSULIN | P6 |
| MYXREDLIN | OTHERS | PRE-MIXED INSULIN | P6 |

### 3.7 Pioglitazone Reclassifications — from OTHERS (3 products, inherit DROP)

| Product | From | To | Priority | Note |
| --- | --- | --- | --- | --- |
| PIOGLITAZONE HCL | OTHERS | ACTOS | P5 | Inherits DROP — parent group flagged for removal |
| PIOGLIT/GLIMEPIRID | OTHERS | PIOGLITAZONE_ACTOS COMBOS | P5 | Inherits DROP |
| PIOGLIT/METFORMIN | OTHERS | PIOGLITAZONE_ACTOS COMBOS | P5 | Inherits DROP |

---

## 4. All Drops (19 products)

### Product-group-level drops

| Group | Products | HCPs | TRX | Reason |
| --- | --- | --- | --- | --- |
| SULFONYLUREAS | CHLORPROPAMIDE, DIABETA | 3 | 3 | Obsolete first-gen sulfonylureas |
| ADLYXIN | ADLYXIN | 21 | 31 | Lixisenatide — discontinued in US 2023 |
| BEXAGLIFLOZIN | BEXAGLIFLOZIN | 42 | 48 | SGLT2i approved then immediately withdrawn from US market |
| PIOGLITAZONE_ACTOS COMBOS | ACTOPLUS MET, ACTOPLUS MET XR, AVANDIA, DUETACT + 2 incoming from OTHERS | 71 | 587 | Brand TZD combos, near-dead |
| ACTOS | ACTOS + PIOGLITAZONE HCL (incoming) | 483 | 3,141 | Brand pioglitazone — 0.2% prevalence; generic captures molecule |
| MIGLITOL | GLYSET, MIGLITOL | 1,225 | 12,685 | Alpha-glucosidase inhibitor — no CKD/HF/CVD mechanistic link |
| TEKTURNA | TEKTURNA, TEKTURNA HCT | 1,331 | 6,672 | Direct renin inhibitor — largely withdrawn internationally |
| CYCLOSET | CYCLOSET | 1,643 | 24,659 | Bromocriptine for T2D — no CKD/HF/CVD mechanistic link |

### Individual product drops from OTHERS

| Product | Reason |
| --- | --- |
| TANZEUM | GLP-1 RA (albiglutide) — discontinued 2018 |
| TOLBUTAMIDE | First-gen sulfonylurea — obsolete, near-zero volume |

---

## 5. All Review Items (54 products)

| Item | # Products | Question | Owner |
| --- | --- | --- | --- |
| CALCIUM CHANNEL BLOCKERS AND COMBOS | 52 | CV=1.27, lowest variance among high-prevalence groups (103.2% HCP prevalence). Candidate for drop if model needs feature pruning. | Data science team |
| DM2 | 1 | Unclear product name in OTHERS — possible data artifact. Look up in IQVIA DIM_PRD to determine what this product is. | LAAD pipeline team (product ops) |
| INSULIN GLAR M SOL | 1 | Possibly duplicate of BASAL (LONG-ACTING) INSULIN (insulin glargine multi-dose solution). 30K HCPs, 145K TRX. Verify against DIM_PRD. | LAAD pipeline team |

---

## 6. Monitor Items (1 product)

| Product | Group | Priority | Trigger Event |
| --- | --- | --- | --- |
| OMECAMTIV MECARBIL | CARDIAC MYOSIN ACTIVATORS | P3 | Pending FDA approval. Cardiac myosin activator studied in GALACTIC-HF trial. Add as active product group when approved. |

---

## 7. Rows Added (4 rows)

### DIGOXIN — CARDIAC GLYCOSIDES (3 rows, ADD)

| PRODUCT_NAME | PRODUCT_GROUP | PRIORITY |
| --- | --- | --- |
| DIGOXIN | CARDIAC GLYCOSIDES | 3 |
| DIGITEK | CARDIAC GLYCOSIDES | 3 |
| LANOXIN | CARDIAC GLYCOSIDES | 3 |

**Caveat:** These 3 products are the standard digoxin formulations. IQVIA DIM_PRD may contain additional NDC-level entries (e.g., LANOXIN PEDIATRIC, DIGOXIN ORAL SOLUTION). The LAAD pipeline team must verify against `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD` and add any additional entries before production use.

### OMECAMTIV MECARBIL — CARDIAC MYOSIN ACTIVATORS (1 row, MONITOR)

Placeholder row. Not currently in IQVIA data. Will be added when FDA-approved.

---

## 8. Decisions Made

### 8.1 DIGOXIN Group Naming: CARDIAC GLYCOSIDES (not DIGOXIN)

**Reasoning:** Multi-product drug-class groups in the file use class-level names (PHOSPHATE BINDERS, ERYTHROPOIESIS STIMULATING AGENTS, IRON DEFICIENCY DRUG). Digoxin has 3 product formulations (DIGOXIN, DIGITEK, LANOXIN) — the class name is cleaner and more descriptive in the feature column context (TOTAL_HCP_NBRX_CLAIMS_CARDIAC_GLYCOSIDES_...).

### 8.2 DIGOXIN Priority: P3

**Reasoning:** P3 contains ENTRESTO (HF pillar 1) — the only other dedicated HF drug with its own group. Digoxin is a guideline-recommended HF drug (ACC/AHA Class IIb for symptom/hospitalization reduction). P4 is themed around "second-tier diabetes + CKD renal" which is a poor fit for a cardiac drug.

### 8.3 GLUCAGON RESCUE Priority: P4 (not P6)

**Reasoning:** Prescribing is highly specific — glucagon rescue goes almost exclusively to insulin-treated patients at hypoglycemia risk, which is exactly the T1D-specialist signal the expansion targets. P6 pools it with high-volume, low-specificity groups (metformin, basal insulin), recreating the signal-dilution problem that the OTHERS decomposition was designed to solve. P4 preserves it as a discriminative therapeutic signal.

### 8.4 T1D DISEASE-MODIFYING Priority: P2

**Reasoning:** TZIELD (teplizumab) is the only FDA-approved T1D disease-modifying agent. P2 contains high-value specialty drugs (GLP-1 RAs). Signals specialist T1D care equivalent in prescriber-specificity to GLP-1 prescribing for T2D.

### 8.5 HF Groups (VASODILATORS, RATE CONTROL): P3

**Reasoning:** Both are guideline-recommended HF-GDMT drugs (BIDIL for NYHA III-IV, ivabradine for elevated HR). Same tier as ENTRESTO — all three are dedicated HF therapeutics with specific guideline indications.

### 8.6 Diuretic Split: All P4

**Reasoning:** All three sub-groups (LOOP, THIAZIDE, K-SPARING) inherit P4 from the dissolved DIURETICS AND COMBOS parent group. No clinical reason to differentiate priority within diuretic sub-classes.

### 8.7 T2D Combo Routing Convention

**Pattern applied:** Products routed to the existing group that matches their active ingredient:
- Brand combos → existing `{GENERIC}_{BRAND} COMBOS` group when one exists
- Brand combos without a combo group → parent brand group (e.g., JANUMET → JANUVIA, since JANUVIA already contains SITAGLIPTIN/METFORMIN)
- Priority inherited from the target group

### 8.8 Groups Dissolved

**DIURETICS AND COMBOS** — all 34 products reclassified into LOOP DIURETICS (11), THIAZIDE DIURETICS (13), K-SPARING DIURETICS (8), and MINERALOCORTICOID RECEPTOR ANTAGONISTS (2). The aggregate group no longer exists in v4.

---

## 9. v3 Priority Tier Sidebar Legend (preserved from Excel)

| Priority | Description |
| --- | --- |
| 1 | SGLT2 Inhibitors |
| 2 | GLP-1 |
| 3 | ACE/ARBs, Iron Deficiency, Vitamin D analogs |
| 4 | Mineralocorticoid Receptor Antagonists, Diuretics, Phosphate Binders, ESAs, Metformin, DPP-4 Inhibitors, Meglitinide |
| 5 | Calcium Channel Blockers, Beta Blockers, Glimepiride, Glipizide, Glyburide, Pioglitazone (Actos), Brenzavvy, Cycloset, Miglitol, Prandin, Starlix, Tradjenta, Sulfonylureas |
| 6 | Insulin, CGM & Supplies, Others |

**v4 additions to tier descriptions:**
- P2: + T1D Disease-Modifying (TZIELD)
- P3: + Cardiac Glycosides (digoxin), HF Vasodilators (BIDIL), HF Rate Control (ivabradine), Cardiac Myosin Activators (monitor)
- P4: + Calcimimetics, CKD Symptom Mgmt, Glucagon Rescue, Loop/Thiazide/K-Sparing Diuretics (split from P4 Diuretics)
- P6: + Insulin Delivery Devices, CKD Supportive

---

## 10. Upstream Pipeline Impact

**Pipeline location:** `/Users/wenjie.chen@bayer.com/kerendia_data_needs/LAAD based LRx Pipeline/`

**What changes require pipeline re-run (mapping file edit only):**
- All 70 reclassifications (PRODUCT_GROUP value changes in mapping)
- All 19 drops (remove rows from mapping, or keep and filter downstream)
- DIGOXIN addition requires DIM_PRD NDC lookup first

**What does NOT require pipeline code changes:**
- All of the above — the pipeline reads the mapping file at runtime
- Only the mapping Excel/CSV needs to be updated and placed at the expected path

**Blocking prerequisite:** IQVIA DIM_PRD must be queried to:
1. Verify DIGOXIN/DIGITEK/LANOXIN NDC codes exist in the raw data
2. Identify any additional digoxin formulations
3. Clarify DM2 and INSULIN GLAR M SOL product identities
