# Feature Analysis — NBA 3.1 Index

This folder documents the HCP-level model feature families for Kerendia NBA 3.1, analysing how each was built in NBA 3.0, what the data shows over the last two years, and what changes or additions are planned for 3.1. Each feature family has a pair of files: an **analysis** file (how NBA 3.0 builds it) and a **changes** file (what NBA 3.1 does differently).

The companion file `90_competitor_comorbidity_summary_and_trends.md` is the cross-cutting summary for the two families most closely tied to the indication landscape: competitor drug prescribing and comorbidity (patient panel) features.

---

## File Map

| # | File | What it covers | Notebook |
| --- | --- | --- | --- |
| 01 | `01_comorbidity_dx_features_analysis.md` | How NBA 3.0 builds the claim comorbidity features: monthly kidney-patient counts, rolling averages, running totals, group shares (KD / DB-KD / CV-KD) | `09_claim_comorbidity` |
| 02 | `02_comorbidity_dx_features_nba31_changes.md` | NBA 3.1 changes: drop redundant windows; rebuild on fixed cohort windows; add indication-mix (T2D+CKD, T1D+CKD, HF), CKD stage shares, and growth log-ratio | `09_claim_comorbidity` (to be rebuilt) |
| 03 | `03_adoption_speed_features_analysis.md` | How NBA 3.0 builds the adoption-speed features: minimum days from patient CKD diagnosis to first Invokana or Farxiga Rx (same-HCP pair) | `11_adoption_features_inv_far` |
| 04 | `04_adoption_speed_features_nba31_changes.md` | NBA 3.1 changes: three feature variants × five drug groups (Farxiga, Invokana, Jardiance, steroidal MRA, Entresto); fix static build; include any-provider CKD date | `11_adoption_features` (new) |
| 05 | `05_iqvia_channel_features_analysis.md` | How NBA 3.0 builds the IQVIA pharmacy-channel features: patient fill-days in retail / mail / LTC / atypical channels for the CKD basket (one month only) | `23_IQVIA_channel_features` |
| 06 | `06_iqvia_channel_features_nba31_changes.md` | NBA 3.1 changes and whether to keep this notebook at all (its features are superseded by `1_Additional_HCP_level_features`) | `23_IQVIA_channel_features` |
| 07 | `07_prior_writing_features_analysis.md` | How NBA 3.0 builds the prior-writing features: Kerendia NBRx counts and trends, new-writer flag, NPS | `10_kerendia_prior_writing`, `26/27/28_Features_*Rx` |
| 08 | `08_prior_writing_features_nba31_changes.md` | NBA 3.1 changes: indication-split NBRx, new-writer signal for HF and T1D cohorts | (to be documented) |
| 09 | `09_competitor_nbrx_share_features_analysis.md` | **NEW.** How NBA 3.0 builds the competitor NBRx share features: monthly shares of Farxiga / Invokana / Jardiance / Steglatro in the HCP's prescribing | `31_Competitor_drugs_NBRX_share` |
| 10 | `10_competitor_nbrx_share_features_nba31_changes.md` | **NEW.** NBA 3.1 changes: fix indication scope, denominator, cohort logic, and drug list | `31_Competitor_drugs_NBRX_share` (to be rebuilt) |
| — | `NBA_3_1_HCP_Feature_Recommendations.xlsx` | Cross-family tracker of all proposed feature changes. Not renamed (binary). | — |
| 90 | `90_competitor_comorbidity_summary_and_trends.md` | **NEW.** Summary across the competitor and comorbidity families: NBA 3.0 status, 2-year market trend data, data-quality gaps, and a prioritised NBA 3.1 improvement list | Both families |
| 91 | `91_josh_briefing_competitor_comorbidity.md` | Plain-language briefing for Josh Buffington (CI). Section 9 holds the Nov 2026 meeting decisions | Both families + market events |
| 92 | `92_competitor_comorbidity_nba31_readiness_plan.md` | NBA 3.1 readiness plan: validations V1-V10, build phases (comorbidity, competitor, adoption, market events), experiments E0-E6, gates G0-G3, decisions, open questions | All four families |

---

## Branch

All files in this folder are on branch `dev/claims-comorbidity-competitor-features`.

## Quick recap of model importance (752-feature NBA 3.0 model)

| Family | Features in model | Total SHAP | Top feature |
| --- | --- | --- | --- |
| Comorbidity / Dx (01–02) | 3 / 39 | 0.54% | `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH`, rank 88 |
| Adoption speed (03–04) | 1 / 2 | 1.10% | `TIME_TO_ADOPT_FARXIGA`, rank 13 |
| IQVIA channel (05–06) | 0 / 4 | 0% | — (superseded by `1_Additional_HCP_level_features`) |
| Competitor NBRx share (09–10) | Unknown | — | See `09_competitor_nbrx_share_features_analysis.md` |
