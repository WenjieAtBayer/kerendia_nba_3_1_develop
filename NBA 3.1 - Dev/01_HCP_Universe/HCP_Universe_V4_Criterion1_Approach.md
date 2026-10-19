# NBA 3.1 v4 — Criterion 1 Approach

**Date:** October 14, 2026

---

## Overview

Criterion 1 identifies HCPs through **indication-specific, drug-pool-level deciling** — a hybrid of the indication-based (v2) and product-class (v3) approaches.

---

## Step 1: Decile Grid (4 Indications × 2 Drug Pools)

For each indication × drug pool combination, independently:
1. Filter `lrx_nbrx` claims where `INDICATION_GROUP_APP1` contains the indication AND `PRODUCT_CLASS` is in the pool
2. Sum NBRX per HCP
3. Apply cumulative volume-based decile (each decile ≈ 10% of total NBRX volume)
4. Keep Decile N+ (cutoff varies by scenario)

| | SGLT2 + GLP1 | ACE + ARB |
|---|---|---|
| **T2D** | Set 1 | Set 2 |
| **CKD** | Set 3 | Set 4 |
| **HF** | Set 5 | Set 6 |
| **T1D** | Set 7 | Set 8 |

> **sMRA is excluded** from the drug pools.

## Step 2: Combine

```
Criterion 1 = (Set 1 ∩ Set 2 ∩ Set 3 ∩ Set 4) ∪ Set 5 ∪ Set 6 ∪ Set 7 ∪ Set 8
```

**In plain language:**
* **Core** = HCPs who are high-volume prescribers of BOTH SGLT2/GLP1 AND ACE/ARB for BOTH T2D AND CKD patients (4-way intersection)
* **Plus** all HF prescribers (SGLT2/GLP1 or ACE/ARB) at the decile threshold
* **Plus** all T1D prescribers (SGLT2/GLP1 or ACE/ARB) at the decile threshold

## Step 3: Results by Decile Cutoff

| | D2+ | D3+ | D4+ |
|:--|------:|------:|------:|
| **Core** (T2D∩CKD, both pools) | 144,371 | 84,396 | 51,659 |
| HF (both pools, union) | 304,479 | 213,977 | 156,493 |
| T1D (both pools, union) | 120,232 | 94,734 | 70,608 |
| **Criterion 1 Total** | **337,591** | **251,288** | **188,435** |
| Core-only (exclusive to core) | 8,931 | 8,162 | 7,114 |
| Core overlap with HF/T1D | 93.8% | 90.3% | 86.2% |

---

## Finalised Cutoff: D3+ (251,288 HCPs)

D3+ was selected as the optimal cutoff — D2+ is too broad (338K), D4+ too aggressive (188K, collapses the core by 64%).

---

## Step 4: Specialty Distribution (D3+)

| Specialty | HCPs | % of Universe |
|:----------|------:|:-------------:|
| PCP | 192,418 | 76.6% |
| CARD | 33,770 | 13.4% |
| ENDO | 9,895 | 3.9% |
| NEPH | 9,333 | 3.7% |
| OTHERS | 4,746 | 1.9% |
| HOSPITALIST | 583 | 0.2% |
| HOS | 543 | 0.2% |

**Specialty by Component:**

| Specialty | Core-only (8,162) | HF/T1D-only (166,892) | Overlap (76,234) |
|:----------|:-----------------:|:---------------------:|:----------------:|
| PCP | 99.3% | 69.6% | 89.3% |
| CARD | 0.2% | 18.2% | 4.4% |
| NEPH | 0.2% | 4.0% | 3.4% |
| ENDO | 0.1% | 4.7% | 2.7% |

> **Insight:** Target specialties (PCP + CARD + ENDO + NEPH) account for **97.7%** of the universe — the indication-based criterion inherently captures specialty-relevant HCPs without an explicit specialty filter. The core-only 8K are almost entirely PCPs (99.3%), while the HF/T1D component brings in the most specialists (CARD 18.2%).

---

## Step 5: Indication Distribution (D3+)

| Indication | HCPs | % of Universe |
|:-----------|------:|:-------------:|
| T2D | 250,592 | 99.7% |
| CKD | 249,847 | 99.4% |
| HF | 248,228 | 98.8% |
| T1D | 178,523 | 71.0% |

> **Insight:** Near-universal T2D/CKD/HF coverage — virtually every HCP in the universe has claims across all three primary indications. T1D separates at 71%, confirming it as a distinct sub-population. Zero HCPs are "indication-free", validating that the criterion captures only indication-relevant prescribers.

---

## Step 6: Top Drugs (PRODUCT_CLASS) Per Indication

### T2D (250,592 HCPs — 36.4M total NBRX)

| PRODUCT_CLASS | NBRX | % NBRX | HCPs | % HCPs |
|:--------------|--------:|:------:|------:|:------:|
| GLP1 | 8,984,466 | 24.7% | 190,409 | 76.0% |
| OTHERS | 7,980,785 | 21.9% | 245,386 | 97.9% |
| SGLT2 | 4,639,068 | 12.8% | 234,879 | 93.7% |
| ARB | 3,687,100 | 10.1% | 239,123 | 95.4% |
| BB | 3,563,372 | 9.8% | 237,878 | 94.9% |
| DIURETICS | 3,431,064 | 9.4% | 238,661 | 95.2% |
| ACE | 2,229,751 | 6.1% | 226,559 | 90.4% |
| sMRA | 1,243,008 | 3.4% | 204,953 | 81.8% |
| ENTRESTO GEN | 240,509 | 0.7% | 76,544 | 30.5% |
| ENTRESTO BRAND | 209,724 | 0.6% | 71,836 | 28.7% |
| KERENDIA | 157,233 | 0.4% | 30,503 | 12.2% |

> **Insight:** T2D is **GLP1-dominant** (24.7% of NBRX). SGLT2 is third (12.8%) but reaches 93.7% of HCPs — high breadth, lower concentration. Kerendia reaches 12.2% of T2D HCPs (30.5K writers).

### CKD (249,847 HCPs — 18.0M total NBRX)

| PRODUCT_CLASS | NBRX | % NBRX | HCPs | % HCPs |
|:--------------|--------:|:------:|------:|:------:|
| OTHERS | 2,896,482 | 16.1% | 238,885 | 95.6% |
| GLP1 | 2,859,992 | 15.9% | 176,653 | 70.7% |
| DIURETICS | 2,635,878 | 14.7% | 231,820 | 92.8% |
| BB | 2,436,139 | 13.6% | 228,444 | 91.4% |
| SGLT2 | 2,348,644 | 13.1% | 222,324 | 89.0% |
| ARB | 2,264,934 | 12.6% | 230,681 | 92.3% |
| ACE | 1,062,596 | 5.9% | 205,818 | 82.4% |
| sMRA | 930,530 | 5.2% | 177,581 | 71.1% |
| ENTRESTO GEN | 206,746 | 1.2% | 69,860 | 28.0% |
| ENTRESTO BRAND | 170,933 | 1.0% | 64,082 | 25.6% |
| KERENDIA | 135,167 | 0.8% | 28,249 | 11.3% |

> **Insight:** CKD is the **most balanced** indication — no single class exceeds 16%. The top 6 classes are tightly packed (12–16%), reflecting multi-class polypharmacy in CKD management. Kerendia reaches 11.3% (28.2K writers).

### HF (248,228 HCPs — 12.4M total NBRX)

| PRODUCT_CLASS | NBRX | % NBRX | HCPs | % HCPs |
|:--------------|--------:|:------:|------:|:------:|
| DIURETICS | 2,130,585 | 17.1% | 223,325 | 90.0% |
| BB | 1,898,380 | 15.3% | 214,187 | 86.3% |
| SGLT2 | 1,741,165 | 14.0% | 215,198 | 86.7% |
| OTHERS | 1,365,728 | 11.0% | 225,960 | 91.0% |
| GLP1 | 1,268,856 | 10.2% | 168,339 | 67.8% |
| sMRA | 1,263,392 | 10.2% | 176,289 | 71.0% |
| ARB | 1,217,306 | 9.8% | 211,655 | 85.3% |
| ENTRESTO GEN | 523,838 | 4.2% | 103,933 | 41.9% |
| ACE | 499,721 | 4.0% | 170,403 | 68.6% |
| ENTRESTO BRAND | 453,762 | 3.7% | 98,383 | 39.6% |
| KERENDIA | 62,737 | 0.5% | 19,235 | 7.7% |

> **Insight:** HF follows GDMT guidelines — DIURETICS/BB/SGLT2 lead. sMRA is notably higher here (10.2%) vs T2D (3.4%) and CKD (5.2%), confirming sMRA's HF skew. Entresto (brand + generic) reaches ~42% of HF HCPs. Kerendia is at 7.7% (19.2K).

### T1D (178,523 HCPs — 664K total NBRX)

| PRODUCT_CLASS | NBRX | % NBRX | HCPs | % HCPs |
|:--------------|--------:|:------:|------:|:------:|
| OTHERS | 187,993 | 28.3% | 69,127 | 38.7% |
| GLP1 | 99,547 | 15.0% | 35,063 | 19.6% |
| ARB | 89,612 | 13.5% | 65,333 | 36.6% |
| BB | 81,176 | 12.2% | 59,714 | 33.4% |
| ACE | 74,835 | 11.3% | 53,408 | 29.9% |
| DIURETICS | 71,319 | 10.7% | 54,066 | 30.3% |
| SGLT2 | 26,582 | 4.0% | 19,876 | 11.1% |
| sMRA | 22,541 | 3.4% | 19,190 | 10.7% |
| KERENDIA | 3,216 | 0.5% | 2,537 | 1.4% |

> **Insight:** T1D is the **smallest and most distinct** indication (664K NBRX vs 36M for T2D). OTHERS dominates (28.3%). SGLT2 and sMRA are low (4.0%, 3.4%), consistent with limited use in T1D. Only 1.4% are Kerendia writers.

---

## Summary of Key Insights

1. **D3+ delivers 251K HCPs** — a focused universe between D2+ (338K) and D4+ (188K)
2. **97.7% are target specialties** (PCP 77%, CARD 13%, ENDO 4%, NEPH 4%) — no explicit specialty filter needed
3. **99%+ have T2D, CKD, and HF claims** — the criterion inherently selects multi-indication prescribers
4. **T1D separates at 71%** — a meaningful sub-segment, not universally overlapping
5. **GLP1 leads T2D by NBRX volume** (24.7%); CKD is the most balanced; HF follows GDMT guidelines
6. **sMRA has a clear HF skew** (10.2% of HF NBRX vs 3–5% elsewhere) — supports the decision to exclude sMRA from the drug pool criterion
7. **Kerendia reaches 12% of T2D, 11% of CKD, 8% of HF, 1.4% of T1D HCPs** — significant room for growth across all indications
8. **The core (84K) is 90% subsumed by HF/T1D** — only 8K exclusive HCPs, mostly PCPs (99.3%)

---

## Rationale

* **T2D & CKD are intersected** because they are the primary Kerendia indications — we want HCPs who are active prescribers in BOTH conditions across BOTH drug pools (high-confidence core)
* **HF & T1D are unioned** because they are secondary/adjacent indications — broader capture ensures we don't miss HF/T1D-focused specialists
* **sMRA excluded** from the drug pools to avoid double-counting Kerendia's own competitive class in the selection criterion
* **Cumulative volume decile** matches v1/NBA 3.0 methodology (each decile ≈ 10% of total NBRX volume, not equal HCP count)

---

*Generated by Genie Code — October 14, 2026*