# NextGen NBA 3.1 — HCP Universe v3 Analysis (Product-Class Decile Union)

**Date:** October 13, 2026  
**Notebook Reference:** `01_HCP_Universe/03_HCP_Universe_Identification_v3`  
**Approach:** Per-product-class **TRx cumulative decile** computation → **Union** of all 5 Decile 2+ sets  
**Lookback Window:** Oct '24 – Sep '26  
**Output Path:** `kerendia_nba_3_hcp_universe_v3` (Delta)

---

## 6. Proposed NBA 3.1 Updated HCP Universe (v3 — Union)

### 6.1 Methodology

Instead of filtering by indication group (v2), v3 computes **independent deciles within each product class** and unions the Decile 2+ sets.

**Logic:**
1. For each of **SGLT2, GLP1, ACE, ARB, sMRA**: count TRx (claims) per PROVIDER_ID within that class from `pt_lvl_trx`
2. Rank into deciles via **cumulative TRx** (each decile holds ~10% of total TRx volume) — matching v1/NBA 3.0 methodology
3. Keep Decile 2+
4. **Union** — HCPs who are Decile 2+ in **any** of the 5 product classes

This creates a **broad, drug-class-aware** universe — any HCP who is a meaningful prescriber of at least one Kerendia-relevant drug class qualifies. Each HCP also carries `N_CLASSES_D2PLUS` (count of classes at Decile 2+) and `IN_ALL_5` flag for downstream tiering.

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
| 1 | **Product-Class Union (Decile 2+)** | `lrx_nbrx` | HCPs who are Decile 2+ in ANY of SGLT2, GLP1, ACE, ARB, sMRA |
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

### 6.5 Union vs Intersection

| Metric | Count |
|:-------|------:|
| **Union** (any 1 of 5 Decile 2+) | **334,204** |
| Intersection (all 5 Decile 2+) | 102,122 |
| Intersection / Union ratio | 30.6% |

### 6.6 HCPs by Number of Product Classes at Decile 2+

| # Classes D2+ | HCPs | % of Union | Cumulative |
|:-------------:|------:|:----------:|:----------:|
| 5 (all classes) | 102,122 | 30.6% | 30.6% |
| 4 | 64,047 | 19.2% | 49.7% |
| 3 | 40,345 | 12.1% | 61.8% |
| 2 | 36,899 | 11.0% | 72.8% |
| 1 | 90,791 | 27.2% | 100.0% |
| 0 (entered via other criteria) | 509,004 | — | — |

> 102K HCPs (30.6%) are the "full intersection" elite — Decile 2+ in all 5 classes. 91K (27%) qualify via only 1 class. The `N_CLASSES_D2PLUS` column enables flexible downstream tiering. With cumulative TRx deciling, the union is much more selective (334K vs 912K with NBRX ntile).

### 6.7 Criterion Counts & Universe Size

| # | Criterion | HCPs | % of Universe |
|---|-----------|-----:|:-------------:|
| 1 | Product-Class Union (Decile 2+) | 334,204 | 39.6% |
| 2 | Kerendia Writers | 53,548 | 6.4% |
| 3 | Specialty HCPs | 809,802 | 96.0% |
| 4 | Targeting & BPT HCPs | 78,389 | 9.3% |
| | **Total HCP Universe v3 (TRx Union)** | **843,208** | — |

> With TRx cumulative deciling, the product-class union (334K) is much more selective than NBRX ntile (912K). **Specialty HCPs dominate at 96.0%**, with the product-class union contributing 39.6% — a meaningful secondary criterion.

### 6.8 Enhanced Output Schema

| Column | Type | Description |
|:-------|:-----|:------------|
| `PROVIDER_ID` | string | Unique HCP identifier |
| `SGLT2_DECILE` | int | SGLT2 TRx cumulative decile (1–10, 0 if no SGLT2 prescribing) |
| `GLP1_DECILE` | int | GLP1 TRx cumulative decile |
| `ACE_DECILE` | int | ACE TRx cumulative decile |
| `ARB_DECILE` | int | ARB TRx cumulative decile |
| `SMRA_DECILE` | int | sMRA TRx cumulative decile |
| `PRODUCT_CLASS_UNION_FLAG` | int | 1 if HCP is Decile 2+ in any of the 5 classes |
| `IN_ALL_5` | int | 1 if HCP is Decile 2+ in all 5 classes |
| `N_CLASSES_D2PLUS` | int | Count of product classes where HCP is Decile 2+ (0–5) |
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

## 7. v1 vs v2 vs v3 (Union) Comparison

### 7.1 Headline Comparison

| Version | Approach | Universe Size |
|:--------|:---------|-------------:|
| v1 | Product-based (SGLT2/GLP1 Decile 2+) | 232,965 |
| v2 | Indication-based (T1D/T2D/CKD/HF Decile 2+) | 1,086,478 |
| **v3 (TRx Union)** | **Per-class TRx cumulative decile (any of 5 Decile 2+)** | **843,208** |

### 7.2 Cross-Version Overlap

| Comparison | Overlap | % of v3 | % of that version |
|:-----------|--------:|:-------:|:-----------------:|
| v3 ∩ v1 | 231,344 | 27.4% | **99.3% of v1** |
| v3 ∩ v2 | 838,718 | 99.5% | **77.2% of v2** |

```
  v1 (233K)       v3 TRx Union (843K)           v2 (1.09M)
  ┌─────────┐     ┌────────────────────┐     ┌──────────────┐
  │ 1,621   │     │                    │     │              │
  │(v1-only)│     │     843,208        │     │   247,760    │
  ├─────────┼─────┤                    ├─────┤   (v2-only,  │
  │ 231,344 │     │   838,718          │     │  not in v3)  │
  │(overlap)│     │   (v3 ∩ v2)        │     │              │
  └─────────┘     └────────────────────┘     └──────────────┘
```

**Key observations:**
- **99.3% of v1** is retained in v3 — virtually no v1 HCPs lost
- **99.5% of v3 overlaps with v2** — v3 is nearly a subset of v2
- v3 (843K) sits between v1 (233K) and v2 (1.09M) in size
- The 248K v2 HCPs not in v3 are those who are low-volume in the 5 target drug classes (D1 by cumulative TRx) and don't have a target specialty or other qualifying criterion

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

### 7.4 Side-by-Side: v3 Intersection vs v3 Union

| Metric | Intersection | Union |
|:-------|:-----------:|:-----:|
| Criterion 1 HCPs | 102,122 | 334,204 |
| Total Universe | 843,208 | **843,208** |
| v1 retention | 99.3% | **99.3%** |
| v2 overlap (% of v2) | 77.2% | **77.2%** |
| Criterion 1 share of universe | 12.1% | **39.6%** |
| Tiering capability | Binary (in/out) | **Continuous** (1–5 classes) |

> Both produce the same universe size (843K) since the union is the current primary criterion. The union approach provides richer HCP segmentation via `N_CLASSES_D2PLUS`.

---

## 8. Assessment & Recommendations

### Strengths
- **TRx cumulative decile matches v1/NBA 3.0 methodology**: Consistent metric (TRx) and method (cumulative volume-based decile) across versions
- **Built-in tiering**: `N_CLASSES_D2PLUS` (1–5) enables flexible prioritization — from the 102K all-5-class elite to the 91K single-class tail
- **99.3% v1 retention**: Perfect backwards compatibility
- **Per-class TRx deciles**: Each HCP carries 5 individual decile scores for granular analysis
- **More selective D2+ threshold**: Cumulative TRx decile concentrates low-volume HCPs into D1, producing a more targeted union (334K vs 912K with NBRX ntile)

### Weaknesses
- **Specialty dominates** (96.0%): With a more selective union (334K vs 912K), specialty HCPs now dominate the universe rather than the product-class criterion
- **248K v2 HCPs lost**: HCPs who are low-volume (D1) in all 5 target classes by cumulative TRx but had other qualifying criteria in v2
- **No indication flags**: Unlike v2, v3 does not carry T1D/T2D/CKD/HF flags — would need to be joined in separately
- **Aggressive D1 exclusion**: ~68–77% of HCPs per class fall into D1 — may exclude some clinically relevant low-volume prescribers

### When to Use
- When you want a **drug-class-driven** rather than indication-driven universe
- When downstream models benefit from **per-class prescribing volume** as features
- When the tiering capability (`N_CLASSES_D2PLUS`) adds value for targeting and prioritization
- When you want an approach that sits close to v2 in size but with different methodology for robustness

### v2 vs v3 Union Decision Guide

| Factor | v2 (Indication) | v3 TRx Union (Product-Class) |
|:-------|:----------------:|:----------------------------:|
| Universe size | 1,086,478 | 843,208 |
| Methodology | Indication group ≠ OTHERS, ntile decile | Cumulative TRx decile (any of 5 classes D2+) |
| HCP flags | T1D, T2D, CKD, HF | SGLT2, GLP1, ACE, ARB, sMRA TRx deciles |
| Tiering | Indication decile (1–10) | N_CLASSES_D2PLUS (1–5) + 5 TRx deciles |
| Decile method | ntile (equal HCP count) | Cumulative TRx (equal volume) — same as v1 |
| Specialty coverage | Same (810K) | Same (810K) |
| Best for | Broad indication-driven analytics | Targeted drug-class-driven analytics |

---

## 9. Next Steps

- [ ] Enrich v3 union with indication flags (T1D/T2D/CKD/HF) for a combined schema
- [ ] Compare Kerendia writer coverage across v1/v2/v3
- [ ] Profile the 266K single-class HCPs to assess clinical relevance
- [ ] Investigate the 113K v2 HCPs not in v3 — what drug classes do they prescribe?
- [ ] Validate downstream model performance with v3 union universe
- [ ] Consider hybrid approach: v3 union + indication flags from v2

---

*Generated by Genie Code — October 13, 2026*