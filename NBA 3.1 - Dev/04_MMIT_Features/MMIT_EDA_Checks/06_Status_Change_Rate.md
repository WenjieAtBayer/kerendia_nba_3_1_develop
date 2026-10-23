# EDA Check 6 — Status Change Rate per Month (signal density for feature group E)

**Question:** How often does a formulary change its coverage status for Kerendia and its competitors? Is there enough signal for change and momentum features?

**Status:** Complete (formulary level). Claim-level exposure (share of Kerendia claims on a formulary that changed in the last 3 months) can be added in notebook `MMIT_EDA_Claim_Level_Checks` (section 4).

**Method:** Latest feed per `MedId x FormularyId x Period` from `bronze_statuses` (202510-202609). A change is when `UniversalStatusRollup` differs from the previous month on the same formulary. Direction uses an ordinal access rank: Preferred 6 > Covered 5 > Preferred (PA/ST) = Specialty 4 > Covered (PA/ST) 3 > Specialty (PA/ST) 2 > Not Listed 1 > Not Covered 0.

---

## 1. Kerendia (607231), month over month

| Period | Formularies | Changes | % changed | Improved | Worsened | Raw-status-only change |
|---|---|---|---|---|---|---|
| 202511 | 2,130 | 12 | 0.56 | 9 | 3 | 0 |
| 202512 | 2,133 | 3 | 0.14 | 3 | 0 | 0 |
| 202601 | 2,133 | 38 | 1.78 | 27 | 11 | 12 |
| 202602 | 2,133 | 70 | 3.28 | 46 | 24 | 33 |
| 202603 | 2,036 | 23 | 1.13 | 13 | 10 | 0 |
| 202604 | 2,036 | 18 | 0.88 | 9 | 9 | 2 |
| 202605 | 2,058 | 10 | 0.49 | 7 | 3 | 2 |
| 202606 | 2,058 | 12 | 0.58 | 5 | 7 | 4 |
| 202607 | 2,058 | 21 | 1.02 | 19 | 2 | 1 |
| 202608 | 2,073 | 9 | 0.43 | 8 | 1 | 0 |
| 202609 | 2,073 | 16 | 0.77 | 6 | 10 | 0 |
| **Total** | | **232** | | **152** | **80** | **54** |

"Raw-status-only change" = the tier or raw label changed while the rollup stayed the same (for example Tier 3 -> Tier 2 within Preferred (PA/ST)). This is invisible to the current pipeline.

## 2. Formularies with at least one rollup change (11 months)

| Drug | MedId | 0 changes | 1 | 2 | 3+ | % changed |
|---|---|---|---|---|---|---|
| Kerendia | 607231 | 2,082 | 193 | 18 | 1 | 9.2% |
| Jardiance | 582254 | 2,081 | 176 | 37 | 0 | 9.3% |
| Farxiga | 580683 | 1,549 | 649 | 80 | 16 | **32.5%** |
| Invokana | 577710 | 2,162 | 119 | 12 | 1 | 5.8% |
| Steglatro | 595221 | 2,191 | 90 | 12 | 1 | 4.5% |

## 3. Findings

* **Kerendia access is improving.** Improvements outnumber deteriorations about 2:1 (152 vs 80). The most common moves (from `silver_status_changes`) are Covered (PA/ST) -> Preferred (PA/ST) and Not Covered -> Preferred (PA/ST).
* **Plan-year seasonality:** Kerendia and Jardiance changes peak in 202601-202602 (January formulary resets).
* **Farxiga is the outlier:** 321 changes in 202607, 304 of them deteriorations (15.6% of formularies in one month), continuing from 202604-202606. This is consistent with formularies moving brand Farxiga down after generic dapagliflozin became available (inferred; to be confirmed). This is a material competitive event for Kerendia's SGLT2 co-therapy context.
* **Signal density is sparse per month** for Kerendia (0.4-3.3% of formularies), but about 9% of formularies change at least once. Rolling windows (L3M / L6M) are needed; single-month change flags will be mostly zero.
* `silver_status_changes` records changes at **weekly** feed granularity (270 Kerendia CKD rows including raw-only changes, 31 already in 202510). It catches changes inside a month that the monthly snapshot misses. Prefer it for change features, aggregated to month.

## 4. Recommended features (claim level, aggregated to HCP x month)

* `kerendia_status_changed_l3m`, `kerendia_status_improved_l3m`, `kerendia_status_worsened_l3m` (rollup-based)
* `kerendia_tier_changed_l3m` (raw-only changes)
* `farxiga_status_worsened_l3m`, `jardiance_status_worsened_l3m` (competitor events)
* `months_since_kerendia_status_change` (capped at 12, with a separate `no_change_observed` flag because the history is only 12 months)

**Caveat:** the history starts at 202510, so L3M features are only complete from 202601 and L6M from 202604.

## 5. Claim-level exposure (from notebook)

Claim-weighted exposure to L3M status changes on the winning formulary (`202601`-`202608`):

| claim_month | kerendia_changed_l3m_pct | kerendia_improved_l3m_pct | kerendia_worsened_l3m_pct | farxiga_worsened_l3m_pct |
| --- | --- | --- | --- | --- |
| 202601 | 1.83 | 1.74 | 0.09 | 1.62 |
| 202602 | 2.44 | 2.15 | 0.29 | 1.65 |
| 202603 | 2.85 | 2.52 | 0.34 | 1.68 |
| 202604 | 0.95 | 0.8 | 0.25 | 1.39 |
| 202605 | 0.94 | 0.9 | 0.04 | 3.11 |
| 202606 | 0.88 | 0.75 | 0.13 | 5.76 |
| 202607 | 0.71 | 0.64 | 0.07 | 33.46 |
| 202608 | 0.66 | 0.57 | 0.08 | 33.39 |

At claim level, Kerendia's own recent change exposure remains sparse but present, while competitor deterioration becomes concentrated in Farxiga-heavy months, especially 202607-202608.
