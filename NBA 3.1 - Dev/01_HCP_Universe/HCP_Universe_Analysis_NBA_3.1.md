# NextGen NBA 3.1 — HCP Universe Selection Analysis

**Date:** October 9, 2026  
**Notebook Reference:** `01_HCP_Universe/01_HCP_Universe_Identification`  
**Status:** Exploratory Analysis — Transitioning from Product-Based to Indication-Based Universe

---

## 1. NBA 3.0 Baseline (Product-Based Approach)

The HCP universe for NBA 3.0 was defined using a **product-based** methodology.  
**Time frame adopted:** 2 years (May '23 to Apr '25)

### 1.1 Selection Criteria & Counts

| # | Criterion | Description | HCP Count | % of Universe |
|---|-----------|-------------|----------:|:-------------:|
| 1 | **SGLT2/GLP1 Prescribers (Decile 2+)** | All HCPs (decile 2 and above) with SGLT2/GLP1 prescriptions in the two years | 184,480 | 83.2% |
| 2 | **Kerendia Writers** | All HCPs prescribing Kerendia in complete history | 49,849 | 22.5% |
| 3 | **NEPH HCPs** | All Nephrologists | 15,209 | 6.9% |
| 4 | **Targeting & BPT HCPs** | All HCPs in BPT or Targeting List | 116,944 | 52.7% |
| | **Total HCP Universe** | Union of all criteria | **221,723** | — |

> *Overall SGLT2/GLP1 prescribing HCPs before decile filter: 648,778*  
> *Percentages represent each group's share of the total universe (221,723)*  
> *Among 117K Targeting and BPT HCPs, 93% were already captured using criteria 1 to 3 (16K explicitly added)*

---

## 2. NBA 3.1 Current Run (Product-Based, Updated Data)

Same methodology as NBA 3.0, run on refreshed data.

### 2.1 Selection Criteria & Counts

| # | Criterion | HCP Count | % of Universe |
|---|-----------|----------:|:-------------:|
| 1 | **SGLT2/GLP1 Prescribers (Decile 2+)** | 193,974 | 83.3% |
| 2 | **Kerendia Writers** (full history) | 77,972 | 33.5% |
| 3 | **NEPH HCPs** | 16,414 | 7.0% |
| 4 | **Targeting & BPT HCPs** | 78,389 | 33.6% |
| | **Total HCP Universe** | **232,965** | — |

> *Overall SGLT2/GLP1 prescribing HCPs before decile filter: 575,742*

### 2.2 NBA 3.0 → 3.1 Comparison

| Criterion | NBA 3.0 | NBA 3.1 | Delta | Notes |
|-----------|--------:|--------:|------:|-------|
| SGLT2/GLP1 (all) | 648,778 | 575,742 | -73,036 | Pool shrank but Decile 2+ grew |
| SGLT2/GLP1 (Decile 2+) | 184,480 | 193,974 | +9,494 | Higher-volume writers grew |
| Kerendia Writers | 49,849 | 77,972 | +28,123 | ~57% growth in Kerendia adoption |
| NEPH HCPs | 15,209 | 16,414 | +1,205 | Stable |
| Targeting & BPT | 116,944 | 78,389 | -38,555 | Call Plan / BPT list updated |
| **Total Universe** | **221,723** | **232,965** | **+11,242** | **+5.1% growth** |

**Key Observations:**
- Kerendia writers nearly doubled (~50K → ~78K), reflecting growing market adoption
- SGLT2/GLP1 Decile 2+ share held steady at ~83% of universe despite the total pool shrinking
- Targeting & BPT list shrank significantly — needs investigation into whether `CP_KER_HCP` source changed
- In NBA 3.1, Targeting and BPT use the identical underlying query, producing the same 78,389 HCPs

---

## 3. Paradigm Shift: Indication-Based Universe

### 3.1 Motivation

The NBA 3.0/3.1 product-based approach only captured HCPs prescribing **SGLT2/GLP1 drugs** — a proxy for treating T2D and CKD. This missed:
- HCPs treating these conditions with **other drug classes** (ACE, ARB, BB, Diuretics, sMRA, etc.)
- HCPs treating **Heart Failure (HF)** — a key Kerendia-adjacent indication
- HCPs treating **Type 1 Diabetes (T1D)** — a newly relevant population

New indication-enriched tables now allow us to **directly identify HCPs by the conditions they treat**, not just the products they prescribe.

### 3.2 Available Data Sources

All tables reside in **`ph-com-ai-us-prod-catalog-2553213839599380.pace_ker_in_house_schema`**

| Table | Rows | Patients | HCPs | Date Range | Grain |
|-------|-----:|:--------:|-----:|:----------:|-------|
| **lrx_nbrx** | 246M | — | 1,653,769 | Jul '21 – Sep '26 | Provider × Week × Product × Indication |
| **pt_lvl_nbrx** | 249M | 117.9M | 1,653,757 | Jul '21 – Sep '26 | Claim-level (NBRx only) |
| **pt_lvl_trx** | 4.8B | 152.1M | 1,972,490 | Jan '21 – Sep '26 | Claim-level (all TRx) |
| **indication_table** | 95.5M | 95.5M | — | — | Patient-level reference (1:1) |

### 3.3 Indication Classification

#### Indication Group Columns

Two indication group columns exist across the prescription tables (`lrx_nbrx`, `pt_lvl_nbrx`):

| Column | # Values | T1D Split? | Recommended? |
|--------|:--------:|:----------:|:------------:|
| `INDICATION_GROUP` | 8 | No — T1D patients lumped into T2D or OTHERS | No |
| `INDICATION_GROUP_APP1` | 16 | **Yes** — T1D separated into own combinations | **Yes** |

**`INDICATION_GROUP_APP1` values (16 combinations):**

| Pure Indications | 2-way Combinations | 3-way Combinations | 4-way |
|:-----------------|:-------------------|:-------------------|:------|
| T1D | T1D + T2D | T1D + T2D + CKD | T1D + T2D + CKD + HF |
| T2D | T1D + CKD | T1D + T2D + HF | |
| CKD | T1D + HF | T1D + CKD + HF | |
| HF | T2D + CKD | T2D + CKD + HF | |
| OTHERS | T2D + HF | | |
| | CKD + HF | | |

> **Recommendation:** Use `INDICATION_GROUP_APP1` — it provides T1D granularity essential for the 4-indication approach.

#### Three Flag Versions: ORIGINAL vs APP1 vs APP2

The `indication_table` contains three different versions of T1D/T2D flags, each using a different **T1D vs T2D disambiguation strategy**. CKD and HF flags are identical across all three versions — only T1D/T2D assignment differs.

| Version | Column Suffix | T1D Patients | T2D Patients | Dual T1D+T2D Handling |
|---------|:-------------|-------------:|-------------:|:----------------------|
| **ORIGINAL** | `_FLAG_ORIGINAL` | 3,619,864 | 68,438,026 | **No disambiguation** — both T1D and T2D can be flagged = 1 simultaneously |
| **APP1** | `_FLAG_APP1` | 2,083,252 | 67,334,183 | **Strict** — force-assigns each dual-flagged patient to either T1D **or** T2D, never both |
| **APP2** | `_FLAG_APP2` | 2,737,593 | 67,511,192 | **Moderate** — more permissive than APP1; re-adds T1D for some patients APP1 had resolved to T2D-only |

Corresponding indication columns: `INDICATION_ORIGINAL`, `INDICATION_APP1`, `INDICATION_APP2`

**How the disambiguation flows (patient counts):**

```
  ORIGINAL (raw flags)          APP1 (strict)              APP2 (moderate)
  ┌───────────────────┐        ┌──────────────────┐       ┌──────────────────┐
  │ T1D+T2D: 1,536,612│───────▶│ Resolved to T2D  │──────▶│ 654K re-added    │
  │ patients (both=1) │        │ only: 882,271    │       │ back as T1D+T2D  │
  │                   │        │                  │       │                  │
  │                   │        │ Resolved to T1D  │       │ 177K re-added    │
  │                   │        │ only: rest       │       │ back as T1D+T2D  │
  └───────────────────┘        └──────────────────┘       └──────────────────┘
```

**Top ORIGINAL → APP1 reclassifications (2.6M patients affected):**

| ORIGINAL Label | APP1 Label | Patients | Change |
|:---------------|:-----------|:--------:|:-------|
| T1D + T2D | T1D | 586,006 | Kept as T1D, dropped T2D |
| T1D + T2D | T2D | 518,993 | Kept as T2D, dropped T1D |
| T1D + T2D + CKD | T2D + CKD | 470,016 | Dropped T1D |
| T1D + T2D + CKD + HF | T2D + CKD + HF | 444,789 | Dropped T1D |
| T1D + T2D + CKD | T1D + CKD | 291,065 | Dropped T2D |
| T1D + T2D + CKD + HF | T1D + CKD + HF | 185,276 | Dropped T2D |
| T1D + T2D + HF | T2D + HF | 102,814 | Dropped T1D |
| T1D + T2D + HF | T1D + HF | 41,496 | Dropped T2D |

**Top APP1 → APP2 relaxations (831K patients affected):**

| APP1 Label | APP2 Label | Patients | Change |
|:-----------|:-----------|:--------:|:-------|
| T2D + CKD + HF | T1D + T2D + CKD + HF | 210,395 | T1D re-added |
| T2D | T1D + T2D | 206,328 | T1D re-added |
| T2D + CKD | T1D + T2D + CKD | 189,614 | T1D re-added |
| T1D | T1D + T2D | 97,385 | T2D re-added |
| T2D + HF | T1D + T2D + HF | 48,004 | T1D re-added |
| T1D + CKD | T1D + T2D + CKD | 43,972 | T2D re-added |
| T1D + CKD + HF | T1D + T2D + CKD + HF | 26,652 | T2D re-added |
| T1D + HF | T1D + T2D + HF | 9,000 | T2D re-added |

> **Note:** The disambiguation likely uses `LATEST_ENDO_DX`, `T1D_DRUG_FLAG`, and `T2D_DRUG_FLAG` columns in the `indication_table`, but the source notebook that builds this table was not found in this workspace — it is likely maintained by the PACE team externally.

### 3.4 Indication Assignment Methods (indication_table)

The `indication_table` columns suggest multiple approaches are used to assign disease flags per patient. **These methods are inferred from column naming patterns** (e.g., `T1D_DX_MIN_DATE` → DX approach, `CKD_LAB_MIN_DATE` → Lab approach). The source notebook for this table was not found in the workspace.

| Approach | Inferred From Column | T1D/T2D | CKD | HF |
|----------|:--------------------|:-------:|:---:|:--:|
| **DX** | `*_DX_MIN_DATE` | ✓ | ✓ | ✓ |
| **Proxy** | `*_PROXY_MIN_DATE` | ✓ | ✓ | ✓ |
| **Lab** | `CKD_LAB_MIN_DATE` | — | ✓ | — |
| **DX + Proxy** | `CKD_DX_PROXY_MIN_DATE` | — | ✓ | — |
| **Drug Flag** | `T1D_DRUG_FLAG`, `T2D_DRUG_FLAG` | ✓ | — | — |
| **Kerendia Proxy** | `HF_KER_PROXY_MIN_DATE` | — | — | ✓ |
| **Combined** | `*_MIN_DATE` | ✓ | ✓ | ✓ |

> **Caveat:** The exact logic behind each approach (DX codes used, proxy rules, lab thresholds) is unknown without the source pipeline. The `*_MIN_DATE` columns represent the earliest date across all approaches for that indication.

**Patient-Level Indication Prevalence (indication_table, 95.5M patients):**

| Indication | ORIGINAL | APP1 | APP2 |
|:-----------|:--------:|:----:|:----:|
| T2D | 68,438,026 (71.6%) | 67,334,183 (70.5%) | 67,511,192 (70.7%) |
| CKD | 41,965,784 (43.9%) | 41,965,784 (43.9%) | 41,965,784 (43.9%) |
| HF | 21,213,328 (22.2%) | 21,213,328 (22.2%) | 21,213,328 (22.2%) |
| T1D | 3,619,864 (3.8%) | 2,083,252 (2.2%) | 2,737,593 (2.9%) |

> CKD and HF counts are identical across all three versions — only T1D/T2D assignment varies.

---

## 4. Indication-Based EDA Results

**Analysis Window:** 2 years (Oct '24 – Sep '26)  
**Source Table:** `lrx_nbrx` using `INDICATION_GROUP_APP1`

### 4.1 HCPs by Indication Group

| Indication Group | Distinct HCPs | Total NBRx |
|:-----------------|:-------------:|-----------:|
| OTHERS | 1,240,418 | 43,710,195 |
| T2D | 945,932 | 30,564,757 |
| T2D + CKD | 601,309 | 8,820,152 |
| CKD | 592,302 | 5,084,919 |
| T2D + CKD + HF | 499,086 | 5,039,783 |
| HF | 482,267 | 3,906,317 |
| T2D + HF | 459,771 | 3,297,644 |
| CKD + HF | 393,347 | 2,399,532 |
| T1D | 184,079 | 458,065 |
| T1D + CKD | 97,326 | 177,527 |
| T1D + CKD + HF | 64,764 | 104,205 |
| T1D + HF | 25,216 | 36,879 |
| T1D + T2D | 14,466 | 21,695 |
| T1D + T2D + CKD | 5,667 | 7,712 |
| T1D + T2D + CKD + HF | 2,339 | 3,023 |
| T1D + T2D + HF | 1,610 | 2,235 |

### 4.2 HCPs Treating Each Target Indication (Any Combination)

| Indication | HCPs | % of All HCPs in Table (1.35M) |
|:-----------|------:|:------------------------------:|
| **T2D** | 1,019,894 | 75.3% |
| **CKD** | 799,068 | 59.0% |
| **HF** | 696,373 | 51.5% |
| **T1D** | 280,902 | 20.8% |
| **Union (any T1D/T2D/CKD/HF)** | **1,078,405** | **79.7%** |
| OTHERS only | 275,042 | 20.3% |

### 4.3 Cross-Indication Overlap Among HCPs

| Overlap | HCP Count |
|:--------|----------:|
| T2D ∩ CKD | 760,527 |
| T2D ∩ HF | 667,553 |
| CKD ∩ HF | 639,342 |
| **T2D ∩ CKD ∩ HF** | **626,632** |

> 626K HCPs treat patients across all three of T2D + CKD + HF — the core Kerendia-relevant population. This represents 58% of all indication-tagged HCPs.

### 4.4 Top Drug Classes by Indication

All counts below use `INDICATION_GROUP_APP1` containing the target indication (i.e., any combination that includes it).

#### T2D — HCPs treating Type 2 Diabetes (1,019,894 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| OTHERS | 792,935 | 11,906,348 |
| BB | 636,037 | 4,798,549 |
| DIURETICS | 599,910 | 4,573,101 |
| ARB | 510,180 | 4,600,873 |
| ACE | 476,577 | 3,005,568 |
| SGLT2 | 452,092 | 5,452,303 |
| GLP1 | 423,012 | 11,013,109 |
| sMRA | 406,922 | 1,730,846 |
| ENTRESTO GENERICS | 101,538 | 267,553 |
| ENTRESTO BRAND | 95,402 | 238,346 |
| **KERENDIA** | **35,798** | **165,152** |

> GLP1 dominates T2D by NBRx volume (11M) despite fewer HCPs than OTHERS/BB. SGLT2 is 6th by HCPs but 2nd by NBRx.

#### CKD — HCPs treating Chronic Kidney Disease (799,068 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| OTHERS | 536,107 | 3,649,164 |
| DIURETICS | 519,141 | 3,357,323 |
| BB | 501,849 | 3,054,186 |
| ARB | 421,848 | 2,660,187 |
| SGLT2 | 367,694 | 2,626,538 |
| ACE | 353,667 | 1,316,686 |
| GLP1 | 317,089 | 3,275,411 |
| sMRA | 303,004 | 1,129,944 |
| ENTRESTO GENERICS | 90,422 | 228,433 |
| ENTRESTO BRAND | 83,123 | 193,513 |
| **KERENDIA** | **32,569** | **140,978** |

> CKD prescribing is more evenly distributed across drug classes than T2D. Diuretics and BB are dominant — these HCP pools were entirely missed by the old SGLT2/GLP1-only approach.

#### HF — HCPs treating Heart Failure (696,373 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| DIURETICS | 479,967 | 2,719,310 |
| BB | 430,402 | 2,343,685 |
| OTHERS | 421,827 | 1,698,413 |
| SGLT2 | 352,337 | 1,956,064 |
| ARB | 342,229 | 1,381,583 |
| sMRA | 311,058 | 1,494,008 |
| GLP1 | 266,972 | 1,430,758 |
| ACE | 252,242 | 592,751 |
| ENTRESTO GENERICS | 153,255 | 589,057 |
| ENTRESTO BRAND | 143,401 | 517,959 |
| **KERENDIA** | **21,071** | **64,274** |

> HF is dominated by Diuretics and BB — classic heart failure drug classes. SGLT2 is already 4th (352K HCPs), showing the overlap between HF and metabolic prescribing. Entresto (brand + generics) together reach ~154K HCPs — a distinctly HF-focused drug class. sMRA writers (311K) represent a Kerendia-adjacent competitive pool.

#### T1D — HCPs treating Type 1 Diabetes (280,902 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| OTHERS | 106,886 | 245,179 |
| BB | 90,926 | 115,719 |
| DIURETICS | 76,017 | 94,964 |
| ARB | 70,967 | 94,879 |
| ACE | 59,750 | 80,848 |
| GLP1 | 40,953 | 104,484 |
| sMRA | 29,850 | 34,851 |
| SGLT2 | 21,909 | 28,459 |
| ENTRESTO GENERICS | 4,253 | 4,516 |
| ENTRESTO BRAND | 3,787 | 3,989 |
| **KERENDIA** | **2,681** | **3,356** |

> T1D is the smallest pool. BB, DIURETICS, and ARB dominate — these are likely managing comorbid hypertension/cardiovascular risk in T1D patients. GLP1 appears for 41K HCPs despite not being a traditional T1D drug, reflecting off-label or dual-diagnosis use. SGLT2 and KERENDIA are minimal.

#### Key Insight Across All Indications

> The old product-based approach (SGLT2 + GLP1 only) captured at most **452K T2D HCPs** and **352K HF HCPs** via those two drug classes. The indication-based approach reveals that **BB, Diuretics, ARB, ACE, and sMRA** each contribute 250K–640K HCPs per indication — large populations entirely invisible to the product-based filter.

### 4.5 Kerendia Writer Indication Profile

**Total Kerendia NBRx writers in 2-year window: 39,704**

| Indication Group | HCPs | NBRx | % of Kerendia Writers |
|:-----------------|-----:|-----:|:---------------------:|
| T2D + CKD | 22,586 | 82,412 | 56.9% |
| T2D + CKD + HF | 16,789 | 43,722 | 42.3% |
| T2D | 13,583 | 30,800 | 34.2% |
| OTHERS | 4,703 | 7,386 | 11.8% |
| T2D + HF | 4,678 | 8,103 | 11.8% |
| CKD | 4,015 | 6,224 | 10.1% |
| CKD + HF | 3,523 | 5,940 | 8.9% |
| HF | 2,836 | 5,607 | 7.1% |
| T1D + CKD | 1,556 | 1,837 | 3.9% |
| T1D + CKD + HF | 717 | 773 | 1.8% |
| T1D | 456 | 520 | 1.1% |
| T1D + HF | 107 | 111 | 0.3% |

> **99.9%** of Kerendia writers (39,657 of 39,704) are captured by the indication-based approach.  
> Only **47** Kerendia writers fall exclusively in OTHERS.

### 4.6 Specialty-Based HCP Analysis

The original notebook only included **Nephrologists (NEPH)** via a complex Provider Dimension → NPI → MDM → Specialty mapping chain. The `lrx_nbrx` table already has a `SPECIALTY_GROUP` column, enabling direct specialty identification — and expanding to additional relevant specialties.

#### All Specialty Groups in `lrx_nbrx`

| Specialty | Code | HCPs | Total NBRx | Kerendia Writers | Kerendia % |
|:----------|:-----|------:|-----------:|-----------------:|:----------:|
| Primary Care Physicians | `PCP` | 721,427 | 77,479,461 | 24,053 | 3.3% |
| Other Specialties | `OTHERS` | 543,876 | 7,879,141 | — | — |
| Cardiologists | `CARD` | 51,622 | 12,279,727 | 5,102 | 9.9% |
| Nephrologists | `NEPH` | 15,035 | 2,087,334 | 7,479 | 49.7% |
| Endocrinologists | `ENDO` | 13,360 | 3,584,796 | 2,593 | 19.4% |
| Hospitalists | `HOSPITALIST` | 7,395 | 147,114 | 1 | 0.0% |
| Hospital-based Specialists | `HOS` | 731 | 177,067 | 386 | 52.8% |

> `HOS` and `HOSPITALIST` have **zero provider overlap** — they are entirely distinct populations. `HOS` (731 HCPs) has the highest Kerendia writing rate (52.8%), suggesting hospital-based subspecialists.

#### Indication Coverage by Specialty

| Specialty | HCPs | % treating T2D | % treating CKD | % treating HF | % treating T1D |
|:----------|------:|:--------------:|:--------------:|:-------------:|:--------------:|
| **NEPH** | 15,035 | 95.2% | 95.3% | 91.0% | 66.3% |
| **CARD** | 51,622 | 94.5% | 92.3% | 92.7% | 50.0% |
| **ENDO** | 13,360 | 96.0% | 91.7% | 87.3% | 81.5% |
| **PCP** | 721,427 | 87.8% | 75.5% | 68.4% | 27.9% |
| **HOSPITALIST** | 7,395 | 72.9% | 61.7% | 60.4% | 14.5% |
| **HOS** | 731 | 99.2% | 98.6% | 97.7% | 64.7% |

**Key observations:**
- **NEPH, CARD, ENDO** are highly concentrated in all 4 indications (87–96%)
- **PCP** is the largest pool by far (721K) with broad but shallower indication coverage
- **ENDO** has the highest T1D involvement (81.5%) — naturally, as endocrinologists manage diabetes
- **CARD** has the highest HF involvement (92.7%) and is 3.4× larger than NEPH
- **HOSPITALIST** has the lowest indication coverage (~60–73%) and almost no Kerendia writing

#### Overlap with Indication-Based Criterion 1

How many of these specialty HCPs are **already captured** by the indication criterion (`INDICATION_GROUP_APP1 != 'OTHERS'`)?

| Specialty | Total HCPs | Already in Indication Set | Net New Adds | % Already Captured |
|:----------|:----------:|:-------------------------:|:------------:|:------------------:|
| **NEPH** | 15,035 | 14,612 | 423 | 97.2% |
| **CARD** | 51,622 | 49,907 | 1,715 | 96.7% |
| **ENDO** | 13,360 | 13,001 | 359 | 97.3% |
| **PCP** | 721,427 | 654,997 | 66,430 | 90.8% |
| **HOSPITALIST** | 7,395 | 6,054 | 1,341 | 81.9% |
| **Combined** | **808,839** | **738,571** | **70,268** | **91.3%** |

> **91.3%** of target specialty HCPs are already in the indication set. The specialty criterion would explicitly add **70,268 net new HCPs** — mostly PCPs (66K) who prescribe only for OTHERS indications but are clinically relevant by virtue of their specialty.

#### Simplification Opportunity

The original notebook derived specialty via a 4-table join chain:
```
STG_CAR_IQV_LAAD_DIM_PRVDR → NPI XREF → MAP_CUSTOMER_XREF → MDM_STG_HCP_PRFL → specialty CSV
```

Since `lrx_nbrx` already has `SPECIALTY_GROUP` at the provider level, the new pipeline can source specialty **directly** — eliminating the complex mapping chain entirely.

---

## 5. Product-Based vs. Indication-Based Comparison

### 5.1 Head-to-Head (Criterion 1 Only)

| Metric | Product-Based (SGLT2/GLP1) | Indication-Based (T1D/T2D/CKD/HF) |
|:-------|---------------------------:|-----------------------------------:|
| Total HCPs in scope | 604,603 | 1,078,405 |
| Overlap | 597,054 | 597,054 |
| Unique to this approach | 7,549 | 481,351 |
| Kerendia writer coverage | — | 99.9% |

```
                Product-Based           Indication-Based
                ┌──────────┐            ┌──────────────────────┐
                │          │            │                      │
                │  7,549   │  597,054   │      481,351         │
                │  (only   │  (overlap) │      (new HCPs       │
                │  SGLT2/  │            │      from ACE, ARB,  │
                │  GLP1)   │            │      BB, Diuretics,  │
                │          │            │      sMRA, etc.)      │
                └──────────┘            └──────────────────────┘
                  604,603                    1,078,405
```

**Key Insight:** The indication-based approach captures **98.8%** of the old SGLT2/GLP1 HCPs while adding **481K new HCPs** who treat T1D/T2D/CKD/HF with non-SGLT2/GLP1 drug classes. The 7,549 SGLT2/GLP1 HCPs not in the indication set are those whose patients have only "OTHERS" indications.

### 5.2 Recommended Table for Universe Building

| Purpose | Recommended Table | Why |
|:--------|:------------------|:----|
| **HCP identification (Criterion 1)** | `lrx_nbrx` | Already at Provider × Indication grain; most efficient for HCP-level aggregation |
| **Decile calculation** | `lrx_nbrx` | Sum NBRX per PROVIDER_ID for TRx-based deciling |
| **Patient-level deep dives** | `pt_lvl_trx` | 4.8B rows with disease flags for granular patient analysis |
| **Indication reference/enrichment** | `indication_table` | Gold-standard patient→indication mapping with diagnosis dates |
| **NBRx-specific analysis** | `pt_lvl_nbrx` | Claim-level new-to-brand data with indication |

---

## 6. Proposed NBA 3.1 Updated HCP Universe

### 6.1 New Selection Criteria

| # | Criterion | Source | Description |
|---|-----------|--------|-------------|
| 1 | **Indication-Based HCPs (Decile 2+)** | `lrx_nbrx` | All HCPs prescribing to T1D/T2D/CKD/HF patients (`INDICATION_GROUP_APP1 != 'OTHERS'`), decile 2 and above by total NBRx |
| 2 | **Kerendia Writers** | `lrx_nbrx` | All HCPs prescribing Kerendia (`PRODUCT_CLASS = 'KERENDIA'`) in complete history |
| 3 | **Specialty HCPs** | `lrx_nbrx` (`SPECIALTY_GROUP`) | All NEPH, CARD, ENDO, PCP, and HOSPITALIST HCPs — expanded from NEPH-only; sourced directly from `lrx_nbrx` instead of the MDM chain |
| 4 | **Targeting & BPT HCPs** | `CP_KER_HCP` | All HCPs in BPT or Targeting List (unchanged) |

### 6.2 Enhanced Output Schema

The new universe output should include **indication-level flags** per HCP:

| Column | Type | Description |
|:-------|:-----|:------------|
| `PROVIDER_ID` | string | Unique HCP identifier |
| `T1D_FLAG` | int | 1 if HCP treats T1D patients |
| `T2D_FLAG` | int | 1 if HCP treats T2D patients |
| `CKD_FLAG` | int | 1 if HCP treats CKD patients |
| `HF_FLAG` | int | 1 if HCP treats HF patients |
| `KERENDIA_FLAG` | int | 1 if HCP prescribes Kerendia |
| `NEPH_FLAG` | int | 1 if HCP is a Nephrologist |
| `CARD_FLAG` | int | 1 if HCP is a Cardiologist |
| `ENDO_FLAG` | int | 1 if HCP is an Endocrinologist |
| `PCP_FLAG` | int | 1 if HCP is a Primary Care Physician |
| `HOSPITALIST_FLAG` | int | 1 if HCP is a Hospitalist |
| `TARGETING_HCP_FLAG` | int | 1 if HCP is in Targeting list |
| `BPT_HCP_FLAG` | int | 1 if HCP is in BPT list |
| `INDICATION_DECILE` | int | NBRx-based decile rank (1–10) |
| `PULL_DT` | date | Data pull date |

### 6.3 Expected Impact

| | NBA 3.0 | NBA 3.1 (Product) | NBA 3.1 (Indication) |
|:--|--------:|------------------:|---------------------:|
| Criterion 1 scope | SGLT2/GLP1 only | SGLT2/GLP1 only | All drug classes for T1D/T2D/CKD/HF |
| Criterion 1 pre-decile | 648,778 | 575,742 | ~1,078,405 |
| Kerendia writer coverage | ✓ | ✓ | ✓ (99.9%) |
| Indications covered | T2D, CKD (implicit) | T2D, CKD (implicit) | **T1D, T2D, CKD, HF (explicit)** |
| Per-HCP indication flags | No | No | **Yes** |

> **Note:** Final universe size will depend on the decile cutoff applied. The indication-based Criterion 1 pool (~1.08M) is ~1.9× larger than the product-based pool (~576K), so the total universe will grow significantly.

---

## 7. Next Steps

- [ ] Confirm lookback window for NBA 3.1 (2 years ending when?)
- [ ] Decide on decile methodology: per-indication deciles or combined NBRx decile?
- [ ] Confirm whether to keep `INDICATION_GROUP_APP1` (with T1D) vs `INDICATION_GROUP` (without T1D)
- [x] ~~Expand Criterion 3 from NEPH-only to NEPH + CARD + ENDO + PCP + HOSPITALIST~~ — **Done** (see Section 4.6)
- [ ] Decide whether to include `HOS` (731 HCPs, 52.8% Kerendia writers) alongside HOSPITALIST
- [ ] Build the updated `01_HCP_Universe_Identification` notebook
- [ ] Validate new universe against Kerendia writer and Targeting list coverage

---

*Generated by Genie Code — October 9, 2026*