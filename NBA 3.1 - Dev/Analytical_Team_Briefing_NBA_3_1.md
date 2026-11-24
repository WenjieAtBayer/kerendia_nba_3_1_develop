# NBA 3.1 Analytical Team Briefing

**Audience:** Kerendia analytical team — no ML background needed.
**Purpose:** Walk through what NBA 3.1 is, what the data review of NBA 3.0 found (depth), how broadly we reviewed Kerendia data for NBA 3.1 (breadth), and where we stand today.
**How to use this doc during the demo:** every blue link opens the underlying notebook or document in this workspace. Items in `backticks` are table names, volume paths, or identifiers to copy.
**Prepared:** Nov 24, 2026. Analysis performed with Genie Code (the Databricks AI agent); findings are labeled **Verified** (confirmed in data and docs) or **In progress** (analysis done, pending validation).

## 1. NBA in one paragraph

NBA 3.0 is a monthly model that scores every HCP in our universe (v5: ~222K prescribers) and produces the target list the field sees in Veeva as a dropdown list — the "NBA list". Under the hood it is a gradient-boosting model (LightGBM) fed by 752 features (production run `f583bcbc...`). The only ML concept you need today: the model is a pattern-finding engine on the data we feed it — good fuel, better recommendations; wrong fuel, confidently wrong recommendations. That is why the last six weeks were spent almost entirely on fuel quality. NBA answers **who and why**; the separate OE engine answers **when, what, and how** for digital.

## 2. What changed in the process

| Before | Now (Genie Code-assisted) |
| --- | --- |
| One analyst profiling one table at a time | Parallel audits across Snowflake and Unity Catalog |
| Findings lived in slides and memory | Every domain gets a document set: NBA 3.0 profile → data assessment → NBA 3.1 readiness plan |
| Weeks to answer one data question | Billions of rows profiled in days |
| Decisions scattered | Numbered decisions (D1, D2...), open questions (Q1...), gates (G0-G3), all committed to Git |

Every readiness plan follows the same skeleton — scope, Phase 0 validations, feature candidates, experiments, gates, open questions — so anyone on the team can pick up any domain and know exactly where it stands. That repeatable structure, plus full Git traceability, is the process change.

## 3. Depth: what the NBA 3.0 audit found

These are the findings that justified rebuilding features for 3.1. Each links to its evidence.

| # | Finding | Why it matters | Evidence |
| --- | --- | --- | --- |
| 1 | **Co-detail calls were invisible.** Kerendia is co-promoted with Lynkuet; the NBA 3.0 call filter kept Kerendia-only calls, dropping ~40-46% of 2026 doctor calls (~20K doctors undercounted). | Call history is one of the model's strongest signals. | <a href="$./04_Promotional_Features/personal_promotional_features/20_field_activity_data_review_2024_2026.md">20_field_activity_data_review_2024_2026</a> (Verified) |
| 2 | **FTP and copay features were mostly dead on arrival.** Built on written dates (leakage risk), PCT_ columns 94.5% empty; only 4 of 752 features were FTP (importance ranks 500-661) and zero were copay. | Affordability programs influence prescribers; the model never saw them properly. | <a href="$./04_Promotional_Features/FTP_and_Copay/NBA%203.0%20FTP%20and%20COPAY%20Assesment.md">NBA 3.0 FTP and COPAY Assessment</a> (Verified) |
| 3 | **iRep email engagement was misread.** The NBA 3.0 template logic matched only ~0.4% of recent emails; open rates fell from ~40% to ~20% in 2026. | iRep features built on stale definitions. | <a href="$./04_Promotional_Features/personal_promotional_features/12_irep_emails_nba_3_0.md">12_irep_emails_nba_3_0</a> (Verified) |
| 4 | **Samples: shipped is not received.** Some shipments are refused, misaddressed, or lost; >95% settle within 3 weeks, ~3% never arrive. Training must trim the last 21 days before the data cut. | Received-sample features need fill-date and delivery-status logic, not shipped counts. | <a href="$./04_Promotional_Features/personal_promotional_features/22_samples_reconciliation_call_vs_shipped_dropped_2024_2026.md">22_samples_reconciliation</a> (In progress) |
| 5 | **Patient eligibility bugs.** The SGLT2 rule compared the wrong sentinel value (unknown stage leaked into eligibility); the CKD arm required T1D/T2D codes; the HF arm needed monthly HF flags and an HFpEF proxy. | Eligibility defines who can even be scored for patient-journey features. | <a href="$./03_Feature_Engineering/03_HCP_level_features/Patient_Journey_Validation/Alignment_Markdowns">Patient Journey Alignment Markdowns</a> (Verified) |
| 6 | **Lab double-count risk.** The historical lab feed (HIST) already contains LabCorp records; a planned union with the separate LabCorp full feed would have double-counted. The HIST feed alone is ~1.8B rows; roughly half cannot be linked to a patient ID and are dropped at load. | Lab features anchor the patient journey; wrong source = wrong stages. | <a href="$./03_Feature_Engineering/03_HCP_level_features/Patient_Journey_Validation/Lab%20Files">Patient Journey Lab Files</a> (Verified) |
| 7 | **CKD stage: the data disagrees with itself.** When the coded diagnosis stage and lab eGFR disagree, later labs confirm the lab value ~2 out of 3 times (61-63% vs 32-33%). The confirmed NBA 3.1 rule is lab-first (12-month lookback, eGFR 60+ requires damage evidence, coded Dx fallback). Impact: ~18% fewer eligible patients than the 3.0 rule — a more precise universe. | CKD stage drives eligibility and patient features. | <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Feature_Evaluation/06_CKD_Stage">Feature_Evaluation/06_CKD_Stage</a> (Verified) |
| 8 | **Claims features ignored claim type.** The claims notebooks applied no CLAIM_TYPE filter while the 3.0 target is built on paid claims; decision: keep PD/RV/RJ as separate feature families going forward. | Different claim types carry different signals and must not be blended. | <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Feature_Evaluation/03_Claims_Feature_Review">Feature_Evaluation/03_Claims_Feature_Review</a> (Verified) |
| 9 | **The 752-feature scorecard.** Every NBA 3.0 feature was re-scored systematically. Example: the DRG access features (PCT_PLANS_*, 44 features) carry 4.7% of model importance — but the DRG data purchase ended Dec 2025, so 3.1 must replace them with MMIT. | A single artifact that ranks what the model actually leans on. | <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Feature_Evaluation/02_NBA_3_0_Model_Evaluation">Feature_Evaluation/02_NBA_3_0_Model_Evaluation</a> (Verified) |

## 4. Breadth: the NBA 3.1 data review map

Twelve data domains reviewed for NBA 3.1. Each ends in the same readiness-plan structure.

| # | Domain | What was reviewed | Headline | Start here |
| --- | --- | --- | --- | --- |
| 1 | Patient journey (labs, Dx, Rx, procedures) | ~1.8B lab rows, eligibility rules C1-C11, lab source selection, CKD stage | Lab-first CKD stage rule confirmed; eligible universe becomes ~18% more precise | <a href="$./03_patient_features/Strategy%20and%20Execution%20Markdowns/03_Patient_Features_AI_Readiness_Plan.md">03_Patient_Features_AI_Readiness_Plan</a> |
| 2 | HCP claims features | 752-feature scorecard, claims feature review, 10 new feature ideas (F1-F10) | Claim types will become separate feature families | <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Feature_Evaluation/04_Feature_Ideas">Feature_Evaluation/04_Feature_Ideas</a> |
| 3 | Competitor and comorbidity | SGLT2 competitor NBRx share, comorbidity Dx, market events | ~85% of Jardiance and ~68% of Farxiga volume is non-CKD — competitor features must be CKD-scoped; market events (Farxiga generic Apr 2026, Entresto LOE) become simple date features | <a href="$./Feature%20Analysis/13_nbrx_nrx_trx_competitor_share_nba_3_1_readiness_plan.md">13_competitor_share_readiness_plan</a> |
| 4 | Market access (MMIT) | DRG replacement: Bronze ~3.1B rows ingested, Silver change-detection layer, DRG-MMIT stitched history design | DRG ends Dec 2025, MMIT from Jan 2026; overlap months 202510-202512 calibrate the stitch | <a href="$./04_MMIT_Features/10_market_access_team_briefing_nba_3_1.md">10_market_access_team_briefing</a> |
| 5 | FTP and copay | UC tables reproduce NBA 3.0 claims exactly (99.5% fill linkage to the 294,727-provider universe) | Only 1.9-2.7% of the universe has any fill per 12-month window — sparsity must drive feature design | <a href="$./04_Promotional_Features/FTP_and_Copay/NBA%203.1%20FTP%20and%20COPAY%20Assessment.md">NBA 3.1 FTP and COPAY Assessment</a> |
| 6 | Colocation and IDN | Colocation data profile, IDN affiliation reality check | No affiliation history table exists — all anchors must use the current snapshot | <a href="$./09_Colocation_Features/33_2_colocation_idn_data_assessment.md">33_2_colocation_idn_data_assessment</a> |
| 7 | Veeva Link KOL | 153-feature feasibility pilot, expert identification, decile segments | 37K experts in the universe; IDN expert share rises monotonically across writer quintiles (6.4% → 12.3%) — best new signal candidate | <a href="$./Veeva%20Link%20To%20People%20Analysis/40_veeva_link_data_assessment_v2.md">40_veeva_link_data_assessment_v2</a> |
| 8 | Personal promotion (calls, BHO, iRep, samples, speaker, CLM) | 2024-2026 data review, Field Analytics alignment meeting, samples reconciliation | Call model re-aligned: HCP interaction grain, product details as attributes, account records kept separate | <a href="$./04_Promotional_Features/personal_promotional_features/40_field_activity_nba_3_1_readiness_plan.md">40_field_activity_readiness_plan</a> |
| 9 | Digital / non-personal promotion | MMX table: 126M rows, 469K NPIs, 2023-2026; PulsePoint = 82% of rows | Monthly volume exploded from ~75K rows (2023-24) to 5-9M rows (2025+) — 3.0 features were built on a different data regime | <a href="$./04_Promotional_Features/non_personal_promotional_features/12_hcp_oe_digital_review_for_nba_3_1.md">12_hcp_oe_digital_review</a> |
| 10 | DTC | Flashtalking, SA360, FB+IG, DMA-level data profiled 2024-2026 | Findings + open questions documented before building a DTC plan | <a href="$./04_Promotional_Features/non_personal_promotional_features/21_dtc_data_findings_2024_2026_and_open_questions.md">21_dtc_data_findings</a> |
| 11 | Digital entity map | Vendor → channel → tactic → content, tagged NBA-M / OE-R / OE-F / BOTH | One page showing which data serves the model vs the OE engine | <a href="$./04_Promotional_Features/non_personal_promotional_features/01_digital_entity_map_vendor_channel_tactic_content.md">01_digital_entity_map</a> |
| 12 | Feature Views infrastructure | Register NBA 3.0 outputs as reusable feature tables; compute new contenders | Two tracks: reuse existing NB01-NB06 outputs vs compute V2/V6-V10 contenders in `kerendia_nba_3_1` | <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/NBA_3_1_Feature_Views_Investigation">NBA_3_1_Feature_Views_Investigation</a> |

## 5. Where we are now

* **Phase: feature engineering.** Every domain above has a readiness plan with phases, experiments, gates, and logged decisions; contender feature builds are the current workstream.
* **CKD stage rule confirmed (Nov 24):** lab-first, 12-month lookback, eGFR 60+ requires damage evidence, coded Dx fallback. Implemented in the patient journey combine notebook with a rule parameter so the 3.0 rule stays reproducible.
* **Feature Views:** investigation notebook and a time-travel walkthrough demo exist — see <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Feature_Views_Table_Time_Travel_Walkthrough.md">Feature_Views_Table_Time_Travel_Walkthrough</a> and <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/NBA_3_1_Feature_Views_Table_Time_Travel_Demo">NBA_3_1_Feature_Views_Table_Time_Travel_Demo</a>.
* **Next milestone:** shortlist contender features across domains and start selection runs.

## 6. Suggested 15-minute demo flow

1. **(2 min) The 752-feature scorecard** — open section 3's evidence links in <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Feature_Evaluation/02_NBA_3_0_Model_Evaluation">02_NBA_3_0_Model_Evaluation</a>. Point: we now know exactly what the model leans on.
2. **(3 min) Live query: MMX channel mix** — run a small query on `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_oe_journey.mmx_fnl_combined_aggr_tab` showing the PulsePoint share and the monthly volume explosion. Generation notebook: <a href="$./04_Promotional_Features/24_Features_Digital">24_Features_Digital</a>.
3. **(3 min) The CKD stage story** — <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Feature_Evaluation/06_CKD_Stage">06_CKD_Stage</a>. Point: when the data disagrees with itself, we quantify who wins and make it a rule.
4. **(3 min) One readiness plan structure** — open <a href="$./04_Promotional_Features/non_personal_promotional_features/50_digital_nba_3_1_readiness_plan.md">50_digital_nba_3_1_readiness_plan</a> or <a href="$./04_Promotional_Features/FTP_and_Copay/60_ftp_copay_nba_3_1_readiness_plan.md">60_ftp_copay_nba_3_1_readiness_plan</a>. Point: the method, not just findings.
5. **(4 min) Feature Views time travel** — <a href="$./03_Feature_Engineering/03_HCP_level_features/hcp_level_features/NBA_3_1_Feature_Views_Table_Time_Travel_Demo">NBA_3_1_Feature_Views_Table_Time_Travel_Demo</a>. Point: point-in-time correctness, the thing leakage accidents destroy.

## 7. Questions for the team

| # | Question |
| --- | --- |
| Q1 | Which domains should be prioritized for the first contender feature builds (V2, V6-V10 are drafted)? |
| Q2 | Claims: any concerns with keeping PD / RV / RJ as separate feature families rather than one blended set? |
| Q3 | Samples reconciliation (finding 4) is analysis-complete but unvalidated — who can help validate against CareTria / warehouse experience? |
| Q4 | Feature Views: should the team adopt them as the standard way to build and share features for 3.1? |
| Q5 | Which data domains do you expect to matter that we have not covered? |
| Q6 | Any feedback on the readiness-plan structure — is it usable as a team working format? |

## Appendix A: repo map (NBA 3.1 - Dev)

| Folder | Contents |
| --- | --- |
| `01_HCP_Universe` | Universe identification |
| `03_patient_features` | Patient-level features and readiness plans |
| `03_Feature_Engineering` | HCP-level claims work, patient journey validation, Feature_Evaluation docs, Feature Views notebooks |
| `03_HCP_Level_Features` | NBA 3.0/3.1 HCP feature notebooks (comorbidity, prior writing, adoption, NBRx/NRx/TRx, competitor share) |
| `04_Promotional_Features` | Personal (calls, iRep, samples, speaker), non-personal (digital, HQ email, DTC), FTP & Copay |
| `04_MMIT_Features` | Market access briefing, MMIT access features walkthrough |
| `09_Colocation_Features` | Colocation / IDN assessment and readiness plan |
| `Feature Analysis` | Competitor share analysis and readiness plan, HCP claims feature analysis |
| `Veeva Link To People Analysis` | KOL data catalog, assessments, readiness plan, signal tests |
| `Feature Selection` | NBA 3.0/3.1 selection run notebooks |

## Appendix B: key artifacts not linkable from a doc

* 752-feature scorecard CSV: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3_volume/hcp_level_model/dev_folder/notebook_output/feature_evaluation/`
* MMX engagement table: `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_oe_journey.mmx_fnl_combined_aggr_tab`
* NBA 3.0 production model: MLflow run `f583bcbc9d56477fae983d44c16f8c70` (LightGBM Tweedie, 752 features), experiment `198916793193107`
* MMIT Bronze/Silver: catalog schema `ph-com-ai-us-prod-catalog-2553213839599380.market_access`

## Appendix C: verified vs in progress

* **Verified:** findings 1, 2, 3, 5, 6, 7, 8, 9 in section 3, and all domain headlines in section 4.
* **In progress:** samples reconciliation (finding 4); Veeva Link Track U in-house pipeline; MMIT DRG-stitch calibration; Feature Views safe-window parameters (45/106/198/379 days, untested).
