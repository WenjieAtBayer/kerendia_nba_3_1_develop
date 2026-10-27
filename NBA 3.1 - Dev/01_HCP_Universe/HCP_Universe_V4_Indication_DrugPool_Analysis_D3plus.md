# NextGen NBA 3.1 — v4 Indication × Drug-Pool Decile Analysis (Decile 3+)

**Date:** October 14, 2026  
**Notebook:** `04_HCP_Universe_v4_Indication_DrugPool_Analysis`  
**Source:** `lrx_nbrx` — `INDICATION_GROUP_APP1` (claim-level indication) × `PRODUCT_CLASS`  
**Metric:** `sum(NBRX)` per PROVIDER_ID within each indication × drug pool  
**Decile Method:** Cumulative volume-based (each decile ≈ 10% of total NBRX volume)  
**Decile Cutoff:** **3+** (drops D1 and D2 — bottom ~20% of NBRX volume)  
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

For each cell: filter `lrx_nbrx` to rows where `INDICATION_GROUP_APP1` contains the indication AND `PRODUCT_CLASS` is in the drug pool, sum NBRX per HCP, apply cumulative volume decile, keep **Decile 3+**.

---

## 2. Results: All 12 Decile Sets

### 2.1 Decile 3+ HCP Counts

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|----------:|--------:|-----:|
| **T2D** | **146,270** | **195,788** | **166,588** |
| **CKD** | **136,503** | **173,187** | **123,656** |
| **HF** | **155,917** | **163,125** | **106,412** |
| **T1D** | **29,419** | **79,454** | **23,029** |

### 2.2 Total HCPs Per Combination (before decile filter)

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|----------:|--------:|-----:|
| T2D | 553,251 | 603,913 | 408,786 |
| CKD | 449,230 | 494,874 | 304,670 |
| HF | 430,659 | 409,457 | 312,648 |
| T1D | 56,350 | 114,916 | 30,056 |

### 2.3 D1–D2 Drop Rate

| Indication | SGLT2/GLP1 | ACE/ARB | sMRA |
|:-----------|:---------:|:------:|:---:|
| T2D | 73.6% | 67.6% | 59.2% |
| CKD | 69.6% | 65.0% | 59.4% |
| HF | 63.8% | 60.2% | 66.0% |
| T1D | 47.8% | 30.9% | 23.4% |

### 2.4 D2+ vs D3+ Comparison

| Indication | Drug Pool | D2+ | D3+ | Reduction |
|:-----------|:----------|------:|------:|:---------:|
| T2D | SGLT2/GLP1 | 210,872 | 146,270 | −30.6% |
| T2D | ACE/ARB | 281,207 | 195,788 | −30.4% |
| T2D | sMRA | 246,217 | 166,588 | −32.3% |
| CKD | SGLT2/GLP1 | 205,248 | 136,503 | −33.5% |
| CKD | ACE/ARB | 253,771 | 173,187 | −31.8% |
| CKD | sMRA | 190,489 | 123,656 | −35.1% |
| HF | SGLT2/GLP1 | 228,342 | 155,917 | −31.7% |
| HF | ACE/ARB | 242,195 | 163,125 | −32.6% |
| HF | sMRA | 171,857 | 106,412 | −38.1% |
| T1D | SGLT2/GLP1 | 42,885 | 29,419 | −31.4% |
| T1D | ACE/ARB | 97,185 | 79,454 | −18.2% |
| T1D | sMRA | 26,543 | 23,029 | −13.2% |

> **Moving from D2+ to D3+ drops ~30–35% of HCPs** in most combinations. T1D ACE/ARB and sMRA drop less (−13–18%) because T1D has a smaller, higher-volume prescriber base.

---

## 3. Cross-Indication Overlap (D3+ HCPs, Per Drug Pool)

### 3.1 SGLT2/GLP1

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 110,659 | 81.1% |
| T2D ∩ HF | 99,048 | 67.7% |
| T2D ∩ T1D | 23,372 | 79.4% |
| CKD ∩ HF | 104,326 | 76.4% |
| CKD ∩ T1D | 22,500 | 76.5% |
| HF ∩ T1D | 22,101 | 75.1% |

### 3.2 ACE/ARB

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 144,082 | 83.2% |
| T2D ∩ HF | 112,058 | 68.7% |
| T2D ∩ T1D | 53,111 | 66.8% |
| CKD ∩ HF | 117,232 | 71.9% |
| CKD ∩ T1D | 49,145 | 61.9% |
| HF ∩ T1D | 42,612 | 53.6% |

### 3.3 sMRA

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| T2D ∩ CKD | 99,906 | 80.8% |
| T2D ∩ HF | 86,320 | 81.1% |
| T2D ∩ T1D | 16,186 | 70.3% |
| CKD ∩ HF | 84,107 | 79.0% |
| CKD ∩ T1D | 13,260 | 57.6% |
| HF ∩ T1D | 11,017 | 47.8% |

> Cross-indication overlaps at D3+ are slightly lower than D2+ (67–83% vs 74–88%) — the tighter cutoff reveals more indication-specific HCPs.

---

## 4. Cross-Drug-Pool Overlap (D3+ HCPs, Per Indication)

### 4.1 T2D

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 124,010 | 84.8% |
| SGLT2/GLP1 ∩ sMRA | 63,833 | 43.6% |
| ACE/ARB ∩ sMRA | 91,522 | 54.9% |

### 4.2 CKD

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 108,264 | 79.3% |
| SGLT2/GLP1 ∩ sMRA | 55,179 | 44.6% |
| ACE/ARB ∩ sMRA | 79,074 | 63.9% |

### 4.3 HF

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 105,065 | 67.4% |
| SGLT2/GLP1 ∩ sMRA | 68,410 | 64.3% |
| ACE/ARB ∩ sMRA | 81,518 | 76.6% |

### 4.4 T1D

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2/GLP1 ∩ ACE/ARB | 14,139 | 48.1% |
| SGLT2/GLP1 ∩ sMRA | 2,963 | 12.9% |
| ACE/ARB ∩ sMRA | 7,076 | 30.7% |

> At D3+, SGLT2/GLP1 ∩ sMRA cross-pool overlap drops significantly (44–54% for T2D/CKD, vs 54–68% at D2+). T1D cross-pool overlap is very low (≤48%), confirming T1D prescribers are highly specialized.

---

## 5. Aggregated Counts

### 5.1 Grand Union & Intersection

| Metric | D3+ | D2+ (ref) |
|:-------|----:|----------:|
| **Union of all 12 sets** | **354,641** | 457,768 |
| Intersection of all 12 sets | 679 | 1,270 |
| Intersection / Union ratio | 0.2% | 0.3% |

### 5.2 Per-Indication Union (any of 3 drug pools D3+)

| Indication | D3+ | D2+ (ref) | Reduction |
|:-----------|----:|----------:|:---------:|
| T2D | 287,953 | 383,822 | −25.0% |
| CKD | 241,566 | 336,676 | −28.3% |
| HF | 231,050 | 331,020 | −30.2% |
| T1D | 109,727 | 136,333 | −19.5% |

### 5.3 Per-Drug-Pool Union (any of 4 indications D3+)

| Drug Pool | D3+ | D2+ (ref) | Reduction |
|:----------|----:|----------:|:---------:|
| ACE/ARB | 277,289 | 361,459 | −23.3% |
| SGLT2/GLP1 | 215,935 | 295,323 | −26.9% |
| sMRA | 206,430 | 303,837 | −32.1% |

### 5.4 Per-Indication Intersection (all 3 drug pools D3+)

| Indication | D3+ | D2+ (ref) | Reduction |
|:-----------|----:|----------:|:---------:|
| HF | 60,589 | 103,598 | −41.5% |
| T2D | 58,672 | 109,600 | −46.5% |
| CKD | 50,737 | 95,866 | −47.1% |
| T1D | 2,003 | 2,794 | −28.3% |

> The 3-pool intersection drops **41–47%** from D2+ to D3+ for T2D/CKD/HF — the multi-class core is cut roughly in half. Grand union drops 22.5% (458K → 355K).

---

## 6. Key Findings & Next Steps

### D2+ vs D3+ Summary

| Metric | D2+ | D3+ | Δ |
|:-------|----:|----:|:--:|
| Grand union (all 12) | 457,768 | 354,641 | −22.5% |
| T2D 3-pool intersection | 109,600 | 58,672 | −46.5% |
| CKD 3-pool intersection | 95,866 | 50,737 | −47.1% |
| HF 3-pool intersection | 103,598 | 60,589 | −41.5% |
| Avg cross-indication overlap | 74–88% | 67–83% | −5–7pp |
| Avg cross-pool overlap | 46–90% | 13–85% | wider spread |

### Findings

1. **D3+ is ~22% smaller** than D2+ at the grand union level (355K vs 458K)
2. **Per-indication 3-pool intersections halve** (T2D: 110K→59K, CKD: 96K→51K, HF: 104K→61K)
3. **Cross-pool overlaps weaken significantly** at D3+, especially SGLT2/GLP1 ∩ sMRA (drops to 44% for T2D)
4. **T1D remains small and specialized** (29K SGLT2/GLP1, 2K 3-pool intersection)
5. **D3+ tightens the universe** by removing an additional ~103K HCPs who sit in D2 (the boundary decile)

### Recommendation

D2+ is likely the better cutoff for v4 — D3+ removes too many HCPs from the multi-class intersections (46–47% loss) without proportionally improving targeting quality. The D2 band already filters out the bottom 10% of NBRX volume. If a tighter universe is needed, consider D2+ with a minimum N-class threshold (e.g., D2+ in ≥2 of 3 pools) rather than raising the decile cutoff.

---

*Generated by Genie Code — October 14, 2026*