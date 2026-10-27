# NBA 3.1 — All Codes Analysis

**Source File:** `NBA all Codes analysis.xlsx`
**Location:** `Product_Group_Mapping/`
**Generated:** October 26, 2026

---

## 1. Overview

This workbook is a **code-level triage analysis** for the Kerendia NBA 3.1 (Next Best Action) feature engineering pipeline. It evaluates every medical code encountered in claims data across four domains — **Rx (prescriptions), Dx (diagnoses), Px (procedures), and Lab (laboratory tests)** — and assigns a tiered decision about whether to keep, drop, or manually review each code for feature inclusion.

The analysis answers: *Which codes should become NBA 3.1 features?*

### Decision Framework

| Decision | Meaning |
| --- | --- |
| **KEEP** | Code is retained as a modeling feature. High volume or strong indication signal. |
| **TIER\_1\_DROP** | Hard drop. Code is statistically unreliable (<20 patients) or an oversplit variant that should roll up to a parent code. |
| **TIER\_2\_DROP** | Soft drop. High volume but weak indication specificity — adds noise more than discriminative signal. |
| **TIER\_3\_REVIEW** | Manual review needed. Low volume with moderate signal — borderline case requiring human judgment. |

### Cross-Sheet Summary

| Sheet | Domain | Total Codes | KEEP | Dropped | TIER\_3\_REVIEW | In 752 Features | In NBA 3.0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rx | Prescriptions | 458 | 329 | 107 | 22 | 33 (7.2%) | 148 (32.3%) |
| Dx | Diagnoses | 414 | 293 | 108 | 13 | 22 (5.3%) | 414 (100%) |
| Px | Procedures | 153 | 127 | 16 | 10 | 24 (15.7%) | 153 (100%) |
| Lab | Lab Tests | 45 | 20 | 19 | 6 | 27 (60.0%) | 29 (64.4%) |
| **Total** | | **1,070** | **769** | **250** | **51** | **106 (9.9%)** | **744 (69.5%)** |

**Key takeaway:** 769 of 1,070 codes (71.9%) are KEEP. The remaining 301 are either dropped (250) or flagged for manual review (51). Only 9.9% of codes are already in the existing 752-feature set — NBA 3.1 expands the feature space substantially, especially in Rx (299 new KEEP drugs) and Dx (275 new KEEP codes).

---

## 2. Volume Concentration (Pareto Analysis)

A small fraction of codes captures the vast majority of patient volume:

| Sheet | Codes at 80% Volume | Total Codes | % of Codes for 80% Volume |
| --- | --- | --- | --- |
| Rx | 19 | 458 | 4.1% |
| Dx | 25 | 414 | 6.0% |
| Px | 9 | 153 | 5.9% |
| Lab | 3 | 45 | 6.7% |

**Insight:** Across all domains, roughly 4–7% of codes account for 80% of all patient encounters. This validates the tiered approach — the long tail of low-volume codes can be safely dropped without losing meaningful signal.

---
## 3. Rx Sheet — Prescription Drugs

### 3.1 Structure (458 rows, 18 columns)

| Column | Description |
| --- | --- |
| `PRODUCT_NAME` | Generic or brand drug name |
| `PRODUCT_GROUP` | Therapeutic class or brand group (54 distinct groups) |
| `decision` | KEEP / TIER_1_DROP / TIER_2_DROP / TIER_3_REVIEW |
| `reason` | Human-readable justification for the decision |
| `patients_total` | Total patients prescribed the drug |
| `providers_total` | Total prescribing HCPs |
| `nbrx_total` | Total new prescriptions (NBRx) |
| `PTNT_PCT_T1D` | % of patients with Type 1 Diabetes |
| `PTNT_PCT_T2D` | % of patients with Type 2 Diabetes |
| `PTNT_PCT_HF` | % of patients with Heart Failure |
| `PTNT_PCT_CKD` | % of patients with Chronic Kidney Disease |
| `in_top_80pct_volume` | YES if drug is in the top 80% cumulative volume |
| `cum_pct_vol` | Cumulative % of volume at this drug |
| `in_752_features` | YES if drug is already in the 752-feature set |
| `n_752_matches` | Number of matching 752 features |
| `matched_752_features` | Names of matched 752 features |
| `considered_in_nba_30` | YES if drug was considered in NBA 3.0 |
| `nba_30_match_type` | Match type for NBA 3.0 (event_name_match / no_match) |

### 3.2 Decision Distribution

| Decision | Count | % of Total |
| --- | --- | --- |
| KEEP | 329 | 71.8% |
| TIER_1_DROP | 74 | 16.2% |
| TIER_2_DROP | 33 | 7.2% |
| TIER_3_REVIEW | 22 | 4.8% |

### 3.3 Product Groups (54 distinct)

The top therapeutic groups by drug count:

| Product Group | Total Drugs | KEEP | Dropped | Review |
| --- | --- | --- | --- | --- |
| OTHERS | 264 | 181 | 63 | 20 |
| BB (Beta-blockers) | 40 | 23 | 10 | 7 |
| ARB | 39 | 27 | 10 | 2 |
| ACE | 35 | 22 | 10 | 3 |
| DIURETICS | 30 | 18 | 11 | 1 |

The remaining 49 groups are mostly single-drug brand groups (MOUNJARO, JARDIANCE, OZEMPIC, KERENDIA, FARXIGA BRAND, etc.) — all classified as discriminative drugs with strong indication signals.

### 3.4 Top 10 Drugs by Patient Volume

| Rank | Product Name | Group | Patients | Providers | NBRx | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | AMLODIPINE BESYLATE | OTHERS | 9,054,597 | 731,287 | 9,185,895 | KEEP |
| 2 | LOSARTAN POTASSIUM | ARB | 8,600,093 | 622,355 | 8,704,609 | KEEP |
| 3 | LISINOPRIL | ACE | 6,544,162 | 630,862 | 6,637,105 | KEEP |
| 4 | FUROSEMIDE | DIURETICS | 5,819,329 | 689,628 | 5,916,404 | KEEP |
| 5 | METOPROLOL SUCCINATE ER | BB | 5,350,604 | 547,122 | 5,409,914 | KEEP |
| 6 | SPIRONOLACTONE | SPIRONOLACTONE | 5,349,989 | 598,912 | 5,415,325 | KEEP |
| 7 | MOUNJARO | MOUNJARO | 4,914,681 | 324,625 | 4,952,813 | KEEP |
| 8 | PROPRANOLOL HYDROCHLORIDE | BB | 4,566,010 | 540,393 | 4,648,573 | KEEP |
| 9 | METFORMIN HYDROCHLORIDE | OTHERS | 4,103,921 | 560,186 | 4,157,229 | KEEP |
| 10 | JARDIANCE | JARDIANCE | 3,861,300 | — | — | KEEP |

### 3.5 Indication Breakdown (KEEP drugs only)

For the 329 KEEP drugs, the patient percentage distribution by indication:

| Indication | Mean % | Median % | Max % |
| --- | --- | --- | --- |
| T1D | 6.26 | 0.60 | 78.80 |
| T2D | 48.29 | 38.80 | 100.00 |
| HF | 13.96 | 8.70 | 100.00 |
| CKD | 24.69 | 20.80 | 100.00 |

**Insight:** T2D is the dominant indication across the drug portfolio (mean 48.3%), aligning with Kerendia's label for T2D-associated CKD. CKD is the second strongest (mean 24.7%), followed by HF (14.0%). T1D is rare (6.3%) — Kerendia is not indicated for T1D.

### 3.6 Discriminative Drugs (110 drugs)

110 drugs are flagged as **discriminative** — they have a strong indication signal (max patient % above a threshold), meaning their prescription pattern is itself informative about the patient's underlying condition. These include:

* **Diabetes drugs:** MOUNJARO (99%), METFORMIN (100%), JARDIANCE (79%), OZEMPIC (88%), TRULICITY (99%), RYBELSUS, FARXIGA (75%), DAPAGLIFLOZIN (75%), WEGOVY, ZEPBOUND
* **Heart failure drugs:** ENTRESTO brand/generic (100%), SACUBITRIL/VALSARTAN (100%)
* **CKD-relevant:** SPIRONOLACTONE (6 matched features), KERENDIA (85%)

### 3.7 Reason Patterns

| Reason Category | Count | Description |
| --- | --- | --- |
| High volume | 39 | Large patient base; prescribing pattern alone is informative |
| Discriminative | 110 | Strong indication signal — drug is specific to T2D/HF/CKD |
| Low volume | 41 | Low patient count; statistically marginal |
| <20 patients | 74 (TIER_1_DROP) | Statistically unreliable regardless of indication |
| Weak indication specificity | 33 (TIER_2_DROP) | High volume but non-discriminative (e.g., hypertension workhorses) |
| Low volume + weak signal | 22 (TIER_3_REVIEW) | Borderline — manual review needed |

---
## 4. Dx Sheet — Diagnosis Codes

### 4.1 Structure (414 rows, 19 columns)

| Column | Description |
| --- | --- |
| `DIAGNOSIS_CODE` | ICD-10 (or legacy ICD-9) code |
| `DIAGNOSIS_DESCRIPTION` | Human-readable diagnosis name |
| `decision` | KEEP / TIER_1_DROP / TIER_2_DROP / TIER_3_REVIEW |
| `reason` | Justification |
| `patients_total` | Total patients with this diagnosis |
| `is_defining` | YES if this is a defining/qualifying diagnosis |
| `PCT_T1D` / `PCT_T2D` / `PCT_HF` / `PCT_CKD` | Patient % by indication |
| `icd_chapter` | ICD-10 chapter grouping |
| `icd_parent` | Parent ICD code for roll-up analysis |
| `in_top_80pct_volume` / `cum_pct_vol` | Volume concentration flags |
| `in_752_features` / `n_752_matches` / `matched_752_features` | Feature matching |
| `considered_in_nba_30` / `nba_30_match_type` | NBA 3.0 coverage |

### 4.2 Decision Distribution

| Decision | Count | % of Total |
| --- | --- | --- |
| KEEP | 293 | 70.8% |
| TIER_1_DROP | 92 | 22.2% |
| TIER_2_DROP | 16 | 3.9% |
| TIER_3_REVIEW | 13 | 3.1% |

### 4.3 ICD Chapter Breakdown

| ICD Chapter | Total | KEEP | Dropped | Review |
| --- | --- | --- | --- | --- |
| Endocrine/Metabolic (E00-E89) | 249 | 154 | 95 | 0 |
| Circulatory (I00-I99) | 101 | 90 | 8 | 3 |
| Musculoskeletal (M00-M99) | 22 | 13 | 0 | 9 |
| Factors/Status (Z00-Z99) | 12 | 11 | 1 | 0 |
| Genitourinary (N00-N99) | 10 | 10 | 0 | 0 |
| Blood/Immune (D50-D89) | 8 | 6 | 1 | 1 |
| Pregnancy/Childbirth (O00-O9A) | 5 | 5 | 0 | 0 |
| Injury/Toxic (S00-T88) | 3 | 3 | 0 | 0 |
| ICD-9 legacy | 3 | 0 | 3 | 0 |
| Symptoms/Signs (R00-R99) | 1 | 1 | 0 | 0 |

**Insight:** Endocrine/Metabolic codes dominate (60% of all diagnoses) — this is the T2D heartland. 80% of Endocrine drops are TIER_1 (oversplit retinopathy/neuropathy variants that should roll up to parent codes). All Genitourinary (CKD) and Circulatory (HF) codes are KEEP — these are core Kerendia indications. All ICD-9 legacy codes are dropped.

### 4.4 Top 15 KEEP Diagnosis Codes

| Code | Description | Patients | T2D % | HF % | CKD % |
| --- | --- | --- | --- | --- | --- |
| E11.9 | Type 2 DM without complications | 16,948,649 | 98.6 | 20.6 | 40.2 |
| D64.9 | Anemia, unspecified | 7,580,727 | 48.5 | 29.4 | 46.2 |
| E11.65 | T2DM with hyperglycemia | 6,747,820 | 97.9 | 22.9 | 47.5 |
| I12.9 | Hypertensive CKD, stage 1-4 | 5,105,633 | 56.4 | 28.6 | 100.0 |
| N18.31 | CKD, Stage 3A | 4,358,658 | 52.3 | 32.7 | 100.0 |
| E11.22 | T2DM with diabetic CKD | 4,271,946 | 98.0 | 45.3 | 100.0 |
| I50.9 | Heart failure, unspecified | 4,073,730 | 57.0 | 100.0 | 62.7 |
| E11.69 | T2DM with other specified complication | 3,585,641 | 98.9 | 23.6 | 52.0 |
| Z79.4 | Long-term insulin use | 3,547,151 | 89.7 | 29.4 | 55.4 |
| I11.0 | Hypertensive heart disease with HF | 3,366,752 | 55.5 | 100.0 | 50.3 |
| I73.9 | Peripheral vascular disease, unspecified | 3,299,125 | 53.1 | 38.2 | 52.1 |
| Z79.84 | Long-term oral hypoglycemic use | 3,164,772 | 96.7 | 22.6 | 44.4 |
| N18.9 | CKD, unspecified | 3,022,355 | 58.3 | 45.1 | 100.0 |
| E11.42 | T2DM with diabetic polyneuropathy | 2,972,715 | 98.0 | 34.3 | 58.9 |
| N18.32 | CKD, Stage 3B | 2,728,475 | 60.5 | 44.1 | 100.0 |

### 4.5 TIER_1_DROP Analysis (92 codes)

The largest drop category in Dx is **oversplit codes** — 74 of 92 codes (80%) are ICD-10 sub-specifications that should roll up to their parent code:

* **Diabetic retinopathy variants** (e.g., E11.3511, E11.3599) → roll up to E11.35
* **Diabetic neuropathy variants** → roll up to parent
* **CKD stage sub-variants** → roll up to parent

The remaining 18 TIER_1_DROP codes are low-volume codes with <20 patients.

### 4.6 TIER_2_DROP: Near-Universal Comorbidities (16 codes)

These are high-volume diagnoses that are near-universal in T2D/CKD/HF cohorts and add noise rather than discriminative signal:

* **Essential hypertension (I10)** — 46.5M patients, 42% T2D / 33% CKD / 17% HF prevalence
* **Hyperlipidemia variants (E78.5, E78.2, E78.00)** — 25M+ patients collectively

**Insight:** These codes are so prevalent in the target cohort that they function as background flags, not discriminative features. Keeping them would dilute the model's ability to distinguish patient subgroups.

### 4.7 Reason Patterns

| Reason Category | Count |
| --- | --- |
| Indication-defining (core modeling feature) | 194 |
| Discriminative | 77 |
| High volume | 25 |
| Low volume | 13 |
| Non-specific | 15 |
| Oversplit (roll up to parent) | 74 |

### 4.8 Feature Coverage

**100% of Dx codes are considered in NBA 3.0** (code_match) — the diagnosis domain was fully covered in the previous iteration. However, only 22 (5.3%) are in the 752-feature set, meaning 275 KEEP codes are new additions for NBA 3.1.

---
## 5. Px Sheet — Procedure Codes

### 5.1 Structure (153 rows, 18 columns)

| Column | Description |
| --- | --- |
| `PROCEDURE_CODE` | CPT or HCPCS code |
| `PROCEDURE_DESCRIPTION` | Human-readable procedure name |
| `proc_category` | Category grouping (15 distinct) |
| `decision` | KEEP / TIER_1_DROP / TIER_2_DROP / TIER_3_REVIEW |
| `reason` | Justification |
| `patients_total` | Total patients with this procedure |
| `is_defining` | YES if defining procedure |
| `PCT_T1D` / `PCT_T2D` / `PCT_HF` / `PCT_CKD` | Patient % by indication |
| `in_top_80pct_volume` / `cum_pct_vol` | Volume concentration |
| `in_752_features` / `n_752_matches` / `matched_752_features` | Feature matching |
| `considered_in_nba_30` / `nba_30_match_type` | NBA 3.0 coverage |

### 5.2 Decision Distribution

| Decision | Count | % of Total |
| --- | --- | --- |
| KEEP | 127 | 83.0% |
| TIER_1_DROP | 6 | 3.9% |
| TIER_2_DROP | 10 | 6.5% |
| TIER_3_REVIEW | 10 | 6.5% |

Px has the **highest KEEP rate (83%)** of all four domains — procedures are highly relevant to Kerendia's target indications.

### 5.3 Procedure Categories (15 distinct)

| Category | Total | KEEP | Dropped | Review |
| --- | --- | --- | --- | --- |
| Lab (CPT 8xxxx) | 37 | 26 | 0 | 3 |
| HCPCS J codes (drugs) | 22 | 18 | 1 | 3 |
| HCPCS supplies (CGM, insulin, DME) | 17 | 17 | 0 | 0 |
| Cardiology (CPT 93xxx) | 16 | 16 | 0 | 0 |
| Vascular/Dialysis access | 13 | 13 | 0 | 0 |
| Dialysis/Nephrology | 11 | 11 | 0 | 0 |
| HCPCS C codes | 10 | 7 | 0 | 3 |
| Other | 8 | 4 | 4 | 0 |
| Category II performance measures | 5 | 3 | 0 | 2 |
| HCPCS G codes | 4 | 4 | 0 | 0 |
| HCPCS E codes (DME) | 4 | 3 | 0 | 1 |
| HCPCS Q codes | 3 | 2 | 1 | 0 |
| E&M visits | 1 | 1 | 0 | 0 |
| Urology/Renal surgery | 1 | 1 | 0 | 0 |
| Surgery (CPT 1-6xxxx) | 1 | 1 | 0 | 0 |

**Insight:** All Cardiology (echo, EKG), Dialysis/Nephrology, Vascular/Dialysis access, and CGM/insulin supply codes are KEEP — these directly map to Kerendia's T2D-CKD patient journey. TIER_2_DROPS are mostly lab panels (lipid panels, BMP, GHP) that are redundant with individual component tests already kept.

### 5.4 Top 10 Procedures by Patient Volume

| Code | Description | Category | Patients | Decision |
| --- | --- | --- | --- | --- |
| 80061 | Lipid panel | Lab (CPT 8xxxx) | 27,462,446 | TIER_2_DROP |
| 83036 | HbA1c (glycosylated hemoglobin) | Lab (CPT 8xxxx) | 24,056,565 | KEEP |
| 82570 | Creatinine | Lab (CPT 8xxxx) | 10,081,125 | KEEP |
| 82043 | Urine albumin (microalbumin) | Lab (CPT 8xxxx) | 9,748,382 | KEEP |
| 93306 | Echocardiogram (echo) | Cardiology (CPT 93xxx) | 8,945,208 | KEEP |
| 3044F | HbA1c <7.0% (DM performance measure) | Category II | 8,508,853 | TIER_2_DROP |
| 80048 | Basic metabolic panel | Lab (CPT 8xxxx) | 7,488,263 | TIER_2_DROP |
| 80050 | General health panel | Lab (CPT 8xxxx) | 5,342,747 | TIER_2_DROP |
| 83880 | Natriuretic peptide (BNP) | Lab (CPT 8xxxx) | 2,012,181 | KEEP |
| 3051F | HbA1c 7.0–8.0% (DM performance measure) | Category II | 1,886,811 | KEEP |

**Insight:** HbA1c, creatinine, urine albumin, echo, and BNP are the core KEEP procedures — they directly track diabetes control, kidney function, and heart failure status. Lab panels (lipid, BMP, GHP) are dropped because their individual components (creatine, HbA1c, etc.) are already kept separately.

---
## 6. Lab Sheet — Laboratory Tests

### 6.1 Structure (45 rows, 19 columns)

| Column | Description |
| --- | --- |
| `LOINC_CD` | LOINC code for the lab test |
| `TEST_NAME` | Human-readable test name |
| `test_family` | Logical grouping (5 families) |
| `decision` | KEEP / TIER_1_DROP / TIER_2_DROP / TIER_3_REVIEW |
| `reason` | Justification |
| `patients_total` | Total patients with this test |
| `tests_total` | Total test orders |
| `is_defining` | YES if defining lab test |
| `PCT_T2D` / `PCT_HF` / `PCT_CKD` / `PCT_K_SAFETY` | Patient % by indication/safety |
| `in_top_80pct_volume` / `cum_pct_vol` | Volume concentration |
| `in_752_features` / `n_752_matches` / `matched_752_features` | Feature matching |
| `considered_in_nba_30` / `nba_30_match_type` | NBA 3.0 coverage |

### 6.2 Decision Distribution

| Decision | Count | % of Total |
| --- | --- | --- |
| KEEP | 20 | 44.4% |
| TIER_1_DROP | 17 | 37.8% |
| TIER_2_DROP | 2 | 4.4% |
| TIER_3_REVIEW | 6 | 13.3% |

Lab has the **lowest KEEP rate (44.4%)** — many LOINC codes are redundant variants of the same underlying test.

### 6.3 Test Families (5 families)

| Test Family | Total | KEEP | Dropped | Review |
| --- | --- | --- | --- | --- |
| eGFR (CKD function) | 12 | 12 | 0 | 0 |
| UACR (CKD albuminuria) | 14 | 12 | 0 | 2 |
| [UNIDENTIFIED — no TEST_NAME] | 17 | 0 | 17 | 0 |
| HbA1c (diabetes control) | 1 | 1 | 0 | 0 |
| Potassium (Kerendia safety) | 1 | 1 | 0 | 0 |

### 6.4 Core Lab Tests (all KEEP)

| LOINC | Test Name | Family | Patients | Signal |
| --- | --- | --- | --- | --- |
| 98979-8 | eGFR | eGFR (CKD function) | 67,028,597 | 26% max pt-based |
| 2823-3 | Potassium | Potassium (Kerendia safety) | 27,814,909 | 29% max pt-based |
| 4548-4 | Hemoglobin A1c | HbA1c (diabetes control) | 18,268,371 | 34% max pt-based |
| 9318-7 | Albumin/Creatinine (UACR) | UACR (CKD albuminuria) | 16,052,532 | 64% max pt-based |
| 14957-5 | Albumin/Creatinine (UACR) | UACR (CKD albuminuria) | 6,436,173 | 90% max pt-based |
| 2161-8 | Albumin/Creatinine (UACR) | UACR (CKD albuminuria) | 6,101,029 | 93% max pt-based |

### 6.5 Lab-Specific Insights

* **eGFR** is the highest-volume lab (67M patients) and has 12 LOINC variants — all are KEEP, as they all measure the same underlying CKD function marker. The numerous variants arise from different calculation methods (race-specific, CKD-EPI versions, etc.).
* **UACR** (urine albumin-to-creatinine ratio) has 14 LOINC codes with strong indication signal (up to 93% pt-based). This is the primary albuminuria marker for CKD staging and Kerendia eligibility.
* **Potassium** is specifically flagged as "Kerendia safety" — hyperkalemia is a known side effect of finerenone, making potassium monitoring a critical safety feature.
* **HbA1c** (18.3M patients) is the core diabetes control marker.
* **17 UNIDENTIFIED codes** (no TEST_NAME) are all TIER_1_DROP — these are data quality issues where the test type cannot be identified. They represent trivial volumes (1–44,515 patients) and are unusable for feature engineering.
* **6 TIER_3_REVIEW codes** are low-volume LOINC variants of eGFR and UACR that are already captured by primary codes — these could be rolled up or dropped.

---
## 7. Kerendia-Specific Insights

### 7.1 Kerendia (Finerenone) Profile

| Metric | Value |
| --- | --- |
| Product Group | KERENDIA |
| Patients | 191,109 |
| Providers | 39,783 |
| NBRx | 192,660 |
| T2D % | 85.2% |
| HF % | 33.6% |
| CKD % | 72.8% |
| T1D % | 1.7% |
| Decision | KEEP |
| Reason | Strong indication signal (max 85%). Discriminative drug. |
| In 752 Features | YES |
| In NBA 3.0 | YES (event_name_match) |

### 7.2 Competitive Landscape (all KEEP)

| Drug | Group | Patients | Signal Strength |
| --- | --- | --- | --- |
| MOUNJARO | MOUNJARO | 4,914,681 | 99% (T2D) |
| JARDIANCE | JARDIANCE | 3,861,300 | 79% (T2D) |
| OZEMPIC | OZEMPIC | 3,721,486 | 88% (T2D) |
| METFORMIN HCL | OTHERS | 4,103,921 | 100% (T2D) |
| ZEPBOUND | ZEPBOUND | 2,145,381 | — |
| WEGOVY | WEGOVY | 1,463,271 | — |
| FARXIGA | FARXIGA BRAND | 1,362,835 | 75% (T2D) |
| DAPAGLIFLOZIN | FARXIGA GENERIC | 1,073,510 | 75% (T2D) |
| TRULICITY | TRULICITY | 739,408 | 99% (T2D) |
| ENTRESTO | ENTRESTO BRAND | 494,207 | 100% (HF) |
| SACUBITRIL/VALSARTAN | ENTRESTO GENERIC | 600,638 | 100% (HF) |
| RYBELSUS | RYBELSUS | 473,090 | — |
| KERENDIA | KERENDIA | 191,109 | 85% (T2D/CKD) |

**Insight:** Kerendia's patient volume (191K) is significantly smaller than major competitors like Jardiance (3.9M), Ozempic (3.7M), and Farxiga (1.4M). However, Kerendia's indication signal is strongly specific to T2D+CKD (85.2% T2D, 72.8% CKD) — this is the discriminative profile the NBA model leverages. The prescribing pattern of Kerendia is itself a strong feature because it identifies the exact T2D-CKD patient segment the drug is indicated for.

### 7.3 Kerendia Safety Monitoring

The Lab sheet explicitly identifies **Potassium (LOINC 2823-3)** as a Kerendia safety test — this is critical because finerenone can cause hyperkalemia, and potassium monitoring is essential for patients on Kerendia therapy. This test is KEEP with 27.8M patients and 29% max pt-based signal.

---
## 8. Feature Evolution: NBA 3.0 → NBA 3.1

### 8.1 New Code Additions

Codes that are KEEP in NBA 3.1 but were NOT in the existing 752-feature set (i.e., new features for NBA 3.1):

| Domain | KEEP Codes | Already in 752 | New for 3.1 | % New |
| --- | --- | --- | --- | --- |
| Rx | 329 | 30 | 299 | 90.9% |
| Dx | 293 | 18 | 275 | 93.9% |
| Px | 127 | 20 | 107 | 84.3% |
| Lab | 20 | 19 | 1 | 5.0% |

**Insight:** NBA 3.1 is a major expansion — 682 of 769 KEEP codes (88.7%) are new features not present in the 752-feature set. The Lab domain is the exception (only 1 new test), as the core labs (eGFR, UACR, HbA1c, K) were already well-covered.

### 8.2 NBA 3.0 Coverage

| Domain | In NBA 3.0 | Match Type |
| --- | --- | --- |
| Rx | 148 (32.3%) | event_name_match |
| Dx | 414 (100%) | code_match |
| Px | 153 (100%) | code_match |
| Lab | 29 (64.4%) | code_match / event_name_match |

**Insight:** Dx and Px were fully covered in NBA 3.0 (all codes matched by code). Rx had partial coverage (32.3% by event name match) — the 180 drugs NOT in NBA 3.0 represent the biggest area of expansion. Lab had 64.4% coverage, with the 16 uncovered tests being mostly low-volume variants or unidentified codes.

---
## 9. Key Insights & Recommendations

### 9.1 Volume Concentration Validates Tiered Approach

Only 4–7% of codes in each domain account for 80% of patient volume. The long tail of low-volume codes (especially in Rx with 458 drugs) can be safely dropped without meaningful signal loss. This is exactly what the tiered decision framework achieves.

### 9.2 Oversplit ICD-10 Codes Are the Biggest Drop Category

74 of 92 Dx TIER_1_DROPS are oversplit ICD-10 sub-codes (mostly diabetic retinopathy and neuropathy variants with <10K patients each). These should be rolled up to parent codes (e.g., E11.35) to recover signal. This is a data engineering recommendation, not a clinical one — the parent code captures the same clinical meaning at higher volume.

### 9.3 Near-Universal Comorbidities Should Be Background Flags

Essential hypertension (I10, 46.5M patients) and hyperlipidemia (E78.x, 25M+ patients) are so prevalent in T2D/CKD/HF cohorts that they function as background noise rather than discriminative features. They are correctly TIER_2_DROPPED. However, they may still be useful as binary cohort flags ("has hypertension" / "has hyperlipidemia") rather than as continuous features.

### 9.4 Lab Domain Is Already Well-Covered

Unlike Rx/Dx/Px, the Lab domain is mature — only 1 new lab test is added for NBA 3.1. The core 4 tests (eGFR, UACR, HbA1c, Potassium) were already in the 752-feature set and cover the key clinical markers for Kerendia's T2D-CKD indication. The main cleanup work in Lab is data quality (17 unidentified LOINC codes with no test name).

### 9.5 Kerendia's Discriminative Value

Kerendia's prescription pattern is highly specific to the T2D+CKD intersection (85.2% T2D, 72.8% CKD). Even though its patient volume (191K) is small relative to competitors, its indication signal is strong, making it a valuable discriminative feature. The NBA model can use "provider prescribed Kerendia" as a proxy for "patient is in the T2D-CKD segment."

### 9.6 TIER_3_REVIEW Codes Need Manual Decision

51 codes (22 Rx + 13 Dx + 10 Px + 6 Lab) are flagged for manual review. These are low-volume codes with moderate indication signal — borderline cases that automated rules cannot resolve. Recommended action: review each individually with a clinical SME to determine if the signal justifies inclusion despite low volume.

---
## 10. Methodology Notes

* **Indication signal** is measured as the maximum patient percentage across T1D, T2D, HF, and CKD indications. A "strong indication signal" (max >= 75%) flags a code as discriminative.
* **Volume concentration** uses a Pareto (80/20) approach — codes are sorted by patient volume descending, and cumulative percentage is tracked. Codes within the top 80% are flagged with `in_top_80pct_volume = YES`.
* **Feature matching** against the 752-feature set uses both event name matching (Rx) and code matching (Dx, Px, Lab) to determine if a code was already included.
* **NBA 3.0 coverage** tracks whether each code was considered in the previous NBA iteration, with the match type recorded.
* **Tiered decisions** follow a hierarchy: TIER_1_DROP (hard drop, clear signal to remove) > TIER_2_DROP (soft drop, high volume but non-discriminative) > TIER_3_REVIEW (manual review needed).