# HQ Email Features for NBA 3.1: Decisions and Evidence

**Notebook:** `HQ Emails/15_promotional_features_HQ_Emails_new` (rebuilt from the NBA 3.0 notebook `15_promotional_features_HQ_Emails`)  
**Spec followed:** `52_digital_feature_families_nba30_vs_nba31.md` sections 1 (shared rules), 3.2 (family 2: HQ email), 6.6 (Phase 1 issues)  
**Other inputs:** `11_hcp_hq_emails_nba_3_0.md` (NBA 3.0 problems), notebook `51_digital_nba_phase1_features` (cohort helpers, P8 block), notebook `50_digital_nba_phase0_validation`  
**Checks run:** 5 November 2026 on serverless, Snowflake `ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` and Unity Catalog MMX, Kerendia rows  
**Status:** notebook **run end to end on 5 Nov 2026** (serverless). All QC1 to QC10 PASS (3,071,194 NPI x cohort rows; MMX / source sent ratio 0.971 to 0.994 every month; hand recompute 5 of 5 doctors match). Per-cohort results identical to the prototype in section 4. Output written to `dev_folder/notebook_output/nba_3_1_hq_email/`. To review by the team.

---

## 1. In short

HQ email = marketing emails sent by Bayer head office, and what the doctor did with them (opened, clicked, unsubscribed, or the email bounced). NBA 3.0 built 5 counts over the last 90 days for one cohort, counting every repeat open, and the same emails were counted again twice in the Digital block. NBA 3.1 reads **one** source, keys doctors by **NPI**, builds **all monthly cohorts** with **1 / 3 / 6 / 12 complete-month windows**, counts **unique** opens and clicks per email, and adds rates, a trend, status flags (unsubscribed, emailable) and recency. 15 fixed features.

---

## 2. Decisions

Each decision lists what was chosen, the alternatives, and why.

### D1. Source: `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` (channel `HQ EMAIL`) is the only HQ email source

| Option | Verdict | Reason |
| --- | --- | --- |
| `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` (NBA 3.0 source) | Rejected | No access; the view failed to compile in the Phase 1 run (52, issue 2) |
| MMX `mmx_fnl_combined_aggr_tab`, channel `HQ EMAIL` (notebook 51 fallback) | Rejected | Same activity (see evidence) but **no bounce, no unsubscribe, no email ID**; opens / clicks rely on the assumption EXPOSURE = sent, TOTAL_ENGAGEMENT = open, DEEP_ENGAGEMENT = click |
| `CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL` (Phase 0) | Rejected | Status `Delivered_vod` is Veeva CRM naming, so this table most likely holds **rep-triggered (iRep) emails**, not HQ emails; its 438,854 delivered emails do not match the HQ volumes. *Assumption, to confirm with the data owner.* |
| **`ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS`** | **Chosen** | Already used by the NBA 3.0 clone as the `HCP_EMAIL_LIST` replacement; has every event type, `NPI_NUM`, and an email name (`EMAIL_NM`) on every row |

**Evidence (sent per month, Jan 2025 to Oct 2026):** MMX HQ exposure / ANLT sent = **0.97 to 0.99 every month** (total 3,872,999 vs 3,922,208). Opens 1,121,013 vs 1,122,475 and clicks 64,316 vs 64,364. So MMX and ANLT describe the same emails; ANLT simply has more detail. The notebook keeps this as a permanent check (QC9: ratio must stay within 0.90 to 1.10).

**Consequence (D8):** HQ email must be counted once. The 12 `DIGITAL_HQ_EMAIL_*` features (P8) in notebook 51 are the same activity from MMX and should be dropped from the digital block when this table is used.

### D2. Doctor key: NPI, from the source first, else BH_ID -> NPI

* `NPI_NUMBER` = `NPI_NUM` when it is a real 10-digit NPI; otherwise the NPI mapped from `BAYER_CUST_ID` (BH_ID) through `kerendia_oe_npi_bhid_mapping_inference` (smallest NPI if a BH_ID has several, same rule as notebook 51).
* Why: NBA 3.1 joins every block on NPI + cohort (52, section 1). Using the source NPI first keeps rows whose BH_ID is not in the mapping.
* Evidence (9,505,590 rows, Jan 2025 to Oct 2026): NPI directly on 91.2% of rows, via BH_ID on 93.4%, **either on 93.5%**. Only 275 rows had two different NPIs (source vs mapping); the source NPI wins. Rows without any NPI (about 6.6%) are dropped.

### D3. Event types kept apart

| Source `MTR_NM` | Event | Use |
| --- | --- | --- |
| `SENT` | SENT | volume, rates (denominator), recency |
| `DELIVERED` | DELIVERED | only to decide whether an unsubscribe / hard bounce is still current (D6) |
| `OPENED` | OPEN | unique opens, open rate, trend, recency |
| `CLICKED` | CLICK | unique clicks, click rate, recency |
| `UNSUBSCRIBED` | UNSUB | unsubscribe status |
| `HARD BOUNCE` | HARD_BOUNCE | hard-bounce flag, emailable flag |
| `SOFT`, `BLOCK`, `TECHNICAL/OTHER`, `UNKNOWN BOUNCE` | OTHER_BOUNCE | not used as features (temporary problems) |

NBA 3.0 (clone) lumped all five bounce types into one "Bounce" count, which mixes "address invalid" with "mailbox full". The notebook stops if a new `MTR_NM` value appears.

### D4. Cohorts and windows: same rules as all NBA 3.1 blocks

* Cohorts monthly from 2025-01, offset 7: cohort `2026-09_offset7` = as of **6 October 2026** (month end + 6 days). Cohorts whose cutoff is after the last date in the source are dropped (data ended 4 Nov 2026, so cohort 2026-10 with cutoff 6 Nov is dropped; 21 cohorts 2025-01 to 2026-09).
* Windows 1 / 3 / 6 / 12 months ending on the cutoff, `(cutoff - w months, cutoff]`. No `RUNNING_` features.
* Data loaded from 1 Jan 2024, so even cohort 2025-01 has a full 12-month window (no artificial trend in early cohorts, unlike 52 issue 1).

### D5. Unique opens and clicks per email; rates capped at 1

* Unique open = distinct `EMAIL_NM` the doctor opened in the window. NBA 3.0 counted every open row, so a doctor who reopened one email 20 times counted 20.
* Evidence: 1,526,458 open rows vs 1,112,114 unique (doctor, email) pairs; the heaviest re-opener had 451 open rows for one email.
* Rates = unique emails opened (clicked) / unique emails sent in the same 6 months. A rate can still exceed 1 when the doctor opens an email sent before the window (up to 1,972 doctors per cohort in the prototype), so it is **capped at 1**. NULL when nothing was sent.
* Sent stays an event count (`HQ_EMAIL_SENT_*`): it measures how much HQ pushed, which is what volume means.

### D6. Unsubscribe and bounce are **status at the cutoff**, not "ever"

* Evidence: of 10,437 doctors (BH_ID) who ever unsubscribed, **829 still received a delivered HQ email more than 30 days later** (487 opened one). Of 20,708 with a hard bounce, 5,893 later had a delivery (another address). So neither event is permanent.
* Rule: `HQ_EMAIL_UNSUBSCRIBED_FLAG` = 1 if the latest unsubscribe on or before the cutoff is **not followed by a delivered email**. Same for hard bounce inside `HQ_EMAILABLE_FLAG`. Full history from Jan 2024 is used, so an unsubscribe from 18 months ago still counts.
* Why it matters for NBA: an unsubscribed or unreachable doctor must not get "send HQ email" as an action. The flag is both a feature and a business rule.

### D7. Doctor universe of the table

One row per NPI x cohort for doctors with **any HQ email event in the last 12 months, or currently unsubscribed**. The combine step fills other doctors: counts and flags 0, `HQ_EMAILABLE_FLAG` = 1, rates / trend / days-since NULL (manifest column `NULL_IN_COMBINE`).

### D8. HQ email counted once in NBA 3.1

See D1. **Open, deliberately not done yet:** notebook 51 is left as it was (it still builds the 12 `DIGITAL_HQ_EMAIL_*` features from MMX). Agreed with the team on 5 Nov 2026: change notebook 51 only when it next needs to run. Two options at that point: (a) remove P8 from notebook 51 (note: its schema check will then need a config change to accept the 12 dropped columns, and doctors with HQ email but no paid media will leave the digital table), or (b) keep notebook 51 and drop the `DIGITAL_HQ_EMAIL_*` columns in the combine step. Never use both HQ email blocks in the same model.

*Trace of a reverted attempt (5 Nov 2026):* a switch to remove P8 was added to notebook 51 and its cells up to the feature specification were run, then the code was restored to the original at the team's request. The main output `hcp_digital_phase1_features` was not touched (still the 3 Nov run). Side effects of that partial run: `placement_dictionary` rewritten with identical content (same dictionary version `057704bbbb`), one extra row appended to `unmapped_report`, `_stage_paid_media_monthly` rebuilt. Some cell outputs in notebook 51 still show messages from that run (e.g. "HQ email (P8) not built here"); they do not match the restored code and can be cleared.

---

## 3. Feature list (15)

| Feature | Meaning |
| --- | --- |
| `HQ_EMAIL_SENT_1M`, `_3M`, `_12M` | HQ emails sent to the doctor (send events) in the last 1 / 3 / 12 months |
| `HQ_EMAIL_UNIQUE_OPENS_3M`, `_12M` | Distinct emails opened |
| `HQ_EMAIL_UNIQUE_CLICKS_12M` | Distinct emails with a click |
| `HQ_EMAIL_OPEN_RATE_6M` | Unique opened / unique sent, 6 months, capped at 1 |
| `HQ_EMAIL_CLICK_RATE_6M` | Unique clicked / unique sent, 6 months, capped at 1 |
| `HQ_EMAIL_OPENS_3M_VS_PRIOR_3M` | (opens last 3M - prior 3M) / (sum), -1 to +1: is the doctor reading more or less (fatigue) |
| `HQ_EMAIL_HARD_BOUNCE_FLAG_12M` | Any hard bounce in 12 months |
| `HQ_EMAIL_UNSUBSCRIBED_FLAG` | Currently unsubscribed (D6) |
| `HQ_EMAILABLE_FLAG` | Not unsubscribed and not currently bouncing |
| `HQ_EMAIL_DAYS_SINCE_LAST_SENT`, `_OPEN`, `_CLICK` | Days from the last event to the cutoff |

The spec in 52 asked for "about 12": sent, unique open and click, open rate, click rate, bounce flag, unsubscribe status, days since last open. All are covered; the extra 3 (emailable, trend, days since last click / sent) come from `30_nba_3_1_proposed_additional_features.md` section 2 and can be pruned after the experiment.

Features from file 30 **not** built: `HQ_BOUNCE_RATE` (bounces are rare; the flag carries the signal), `HQ_OPENS_PER_OPEN_DAY` (replaced by true unique opens).

---

## 4. Prototype results (full data, logic identical to the notebook)

| Cohort | Doctors | Sent 3M | Unique opens 3M | Avg open rate 6M | Unsubscribed |
| --- | --- | --- | --- | --- | --- |
| 2025-01_offset7 | 112,639 | 273,070 | 79,790 | 0.280 | 2,435 |
| 2025-06_offset7 | 160,596 | 1,027,740 | 284,456 | 0.278 | 5,223 |
| 2026-01_offset7 | 154,132 | 474,170 | 140,190 | 0.302 | 6,755 |
| 2026-09_offset7 | 110,002 | 356,228 | 86,403 | 0.271 | 8,219 |

Checks (all 21 cohorts): one row per NPI x cohort; no event after the cutoff; days-since never negative. Independent comparison: cohort 2026-09 sent 3M = 356,228 here vs 344,245 in notebook 51 (MMX source, BH_ID-only mapping), consistent with the 97 to 99% ratio in D1.

The notebook adds QC1 to QC10 (keys, leakage, fixed schema, NPI format, rate and trend ranges, nested windows, MMX reconciliation, hand recompute of 5 doctors) and refuses to write if any fails.

---

## 5. Open points for the team

0. **Figure check (5 Nov run):** the 97 to 99% MMX / ANLT ratio is confirmed by QC9 (0.971 to 0.994 per month). Not re-measured: the exact totals (3,872,999 / 3,922,208 sent, opens, clicks), the `FACT_SENT_EMAIL` count (438,854) and the notebook 51 figure (344,245, from its 3 Nov run). Note: NPI coverage over the full load (Jan 2024 to Nov 2026) is 89.3% of rows (87.2% direct); the 93.5% in D2 is for Jan 2025 to Oct 2026 only.

1. **Confirm D1 with the data owner:** is `FACT_SENT_EMAIL` really iRep (Veeva) email? If it is HQ, decide whether it should replace ANLT.
2. **Unsubscribe scope:** does a Kerendia unsubscribe block all HQ emails or only Kerendia? The 829 doctors with deliveries after unsubscribing suggest either brand-level opt-out or re-subscription. D6 handles both, but the meaning of the flag should be confirmed.
3. **HQ email counted once (D8):** decide between options (a) and (b) when notebook 51 next runs. Notebook `14_hcp_digital_phase1_feature_block` (older copy) also builds P8: confirm it is not used.
4. ~~Run the notebook~~ Done 5 Nov 2026; results match the prototype.
5. After the experiment: drop features with low SHAP rank; the 3 sent windows and 2 unique-open windows are correlated.
