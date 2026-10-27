# Additional Features — Non-Personal Promotional Channels (NBA 3.1)

**Scope:** Digital / MMX (`24`), HQ Emails (`15`), DTC Direct Buy + Social (`34`), Samples (`17`), Speaker Programs (`14`), Free Trial Program / FTP (`19`)  
**Folder:** `NBA 3.1 - Dev/04_Promotional_Features/`  
**Built from:** line-by-line review of the six NBA 3.1 Dev notebooks (current feature sets verified from the `withColumn` / `alias` / `pivot` code)  
**Companion file:** `additional_features_personal_promotional_channels.md`  
**Date:** October 22, 2026

This file proposes additional features for each non-personal channel, organized by category: volume, ratio/rate, recency, diversity, mix, trend, and cross-channel. Each proposal gives the computation and why it adds value beyond the existing features. Risk IDs (D-*, H-*, T-*, S-*, SP-*, F-*) refer to `non_personal_promotional_features_strategic_file.md` (not in this folder). The NBA 3.0 problems themselves are explained in files 10, 11 and 20.

**Types in this file.** Sections 1 and 2 are **HCP digital** (paid media, HQ emails), section 3 is **DTC**. Sections 4 to 6 (Samples, Speaker Programs, FTP) now belong to `market_access_promotional_features` and `personal_promotional_features`; they are kept here for reference.

**Grain reminder.** The six channels use three different keys, and this changes where each feature can be built:

| Architecture | Channels | Key | Time logic |
| --- | --- | --- | --- |
| A: daily spine | HQ Emails, Samples, Speaker, FTP | `HCP_COHORT_ID` + `SVC_DT` | 30–180 day rolling windows at the cohort anchor |
| B: monthly panel | Digital | `NPI_NUMBER` + `SVC_DT_M` | 1 / 3 / 6 month rolling windows, every month output |
| C: geographic | DTC | `DMA_Code` + `DATA_MONTH` | No windows; contemporaneous month |

Features for A can be added inside the notebook. Features for B and C that need an HCP or anchor-date view are best built in the combine step (`99_Combine_Physician_Data_Promotional&Acc`).

---

## 1. Digital / MMX (`24_Features_Digital`)

### Current feature inventory (~665–896 columns, drifting)

| Group | Construction | Notes |
| --- | --- | --- |
| Channel pivot | `CH_<CHANNEL>_<METRIC>_IN_LAST_{1,3,6}_MONTH` | Raw `UPPER(CHANNEL)` values; includes CALL / SAMPLE (D-1) |
| Source pivot | `SRC_<SRC_SYS_CD>_<METRIC>_IN_LAST_{1,3,6}_MONTH` | ~vendor level |
| Tactic pivot | `TAC_<TACTIC_NAME>_<METRIC>_IN_LAST_{1,3,6}_MONTH` | Raw tactic names (no 3.0 standardization, D-2) |
| Metrics | `DEEP_ENGAGEMENT`, `LIGHT_ENGAGEMENT`, `TOTAL_ENGAGEMENT`, `EXPOSURE` | SUMs |

All prefixed `DIGITAL_`, zero-variance columns dropped at run time (D-5). There is no channel-agnostic total, no rate, no recency, no diversity, and no trend feature. Every feature is a pivot-specific sum.

### Proposed additions

#### 1A. Channel-agnostic totals (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DIGITAL_TOTAL_EXPOSURE` | `sum(EXPOSURE)` across all channels, per NPI-month, then rolling 1/3/6 | A single digital-reach feature. Today exposure is split over ~150 sparse columns (99.1% sparse); the model never sees overall digital pressure. |
| `DIGITAL_TOTAL_ENGAGEMENT` | `sum(TOTAL_ENGAGEMENT)` across all channels | Overall digital engagement. |
| `DIGITAL_TOTAL_DEEP_ENGAGEMENT` | `sum(DEEP_ENGAGEMENT)` across all channels | Overall deep engagement (strongest intent). |

Compute these **after** excluding `CALLS` / `SAMPLES` (and, by decision, `HQ_EMAILS` / `IREP_EMAILS`) so they do not double-count notebooks 25, 17, 15, 16.

#### 1B. Rate and ratio features (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DIGITAL_ENGAGEMENT_RATE` | `TOTAL_ENGAGEMENT / EXPOSURE` | Receptivity to digital media, separated from media weight. Two HCPs with the same exposure but different engagement need different actions. |
| `DIGITAL_DEEP_ENGAGEMENT_RATE` | `DEEP_ENGAGEMENT / EXPOSURE` | Quality of engagement per impression. |
| `DIGITAL_DEEP_SHARE` | `DEEP_ENGAGEMENT / TOTAL_ENGAGEMENT` | Depth mix. Replaces `LIGHT_ENGAGEMENT` (redundant: Light = Total − Deep), which can then be dropped. |
| `DIGITAL_<TOP_CHANNEL>_SHARE` | `EXPOSURE_<channel> / DIGITAL_TOTAL_EXPOSURE` for the top 5–6 channels (e.g. Banner, EHR, Doximity, DocNews, CTV, Video) | Channel mix. More stable and interpretable than raw per-channel sums, and directly answers "which digital channel to use". |

#### 1C. Recency and activity features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DIGITAL_MONTHS_SINCE_LAST_EXPOSURE` | Months between the anchor month and the last month with `EXPOSURE > 0` | Monthly grain only; still strongly predictive. |
| `DIGITAL_MONTHS_SINCE_LAST_ENGAGEMENT` | Same, with `TOTAL_ENGAGEMENT > 0` | Engagement recency beats exposure recency. |
| `DIGITAL_MONTHS_SINCE_LAST_DEEP_ENGAGEMENT` | Same, with `DEEP_ENGAGEMENT > 0` | Strongest digital intent signal. |
| `DIGITAL_ACTIVE_MONTHS_IN_LAST_6` | Count of months with `EXPOSURE > 0` in the last 6 | Sustained vs one-off campaign exposure. |
| `DIGITAL_ENGAGED_MONTHS_IN_LAST_6` | Count of months with `TOTAL_ENGAGEMENT > 0` in the last 6 | Consistency of HCP response. |

#### 1D. Diversity features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DIGITAL_DISTINCT_CHANNELS` | `countDistinct(CHANNEL where EXPOSURE > 0)` per window (from raw rows, before pivot) | Omnichannel digital reach. |
| `DIGITAL_DISTINCT_TACTICS` | `countDistinct(TACTIC_NAME where EXPOSURE > 0)` | Message / format variety. |
| `DIGITAL_DISTINCT_ENGAGED_CHANNELS` | `countDistinct(CHANNEL where TOTAL_ENGAGEMENT > 0)` | Channels the HCP actually responds to. |

#### 1E. Trend features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DIGITAL_EXPOSURE_TREND_1M_VS_6M` | `TOTAL_EXPOSURE_IN_LAST_1_MONTH / TOTAL_EXPOSURE_IN_LAST_6_MONTH` | Is media weight increasing? |
| `DIGITAL_ENGAGEMENT_RATE_TREND_3M_VS_6M` | `ENGAGEMENT_RATE_IN_LAST_3_MONTH / ENGAGEMENT_RATE_IN_LAST_6_MONTH` | Is the HCP becoming more or less receptive (fatigue signal)? |

#### 1F. Dimensionality-reduction replacements

These are not new signals but cleaner versions of what exists:

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DIGITAL_SRC_OTHER_<METRIC>` | Sum of all `SRC_SYS_CD` values below a prevalence threshold (e.g. < 1% of NPIs) | Collapses the long vendor tail (D-6) into one bucket, so the schema stops drifting with new vendors. |
| Standardized tactic families | Map raw `TACTIC_NAME` to the 3.0 list of 14 + `OTHER_TACTIC` before pivoting | Restores 3.0 comparability (D-2) and halves tactic columns. |

**Anchor alignment note.** All Digital features are produced for every NPI-month. When joining to cohorts in the combine step, use the **last complete month before the anchor** to avoid post-anchor leakage (D-4).

---

## 2. HQ Emails (`15_promotional_features_HQ_Emails`)

### Current feature inventory (5 base × 6 windows = 30)

`TOTAL_BOUNCE`, `TOTAL_CLICK`, `TOTAL_OPEN`, `TOTAL_SENT`, `TOTAL_UNSUBSCRIBE`, each `_IN_LAST_1_MONTH` … `_IN_LAST_6_MONTH`. Counts are event rows (repeat opens and clicks of the same email each count, H-1). No rates, no recency, no status features.

### Proposed additions

#### 2A. Rate and ratio features (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `HQ_OPEN_RATE` | `TOTAL_OPEN / TOTAL_SENT` | Receptivity, separated from HQ send volume. Main engagement metric. |
| `HQ_CLICK_RATE` | `TOTAL_CLICK / TOTAL_SENT` | Intent signal per email sent. |
| `HQ_CLICK_TO_OPEN_RATE` | `TOTAL_CLICK / TOTAL_OPEN` | Content quality after the open. |
| `HQ_BOUNCE_RATE` | `TOTAL_BOUNCE / TOTAL_SENT` | Data-quality / reachability signal; high bounce means the address is bad and HQ email is not a viable action for this HCP. |

Because of H-1, rates can exceed 1. Either cap at 1 or, preferably, count distinct emails (see 2D).

#### 2B. Status features (single value at anchor, not windowed)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `HQ_EVER_UNSUBSCRIBED` | `1 if any Unsubscribe event on or before LOOKBACK_END_DATE` (full history, not just the lookback) | **Eligibility flag.** An unsubscribed HCP cannot receive HQ email; NBA must not recommend it. Window counts miss unsubscribes older than 180 days. |
| `HQ_EVER_HARD_BOUNCED` | Same, for Bounce | Reachability flag. |
| `HQ_EMAILABLE_FLAG` | `NOT EVER_UNSUBSCRIBED AND NOT EVER_HARD_BOUNCED` | Single action-eligibility feature for the NBA engine. |

#### 2C. Recency features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DAYS_SINCE_LAST_HQ_SENT` | `LOOKBACK_END_DATE − max(EVENTDATE where Sent)` | Send recency (also useful for frequency capping). |
| `DAYS_SINCE_LAST_HQ_OPEN` | Same, for Open | Engagement recency. |
| `DAYS_SINCE_LAST_HQ_CLICK` | Same, for Click | Strongest HQ engagement recency. |

#### 2D. De-duplicated and coverage features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `HQ_UNIQUE_OPEN_DAYS` | `countDistinct(EVENTDATE where Open)` per window | Proxy for unique opens until an email/campaign ID is available; dampens heavy re-openers (H-1). |
| `HQ_UNIQUE_CLICK_DAYS` | Same, for Click | Same. |
| `HQ_ACTIVE_SEND_DAYS` | `countDistinct(EVENTDATE where Sent)` | Campaign cadence: bursts vs steady drip. |
| `HQ_OPENS_PER_OPEN_DAY` | `TOTAL_OPEN / HQ_UNIQUE_OPEN_DAYS` | Re-engagement intensity on the same day. |

If `HCP_EMAIL_LIST` exposes a campaign or email ID, replace the "days" proxies with `countDistinct(EMAIL_ID)` per event type.

#### 2E. Trend features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `HQ_SENT_TREND_1M_VS_6M` | `TOTAL_SENT_IN_LAST_1_MONTH / TOTAL_SENT_IN_LAST_6_MONTH` | Is HQ ramping up on this HCP? |
| `HQ_OPEN_RATE_TREND_3M_VS_6M` | `HQ_OPEN_RATE_IN_LAST_3_MONTH / HQ_OPEN_RATE_IN_LAST_6_MONTH` | Email fatigue signal. |

---

## 3. DTC Direct Buy + Social (`34_promotional_features_DTC`)

### Current feature inventory (10 features, no windows)

`DTC_PROMOTION_<VENDOR>_TOTAL_IMPRESSIONS` and `DTC_PROMOTION_<VENDOR>_TOTAL_CLICKS` for 4 Direct Buy vendors (Health Union, Healthline, Sharecare, WebMD) and FB+IG, at `DMA_Code × DATA_MONTH`. Contemporaneous month only. Vendor list collected at run time (T-1).

**Role reminder:** DTC is market-level pressure, a **control variable**, not an HCP lever (T-7). New features should describe the HCP's market context, not suggest HCP actions.

### Proposed additions

#### 3A. Totals and rates (DMA × month)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DTC_TOTAL_IMPRESSIONS` | Sum over all vendors | Overall patient-pull pressure in the DMA. One stable column instead of 5 sparse ones. |
| `DTC_TOTAL_CLICKS` | Sum over all vendors | Overall patient response. |
| `DTC_CTR` | `DTC_TOTAL_CLICKS / DTC_TOTAL_IMPRESSIONS` | Patient receptivity in the market. |
| `DTC_SOCIAL_SHARE` | `FB_AND_IG_IMPRESSIONS / DTC_TOTAL_IMPRESSIONS` | Media mix: social vs publisher direct buys. |
| `DTC_ACTIVE_VENDOR_COUNT` | Count of vendors with impressions > 0 | Breadth of the DTC campaign in the DMA. |

#### 3B. Lagged and rolling pressure (DMA × month)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DTC_TOTAL_IMPRESSIONS_LAG_1M` | Previous month's value | Removes mid-month leakage (T-4) and reflects the delay between patient exposure and an HCP visit. |
| `DTC_TOTAL_IMPRESSIONS_IN_LAST_3_MONTH` | Rolling 3-month SUM (monthly spine per DMA, months with no campaign = 0) | Sustained pressure. DTC effects build over several months. |
| `DTC_TOTAL_IMPRESSIONS_IN_LAST_6_MONTH` | Rolling 6-month SUM | Longer-run pressure. |
| `DTC_MONTHS_SINCE_LAST_CAMPAIGN` | Months since the last month with impressions > 0 | Campaign recency / carry-over. |
| `DTC_IMPRESSIONS_TREND_1M_VS_6M` | `LAST_1_MONTH / LAST_6_MONTH` | Is pressure ramping or fading in this market? |

#### 3C. Normalized pressure (needs a population denominator)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DTC_IMPRESSIONS_PER_1K_ADULTS` | `DTC_TOTAL_IMPRESSIONS / DMA adult population × 1000` | Raw impressions scale with DMA size; a per-capita rate makes large and small markets comparable. Population from the SDOH / ACS sources already used elsewhere in the Kerendia pipelines. |
| `DTC_IMPRESSIONS_PER_HCP` | `DTC_TOTAL_IMPRESSIONS / count(HCPs in DMA)` | Pressure per prescriber; built in the combine step. |
| `DTC_PRESSURE_INDEX` | `DTC_IMPRESSIONS_PER_1K_ADULTS / national mean` | Relative pressure (1.0 = national average). Easier to interpret in driver reports. |

All DTC features are broadcast to HCPs via DMA → ZIP → HCP in the combine step. Keep the effective sample size (~210 DMAs) in mind: add only a few DTC features to avoid geographic overfitting.

---

## 4. Samples (`17_promotional_features_samples`)

### Current feature inventory (20 base × 6 windows = 120)

| Group | FLAG (event count) | QTY (units) |
| --- | --- | --- |
| SKU (7) | `SAMPLE_FLAG_KERENDIA_{10MG, 20MG, 10MG_BRC, 20MG_BRC, 40MG_BRC, SAMPLING_KIT_BRC, SAMPLE_HOUSING_BOX_BRC}` | `SAMPLE_QTY_KERENDIA_{same}` |
| Delivery (2) | `SAMPLE_FLAG_{DROPPED, SHIPPED}` | `SAMPLE_QTY_{DROPPED, SHIPPED}` |
| Overall (1) | `SAMPLE_FLAG_OVERALL` | `SAMPLE_QTY_OVERALL` |

All prefixed `TOTAL_`, windowed SUMs. No dose grouping, no rates, no recency.

### Proposed additions

#### 4A. Dose-level groupings (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `SAMPLE_QTY_10MG_ALL` | `QTY_10MG + QTY_10MG_BRC` | Combines legacy and BRC SKUs of the same dose; the SKU split is a packaging detail, not a clinical one. |
| `SAMPLE_QTY_20MG_ALL` | `QTY_20MG + QTY_20MG_BRC` | Same. |
| `SAMPLE_QTY_40MG_ALL` | `QTY_40MG_BRC` | 40 mg is the newer HF-indication dose. |
| `SAMPLE_QTY_SUPPORT_ITEMS` | `QTY_SAMPLING_KIT_BRC + QTY_SAMPLE_HOUSING_BOX_BRC` | Kits and housing boxes are infrastructure for sampling, not doses. Separating them keeps "dose" features clean. |
| `SAMPLE_QTY_OTHER` | `QTY_OVERALL − sum(named SKU QTY)` | Reconciles overall vs named SKUs (S-2); flags new SKUs. |

#### 4B. Mix and ratio features (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `SAMPLE_SHIPPED_SHARE` | `QTY_SHIPPED / QTY_OVERALL` | Remote (shipped, HCP-requested) vs rep-dropped. A high shipped share means the HCP actively requests samples — a strong pull signal. |
| `SAMPLE_20MG_SHARE` | `QTY_20MG_ALL / (QTY_10MG_ALL + QTY_20MG_ALL + QTY_40MG_ALL)` | Titration signal. 20 mg is the maintenance dose for CKD-T2D; a high share indicates patients moving to maintenance. |
| `SAMPLE_40MG_SHARE` | `QTY_40MG_ALL / (dose total)` | Signals HF-indication use, relevant to the NBA 3.1 indication-based universe. |
| `SAMPLE_QTY_PER_EVENT` | `QTY_OVERALL / FLAG_OVERALL` | Average drop size. Separates bulk drops from frequent small drops. |

#### 4C. Recency and activity features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DAYS_SINCE_LAST_SAMPLE` | `LOOKBACK_END_DATE − max(MONTH_ID where FLAG_OVERALL > 0)` | Recency of any sample. |
| `DAYS_SINCE_LAST_SHIPPED_SAMPLE` | Same, `FLAG_SHIPPED > 0` | Recency of HCP-initiated sample requests (stronger pull signal). |
| `DAYS_SINCE_FIRST_SAMPLE_IN_LOOKBACK` | `LOOKBACK_END_DATE − min(MONTH_ID where FLAG_OVERALL > 0)` | Tenure of sampling relationship within the lookback. Combined with recency, distinguishes new vs lapsed samplers. |
| `SAMPLE_ACTIVE_DAYS` | `countDistinct(MONTH_ID where FLAG_OVERALL > 0)` per window | Cadence of sampling. |
| `NEW_SAMPLER_FLAG` | `1 if first sample in the lookback falls in the last 90 days AND no sample before` | Newly sampling HCPs are often about to start writing. Requires history before the lookback; otherwise approximate with the lookback start. |

#### 4D. Trend features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `SAMPLE_QTY_TREND_1M_VS_6M` | `QTY_OVERALL_IN_LAST_1_MONTH / QTY_OVERALL_IN_LAST_6_MONTH` | Is sampling accelerating? |
| `SAMPLE_SHIPPED_TREND_3M_VS_6M` | `QTY_SHIPPED_IN_LAST_3_MONTH / QTY_SHIPPED_IN_LAST_6_MONTH` | Is HCP-initiated demand rising? |

---

## 5. Speaker Programs (`14_promotional_features_speaker_program`)

### Current feature inventory (11 base × 6 windows = 66)

| Group | Features |
| --- | --- |
| Format (5) | `TOTAL_SPKR_EVNT_FMT_{F2F, REMOTE, HYBRID, IN_OFFC_MEAL, OTHER}` |
| Type (2) | `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM`, `TOTAL_SPKR_EVNT_TYP_NON_SPKR_PRGM` |
| Topic (4) | `TOTAL_SPKR_TOPIC_{CKD, CVR, INTRO, OTHER}` |

No overall attendance count (SP-5), no recency, no diversity. Topic coverage is about 50% (SP-4).

### Proposed additions

#### 5A. Volume

| Feature | Computation | Rationale |
| --- | --- | --- |
| `TOTAL_SPEAKER_PROGRAMS_ATTENDED` | `count(distinct EVNT_ID)` per window | Headline feature, present in 3.0 and dropped in 3.1 (SP-5). Using `EVNT_ID` also fixes the missing dedup. |
| `TOTAL_SPKR_TOPIC_HF` | Events whose topic matches HF / LVEF / Heart Failure patterns | New HF-indication content is currently invisible (SP-4). Important for the indication-based 3.1 universe. |
| `TOTAL_SPKR_TOPIC_GDMT` | Events matching GDMT / "Fundamental Pillar" patterns | Guideline-positioning content, distinct from CKD intro decks. |
| `TOTAL_SPKR_TOPIC_UNCATEGORIZED` | Events with a topic not in any bucket | Preserves volume and flags bucket gaps. |

#### 5B. Ratio and mix features (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `SPKR_REMOTE_SHARE` | `(REMOTE + HYBRID) / TOTAL_ATTENDED` | Preference for virtual education — tells NBA which format to invite to. |
| `SPKR_IN_PERSON_SHARE` | `(F2F + IN_OFFC_MEAL) / TOTAL_ATTENDED` | Preference for in-person events. |
| `SPKR_CKD_TOPIC_SHARE` | `TOPIC_CKD / TOTAL_ATTENDED` | Content focus of the HCP's education. |
| `SPKR_CVR_HF_TOPIC_SHARE` | `(TOPIC_CVR + TOPIC_HF) / TOTAL_ATTENDED` | Cardiorenal / HF focus, relevant for cardiologists. |

#### 5C. Recency and history features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DAYS_SINCE_LAST_SPEAKER_PROGRAM` | `LOOKBACK_END_DATE − max(EVNT_START_DATE)` | Speaker programs are rare (96.9% sparse); recency carries more signal than a 30-day count. |
| `SPKR_EVER_ATTENDED` | `1 if any attendance in the full history before the anchor` | Advocacy flag. Most HCPs attend once or never, so a lifetime flag captures the signal that short windows miss. |
| `SPKR_REPEAT_ATTENDEE` | `1 if >= 2 distinct events in the lookback` | Repeat attendees are a distinct, high-engagement segment. |
| `SPKR_DISTINCT_TOPICS` | `countDistinct(topic bucket)` per window | Breadth of education received. |

#### 5D. Event-context features (optional, needs extra columns)

If `ANLT_BASE_FACT_EVNT_PRSNL_PROM` exposes the speaker or host-rep IDs, these become possible:

| Feature | Computation | Rationale |
| --- | --- | --- |
| `SPKR_PEER_SPEAKER_FLAG` | `1 if the HCP has been a speaker (not just attendee)` | Speakers are KOLs; a separate segment for NBA. |
| `SPKR_PROGRAMS_IN_TERRITORY_LAST_3M` | Count of Kerendia speaker programs held in the HCP's territory | Local education intensity (available as context even for non-attendees). |

---

## 6. Free Trial Program / FTP (`19_ftp_features`)

### Current feature inventory (7 features)

`TOTAL_RX_FTP_IN_LAST_1_MONTH` … `_IN_LAST_6_MONTH` (count of valid voucher claims) and `RUNNING_TOTAL_RX_FTP` (cumulative since `LOOKBACK_START_DATE`, F-2). Source also carries `DAY_SUPPLY` and `ORGN_CLM_AUTH_NUM`, which are only used for reversal removal.

**Leakage reminder (F-1).** FTP fills are Kerendia prescriptions. Every feature below must be computed strictly on or before `LOOKBACK_END_DATE`, and the label window must not overlap. If the model target is NBRx, treat FTP features as "prior Kerendia experience" and review their SHAP contribution for circularity.

### Proposed additions

#### 6A. Volume and supply features (per window)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `TOTAL_FTP_DAY_SUPPLY` | `sum(DAY_SUPPLY)` of valid claims | Volume of free drug supplied, not just claim count. A 30-day voucher and a 90-day voucher are different exposures. |
| `AVG_FTP_DAY_SUPPLY` | `TOTAL_FTP_DAY_SUPPLY / TOTAL_RX_FTP` | Typical voucher size. |
| `FTP_ACTIVE_DAYS` | `countDistinct(MONTH_ID where TOTAL_RX_FTP > 0)` | Distinct redemption days (several claims the same day = one patient visit pattern). |

#### 6B. Recency and history features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `DAYS_SINCE_LAST_FTP` | `LOOKBACK_END_DATE − max(MONTH_ID where TOTAL_RX_FTP > 0)` | Recency of trial use. Recent FTP use is the closest promotional signal to a new paid Rx. |
| `DAYS_SINCE_FIRST_FTP` | `LOOKBACK_END_DATE − min(RX_FILL_DT)` over the **full** voucher history (not the cohort spine) | True tenure of FTP use. Fixes the F-2 limitation of `RUNNING_TOTAL`. |
| `LIFETIME_RX_FTP` | Count of all valid voucher claims on or before `LOOKBACK_END_DATE` (full history) | The real lifetime total that `RUNNING_TOTAL_RX_FTP` was meant to be. |
| `FTP_EVER_FLAG` | `1 if LIFETIME_RX_FTP > 0` | Simple "has used the trial program" segment flag. |
| `NEW_FTP_USER_FLAG` | `1 if first-ever FTP claim falls in the last 90 days` | New trial adopters are a key NBA target (likely to convert to paid). |

#### 6C. Reversal and quality features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `FTP_REVERSAL_COUNT` | Count of `ORGN_CLM_AUTH_NUM` groups removed as reversals, per window | Reversed vouchers may signal access or pharmacy friction. Today they are only removed, not measured. |
| `FTP_REVERSAL_RATE` | `FTP_REVERSAL_COUNT / (TOTAL_RX_FTP + FTP_REVERSAL_COUNT)` | Friction rate, independent of volume. |

#### 6D. Trend features

| Feature | Computation | Rationale |
| --- | --- | --- |
| `FTP_TREND_1M_VS_6M` | `TOTAL_RX_FTP_IN_LAST_1_MONTH / TOTAL_RX_FTP_IN_LAST_6_MONTH` | Accelerating trial use. |
| `FTP_TREND_3M_VS_PRIOR_3M` | `LAST_3_MONTH / (LAST_6_MONTH − LAST_3_MONTH)` | Momentum: recent quarter vs the quarter before. |

#### 6E. Conversion features (combine step, leakage-safe only)

| Feature | Computation | Rationale |
| --- | --- | --- |
| `FTP_TO_PAID_RX_RATIO` | `TOTAL_RX_FTP_IN_LAST_6_MONTH / Kerendia paid NRx in the same window` (from LAAD Rx features) | How dependent the HCP is on free trial vs paid Rx. Only if both are strictly before the anchor and the target is a later window. |

---

## 7. Cross-Channel Features

These combine non-personal channels with each other and with personal channels. Build them in the combine step after all outputs are joined on `HCP_COHORT_ID` (Digital via NPI → BHID; DTC via DMA → HCP).

| Feature | Computation | Rationale |
| --- | --- | --- |
| `NON_PERSONAL_TOUCHPOINT_COUNT` | Count of HCP-addressable non-personal channels with >= 1 event in the last 90 days (Digital, HQ, Speaker, Samples, FTP) | Breadth of non-rep exposure. |
| `TOTAL_TOUCHPOINT_COUNT` | Non-personal count + personal count (Calls, iRep, CLM) | Full omnichannel breadth (0–8). |
| `DAYS_SINCE_LAST_ANY_PROMOTION` | `min` of all channel recency features | Single "last touched" feature, useful for NBA frequency capping. |
| `DIGITAL_TO_PERSONAL_RATIO` | `DIGITAL_TOTAL_EXPOSURE_IN_LAST_3_MONTH / (TOTAL_CALLS + TOTAL_IREP_EMAILS_SENT)_IN_LAST_3_MONTH` | Non-personal vs personal mix. A key NBA question: where is the HCP reached most? |
| `HQ_TO_IREP_EMAIL_RATIO` | `TOTAL_SENT (HQ) / TOTAL_IREP_EMAILS_SENT` per window | HQ vs rep email balance; helps decide which email lever to pull. |
| `SAMPLES_PER_CALL` | `SAMPLE_FLAG_OVERALL / TOTAL_CALLS` per window | How often calls translate into sample drops. |
| `SHIPPED_SAMPLES_WITHOUT_CALL` | Shipped sample events with no call to the HCP within +/- 14 days | Pure HCP-initiated demand, independent of rep activity. Needs event-level joins. |
| `SPEAKER_AFTER_CALL_FLAG` | `1 if a speaker program was attended within 30 days after a call` | Rep-driven invitation conversion. |
| `FTP_AFTER_SAMPLE_FLAG` | `1 if an FTP claim occurs within 60 days after a sample` | Sample-to-trial conversion path. |
| `DTC_X_CALLS_INTERACTION` | `DTC_IMPRESSIONS_PER_1K_ADULTS × TOTAL_CALLS_IN_LAST_3_MONTH` | Tests whether rep activity is more effective in high-DTC markets (synergy). Use only if the model is not tree-based (trees learn interactions themselves). |

Event-sequence features (`*_AFTER_*`, `*_WITHOUT_CALL`) need event-level data from two notebooks. They are the most expensive; build them only after the simpler features have been evaluated.

---

## 8. Summary: Feature Count Impact

| Channel | Current | Proposed new base | Windowing | Approx. new columns |
| --- | --- | --- | --- | --- |
| Digital (24) | ~665–896 (drifting) | 3 totals + ~9 rates/shares + 5 recency/activity + 3 diversity + 2 trends = ~22 | Totals/rates × 3 windows; rest single-value | ~45 (and ~300 fewer after 1F consolidation) |
| HQ Emails (15) | 30 | 4 rates + 3 status + 3 recency + 4 coverage + 2 trends = 16 | Rates/coverage × 6; rest single-value | ~56 |
| DTC (34) | 10 | 5 totals/rates + 5 lag/rolling + 3 normalized = 13 | Single-value per DMA-month | 13 |
| Samples (17) | 120 | 5 dose groups + 4 mix + 5 recency/activity + 2 trends = 16 | Dose/mix × 6; rest single-value | ~61 |
| Speaker (14) | 66 | 4 volume + 4 mix + 4 recency/history (+2 optional) = 12–14 | Volume/mix × 6; rest single-value | ~52 |
| FTP (19) | 7 | 3 supply + 5 history + 2 reversal + 2 trend + 1 conversion = 13 | Supply/reversal × 6; rest single-value | ~38 |
| Cross-channel | 0 | 10 | Single-value | 10 |

**Priority order:**

1. **Eligibility and headline features** (highest NBA value, low cost): `HQ_EMAILABLE_FLAG`, `TOTAL_SPEAKER_PROGRAMS_ATTENDED`, `DIGITAL_TOTAL_EXPOSURE` / `ENGAGEMENT`, `DTC_TOTAL_IMPRESSIONS`.
2. **Rates** (separate receptivity from volume): HQ open/click rate, Digital engagement rate, DTC CTR, Samples shipped share.
3. **Recency and lifetime flags** (cheap, high signal for sparse channels): Speaker, FTP, Samples, HQ.
4. **Mix and dose features**: Samples 20/40 mg share, Speaker remote share, Digital channel shares.
5. **Trends**: computed from existing windowed columns; prune by correlation.
6. **Cross-channel and event-sequence features**: most expensive; build only after the parent channels show signal.

---

## 9. Implementation Notes

* **Architecture A (HQ, Samples, Speaker, FTP).** Ratios: carry numerator and denominator as separate daily columns, let `step3_lag_date` roll both, divide at the anchor row. Recency: compute from the raw events (`max(event_date) where date <= LOOKBACK_END_DATE`) per `HCP_COHORT_ID`, rather than from the spine. Lifetime / ever flags must use the **full history** query, not the cohort-filtered data; this means the SQL date bounds must allow history before `LOOKBACK_START_DATE`.

* **Architecture B (Digital).** Channel-agnostic totals can be computed in the SQL (`GROUP BY NPI_NUMBER, SVC_DT_M` without the pivot dimensions) and joined to the pivot output; this is cheaper than summing hundreds of pivot columns. Diversity features need `countDistinct` on the raw rows before the pivot. Recency in months uses the monthly spine already produced by `step2_fill_missing`.

* **Architecture C (DTC).** Lags and rolling sums need a dense `DMA × month` spine (months with no campaign = 0) before the window functions; the current output has gaps for months with no data. Normalization needs a DMA population table.

* **Avoid schema drift.** New pivot-derived features (Digital shares, DTC vendor totals) should use frozen value lists, not run-time `distinct().collect()`, so the trained model sees the same columns at inference.

* **Use `.withColumns()`** with a dict for batches of new columns, as notebook `17` already does, to avoid the chained `.withColumn()` RecursionError risk on Spark Connect.

* **Leakage checks.** FTP and Samples are close to the Rx outcome. Run a SHAP or correlation check of the new FTP / Samples features against the target window before keeping them.
