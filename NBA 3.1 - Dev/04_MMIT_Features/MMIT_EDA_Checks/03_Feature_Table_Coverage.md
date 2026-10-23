# EDA Check 3 — Coverage of PA / ST / UDF / Derived-Field Tables

**Question:** For the formularies that carry a Kerendia status, how often do the candidate feature tables have a matching row?

**Status:** Formulary-level complete. Claim-weighted coverage (using the Step 3 winning formulary per payer x month) runs in notebook `MMIT_EDA_Claim_Level_Checks` (section 3).

**Base:** Kerendia (MedId 607231), CKD class, latest feed per formulary x period, periods 202510-202609. Joins on `FormularyId, Period`; PA / ST / UDF filtered to `IndicationName = 'Chronic Kidney Disease'`.

---

## 1. Coverage by period (% of Kerendia formularies)

| Period | Formularies | pa_v2 | st | pa_udf | derived_fields (CKD HPM) | restrictions |
|---|---|---|---|---|---|---|
| 202510 | 2,139 | 39.7 | 28.5 | 39.7 | 0.0 | 73.4 |
| 202511 | 2,133 | 41.0 | 31.9 | 41.0 | 0.0 | 74.0 |
| 202512 | 2,133 | 41.4 | 32.6 | 41.4 | 0.0 | 74.1 |
| 202601 | 2,133 | 43.6 | 36.4 | 43.6 | 100.0 | 74.4 |
| 202602 | 2,233 | 42.8 | 36.0 | 42.8 | 100.0 | 75.5 |
| 202603 | 2,036 | 41.5 | 36.1 | 41.5 | 100.0 | 73.7 |
| 202604 | 2,075 | 42.5 | 37.7 | 42.5 | 100.0 | 74.4 |
| 202605 | 2,058 | 43.0 | 37.9 | 43.0 | 100.0 | 74.2 |
| 202606 | 2,058 | 43.5 | 38.8 | 43.5 | 100.0 | 74.6 |
| 202607 | 2,080 | 43.7 | 39.1 | 43.7 | 100.0 | 75.1 |
| 202608 | 2,073 | 43.6 | 39.8 | 43.6 | 100.0 | 75.1 |
| 202609 | 2,073 | 44.0 | 40.3 | 44.0 | 100.0 | 75.5 |

## 2. Coverage by Kerendia status (202608)

| Status rollup | Formularies | pa_v2 | st | restrictions |
|---|---|---|---|---|
| Covered (PA/ST) | 753 | 70.1 | 63.6 | 100.0 |
| Preferred (PA/ST) | 631 | 59.3 | 54.5 | 100.0 |
| Preferred | 272 | 0.0 | 0.0 | 54.4 |
| Covered | 160 | 0.0 | 0.0 | 11.9 |
| Not Covered | 152 | 0.7 | 0.7 | 0.7 |
| Not Listed | 101 | 0.0 | 0.0 | 0.0 |
| Specialty (PA/ST) | 4 | 0.0 | 25.0 | 100.0 |

## 3. Interpretation

* **Missing is structural, not random.** PA / ST rows exist only when the drug is restricted, so a missing value usually means "no PA / no step". Encode missing as an explicit level (`No_PA`, `No_Step`) only when the status is unrestricted; otherwise use `Unknown`.
* **Detail gap for restricted formularies:** 30-40% of `(PA/ST)` formularies have no structured PA / ST row. Their only detail is the free text in `bronze_restrictions` (100% coverage for PA/ST). Features from pa_v2 / st need an `Unknown` level, or a text-parsed fallback from `RestrictionDetail`.
* `restrictions` is present for 54% of `Preferred` formularies, most likely QL (quantity limit) only, since PA / ST tables are empty for them (to verify by RestrictionCode in the notebook). It is a clean source for the `has_PA` / `has_ST` / `has_QL` flags.
* `pa_v2` and `pa_udf` have identical coverage, so they come from the same PA record and can be joined together.
* **Derived fields (Bayer HPM) are 100% complete from 202601** and absent before. Pre-202601 claims need a fallback (for example the 202601 value carried back, with an imputed flag).

## 4. Claim-weighted results (from notebook)

* Matched Kerendia claims in `202510`-`202608`: **1,209,617** (denominator for all percentages below).

Claim-weighted coverage on the winning `FormularyId + Period`:

| table | matched_claims_with_row | claim_weighted_coverage_pct |
| --- | --- | --- |
| bronze_pa_v2 | 613308 | 50.7 |
| bronze_st | 561503 | 46.42 |
| bronze_pa_udf | 613308 | 50.7 |
| bronze_derived_fields HPM | 876043 | 72.42 |
| bronze_restrictions | 1008994 | 83.41 |

Restriction-code mix for claims on raw `Preferred` Kerendia formularies (`n = 348,802` claims):

| restriction_mix | claims | pct_of_preferred_claims |
| --- | --- | --- |
| Any restriction row | 249692 | 71.59 |
| PA | 750 | 0.22 |
| ST | 1 | 0.0 |
| QL | 249668 | 71.58 |
| QL only | 248941 | 71.37 |

The claim weighting makes the structural patterns clearer: restrictions are available for most matched claims, PA/ST detail covers roughly half, and raw `Preferred` is overwhelmingly quantity-limit-only rather than PA/ST-driven.
