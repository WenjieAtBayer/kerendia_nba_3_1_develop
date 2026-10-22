# Promotional Features Documentation

Documentation of the promotional feature notebooks for the Kerendia NBA 3.1 HCP-level inference pipeline. Each section covers the notebook's Purpose, Input, Processing, and Output, as recorded in the source spreadsheet.

## Contents

- [13_promotional_features_bho_calls](#13_promotional_features_bho_calls)
- [14_promotional_features_speaker_program](#14_promotional_features_speaker_program)
- [15_promotional_features_HQ_Emails](#15_promotional_features_hq_emails)
- [16_promotional_features_irep](#16_promotional_features_irep)
- [17_promotional_features_samples](#17_promotional_features_samples)
- [18_promotional_ClickStream_features](#18_promotional_clickstream_features)
- [19_ftp_features](#19_ftp_features)
- [24_Features_Digital](#24_features_digital)
- [25_promotional_features_call](#25_promotional_features_call)
- [34_promotional_features_DTC](#34_promotional_features_dtc)

---

## 13_promotional_features_bho_calls

### Purpose

Generate time-series promotional call features at the physician (HCP) level — capturing Kerendia-related sales rep call activity (by channel, call type, call purpose, and duration) across multiple lookback cohort windows — for the Kerendia NBA 3.1 HCP-level inference pipeline.

### Input

- HCP Universe — Delta table at /Volumes/.../kerendia_nba_3_hcp_model_base_hcp_universe_for_inference (provides the PROVIDER_ID spine)
- ID Mapping — kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING (maps PROVIDER_ID → BHID)
- BHO-to-BHID Mapping — PHCDW.PHCDW_STG.MDM_STG_HCP_ACCT_AFFL (maps BH_ID → BHO_ID)
- Calls Data — CPH_DB_PROD.MODEL_V2.FACT_CALL joined with CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF (Kerendia-specific submitted calls with channel, call type, duration, and purpose)
- Promotional Cohort Dates — Delta table at /Volumes/.../promotional_cohort_inference_dates (defines multiple cohort lookback windows with start/end dates)

### Processing

1. Load HCP universe; join through PROVIDER_ID → BHID → BHO_ID to link providers to the calls data
2. Query Snowflake for Kerendia submitted calls within the lookback window; classify each call into:
   - Channel binary flags: F2F, PHONE, GROUP_CALL, REMOTE_CALL
   - Call Type binary flags: GROUP_DETAIL_WITH_SAMPLE, DETAIL_WITH_SAMPLE, DETAIL_ONLY, GROUP_DETAIL, EVENT_DETAIL
   - Call Purpose binary flags: PROMOTIONAL_ACTIVITY, PROMOTIONAL_ACTIVITY_WITH_MEAL, EVENT_RELATED_PROMOTIONAL_ACTIVITY, NON_PROMOTIONAL_ACTIVITY, MISCELLANEOUS
3. Clean CALL_DURATION (cast non-numeric to 0, then to double)
4. Cross-join with promotional cohort anchor dates, then filter calls to each cohort's lookback window; create HCP_COHORT_ID = BHID_COHORT
5. Aggregate to (HCP_COHORT_ID, MONTH_ID) level — sum all binary flags and call duration into TOTAL_\* columns
6. Fill missing dates — expand each cohort's full date range, left-join actuals, fill nulls with 0
7. Rolling lag features — compute rolling sums over 30, 60, 90, 120, 150, and 180-day windows for every feature column (\*\_IN_LAST_1_MONTH through \*\_IN_LAST_6_MONTH)
8. Filter to only the cohort end date row (snapshot at lookback boundary), prefix all feature columns with BHO_, split HCP_COHORT_ID back into BHID and COHORT, stamp with PULL_DT

### Output

A Delta table written to /Volumes/.../kerendia_nba_3_hcp_model_call_features_bhoid_for_inference keyed by (HCP_COHORT_ID, SVC_DT, BHID), containing BHO_-prefixed rolling-window sums (1–6 months) for each call channel, call type, call purpose, and call duration — one snapshot row per provider per cohort.

---

## 14_promotional_features_speaker_program

### Purpose

Generate time-series promotional features based on Kerendia speaker program event attendance at the physician (HCP) level — capturing how many and what types of speaker events each HCP attended, broken down by event format, event type, and discussion topic — for the Kerendia NBA 3.1 HCP-level inference pipeline.

### Input

- Promotional Cohort Dates — Delta table at /Volumes/.../promotional_cohort_inference_dates (defines multiple cohort lookback windows with start/end dates)
- Speaker Program Attendance — CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM (Snowflake; Kerendia event attendance records including event ID, HCP ID, attendance status, event format, event type, and topic name)
- NPI-BHID Mapping — Delta table at /Volumes/.../query_output/kerendia_nba_3_0_npi_bhid_mapping (maps BH_ID to NPI)
- Shared helpers — 00_connection, 00_config, 00_step23_function

### Processing

1. Load cohort anchor dates and query Snowflake for Kerendia speaker events where ATND = 'ATTENDED', within the global lookback window
2. Deduplicate raw attendance records
3. One-hot encode each record into binary flags across three dimensions:
   - Event Format: SPKR_EVNT_FMT_F2F, \_IN_OFFC_MEAL, \_REMOTE, \_HYBRID, \_OTHER
   - Event Type: SPKR_EVNT_TYP_SPKR_PRGM, \_NON_SPKR_PRGM
   - Topic: SPKR_TOPIC_CKD (CKD-related), \_CVR (cardiorenal), \_INTRO (Kerendia introductions/case-based), \_OTHER (display/exhibit/null)
4. Cross-join with cohort anchor dates; filter events to each cohort's lookback window; create HCP_COHORT_ID = BHID_COHORT
5. Aggregate to (HCP_COHORT_ID, MONTH_ID) — sum all binary flags plus an overall TOTAL_SPEAKER_PROGRAMS_ATTENDED
6. Fill missing dates — expand each cohort's full daily date range, left-join actuals, fill nulls with 0
7. Rolling lag features — compute rolling sums over 30, 60, 90, 120, 150, and 180-day windows for every feature column (producing \*\_IN_LAST_1_MONTH through \*\_IN_LAST_6_MONTH)
8. Filter to only the cohort end date row (snapshot), split HCP_COHORT_ID back into BHID and COHORT, drop intermediate columns, stamp with PULL_DT

### Output

A Delta table written to /Volumes/.../kerendia_nba_3_hcp_model_speaker_program_for_inference keyed by (HCP_COHORT_ID, SVC_DT, BHID), containing rolling-window sums (1–6 months) for total speaker programs attended, plus breakdowns by event format, event type, and topic — one snapshot row per provider per cohort.

---

## 15_promotional_features_HQ_Emails

### Purpose

Generate time-series promotional features based on HQ (headquarters) email engagement at the physician (HCP) level — capturing how many Kerendia-related marketing emails each HCP bounced, clicked, opened, received, or unsubscribed from — for the Kerendia NBA 3.1 HCP-level inference pipeline.

### Input

- Promotional Cohort Dates — Delta table at /Volumes/.../promotional_cohort_inference_dates (defines multiple cohort lookback windows with start/end dates)
- HCP Email Events — PHCDW.PHCDW_CDM.HCP_EMAIL_LIST (Snowflake; contains EVENTDATE, EVENTTYPE, BH_ID, and EMAILPRODUCTTYPE — filtered to Kerendia-related emails only)
- NPI-BHID Mapping — Delta table at /Volumes/.../query_output/kerendia_nba_3_0_npi_bhid_mapping (loaded but used as reference for BH_ID linkage)
- Shared helpers — 00_connection, 00_config, 00_step23_function

### Processing

1. Load cohort anchor dates and query Snowflake for Kerendia HQ email events (EMAILPRODUCTTYPE LIKE '%KERENDIA%') within the global lookback window
2. Cast EVENTDATE to date; add a FLAG = 1 column for counting
3. Cross-join with cohort anchor dates, then filter each email event to its respective cohort's lookback window; create HCP_COHORT_ID = BHID_COHORT
4. Filter out null BHIDs
5. Pivot by EVENTTYPE — group by (HCP_COHORT_ID, MONTH_ID) and pivot on EVENTTYPE (Bounce, Click, Open, Sent, Unsubscribe), summing the flag to get daily counts; rename columns to TOTAL_BOUNCE, TOTAL_CLICK, TOTAL_OPEN, TOTAL_SENT, TOTAL_UNSUBSCRIBE
6. Fill missing dates — expand each cohort's full daily date range, left-join actuals, fill nulls with 0
7. Rolling lag features — unlike other promotional notebooks that use 30/60/90/120/150/180-day windows, this notebook uses only a single 90-day rolling window, producing \*\_IN_LAST_3_MONTH features for each email event type
8. Filter to only the cohort end date row (snapshot), split HCP_COHORT_ID back into BHID and COHORT, drop intermediate columns, stamp with PULL_DT

### Output

A Delta table written to /Volumes/.../kerendia_nba_3_hcp_model_hq_email_features_for_inference keyed by (HCP_COHORT_ID, SVC_DT, BHID), containing 90-day rolling sums for each email engagement type (bounce, click, open, sent, unsubscribe) — one snapshot row per provider per cohort. Notably simpler than the BHO calls and speaker program notebooks since it uses only a single lookback window (3 months) rather than six.

---

## 16_promotional_features_irep

### Purpose

Generate time-series promotional features based on iRep (field rep) email engagement at the physician (HCP) level — capturing how many Kerendia-related iRep emails each HCP received, opened, and clicked, plus breakdowns by the specific approved document/content type sent — for the Kerendia NBA 3.1 HCP-level inference pipeline.

### Input

- Promotional Cohort Dates — Delta table at /Volumes/.../promotional_cohort_inference_dates (defines multiple cohort lookback windows with start/end dates)
- iRep Sent Emails — Snowflake query joining three tables:
  - CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL (email events: sent date, clicked, opened, status)
  - CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT (approved document names, joined on APV_EMAIL_TEMPLATE)
  - PHCDW.PHCDW_STG.MDM_STG_HCP_XREF + PHCDW.PHCDW_STG.MDM_STG_HCP_PRFL (maps source customer IDs → BH_ID)
  - Filtered to: Kerendia-related documents (DOC.NM LIKE '%KERENDIA%'), delivered emails only, non-BHO accounts
- NPI-BHID Mapping — Delta table at /Volumes/.../query_output/kerendia_nba_3_0_npi_bhid_mapping
- Shared helpers — 00_connection, 00_step23_function

### Processing

1. Load cohort anchor dates and query Snowflake for Kerendia delivered iRep emails
2. One-hot encode each email record into binary flags across two dimensions:
   - Email engagement: IREP_EMAIL_DELIVERED_FLAG, IREP_EMAIL_CLICKED_FLAG, IREP_EMAIL_OPENED_FLAG
   - Approved document category (11 categories): FDA (FDA approval announcements), PSP_PRESCRIBING (patient support / prescribing info), BRANDED_ASSET, NATIONAL_BROADCAST, KIDNEY (CKD screening / kidney profile), INVITE (meeting invitations), EDUCATION (educational events), BACC_ACCESS (commercial / Medicare access), EXCLUSIVE_BROADCAST, TRIAL (free trial conversion), MISCELLANEOUS (speaker thank-you, Epic/Cerner preference lists)
3. Cross-join with cohort anchor dates; filter each email to its respective cohort's lookback window; create HCP_COHORT_ID = BHID_COHORT; filter out null BHIDs
4. Aggregate to (HCP_COHORT_ID, MONTH_ID) level — sum all binary flags into TOTAL_\* columns (14 aggregated features)
5. Fill missing dates — expand each cohort's full daily date range, left-join actuals, fill nulls with 0
6. Rolling lag features — uses a single 90-day rolling window (same as HQ emails), producing \*\_IN_LAST_3_MONTH for all 14 feature columns
7. Filter to only the cohort end date row (snapshot), split HCP_COHORT_ID back into BHID and COHORT, drop intermediate columns, stamp with PULL_DT

### Output

A Delta table written to /Volumes/.../kerendia_nba_3_hcp_model_irep_features_for_inference keyed by (HCP_COHORT_ID, SVC_DT, BHID), containing 90-day rolling sums for 14 iRep email features — 3 engagement metrics (delivered, clicked, opened) and 11 approved document category counts — one snapshot row per provider per cohort. Like the HQ emails notebook, this uses only a single 3-month lookback rather than the six windows used for BHO calls and speaker programs.

---

## 17_promotional_features_samples

### Purpose

Generate time-series promotional features based on Kerendia drug sample distribution (dropped and shipped) at the physician (HCP) level — capturing the volume and type of Kerendia samples each HCP received across multiple lookback cohort windows — for the Kerendia NBA 3.1 HCP-level inference pipeline.

### Input

- Promotional Cohort Dates — Delta table at /Volumes/.../promotional_cohort_inference_dates (defines multiple cohort lookback windows with start/end dates)
- Kerendia Samples — Snowflake table CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER (contains BHID, SMPLE_CALL_DT, SMPLE_NM, SMPLE_QTY, SAMPLE_FLAG — records of both dropped and shipped Kerendia samples; previously sourced from two separate tables which were unioned, now consolidated by the data team as of 2025-12-19)
- HCP Universe — Delta table at /Volumes/.../kerendia_nba_3_hcp_model_base_hcp_universe_for_inference (provides the PROVIDER_ID spine)
- ID Mapping — kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING (maps PROVIDER_ID → BHID)
- Shared helpers — 00_connection, 00_config, 00_step23_function

### Processing

1. Load cohort anchor dates and query Snowflake for all Kerendia samples records
2. One-hot encode each sample record into binary/quantity flags across three dimensions:
   - Sample product type (6 categories): KERENDIA_10MG, KERENDIA_20MG, KERENDIA_10MG_BRC, KERENDIA_20MG_BRC, KERENDIA_SAMPLING_KIT_BRC, KERENDIA_SAMPLE_HOUSING_BOX_BRC — each valued at SMPLE_QTY when matched
   - Overall sample: total quantity across all categories (excluding "KERENDIA PATIENT BROCHURES BRC")
   - Fulfillment channel: SAMPLE_DROPPED vs SAMPLE_SHIPPED (also excluding patient brochures)
3. Cross-join with cohort anchor dates; filter each sample to its respective cohort's lookback window; create HCP_COHORT_ID = BHID_COHORT; filter out null BHIDs
4. Aggregate to (HCP_COHORT_ID, MONTH_ID) level — sum all quantity flags into 9 TOTAL_\* columns
5. Fill missing dates — expand each cohort's full daily date range, left-join actuals, fill nulls with 0
6. Rolling lag features — uses six rolling windows (30, 60, 90, 120, 150, 180 days), producing \*\_IN_LAST_1_MONTH through \*\_IN_LAST_6_MONTH for all 9 feature columns (54 lag features total)
7. Filter to only the cohort end date row (snapshot), split HCP_COHORT_ID back into BHID and COHORT
8. Join back to HCP universe — load the HCP universe, map to BHID, cross-join with cohorts to create a complete HCP_COHORT_ID spine, then inner-join with the sample features to ensure only in-universe providers are included
9. Null check, stamp with PULL_DT

### Output

A Delta table written to /Volumes/.../kerendia_nba_3_hcp_model_samples_features_for_inference keyed by (HCP_COHORT_ID, SVC_DT, BHID), containing 1–6 month rolling sums for 9 base sample metrics (overall quantity, 6 product types, dropped count, shipped count) — one snapshot row per provider per cohort. This notebook uses the full six lookback windows (like BHO calls and speaker programs), unlike HQ emails and iRep which use only a single 3-month window. It also has an extra HCP-universe join step at the end that the other promotional notebooks lack.

---

## 18_promotional_ClickStream_features

### Purpose

Generate time-series promotional features based on Kerendia clickstream data at the physician (HCP) level — capturing how long each HCP engaged with Kerendia digital content (usage duration and presentation duration) during sales rep calls — for the Kerendia NBA 3.1 HCP-level inference pipeline.

### Input

- Promotional Cohort Dates — Delta table at /Volumes/.../promotional_cohort_inference_dates (defines multiple cohort lookback windows with start/end dates)
- Kerendia Calls — Snowflake via CPH_DB_PROD.MODEL_V2.FACT_CALL joined with CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF (provides submitted Kerendia CALL_IDs for non-BHO HCPs)
- Clickstream Data — Snowflake table CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM (contains CALL_ID, BAYER_HCP_ID, DATE_ID, USAGE_DUR, PRESN_DUR — per-call digital content engagement metrics for Kerendia)
- NPI-BHID Mapping — Delta table at /Volumes/.../query_output/kerendia_nba_3_0_npi_bhid_mapping
- Shared helpers — 00_connection, 00_step23_function

### Processing

1. Load cohort anchor dates; query Snowflake for submitted Kerendia call IDs (non-BHO) and clickstream records (BAYER_PROD_NM = 'KERENDIA')
2. Deduplicate clickstream — for each CALL_ID, keep only the row with the highest USAGE_DUR (ties broken by PRESN_DUR), yielding MAX_USAGE_DUR and MAX_PRESN_DUR per call
3. Inner-join clickstream with calls on CALL_ID to link clickstream events to validated submitted calls
4. Parse DATE_ID (yyyyMMdd integer) into a proper CALL_DATE, add a SUBMITTED_CALL_COUNT = 1 flag
5. Cross-join with cohort anchor dates; filter each clickstream record to its respective cohort's lookback window; create HCP_COHORT_ID = BHID_COHORT; filter out null BHIDs
6. Aggregate to (HCP_COHORT_ID, MONTH_ID) level — compute TOTAL_USAGE_DURATION, TOTAL_PRESN_DURATION, AVG_USAGE_DURATION, AVG_PRESN_DURATION
7. Fill missing dates — expand each cohort's full daily date range, left-join actuals, fill nulls with 0
8. Rolling lag features — uses six rolling windows (30, 60, 90, 120, 150, 180 days), producing \*\_IN_LAST_1_MONTH through \*\_IN_LAST_6_MONTH for all 4 base features (24 lag features total)
9. Filter to only the cohort end date row (snapshot), drop raw feature columns, prefix all lag columns with CLICKSTREAM_, stamp with PULL_DT

### Output

A Delta table written to /Volumes/.../kerendia_nba_3_hcp_model_clickstream_features_for_inference keyed by (HCP_COHORT_ID, SVC_DT), containing CLICKSTREAM_-prefixed 1–6 month rolling sums for 4 base metrics (total/avg usage duration, total/avg presentation duration) — one snapshot row per provider per cohort. This notebook is unique among the promotional feature notebooks in that it captures content engagement depth (time spent) rather than event counts, and it includes both sum and average aggregations (unlike the others which only use sums).

---

## 19_ftp_features

### Purpose

This notebook engineers FTP (Free Trial Program / Voucher) features at the HCP (healthcare provider) level for the Kerendia NBA 3.1 inference pipeline. It computes rolling prescription counts over multiple lookback windows to quantify each provider's FTP utilization history.

### Input

- PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP — Snowflake view of Kerendia voucher/FTP claims (prescriptions, reversals, day supply, claim auth numbers)
- /Volumes/.../kerendia_nba_3_volume/.../kerendia_nba_3_0_npi_bhid_mapping — Delta table mapping NPI numbers to internal BH_ID (provider identifiers)
- /Volumes/.../promotional_cohort_inference_dates — Delta table of cohort anchor dates with LOOKBACK_START_DATE, LOOKBACK_END_DATE, and COHORT

### Processing

1. Load & clean FTP claims — pulls prescriptions where USE_SLS = 'Y' and PRSC_NPI is not null
2. Remove reversals — identifies reversed claims (where DAY_SUPPLY sums to zero for an ORGN_CLM_AUTH_NUM) and filters out both the reversal and its corresponding original approval
3. Map NPI → BHID — joins claims to the NPI-BHID mapping to get internal provider IDs
4. Cross-join with cohort dates — expands each provider's claims across all inference cohort windows
5. Filter to lookback window — keeps only claims within each cohort's [LOOKBACK_START_DATE, LOOKBACK_END_DATE]
6. Aggregate — counts total FTP prescriptions (TOTAL_RX_FTP) per provider-cohort per day
7. Fill missing dates (Step 2) — generates a daily spine so gaps have zero counts
8. Generate rolling lag features (Step 3) — computes rolling sums over 30, 60, 90, 120, 150, and 180-day windows, then keeps only the row at LOOKBACK_END_DATE

### Output

The output is written to /Volumes/.../kerendia_nba_3_hcp_model_ftp_features_v2_for_inference with columns:

- HCP_COHORT_ID — provider-cohort identifier
- MONTH_ID — the lookback end date
- LOOKBACK_END_MONTH
- TOTAL_RX_FTP_IN_LAST_1_MONTH through TOTAL_RX_FTP_IN_LAST_6_MONTH — rolling FTP prescription counts
- PULL_DT — run date stamp

---

## 24_Features_Digital

### Purpose

This notebook engineers digital marketing engagement features at the HCP level for the Kerendia NBA 3.1 inference pipeline. It captures how each provider interacts with Kerendia digital promotions across three dimensions — channel, source system, and tactic — and computes rolling engagement metrics over multiple lookback windows.

### Input

| Source | Type | Description |
|---|---|---|
| PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB | Snowflake | Raw MMX digital engagement data — NPI_NUM, DATE_ACT, CHANNEL, SRC_SYS_CD, TACTIC_NAME, DEEP_ENGAGEMENT, LIGHT_ENGAGEMENT, TOTAL_ENGAGEMENT, EXPOSURE (filtered on BRND_NM = 'KERENDIA') |
| .../notebook_output/promotional_cohort_inference_dates | Delta (Volume) | Cohort anchor dates — LOOKBACK_START_DATE (cohort I01) used as the digital data start date |
| 00_connection, 00_config, 00_step23_function | Helper notebooks (%run) | Snowflake connection, config variables, and the step2_fill_missing / step3_lag rolling-window functions |

### Processing

1. Load digital engagement data — pulls Kerendia-brand records from the MMX combined aggregation table, starting from the cohort lookback start date
2. Standardize channels — remaps channel names (CALL→CALLS, HQ EMAIL→HQ_EMAILS, IREP EMAIL→IREP_EMAILS, SAMPLE→SAMPLES)
3. Standardize tactics — maps 14 tactic names to normalized labels (BANNER_TACTIC, CTV_TACTIC, HQ_EMAIL_TACTIC, DOCNEWS_TACTIC, VIDEO_TACTIC, IREP_EMAIL_TACTIC, MONOGRAPH_MESSAGE_TACTIC, DOCSPOT_TACTIC, BRAND_ALERT_TACTIC, DOC_ALERT_TACTIC, EMAIL_TACTIC, EMAIL_ALERT_TACTIC, NATIVEVIDEO_TACTIC, FORMULARY_TACTIC, OTHER_TACTIC)
4. Remove CALLS/SAMPLES channels — filters out non-digital channels
5. Pivot into 3 feature sets — creates separate pivoted DataFrames:
   - df_channel — pivoted by CHANNEL, with DEEP_ENGAGEMENT, LIGHT_ENGAGEMENT, TOTAL_ENGAGEMENT, EXPOSURE per channel
   - df_src_sys_cd — pivoted by SRC_SYS_CD, same 4 metrics per source system
   - df_tactic_name — pivoted by TACTIC_NAME, same 4 metrics per tactic
6. Fill missing months + rolling lag features — for each of the 3 feature sets, applies step2_fill_missing (monthly spine) then step3_lag with windows of 1, 3, and 6 months (note: unlike other feature notebooks that use 1–6, this one uses only 1, 3, 6)
7. Drop raw tactic columns — removes the pre-lag tactic columns, keeping only the rolling features
8. Merge all 3 feature sets — left-joins channel, source system, and tactic rolling features on NPI_NUMBER + SVC_DT_M
9. Prefix all features — renames every feature column with a DIGITAL_ prefix for namespace clarity

### Output

Final Output Features (saved to .../kerendia_nba_3_0_hcp_model_paid_search_features_for_inference):

- NPI_NUMBER — provider NPI identifier
- SVC_DT_M — service month
- DIGITAL_\<CHANNEL\>\_\<METRIC\>\_IN_LAST_{1,3,6}\_MONTH — rolling channel engagement (e.g., DIGITAL_HQ_EMAILS_DEEP_ENGAGEMENT_IN_LAST_3_MONTH)
- DIGITAL_\<SRC_SYS_CD\>\_\<METRIC\>\_IN_LAST_{1,3,6}\_MONTH — rolling source-system engagement
- DIGITAL_\<TACTIC\>\_\<METRIC\>\_IN_LAST_{1,3,6}\_MONTH — rolling tactic engagement
- PULL_DT — run date stamp

This produces a large feature set — each of the 3 dimensions is crossed with 4 engagement metrics and 3 lookback windows, making this the most feature-rich notebook in the series. It's also unique in using NPI_NUMBER as the key (rather than PROVIDER_ID or BHID used in other notebooks), and in using 1, 3, 6-month windows instead of the standard 1–6 month windows.

---

## 25_promotional_features_call

### Purpose

This notebook engineers promotional call features at the HCP level for the Kerendia NBA 3.1 inference pipeline. It captures sales rep call activity — broken down by channel type, call type, and call purpose — and computes interaction features across those dimensions, including cross-combinations.

### Input

| Source | Type | Description |
|---|---|---|
| CPH_DB_PROD.MODEL_V2.FACT_CALL | Snowflake | Raw Kerendia call records — CALL_DATE, CALL_REC_TYP_NM, CALL_TYP, CALL_DUR, CALL_PURPS, DETL_PROD, STAT (filtered on KERENDIA, SUBMITTED_VOD) |
| CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF | Snowflake | SOURCE_CUST_ID → BAYER_CUST_ID (BHID) mapping |
| .../notebook_output/promotional_cohort_inference_dates | Delta (Volume) | Cohort anchor dates — LOOKBACK_START_DATE, LOOKBACK_END_DATE, COHORT |
| .../query_output/kerendia_nba_3_0_npi_bhid_mapping | Delta (Volume) | NPI-to-BHID mapping |
| 00_connection, 00_config, 00_step23_function | Helper notebooks (%run) | Snowflake connection, config, and step 2/3 fill & lag functions |

### Processing

1. Load & classify calls — pulls Kerendia calls within the lookback window and maps CALL_REC_TYP_NM into 4 channel categories:
   - F2F (Face-to-Face), PHONE, GROUP_CALL, REMOTE_CALL
2. One-hot encode 3 dimensions — creates binary indicators for:
   - Channel (4): F2F, PHONE, GROUP_CALL, REMOTE_CALL
   - Call Type (5): GROUP_DETAIL_WITH_SAMPLE, DETAIL_WITH_SAMPLE, DETAIL_ONLY, GROUP_DETAIL, EVENT_DETAIL
   - Call Purpose (5): PROMOTIONAL_ACTIVITY, PROMOTIONAL_ACTIVITY_WITH_MEAL, EVENT_RELATED_PROMOTIONAL_ACTIVITY, NON_PROMOTIONAL_ACTIVITY, MISCELLANEOUS
   - Plus CALL_DURATION as a continuous feature
3. Cross-join with cohort dates — expands records across cohort windows, filters to [LOOKBACK_START_DATE, LOOKBACK_END_DATE], creates HCP_COHORT_ID
4. Aggregate — sums all indicators + call duration per HCP_COHORT_ID per day
5. Cross-combination features — generates interaction columns for every channel × call-type combination using least() (e.g., TOTAL_F2F_AND_DETAIL_WITH_SAMPLE)
6. Fill missing dates (Step 2) — expands a daily spine so gaps get zero counts
7. Rolling lag features (Step 3) — applies a 90-day (3-month) only rolling window, producing \*\_IN_LAST_3_MONTH for every feature
8. Extract BHID from HCP_COHORT_ID, drop intermediate columns, rename MONTH_ID → SVC_DT

### Output

Final Output Features (saved to .../kerendia_nba_3_hcp_model_call_features_for_inference):

- HCP_COHORT_ID, BHID — provider identifiers
- SVC_DT — lookback end date
- 15 base features × 1 lag window = TOTAL_\<feature\>\_IN_LAST_3_MONTH for:
  - 4 channel counts + 5 call-type counts + 5 call-purpose counts + call duration
- 20 cross-combination features × 1 lag window = TOTAL_\<channel\>\_AND_\<call_type\>\_IN_LAST_3_MONTH (4 channels × 5 call types)
- PULL_DT — run date stamp

This is unique among the feature notebooks in two ways: it uses only a single 3-month rolling window (unlike the 1–6 month windows in notebooks 19–22), and it generates channel × call-type cross-features via least() that capture co-occurrence of specific interaction modes.

---

## 34_promotional_features_DTC

### Purpose

Not documented but important

### Input

_Not documented._

### Processing

_Not documented._

### Output

_Not documented._