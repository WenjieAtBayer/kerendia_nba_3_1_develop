# Feature Evaluation — NBA 3.1 HCP-Level Features

**Purpose:** One place for the source-level review of the IQVIA LAAD claim sources, the evaluation of the NBA 3.0 production model's features, the review of the NBA 3.1 HCP claims features (NB01–NB06), and the draft list of new feature ideas.

**Started:** 2026-11-23 | **Owner:** Wenjie Chen | **Branch:** `combine` (`kerendia_nba_3_1_develop_pg`)

`Alignment_Markdowns/` (sibling folder) stays for time-alignment docs. Nothing in this folder changes a pipeline notebook, model or table.

---

## Folder map

| Path | Question it answers | Status |
| --- | --- | --- |
| `01_Source_Review/NBA_3_1_LAAD_Source_Review_Overview.md` | How do Rx, Dx, Px and Lab compare on freshness, duplicates, linkage and known issues? | Done 2026-11-23 |
| `01_Source_Review/NBA_3_1_Rx_Source_Review.md` | What does the LAAD Rx source look like 2021-01 to latest? | Done 2026-11-23 |
| `01_Source_Review/NBA_3_1_Dx_Source_Review.md` | What does the LAAD Dx source look like 2021-01 to latest? | Done 2026-11-23 |
| `01_Source_Review/NBA_3_1_Px_Source_Review.md` | What does the LAAD Px source look like 2021-01 to latest? | Done 2026-11-23 |
| `02_NBA_3_0_Model_Evaluation/NBA_3_0_Model_Feature_Evaluation.md` | Which of the 752 NBA 3.0 model features carry the signal, which are dead or redundant? | Done 2026-11-23 |
| Scorecard CSV (in volume: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder/notebook_output/feature_evaluation/NBA_3_0_Model_752_Feature_Scorecard.csv`) | One row per model feature (752 rows) | Done 2026-11-23 |
| `03_Claims_Feature_Review/NBA_3_1_HCP_Claims_Feature_Review.md` | For each NB01–NB06 family: keep, fix or drop? | Done 2026-11-23 |
| `04_Feature_Ideas/NBA_3_1_HCP_Feature_Ideas_Draft.md` | What new HCP features should NBA 3.1 try? | Draft 2026-11-23 |
| `05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` | How should the LAAD features use Databricks Feature Views, and what is ready? | Draft 2026-11-23 |
| `06_CKD_Stage/NBA_3_1_CKD_Stage_Readiness_Plan.md` | How do we roll out the confirmed 3.1 CKD stage rule (eligibility C11, V7 features)? | Draft 2026-11-24 |

Order of the work: source → 3.0 model → 3.1 claims features → new ideas → Feature Views readiness → CKD stage readiness.

## Related docs (not moved)

* Lab source review: `../../Patient_Journey_Validation/Lab Files/NBA_3_1_Lab_Data_Learnings_and_3_0_Review.md`
* Journey plans: `../../Patient_Journey_Validation/{Rx,Dx,Px,Lab} Files/NBA_3_1_*_Journey_Plan.md`
* NB build plans: `../01 Rx Claims Files/` … `../07 Cohort Set Files/`
* Decisions and full runs: `../Alignment_Markdowns/Strategy_and_Execution/NBA_3_1_HCP_Features_Decisions.md`, `../Alignment_Markdowns/Review_and_Findings/NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_11.md`
* 3.0 family analyses: `../../../../Feature Analysis/00_README.md`

## Doc header convention

Each doc starts with: **Purpose**, **Date**, **Inputs** (tables, files, runs), **Related docs**.
