# Veeva Link To People Analysis: folder guide

This folder holds the analysis of Veeva Link Key People ("Veeva Link to People") data for the Kerendia NBA 3.1 model, in the order the work was done. The order follows the git history of this folder (first commits on 23 Oct, 30 Oct, 2 Nov and 17 Nov 2026).

File names use `NN_topic`. The tens digit is the step, and the files within a step are numbered in reading order.

## Order of analysis

| Step | Range | File | Type | What it is | Produces / used by |
| --- | --- | --- | --- | --- | --- |
| 1. Initial catalog and feature feasibility (23 Oct 2026) | 10-19 | `10_veeva_link_kol_data_catalog.xlsx` | Input | Veeva Link KOL data catalog: table catalog, indication scope, feature library (`05_Feature_Library`) | Read by 11 |
| | | `11_veeva_link_data_sources_and_feature_feasibility` | Notebook | Access check for the catalog tables, US coverage, feasibility of 56 catalog features, suggested features, 153-feature pilot on 100 HCPs | Feeds 33 and 50 |
| 2. Full data profiling (30 Oct 2026) | 20-29 | `20_veeva_link_data_catalog_profiler` | Notebook | Profiles all `ANLT_VEEVA_LINK_*` tables: columns, join cardinality, data traps, indication scoping, date coverage | Writes 21 and 22 |
| | | `21_veeva_link_data_catalog_profiled.xlsx` | Output | Profiled data catalog workbook | From 20 |
| | | `22_veeva_link_focus_name_taxonomy.csv` | Output | Full `FOCUS_NAME` taxonomy across scoring tables | From 20; dictionary input for 50 (U4) |
| | | `23_veeva_link_data_assessment_v1.md` | Document | Data assessment v1 | Superseded by 40 |
| 3. KOL identification and feature design (2 Nov 2026) | 30-39 | `30_veeva_link_kol_identification_and_activity_eda` | Notebook | KOL identification from the scoring tables, High / Medium / Low tiers on the HCP Universe, activity profiles | Writes 31 and 32 |
| | | `31_veeva_kol_list.csv` | Output | KOL list with activity counts and source flags | From 30 |
| | | `32_veeva_hcp_decile_segments.csv` | Output | HCP decile segment assignments | From 30 |
| | | `33_veeva_link_feature_engineering_plan.md` | Document | Feature engineering plan: 66 features, leakage tiers, indication patterns | Companion to 23; input to 50 |
| 4. Assessment with HCP Universe and call plan (17 Nov 2026) | 40-49 | `40_veeva_link_data_assessment_v2.md` | Document | **Current data assessment**: tables, time dependence, HCP Universe overlap, call-plan segments, deciles, activity by decile and segment | Main reference for 50 |
| 5. NBA 3.1 readiness (18 Nov 2026) | 50-59 | `50_veeva_link_nba_3_1_readiness_plan.md` | Document | Readiness plan: Phase 0 split into Track U (unblock, in-house) and Track X (external), phases 1 to 4, experiments E0 to E7, gates G0 to G3; section 5.2 holds the combined signal test results | Draft |
| 6. Combined colocation, IDN and Veeva signal test (18 Nov 2026) | 60-69 | `60_veeva_colocation_idn_combined_signal_test` | Notebook | One-feature-at-a-time signal test of expert colleague (practice / IDN), expert peer writers and experts in low-adoption IDNs | Results in 50 section 5.2 |

## Notes

* Start with `40_` for the data, then `50_` for the plan. `23_` is superseded by `40_`. `30_` and `33_` use older definitions: a narrow focus-name list (34.8% scored, against 64.4% in `40_`) and High / Medium / Low tiers.
* The notebooks still write their outputs to directories in other repo copies (`kerendia_nba_3_1_develop_sm` for 20 and 30, `kerendia_nba_3_1_develop_sa` for the catalog read in 11). The file names in the code were updated to the new names, but the directories were not changed. Point `OUTPUT_DIR` / `XLSX` to this folder before re-running if outputs should land here.
* New files: use the next free number in the right step range (for example `51_` for a Phase 0 build notebook).
