# HCP Digital: Orchestration Engine (OE 2.0) Review for NBA 3.1

**Group:** Non-personal promotional features (promotion that does not involve a sales rep)  
**Project reviewed:** `/Users/wenjie.chen@bayer.com/OE` (Orchestration Engine, "OE")  
**Weekly job reviewed:** `OE_Inference_Weekly_Pipeline` (job ID 876078160962536)  
**Model reviewed:** `kerendia_oe_journey.bayer_kerendia_ga_model_oe_2`, alias `@champion` (version 2)  
**NBA 3.0 model compared:** MLflow run `f583bcbc9d56477fae983d44c16f8c70` ("LightGBM with Tweedie - Best Model - Trained on Complete Data")  
**Built from:** a review of the OE notebooks, the code copies in the workspace, the job settings, the run logs and the model / training tables  
**Date:** October 26, 2026

## What is this document about?

The **Orchestration Engine (OE)** is the Kerendia project that decides, every week, which digital messages each doctor should be **recommended** for over the next quarter (which vendor channel, which content, on which day). Its lists go to the media partners (Doximity, Medscape, PeerDirect, PulsePoint) and to Bayer's own email system (SFMC). OE only **recommends** doctors to the vendors; it does not confirm that the message was delivered.

NBA and OE work on the same doctors and use much of the same data. OE has gone further than NBA 3.0 on digital: it reads vendor data at the event level, tags the **content** of each message, and models the **order and timing** of touches. This document describes what OE uses for digital and lists ideas that NBA 3.1 could reuse.

**How it is organised:** 1. In short, 2. How the weekly OE job works, 3. The OE 2.0 model, 4. Where OE digital data comes from, 5. The digital features in the OE 2.0 model, 6. OE versus NBA 3.0 side by side, 7. Ideas for NBA 3.1, 8. Things to watch out for.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures come from the model registry, the training table and the run logs as they were on 26 October 2026. They will change with the next run.

---

## 1. In short

* OE 2.0 is a **two-part system**: (1) a deep-learning model that predicts how many new Kerendia patients (NBRx) a doctor will start, given the doctor's profile and a proposed **journey** (a day-by-day sequence of touches), and (2) a **genetic algorithm** ("GA", a search method that tries many candidate journeys and keeps the best) that uses the model to choose the best 91-day journey for each doctor under business rules.
* Digital enters the model in **two ways**: as the **journey** itself (which channel and which content on which day) and as **history features** (what the doctor saw and did in the previous months).
* The digital history comes from **three families** of features: OE's own event-level vendor metrics (exposure / engagement / action, plus content counts), and a short list of NBA-style `DIGITAL_` features from the marketing-mix (MMX) table.
* NBA 3.0 builds about 684 `DIGITAL_` features, but its final model keeps **only 9** of them (banner, HQ email and iRep email), plus 9 DTC features. OE's model keeps **41** `DIGITAL_` features, mostly different ones (Epocrates, Prescriber Point, Custom), and relies more on its own event-level features.
* In the NBA 3.0 model, digital features have **low importance**: the best one ranks 68th of 752 features. Rep calls, Kerendia history and patient features dominate.
* The most useful ideas for NBA 3.1 are: a fixed and documented definition of exposure / engagement / action per vendor metric, **content-category** features, simple **touchpoint totals**, **recency and gap** features, a **fixed column list** instead of a dynamic pivot, and checking digital features for the **change in digital patterns after OE was fully rolled out**.

## 2. How the weekly OE job works

The weekly job `OE_Inference_Weekly_Pipeline` runs code from the GitHub repo `WenjieAtBayer/OE` (branch `develop_fix`) and notebooks in the OE folder. Its schedule (Fridays 12:00) is currently **paused**; it is started by hand. The steps are:

| Step | Task | What it does |
| --- | --- | --- |
| 1 | `RUN_Helper_Pipeline` | Runs the helper job (connection, config, dates). |
| 2 | `RUN_Promotional_Data_Ingestion` | Pulls the last 24 months of calls, non-personal promotion events and personal promotion events from Snowflake (see section 4). Also loads the suppression list (AMA "do not contact", Kaiser, Colorado and Vermont doctors). |
| 3 | `RUN_Blink_RX_Inference`, `RUN_NBRX_Inference`, `RUN_TRX_Inference` | Refresh the sales history (NBRx, TRx, BlinkRx). |
| 4 | `RUN_GA_Guadrails` | Builds the business rules for the optimiser: maximum and minimum touches per channel and per doctor segment, minimum gap between touches, fixed events, invalid channel / content combinations, blackout periods, and past priorities. Also builds the model input ("extra data") for each doctor. |
| 5 | `RUN_Generate_Past_Events` | Collects the touches already made, so the new journey continues from them. |
| 6 | `RUN_GA_Input_Dataframe` | Prepares the optimiser input in batches of 5,000 doctors. |
| 7 | `RUN_Sequence_Generation` | Runs the genetic algorithm. For each doctor it builds candidate journeys, scores them with the model, and keeps the best one. |
| 8 | `RUN_Post_Processing` | Turns the chosen journeys into vendor lists ("message architecture"). A separate job, `OE_Inference_Vendor_Deliverable_Push`, sends the files by SFTP / S3. |

The non-digital NBA-style features used by OE (sales, patients, calls, profile) are refreshed by a separate **quarterly** job, `OE_Inference_Quarterly_Pipeline`, which runs a copy of the NBA feature notebooks (including an OE version of `24_Features_Digital`).

**Last optimiser run (logs of 22 October 2026):**

| Setting | Value |
| --- | --- |
| Doctors scored | 85,166 |
| Recommendation period | 91 days, starting 15 September 2026 |
| Model | `bayer_kerendia_ga_model_oe_2@champion` |
| GA settings | population 50, 10 generations, mutation 0.3, crossover 0.3 |
| Output table | `kerendia_oe_journey.Bayer_OE_Kerendia_GA_optimizer_result_test_T1D_T2D_test_10_22_26` |

**Channels the optimiser can recommend (12):** SFMC HQ email, Medscape 3rd-party email, Medscape BrandAlert, Medscape banner, Doximity DocNews, Doximity DocPoint, Doximity DocSpot, Doximity Announcement, PeerDirect MDFI email, PeerDirect MDFI web, PeerDirect MD Minute email, PulsePoint banner.

**Content types the optimiser can recommend (14):** disease awareness and management, cost, access and coverage, unmet need, safety and efficacy, guidelines, basic product information, study design, samples, patient profile, mechanism of action, dosing and administration, real-world evidence, general.

## 3. The OE 2.0 model

| Item | Value |
| --- | --- |
| Registered model | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_oe_journey.bayer_kerendia_ga_model_oe_2`, version 2 (`@champion`) |
| Type | TensorFlow neural network: a convolutional part ("CNN") reads the journey, a dense part reads the history features |
| Trained by | job `OE_2_NBA_Model_Training` (ID 1098314767901415), code `src/NBA/model_training/runner.py`, branch `develop_fix_oe_2` |
| Training table | `kerendia_oe_journey.final_mdb_oe_2_0_22_instances_append_full` |
| What it predicts (target) | `TOTAL_NBRX_C4`: Kerendia NBRx in the 3-month window plus the following month |
| Quality on test data | R² 0.73, mean absolute error 0.85 NBRx (average target 1.21) |

**Input 1: the journey** (`padded_journey`, shape 40 x 51 x 21). Each doctor's touches in the 3-month window are written as a sequence of up to 40 steps. Each step is one channel (51 possible, including calls, speaker programs and digital channels) and one content type (21 possible). Between touches the sequence holds a **gap token**: `ZG` (no gap), `LG` (low), `MG` (medium) or `HG` (high gap). Example of a real sequence: `ZG, SFMC_HQ_EMAIL, ZG, DOXIMITY_DOCNEWS_EMAIL, HG, SFMC_HQ_EMAIL, ...` with content `GUIDELINES, GUIDELINES, BASIC_PRODUCT_INFO, ...`.

**Input 2: the history features** (`extra_data`, 2,176 columns). These describe the doctor before the window: sales, patients, calls, profile and digital history. They are log-transformed (for counts) and standardised.

**How the training data is built ("instances").** The same doctor appears once per **instance**, each instance being a different 3-month window. There are 22 instances, with start months from May 2024 to February 2026, and 78,119 doctors per instance (49,609 in the last one). For each instance:

* **C3** = the 3-month window (the journey);
* **C4** = C3 plus one month (the target period);
* **P3** = the 3 months before C3 (history features); P4, P6 and P12 give longer sales history.

**How the features were selected.** OE started from about 25,700 candidate columns and kept about 2,100 using a LightGBM model with SHAP values (a way to measure how much each feature helps the prediction), with a Poisson objective (suited to counts). See the job `KERENDIA_LGBM_FS_P3_P12` and the notebooks in `Kerendia_OE_2.0/Feature Selection`.

## 4. Where OE digital data comes from

OE does **not** rely mainly on the MMX table that NBA 3.0 uses. Its main digital source is the event-level non-personal promotion table.

| Source (Snowflake) | Saved locally as | Used for |
| --- | --- | --- |
| `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` | `kerendia_oe_journey.oe_kerendia_fact_npp_inference` | All vendor digital events: one line per doctor, day, vendor, channel, **metric** (for example `OPENED`, `CLICKED`, `IMPRESSIONS`) and **content** (`LITCODE`, creative, subject line). |
| `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` | `oe_kerendia_fact_call_inference` | Rep calls (F2F, phone, remote, group call), as journey steps. |
| `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | `oe_kerendia_fact_evnt_prsnl_prom_inference` | Speaker programs and other events, as journey steps. |
| `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` | `kerendia_oe_journey.hcp_model_paid_search_features_for_inference` | The NBA-style `DIGITAL_` features (OE copy of notebook 24). |

**How a vendor event becomes a feature (code: `data_processing.py`, `Transactions.email_processing`).**

1. Keep Kerendia events for doctors in the modelling universe; remove duplicates.
2. **Tag the content.** Each event is joined to a content tagging file (`OE/test/Content_tagging_6_5.xlsx`) on litcode, content name, subject line, creative, tactic, campaign and key message. The result is a content category (for example `GUIDELINES`, `ACCESS_COVERAGE`); untagged events become `GENERAL`.
3. **Name the placement.** A clean channel name is derived from the tactic name per vendor (for example Doximity `DocNews` / `DocSpot` / `DocPoint` / `FormularyOne` / `Announcement`; Medscape `3rd Party Email` / `BrandAlert` / `BrandSpot` / `PulsePoint Banner` / `FFQ` / `RECAP`; PeerDirect `MDFI - Email` / `MD Minute - Web`, ...).
4. **Classify the metric.** A flag file (`OE/Data/5_5_2026_Bayer_OE_updated_channel_eng_exp_flag_latest.xlsx`, 5,027 lines) says, for each vendor + channel + metric, whether it counts as **exposure**, **engagement** or **action**. Events with no flag are dropped.
5. **Shift by 7 days.** All promotion dates are moved 7 days later (`PROMO_LAG_DAYS = 7`), to allow time for the doctor to react.
6. **Count by month** and name each count `<VENDOR_CHANNEL>_<METRIC>_<R|I|E>`, using the "Metric Mappings" sheet of `mdb_prep_config.xlsx` (160 rules).

**The three levels (R / I / E).** This is OE's equivalent of NBA's exposure / light / deep engagement, but written down for every vendor metric:

| Level | Meaning | Examples |
| --- | --- | --- |
| `R` (reach / exposure) | The doctor was shown or sent the message | HQ email `DELIVERED`, PulsePoint banner `IMPRESSIONS`, Doximity DocNews `HEADLINE_VIEW`, Doximity DocSpot `VIEW` |
| `I` (interaction / light engagement) | The doctor opened or looked at it | HQ email `OPENED`, Doximity DocSpot `VIDEO_PLAY_5S`, PulsePoint banner `CLICKED`, Medscape email `OPENED` |
| `E` (engagement / action) | The doctor clicked through or took part | HQ email `CLICKED`, Doximity `CLICK_THROUGH`, Medscape email `CLICKED`, iRep email `CLICKED` |

Note that **banners** are treated differently: a banner click counts as `I` (not `E`), because clicks are the only interaction a banner has.

## 5. The digital features in the OE 2.0 model

Of the 2,176 history features of the champion model, about 90 are digital. They fall into four families (counts grouped by name pattern, so approximate):

| Family | Number | What it is | Examples |
| --- | --- | --- | --- |
| Vendor metrics, previous 3 months | 24 (of which 18 digital) | Count of one vendor metric at one level in P3 | `SFMC_HQ_EMAIL_OPENED_I_P3`, `DOXIMITY_DOCSPOT_CLICK_THROUGH_E_P3`, `PULSEPOINT_BANNER_IMPRESSIONS_R_P3`, `MEDSCAPE_3RD_PARTY_EMAIL_EMAIL_CLICK_E_P3` |
| Content counts, previous 3 months | 13 | Number of touches with each content category in P3 | `GUIDELINES_COUNT_P3`, `ACCESS_COVERAGE_COUNT_P3`, `UNMET_NEED_COUNT_P3`, `MECHANISM_OF_ACTION_COUNT_P3` |
| Touchpoint totals, previous 3 months | 4 | Sum across all channels | `EXPOSURE_TOUCHPOINT_P3` (all R), `ENGAGEMENT_TOUCHPOINT_P3` (all I), `INTERACTION_TOUCHPOINT_P3` (all E), `EXPOSURE_TOUCHPOINT_BANNER_ENGAGEMENT_P3` (R for non-banner + I for banner) |
| NBA-style `DIGITAL_` (MMX, monthly) | 41 | Same build as NBA 3.0 notebook 24, with windows 1, 2, 3, 6 and 12 months | `DIGITAL_EPOCRATES_EXPOSURE_IN_LAST_3_MONTH`, `DIGITAL_PRESCRIBER_POINT_EXPOSURE_IN_LAST_6_MONTH`, `DIGITAL_HQ_EMAIL_TACTIC_EXPOSURE_IN_LAST_2_MONTH`, `DIGITAL_OTHER_TACTIC_EXPOSURE_IN_LAST_12_MONTH` |

Other non-personal promotion features kept: 9 DTC (consumer media: WebMD, Healthline, Health Union, Sharecare, Facebook / Instagram impressions and clicks), HQ email `TOTAL_SENT_IN_LAST_n_MONTH` (from notebook 15) and 2 clickstream features.

**Which `DIGITAL_` features survived.** The 41 kept are mostly about vendors and tactics that OE's own event data does **not** cover well: Epocrates (12), Prescriber Point (7), Custom programs (5), `OTHER_TACTIC` (8), Monograph Message (3), plus a few for HQ email, Banner, Doximity, Medscape, 3rd-party email and iRep. In other words, OE uses the event-level data for the big four vendors and SFMC, and the MMX table to fill the gaps.

**The journey is digital too.** Besides the history features, the journey input (section 3) carries the full order of channels and contents and the gaps between them. This is the part of the model the optimiser changes when it searches for the best plan.

## 6. OE versus NBA 3.0 side by side

**The NBA 3.0 model.** The NBA 3.0 HCP-level model (MLflow run `f583bcbc9d56477fae983d44c16f8c70`, notebook `NBA 3.0 Dev/08_HCP_Level_Model/04_Modelling/finalized_runs/03_03_Lightgbm_Model_with_tuning_tweedie_v2_simulation_run_full_data`) is a LightGBM model with a Tweedie objective (suited to counts with many zeros). It predicts the count `TARGET` from 752 features. Its top features are rep visits (`TOTAL_F2F_IN_LAST_6_MONTH` is first), Kerendia NBRx history, time since first Kerendia Rx, affiliations and Farxiga adoption.

**Non-personal promotion features in the NBA 3.0 model (18 of 752), ranked by SHAP importance:**

| Rank (of 752) | Feature | Family |
| --- | --- | --- |
| 32 | `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS` | DTC |
| 68 | `DIGITAL_BANNER_TACTIC_EXPOSURE_IN_LAST_3_MONTH` | `DIGITAL_` (tactic) |
| 93 | `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS` | DTC |
| 107 | `DTC_PROMOTION_WEBMD_TOTAL_IMPRESSIONS` | DTC |
| 124 | `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS` | DTC |
| 151 | `DIGITAL_RUNNING_BANNER_EXPOSURE` | `DIGITAL_` (channel) |
| 200 | `DIGITAL_BANNER_EXPOSURE_IN_LAST_3_MONTH` | `DIGITAL_` (channel) |
| 283 | `DTC_PROMOTION_SHARECARE_TOTAL_IMPRESSIONS` | DTC |
| 392 | `DTC_PROMOTION_HEALTH_UNION_TOTAL_CLICKS` | DTC |
| 431 | `DTC_PROMOTION_WEBMD_TOTAL_CLICKS` | DTC |
| 559 | `DTC_PROMOTION_SHARECARE_TOTAL_CLICKS` | DTC |
| 632 | `DTC_PROMOTION_HEALTHLINE_TOTAL_IMPRESSIONS` | DTC |
| 644 | `DIGITAL_BANNER_EXPOSURE_IN_LAST_1_MONTH` | `DIGITAL_` (channel) |
| 688 | `DIGITAL_HQ_EMAIL_EXPOSURE_IN_LAST_3_MONTH` | `DIGITAL_` (channel) |
| 695 | `DIGITAL_HQ_EMAIL_LIGHT_ENGAGEMENT_IN_LAST_6_MONTH` | `DIGITAL_` (channel) |
| 698 | `DIGITAL_RUNNING_HQ_EMAIL_TACTIC_LIGHT_ENGAGEMENT` | `DIGITAL_` (tactic) |
| 738 | `DIGITAL_IREP_EMAIL_EXPOSURE_IN_LAST_6_MONTH` | `DIGITAL_` (channel) |
| 743 | `DIGITAL_IREP_EMAIL_EXPOSURE_IN_LAST_3_MONTH` | `DIGITAL_` (channel) |

The HQ email and iRep email features are vendor-level in the MMX table (`SRC_SYS_CD` = `HQ EMAIL`, `IREP EMAIL`), but no media partner (Doximity, Medscape, PeerDirect, PulsePoint, Epocrates, ...) appears by name. No HQ email event feature (`TOTAL_SENT`, `TOTAL_OPEN`, ...) and no clickstream feature is in the NBA 3.0 model. Of the `DIGITAL_` features, only exposure and light engagement were kept; no deep engagement feature was kept.

**Comparison:**

| Topic | NBA 3.0 (`24_Features_Digital` and model `f583bcbc...`) | OE 2.0 |
| --- | --- | --- |
| Model | LightGBM, Tweedie objective, 752 features, target `TARGET` | TensorFlow CNN + dense, journey + 2,176 features, target `TOTAL_NBRX_C4` |
| Main digital source | MMX aggregate table (vendor-reported totals) | Event-level non-personal promotion table, plus MMX for gaps |
| Doctor key | NPI | BH_ID (NPI through `kerendia_oe_npi_bhid_mapping_inference`) |
| Definition of exposure / engagement | Light / deep / total as reported by vendors, not documented | R / I / E fixed per vendor metric in a mapping file (160 rules) |
| Channel detail | Channel (5), vendor (about 18), tactic (15 labels) as separate pivots | Vendor + placement combined (for example `DOXIMITY_DOCSPOT`), 51 channels in the journey |
| Content | None | 14 to 21 content categories from litcode tagging |
| Time windows | 1, 3, 6 months and running total | P3 for event metrics; 1, 2, 3, 6, 12 months for `DIGITAL_` |
| Response lag | None | Promotion dates shifted 7 days |
| Order and timing of touches | Not captured | Journey sequence with gap tokens |
| Column list | Dynamic (changes with the data) | Fixed by the model config; missing columns are added as 0 |
| Digital features built | About 684 `DIGITAL_` + HQ email + clickstream | About 25,700 candidate columns in total (all families) |
| Digital features in the model | 9 `DIGITAL_` (banner, HQ email, iRep email) + 9 DTC | About 90: 18 vendor event metrics, 13 content counts, 4 touchpoint totals, 41 `DIGITAL_`, plus 9 DTC, HQ email sent and 2 clickstream |
| Vendors visible in the model | Bayer's own email systems (`HQ EMAIL`, `IREP EMAIL` vendor codes), and PulsePoint indirectly: the Banner channel features are in practice PulsePoint (98% of banner rows). No other media partner. The banner *tactic* feature is not PulsePoint (see `01_digital_entity_map_vendor_channel_tactic_content.md`) | Doximity, Medscape, PeerDirect, PulsePoint, SFMC, Epocrates, Prescriber Point |
| Feature selection | Done at model level: 752 features kept | LightGBM + SHAP, Poisson objective: about 2,100 kept |

## 7. Ideas for NBA 3.1

The ideas are ordered from easiest to largest change.

**1. Fix the column list.** Replace the dynamic pivot by a fixed list of channels, vendors and tactics (as OE does with its config file). Unknown values go to an `OTHER` bucket; missing columns are added as 0. This solves the "features change from run to run" problem of NBA 3.0.

**2. Add touchpoint totals.** Add four simple totals per period: all exposure, all light engagement, all deep engagement, and a banner-adjusted exposure. They are easy to build from the existing MMX data, stable over time, and OE kept all four after selection.

**3. Add recency and gap features.** OE's journey shows that timing matters. Simple NBA versions: days since the last digital exposure, days since the last engagement, number of distinct digital channels in the last 3 months, and the average gap between touches.

**4. Write down exposure / engagement per vendor metric.** Reuse OE's R / I / E mapping and flag file so that NBA's "light" and "deep" have a documented meaning. This answers the open point in `10_hcp_digital_paid_media_nba_3_0.md` section 6, and removes the "total is not light + deep" ambiguity.

**5. Add content-category features.** Reuse OE's content tagging (litcode to category) to count, for each doctor, how many touches were about guidelines, access and coverage, safety and efficacy, and so on. NBA 3.0 has no content dimension today; OE kept all 13 content counts.

**6. Move the big vendors to event-level data.** For Doximity, Medscape, PeerDirect, PulsePoint and SFMC, build features from `oe_kerendia_fact_npp_inference` (vendor + placement + metric), as OE does. Keep the MMX table for vendors without event data (Epocrates, Prescriber Point, Custom), which is also what OE's feature selection points to.

**7. Allow for the OE roll-out in the digital history.** OE ran a 3-month pilot with a test and a control group, then was fully rolled out; there is no control group after 18 September 2026. A per-doctor OE flag is therefore not useful for NBA 3.1, because after the roll-out every doctor in the OE universe gets OE-chosen digital messages. What does change is the **period**: digital volume, mix and timing after the roll-out are driven by OE's plan, not by the earlier campaign rules. When NBA 3.1 training windows cover both periods, check that the digital features behave the same way before and after the roll-out (volume, share of doctors with any touch, importance in the model). If they do not, consider a period indicator or training on the post-roll-out period only. The pilot test / control tagging (`OE_Eligible` in `mmx_fnl_combined_aggr_tab`) remains useful for measuring the pilot, not as an NBA feature.

**8. Add a short response lag.** Consider OE's 7-day shift (or simply leave the most recent week out) so that a message sent at the end of a month is matched with the reaction that follows.

**9. Rethink the digital block rather than add more columns.** The NBA 3.0 model already drops most of the about 684 `DIGITAL_` features and keeps only 9 (banner, HQ email, iRep email exposure and light engagement), all with low importance. Adding more columns of the same kind is unlikely to help. The OE experience suggests the gain comes from **different** information: vendor and placement detail (OE kept Epocrates, Prescriber Point, Doximity DocSpot / DocPoint), content, totals and timing (ideas 2 to 6). NBA 3.1 could build a smaller, better-defined digital block and test it against the 9 features kept today.

**10. Coordinate NBA and OE.** Both systems recommend actions for the same doctors. A shared view (for example NBA using "OE recommended channels this quarter" as an input, or OE using the NBA rep action) would avoid sending conflicting messages.

## 8. Things to watch out for

* **Code lives in GitHub.** The OE model training, GA and data preparation code is in the repo `WenjieAtBayer/OE` (`src/NBA/...`). The workspace only has copies (`Kerendia_OE_2.0/OE 2.0 Model Training`, `Kerendia_OE_2.0/Ad_hoc/Data Processing Files`), which may differ from the branch the job runs.
* **The weekly schedule is paused.** The job is started by hand; the runs of 15 October 2026 failed at the first step. The optimiser logs of 22 October show a successful run.
* **Double counting.** OE also counts HQ email in several places (`SFMC_HQ_EMAIL_*_P3`, `DIGITAL_HQ_EMAIL_TACTIC_*`, `TOTAL_SENT_*`), the same issue noted for NBA 3.0.
* **Content tagging is a manual file.** The tagging file must be updated when new litcodes appear; otherwise new content becomes `GENERAL`.
* **Different key and grain.** OE works by BH_ID and 3-month windows; NBA 3.0 digital works by NPI and month. Reusing OE features in NBA needs the NPI / BH_ID mapping and a choice of window aligned with the NBA anchor date.
* **The model target is not the NBA target.** OE predicts NBRx in the next 4 months for a given journey; the NBA 3.0 HCP-level model predicts its own count target (`TARGET`) on NBA cohorts. Features that help OE may not help NBA in the same way, so each idea should be tested in NBA's own model.
* **Digital is weak in NBA 3.0 today.** The best digital feature in the NBA 3.0 model ranks 68th of 752; the strongest non-personal feature is a DTC one (Health Union impressions, rank 32). Any NBA 3.1 digital change should be judged on whether it moves digital up in importance and improves the model, not only on the number of features.
* **Use "recommended", not "reached".** When describing OE output, say doctors were **recommended** to a vendor; OE does not confirm delivery.
