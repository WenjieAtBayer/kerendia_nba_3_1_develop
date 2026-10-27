# NextGen NBA 3.1 — v4 Indication × Drug-Pool Decile Analysis (Decile 4+)

**Date:** October 14, 2026  
**Notebook:** `04_HCP_Universe_v4_Indication_DrugPool_Analysis`  
**Source:** `lrx_nbrx` — `INDICATION_GROUP_APP1` (claim-level indication) × `PRODUCT_CLASS`  
**Metric:** `sum(NBRX)` per PROVIDER_ID within each indication × drug pool  
**Decile Method:** Cumulative volume-based (each decile ≈ 10% of total NBRX volume)  
**Decile Cutoff:** **4+** (drops D1–D3 — bottom ~30% of NBRX volume)  
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

For each cell: filter `lrx_nbrx` to rows where `INDICATION_GROUP_APP1` contains the indication AND `PRODUCT_CLASS` is in the drug pool, sum NBRX per HCP, apply cumulative volume decile, keep **Decile 4+**.

---

## 2. Results: All 12 Decile Sets

### 2.1 Decile 4+ HCP Counts

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|----------:|--------:|-----:|
| **T2D** | **106,869** | **143,309** | **115,116** |
| **CKD** | **95,465** | **123,567** | **82,212** |
| **HF** | **109,756** | **114,988** | **68,218** |
| **T1D** | **17,574** | **61,723** | **19,515** |

### 2.2 Total HCPs Per Combination (before decile filter)

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|----------:|--------:|-----:|
| T2D | 553,251 | 603,913 | 408,786 |
| CKD | 449,230 | 494,874 | 304,670 |
| HF | 430,659 | 409,457 | 312,648 |
| T1D | 56,350 | 114,916 | 30,056 |

### 2.3 D1–D3 Drop Rate

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|:---------:|:------:|:---:|
| T2D | 80.7% | 76.3% | 71.8% |
| CKD | 78.7% | 75.0% | 73.0% |
| HF | 74.5% | 71.9% | 78.2% |
| T1D | 68.8% | 46.3% | 35.1% |

### 2.4 D2+ vs D3+ vs D4+ Comparison

| Indication | Drug Pool | D2+ | D3+ | D4+ | D2+→D4+ Δ |
|:-----------|:----------|------:|------:|------:|:---------:|
| T2D | SGLT2/GLP1 | 210,872 | 146,270 | 106,869 | −49.3% |
| T2D | ACE/ARB | 281,207 | 195,788 | 143,309 | −49.0% |
| T2D | sMRA | 246,217 | 166,588 | 115,116 | −53.2% |
| CKD | SGLT2/GLP1 | 205,248 | 136,503 | 95,465 | −53.5% |
| CKD | ACE/ARB | 253,771 | 173,187 | 123,567 | −51.3% |
| CKD | sMRA | 190,489 | 123,656 | 82,212 | −56.8% |
| HF | SGLT2/GLP1 | 228,342 | 155,917 | 109,756 | −51.9% |
| HF | ACE/ARB | 242,195 | 163,125 | 114,988 | −52.5% |
| HF | sMRA | 171,857 | 106,412 | 68,218 | −60.3% |
| T1D | SGLT2/GLP1 | 42,885 | 29,419 | 17,574 | −59.0% |
| T1D | ACE/ARB | 97,185 | 79,454 | 61,723 | −36.5% |
| T1D | sMRA | 26,543 | 23,029 | 19,515 | −26.5% |

> **Moving from D2+ to D4+ drops ~49–60% of HCPs** in most combinations. HF × sMRA sees the steepest drop (−60.3%). T1D ACE/ARB and sMRA are more resilient (−27–37%) due to concentrated prescriber pools.

---

## 3. Cross-Indication Overlap (D4+ HCPs, Per Drug Pool)

### 3.1 SGLT2/GLP1

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 74,728 | 78.3% |
| T2D ∩ HF | 65,369 | 61.2% |
| T2D ∩ T1D | 14,037 | 79.9% |
| CKD ∩ HF | 67,486 | 70.7% |
| CKD ∩ T1D | 13,166 | 74.9% |
| HF ∩ T1D | 12,543 | 71.4% |

### 3.2 ACE/ARB

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 96,768 | 78.3% |
| T2D ∩ HF | 70,476 | 61.3% |
| T2D ∩ T1D | 37,968 | 61.5% |
| CKD ∩ HF | 76,221 | 66.3% |
| CKD ∩ T1D | 35,082 | 56.8% |
| HF ∩ T1D | 30,071 | 48.7% |

### 3.3 sMRA

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 66,758 | 81.2% |
| T2D ∩ HF | 56,325 | 82.6% |
| T2D ∩ T1D | 11,927 | 61.1% |
| CKD ∩ HF | 54,413 | 79.8% |
| CKD ∩ T1D | 9,344 | 47.9% |
| HF ∩ T1D | 7,661 | 39.3% |

> At D4+, cross-indication overlaps drop further (61–83% vs 67–88% at D3+, 74–88% at D2+). sMRA T2D ∩ HF remains high (82.6%) but T1D pairs weaken significantly (39–62%).

---

## 4. Cross-Drug-Pool Overlap (D4+ HCPs, Per Indication)

### 4.1 T2D

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 83,941 | 78.5% |
| SGLT2/GLP1 ∩ sMRA | 37,699 | 35.3% |
| ACE/ARB ∩ sMRA | 55,501 | 48.2% |

### 4.2 CKD

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 71,002 | 74.4% |
| SGLT2/GLP1 ∩ sMRA | 30,779 | 37.4% |
| ACE/ARB ∩ sMRA | 48,136 | 58.6% |

### 4.3 HF

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 68,251 | 62.2% |
| SGLT2/GLP1 ∩ sMRA | 41,750 | 61.2% |
| ACE/ARB ∩ sMRA | 51,953 | 76.2% |

### 4.4 T1D

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 8,689 | 49.4% |
| SGLT2/GLP1 ∩ sMRA | 1,604 | 9.1% |
| ACE/ARB ∩ sMRA | 5,661 | 29.0% |

> At D4+, SGLT2/GLP1 ∩ sMRA drops dramatically (35% for T2D, 9% for T1D). The drug pools become much more distinct at higher decile cutoffs. ACE/ARB ∩ sMRA holds better (48–76%) except T1D.

---

## 5. Aggregated Counts

### 5.1 Grand Union & Intersection

| Metric | D4+ | D3+ (ref) | D2+ (ref) |
|:-------|----:|----------:|----------:|
| **Union of all 12 sets** | **280,615** | 354,641 | 457,768 |
| Intersection of all 12 sets | 254 | 679 | 1,270 |
| Intersection / Union ratio | 0.1% | 0.2% | 0.3% |

### 5.2 Per-Indication Union (any of 3 drug pools D4+)

| Indication | D4+ | D3+ (ref) | D2+ (ref) | D2+→D4+ Δ |
|:-----------|----:|----------:|----------:|:---------:|
| T2D | 221,379 | 287,953 | 383,822 | −42.3% |
| CKD | 179,340 | 241,566 | 336,676 | −46.7% |
| HF | 167,789 | 231,050 | 331,020 | −49.3% |
| T1D | 84,035 | 109,727 | 136,333 | −38.4% |

### 5.3 Per-Drug-Pool Union (any of 4 indications D4+)

| Drug Pool | D4+ | D3+ (ref) | D2+ (ref) | D2+→D4+ Δ |
|:----------|----:|----------:|----------:|:---------:|
| ACE/ARB | 216,579 | 277,289 | 361,459 | −40.1% |
| SGLT2/GLP1 | 162,767 | 215,935 | 295,323 | −44.9% |
| sMRA | 143,547 | 206,430 | 303,837 | −52.7% |

### 5.4 Per-Indication Intersection (all 3 drug pools D4+)

| Indication | D4+ | D3+ (ref) | D2+ (ref) | D2+→D4+ Δ |
|:-----------|----:|----------:|----------:|:---------:|
| HF | 36,781 | 60,589 | 103,598 | −64.5% |
| T2D | 33,226 | 58,672 | 109,600 | −69.7% |
| CKD | 28,013 | 50,737 | 95,866 | −70.8% |
| T1D | 1,177 | 2,003 | 2,794 | −57.9% |

> The 3-pool intersection collapses at D4+ (−65–71% from D2+). T2D drops from 110K to 33K, CKD from 96K to 28K. Only HF holds relatively better (37K) because HF prescribers tend to span all 3 pools.

---

## 6. Key Findings & Next Steps

### D2+ vs D3+ vs D4+ Summary

| Metric | D2+ | D3+ | D4+ |
|:-------|----:|----:|----:|
| Grand union (all 12) | 457,768 | 354,641 | **280,615** |
| T2D 3-pool intersection | 109,600 | 58,672 | **33,226** |
| CKD 3-pool intersection | 95,866 | 50,737 | **28,013** |
| HF 3-pool intersection | 103,598 | 60,589 | **36,781** |
| Avg cross-indication overlap | 74–88% | 67–83% | **61–83%** |
| Avg cross-pool overlap | 46–90% | 13–85% | **9–79%** |

### Findings

1. **D4+ is ~39% smaller** than D2+ at the grand union level (281K vs 458K)
2. **Per-indication 3-pool intersections collapse** (−65–71% from D2+): T2D 110K→33K, CKD 96K→28K
3. **Cross-pool overlaps weaken dramatically** at D4+, especially SGLT2/GLP1 ∩ sMRA (35% for T2D, 9% for T1D)
4. **sMRA is the most affected** pool (−53% from D2+→D4+) — its prescribers are more distributed across lower deciles
5. **T1D ACE/ARB is the most resilient** (−36.5% from D2+) — concentrated prescriber pool
6. **HF 3-pool intersection (37K)** is now the largest per-indication core, overtaking T2D

### Recommendation

D4+ is likely too aggressive for a broad universe — the 3-pool intersections lose 65–71% of their D2+ sizes. However, D4+ could serve as a **high-value tiering layer** within a D2+-based universe to identify the most active multi-class prescribers. Consider using D2+ for universe inclusion and D4+ as a targeting priority flag.

---

*Generated by Genie Code — October 14, 2026*