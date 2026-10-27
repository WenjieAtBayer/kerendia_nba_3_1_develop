# NextGen NBA 3.1 — v4 Indication × Drug-Pool Decile Analysis

**Date:** October 14, 2026  
**Notebook:** `04_HCP_Universe_v4_Indication_DrugPool_Analysis`  
**Source:** `lrx_nbrx` — `INDICATION_GROUP_APP1` (claim-level indication) × `PRODUCT_CLASS`  
**Metric:** `sum(NBRX)` per PROVIDER_ID within each indication × drug pool  
**Decile Method:** Cumulative volume-based (each decile ≈ 10% of total NBRX volume)  
**Lookback Window:** Oct ’24 – Sep ’26  

> **Note:** `INDICATION_GROUP_APP1` contains compound values (e.g., "T2D + CKD", "T1D + T2D + HF"). We use `contains()` matching, so a T2D filter captures claims coded as "T2D", "T2D + CKD", "T2D + HF", etc. A single claim can thus appear in multiple indication groups.

---

## Overview Diagram

> **📊 Diagram:** [hcp_universe_v4.svg](./hcp_universe_v4.svg) *(open in a separate tab to view the v4 design schematic)*

---

## 1. Design: 4 Indications × 3 Drug Pools = 12 Decile Sets

| | SGLT2 + GLP1 (pooled) | ACE + ARB (pooled) | sMRA |
|---|---|---|---|
| **T2D** | Decile 1 | Decile 2 | Decile 3 |
| **CKD** | Decile 4 | Decile 5 | Decile 6 |
| **HF** | Decile 7 | Decile 8 | Decile 9 |
| **T1D** | Decile 10 | Decile 11 | Decile 12 |

For each cell: filter `lrx_nbrx` to rows where `INDICATION_GROUP_APP1` contains the indication AND `PRODUCT_CLASS` is in the drug pool, sum NBRX per HCP, apply cumulative volume decile, keep Decile 2+.

---

## 2. Results: All 12 Decile Sets

### 2.1 Decile 2+ HCP Counts

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|----------:|--------:|-----:|
| **T2D** | **210,872** | **281,207** | **246,217** |
| **CKD** | **205,248** | **253,771** | **190,489** |
| **HF** | **228,342** | **242,195** | **171,857** |
| **T1D** | **42,885** | **97,185** | **26,543** |

### 2.2 Total HCPs Per Combination (before decile filter)

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|----------:|--------:|-----:|
| T2D | 553,251 | 603,913 | 408,786 |
| CKD | 449,230 | 494,874 | 304,670 |
| HF | 430,659 | 409,457 | 312,648 |
| T1D | 56,350 | 114,916 | 30,056 |

### 2.3 D1 Drop Rate

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|:---------:|:------:|:---:|
| T2D | 61.9% | 53.4% | 39.8% |
| CKD | 54.3% | 48.7% | 37.5% |
| HF | 47.0% | 40.8% | 45.0% |
| T1D | 23.9% | 15.4% | 11.7% |

> **Observations:**
> * T2D × SGLT2/GLP1 is the most aggressive filter (61.9% dropped to D1) — many low-volume SGLT2/GLP1 prescribers in T2D
> * T1D has the lowest D1 rates (12–24%) — small prescriber pools where most HCPs have meaningful volume
> * ACE/ARB consistently has the largest total HCP pools
> * HF and CKD have more balanced D1 rates across drug pools (37–55%)

---

## 3. Cross-Indication Overlap (D2+ HCPs, Per Drug Pool)

For each drug pool: how much overlap exists between indications?

### 3.1 SGLT2/GLP1

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 173,252 | 84.4% |
| T2D ∩ HF | 156,303 | 74.1% |
| T2D ∩ T1D | 35,554 | 82.9% |
| CKD ∩ HF | 168,125 | 81.9% |
| CKD ∩ T1D | 34,595 | 80.7% |
| HF ∩ T1D | 33,838 | 78.9% |

### 3.2 ACE/ARB

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 223,831 | 88.2% |
| T2D ∩ HF | 186,296 | 76.9% |
| T2D ∩ T1D | 77,095 | 79.3% |
| CKD ∩ HF | 187,982 | 77.6% |
| CKD ∩ T1D | 73,201 | 75.3% |
| HF ∩ T1D | 64,926 | 66.8% |

### 3.3 sMRA

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 154,748 | 81.2% |
| T2D ∩ HF | 139,782 | 81.3% |
| T2D ∩ T1D | 21,095 | 79.5% |
| CKD ∩ HF | 131,325 | 76.4% |
| CKD ∩ T1D | 18,219 | 68.6% |
| HF ∩ T1D | 15,432 | 58.1% |

> **Key insight:** Cross-indication overlap is **high** (74–88% for SGLT2/GLP1 and ACE/ARB). This means most D2+ HCPs in one indication are also D2+ in others for the same drug pool. The indications capture largely overlapping prescriber populations, especially T2D ∩ CKD.

---

## 4. Cross-Drug-Pool Overlap (D2+ HCPs, Per Indication)

For each indication: how much overlap exists between the 3 drug pools?

### 4.1 T2D

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 189,889 | 90.0% |
| SGLT2/GLP1 ∩ sMRA | 115,203 | 54.6% |
| ACE/ARB ∩ sMRA | 158,982 | 64.6% |

### 4.2 CKD

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 173,155 | 84.4% |
| SGLT2/GLP1 ∩ sMRA | 102,826 | 54.0% |
| ACE/ARB ∩ sMRA | 132,717 | 69.7% |

### 4.3 HF

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 166,058 | 72.7% |
| SGLT2/GLP1 ∩ sMRA | 117,379 | 68.3% |
| ACE/ARB ∩ sMRA | 131,535 | 76.5% |

### 4.4 T1D

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 19,838 | 46.3% |
| SGLT2/GLP1 ∩ sMRA | 4,382 | 16.5% |
| ACE/ARB ∩ sMRA | 8,854 | 33.4% |

> **Key insight:** SGLT2/GLP1 ∩ ACE/ARB overlap is very high in T2D (90%) and CKD (84%) — HCPs who prescribe one pool at D2+ volume typically also prescribe the other. sMRA has lower cross-pool overlap (54–68% for major indications). T1D has notably low cross-pool overlap (≤46%), suggesting T1D prescribers are more specialized.

---

## 5. Aggregated Counts

### 5.1 Grand Union & Intersection

| Metric | HCPs |
|:-------|-----:|
| **Union of all 12 D2+ sets** | **457,768** |
| Intersection of all 12 sets | 1,270 |
| Intersection / Union ratio | 0.3% |

> The 12-way intersection is tiny (1,270) because T1D × sMRA is very small. The grand union (458K) represents the broadest possible v4 universe from this approach.

### 5.2 Per-Indication Union (any of 3 drug pools D2+)

| Indication | HCPs |
|:-----------|-----:|
| T2D | 383,822 |
| CKD | 336,676 |
| HF | 331,020 |
| T1D | 136,333 |

### 5.3 Per-Drug-Pool Union (any of 4 indications D2+)

| Drug Pool | HCPs |
|:----------|-----:|
| ACE/ARB | 361,459 |
| sMRA | 303,837 |
| SGLT2/GLP1 | 295,323 |

### 5.4 Per-Indication Intersection (all 3 drug pools D2+)

| Indication | HCPs |
|:-----------|-----:|
| T2D | 109,600 |
| HF | 103,598 |
| CKD | 95,866 |
| T1D | 2,794 |

> The per-indication 3-pool intersection gives a **focused core** of multi-class prescribers within each disease. T2D (110K) and HF (104K) are the richest; T1D (2.8K) is negligible.

---

## 6. Key Findings & Next Steps

### Findings

1. **T2D is the richest indication** across all drug pools (211–281K D2+ HCPs)
2. **Cross-indication overlap is high** (74–88%) — the same HCPs prescribe across T2D, CKD, HF
3. **SGLT2/GLP1 ∩ ACE/ARB overlap is very tight** (84–90% for T2D/CKD) — these drug pools have highly overlapping prescriber bases
4. **sMRA has lower cross-pool overlap** (54–69%) — sMRA prescribers are a more distinct population
5. **T1D is a small, specialized cohort** (43–97K D2+, very low cross-pool overlap)
6. **Grand union = 458K HCPs** from all 12 sets — a plausible v4 universe candidate
7. **Per-indication 3-pool intersections** (96–110K for T2D/CKD/HF) could serve as a high-confidence core

### Design Options for v4 Universe

| Option | Logic | Estimated Size |
|:-------|:------|---------------:|
| A. Grand union (all 12) | D2+ in any indication × pool | ~458K |
| B. Per-indication union, then union across indications | Same as A | ~458K |
| C. Per-indication 3-pool intersection, union across indications | D2+ in all 3 pools within any indication | ~200K (est.) |
| D. Select top-2 indications (T2D+CKD) union | D2+ in any pool for T2D or CKD | ~400K (est.) |
| E. Weighted: require D2+ in ≥2 of 3 pools in ≥1 indication | Balanced selectivity | TBD |

### Additional Note: `pt_lvl_nbrx` as Alternative Source

`pt_lvl_nbrx` has **both** `INDICATION_GROUP_APP1` and `PRODUCT_CLASS` at **claim level** (each row = 1 NBRX claim). This would allow true count-based deciling (each claim = 1 unit, matching v1’s TRx methodology exactly) instead of aggregated `sum(NBRX)` from `lrx_nbrx`. Consider re-running with `pt_lvl_nbrx` for final v4 universe.

---

*Generated by Genie Code — October 14, 2026*