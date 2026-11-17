# Feature Dictionary — NBA 3.1 Non-Personal Promotional Features

**Last updated:** 2026-11-13  
**Scope:** 4 notebooks producing ZIP-level (DTC) and HCP-level (Digital, HQ Email, High Intent) promotional features for all 28 NBA 3.1 cohorts (c1–c28).

---

## 1. Summary

| Notebook | Grain | Features | Output rows | Distinct units | Cohorts |
|---|---|---|---|---|---|
| `34_promotional_features_DTC` | ZIP5 × cohort | 8 | 904,540 | 32,305 ZIPs | 28 |
| `24_Features_Digital_NBA31` | HCP × cohort | 144 | 8,252,328 | 294,726 HCPs | 28 |
| `15_promotional_features_HQ_Emails_new` | HCP × cohort | 15 | 3,112,543 \* | 162,557 HCPs \* | 28 |
| `25_Features_High_Intent_Signals_NBA31` | HCP × cohort | 28 | 8,252,328 | 294,726 HCPs | 28 |

\* HQ Emails only stores rows for HCPs with any email activity in the last 12 months or currently unsubscribed. The combine step fills missing HCPs with counts = 0, `HQ_EMAILABLE_FLAG` = 1, rates/trend/days = NULL.

---

## 2. Common Framework

### 2.1 Cohorts
- **Source:** `kerendia_nba_3_1_volume/cohorts/promotional/cohorts.parquet`
- **28 cohorts** c1 (SVC_DT 2024-06-17) .. c28 (SVC_DT 2026-09-17), monthly cadence, lookback end = 17th of each month
- **Training:** c1–c24 · **Testing:** c25–c26 · **Holdout (Backtesting):** c27–c28
- **Window definition:** `(LOOKBACK_END_DATE − w months, LOOKBACK_END_DATE]` — left-exclusive, right-inclusive

### 2.2 HCP Universe (HCP-level notebooks only)
- **Source:** `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/`
- **294,726 PROVIDER_IDs** (call HCPs excluded by design)
- **Doctor key:** `PROVIDER_ID` (same mapping table `SOURCE_PROVIDER_BHID_NPI_MAPPING` across all three HCP notebooks)
- **Join key:** `HCP_COHORT_ID = PROVIDER_ID + "_" + COHORT`

### 2.3 NULL vs 0 convention
- **Counts / flags / recency-sentinel features** → always filled (0 or sentinel 999) for every HCP × cohort row
- **Rate / trend / days-since features** → NULL when the denominator is 0 or insufficient history exists
- **DTC features** → NULL when the data window is not fully inside the source data range (not 0)

---

## 3. DTC Features — `34_promotional_features_DTC`

### 3.1 Sources & Geography

| Channel | Source (Snowflake) | Geography | Data start |
|---|---|---|---|
| Social (Facebook + Instagram) | `BAYER_CPHCDP_PROD.FACEBOOK_ADS.*` | DMA level | Jan 2024 |
| Search (SA360 DTC patient campaigns) | `BAYER_CPHCDP_PROD.NEW_SEARCH_ADS_360.*` | State level | Jan 2025 |

- **Search filter:** campaign name starts with `KER_DTC_` (excludes `KER_HCP_` doctor-search campaigns)
- **CA subregions:** "San Francisco Bay Area" and "Silicon Valley" collapsed to "California" for state-level search
- **Population denominator:** ACS 18+ adult population by DMA (`dma_pop`) and state (`state_pop`)
- **Cohort month (CM):** last complete calendar month on or before CUTOFF_DT (e.g. c28 CUTOFF 2026-09-17 → CM = 2026-08-01)

### 3.2 Business Rules

| Rule | Description |
|---|---|
| D1 | Only complete calendar months are used (no partial months) |
| D2 | DMA names from Facebook are fuzzy-matched to DMA codes via a canonical CSV; unmatched < 1% are dropped |
| D3 | 1M window = cohort month only; 3M window = cohort month − 2 .. cohort month |
| D6 | **Click outlier correction:** compute national CTR per month; any month where CTR > 2.0 × median CTR has its clicks replaced by `impressions × median_CTR` |
| D7 | Features are **NULL** (not 0) when the required window extends beyond the source data range |
| D8 | `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_1M` is computed internally but excluded from final FEATURES (1M click window too noisy) |

### 3.3 Feature Formulas

All per-1K features share the formula:
```
metric_per_1k = sum(raw_metric in window) / (ADULTS / 1000)
             = NULL  if window not fully in data OR ADULTS = 0
```

| Feature | Channel | Geo | Window | Formula | NULL when |
|---|---|---|---|---|---|
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_1M` | Social | DMA | 1M | `IMP_CM / (DMA_adults / 1000)` | CM not in social data |
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_3M` | Social | DMA | 3M | `IMP_(CM-2..CM) / (DMA_adults / 1000)` | 3M window not fully in data |
| `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` | Social | DMA | 3M | `CLK*_(CM-2..CM) / (DMA_adults / 1000)` | 3M window not fully in data |
| `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` | Social | DMA | Full history | `coalesce(min_k_where_IMP>0, months_since_Jan2024 + 1)` | Never NULL |
| `DTC_SEARCH_IMPRESSIONS_PER_1K_ADULTS_3M` | Search | State | 3M | `IMP_(CM-2..CM) / (state_adults / 1000)` | 3M window not fully in data |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_1M` | Search | State | 1M | `CLK_CM / (state_adults / 1000)` | CM not in search data |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_3M` | Search | State | 3M | `CLK_(CM-2..CM) / (state_adults / 1000)` | 3M window not fully in data |
| `DTC_SEARCH_MONTHS_SINCE_LAST_CAMPAIGN` | Search | State | Full history | `coalesce(min_k_where_IMP>0, months_since_Jan2025 + 1)` | Never NULL |

**CLK\*** = outlier-corrected clicks (rule D6): replaced by `IMP × median_national_CTR` for any month flagged as outlier.

**MONTHS_SINCE formula detail:**  
`k = months_between(CM, MONTH)` for each historical month; `MSL = min(k where IMP > 0)`.  
Value 0 = active in cohort month · 1 = active last month · N = last active N months ago · never active = `months_since_data_start + 1`.

### 3.4 Fill Rates (observed)

| Feature | Fill Rate | Note |
|---|---|---|
| `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` | 100% | Always non-null by design |
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_1M` | 89.3% | c1–c3: CM before Jan 2024 |
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_3M` | 89.3% | Same cohorts |
| `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` | 89.3% | Same cohorts |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_1M` | 71.4% | c1–c8: CM before Jan 2025 |
| `DTC_SEARCH_MONTHS_SINCE_LAST_CAMPAIGN` | 71.4% | Same cohorts |
| `DTC_SEARCH_IMPRESSIONS_PER_1K_ADULTS_3M` | 64.3% | c1–c9: 3M window not fully in data |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_3M` | 64.3% | Same cohorts |

---

## 4. Digital Paid Media Features — `24_Features_Digital_NBA31`

### 4.1 Source & Mapping
- **Source:** `kerendia_oe_journey.mmx_fnl_combined_aggr_tab` (Unity Catalog copy of Snowflake MMX)
- **Brand filter:** `UPPER(BRND_NM) LIKE '%KERENDIA%'` (broader than NBA 3.0 `= 'KERENDIA'`)
- **Data start:** Jan 2025 (first MMX paid-media row in UC copy)
- **Doctor key:** NPI (`NPI_NUM`) → `PROVIDER_ID` via `SOURCE_PROVIDER_BHID_NPI_MAPPING`
- **Placement dictionary:** 44 rules, 38 named placements, 18 vendors (SHA256 version hash `de095a100b`)

### 4.2 Business Rules

| Rule | Description |
|---|---|
| Exclusions | HQ Email (family 2), iRep (family excluded), and CALL rows are excluded from paid-media features |
| Family 1 | Only PAID_MEDIA role rows contribute to features |
| Unmapped rows | Any row not matched by the placement dictionary is flagged as `PAID_MEDIA_UNMAPPED`; alert if > 1% |
| History months | `DIGITAL_HISTORY_MONTHS` = complete months of data before cohort end (0–12); c1–c8 have 0 (no data before Jan 2025) |
| Trend NULL gate | Trend features (`_VS_PRIOR_3M`) are NULL when `DIGITAL_HISTORY_MONTHS < 6` |
| Recency sentinel | 999 days when no event in last 12 months |
| Indication | `CF_INDICATION` column (when present) + `BRND_NM` used to tag HF / CKD / BOTH |

### 4.3 Feature Families & Formulas

#### Family P1 — Total paid media (16 features)
Pattern: `DIGITAL_TOTAL_{METRIC}_{w}M` and `DIGITAL_TOTAL_XPP_{METRIC}_{w}M`  
for `METRIC` ∈ {EXPOSURE, ENGAGEMENT}, `w` ∈ {1, 3, 6, 12}

```
DIGITAL_TOTAL_EXPOSURE_{w}M   = sum(EXP_ALL  in last w months)
DIGITAL_TOTAL_ENGAGEMENT_{w}M = sum(ENG_ALL  in last w months)
DIGITAL_TOTAL_XPP_EXPOSURE_{w}M   = sum(EXP excluding PulsePoint programmatic display)
DIGITAL_TOTAL_XPP_ENGAGEMENT_{w}M = sum(ENG excluding PulsePoint programmatic display)
```

#### Family P2 — Channel totals (24 features)
Pattern: `DIGITAL_CH_{CHANNEL}_{METRIC}_{w}M`  
for `CHANNEL` ∈ {BANNER, 3P_EMAIL, CUSTOM}, `METRIC` ∈ {EXPOSURE, ENGAGEMENT}, `w` ∈ {1, 3, 6, 12}

```
DIGITAL_CH_BANNER_EXPOSURE_{w}M = sum(EXP where CHANNEL = BANNER in last w months)
```

#### Family P3 — Vendor × placement (76 features)
Pattern: `DIGITAL_PLC_{PLACEMENT}_{METRIC}_{w}M`  
for each of 38 placements × {(EXPOSURE, 3M), (ENGAGEMENT, 6M)}

Examples: `DIGITAL_PLC_MEDSCAPE_BANNER_EXPOSURE_3M`, `DIGITAL_PLC_DOXIMITY_DOCNEWS_ENGAGEMENT_6M`

```
DIGITAL_PLC_{PLACEMENT}_EXPOSURE_3M   = sum(EXP for mapped placement in last 3 months)
DIGITAL_PLC_{PLACEMENT}_ENGAGEMENT_6M = sum(ENG for mapped placement in last 6 months)
```

#### Family P4 — Engagement rates (7 features)
```
DIGITAL_ENGAGEMENT_RATE_{w}M         = ENGAGEMENT_{w}M / EXPOSURE_{w}M   (NULL if no exposure; can exceed 1)
DIGITAL_XPP_ENGAGEMENT_RATE_6M       = XPP_ENGAGEMENT_6M / XPP_EXPOSURE_6M
DIGITAL_CH_BANNER_ENGAGEMENT_RATE_6M = CH_BANNER_ENGAGEMENT_6M / CH_BANNER_EXPOSURE_6M
DIGITAL_CH_3P_EMAIL_ENGAGEMENT_RATE_6M
DIGITAL_CH_CUSTOM_ENGAGEMENT_RATE_6M
```
Windows: overall rate at 3M, 6M, 12M; channel-specific at 6M only.

#### Family P5 — Recency (4 features)
```
DIGITAL_DAYS_SINCE_LAST_EXPOSURE                = datediff(END, max(EVENT_DT where EXP > 0 in 12M))
DIGITAL_DAYS_SINCE_LAST_ENGAGEMENT              = datediff(END, max(EVENT_DT where ENG > 0 in 12M))
DIGITAL_CH_3P_EMAIL_DAYS_SINCE_LAST_ENGAGEMENT  = same, 3P_EMAIL channel only
DIGITAL_CH_CUSTOM_DAYS_SINCE_LAST_ENGAGEMENT    = same, CUSTOM channel only
```
Sentinel: **999** when no event in last 12 months (never NULL).

#### Family P6 — Diversity (5 features)
```
DIGITAL_N_VENDORS_3M        = countDistinct(VENDOR in last 3M)
DIGITAL_N_VENDORS_12M       = countDistinct(VENDOR in last 12M)
DIGITAL_N_PLACEMENTS_3M     = countDistinct(PLACEMENT in last 3M)
DIGITAL_N_ACTIVE_MONTHS_6M  = count(distinct months with any paid-media activity in last 6M)
DIGITAL_N_ACTIVE_MONTHS_12M = count(distinct months with any paid-media activity in last 12M)
```

#### Family P7 — Trend (3 features)
```
DIGITAL_EXPOSURE_3M_VS_PRIOR_3M    = (EXP_last3M - EXP_prior3M) / (EXP_last3M + EXP_prior3M)
DIGITAL_ENGAGEMENT_3M_VS_PRIOR_3M  = (ENG_last3M - ENG_prior3M) / (ENG_last3M + ENG_prior3M)
DIGITAL_XPP_EXPOSURE_3M_VS_PRIOR_3M = same without PulsePoint
```
Range: −1..1; 0 if both windows are 0; **NULL** when `DIGITAL_HISTORY_MONTHS < 6`.

#### Family IND — Indication (9 features)
Pattern: `DIGITAL_IND_{IND}_{METRIC}_{w}M`  
for `IND` ∈ {HF, CKD, BOTH}, `(METRIC, w)` ∈ {(EXPOSURE, 3M), (EXPOSURE, 6M), (ENGAGEMENT, 6M)}

```
DIGITAL_IND_HF_EXPOSURE_3M = sum(EXP where indication tag = 'HF' in last 3M)
```

### 4.4 Fill Rates (observed)

| Feature group | Fill Rate | Note |
|---|---|---|
| All count features (P1–P3, P6, IND) | 100% | Always 0 when no activity |
| All recency features (P5) | 100% | Sentinel 999 when no activity |
| Trend features (P7) | 53.6% | NULL for c1–c13 (< 6 months digital history) |
| Engagement rate 12M (P4) | 29.3% | NULL when no exposure |
| Engagement rate 6M | 26.4% | |
| Engagement rate 3M | 22.8% | |
| Channel-specific rates | 12–23% | |

---

## 5. HQ Email Features — `15_promotional_features_HQ_Emails_new`

### 5.1 Source & Doctor Key
- **Source:** Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS`
- **Filter:** `UPPER(PROD_BRAND_NM) LIKE '%KERENDIA%'` AND `UPPER(CHNL_ID) = 'HQ EMAIL'`
- **Data start:** Loaded from Jun 2023 (c1 earliest lookback start is 2023-06-17)
- **Doctor key:** NPI from source (`NPI_NUM`) → `PROVIDER_ID`; fallback BH_ID → NPI via `kerendia_oe_npi_bhid_mapping_inference` → `PROVIDER_ID`
- **HQ email is the ONLY source** — it is explicitly excluded from Digital (MMX) features to avoid double-counting

### 5.2 Event Types

| Source MTR_NM | Internal EVENT | Description |
|---|---|---|
| SENT | SENT | Email dispatched |
| DELIVERED | DELIVERED | Email accepted by recipient server |
| OPENED | OPEN | Recipient opened the email |
| CLICKED | CLICK | Recipient clicked a link |
| UNSUBSCRIBED | UNSUB | Opt-out event |
| HARD BOUNCE | HARD_BOUNCE | Permanent delivery failure (invalid address) |
| *any BOUNCE* | OTHER_BOUNCE | Soft / block / technical / unknown bounce |

### 5.3 Business Rules

| Rule | Description |
|---|---|
| D1 | Single source: `ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` only (not MMX) |
| D2 | NPI from source preferred; BH_ID fallback via OE mapping table |
| D3 | Event types kept separate (not lumped); new MTR values assert-fail if unrecognised |
| D4 | Only HCPs in the NBA 3.1 universe are retained |
| D5 | Rates are **unique-email based** (not raw event counts); capped at 1.0 |
| D6 | `HQ_EMAILABLE_FLAG` = 1 if NOT unsubscribed AND latest hard bounce (if any) is followed by a delivered email |
| D7 | Only HCPs with any activity in 12M or currently unsubscribed are stored (save output size); missing HCPs → 0/NULL in combine |
| `HQ_HISTORY_MONTHS` | Complete months of source data before cohort end (0–12); prevents "no data" from being read as "no email" |

### 5.4 Feature Formulas

| Feature | Kind | Window | Formula |
|---|---|---|---|
| `HQ_EMAIL_SENT_1M` | COUNT | 1M | `sum(N for SENT events in window)` |
| `HQ_EMAIL_SENT_3M` | COUNT | 3M | `sum(N for SENT events in window)` |
| `HQ_EMAIL_SENT_12M` | COUNT | 12M | `sum(N for SENT events in window)` |
| `HQ_EMAIL_UNIQUE_OPENS_3M` | COUNT | 3M | `countDistinct(EMAIL_NM for OPEN events in window)` |
| `HQ_EMAIL_UNIQUE_OPENS_12M` | COUNT | 12M | `countDistinct(EMAIL_NM for OPEN events in window)` |
| `HQ_EMAIL_UNIQUE_CLICKS_12M` | COUNT | 12M | `countDistinct(EMAIL_NM for CLICK events in window)` |
| `HQ_EMAIL_OPEN_RATE_6M` | RATE | 6M | `min(unique_opens_6M / unique_sent_6M, 1.0)` — NULL if sent_6M = 0 |
| `HQ_EMAIL_CLICK_RATE_6M` | RATE | 6M | `min(unique_clicks_6M / unique_sent_6M, 1.0)` — NULL if sent_6M = 0 |
| `HQ_EMAIL_OPENS_3M_VS_PRIOR_3M` | TREND | 6M | `(opens_3M − opens_prior_3M) / (opens_3M + opens_prior_3M)` — NULL if sum = 0 |
| `HQ_EMAIL_HARD_BOUNCE_FLAG_12M` | FLAG | 12M | `1 if any HARD_BOUNCE event in window` |
| `HQ_EMAIL_UNSUBSCRIBED_FLAG` | FLAG | Full history | `1 if latest_UNSUB ≥ latest_DELIVERED (or no DELIVERED)` |
| `HQ_EMAILABLE_FLAG` | FLAG | Full history | `1 if NOT unsubscribed AND NOT (latest_HARD_BOUNCE ≥ latest_DELIVERED)` |
| `HQ_EMAIL_DAYS_SINCE_LAST_SENT` | DAYS | Full history | `datediff(CUTOFF, max(SENT event date))` — NULL if never sent |
| `HQ_EMAIL_DAYS_SINCE_LAST_OPEN` | DAYS | Full history | `datediff(CUTOFF, max(OPEN event date))` — NULL if never opened |
| `HQ_EMAIL_DAYS_SINCE_LAST_CLICK` | DAYS | Full history | `datediff(CUTOFF, max(CLICK event date))` — NULL if never clicked |

**Note on SENT vs UNIQUE_OPENS:**  
`SENT` counts raw event rows (one per send dispatch), so the same email sent twice = 2.  
`UNIQUE_OPENS` counts distinct `EMAIL_NM` with ≥1 open — the same email opened 5 times = 1.  
This difference prevents repeated-open campaigns from inflating engagement signals.

### 5.5 Fill Rates (observed)

| Feature | Fill Rate | Note |
|---|---|---|
| `HQ_EMAIL_SENT_1/3/12M` | 100% | |
| `HQ_EMAIL_UNIQUE_OPENS_3/12M` | 100% | |
| `HQ_EMAIL_UNIQUE_CLICKS_12M` | 100% | |
| `HQ_EMAIL_UNSUBSCRIBED_FLAG` | 100% | |
| `HQ_EMAIL_HARD_BOUNCE_FLAG_12M` | 100% | |
| `HQ_EMAILABLE_FLAG` | 100% | |
| `HQ_EMAIL_DAYS_SINCE_LAST_SENT` | ~100% (1 null) | |
| `HQ_EMAIL_OPEN_RATE_6M` | 79.3% | NULL when nothing sent in 6M |
| `HQ_EMAIL_CLICK_RATE_6M` | 79.3% | Same condition |
| `HQ_EMAIL_DAYS_SINCE_LAST_OPEN` | 64.6% | NULL when never opened |
| `HQ_EMAIL_OPENS_3M_VS_PRIOR_3M` | 39.0% | NULL when both windows are 0 |
| `HQ_EMAIL_DAYS_SINCE_LAST_CLICK` | 9.9% | NULL when never clicked — click engagement is rare |

---

## 6. High Intent Signal Features — `25_Features_High_Intent_Signals_NBA31`

### 6.1 Sources

| Signal | Source | Doctor key | Data start |
|---|---|---|---|
| Request-a-Rep (RAR) | Snowflake `PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB` | BH_ID | Jan 2025 |
| New Writer (Kerendia Rx) | Delta `kerendia_nba_3_1_volume/.../kerendia_claims_monthly_from_raw_fct_rx` | PROVIDER_ID | Jul 2021 |
| Impiricus SMS | MMX (`mmx_fnl_combined_aggr_tab`, `SRC_SYS_CD = IMPIRICUS`, tactic LIKE `%SMS%`) | NPI | Jan 2025 |

### 6.2 Business Rules

| Rule | Description |
|---|---|
| RAR window | Only requests with `REQUEST_DT ≤ cohort END` are used (no leakage) |
| RAR open definition | A request is **open** if it is within the last `RAR_OPEN_DAYS = 90` days AND has no follow-up of any type (call / sample / iRep / HQ) on or before the cohort end |
| Follow-up | CALL, SAMPLE, IREP, HQ — must be `≥ REQUEST_DT` AND `≤ END` to count |
| New writer | First month with `TRX_KERENDIA_OVERALL > 0`; only **complete** months before cohort END are used (partial last month excluded to prevent leakage) |
| SMS | Exposure = `SMS_SENT`; engagement = `SMS_ENG > 0`; from MMX Impiricus rows only |
| Zero-fill | All COUNT and FLAG features are filled to 0 for HCPs with no activity (full 294,726 × 28 grid) |
| Recency sentinel | **999** for DAYS_SINCE features when no event in 12M (not NULL) |
| `MONTHS_SINCE_FIRST_KERENDIA_RX` sentinel | **999** when doctor has never written Kerendia |

### 6.3 Feature Formulas

#### Family RAR_ALL — All requests (8 features)

| Feature | Formula |
|---|---|
| `RAR_COUNT_3M` | `sum(1 if REQUEST_DT in (END−3M, END])` |
| `RAR_COUNT_6M` | `sum(1 if REQUEST_DT in (END−6M, END])` |
| `RAR_COUNT_12M` | `sum(1 if REQUEST_DT in (END−12M, END])` |
| `RAR_LAST_6M_FLAG` | `1 if any request in (END−6M, END]` |
| `DAYS_SINCE_LAST_RAR` | `datediff(END, max(REQUEST_DT in 12M))` — 999 if none |
| `RAR_OPEN_REQUEST_FLAG` | `1 if any request where datediff(END, REQUEST_DT) < 90 AND no follow-up (call/sample/iRep/HQ) by END` |
| `RAR_TYPE_SAMPLES_FLAG` | `1 if any request in 12M where REQUEST_TYPE contains 'SAMPL'` |
| `RAR_TYPE_CONTACT_BY_REP_FLAG` | `1 if any request in 12M where REQUEST_TYPE contains 'CONTACT BY REP'` |

#### Families RAR_CALL / RAR_SAMPLE / RAR_HQ / RAR_IREP — Per follow-up type (10 features)

| Feature | Formula |
|---|---|
| `RAR_{TYPE}_COUNT_12M` | `sum(1 if request in 12M AND {TYPE}_DT ≥ REQUEST_DT AND ≤ END)` |
| `RAR_{TYPE}_SHARE_12M` | `RAR_{TYPE}_COUNT_12M / RAR_COUNT_12M` — NULL if `RAR_COUNT_12M = 0` |
| `RAR_OPEN_NO_CALL_FLAG` | `1 if any request in last 90 days with no CALL follow-up by END` |
| `RAR_OPEN_NO_SAMPLE_FLAG` | `1 if any request in last 90 days with no SAMPLE follow-up by END` |

#### Family NEW_WRITER — First Kerendia prescription (5 features)

| Feature | Formula |
|---|---|
| `NEW_WRITER_LAST_3M_FLAG` | `1 if FIRST_RX_M ≥ add_months(LAST_M, −2)` (i.e. in the last 3 complete months) |
| `NEW_WRITER_LAST_6M_FLAG` | `1 if FIRST_RX_M ≥ add_months(LAST_M, −5)` |
| `NEW_WRITER_LAST_12M_FLAG` | `1 if FIRST_RX_M ≥ add_months(LAST_M, −11)` |
| `KERENDIA_WRITER_EVER_FLAG` | `1 if FIRST_RX_M ≤ LAST_M` (any Kerendia Rx up to last complete month) |
| `MONTHS_SINCE_FIRST_KERENDIA_RX` | `months_between(LAST_M, FIRST_RX_M)` — 0 = started this month; 999 if never |

`LAST_M` = last complete calendar month before cohort END = `trunc(END, 'month') − 1 month`.

#### Family SMS — Impiricus SMS (5 features)

| Feature | Formula |
|---|---|
| `SMS_SENT_3M` | `sum(SMS_SENT in (END−3M, END])` |
| `SMS_SENT_12M` | `sum(SMS_SENT in (END−12M, END])` |
| `SMS_ENGAGED_3M_FLAG` | `1 if any SMS_ENG > 0 in (END−3M, END]` |
| `SMS_ENGAGED_12M_FLAG` | `1 if any SMS_ENG > 0 in (END−12M, END]` |
| `DAYS_SINCE_LAST_SMS` | `datediff(END, max(EVENT_DT where SMS_SENT + SMS_ENG > 0 in 12M))` — 999 if none |

### 6.4 Fill Rates (observed)

| Feature | Fill Rate | Note |
|---|---|---|
| All COUNT / FLAG / DAYS features (24) | 100% | 0 or sentinel 999 for no-activity rows |
| `RAR_CALL_SHARE_12M` | 0.03% | Only non-null for HCPs with ≥1 RAR request in 12M |
| `RAR_SAMPLE_SHARE_12M` | 0.02% | Same |
| `RAR_IREP_SHARE_12M` | ~0% | Same |
| `RAR_HQ_SHARE_12M` | ~0% | Same — only 1,397 total RAR requests across all 8.25M HCP×cohort rows |

---

## 7. Key Insights

### 7.1 Data Coverage by Cohort
- **Social DTC** is fully populated from c4 onwards (3M window inside Jan 2024 start); c1–c3 have ~11% null social features.
- **Search DTC** is fully populated from c10 onwards (3M window inside Jan 2025 start); c1–c9 have null search features.
- **Digital paid media** has zero history for c1–c8 (all DIGITAL_HISTORY_MONTHS = 0 — no MMX data before Jan 2025). First trend-eligible cohort is c14 (6 complete months).
- **RAR signals** are absent for c1–c7 (data starts Jan 2025); first requests appear at c8.
- **New Writer** has full history from Jul 2021 — covers all 28 cohorts.
- **HQ Email** has full 12-month windows for all cohorts (data loaded from Jun 2023).

### 7.2 Activity Sparsity
- Digital: 173,449 of 294,726 HCPs (58.8%) saw any paid-media activity across the full data range; engagement (clicks) is far sparser than exposure (impressions) — engagement rates range 12–29%.
- HQ Email: Only 162,557 unique HCPs appear in the output (55% of universe), reflecting that ~45% had no email contact and are not unsubscribed. Among those with emails, click engagement is very rare (days-since-last-click fill rate = 9.9%).
- RAR: Only 1,397 total Request-a-Rep interactions across the entire dataset — an extremely rare high-intent signal. The share features (RAR_*_SHARE_12M) are ~0% filled and will be near-zero for most cohorts. The most common follow-up to a RAR is a rep call (265 of 422 requests in c28).
- New Writer: 84,389 doctors (28.6% of universe) have ever written Kerendia as of c28. Adoption is growing: 17,900 new writers in 2026 (through Oct) vs 15,369 in 2023.
- SMS: Impiricus SMS only became active from Mar 2025. Engagement rates are very low (~1.5–2%). Only 5 active months in the data, with Dec 2025 being the largest (3,116 providers reached).

### 7.3 Signal Quality Notes
- **DTC per-1K features** are area-level signals (not individual), making them proxies for local market pressure rather than direct HCP exposure. Social at DMA level is coarser than search at state level for some rural areas.
- **Digital rates (P4)** can exceed 1.0 when engagement (e.g. clicks on a banner) is counted per row and the same event fires multiple times — the XPP (without PulsePoint) rate is a more reliable engagement signal since PulsePoint programmatic display is high-volume / low-engagement.
- **HQ_EMAILABLE_FLAG** is a production-ready eligibility gate for the HQ email action: only HCPs with this flag = 1 should receive HQ emails. As of c28, the flag is 1 for the vast majority of the universe (the unsubscribe / bounce exclusion is relatively rare).
- **RAR_OPEN_REQUEST_FLAG** directly feeds the NBA dropdown list (48 open HCPs at c28 cutoff 2026-09-17) and should be treated as the highest-priority engagement signal in the NBA model — a rep should follow up within the 90-day window.
- **MONTHS_SINCE_FIRST_KERENDIA_RX** (sentinel 999 = never) combined with **KERENDIA_WRITER_EVER_FLAG** distinguishes never-writers (potential targets) from lapsed writers (re-activation opportunities) from recent adopters.

### 7.4 Combine Step Notes
- DTC features join on `[ZIP5, DMA_CODE, STATE_NAME, COHORT]`; HCP-level features join on `HCP_COHORT_ID`.
- Features with `NULL_IN_COMBINE = True` (rates, trend, days-since in HQ Email; engagement rates and trend in Digital) stay NULL after the combine — they should **not** be imputed with 0.
- HQ Email is now the **only** source for HQ email signals. The 12 `DIGITAL_HQ_EMAIL_*` features in notebook 51 (P8 family) describe the same activity — one of the two must be dropped in the combine step to avoid double-counting (decision D8, open).
- DTC `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_1M` is computed internally but intentionally excluded from the final feature set.
