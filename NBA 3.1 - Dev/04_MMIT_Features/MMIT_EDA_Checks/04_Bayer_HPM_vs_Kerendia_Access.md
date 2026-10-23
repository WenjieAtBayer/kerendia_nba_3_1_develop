# EDA Check 4 — Bayer CKD HPM Status vs Current `kerendia_access`

**Question:** Is the Bayer-specific field `Bayer_ChronicKidneyDisease_HPM_Pharm` (`bronze_derived_fields`) consistent with the `UniversalStatusRollup` the pipeline uses today, and does it add information?

**Status:** Formulary-level complete (202608). Claim-weighted cross-tab against `kerendia_access` runs in notebook `MMIT_EDA_Claim_Level_Checks` (section 4).

**Base:** Kerendia, CKD class, latest feed per formulary for Period 202608; HPM latest feed for the same formulary and period. 2,073 formularies, all matched.

---

## 1. Cross-tab (formularies)

| UniversalStatusRollup | -> pipeline `kerendia_access` | Bayer CKD HPM | Formularies |
|---|---|---|---|
| Preferred | Covered | Preferred -Unrestricted | 255 |
| Preferred | Covered | APR | 17 |
| Covered | Covered | **Preferred -Unrestricted** | 119 |
| Covered | Covered | Covered -Unrestricted | 41 |
| Preferred (PA/ST) | Covered_with_PA_ST | Preferred (PA to Label) | 307 |
| Preferred (PA/ST) | Covered_with_PA_ST | APR | 126 |
| Preferred (PA/ST) | Covered_with_PA_ST | Preferred (PA Unspecified) | 123 |
| Preferred (PA/ST) | Covered_with_PA_ST | Preferred (Step[s]) | 73 |
| Preferred (PA/ST) | Covered_with_PA_ST | Preferred (PA+) | 2 |
| Covered (PA/ST) | Covered_with_PA_ST | Covered (Step[s]) | 328 |
| Covered (PA/ST) | Covered_with_PA_ST | Covered (PA Unspecified) | 220 |
| Covered (PA/ST) | Covered_with_PA_ST | Covered (PA to Label) | 174 |
| Covered (PA/ST) | Covered_with_PA_ST | APR | 22 |
| Covered (PA/ST) | Covered_with_PA_ST | Covered (PA+) | 9 |
| Specialty (PA/ST) | Specialty_with_PA_ST | Covered (PA Unspecified) / APR | 3 / 1 |
| Not Covered | Not_Covered | Medical Exception | 152 |
| Not Listed | Not_Listed | Unknown | 101 |

## 2. Findings

* **Consistent at the coarse level.** No HPM value contradicts the restricted / unrestricted / not covered split. Not Covered maps 1:1 to `Medical Exception`, and Not Listed maps 1:1 to `Unknown`.
* **HPM adds restriction type** inside `Covered_with_PA_ST` (1,384 formularies, 67%). The value meanings below are inferred from the labels and should be confirmed with Bayer Market Access:
  * `PA to Label` (481): PA that only requires the FDA label criteria (low burden).
  * `Step[s]` (401): step therapy required.
  * `PA Unspecified` (343): PA without a documented criteria set.
  * `PA+` (11): PA beyond label (high burden).
  * `APR` (148, plus 17 on unrestricted Preferred): the meaning of this code is not documented in the table. Confirm with MMIT / Bayer Market Access before using it.
* **Preferred tier disagreement:** 119 formularies (74% of `Covered`) are `Covered` in the universal rollup but `Preferred -Unrestricted` in Bayer HPM. Bayer's taxonomy is more favorable on these plans. This matters for D2 (Preferred vs Covered); align on which source is the truth.
* Coverage: HPM is available from **202601** only (see Check 3).

## 3. Recommended feature

`kerendia_ckd_hpm_group` (claim-level), counted per HCP x month:

| Group | HPM values |
|---|---|
| Unrestricted_Preferred | Preferred -Unrestricted |
| Unrestricted_Covered | Covered -Unrestricted |
| PA_to_Label | Preferred / Covered (PA to Label) |
| PA_Unspecified | Preferred / Covered (PA Unspecified) |
| PA_Plus | Preferred / Covered (PA+) |
| Step | Preferred / Covered (Step[s]) |
| APR | APR |
| Medical_Exception | Medical Exception |
| Unknown | Unknown / missing |

Keep the Preferred / Covered prefix as a separate binary (`hpm_is_preferred`) so restriction type and tier can be tested independently.

## 4. Claim-weighted results (from notebook)

* Matched claims in `202601`-`202608`: **876,043**

Claim-weighted cross-tab of `kerendia_access x kerendia_ckd_hpm_group`:

| kerendia_access | ckd_hpm_group | count | claim_share_pct |
| --- | --- | --- | --- |
| Covered | Other | 226055 | 25.8 |
| Covered | Unrestricted | 75782 | 8.65 |
| Covered | APR | 377 | 0.04 |
| Covered_with_PA_ST | Other | 410952 | 46.91 |
| Covered_with_PA_ST | PA_to_Label | 76651 | 8.75 |
| Covered_with_PA_ST | APR | 39101 | 4.46 |
| Covered_with_PA_ST | PA_Unspecified | 17332 | 1.98 |
| Covered_with_PA_ST | Step | 15092 | 1.72 |
| Covered_with_PA_ST | PA_Plus | 296 | 0.03 |
| Not_Covered | Medical_Exception | 9310 | 1.06 |
| Not_Listed | Unknown | 4863 | 0.56 |
| Specialty_with_PA_ST | Other | 199 | 0.02 |
| Specialty_with_PA_ST | PA_Unspecified | 33 | 0.0 |

At claim level, the same pattern holds as the formulary snapshot: most volume sits in `Covered_with_PA_ST`, and Bayer HPM mainly refines that bucket into `PA_to_Label`, `APR`, `PA_Unspecified`, and `Step` rather than contradicting the existing access rollup.
