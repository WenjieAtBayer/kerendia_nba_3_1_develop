# NBA 3.0 Competitor NBRx Share Features: How They Are Built

Notebook reviewed: `03_HCP_Level_Features/31_Competitor_drugs_NBRX_share`. NBA 3.1 changes are in `10_competitor_nbrx_share_features_nba31_changes.md`.

## 1. How NBA 3.0 builds these features

### 1.0 What is this section about?

For every HCP and calendar month, the notebook tracks how many new prescriptions (NBRx) the HCP wrote for four competitor SGLT2 drugs — Farxiga, Invokana, Jardiance, and Steglatro — and what share each drug holds in that HCP's prescribing. The idea is that an HCP who already prescribes a lot of Jardiance is a well-identified SGLT2 user, while an HCP with a declining Farxiga share may be switching to alternatives.

| Feature type | Business question | Section |
| --- | --- | --- |
| 12-month rolling count | How many NBRx did the HCP write for each competitor drug in the last 12 months? | 1.2 |
| Percentage share | What fraction of the HCP’s total NBRx across these 4 drugs went to each one? | 1.3 |

### 1.1 Shared foundations

**Who is scored and on which date**

| Item | What it means | Last run |
| --- | --- | --- |
| HCP universe | Join key is `NPI_NUMBER` (not `PROVIDER_ID` as in the LAAD features). The LRx data provides NPI directly. | — |
| Grain | One row per NPI and calendar month with at least one qualifying Rx. `99_Combine_Physician_Data` joins on `NPI_NUMBER` + `SVC_DT_M` | Filter: `SVC_DT_M >= 2022-11-01` |
| Dates | All history from `KERENDIA_LAAD_BASED_LRX_V6` | Available from ~2019; LAAD projected NBRx data |

**Source table**

| Source | Table | One row is |
| --- | --- | --- |
| Projected Rx (LRx) | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | One HCP x week x product x many demographic slices (INDICATION_GROUP, SPECIALTY_GROUP, AGE_GROUP, PAY_TYPE, etc.) projected as NBRx / TRx / NRx |

**Key columns used**

| Column | What it means | Notes |
| --- | --- | --- |
| `NPI` | HCP identifier. Aliased to `NPI_NUMBER` | Not the same as LAAD `PROVIDER_ID` |
| `WEEK_ENDING_DATE` | End date of the IQVIA projection week | Converted to `PERIOD_ID` date, then truncated to month |
| `PERIOD_ID` | Date of the period (weekly data: PERIOD_TYPE = W) | Used for month truncation |
| `PRODUCT_GROUP` | Drug brand name group as labelled by IQVIA | Filtered with `LIKE '%FARXIGA%'` (brand + generic), exact match for others |
| `NBRX` | Projected New Brand Rx (new prescriptions, not refills) | `SUM(PROJECTED_NBRX)` after `SELECT DISTINCT` on many dimension columns |

**Products included**

| `{DRUG}` in feature name | IQVIA `PRODUCT_GROUP` values matched | Drug class | Status (Nov 2026) |
| --- | --- | --- | --- |
| `FARXIGA` | `FARXIGA BRAND`, `FARXIGA GENERICS` (via `LIKE '%FARXIGA%'`) | SGLT2 | Growing — generic launch driving volume up |
| `INVOKANA` | `INVOKANA` (exact), `CANAGLIFLOZIN_INVOKANA COMBOS` also matched | SGLT2 | Near-zero and declining |
| `JARDIANCE` | `JARDIANCE` (exact), `EMPAGLIFLOZIN_JARDIANCE COMBOS` also matched | SGLT2 | Dominant and stable |
| `STEGLATRO` | `STEGLATRO` (exact), `ERTUGLIFLOZIN_STEGLATRO COMBOS` also matched | SGLT2 | Near-zero and declining |

*Note:* the `LIKE '%FARXIGA%'` filter also matches `DAPAGLIFLOZIN_FARXIGA COMBOS` if such a group existed, but the notebook comment records that IQVIA renamed the product group in March 2024 to `COMBINED FARXIGA BRAND AND GENERIC`. In 2026 data the labels are `FARXIGA BRAND` and `FARXIGA GENERICS`. Both are captured by the LIKE filter.

**Important scope caveat**: The query pulls **all INDICATION_GROUP values** (T2D, CVD, HF, CKD, ALL_OTHERS, etc.), not only CKD-labelled Rx. In practice, most Jardiance and Farxiga volume is for T2D or T2D+CVD patients. Analysis of INDICATION_GROUP for Oct 2025–Sep 2026 shows that only ~15% of JARDIANCE NBRx and ~32% of FARXIGA NBRx carry a CKD-containing indication group.

---

### 1.2 Monthly NBRx count and 12-month rolling count

**a. Preprocessing steps**

1. **Null handling.** `PRODUCT_GROUP = NULL` or `'NULL'` is replaced with `'UNKNOWN'`. This is then pivoted to a column `TOTAL_NBRX_CLAIMS_UNKNOWN`, which is later dropped.
2. **Standardise Farxiga label.** Any `PRODUCT_GROUP LIKE '%FARXIGA%'` is relabelled to `'FARXIGA'` so all Farxiga rows pivot into one column.
3. **Monthly pivot.** Group by `NPI_NUMBER` + `SVC_DT_M`, pivot on `PRODUCT_GROUP`, `SUM(PROJECTED_NBRX)`. Fill with 0. Clean column names to `TOTAL_NBRX_CLAIMS_{DRUG}`.
4. **Subset columns.** Keep only the four drugs plus the total.
5. **Denominator.** `TOTAL_NBRX_CLAIMS = FARXIGA + INVOKANA + JARDIANCE + STEGLATRO` (sum of the four drugs only).
6. **Fill calendar.** `step2_fill_missing` fills every NPI’s missing months with empty (not 0). This crosses the full date span in the data.
7. **12-month rolling sum.** `step3_lag` with `last_i_month_list = [12]`. This helper uses `rowsBetween(-11, 0)` (12 months: the current plus the 11 before), so the `_IN_LAST_12_MONTH` column is a true 12-month sum. The raw monthly columns are then dropped (only the 12-month aggregates and percentages are kept in the final output).

**b. Features created (12-month rolling counts)**

| Feature | Business meaning | Example (Sep 2026) |
| --- | --- | --- |
| `TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` | Total NBRx for these 4 SGLT2s in the last 12 months | — |
| `TOTAL_NBRX_CLAIMS_FARXIGA_IN_LAST_12_MONTH` | Farxiga (brand + generic) NBRx in the last 12 months | — |
| `TOTAL_NBRX_CLAIMS_INVOKANA_IN_LAST_12_MONTH` | Invokana NBRx | Mostly 0 or very small |
| `TOTAL_NBRX_CLAIMS_JARDIANCE_IN_LAST_12_MONTH` | Jardiance NBRx | Largest drug in the set |
| `TOTAL_NBRX_CLAIMS_STEGLATRO_IN_LAST_12_MONTH` | Steglatro NBRx | Near-zero |

*Notes:*
- Running totals are also computed but a commented-out `drop` line suggests they were considered for removal. Whether they are in the output depends on the run.
- After `step3_lag`, `cols_to_drop` removes the raw monthly values before saving.

---

### 1.3 Percentage share features

Computed after `step3_lag` and after `fillna(0)`.

| Feature | Formula | Notes |
| --- | --- | --- |
| `PERC_FARXIGA_NBRX_SHARE` | `TOTAL_NBRX_CLAIMS_FARXIGA_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` | 0 when denominator = 0 |
| `PERC_JARDIANCE_NBRX_SHARE` | `TOTAL_NBRX_CLAIMS_JARDIANCE_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` | 0 when denominator = 0 |
| `PERC_INVOKANA_NBRX_SHARE` | `TOTAL_NBRX_CLAIMS_INVOKANA_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` | Near-zero for almost all HCPs |
| `PERC_STEGLATRO_NBRX_SHARE` | `TOTAL_NBRX_CLAIMS_STEGLATRO_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` | Near-zero for almost all HCPs |

These four shares sum to 1 (when the denominator is non-zero). `PERC_JARDIANCE` + `PERC_FARXIGA` account for nearly all of the total for almost every HCP by 2026.

---

### 1.4 What the final table looks like

| Output | Key columns | Contains |
| --- | --- | --- |
| `/Volumes/.../kerendia_nba_3_hcp_model_perc_competitor_nbrx_shares_for_inference` | `NPI_NUMBER`, `SVC_DT_M`, `PULL_DT` | 12-month counts (5) + percentage shares (4) + possibly running totals |

Filter applied: `SVC_DT_M >= 2022-11-01`. This means approximately 46 months of data per NPI.

---

### 1.5 Things to watch out for

1. **All indication groups, not CKD-specific.** The Rx pull does not filter `INDICATION_GROUP`. Most Jardiance and Farxiga volume is for T2D or T2D+CVD patients. The features therefore partly reflect a general SGLT2 prescriber profile, not just CKD use. A high Jardiance share signals an SGLT2-friendly HCP, but not necessarily one who uses it for CKD. Only ~15% of Jardiance and ~32% of Farxiga NBRx in 2025–2026 carry a CKD indication group.

2. **Denominator is only these 4 drugs.** The total does not include ACE inhibitors, ARBs, MRAs, or other CKD drugs. An HCP who prescribes these 4 drugs at low volume but has a large CKD practice gets a denominator close to zero and a share that is unstable.

3. **INVOKANA and STEGLATRO are near-zero and declining.** In 2025–2026, both contribute <1K NBRx/month across all HCPs nationally. Their shares inflate the denominator size check without adding signal. An HCP who had a high Invokana share in 2021 will have a near-zero value today and a near-zero share contribution.

4. **Static build — data leakage in training.** The notebook has no cohort or lookback filter. It processes all claims up to the pull date and saves one time-series output. `99_Combine_Physician_Data` joins on `NPI_NUMBER` + `SVC_DT_M`, so each training cohort gets the value for its scoring month — but the 12-month window for an early cohort still uses the same LRx table pull, which extends to the current date. This is the same leakage issue as the adoption features.

5. **`step2_fill_missing` fills the full calendar span.** Missing months get empty (null) values. `fillna(0)` is applied afterwards, so all NPI–month combinations in the table have 0 for months with no qualifying Rx.

6. **IQVIA projected data, not actual claims.** `NBRX` is IQVIA’s projected new brand prescriptions, which differs from actual fill counts. This is consistent with the prior-writing features (which also use this LRx table), but it differs from the LAAD-based Rx features used for the adoption and comorbidity features.

7. **ID is NPI, not PROVIDER_ID.** The other HCP features use LAAD PROVIDER_ID (except for the digital features which use BHID). The join in `99_Combine_Physician_Data` must map between IDs. If an NPI maps to multiple PROVIDER_IDs, the competitor feature will apply to all.

---

### 1.6 Importance in the NBA 3.0 model

The 752-feature Excel (`Final NBA 3.0 Modeling Features.xlsx`) was not checked against this notebook's output for this document. The feature names to search for are `PERC_FARXIGA_NBRX_SHARE`, `PERC_JARDIANCE_NBRX_SHARE`, `TOTAL_NBRX_CLAIMS_*_IN_LAST_12_MONTH`, and any running-total variants.

---

### 1.7 Data used

| Source | Path | Notes |
| --- | --- | --- |
| LRx table | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | PERIOD_TYPE = W (weekly); all indication groups |
| Output | `/Volumes/.../kerendia_nba_3_hcp_model_perc_competitor_nbrx_shares_for_inference` | Delta format |
