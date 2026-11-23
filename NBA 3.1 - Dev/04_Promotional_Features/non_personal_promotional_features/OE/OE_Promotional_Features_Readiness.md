# OE Promotional Features (NBA 3.1): Readiness File

This file defines the business logic, business rules and formulas behind the OE (Omnichannel Engine) promotional features of the Kerendia NBA 3.1 model, as built by notebook `35_OE_Promotional_Features_NBA31`. It describes **what** each feature is and **how** it is calculated, not how to lay out a notebook.

When it is triggered ("trigger the file"), the features must be generated so that they follow sections 4 to 7 exactly and pass the validation rules in section 8.

Contents:

1. Overview
2. Data sources
3. Parameters
4. Business logic and formulas
5. Business rules
6. Reach / engagement / action metric mapping
7. Features produced
8. Validation rules
9. Known limitations
10. Combine-step notes

---

## 1. Overview

| Item | Value |
| --- | --- |
| Purpose | HCP-level non-personal promotion (NPP) features for the Kerendia NBA 3.1 model |
| Source | NPP fact table `kerendia_oe_journey.oe_kerendia_fact_npp_inference` |
| Grain | One row per `PROVIDER_ID` x `COHORT` (every HCP in the NBA 3.1 universe x 28 cohorts) |
| Join key | `HCP_COHORT_ID = PROVIDER_ID + "_" + COHORT` |
| Windows | P3, P6, P9, P12: the 3, 6, 9 or 12 months ending at the cohort's `lookback_end_date` |
| Feature families | Channel reach (R), engagement (I), action (E); indication R/I/E; content-category counts; touchpoint totals |
| Output | `{V31}/notebook_output/oe_nba_3_1/kerendia_nba_3_1_oe_promotional_features.parquet` |

---

## 2. Data sources

Catalog: `ph-com-ai-us-prod-catalog-2553213839599380`
Volume root (`V31`): `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume`

| # | Source | Location | Used for | Key columns |
| --- | --- | --- | --- | --- |
| 1 | NPP fact table | `` `{CATALOG}`.kerendia_oe_journey.oe_kerendia_fact_npp_inference `` | All promotion events | `CUST_ID` (= BH_ID), `BAYER_HCP_ID`, `PROD_BRAND_NM`, `VEND_NM`, `CHNL_NM`, `TACT_NM`, `MTR_NM`, `UNIQ_NPP_ID`, `DATE_ID` (yyyyMMdd), `CF_INDICATION`, plus 14 creative columns for content tagging |
| 2 | Cohorts | `{V31}/cohorts/promotional/cohorts.parquet` | 28 cohorts c1..c28 | lowercase: `cohort_id`, `lookback_end_date`, `dataset`, `prediction_month`, `lookback_start_date`, `offset_days` |
| 3 | HCP universe | `{V31}/HCP_Universe_without_call_hcps/` | Output grid | `PROVIDER_ID` only |
| 4 | Primary ID mapping | `` `{CATALOG}`.kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING `` | BH_ID to PROVIDER_ID | `PROVIDER_ID`, `BH_ID`, `NPI_NUMBER` |
| 5 | OE fallback ID mapping | `` `{CATALOG}`.kerendia_oe_journey.kerendia_oe_npi_bhid_mapping_inference `` | Newer BH_IDs (BH_ID to NPI) | `BH_ID`, `NPI_NUMBER` |
| 6 | R/I/E metric mapping | `helper_files/mdb_prep_config.xlsx`, sheet `Metric Mappings` (in this OE folder) | Exposure, engagement and action flags | `Category` (R/I/E), `Event Type` (= channel), `Mapped Metric` (= `MTR_NM`) |
| 7 | Content tagging | `helper_files/Content_tagging_6_5.xlsx` (in this OE folder; byte-identical copy of `/Workspace/Users/wenjie.chen@bayer.com/OE/GA Run/Data_for_production/Content_tagging_6_5.xlsx`) | Message category per creative | 14 merge columns + `Content Category` |

Cohort facts: every `lookback_end_date` falls on the 17th. c1 = 2024-06-17 and c28 = 2026-09-17. c1-c24 are Training, c25-c26 Testing, and c27-c28 Holdout (Backtesting).

Out of scope: FACT_CALL and EVNT_PRSNL_PROM (calls and personal events) are not used.

---

## 3. Parameters

| Parameter | Value | Meaning |
| --- | --- | --- |
| Product | `KERENDIA` | Only Kerendia promotion is used |
| Excluded vendors | `SFMC` | HQ Email is built in notebook 15 |
| Excluded content tags | `SAMPLES` | No sample-tag features |
| Promo lag | 7 days | Every event date is moved forward 7 days |
| Period cutoff day | 17 (= day of every `lookback_end_date`) | Periods run from the 18th to the 17th |
| Windows | P3 = 3, P6 = 6, P9 = 9, P12 = 12 periods | Ending at `lookback_end_date` |
| Indications searched | HF, CKD, T1D, T2D | Substring match on `CF_INDICATION` |
| Valid NPI | `^[0-9]{10}$` | Used in the fallback ID mapping |
| Output path | `{V31}/notebook_output/oe_nba_3_1/kerendia_nba_3_1_oe_promotional_features.parquet` | |

Implementation constraint: in the latest NBA 3.1 run (2026-11-23) the full history was 68,194,873 NPP rows and 7,853,188 interactions. Keep the processing in Spark; converting the interaction table to pandas runs out of memory.

---

## 4. Business logic and formulas

The features are built in eight stages. Each stage below gives its logic and formulas.

### 4.1 HCP identity (BH_ID to PROVIDER_ID)
The NPP table identifies HCPs by `CUST_ID` (a BH_ID). The NBA 3.1 model uses `PROVIDER_ID`.

1. **Primary:** `SOURCE_PROVIDER_BHID_NPI_MAPPING` gives BH_ID to PROVIDER_ID (both trimmed, not null).
2. **Fallback for newer BH_IDs:** `kerendia_oe_npi_bhid_mapping_inference` gives BH_ID to NPI (10-digit NPIs only). That NPI is mapped to PROVIDER_ID through `SOURCE_PROVIDER_BHID_NPI_MAPPING.NPI_NUMBER`.
3. **Combine:** take the union of both, keep only PROVIDER_IDs in `HCP_Universe_without_call_hcps` (the placeholder `PROVIDER_ID = '0'` is excluded), and keep one PROVIDER_ID per BH_ID: `PROVIDER_ID = min(PROVIDER_ID)` per BH_ID.
4. Only NPP records whose `CUST_ID` is in this map are used.

Latest NBA 3.1 run (2026-11-23): 296,295 BH_IDs mapped.

### 4.2 Event selection
A source record is kept when all of the following hold:

* `PROD_BRAND_NM = 'KERENDIA'` and `BAYER_HCP_ID` is not null.
* `upper(trim(VEND_NM))` is not `SFMC`.
* `DATE_ID` (yyyyMMdd) falls in the load range. The range runs from the first day of the month before the first needed period, minus 7 days, to the last day of the last cohort's month, minus 7 days. The first needed period is the earliest cohort's end period minus 11 months.
* `CUST_ID` is mapped (4.1).

Source duplicates are removed: one record per `UNIQ_NPP_ID, DATE_ID, CUST_ID, VEND_NM, CHNL_NM, MTR_NM`.

### 4.3 Content tagging
Each record gets a message category (`CONTENT_TAG`) from `Content_tagging_6_5.xlsx`.

* **Join columns (14):** `CHNL_NM, VEND_NM, LITCODE, CNTT_NM, EMAIL_SUBJ_LN, CRTV_NM, TACT_NM, CPGN_NM, PRMRY_KEY_MSG, CF_NAME, CF_INDICATION, RPT_CHNL, CHNL_TYP, TACT_TYP`.
* **Normalisation before joining** (both sides): trim the value. Treat empty, None, NaN, NULL, N/A or NA as `_`. Replace every run of non-word characters with `_`, collapse repeated `_`, and strip leading and trailing `_`. The tagging file is deduplicated on the 14 columns. `LITCODE` is read as text.
* **Rule:** a left join. A missing category, `-` or `Not Needed` becomes `General`.
* `CF_INDICATION` is saved (uppercased and trimmed) **before** normalisation, for the indication features.
* `VEND_NM`, `CHNL_NM`, `MTR_NM` and `TACT_NM` keep their original values for everything after the join.
* **Final tag:** `upper(trim(tag))`. `NONE`, `NAN`, empty, `OTHERS` and `NONE_` become `GENERAL`.

### 4.4 Channel derivation
`CHANNEL = VEND_NM + "_" + sub-channel`, standardised to `[A-Z0-9_]` (uppercase, every run of other characters replaced by `_`, leading and trailing `_` stripped). The sub-channel comes from `TACT_NM`:

* `T = upper(TACT_NM)`
* `code = upper(` text after `KERENDIA_` or `Kerendiafinerenone_` (case-insensitive), letters only `)`

Within each vendor the first matching rule wins.

PeerDirect note: all 2025 PeerDirect records have `TACT_NM` = NULL; their placement is in `TACT_TYP` (for example `MD Minute - Email`, or a bare `MD Minute` / `MDFI`). The format pairing comes from the 2026 records, which carry both. Records with `TACT_NM` are unaffected. `TACT_TYP` is kept in its raw form through content tagging for this rule.

| Vendor | Rule | Sub-channel |
| --- | --- | --- |
| DOXIMITY | T contains DOCNEWS / DOCSPOT / DOCPOINT / FORMULARY / ANNOUNCE | DocNews / DocSpot / DocPoint / FormularyOne / Announcement |
| DOXIMITY | otherwise, word `DN` / `F1` / `AN` in T | DocNews / FormularyOne / Announcement |
| MEDSCAPE | code = EA / BA / BS / PP / FFQ / RECAP / TLM / PPEHR / FAP / DDTRD | 3rd Party Email / BrandAlert / BrandSpot / PulsePoint Banner / FFQ / RECAP / BANNER / EHR / FAP / DDTRD |
| PEERDIRECT | `T' = upper(coalesce(TACT_NM, TACT_TYP))`; if T' has no ` - <format>` suffix, append it from `CHNL_NM` (`3rd Party Email` -> ` - EMAIL`, `BANNER` -> ` - BANNER`, `CUSTOM` -> ` - WEB`). Then T' contains `MDFI - EMAIL` / `MDFI - WEB` / `MDFI - BANNER` / `MD MINUTE - EMAIL` / `MD MINUTE - WEB` / `MD MINUTE - BANNER` | the same label |
| PULSEPOINT | always | Banner |
| any other, or no rule matched | | none: the record is dropped |

### 4.5 Reach / engagement / action flags
Each record is flagged using the metric mapping in section 6.

* Match key: `CH_KEY = standardise(VEND_NM + "_" + sub-channel)` and `MTR_KEY = standardise(MTR_NM)`. Here `standardise` means uppercase, trim, and replace every run of non-alphanumeric characters with `_`. The mapping's `Event Type` and `Mapped Metric` are standardised the same way.
* `R = 1` if the pair is mapped to category R, `I = 1` if mapped to I, `E = 1` if mapped to E. A pair can carry several flags.
* Records with no flag, no sub-channel or no `UNIQ_NPP_ID` are dropped.

### 4.6 Interaction collapse (engagement can never exceed exposure)
An **interaction** is one HCP x vendor x sub-channel x content tag x product x `UNIQ_NPP_ID`.

* `EXPOSED_ON = min(date)` over the interaction's R records
* `ENGAGED_ON = min(date)` over its I records
* `ACTED_ON = min(date)` over its E records
* I and E records are attached to the exposure on HCP x vendor x sub-channel x product x `UNIQ_NPP_ID`, **without** the content tag: records of one interaction can carry different LITCODE / CF_* values and so different tags, and must still count as one engagement
* `INDICATION` = `CF_INDICATION` of the earliest R record

The interaction exists only if it has an R record; I and E records without one are dropped. Each interaction therefore gives exactly 1 exposure, at most 1 engagement and at most 1 action. An email opened 3 times in one day, or on several days, counts as one engagement.

After the period is assigned (4.7), one row is kept per HCP x interaction x channel x exposure date. Ties are broken by content tag, then engagement date, action date and indication. Each row has `COUNT = 1`.

### 4.7 Promo lag and periods
* `date' = date + 7 days` (applied to EXPOSED_ON, ENGAGED_ON and ACTED_ON).
* `period(d) = yyyyMM(d)` if `day(d) <= 17`, else `yyyyMM(d + 1 month)`. Example: 2026-09-17 is period 202609 and 2026-09-18 is period 202610, so period 202609 covers 2026-08-18 to 2026-09-17.
* Each interaction's period is `YRMO = period(EXPOSED_ON')`. **Engagement and action are counted in the same period as their exposure.**
* Interactions are kept only if `YRMO` is between the first needed period and the last cohort's period.

### 4.8 Windows
For a cohort with `lookback_end_date` E, the end period is `yyyyMM(E)`. Its window Pn contains the n periods `end period, end period - 1 month, ..., end period - (n - 1) months`. That is event dates (after the lag) in (E - n months, E].

### 4.9 Feature formulas
For HCP h, cohort c and window W, let `X(h, c, W)` be the set of interactions of h whose `YRMO` is in window W of cohort c.

| Feature | Formula |
| --- | --- |
| `OE_{CH}_R_{W}` | number of interactions in X with channel CH |
| `OE_{CH}_I_{W}` | number of interactions in X with channel CH and ENGAGED_ON not null |
| `OE_{CH}_E_{W}` | number of interactions in X with channel CH and ACTED_ON not null |
| `OE_IND_{IND}_{R,I,E}_{W}` | same three counts over all channels, restricted to interactions where `upper(coalesce(INDICATION, 'UNKNOWN'))` contains IND |
| `OE_{TAG}_COUNT_{W}` | number of interactions in X with content tag TAG (TAG is not SAMPLES) |
| `OE_EXPOSURE_TOUCHPOINT_{W}` | sum over channels of `OE_{CH}_R_{W}` |
| `OE_ENGAGEMENT_TOUCHPOINT_{W}` | sum over channels of `OE_{CH}_I_{W}` |
| `OE_ACTION_TOUCHPOINT_{W}` | sum over channels of `OE_{CH}_E_{W}` |

Naming: `OE_` + the standardised name (`[A-Z0-9_]`), with the window as suffix. A feature column exists only if at least one interaction produces it.

### 4.10 Output grid and fill
* Grid = every `PROVIDER_ID` in the universe (except the placeholder `0`) x every cohort (with its `DATASET` label). `HCP_COHORT_ID = PROVIDER_ID + "_" + COHORT`.
* Feature rows are mapped from BH_ID to PROVIDER_ID (4.1) and left-joined to the grid.
* Missing values are 0. Features are stored as double.

---

## 5. Business rules

| # | Rule | Detail |
| --- | --- | --- |
| 1 | Source scope | NPP table only; calls and personal events are out of scope |
| 2 | Product | `PROD_BRAND_NM = 'KERENDIA'`, `BAYER_HCP_ID` not null |
| 3 | Vendor exclusion | SFMC (HQ Email) is removed at load. Notebook 15 builds HQ email features, so keeping it would double count. This applies to all families |
| 4 | HCP mapping | BH_ID to PROVIDER_ID through the primary mapping, with the OE BH_ID-to-NPI fallback. Keep the min PROVIDER_ID per BH_ID so each event counts once. Only HCPs in `HCP_Universe_without_call_hcps`, without the placeholder `0` |
| 5 | Source dedup | One record per `UNIQ_NPP_ID, DATE_ID, CUST_ID, VEND_NM, CHNL_NM, MTR_NM` |
| 6 | Channel | `VEND_NM` + sub-channel derived from `TACT_NM` (section 4.4), standardised to `[A-Z0-9_]`. PeerDirect uses `TACT_TYP` when `TACT_NM` is NULL |
| 7 | R/I/E flags | From `mdb_prep_config.xlsx` `Metric Mappings`, plus the supplemental Medscape mappings in section 6.2: R = reach (exposure), I = engagement, E = action. Matched on (channel, metric). A pair can carry several flags. Unmatched records are dropped |
| 8 | **Engagement never exceeds exposure** | Each interaction (HCP x channel x content x `UNIQ_NPP_ID`) is one exposure, dated on its first exposure record. It counts at most one engagement and one action, however many open, view or click records it has. For example, an email opened 3 times in one day, or on several days, is one engagement. Engagement and action are counted in the exposure's period, so I <= R and E <= R in every window. Engagement or action is matched to the exposure on the interaction, ignoring content tag. Engagement or action with no exposure is dropped |
| 9 | Content tag | Left join to `Content_tagging_6_5.xlsx` on 14 attributes. Untagged, `-` and `Not Needed` become GENERAL. `SAMPLES` columns are dropped, but those exposures still count in channel, indication and touchpoint totals |
| 10 | Promo lag | +7 days on every event date before the period is assigned |
| 11 | Periods | 18th-to-17th periods (cutoff = day of `lookback_end_date` = 17) |
| 12 | Windows | Pn = the n periods ending at `lookback_end_date` (inclusive). Windows are nested, and nothing after `lookback_end_date` is used (no leakage) |
| 13 | Event dedup | One row per HCP x channel x content x interaction; each row counts 1 |
| 14 | Indication | `CF_INDICATION` is uppercased and matched by substring, so one record can count for several indications (for example `HFPEF,CKD IN T2D` counts for HF, CKD and T2D). `HF` also matches `HFPEF`. Indications with no records produce no columns (currently T1D) |
| 15 | Touchpoint totals | Sum of the channel R / I / E columns only (indication and content columns excluded) |
| 16 | Naming | Every feature starts with `OE_` and uses only `[A-Z0-9_]` |
| 17 | Fill | HCP x cohort rows with no activity are 0. All features are counts. Do not impute again downstream |

---

## 6. Reach / engagement / action metric mapping

### 6.1 Main mapping
`helper_files/mdb_prep_config.xlsx`, sheet `Metric Mappings`, in the OE folder. Columns: `Category` (R / I / E), `Event Type` (channel, for example `MEDSCAPE_FFQ`), `Mapped Metric` (`MTR_NM`). At the latest NBA 3.1 run (2026-11-13) it had 160 rows (R 60, I 53, E 47).

### 6.2 Supplemental Medscape mapping
Five Medscape channels record their activity under generic metric names that the sheet does not list, so without these rows they would produce no features. They are added to the sheet at load time; the Excel file is not changed. They follow the sheet's own conventions:
* R = delivery, exposure or impression.
* I = open, view or time spent.
* E = click.
* Banner clicks count as both I and E (as `PULSEPOINT_MEDIA_CLICK` does in the sheet).
* A view counts as both R and I where there is no separate exposure record (as `PAGE_VIEW` does for BrandAlert).

| Event Type | R | I | E |
| --- | --- | --- | --- |
| MEDSCAPE_BANNER | EXPOSURE, IMPRESSIONS | LINK CLICK, CLICKED | LINK CLICK, CLICKED |
| MEDSCAPE_PULSEPOINT_BANNER | EXPOSURE, IMPRESSIONS | LINK CLICK, CLICKED | LINK CLICK, CLICKED |
| MEDSCAPE_BRANDSPOT | EXPOSURE, IMPRESSIONS, PARTICIPATION | VIDEO TIME SPENT | LINK CLICK, CLICKED |
| MEDSCAPE_DDTRD | DELIVERED, EXPOSURE, VIEW | OPENED, VIEW | CLICKED, PARTICIPATION |
| MEDSCAPE_FAP | DELIVERED, EXPOSURE, VIEW | OPENED, VIEW | CLICKED, LINK CLICK |

That is 32 rows in total (one per Event Type x category x metric). BrandSpot `PARTICIPATION` is treated as reach because it is the exposure record before August 2025, in the same way the sheet treats `RICH_MEDIA_ENGAGEMENT` as R. `SENT` is never mapped; delivery is the reach event for emails.

These rows are an analyst assumption based on the data and the sheet's conventions. Confirm them with the OE owner.

---

## 7. Features produced

W is one of P3, P6, P9 or P12. The counts below are from the latest NBA 3.1 run (2026-11-23, after QC fixes): 80 base features x 4 windows = 320 columns (output 324 columns with the 4 keys; 8,252,328 rows = 294,726 HCPs x 28 cohorts). The 2026-11-13 run had 79 base / 316 columns. They can change when the source data adds or drops channels or tags.

| Family | Pattern | Base | Columns | Definition |
| --- | --- | --- | --- | --- |
| Channel reach | `OE_{CHANNEL}_R_{W}` | 22 | 88 | Exposed interactions on the channel |
| Channel engagement | `OE_{CHANNEL}_I_{W}` | 16 | 64 | Exposed interactions with at least one engagement (<= R) |
| Channel action | `OE_{CHANNEL}_E_{W}` | 14 | 56 | Exposed interactions with at least one action (<= R) |
| Indication | `OE_IND_{HF,CKD,T2D}_{R,I,E}_{W}` | 9 | 36 | The same three counts, for records mentioning that indication |
| Content category | `OE_{TAG}_COUNT_{W}` | 16 | 64 | Exposed interactions with that message category |
| Touchpoint totals | `OE_{EXPOSURE,ENGAGEMENT,ACTION}_TOUCHPOINT_{W}` | 3 | 12 | Sum of the channel R, I or E columns |
| **Total** | | **80** | **320** | |

**Channels in the latest NBA 3.1 run (2026-11-23) and which flags they have:**

| Channel | R | I | E |
| --- | --- | --- | --- |
| DOXIMITY_ANNOUNCEMENT, DOXIMITY_DOCNEWS, DOXIMITY_DOCPOINT, DOXIMITY_DOCSPOT, DOXIMITY_FORMULARYONE | Yes | Yes | Yes |
| MEDSCAPE_3RD_PARTY_EMAIL, MEDSCAPE_BANNER, MEDSCAPE_DDTRD, MEDSCAPE_FAP, MEDSCAPE_FFQ, MEDSCAPE_PULSEPOINT_BANNER, MEDSCAPE_RECAP, PEERDIRECT_MDFI_EMAIL | Yes | Yes | Yes |
| MEDSCAPE_BRANDALERT, PEERDIRECT_MD_MINUTE_EMAIL, PULSEPOINT_BANNER | Yes | Yes | |
| MEDSCAPE_BRANDSPOT | Yes | | Yes |
| MEDSCAPE_EHR, PEERDIRECT_MDFI_BANNER, PEERDIRECT_MDFI_WEB, PEERDIRECT_MD_MINUTE_BANNER, PEERDIRECT_MD_MINUTE_WEB | Yes | | |

`PEERDIRECT_MDFI_EMAIL` gained I and E with the 2025 PeerDirect records (section 4.4).

**Content tags (16):** ACCESS_COVERAGE, BASIC_PRODUCT_INFO, COST, DISEASE_AWARENESS_MANAGEMENT, DOSING_ADMINISTRATION, EFFICACY, EVENT, GENERAL, GUIDELINES, MECHANISM_OF_ACTION, MECHANISM_OF_DISEASE, PATIENT_ADHERENCE_SUPPORT, PATIENT_PROFILE, SOCIAL_PROOF, STUDY_DESIGN, UNMET_NEED. `SAFETY_EFFICACY` (in the 2026-11-13 run) has no matching exposures since the 2026-11-19 source rebuild, so its 4 columns are not produced; the combine schema must tolerate this.

The channel and tag lists come from the data, so new values in the source add columns. That is expected; report them.

**Window example, c28 (`lookback_end_date` 2026-09-17):**

| Window | Event dates (after lag) |
| --- | --- |
| P3 | 2026-06-18 to 2026-09-17 |
| P6 | 2026-03-18 to 2026-09-17 |
| P9 | 2025-12-18 to 2026-09-17 |
| P12 | 2025-09-18 to 2026-09-17 |

---

## 8. Validation rules

The generated output must satisfy all of these:

| # | Check | Pass condition |
| --- | --- | --- |
| 1 | Rows = universe x cohorts | `n_rows == N_HCP * n_cohorts` |
| 2 | `HCP_COHORT_ID` unique | distinct count == `n_rows` |
| 3 | No NULLs (first 5 feature columns) | 0 |
| 4 | No negatives (first 5 feature columns) | 0 |
| 5 | Window nesting on `OE_EXPOSURE_TOUCHPOINT` | P3 <= P6 <= P9 <= P12 |
| 6 | Only P3/P6/P9/P12 columns | no other suffix |
| 7 | No cohorts with zero NPP data | **Expected FAIL for c1-c6** (data starts later) |
| 8 | Indication features present | > 0 columns |
| 9 | Content-category features present | > 0 columns |
| 10 | Content tagging file found | file exists (otherwise every tag is GENERAL) |
| 11 | I/E features present | > 0 `_I_P3` / `_E_P3` columns |
| 12 | Excluded vendor absent | no `OE_SFMC_*` |
| 13 | Excluded content absent | no `OE_SAMPLES_COUNT_*` |
| 14 | Engagement/action <= exposure (all columns) | 0 violating rows across every I/E vs R pair (channel, indication, touchpoint) in all windows |
| 15 | Touchpoint totals | each total equals the sum of its channel columns |
| 16 | Supplemental channels present | `OE_MEDSCAPE_BANNER_*`, `OE_MEDSCAPE_PULSEPOINT_BANNER_*`, `OE_MEDSCAPE_BRANDSPOT_*`, `OE_MEDSCAPE_DDTRD_*`, `OE_MEDSCAPE_FAP_*` exist |

Checks 3 and 4 must hold for **all** feature columns, and check 5 for **every** base feature.

---

## 9. Known limitations

* **History starts 2024-11-19 (after the lag).** c1-c6 are all zero, and c7-c9 have only 1-3 periods (their P6/P9/P12 equal P3).
* **Supplemental Medscape mapping is an assumption** (section 6.2); confirm it with the OE owner.
* **MEDSCAPE_BRANDSPOT has no engagement column:** none of its engagement records were attached to an exposed interaction. The reason has not been investigated.
* **Some Medscape records are still dropped:** records whose `TACT_NM` gives no sub-channel (VIEW, MEDIA TIME SPENT, PARTICIPATION, 2024-11 to 2025-01) match no channel rule.
* **No T1D.** There are no T1D records in `CF_INDICATION`.
* **Engagement timing.** An engagement is counted in its exposure's period, even if the open happened a few days later.
* **One exposure per interaction.** An interaction exposed on several days counts as one exposure, dated on its first day.
* **Some PeerDirect placements are dropped:** `PV Compendium Quiz` (Series / Edition, Banner / Web; 13,478 records in 2025 plus some in 2026) and `MD Shuffle` (Banner / Web, 2026) have no channel rule or metric mapping. Accepted for NBA 3.1 (2026-11-23).
* **Records without `UNIQ_NPP_ID` are dropped**, and engagement or action dated after the load end (section 4.2: last day of the last cohort's month minus 7 days, 2026-09-23 for c28) is not counted.
* **Source is rebuilt weekly** (`CREATE OR REPLACE`, about 7 days of time travel), so channel and tag columns can change between runs.
* **Content coverage:** GENERAL is 55.6% of c28 P12 content counts; `ACCESS_COVERAGE`, `MECHANISM_OF_DISEASE`, `PATIENT_PROFILE` and `STUDY_DESIGN` have no HCPs in c28 P12 (2026-11-23 run).

---

## 10. Combine-step notes

* Join on `HCP_COHORT_ID` with the other HCP-level NBA 3.1 feature files. DTC features join on geography, not on this key.
* Features are already 0-filled; do not impute again.
* Exclude c1-c6, or add a history indicator; treat P6/P9/P12 with care for c7-c9.
* `OE_IND_*` columns overlap each other and repeat channel activity, so do not sum them with channel columns.
* HQ Email features come from notebook 15 only (SFMC is excluded here).
