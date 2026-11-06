# OE Promotional Features — NBA 3.1 Family 5: Engagement Depth & Content

**Project:** Kerendia NBA 3.1  
**Family:** 5 — Engagement Depth and Content (non-personal promotional features)  
**Source Pipeline:** Omnichannel Engine (OE) `data_processing.py` → `data_processing_promotion.py`  
**EDA Notebook:** `Email_Processing_Downstream_EDA`  
**Date:** November 2026

---

## 1. End-to-End Feature Creation Pipeline

The pipeline transforms raw Snowflake promotion event tables into HCP-level features through 8 sequential steps.

```
Snowflake Source Tables
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Step 1: Raw Data Ingestion (3 tables)              │
│  FACT_CALL · NPP · EVNT_PRSNL_PROM                  │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 2: Channel-Specific Processing                │
│  calls_processing() · email_processing()            │
│  pp_processing()                                    │
│  → Each produces 8-col IDC DataFrame                │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 3: Concatenation into proto_idc               │
│  pd.concat([calls, emails, events])                 │
│  ~1.95M rows                                        │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 4: Post-Processing (get_transaction_idc)      │
│  +7 day promo lag · YRMO filter · standardize       │
│  nan_handler · deduplication                        │
│  → ~1.94M rows × 10 cols                            │
└──────────────┬───────────────────┬──────────────────┘
               ▼                   ▼
┌──────────────────────┐  ┌───────────────────────────┐
│ Step 5: get_counts() │  │ Step 6: SequenceProcessor │
│ R/I/E pivot per      │  │ Channel + content         │
│ channel + content    │  │ sequences, encodings,     │
│ counts per YRMO      │  │ gap-group sequences       │
└──────────┬───────────┘  └──────────┬────────────────┘
           ▼                         ▼
┌─────────────────────────────────────────────────────┐
│  Step 7: process_timeframes()                       │
│  Aggregate into C1/C3/P3/P6/P12 windows             │
│  + touchpoint rollup features                       │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 8: Final MDB Assembly                         │
│  Merge: sequences + counts + demographics           │
│  → Model-ready DataFrame                            │
└─────────────────────────────────────────────────────┘
```

### Step-by-Step Detail

| Step | Input | Operation | Output |
|------|-------|-----------|--------|
| 1 | Snowflake tables | Pull CALL, NPP, EVNT with 24-month DATE_ID filter | 3 raw Spark DataFrames |
| 2 | Raw DFs + target universe + flag lookup + content tagging | Filter KERENDIA, join target HCPs, derive channels, tag content, map R/I/E flags | 3 pandas IDC DataFrames (8 cols each) |
| 3 | 3 IDC DataFrames | `pd.concat` | Single proto_idc (~1.95M rows) |
| 4 | proto_idc | Date conversion, +7 day promo lag, YRMO filter, standardize columns, handle NaNs, dedup | Cleaned transactions (~1.94M × 10) |
| 5 | transactions | Pivot by CHANNEL_ID × R/I/E metric + pivot by CONTENT_TAG | R/I/E count matrix + content count matrix per CUSTOMER_ID × YRMO |
| 6 | transactions | Daily sequences, integer encodings, gap-group classification | Sequence features per CUSTOMER_ID |
| 7 | count matrices | Sum each metric into C1, C3, P3, P6, P12 time windows | Timeframe-aggregated features per CUSTOMER_ID |
| 8 | All above + demographics | Left-join everything | Final model-ready MDB |

---

## 2. Vendors and Channels in the Data

The pipeline processes **5 target digital vendors** (13 placements) plus **10 personal promo channels**.

### Target Vendors (Non-Personal — Section 3.5 Scope)

| Vendor | Placements | Data Volume (email_processing output) |
|--------|-----------|-------|
| **PulsePoint** | Banner | 959,633 rows (55.4%) |
| **SFMC** | HQ Email | 595,902 rows (34.4%) |
| **Doximity** | DocNews, DocSpot, DocPoint, FormularyOne, Announcement | 109,508 rows (6.3%) |
| **Medscape** | 3rd Party Email, FFQ, RECAP, BrandAlert, EHR | 65,369 rows (3.8%) |
| **PeerDirect** | MDFI - Email, MDFI - Web, MDFI - Banner | (included in NPP) |

### Personal Promo Channels (from calls + events)

| Channel | Source Table | Volume |
|---------|-------------|--------|
| F2F (Face-to-Face) | FACT_CALL | 213,936 rows |
| Phone | FACT_CALL | included |
| Group Call | FACT_CALL | included |
| Remote Call | FACT_CALL | included |
| Speaker Program | EVNT_PRSNL_PROM | 2,079 rows |
| Advisory Board | EVNT_PRSNL_PROM | included |
| Sponsorship | EVNT_PRSNL_PROM | included |
| Scientific Presentation | EVNT_PRSNL_PROM | included |
| Scientific Round Tables | EVNT_PRSNL_PROM | included |
| Market Access / Formulary Assist | EVNT_PRSNL_PROM | included |

> **Note for NBA 3.1:** Section 3.5 features use only the 5 target vendors. Personal channels belong to their own feature families.

---

## 3. Cross-Join with Monthly Cohorts

The OE pipeline natively processes one **date-range instance** at a time (defined in `mdb_prep_config.xlsx`). For NBA 3.1, this must expand to **21 monthly cohorts** matching the claims feature structure.

### Cohort Structure

| Cohort ID | Anchor Date | Lookback Start |
|-----------|------------|----------------|
| `2025-01_offset7` | 7 Feb 2025 | Feb 2024 |
| `2025-02_offset7` | 7 Mar 2025 | Mar 2024 |
| ... | ... | ... |
| `2026-09_offset7` | 6 Oct 2026 | Oct 2025 |

### How Cohorts Intersect with Features

```
For each cohort:
  1. Set anchor_date = month-end + 6 days
  2. Define windows:
     C1  = 1 complete month before anchor
     C3  = 3 complete months before anchor
     P3  = months 4–6 before anchor
     P6  = months 4–9 before anchor
     P12 = months 4–15 before anchor
  3. Filter transactions to the window boundaries
  4. Compute all R/I/E and content features within each window
  5. Output: 1 row per CUSTOMER_ID per COHORT_ID
```

### Output Grain

**CUSTOMER_ID × COHORT_ID** — one row per doctor per monthly prediction date, with all promotional features as columns.

---

## 4. Types of OE Features Created

### 4.1 R/I/E Channel Counts (per placement × metric × time window)

For each of the 13 placements across 5 vendors, three engagement-level counts are produced per time window.

**Example columns:**

| Feature Name | Meaning |
|-------------|--------|
| `DOXIMITY_DOCSPOT_VIEW_R_C3` | Doximity DocSpot reach count, last 3 months |
| `SFMC_HQ_EMAIL_OPEN_I_P6` | SFMC HQ Email interaction count, prior 6 months |
| `PULSEPOINT_BANNER_CLICK_E_C1` | PulsePoint banner engagement count, last 1 month |

**Count:** 13 placements × 3 metrics (R/I/E) × 5 windows = **195 features**

### 4.2 Content-Category Counts (per tag × time window)

15 content categories are counted per CUSTOMER_ID × time window.

| Content Category | Volume (email rows) |
|-----------------|----|
| GENERAL | 864,912 |
| PATIENT_ADHERENCE_SUPPORT | 165,356 |
| COST | 155,652 |
| ACCESS_COVERAGE | 152,682 |
| BASIC_PRODUCT_INFO | 67,634 |
| UNMET_NEED | 61,486 |
| GUIDELINES | 57,505 |
| SAMPLES | 53,971 |
| MECHANISM_OF_DISEASE | 37,666 |
| EFFICACY | 37,033 |
| DISEASE_AWARENESS_MANAGEMENT | 31,589 |
| DOSING_ADMINISTRATION | 14,710 |
| MECHANISM_OF_ACTION | 14,041 |
| STUDY_DESIGN | 13,393 |
| PATIENT_PROFILE | 3,184 |

**Count:** 15 tags × 5 windows = **75 features**

### 4.3 Sequence Features (from SequenceProcessor)

Capture the **temporal ordering** of promotional touches.

| Feature | Description |
|---------|------------|
| `full_channelName_seq` | Complete daily channel sequence (with GAPs for inactive days) |
| `full_channelCode_seq` | Integer-encoded version |
| `channelName_seq` | Activity-only channel sequence (no gaps) |
| `contentName_seq` | Activity-only content sequence |
| `full_channelName_seq_GAP_grp` | Gap-grouped: ZG (0–3 days), LG (4–10), MG (11–17), HG (17+) |
| `full_contentName_seq_GAP_grp` | Gap-grouped content sequence |

**Count:** 6 sequence columns + per-channel and per-content count columns from sequence analysis

### 4.4 Touchpoint Rollup Features (from process_timeframes)

| Feature | Description |
|---------|------------|
| `INTERACTION_TOUCHPOINT_{window}` | Total promotional touchpoints in window |
| `UNIQUE_CHANNELS_{window}` | Number of distinct channels active |

### Summary

| Feature Group | Per YRMO | With Time Windows | Notes |
|---------------|----------|-------------------|-------|
| R/I/E per placement | 39 | 195 | 5 vendors × 13 placements |
| Content counts | 15 | 75 | 14 non-General + General |
| Sequence features | 6+ | N/A | One per customer (full history) |
| Touchpoint rollups | 2 | 10 | Total + unique channels |
| **Total** | **62+** | **280+** | Before feature selection |

---

## 5. Source Table Preprocessing

### 5.1 Calls Table (`FACT_CALL`)

**Snowflake source:** `CPH_DB_PROD.MODEL_V2.FACT_CALL` joined with `MAP_CUSTOMER_XREF`

| Step | What Happens |
|------|-------------|
| Join | Link `SOURCE_CUST_ID` → `BAYER_CUST_ID` (BH_ID) via `MAP_CUSTOMER_XREF` |
| Channel mapping | Map `CALL_REC_TYP_NM` to standardized names: F2F, PHONE, GROUP_CALL, REMOTE_CALL |
| Filter | `STAT = 'SUBMITTED_VOD'`, `DETL_PROD = 'KERENDIA'`, exclude `BHO%` IDs, 24-month lookback |
| Target join | Inner join with modelling universe (`modelling_flag = 'Yes'`, 78,123 HCPs) |
| Date derivation | `DATE_ID` → `EXPOSED_ON` date; `ENGAGED_ON` and `ACTED_ON` set equal to `EXPOSED_ON` (calls have no separate engagement event) |
| Content tag | Hardcoded `CONTENT_TAG = 'General'` (calls carry no content metadata) |
| Output | 8 columns: `CUSTOMER_ID, CHANNEL_ID, CONTENT_TAG, PRODUCT_ID, INTERACTION_ID, EXPOSED_ON, ENGAGED_ON, ACTED_ON` |

### 5.2 NPP Table (`ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS`)

**Snowflake source:** `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` (41 columns)

| Step | What Happens |
|------|-------------|
| Filter | `PROD_BRAND_NM = 'KERENDIA'`, `BAYER_HCP_ID IS NOT NULL`, 24-month lookback |
| Target join | Inner join on `CUST_ID = BH_ID` |
| Date filter | `DATE_ID` → date, filter to [start_boundary, end_boundary] |
| Dedup | Drop duplicates on `[UNIQ_NPP_ID, DATE_ID, CUST_ID, VEND_NM, CHNL_NM, MTR_NM]` |
| Content tagging | Left join with `Content_tagging_6_5.xlsx` on 14 merge columns → assigns `CONTENT_TAG` |
| Channel derivation | Map `TACT_NM` + `VEND_NM` → `CHNL_NM_NEW` (e.g., Doximity + DocNews tactic → `DocNews`) |
| R/I/E flag join | Join with `5_5_2026_Bayer_OE_updated_channel_eng_exp_flag.xlsx` → `Exposure Flag`, `Engagement Flag`, `Acted Flag` |
| Event sequencing | Partition by customer × channel × content × interaction, order by date → separate exposure/engagement/action events |
| Output | Same 8-column IDC schema |

### 5.3 Events Table (`ANLT_BASE_FACT_EVNT_PRSNL_PROM`)

**Snowflake source:** `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` (11 columns)

| Step | What Happens |
|------|-------------|
| Filter | `PROD_BRAND_NM = 'KERENDIA'`, `CUST_HCP_ID IS NOT NULL`, 24-month lookback |
| Target join | Inner join on `CUST_HCP_ID = BH_ID` |
| Dedup | Drop duplicates on `[EVNT_ID, DATE_ID, CUST_HCP_ID, EVNT_CAT, EVNT_TYP, EVNT_SUB_TYP, ATND]` |
| Channel | `EVNT_TYP` becomes `CHANNEL_ID` (Speaker Program, Advisory Board, etc.) |
| Content tag | Hardcoded `CONTENT_TAG = 'General'` |
| Dates | `EXPOSED_ON = ENGAGED_ON = ACTED_ON` (single-event model) |
| Output | Same 8-column IDC schema |

---

## 6. R/I/E Mapping — Reach, Interaction, Engagement

### What It Is

OE uses a **documented mapping of 160 rules** that classifies every vendor metric into one of three engagement levels:

| Level | Code | Meaning | Example |
|-------|------|---------|--------|
| **Reach** | R | Doctor was **shown** the content (impression, email delivered, page served) | PulsePoint impression, SFMC email sent |
| **Interaction** | I | Doctor **opened or viewed** the content (a light response) | Email opened, page viewed, headline clicked |
| **Engagement** | E | Doctor **clicked through or took an action** (a strong response) | Link clicked, form submitted, content downloaded |

### How It Is Applied

1. The mapping lives in **`5_5_2026_Bayer_OE_updated_channel_eng_exp_flag_latest.xlsx`** (`df_flag_new`)
2. Each row in the lookup maps `(VEND_NM, CHNL_NM_NEW, MTR_NM)` → `(Exposure Flag, Engagement Flag, Acted Flag)` as 0/1
3. During `email_processing()`, NPP records are joined to this lookup
4. A single interaction can be:
   * Exposure only (R=1, I=0, E=0) — e.g., banner impression
   * Exposure + Interaction (R=1, I=1, E=0) — e.g., email opened
   * Exposure + Interaction + Engagement (R=1, I=1, E=1) — e.g., email clicked
5. Event sequencing then separates each NPP record into up to 3 dated events (EXPOSED_ON, ENGAGED_ON, ACTED_ON)
6. In `get_counts()`, these are pivoted into separate `{CHANNEL}_{METRIC}_R`, `{CHANNEL}_{METRIC}_I`, `{CHANNEL}_{METRIC}_E` columns

### Why It Matters

R/I/E separates **"the doctor was shown a lot"** from **"the doctor responds"**. PulsePoint has 109M exposures but only 84K engagements (0.08%), while Medscape 3rd-party email has 45% engagement. Without R/I/E, these look the same in a total count.

---

## 7. Content Tagging

### What It Is

A lookup that maps each NPP record to a **content theme** based on the creative, tactic, campaign, and channel metadata of the promotion.

### Source

**`Content_tagging_6_5.xlsx`** (5,883 rows, 22 unique `Content Category` values before cleanup)

### How It Works

1. The lookup is joined to NPP records on **14 merge columns**: `CHNL_NM, VEND_NM, LITCODE, CNTT_NM, EMAIL_SUBJ_LN, CRTV_NM, TACT_NM, CPGN_NM, PRMRY_KEY_MSG, CF_NAME, CF_INDICATION, RPT_CHNL, CHNL_TYP, TACT_TYP`
2. Before joining, both sides are cleaned: trimmed, lowercased, special characters replaced with underscores, missing values set to `"_"`
3. The join assigns `Content Category` → renamed to `CONTENT_TAG`
4. Unmatched rows (null, `"-"`, `"Not Needed"`) default to `"General"`

### Coverage

* **50% of email rows** receive a specific (non-General) content tag
* **Calls and events** are always `"General"` (no content metadata in those tables)
* After standardization, 15 final content categories remain in the feature set

### What Content Tags Tell the Model

Content tagging answers: **"What topic was the doctor shown?"** — not just how many times they were reached. A doctor shown "Access & Coverage" content 10 times signals something different from one shown "Efficacy" content 10 times. OE's own model found all 13 content-category counts were kept by feature selection.

---

## 8. Business-Level Explanation of Features

### What These Features Tell the NBA Model

Each feature answers a specific business question about a doctor's digital promotional experience:

| Feature Group | Business Question | Example Insight |
|--------------|-------------------|----------------|
| **R counts per placement** | How much was this doctor **shown** Kerendia content, and on which platform? | "Dr. Smith saw 47 PulsePoint banners and 3 Doximity DocSpot articles in the last 3 months" |
| **I counts per placement** | Did the doctor **open or view** what was sent? | "Dr. Smith opened 2 of 5 HQ emails (40% open rate)" |
| **E counts per placement** | Did the doctor **click through or take action**? | "Dr. Smith clicked through on a Medscape 3rd-party email — a strong signal" |
| **Content counts** | What **topics** resonate with this doctor? | "Dr. Smith has been shown mostly Access & Coverage and Cost content" |
| **Time-window comparison** | Is digital engagement **rising or falling**? | "Dr. Smith's interactions in the last 3 months are double the prior 3 months" |
| **Sequence features** | What is the **pattern** of promotional touches over time? | "Dr. Smith's journey: Banner → Email → DocSpot → (12-day gap) → Banner" |
| **Touchpoint rollups** | How **broadly** is this doctor being reached? | "Dr. Smith is reached on 4 different channels from 3 vendors" |

### How These Features Improve NBA 3.1 Over NBA 3.0

| Dimension | NBA 3.0 | NBA 3.1 (OE Family 5) |
|-----------|---------|------------------------|
| **Engagement depth** | "Total exposure" and "total engagement" (no definition of what counts) | R/I/E per placement with documented rules |
| **Content** | Not available | 15 content categories, answering "what was the topic?" |
| **Vendor detail** | Grouped into channel/vendor/tactic pivots; no named placements | Each vendor × placement tracked individually |
| **PulsePoint separation** | 93.7% of exposure is PulsePoint; drowns other signals | Separate PulsePoint from other vendors; engagement rates expose low-response channels |
| **Schema stability** | Dynamic pivots — columns change between runs | Fixed schema from config; same columns every run |
| **Deduplication** | Same HQ email counted 3 times (in Digital, as channel, as vendor) | Each activity counted once through OE event-level dedup |

### Expected Feature Count for NBA 3.1

| Category | Raw Features | After Selection (target) |
|----------|-------------|------------------------|
| R/I/E × placement × window | 195 | ~20–30 |
| Content × window | 75 | ~10–15 |
| Sequences + rollups | 16+ | ~5–10 |
| **Total** | **286+** | **40–60** |

---

## Appendix: Key Configuration Files

| File | Purpose |
|------|---------|
| `mdb_prep_config.xlsx` | Date ranges, metric mappings (R/I/E), column lists |
| `5_5_2026_Bayer_OE_updated_channel_eng_exp_flag_latest.xlsx` | R/I/E flag lookup per vendor × channel × metric |
| `Content_tagging_6_5.xlsx` | Content category assignment per NPP creative/tactic |
| `13_5_oe_modelling_universe_final` (Delta) | Target HCP universe (78,123 doctors with `modelling_flag = 'Yes'`) |
| `temp_kerendia_hcp_attr` (Delta) | HCP demographics (specialty, scores, affiliation) |

## Appendix: Source Tables

| Snowflake Table | What It Contains | Volume |
|----------------|-----------------|--------|
| `CPH_DB_PROD.MODEL_V2.FACT_CALL` | Rep call records (F2F, phone, remote, group) | ~958K rows (24 months) |
| `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` | Digital/email promotions (all vendors) | ~409M rows (24 months) |
| `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | Speaker programs, advisory boards, events | ~70K rows (24 months) |