# Additional Features — Personal Promotional Channels (NBA 3.1)

**Scope:** Sales Rep Calls (`25`), iRep Emails (`16`), ClickStream / CLM (`18`)  
**Folder:** `NBA 3.1 - Dev/04_Promotional_Features/`  
**Built from:** line-by-line review of the three NBA 3.1 Dev notebooks (current feature sets verified from the `withColumn` / `alias` code)  
**Date:** October 22, 2026

This file proposes additional features for each personal promotional channel, organized by category: volume, ratio/rate, recency, diversity, cross-product, trend, and cross-channel. Each proposal notes the computation and why it adds value beyond the existing features. 


---

## 1. Sales Rep Calls (`25_promotional_features_call`)

### Current feature inventory (35 base × 6 windows = 210)

| Group | Count | Features |
| --- | --- | --- |
| Channel | 4 | `F2F`, `PHONE`, `GROUP_CALL`, `REMOTE_CALL` |
| Call type | 5 | `DETAIL_ONLY`, `DETAIL_WITH_SAMPLE`, `GROUP_DETAIL`, `GROUP_DETAIL_WITH_SAMPLE`, `EVENT_DETAIL` |
| Call purpose | 5 | `PROMOTIONAL_ACTIVITY`, `..._WITH_MEAL`, `EVENT_RELATED_...`, `NON_PROMOTIONAL_ACTIVITY`, `MISCELLANEOUS` |
| Duration | 1 | `CALL_DURATION` (sum) |
| Cross products | 20 | channel × call type via `least()` |

All are windowed cumulative SUMs over 30/60/90/120/150/180 days. There are no ratios, recency, diversity, or trend features.

### Proposed additions

#### 1A. Volume and overall count

| Feature | Computation | Rationale |
| --- | --- | --- |
| `TOTAL_CALLS` | `sum(1)` per HCP-cohort-day, then rolling SUM | The overall call count is only implied by summing channel flags. An explicit total gives the model a headline volume feature and enables ratio derivations. Risk C-6 calls this out. |
| `TOTAL_PROMOTIONAL_CALLS` | `F2F + PHONE + GROUP_CALL + REMOTE_CALL` (post-agg sum) | Redundant with `TOTAL_CALLS` if no unmapped record types exist, but if unmapped types fall through the CASE, this captures only the four recognized channels. |

#### 1B. Rate and ratio features (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `F2F_CALL_RATIO` | `TOTAL_F2F / TOTAL_CALLS` | Channel mix. F2F is the highest-cost, highest-impact channel; its share matters independently of total volume. |
| `REMOTE_CALL_RATIO` | `TOTAL_REMOTE_CALL / TOTAL_CALLS` | Remote penetration. The shift from F2F to remote is a strategic signal; a ratio separates it from raw frequency. |
| `SAMPLE_CALL_RATE` | `TOTAL_DETAIL_WITH_SAMPLE / TOTAL_CALLS` | Sampling during a call is a strong conversion indicator. A rate is more stable than a count for HCPs with few calls. |
| `PROMOTIONAL_CALL_RATE` | `TOTAL_CALL_PURPOSE_PROMOTIONAL_ACTIVITY / TOTAL_CALLS` | Separates promotional intensity from total activity (includes non-promotional and miscellaneous). |
| `GROUP_CALL_SHARE` | `(TOTAL_GROUP_CALL + TOTAL_GROUP_DETAIL + TOTAL_GROUP_DETAIL_WITH_SAMPLE) / TOTAL_CALLS` | Group calls reach multiple HCPs at once; high share means breadth over depth. |
| `AVG_CALL_DURATION` | `TOTAL_CALL_DURATION / TOTAL_CALLS` | Average depth per call. Currently only the sum exists, which mixes volume with engagement depth. |
| `AVG_F2F_DURATION` | Daily: `sum(CALL_DURATION * F2F_flag) / sum(F2F_flag)`, then keep anchor value | F2F duration is a quality signal; phone/remote durations are less meaningful. Computed at the daily aggregation level, not from windowed totals. |

**Windowing:** each ratio is computed per window (`_IN_LAST_1_MONTH` ... `_IN_LAST_6_MONTH`) as `SUM(numerator) / SUM(denominator)` at the anchor row. This is the correct way to compute a ratio over a rolling window, not a ratio of rolling sums (which is equivalent for simple ratios, but not for `AVG_F2F_DURATION`).

#### 1C. Recency features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DAYS_SINCE_LAST_CALL` | `LOOKBACK_END_DATE − max(MONTH_ID where any call flag = 1)` | Single value at the anchor. Strong predictor in pharma models — recency often dominates frequency. |
| `DAYS_SINCE_LAST_F2F` | Same, filtered to `F2F = 1` | F2F recency may matter more than overall recency for NBRx response. |
| `DAYS_SINCE_LAST_SAMPLE_CALL` | Same, filtered to `DETAIL_WITH_SAMPLE = 1` | Sample-bearing calls are the conversion lever; their recency is a leading indicator. |

These are not windowed. They are computed once at the anchor row from the daily-spine data.

#### 1D. Diversity and coverage features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `ACTIVE_CALL_DAYS` | `count distinct(MONTH_ID where any call flag = 1)` per window | Days with calls vs total calls. An HCP with 1 call per day for 30 days differs from one with 30 calls in 1 day. |
| `DISTINCT_CALL_TYPES` | `count distinct(CALL_TYP_CD where flag = 1)` per window | Content diversity. An HCP reached with 4 different call types may respond differently than one reached with only detail-only. |
| `DISTINCT_CHANNELS` | `count distinct(CHNNL_NM where flag = 1)` per window | Channel diversity. Omnichannel reach (F2F + remote + phone) is a different signal than same-channel frequency. |
| `CALL_INTENSITY` | `TOTAL_CALLS / ACTIVE_CALL_DAYS` | Calls per active day. Separates frequency from coverage. High intensity with few active days = burst calling; low intensity with many days = steady coverage. |

#### 1E. Additional cross-product features

| Feature | Computation | Rationale |
| --- | --- | --- |
| Channel × Purpose (4 × 5 = 20) | `least(channel_flag, purpose_flag)` at row level | Currently only channel × call type crosses exist. Channel × purpose captures "F2F promotional" vs "Remote non-promotional" interactions, which are strategically different. |
| Call type × Purpose (5 × 5 = 25) | `least(call_type_flag, purpose_flag)` at row level | Captures "Detail with sample + promotional activity" vs "Detail only + non-promotional". |

These add 45 cross features × 6 windows = 270 features. Combined with the existing 210, the total would be 480. This is large; consider pruning to high-prevalence combinations (>1% of HCP-cohorts).

#### 1F. Trend features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `CALL_VOLUME_TREND_1M_VS_6M` | `TOTAL_CALLS_IN_LAST_1_MONTH / TOTAL_CALLS_IN_LAST_6_MONTH` | Is engagement increasing or declining? A ratio > 1/6 means recent acceleration. |
| `F2F_TREND_1M_VS_6M` | `TOTAL_F2F_IN_LAST_1_MONTH / TOTAL_F2F_IN_LAST_6_MONTH` | Channel-specific trend. If F2F is declining while remote rises, the model should see the shift. |
| `DURATION_TREND_1M_VS_6M` | `AVG_CALL_DURATION_IN_LAST_1_MONTH / AVG_CALL_DURATION_IN_LAST_6_MONTH` | Is the rep spending more or less time per call? Trend in call quality, not volume. |

Trend features are computed at the anchor row from the existing `_IN_LAST_*` columns. Each is a single value, not windowed further.

---

## 2. iRep Emails (`16_promotional_features_irep`)

### Current feature inventory (14 base × 6 windows = 84)

| Group | Count | Features |
| --- | --- | --- |
| Engagement | 3 | `IREP_EMAIL_DELIVERED_FLAG`, `IREP_EMAIL_CLICKED_FLAG`, `IREP_EMAIL_OPENED_FLAG` |
| Document category | 11 | `FDA`, `PSP_PRESCRIBING`, `BRANDED_ASSET`, `NATIONAL_BROADCAST`, `KIDNEY`, `INVITE`, `EDUCATION`, `BACC_ACCESS`, `EXCLUSIVE_BROADCAST`, `TRIAL`, `MISCELLANEOUS` |

All are windowed cumulative SUMs. The 11 document-category features count emails **sent** (delivered) with each content type, not engagement with that content. There are no rates, recency, or per-content engagement features.

### Proposed additions

#### 2A. Volume and overall count

| Feature | Computation | Rationale |
| --- | --- | --- |
| `TOTAL_IREP_EMAILS_SENT` | `count(1)` per HCP-cohort-day (same as `DELIVERED_FLAG` sum, but explicit) | The delivered flag equals the total since all rows are filtered to `DELIVERED`. An explicit sent count is cleaner and survives if the filter changes. Risk I-2. |
| `TOTAL_IREP_UNCATEGORIZED_DOC` | `count(1 where no doc-category flag = 1)` | Currently ~57% of email volume has no content signal (I-3). Tracking uncategorized volume explicitly preserves the total and flags content-classification gaps. |

#### 2B. Rate and ratio features (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `IREP_OPEN_RATE` | `TOTAL_IREP_EMAIL_OPENED_FLAG / TOTAL_IREP_EMAIL_DELIVERED_FLAG` | Separates HCP receptivity from rep send volume. This is the single most important email engagement metric. |
| `IREP_CLICK_RATE` | `TOTAL_IREP_EMAIL_CLICKED_FLAG / TOTAL_IREP_EMAIL_DELIVERED_FLAG` | Click is a stronger intent signal than open. Rate normalizes for send volume. |
| `IREP_CLICK_TO_OPEN_RATE` | `TOTAL_IREP_EMAIL_CLICKED_FLAG / TOTAL_IREP_EMAIL_OPENED_FLAG` | Content quality after the HCP opened. Low click-to-open means the subject line worked but the content did not. |
| `IREP_UNCATEGORIZED_RATE` | `TOTAL_IREP_UNCATEGORIZED_DOC / TOTAL_IREP_EMAILS_SENT` | Tracks the share of emails with no content classification. Should decrease as bucketing improves. |

**Windowing:** each is computed per window as `SUM(numerator) / SUM(denominator)` at the anchor row.

#### 2C. Per-content engagement (engagement × document category)

Currently the 11 document features count emails **sent** with each content type. The 3 engagement features count opens/clicks across **all** content. There is no per-content engagement breakdown.

| Feature | Computation | Count | Rationale |
| --- | --- | --- | --- |
| `IREP_OPENED_<CATEGORY>` | `count(1 where OPENED_FLAG = 1 AND doc_category_flag = 1)` | 11 | Which content the HCP actually opened. |
| `IREP_CLICKED_<CATEGORY>` | `count(1 where CLICKED_FLAG = 1 AND doc_category_flag = 1)` | 11 | Which content the HCP clicked through. |

This adds 22 base features × 6 windows = 132 features. Combined with the existing 84, the total would be 216. The per-content open and click counts are the channel's most actionable signal for NBA: they tell the model not just whether to email, but **which content** to send.

**Pruning consideration:** many of the 11 categories have zero volume today (FDA, PSP_PRESCRIBING, BRANDED_ASSET, NATIONAL_BROADCAST are all zero in current data, I-4). In practice only KIDNEY, INVITE, EDUCATION, BACC_ACCESS, EXCLUSIVE_BROADCAST, TRIAL, MISCELLANEOUS have volume. Consider building per-content engagement only for categories with >1% prevalence.

#### 2D. Recency features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DAYS_SINCE_LAST_IREP_EMAIL` | `LOOKBACK_END_DATE − max(EMAIL_SENT_DT)` | Single value at the anchor. Email recency is a predictor of NBRx response. |
| `DAYS_SINCE_LAST_IREP_OPEN` | Same, filtered to `OPENED_FLAG = 1` | Opened-email recency is stronger than sent-email recency because it reflects actual engagement. |
| `DAYS_SINCE_LAST_IREP_CLICK` | Same, filtered to `CLICKED_FLAG = 1` | Click recency is the strongest digital engagement signal. |

#### 2E. Diversity and coverage features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `ACTIVE_EMAIL_DAYS` | `count distinct(MONTH_ID where DELIVERED = 1)` per window | Days with emails vs total emails. Separates sustained outreach from burst campaigns. |
| `DISTINCT_DOC_CATEGORIES` | `count distinct(category where flag = 1)` per window | Content diversity. An HCP receiving 6 different content types may respond differently than one receiving 6 of the same. |
| `EMAIL_FREQUENCY` | `TOTAL_IREP_EMAILS_SENT / ACTIVE_EMAIL_DAYS` | Emails per active day. High frequency with few days = campaign burst; low frequency with many days = sustained drip. |

#### 2F. Trend features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `IREP_VOLUME_TREND_1M_VS_6M` | `TOTAL_IREP_EMAILS_SENT_IN_LAST_1_MONTH / TOTAL_IREP_EMAILS_SENT_IN_LAST_6_MONTH` | Is email outreach increasing or declining? |
| `IREP_OPEN_RATE_TREND_1M_VS_6M` | `IREP_OPEN_RATE_IN_LAST_1_MONTH / IREP_OPEN_RATE_IN_LAST_6_MONTH` | Is the HCP becoming more or less responsive? Trend in receptivity, not volume. |

---

## 3. ClickStream / CLM (`18_promotional_ClickStream_features`)

### Current feature inventory (4 base × 6 windows = 24)

| Feature | Daily aggregation | Rolling operation |
| --- | --- | --- |
| `TOTAL_USAGE_DURATION` | SUM | SUM |
| `TOTAL_PRESN_DURATION` | SUM | SUM |
| `AVG_USAGE_DURATION` | AVG | SUM (bug, K-1) |
| `AVG_PRESN_DURATION` | AVG | SUM (bug, K-1) |

There is no call count, no ratio, no recency, and no diversity feature. The AVG features are mislabelled (they are sums of daily averages, not true averages).

### Proposed additions

#### 3A. Call count and true averages

| Feature | Computation | Rationale |
| --- | --- | --- |
| `CLM_CALL_COUNT` | `count distinct(CALL_ID)` per HCP-cohort-day, then rolling SUM | Critical missing feature (K-2). Without it, true averages and content penetration cannot be computed. |
| `AVG_USAGE_PER_CALL` | `TOTAL_USAGE_DURATION / CLM_CALL_COUNT` (per window) | True average usage duration per call. Replaces the buggy `AVG_USAGE_DURATION` (K-1). |
| `AVG_PRESN_PER_CALL` | `TOTAL_PRESN_DURATION / CLM_CALL_COUNT` (per window) | True average presentation duration per call. Replaces the buggy `AVG_PRESN_DURATION` (K-1). |
| `MAX_USAGE_DUR` | `max(USAGE_DUR)` per HCP-cohort-day, then rolling MAX | Peak engagement. A single long CLM session may signal more interest than many short ones. |

#### 3B. Ratio and penetration features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `USAGE_TO_PRESN_RATIO` | `TOTAL_USAGE_DURATION / TOTAL_PRESN_DURATION` | How much of the presented content was actually used/viewed. Low ratio = content shown but not engaged with. |
| `CLM_PENETRATION_RATE` | `CLM_CALL_COUNT / TOTAL_CALLS` (cross-channel, from notebook 25) | What % of calls included CLM content. Requires joining with the calls output. High penetration = rep uses digital content consistently. |
| `NON_CLM_CALL_RATE` | `1 − CLM_PENETRATION_RATE` | Inverse. Calls without CLM may be shorter or less effective. |

`CLM_PENETRATION_RATE` and `NON_CLM_CALL_RATE` require a cross-channel join (ClickStream `CALL_ID` to calls notebook `BHID`). This can be computed in the combine step (`99_Combine_Physician_Data_Promotional&Acc`), not in the ClickStream notebook alone.

#### 3C. Recency features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DAYS_SINCE_LAST_CLM_CALL` | `LOOKBACK_END_DATE − max(MONTH_ID where CLM_CALL_COUNT > 0)` | Recency of content engagement. An HCP who saw CLM content yesterday is more engaged than one who saw it 5 months ago. |
| `DAYS_SINCE_LAST_DEEP_CLM` | Same, filtered to `USAGE_DUR > 120` (2 minutes) | Deep-engagement recency. Threshold can be tuned. |

#### 3D. Diversity and intensity features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `ACTIVE_CLM_DAYS` | `count distinct(MONTH_ID where CLM_CALL_COUNT > 0)` per window | Days with CLM content. Separates sustained content usage from occasional use. |
| `CLM_INTENSITY` | `TOTAL_USAGE_DURATION / ACTIVE_CLM_DAYS` | Usage per active day. High intensity = deep content engagement on active days. |
| `USAGE_DUR_STD` | `stddev(USAGE_DUR)` per HCP-cohort within the window | Variability of content engagement. Consistent engagement vs occasional spikes may predict different prescribing patterns. |
| `DEEP_CLM_CALL_COUNT` | `count(CALL_ID where USAGE_DUR > 120)` per window | Number of calls with > 2 min of content usage. Deep engagement is a stronger signal than shallow. |
| `BRIEF_CLM_CALL_COUNT` | `count(CALL_ID where USAGE_DUR <= 30)` per window | Number of calls with <= 30 seconds. Brief engagement may indicate low interest. |

#### 3E. Trend features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `USAGE_TREND_1M_VS_6M` | `TOTAL_USAGE_DURATION_IN_LAST_1_MONTH / TOTAL_USAGE_DURATION_IN_LAST_6_MONTH` | Is content engagement deepening or fading? |
| `CLM_CALL_TREND_1M_VS_6M` | `CLM_CALL_COUNT_IN_LAST_1_MONTH / CLM_CALL_COUNT_IN_LAST_6_MONTH` | Is the rep using CLM content more or less often? |

---

## 4. Cross-Channel Features (spanning multiple personal channels)

These features combine signals from two or more personal channels. They are best computed in the combine step (`99_Combine_Physician_Data_Promotional&Acc`) after all three channel outputs are available.

| Feature | Computation | Rationale |
| --- | --- | --- |
| `OMNICHANNEL_TOUCHPOINT_COUNT` | Count of personal channels with >= 1 event in the window (0 to 3: calls, iRep, CLM) | Full omnichannel reach (3 channels) is a different signal than single-channel frequency. |
| `DAYS_SINCE_LAST_PERSONAL_TOUCH` | `min(DAYS_SINCE_LAST_CALL, DAYS_SINCE_LAST_IREP_EMAIL, DAYS_SINCE_LAST_CLM_CALL)` | Earliest recency across all personal channels. An HCP reached by any channel recently is more likely to respond. |
| `EMAIL_AFTER_CALL_COUNT` | Count of iRep emails sent within 7 days after a call to the same HCP-cohort | Follow-up intensity. Email-after-call is a coordinated outreach pattern that may predict response better than either channel alone. |
| `CLM_CALL_SHARE_OF_CALLS` | `CLM_CALL_COUNT / TOTAL_CALLS` (same as `CLM_PENETRATION_RATE` above) | Cross-channel. Calls with digital content vs calls without. |
| `CALL_TO_EMAIL_RATIO` | `TOTAL_CALLS / TOTAL_IREP_EMAILS_SENT` (per window) | Channel balance. High ratio = call-heavy strategy; low ratio = email-heavy. The optimal mix is a key NBA question. |
| `SAMPLE_AND_CLM_CALL_COUNT` | Count of calls where `DETAIL_WITH_SAMPLE = 1` AND `CLM_CALL_COUNT > 0` for the same `CALL_ID` | Samples + CLM content in the same call is the richest single-call experience. Requires joining ClickStream `CALL_ID` to calls. |

---

## 5. Summary: Feature Count Impact

| Channel | Current base | Current total (x6 windows) | Proposed new base | New + current (approx) |
| --- | --- | --- | --- | --- |
| Calls (25) | 35 | 210 | +1 overall + 7 ratios + 3 recency + 4 diversity + 45 crosses + 3 trends = 63 | ~483 |
| iRep (16) | 14 | 84 | +2 volume + 4 rates + 22 per-content + 3 recency + 3 diversity + 2 trends = 36 | ~300 |
| ClickStream (18) | 4 | 24 | +4 count/avg + 3 ratios + 2 recency + 5 diversity + 2 trends = 16 | ~120 |
| Cross-channel | 0 | 0 | 6 (single-value) | 6 |
| **Total** | **53** | **318** | **121** | **~909** |

**Pruning guidance:** 909 features is large. Many proposed features are correlated with their parent counts. Recommended pruning order:

1. Build all volume and count features first (lowest cost, highest value).
2. Build rate/ratio features next; these are the main value-add over raw counts.
3. Build recency features; these are single-value (cheap) and often high-impact.
4. Build cross-product features last; prune to combinations with >1% prevalence.
5. Build trend features; these are cheap (computed from existing windowed columns) and may be pruned by correlation with parent features.
6. Cross-channel features are the most expensive (require joins); build only if the model shows signal from the parent channels.

---

## 6. Implementation Notes

* **Ratio computation:** ratios should be computed at the anchor row as `SUM(numerator) / SUM(denominator)` over the window, not as a ratio of rolling sums. For most features these are equivalent, but for `AVG_F2F_DURATION` they are not. The safest approach is to add the numerator and denominator as separate daily-aggregated columns, let `step3_lag_date` produce their rolling SUMs, and then divide at the anchor row.

* **Recency computation:** recency features require the daily spine (already built by `step2_fill_missing_dates`). At the anchor row, `DAYS_SINCE_LAST_EVENT = LOOKBACK_END_DATE - max(MONTH_ID where event_flag > 0)`. This is a single value per HCP-cohort, not windowed.

* **Diversity features:** `countDistinct` cannot be computed from the daily spine because the spine aggregates away the row-level dimensions. Diversity features require either (a) carrying a `SET` or `ARRAY` of distinct values through the spine, or (b) computing them at the raw-event level before the spine. Option (b) is simpler: compute `countDistinct(CALL_TYP_CD)` per HCP-cohort per window in a separate aggregation, then join to the anchor row.

* **Cross-product features:** use `.withColumns()` with a dict (as the calls notebook already does) to avoid the RecursionError risk from chained `.withColumn()`.

* **Cross-channel features:** require a join between channel outputs. The combine notebook (`99_Combine_Physician_Data_Promotional&Acc`) is the natural place. The `CALL_ID` is available in ClickStream but not in the calls output; to compute `SAMPLE_AND_CLM_CALL_COUNT`, the calls query must include `CALL_ID` in the output.

* **Trend features:** can be computed at the anchor row from existing `_IN_LAST_*` columns with no new spine or lag computation. They are the cheapest additions per feature.
