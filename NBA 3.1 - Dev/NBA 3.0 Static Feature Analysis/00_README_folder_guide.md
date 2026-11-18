# NBA 3.0 Static Feature Analysis: folder guide

This folder reviews the NBA 3.0 static (HCP-level) feature families and prepares each one for NBA 3.1.

**Naming.** `NN_k_topic.md`. `NN` is the NBA 3.0 feature notebook the family comes from (07 physician attributes, 08 census, 33 colocation), the same numbers the documents use for each other. `k` is the reading order within a family: 1 = NBA 3.0 profile, 2 = NBA 3.1 data assessment, 3 = NBA 3.1 readiness plan.

| Family | File | What it is | Status |
| --- | --- | --- | --- |
| All families | `01_data_improvement_requests.md` | Data gaps to propose to the data team (DR-01 onwards), with evidence and the NBA 3.1 workaround | Living document |
| 07 Physician attributes (nb 07_phy_static_features) | `07_1_physician_attributes_nba_3_0_profile.md` | NBA 3.0 profile of the physician static features | Done |
| | `07_2_physician_attributes_data_assessment.md` | NBA 3.1 checks of the nb 07 draft and MDM account sources; section 3.3 covers IDN and account features | Done |
| 08 Census / SDoH (nb 08_census_features) | `08_1_census_nba_3_0_profile.md` | NBA 3.0 profile of the ZIP-level ACS features | Done |
| | `08_2_census_data_assessment.md` | NBA 3.1 checks of the census file, ZIP join and other area sources | Done |
| 33 Colocation and IDN | `33_1_colocation_nba_3_0_profile.md` | NBA 3.0 building / sub-premise colocation profile and defects | Done |
| | `33_2_colocation_idn_data_assessment.md` | NBA 3.1 sources (BEST_AFFL, hierarchy, account profile, PACE), coverage and signal checks for building, practice, HQ and IDN | Done |
| | `33_3_colocation_idn_nba_3_1_readiness_plan.md` | NBA 3.1 readiness plan: phases 0 to 4, experiments C0 to C5, gates G0 to G3 | Draft |

## Notes

* All 3.1 checks use the same universe (294,727), outcome (Kerendia NBRx, 2025-10-24 to 2026-10-23, baseline 9.7%) and look-back (2025-07-25 to 2025-10-23), so their numbers compare directly.
* The combined colocation / IDN / Veeva signal test is in the `kerendia_nba_3_1_develop` repo (`Veeva Link To People Analysis/60_veeva_colocation_idn_combined_signal_test`); its results are in `50_veeva_link_nba_3_1_readiness_plan.md` section 5.2 there.
* New files: use the family number and the next free `k` (for example `07_3_physician_attributes_nba_3_1_readiness_plan.md`).
