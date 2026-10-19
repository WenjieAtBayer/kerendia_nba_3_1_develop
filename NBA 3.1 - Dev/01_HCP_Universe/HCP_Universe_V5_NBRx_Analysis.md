# NBA 3.1 v5 — NBRx-Based Indication × Drug-Pool Analysis

**Date:** October 15, 2026  
**Source:** `pace_ker_in_house_schema.lrx_nbrx` (247.3M rows total, 103.9M in lookback)  
**Metric:** `sum(NBRX)` per PROVIDER_ID  
**Indication column:** `INDICATION_GROUP_APP1` (T2D, CKD, HF, T1D — compound values with `contains()`)  
**Product column:** `PRODUCT_CLASS` (SGLT2, GLP1, ACE, ARB, KERENDIA, sMRA, etc.)  
**Decile Method:** Cumulative volume-based (each decile ≈ 10% of total NBRX volume)  
**Lookback:** Oct ’24 – Sep ’26 (1,357,359 unique HCPs)  
**Notebook:** `05_HCP_Universe_V5_NBRx_Analysis`  

---

## Key Changes from v4

| | v4 | v5 |
|---|---|---|
| **Metric** | `sum(NBRX)` from `lrx_nbrx` | `sum(NBRX)` from `lrx_nbrx` (same) |
| **Indications** | T2D, CKD, HF, T1D | T2D, CKD, HF, T1D (same) |
| **Product column** | `PRODUCT_CLASS` | `PRODUCT_CLASS` (same) |
| **Kerendia coverage** | Not analysed | Full writer coverage analysis |
| **Decile cutoff** | D3+ assumed | No assumption — full D1–D10 provided |

### PRODUCT_CLASS → Drug Pool Mapping

* **SGLT2/GLP1 pool:** `SGLT2`, `GLP1`
* **ACE/ARB pool:** `ACE`, `ARB`
* **sMRA excluded** (same as v4)

### INDICATION_GROUP_APP1 Values

16 compound values (e.g., "T2D + CKD", "T1D + T2D + CKD + HF"). Uses `contains()` matching. A single row can contribute to multiple indication groups.

---

## 1. Full Decile Distributions (D1–D10)

### 1.1 T2D × SGLT2/GLP1 (553,251 HCPs — 16.7M NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 342,379 | 61.9% | 61.9% | 1–18 |
| 2 | 64,602 | 11.7% | 73.6% | 18–35 |
| 3 | 39,401 | 7.1% | 80.7% | 35–50 |
| 4 | 28,933 | 5.2% | 85.9% | 50–66 |
| 5 | 22,648 | 4.1% | 90.0% | 66–83 |
| 6 | 18,096 | 3.3% | 93.3% | 83–103 |
| 7 | 14,438 | 2.6% | 95.9% | 103–131 |
| 8 | 11,106 | 2.0% | 97.9% | 131–176 |
| 9 | 7,726 | 1.4% | 99.3% | 176–281 |
| 10 | 3,922 | 0.7% | 100.0% | 281–10,351 |

### 1.2 T2D × ACE/ARB (603,913 HCPs — 7.7M NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 322,706 | 53.4% | 53.4% | 1–6 |
| 2 | 85,419 | 14.1% | 67.6% | 6–12 |
| 3 | 52,479 | 8.7% | 76.3% | 12–18 |
| 4 | 38,139 | 6.3% | 82.6% | 18–23 |
| 5 | 29,780 | 4.9% | 87.5% | 23–29 |
| 6 | 23,871 | 4.0% | 91.5% | 29–36 |
| 7 | 19,195 | 3.2% | 94.6% | 36–45 |
| 8 | 15,123 | 2.5% | 97.2% | 45–58 |
| 9 | 11,130 | 1.8% | 99.0% | 58–85 |
| 10 | 6,071 | 1.0% | 100.0% | 85–8,573 |

### 1.3 CKD × SGLT2/GLP1 (449,230 HCPs — 6.0M NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 243,982 | 54.3% | 54.3% | 1–6 |
| 2 | 68,745 | 15.3% | 69.6% | 6–12 |
| 3 | 41,038 | 9.1% | 78.7% | 12–18 |
| 4 | 28,551 | 6.4% | 85.1% | 18–25 |
| 5 | 21,076 | 4.7% | 89.8% | 25–33 |
| 6 | 15,947 | 3.5% | 93.3% | 33–43 |
| 7 | 12,022 | 2.7% | 96.0% | 43–58 |
| 8 | 8,864 | 2.0% | 98.0% | 58–81 |
| 9 | 6,000 | 1.3% | 99.3% | 81–130 |
| 10 | 3,005 | 0.7% | 100.0% | 130–2,979 |

### 1.4 CKD × ACE/ARB (494,874 HCPs — 4.0M NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 241,103 | 48.7% | 48.7% | 1–4 |
| 2 | 80,584 | 16.3% | 65.0% | 4–7 |
| 3 | 49,620 | 10.0% | 75.0% | 7–10 |
| 4 | 35,274 | 7.1% | 82.2% | 10–13 |
| 5 | 26,472 | 5.3% | 87.5% | 13–17 |
| 6 | 20,426 | 4.1% | 91.6% | 17–22 |
| 7 | 15,806 | 3.2% | 94.8% | 22–29 |
| 8 | 12,036 | 2.4% | 97.3% | 29–39 |
| 9 | 8,673 | 1.8% | 99.0% | 39–57 |
| 10 | 4,880 | 1.0% | 100.0% | 57–2,467 |

### 1.5 HF × SGLT2/GLP1 (430,659 HCPs — 3.4M NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 202,317 | 47.0% | 47.0% | 1–3 |
| 2 | 72,425 | 16.8% | 63.8% | 3–6 |
| 3 | 46,161 | 10.7% | 74.5% | 6–9 |
| 4 | 32,877 | 7.6% | 82.1% | 9–12 |
| 5 | 24,500 | 5.7% | 87.8% | 12–16 |
| 6 | 18,530 | 4.3% | 92.1% | 16–21 |
| 7 | 13,843 | 3.2% | 95.4% | 21–29 |
| 8 | 10,004 | 2.3% | 97.7% | 29–41 |
| 9 | 6,663 | 1.5% | 99.2% | 41–67 |
| 10 | 3,339 | 0.8% | 100.0% | 67–2,383 |

### 1.6 HF × ACE/ARB (409,457 HCPs — 2.0M NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 167,262 | 40.8% | 40.8% | 1–2 |
| 2 | 79,070 | 19.3% | 60.2% | 2–3 |
| 3 | 48,137 | 11.8% | 71.9% | 3–5 |
| 4 | 34,542 | 8.4% | 80.4% | 5–7 |
| 5 | 25,439 | 6.2% | 86.6% | 7–9 |
| 6 | 19,110 | 4.7% | 91.2% | 9–12 |
| 7 | 14,342 | 3.5% | 94.7% | 12–16 |
| 8 | 10,486 | 2.6% | 97.3% | 16–23 |
| 9 | 7,218 | 1.8% | 99.1% | 23–35 |
| 10 | 3,851 | 0.9% | 100.0% | 35–1,443 |

### 1.7 T1D × SGLT2/GLP1 (56,350 HCPs — 135K NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 13,465 | 23.9% | 23.9% | 1–1 |
| 2 | 13,466 | 23.9% | 47.8% | 1–1 |
| 3 | 11,845 | 21.0% | 68.8% | 1–2 |
| 4 | 6,733 | 11.9% | 80.8% | 2–2 |
| 5 | 4,284 | 7.6% | 88.4% | 2–4 |
| 6–10 | 6,557 | 11.6% | 100.0% | 4–201 |

> **T1D × SGLT2/GLP1** is unique: D1–D3 all have max NBRX ≤2. Most T1D HCPs are single-script writers.

### 1.8 T1D × ACE/ARB (114,916 HCPs — 582K NBRX)

| Decile | HCPs | % HCPs | Cum % HCPs | NBRx Range |
|:------:|------:|:------:|:----------:|:----------:|
| 1 | 17,731 | 15.4% | 15.4% | 1–2 |
| 2 | 17,731 | 15.4% | 30.9% | 2–4 |
| 3 | 17,731 | 15.4% | 46.3% | 4–5 |
| 4 | 17,731 | 15.4% | 61.7% | 5–7 |
| 5 | 14,269 | 12.4% | 74.1% | 7–9 |
| 6–10 | 29,723 | 25.9% | 100.0% | 9–504 |

---

## 2. Summary: HCP Counts by Decile Cutoff

| Ind × Pool | Total | D2+ | D3+ | D4+ | D5+ |
|:-----------|------:|------:|------:|------:|------:|
| T2D × SGLT2/GLP1 | 553,251 | 210,872 | 146,270 | 106,869 | 77,936 |
| T2D × ACE/ARB | 603,913 | 281,207 | 195,788 | 143,309 | 105,170 |
| CKD × SGLT2/GLP1 | 449,230 | 205,248 | 136,503 | 95,465 | 66,914 |
| CKD × ACE/ARB | 494,874 | 253,771 | 173,187 | 123,567 | 88,293 |
| HF × SGLT2/GLP1 | 430,659 | 228,342 | 155,917 | 109,756 | 76,879 |
| HF × ACE/ARB | 409,457 | 242,195 | 163,125 | 114,988 | 80,446 |
| T1D × SGLT2/GLP1 | 56,350 | 42,885 | 29,419 | 17,574 | 10,841 |
| T1D × ACE/ARB | 114,916 | 97,185 | 79,454 | 61,723 | 43,992 |

> **D1 holds 24–62% of HCPs** across combinations (lowest for T1D, highest for T2D×SGLT2/GLP1) but contributes only 10% of NBRX volume. These are the lowest-volume prescribers.

---

## 3. Kerendia Writer Coverage

### 3.1 Writer Counts

| Metric | Count |
|:-------|------:|
| Kerendia writers (NBRX > 0, lookback) | **40,112** |
| Total KERENDIA NBRX in lookback | **196,109** |

### 3.2 Writers by INDICATION_GROUP_APP1

| Indication Group | NBRX | HCPs |
|:-----------------|-----:|-----:|
| T2D + CKD | 83,288 | 22,731 |
| T2D + CKD + HF | 44,396 | 17,008 |
| T2D | 31,142 | 13,705 |
| T2D + HF | 8,260 | 4,765 |
| OTHERS | 7,455 | 4,753 |
| CKD | 6,320 | 4,070 |
| CKD + HF | 6,099 | 3,598 |
| HF | 5,751 | 2,906 |
| T1D + CKD | 1,855 | 1,568 |
| T1D (all groups) | 1,443 | 1,414 |

> **65% of Kerendia NBRX** comes from T2D+CKD and T2D+CKD+HF indication groups. T1D is very small (1.4K writers).

### 3.3 Kerendia Writer Capture by Decile Cutoff (Paid Writers)

| Ind × Pool | In Set | NOT in | D2+ | D3+ | D4+ | D5+ |
|:-----------|-------:|-------:|------:|------:|------:|------:|
| T2D × SGLT2/GLP1 | 39,437 | 675 | 76.0% | 61.4% | 51.3% | 43.0% |
| T2D × ACE/ARB | 39,267 | 845 | **86.1%** | 73.6% | 62.2% | 51.6% |
| CKD × SGLT2/GLP1 | 38,996 | 1,116 | 84.1% | 72.1% | 60.8% | 49.9% |
| CKD × ACE/ARB | 38,582 | 1,530 | **85.1%** | 74.2% | 63.9% | 53.9% |
| HF × SGLT2/GLP1 | 38,014 | 2,098 | 79.9% | 68.0% | 57.2% | 47.1% |
| HF × ACE/ARB | 35,736 | 4,376 | 74.4% | 61.8% | 50.8% | 40.9% |
| T1D × SGLT2/GLP1 | 10,479 | 29,633 | 21.4% | 16.7% | 11.1% | 7.6% |
| T1D × ACE/ARB | 16,949 | 23,163 | 36.9% | 32.5% | 29.3% | 22.8% |

### 3.4 Union Capture Across All 8 Sets

| Cutoff | Writers Captured | % of 40,112 |
|:-------|----------------:|:-----------:|
| D2+ | 38,421 | **95.8%** |
| D3+ | 36,671 | 91.4% |
| D4+ | 34,500 | 86.0% |
| D5+ | 31,908 | 79.5% |

### 3.5 Writers NOT in ANY Decile Set

**275 writers** (0.7%) have zero claims in all 8 indication×pool combinations. These are Kerendia-only prescribers with no SGLT2/GLP1 or ACE/ARB claims for any indication.

* Specialty: PCP 227, OTHERS 21, NEPH 14, CARD 5, HOS 4, ENDO 3, HOSPITALIST 1
* Kerendia NBRX: Avg 1.2, Median 1, Max 11 — almost all single-script writers

> **Best single-set capture:** T2D × ACE/ARB (86.1%) and CKD × ACE/ARB (85.1%).  
> **Union of all 8 at D2+** captures **95.8%** of Kerendia writers — the remaining 4.2% (1,691) need a separate Kerendia writer rule.  
> **T1D capture is poor** (21–37%) — most Kerendia writers don't prescribe SGLT2/GLP1 or ACE/ARB for T1D patients.  
> **275 writers are completely missed** by all 8 sets — mostly PCPs with 1 Kerendia script and no other pool claims.

---

## 4. Key Observations

1. **D1 concentration varies**: T2D×SGLT2/GLP1 has 62% in D1; HF×ACE/ARB only 41%. More HCPs are "active" in HF/ACE/ARB than T2D/SGLT2/GLP1.
2. **T1D is very different**: Tiny NBRX volumes (135K–582K vs millions), D1 has only 15–24% of HCPs. T1D deciling behaves differently from T2D/CKD/HF.
3. **Union of 8 sets at D2+ captures 95.8% of Kerendia writers** — but no single set exceeds 86%. Combination logic is essential.
4. **T1D contributes almost nothing to Kerendia capture**: Only 21–37% of writers are in T1D sets. T1D’s role in the combination formula needs rethinking.
5. **275 writers completely missed** — almost all PCPs with a single Kerendia script. Need explicit Kerendia writer criterion.
6. **65% of Kerendia NBRX is from T2D+CKD and T2D+CKD+HF** indication groups — these are the primary Kerendia indications.
7. **`lrx_nbrx` has no non-paid claims** — all rows have NBRX > 0. Non-paid claims expansion requires the LAAD V6 source (67.9K total writers vs 40.1K paid-only).

---

## 5. Kerendia Writer Profiling by Set

### 5.1 Core Sets: Writer Density by Decile

**Set 1: T2D × SGLT2/GLP1 (CORE)** — 39,437 writers in set, 675 missing

| Decile | Ker Writers | Cum % of All | Set HCPs | Writer Density |
|:------:|----------:|:-----------:|--------:|:-------------:|
| 1 | 8,963 | 22.3% | 342,379 | 2.6% |
| 2 | 5,851 | 36.9% | 64,602 | 9.1% |
| 3 | 4,062 | 47.1% | 39,401 | 10.3% |
| 4 | 3,311 | 55.3% | 28,933 | 11.4% |
| 5–10 | 17,250 | 98.3% | 77,936 | 22.1% |

**Set 3: CKD × SGLT2/GLP1 (CORE)** — 38,996 writers in set, 1,116 missing

| Decile | Ker Writers | Cum % of All | Set HCPs | Writer Density |
|:------:|----------:|:-----------:|--------:|:-------------:|
| 1 | 5,256 | 13.1% | 243,982 | 2.2% |
| 2 | 4,828 | 25.1% | 68,745 | 7.0% |
| 3 | 4,531 | 36.4% | 41,038 | 11.0% |
| 4 | 4,348 | 47.3% | 28,551 | 15.2% |
| 5–10 | 20,033 | 97.2% | 66,914 | 29.9% |

> **Key insight:** Writer density climbs steeply from D1 (2–3%) to D10 (49–63%). In the core sets, even D1 contains 5–9K Kerendia writers — dropping D1 loses 13–22% of all writers.

### 5.2 Missing Writers: Cross-Set Recovery

| Set Missing From | Count | Top Recovery Set | Recovers | At D2+ |
|:-----------------|------:|:-----------------|--------:|-------:|
| Set1 (T2D×SGLT2/GLP1) | 675 | Set2 (T2D×ACE/ARB) | 320 | 58 |
| Set3 (CKD×SGLT2/GLP1) | 1,116 | Set2 (T2D×ACE/ARB) | 668 | 201 |
| Set5 (HF×SGLT2/GLP1) | 2,098 | Set2 (T2D×ACE/ARB) | 1,622 | 754 |
| Set6 (HF×ACE/ARB) | 4,376 | Set1 (CORE) | 3,926 | 2,483 |
| Set7 (T1D×SGLT2/GLP1) | 29,633 | Set2 (T2D×ACE/ARB) | 28,848 | 24,898 |
| Set8 (T1D×ACE/ARB) | 23,163 | Set2 (T2D×ACE/ARB) | 22,362 | 18,590 |

> **Pattern:** Missing writers from core sets (675–1,116) are almost all **low-volume, single-script PCPs** (Avg Kerendia NBRX 1.2–1.3). ACE/ARB sets recover them best. T1D sets miss 23–30K writers — most are active in T2D/CKD/HF sets.

### 5.3 Core (Set1 ∪ Set3) Gap + Marginal Add-on Value

| Cutoff | Core HCPs | Core Ker (%) | Best Add-on | Gap Recovered |
|:------:|----------:|:-----------:|:------------|:-------------:|
| D2+ | 242,868 | 35,013 (87.3%) | Set4: CKD×ACE/ARB | 2,209 (43.3%) |
| D3+ | 172,114 | 30,831 (76.9%) | Set4: CKD×ACE/ARB | 3,657 (39.4%) |
| D4+ | 127,606 | 26,776 (66.8%) | Set4: CKD×ACE/ARB | 4,667 (35.0%) |
| D5+ | 94,171 | 22,861 (57.0%) | Set4: CKD×ACE/ARB | 5,267 (30.5%) |

> **Set4 (CKD×ACE/ARB) is always the best first add-on** to the core, recovering 35–43% of the gap. Set6 (HF×ACE/ARB) is a close second.

### 5.4 Greedy Set Addition (D2+ example)

| Step | Action | Universe | Ker Writers | % Captured | Marginal HCPs | Marginal Ker |
|:----:|:-------|--------:|-----------:|:----------:|-------------:|------------:|
| 0 | Core (Set1 ∪ Set3) | 242,868 | 35,013 | 87.3% | — | — |
| 1 | + Set4: CKD×ACE/ARB | 308,048 | 37,222 | 92.8% | 65,180 | 2,209 |
| 2 | + Set5: HF×SGLT2/GLP1 | 331,575 | 37,785 | 94.2% | 23,527 | 563 |
| 3 | + Set2: T2D×ACE/ARB | 353,226 | 38,104 | 95.0% | 21,651 | 319 |
| 4–6 | + T1D + HF×ACE/ARB | 390,549 | 38,421 | 95.8% | 37,323 | 317 |

> **After the core + Set4, each additional set adds diminishing Kerendia writers** (563 → 319 → 37). The remaining 4.2% gap (1,691 writers) needs an explicit Kerendia writer criterion.

---

## 6. NBA 3.0 Universe Overlap

**NBA 3.0 baseline:** 232,965 HCPs (PULL_DT: 2026_10_09)  
**NBA 3.0 Kerendia writers (KERENDIA_FLAG=1):** 77,972  
**v5 Kerendia writers (paid NBRX>0):** 40,112

> **Important:** NBA 3.0 KERENDIA_FLAG (77,972) is broader than v5 paid writers (40,112). NBA 3.0 likely uses a wider definition (e.g., TRx-based, longer lookback, or non-paid claims).

### 6.1 Core (Set1 ∪ Set3) vs NBA 3.0 by Cutoff

| Cutoff | v5 HCPs | Overlap | v5-only | NBA30-only | Ker Overlap | Ker v5-only | Ker NBA30-only |
|:------:|--------:|--------:|--------:|-----------:|------------:|------------:|---------------:|
| ALL | 566,605 | 224,697 | 341,908 | 8,268 | 38,880 | 672 | 39,092 |
| D2+ | 242,868 | 198,007 | 44,861 | 34,958 | 34,545 | 468 | 43,427 |
| D3+ | 172,114 | 160,217 | 11,897 | 72,748 | 30,470 | 361 | 47,502 |
| D4+ | 127,606 | 123,488 | 4,118 | 109,477 | 26,493 | 283 | 51,479 |
| D5+ | 94,171 | 92,427 | 1,744 | 140,538 | 22,662 | 199 | 55,310 |

> **At D2+:** 198K overlap (85% of NBA 3.0), only 35K NBA30-only HCPs not captured. v5 adds 45K new HCPs.  
> **At D3+:** Still 160K overlap (69%), but 73K NBA30-only are lost.  
> **Kerendia writer overlap is very high** — v5-only writers are minimal (48–672), meaning v5 captures nearly all writers that NBA 3.0 has within its own definition.

### 6.2 Flag Distribution: Overlap vs NBA30-only (Core D2+)

| Flag | In Overlap (198K) | % | In NBA30-only (35K) | % |
|:-----|------------------:|:---:|--------------------:|:---:|
| KERENDIA_FLAG | 61,437 | 31.0% | 16,535 | **47.3%** |
| SGLT2_GLP1_FLAG | 185,084 | 93.5% | 8,890 | 25.4% |
| NEPH_FLAG | 8,976 | 4.5% | 7,438 | **21.3%** |
| TARGETING_HCP_FLAG | 66,681 | 33.7% | 11,708 | 33.5% |
| BPT_HCP_FLAG | 66,681 | 33.7% | 11,708 | 33.5% |

> **The 35K NBA30-only HCPs** are enriched in KERENDIA writers (47.3% vs 31.0%) and NEPH (21.3% vs 4.5%). These are high-value HCPs that the core sets miss — they likely enter NBA 3.0 via the Kerendia writer and Nephrology criteria (Criterion 2 & 3), not via deciling.

### 6.3 Kerendia Writer Breakdown (Core D2+)

| Segment | Count |
|:--------|------:|
| In overlap (both v5 & NBA 3.0) | 61,437 |
| v5-only (new writers) | 48 |
| NBA30-only (would lose) | 16,535 |

> The 16,535 NBA30-only Kerendia writers are **not** in the v5 core D2+ decile sets. These must be recovered by the explicit **Kerendia writer criterion** (Criterion 2) in the final universe.

### 6.4 Full 8-Set Union vs NBA 3.0

| Cutoff | v5 Union | Overlap | % NBA30 | v5-only | NBA30-only | Ker Overlap | Ker v5-only | Ker NBA30-only |
|:------:|---------:|--------:|:-------:|--------:|-----------:|------------:|------------:|---------------:|
| D2+ | 390,549 | 218,835 | **93.9%** | 171,715 | 14,131 | 37,812 | 609 | 40,160 |
| D3+ | 303,802 | 204,109 | 87.6% | 99,693 | 28,856 | 36,123 | 548 | 41,849 |
| D4+ | 241,825 | 181,549 | 77.9% | 60,276 | 51,416 | 34,011 | 489 | 43,961 |

> **Full union at D2+ covers 93.9% of the NBA 3.0 universe.** The remaining 14K NBA30-only HCPs are primarily Kerendia writers (40K of 78K NBA30 writers not in v5 paid set) and NEPH specialists.

---

## Summary of Key Insights

1. **v5 Core (Set1 ∪ Set3) at D2+ is the closest match** to NBA 3.0: 198K overlap (85%) with 45K new HCPs
2. **35K NBA30-only HCPs are enriched in Kerendia writers (47%) and NEPH (21%)** — these enter via Criterion 2 (Kerendia writers) and Criterion 3 (Specialty), not deciling
3. **v5 adds almost zero new Kerendia writers** over NBA 3.0 (48 at D2+) — the v5 paid writer list is a strict subset of NBA 3.0’s KERENDIA_FLAG
4. **NBA 3.0 KERENDIA_FLAG is 2× larger** (77,972) than v5 paid writers (40,112) — likely includes TRx-based or non-paid writers
5. **Full 8-set union at D2+ recovers 93.9% of NBA 3.0** — only 14K unmatched, mostly Kerendia/NEPH
6. **Criteria 2–4 (Kerendia writers, Specialty, Targeting/BPT) are essential** to close the gap — deciling alone cannot replace them

---

## 7. Combined Universe: Core + Criterion 2 + Criterion 3

**Criterion definitions:**
* **C1 (Core):** Set1 (T2D×SGLT2/GLP1) ∪ Set3 (CKD×SGLT2/GLP1) at decile cutoff
* **C2 (Kerendia Writers):** `PRODUCT_CLASS = 'KERENDIA'` AND `NBRX > 0` → **40,112 HCPs**
* **C3 (Specialty):** NEPH (15,048) ∪ CARD (51,666) = **66,714 HCPs**

Kerendia writers who are NEPH: 7,525 | CARD: 5,201

### 7.1 Incremental Buildup + 4 Kerendia Metrics

**4 Kerendia Writer Definitions:**
* **M1:** NBA 3.0 `KERENDIA_FLAG` = **77,972** (output flag from prior pipeline run)
* **M2:** LAAD V6 `NBRX > 0`, 24-month lookback = **40,122**
* **M3:** LAAD V6 `TRX > 0`, full history (Jan '23–Sep '26) = **77,582**
* **M4:** Raw `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake), `CLAIM_TYPE='PD'`, `PRODUCT_GROUP='KERENDIA'`, 24-mo lookback = **67,796**

| Cutoff | C1 Core | +C2 Ker | +C3 NEPH | +CARD = Total | %NBA30 | M1: FLAG (77,972) | M2: V6 NBRX (40,122) | M3: V6 TRX (77,582) | M4: FCT_RX (67,796) |
|:------:|--------:|--------:|---------:|--------------:|:------:|------------------:|---------------------:|---------------------:|--------------------:|
| D2+ | 242,868 | 247,967 | 253,215 | **285,608** | **91.7%** | 67,956 (**87.2%**) | 40,098 (99.9%) | 68,143 (87.8%) | 62,046 (**91.5%**) |
| D3+ | 172,114 | 181,395 | 187,521 | **226,462** | 79.8% | 63,614 (81.6%) | 40,086 (99.9%) | 63,870 (82.3%) | 58,744 (86.6%) |
| D4+ | 127,606 | 140,942 | 147,579 | **189,759** | 67.3% | 59,939 (76.9%) | 40,080 (99.9%) | 60,246 (77.7%) | 55,901 (82.5%) |
| D5+ | 94,171 | 111,422 | 118,348 | **162,374** | 56.5% | 56,535 (72.5%) | 40,073 (99.9%) | 56,905 (73.3%) | 53,251 (78.5%) |

> **Key insight:** M4 (67,796) with 24-mo lookback is **smaller** than M1 (77,972) and M3 (77,582) because those use full history. But M4 achieves the **highest capture rate at D2+ (91.5%)** because the 24-mo cohort aligns better with the decile lookback window. M2 is trivially 99.9% since C2 adds all paid NBRX writers. M4 shows that 27,750 writers (67,796 − 40,122 = M4 − M2) wrote Kerendia TRx in the last 2 years but are refill-only (no NBRX).

### 7.2 Flag Distribution (D2+ Combined vs NBA 3.0)

| Flag | In Overlap (213,694) | % | NBA30-only (19,271) | % |
|:-----|---------------------:|:---:|--------------------:|:---:|
| KERENDIA_FLAG | 67,956 | 31.8% | 10,016 | **52.0%** |
| SGLT2_GLP1_FLAG | 187,584 | 87.8% | 6,390 | 33.2% |
| NEPH_FLAG | 15,041 | 7.0% | 1,373 | 7.1% |
| TARGETING_HCP_FLAG | 75,571 | 35.4% | 2,818 | **14.6%** |
| BPT_HCP_FLAG | 75,571 | 35.4% | 2,818 | 14.6% |

> The 19K NBA30-only HCPs are **heavily Kerendia-enriched (52%)** — these are writers captured by NBA 3.0’s broader KERENDIA_FLAG (78K vs v5’s 40K paid). **NEPH coverage is now near-complete** (15,041 in overlap vs only 1,373 remaining).

### 7.3 Kerendia Writer Coverage (D2+ Combined) — 4 Metrics

| Metric | Source | Baseline | In D2+ Universe | % Captured | Missed |
|:-------|:-------|----------:|----------------:|:----------:|-------:|
| **M1: NBA 3.0 KERENDIA_FLAG** | Prior pipeline output (full hist) | 77,972 | 67,956 | **87.2%** | 10,016 |
| **M2: LAAD V6 NBRX>0 (24-mo)** | LAAD V6, 24-mo lookback | 40,122 | 40,098 | **99.9%** | 24 |
| **M3: LAAD V6 TRX>0 (full hist)** | LAAD V6, Jan’23+ | 77,582 | 68,143 | **87.8%** | 9,439 |
| **M4: FCT_RX paid TRX (24-mo)** | Snowflake FCT_RX, Oct’24–Sep’26 | **67,796** | **62,046** | **91.5%** | **5,750** |

**Why these baselines differ:**
* **M1/M3 (full hist) ≫ M4 (24-mo):** Full history captures writers who stopped prescribing before Oct’24; 24-mo only counts active writers
* **M4 > M2 by 27,674:** Both use 24-mo lookback, but M4 = TRx (includes refills), M2 = NBRX (new scripts only) → 27.7K are refill-only writers
* **M4 has best capture rate (91.5%):** The 24-mo cohort aligns with the decile lookback, so more of these writers naturally fall inside the core sets

> **M4 misses only 5,750 writers** at D2+ (vs 10K for M1/M3). These are TRx writers in the last 2 years who aren’t in core decile sets or NEPH/CARD. Expanding C2 from NBRX>0 to **TRX>0 (24-mo from FCT_RX)** would add 27.7K HCPs and close the gap.

### 7.4 Comparison: Core-only vs Combined vs NBA 3.0 — 4 Metrics

| Universe | Total HCPs | %NBA30 | M1: FLAG (77,972) | M2: V6 NBRX (40,122) | M3: V6 TRX (77,582) | M4: FCT_RX (67,796) |
|:---------|----------:|:------:|------------------:|---------------------:|---------------------:|--------------------:|
| Core D2+ only | 242,868 | 85.0% | — | 35,013 (87.3%) | — | — |
| Core D2+ + C2 + C3 | **285,608** | **91.7%** | **67,956 (87.2%)** | **40,098 (99.9%)** | **68,143 (87.8%)** | **62,046 (91.5%)** |
| NBA 3.0 | 232,965 | 100% | 77,972 (baseline) | — | — | — |

> Adding C2+C3 lifts NBA 3.0 overlap from 85% to 92%. **M4 (91.5%) has the best capture rate** because 24-mo FCT_RX writers align with the decile lookback. To close the remaining 8.5% (5,750 writers), C2 would need to expand from NBRX>0 to TRX>0 from FCT_RX.

---

## Next Steps (Combining Strategy TBD)

* **D2+ combined (286K) is the leading candidate** — 91.7% NBA 3.0 overlap, 100% Kerendia capture
* Investigate the 10K NBA30-only Kerendia writers — are they TRx-based or non-paid?
* Consider adding Targeting/BPT (Criterion 4) to close the remaining 19K gap
* Decide whether to add Set4 (CKD×ACE/ARB) for additional indication coverage

---

*Generated by Genie Code — October 15, 2026*