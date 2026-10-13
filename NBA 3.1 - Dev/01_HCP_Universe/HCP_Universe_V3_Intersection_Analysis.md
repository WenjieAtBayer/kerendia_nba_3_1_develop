# NextGen NBA 3.1 — HCP Universe v3 Analysis (Product-Class Decile Intersection)

**Date:** October 13, 2026  
**Notebook Reference:** `01_HCP_Universe/03_HCP_Universe_Identification_v3`  
**Approach:** Per-product-class **TRx cumulative decile** computation → **Intersection** of all 5 Decile 2+ sets  
**Lookback Window:** Oct '24 – Sep '26  
**Output Path:** `kerendia_nba_3_hcp_universe_v3` (Delta)

---

## 6. Proposed NBA 3.1 Updated HCP Universe (v3 — Intersection)

### 6.1 Methodology

Instead of filtering by indication group (v2), v3 computes **independent deciles within each product class** and intersects the Decile 2+ sets.

**Logic:**
1. For each of **SGLT2, GLP1, ACE, ARB, sMRA**: count TRx (claims) per PROVIDER_ID within that class from `pt_lvl_trx`
2. Rank into deciles via **cumulative TRx** (each decile holds ~10% of total TRx volume) — matching v1/NBA 3.0 methodology
3. Keep Decile 2+
4. **Intersect** — only HCPs who are Decile 2+ in **all 5** product classes simultaneously

This creates a **focused core** of multi-class prescribers — HCPs who meaningfully prescribe across all 5 Kerendia-relevant drug classes.

#### Decile Methodology

| Aspect | v1 (NBA 3.0) | v3 (This notebook) |
|:-------|:-------------|:--------------------|
| **Metric** | TRx (each claim = 1 TRx) | **TRx** (each claim = 1 TRx) — **same as v1** |
| **Decile method** | Cumulative TRx-based (~10% of total TRx volume per decile) | **Cumulative TRx-based** — **same as v1** |
| **Source table** | `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake) | `pt_lvl_trx` (Unity Catalog) |
| **Decile scope** | Single pool: all SGLT2/GLP1 combined | **Per-class**: independent decile within each of the 5 product classes |

> **v3 now matches v1's metric and method** (cumulative TRx-based decile). The only structural difference is that v1 pools SGLT2/GLP1 into a single decile, while v3 computes independent deciles per product class.

### 6.2 New Selection Criteria

| # | Criterion | Source | Description |
|---|-----------|--------|-------------|
| 1 | **Product-Class Intersection (Decile 2+)** | `lrx_nbrx` | HCPs who are Decile 2+ in ALL of SGLT2, GLP1, ACE, ARB, sMRA simultaneously |
| 2 | **Kerendia Writers** | `lrx_nbrx` | All HCPs prescribing Kerendia (`PRODUCT_CLASS = 'KERENDIA'`) in complete history |
| 3 | **Specialty HCPs** | `lrx_nbrx` (`SPECIALTY_GROUP`) | All NEPH, CARD, ENDO, PCP, and HOSPITALIST HCPs |
| 4 | **Targeting & BPT HCPs** | `CP_KER_HCP` | All HCPs in BPT or Targeting List (unchanged) |

### 6.3 Per-Product-Class Decile 2+ Counts

| Product Class | Total HCPs | Decile 2+ | Dropped (D1) |
|:-------------|----------:|----------:|-------------:|
| SGLT2 | 599,436 | 193,076 | 406,360 |
| GLP1 | 569,830 | 169,333 | 400,497 |
| ACE | 937,660 | 222,201 | 715,459 |
| ARB | 934,702 | 215,161 | 719,541 |
| sMRA | 774,522 | 252,651 | 521,871 |

> Cumulative TRx deciling is much more aggressive than ntile: D1 absorbs ~68–77% of HCPs (low-volume prescribers contributing <10% of total TRx). ACE and ARB have the largest prescriber pools (~935K each). sMRA retains the most D2+ HCPs (253K).

### 6.4 Pairwise Overlap Between Product Classes (Decile 2+)

| Pair | Overlap | % of Smaller Set |
|:-----|--------:|:----------------:|
| SGLT2 ∩ GLP1 | 134,090 | 79.2% |
| SGLT2 ∩ ACE | 164,380 | 85.1% |
| SGLT2 ∩ ARB | 165,341 | 85.6% |
| SGLT2 ∩ sMRA | 151,718 | 78.6% |
| GLP1 ∩ ACE | 147,650 | 87.2% |
| GLP1 ∩ ARB | 145,605 | 86.0% |
| GLP1 ∩ sMRA | 127,500 | 75.3% |
| ACE ∩ ARB | 193,874 | 90.1% |
| ACE ∩ sMRA | 165,831 | 74.6% |
| ARB ∩ sMRA | 167,447 | 77.8% |

> ACE ∩ ARB is the tightest pair (90.1%). ACE ∩ sMRA is the loosest (74.6%).

### 6.5 Intersection vs Union

| Metric | Count |
|:-------|------:|
| **Intersection** (all 5 Decile 2+) | **102,122** |
| Union (any 1 Decile 2+) | 334,204 |
| Intersection / Union ratio | 30.6% |

> The intersection is a highly targeted 102K-HCP core — only those prescribing meaningfully across all 5 drug classes.

### 6.6 Criterion Counts & Universe Size

| # | Criterion | HCPs | % of Universe |
|---|-----------|-----:|:-------------:|
| 1 | Product-Class Union (Decile 2+) | 334,204 | 39.6% |
| 2 | Kerendia Writers | 53,548 | 6.4% |
| 3 | Specialty HCPs | 809,802 | 96.0% |
| 4 | Targeting & BPT HCPs | 78,389 | 9.3% |
| | **Total HCP Universe v3 (TRx, Union-based)** | **843,208** | — |

> With TRx cumulative deciling, the product-class union (334K) is more selective than NBRX ntile (912K). **Specialty HCPs still dominate at 96.0%** but the product-class criterion is now a meaningful contributor at 39.6%.

### 6.7 Enhanced Output Schema

| Column | Type | Description |
|:-------|:-----|:------------|
| `PROVIDER_ID` | string | Unique HCP identifier |
| `SGLT2_DECILE` | int | SGLT2 TRx cumulative decile (1–10, 0 if no SGLT2 prescribing) |
| `GLP1_DECILE` | int | GLP1 TRx cumulative decile |
| `ACE_DECILE` | int | ACE TRx cumulative decile |
| `ARB_DECILE` | int | ARB TRx cumulative decile |
| `SMRA_DECILE` | int | sMRA TRx cumulative decile |
| `PRODUCT_CLASS_INTERSECTION_FLAG` | int | 1 if HCP is Decile 2+ in all 5 classes |
| `KERENDIA_FLAG` | int | 1 if HCP prescribes Kerendia |
| `NEPH_FLAG` | int | 1 if Nephrologist |
| `CARD_FLAG` | int | 1 if Cardiologist |
| `ENDO_FLAG` | int | 1 if Endocrinologist |
| `PCP_FLAG` | int | 1 if Primary Care Physician |
| `HOSPITALIST_FLAG` | int | 1 if Hospitalist |
| `SPECIALTY_HCP_FLAG` | int | 1 if any target specialty |
| `TARGETING_HCP_FLAG` | int | 1 if in Targeting list |
| `BPT_HCP_FLAG` | int | 1 if in BPT list |
| `PULL_DT` | string | Data pull date |

---

## 7. v1 vs v2 vs v3 (Intersection) Comparison

### 7.1 Headline Comparison

| Version | Approach | Universe Size |
|:--------|:---------|-------------:|
| v1 | Product-based (SGLT2/GLP1 Decile 2+) | 232,965 |
| v2 | Indication-based (T1D/T2D/CKD/HF Decile 2+) | 1,086,478 |
| **v3 (TRx Intersection)** | **Per-class TRx cumulative decile (all 5 Decile 2+)** | **843,208** |

### 7.2 Cross-Version Overlap

| Comparison | Overlap | % of v3 | % of that version |
|:-----------|--------:|:-------:|:-----------------:|
| v3 ∩ v1 | 231,344 | 27.4% | **99.3% of v1** |
| v3 ∩ v2 | 838,718 | 99.5% | **77.2% of v2** |

```
  v1 (233K)       v3 TRx Union (843K)           v2 (1.09M)
  ┌─────────┐     ┌────────────────────┐     ┌──────────────────────┐
  │ 1,621   │     │                    │     │                      │
  │(v1-only)│     │                    │     │    247,760            │
  ├─────────┼─────┤    843,208         ├─────┤    (v2-only,          │
  │ 231,344 │     │                    │     │     not in v3)         │
  │(overlap)│     │                    │     │                      │
  └─────────┘     └────────────────────┘     └──────────────────────┘
```

**Key observations:**
- **99.3% of v1** is retained in v3 — virtually no v1 HCPs lost
- **99.5% of v3 overlaps with v2** — v3 is nearly a subset of v2
- v3 (843K) sits between v1 (233K) and v2 (1.09M) in size
- The specialty criterion (810K) dominates the universe; the product-class union (334K) provides a meaningful additional dimension at 39.6%

### 7.3 Flag Composition

| Flag | Count | % of Universe |
|:-----|------:|:-------------:|
| SPECIALTY HCP | 809,802 | 96.0% |
| PCP | 722,285 | 85.7% |
| PRODUCT CLASS UNION | 334,204 | 39.6% |
| TARGETING HCP | 78,389 | 9.3% |
| BPT HCP | 78,389 | 9.3% |
| KERENDIA | 53,548 | 6.4% |
| CARD | 51,666 | 6.1% |
| NEPH | 15,048 | 1.8% |
| ENDO | 13,371 | 1.6% |
| HOSPITALIST | 7,432 | 0.9% |

---

## 8. Assessment & Recommendations

### Strengths
- **TRx cumulative decile matches v1/NBA 3.0 methodology**: Consistent metric (TRx) and method (cumulative volume-based decile) across versions
- **More selective D2+ threshold**: Cumulative TRx decile concentrates many low-volume HCPs into D1, producing a more targeted D2+ pool (102K intersection, 334K union) vs NBRX ntile (247K/912K)
- **99.3% v1 retention**: Nearly perfect backwards compatibility
- **Per-class TRx deciles**: Each HCP carries 5 individual decile scores, enabling granular downstream tiering
- **Intersection core (102K)**: The all-5-class intersection identifies a premium cohort of high-volume multi-class prescribers

### Weaknesses
- **More aggressive exclusion**: Cumulative TRx D1 drops ~68–77% of HCPs per class (vs ~10% with ntile), which may exclude some clinically relevant HCPs
- **Loses 23% of v2**: 248K v2 HCPs are dropped — needs validation whether these are low-value or clinically relevant
- **Criterion 1 more meaningful but still secondary**: Product-class union (39.6%) contributes more than before but specialty HCPs (96%) still dominate

### When to Use
- When a **targeted, high-confidence** universe is preferred over breadth
- When downstream models benefit from HCPs with multi-class prescribing breadth as a signal
- When the specialty criterion (NEPH/CARD/ENDO/PCP/HOSPITALIST) is the primary capture mechanism and the product-class intersection serves as a **quality enrichment layer**

---

## 9. Next Steps

- [ ] Compare Kerendia writer coverage: how many of the 53,548 writers fall in the intersection vs specialty-only?
- [ ] Validate downstream model performance with v3 intersection universe
- [ ] Consider relaxing to 3-of-5 or 4-of-5 intersection instead of full 5-of-5
- [ ] Compare with v3 Union approach (see `HCP_Universe_V3_Union_Analysis.md`)

---

*Generated by Genie Code — October 13, 2026*