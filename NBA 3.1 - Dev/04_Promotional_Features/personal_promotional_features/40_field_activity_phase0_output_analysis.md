## 6. Guide for new readers: why each expectation exists, and what to raise with the client

### 6.1 Background in five points

1. **NBA (Next Best Action)** is a model that ranks doctors (HCPs) for Kerendia reps to visit. NBA 3.0 is the current model; NBA 3.1 is the next version.
2. **Field activity** is what reps do with doctors: calls (visits), emails sent by reps (iRep), speaker events, MSL (medical) visits. These become model features such as "number of Kerendia calls in the last 3 months".
3. The **readiness plan** (`40_..._readiness_plan.md`, section 3) lists what is wrong with the NBA 3.0 field features. Each Phase 0 step (V1 – V10) checks that the data can support the fix before features are built.
4. The **expected figures** (for example about 660K calls) come from the earlier data review (`20_`), which counted the same data by hand. Phase 0 checks that the notebook reproduces them.
5. **Gate G0** is the checkpoint at the end of Phase 0: Phase 1 features are only trusted once the foundations pass.

**Status of this section:** updated 3 Nov 2026 after two fixes in the Phase 0 notebook: (1) `KEY_MSG_NM` is now brought into the V1a query, so account / office records are found; (2) medical record types are matched by pattern instead of a fixed list. V2, V3 and V10 below reflect the re-run. **Update 5 Nov 2026:** V10 / C11 now include the MSL scope evidence (product mix, Kerendia overlap, check on the 28 promotional cohorts) and the decision to keep MD-1 Finerenone only, without Asundexian; V2 records the exact medical pattern used in notebooks 41 and 43; V1 adds a warning on the word `Kerendia` in MSL product text.

### 6.2 Overview

| ID | NBA 3.0 problem behind the expectation | In NBA 3.0 or new in 3.1? | Expectation met? | Raise with client? |
| --- | --- | --- | --- | --- |
| V1 | Kerendia calls found by product text; co-detail calls missed | Calls existed in 3.0; the interaction grain and detail rule are new | Yes | Yes: confirm the split target (606K + 70K) |
| V2 | Account / office visits counted as doctor calls; BHO copies given to every colleague | New | Yes on rules (fixed 3 Nov); 3 points to confirm | Yes: no-HCP key-message list, calls with both HCP and account messages, medical records on BHO IDs |
| V3 | BHO calls repeated to about 80 colleagues per organisation | New (3.0 used BHO calls without this logic) | Data yes; business answer missing | Yes: CRM team questions |
| V4 | No key-message information in 3.0 | New | Partly | Yes: entry process and HF decline |
| V5 | Samples only as "call type with sample" | New | Yes (30 Oct); Phase 4 (X1) design and cohort check added | Yes: who fixes the market access table; delivery date or status snapshots; 40 mg and HF |
| V6 | Registration treated as attendance; all event types mixed | Attendance existed in 3.0; separate states are new | Partly (fixed 4 Nov: Kerendia filter, attendee status column; type labels sit in `EVNT_CAT`) | Yes: `Signed_vod` meaning, event groups, attendee data |
| V7 | Delivered filter never matched (feature always 0) | Fix of a 3.0 feature | Fix yes; opens open (drop is platform-wide, clicks stable: likely tracking change) | Yes: April 2026 open-rate drop |
| V8 | Text rule would break again with a new co-detailed product | New | Not due | Yes: launch date and recording |
| V9 | Columns not driven by a config | New (engineering standard) | No | No (internal) |
| V10 | MSL visits not handled explicitly | New (MSL flag, compliance-approved 30 Oct 2026) | Yes (volume and classification, fixed 3 Nov); scope checked on cohorts c1 – c28 (5 Nov) | Yes: confirm Finerenone-only scope (recommended; Asundexian not added) |

### 6.3 Step by step

#### V1 – Interaction grain

* **Why we expect this.** NBA 3.0 kept a call only when the product text on the call equals `KERENDIA`. When a rep also presents Lynkuet in the same visit, the text holds both products, so the call is dropped. Since January 2026 (Lynkuet co-detailing) this loses 40 – 46% of Kerendia calls each month, and about 20,000 doctors look "never called". NBA 3.1 counts one visit once and checks the product detail rows instead of the text. The review counted about 660K calls and about 104K doctors in Year 2 this way, and Kerendia as first product on 87 – 92% of visits.
* **NBA 3.0 or new.** Call counts existed in 3.0. The rule (any Kerendia detail row) and the grain (one row per visit, products below it) are new in 3.1.
* **Status.** Met: 676,136 calls / 104,752 doctors; first priority 91.6%.
* **Raise with client.** Confirm that the target is two numbers: about 606K doctor visits plus about 70K account / office records. Reason: the 660K in the review included account / office records, which NBA 3.1 deliberately separates (V2).
* **Suggestions.** Use the same detail rule in every block that filters on Kerendia calls (for example samples, CLM). Remove medical records **before** applying any Kerendia rule: Finerenone MSL product text is `Finerenone [Kerendia/Firialta] ...`, so a filter such as `DETL_PROD ILIKE '%kerendia%'` also picks up MSL visits (found 5 Nov 2026 during the V10 scope check). Run E1 (NBA 3.0 features with only this fix) to show the client how much the co-detail gap alone changes the model.

#### V2 – Record classification

* **Why we expect this.** NBA 3.0 counted every call record as a doctor call. About 10 – 12% of them are account-only or virtual-office records with no doctor present, and many are organisation (BHO) copies or MSL visits. NBA 3.1 gives every record one class so only true doctor visits feed the core counts.
* **NBA 3.0 or new.** New.
* **Status.** Met on rules after the 3 Nov fixes; three business points to confirm.
  * *What went wrong first:* `ACCOUNT_OFFICE` was 0, because the plan assumed "no HCP present" is stored in the record type; Veeva stores it as a key message (`FACT_CALL_KEY_MESSAGE.KEY_MSG_NM`). The medical list also used spaces where Veeva uses underscores and missed the Non Face2Face / Group types.
  * *Fix 1:* the V1a query now joins the key messages (one row per call: `KEY_MSG_NMS`, `HAS_ACCT_OFFICE_MSG`). Account / office: 76,662 Kerendia doctor calls in Year 1 (14.0%) and 69,897 in Year 2 (10.3%), within the expected 10 – 12% range in Year 2. Kerendia HCP interactions: 472,236 (Y1) and 606,239 (Y2).
  * *Fix 2:* medical records matched by pattern. Exact rule in notebooks 41 and 43 (`MEDICAL_REC_TYPE_REGEX`, `MEDICAL_DETL_PROD_REGEX`): record type contains `Interaction Med` / `Interaction_Med` (for example `Face2Face Interaction Med`, `Non Face2Face Interaction Med`, `Group Interaction Med`), starts with `BPH_MED_`, or starts with `Event Call Report`; **or** product text contains `Finerenone`. Earlier versions of this file described the type rule as "ends with ` Med` / `_Med`"; both match the 12 types seen today, but a new type such as `Other Med` would be missed by the code rule (see C3). An independent check finds 0 medical records left among HCP interactions (was 5,045 in Year 2).
* **Raise with client.**
  * Confirm that the key messages `5- Acct Call`, `2-Account Call Only`, `vOffice call (no HCP)`, `Account Call`, `Office call (no HCP)` always mean no doctor was present, and whether reps use them consistently. Reason: the account / office class depends entirely on reps choosing that message. The last two are not in the readiness plan list.
  * Some calls carry both an HCP message and an account message, for example `1-HCP Call | 2-Account Call Only` (6,090 records) or `1-Position 1 KER CKD (HCP call) | 5- Acct Call` (2,809). Which one wins? Reason: they are currently classed as account / office, so they are not counted as doctor visits.
  * About 34K medical-type records sit on BHO IDs (Y1 14,967; Y2 18,783). They are classed as BHO first and would feed organisation context. Should they be dropped? Reason: they are MSL copies, not rep activity.
* **Suggestions.** Keep the rules (key-message list, medical pattern) in a config table, not in code; report class shares every month so a new Veeva value is spotted early; exclude medical-type records from the BHO classes until the client answers.

#### V3 – BHO parent / child

* **Why we expect this.** In NBA 3.0 every BHO (organisation) call was given to every doctor of the organisation. The review found 494K of about 502K BHO calls are copies of a single doctor's call, so the same visit was repeated to about 80 colleagues, including the doctor himself. NBA 3.1 uses these records only as organisation context, without the focal doctor.
* **NBA 3.0 or new.** BHO calls were used in 3.0; the parent / child logic is new.
* **Status.** The data supports the logic: one organisation per parent; 88.2% of children point to an HCP interaction, about 9% to account / office or medical calls (before the 3 Nov fixes these were counted as doctor calls, giving 97.0%), and about 3% to no doctor call in the extract. The business confirmation is missing, and 7,096 children have an empty parent ID.
* **What NBA 3.0 did (legacy notebook `13_promotional_features_bho_calls`, see `11_bho_calls_nba_3_0.md`).**
  1. Keep submitted Kerendia calls whose Bayer ID contains `BHO` (organisation calls). It does not look at `PAR_CALL_ID`, so a copy of a doctor call and a real organisation call are treated the same.
  2. Find the doctors of each organisation from Bayer master data (`PHCDW_STG.MDM_STG_HCP_ACCT_AFFL`, doctor-organisation affiliations).
  3. Give every organisation call to **every** affiliated doctor: 376,617 organisation calls became 30,351,434 rows (about 80 doctors per call); 163,233 doctors received at least one.
  4. Build 90 features `BHO_TOTAL_<measure>_IN_LAST_<N>_MONTH` (channel, call type, purpose, duration; 1 to 6 months). In the saved table, 6.2M face-to-face "calls" in 3 months against about 100K in the personal Sales Rep Calls table; phone, group call, detail with sample and event detail are 0 for every doctor.

* **NBA 3.0 vs NBA 3.1 side by side.**

| Question | NBA 3.0 | NBA 3.1 (plan, C7, D3) |
| --- | --- | --- |
| What is a BHO record? | Always an organisation call | Two kinds: `BHO_CHILD` (has `PAR_CALL_ID`, a copy of a doctor call) and `BHO_TOP_LEVEL` (no parent, possibly a real organisation call) |
| Is a BHO child new activity? | Yes, counted again | No. The activity is already counted once, on the doctor who was visited |
| Who receives the record? | Every doctor affiliated with the organisation in MDM, including the doctor who was visited | Organisation context only, **focal doctor excluded**; the doctor's own visit stays in his personal counts |
| How is a doctor linked to an organisation? | MDM affiliation table | From the calls: the doctor's call has a BHO child, or the doctor attended a BHO group call (plan section 6, Phase 1 status) |
| Top-level BHO calls | Counted, same as children | Kept out of features until the CRM team confirms what they are |
| Features | 90 counts of organisation calls by channel, type, purpose | About 4 – 6 context features: interactions of colleagues, number of colleagues called, top-level organisation calls (after V3) |

* **Business rule we are adding.**
  * *Rule 1 (copy rule):* a BHO record with a parent (`PAR_CALL_ID`) is a system copy of the parent call. It is never counted as a new interaction, for anyone.
  * *Rule 2 (focal-doctor rule):* organisation context for a doctor counts only the activity on **other** doctors of the same organisation, never the doctor's own calls.
  * *Rule 3 (top-level rule):* a BHO record without a parent is a candidate real organisation call. It is kept apart and not used until V3 is confirmed.
  * *Rule 4 (parent class rule, from the 3 Nov fixes):* a BHO child inherits the meaning of its parent. A copy of an account / office call or of an MSL call is not a rep interaction with a doctor.

* **Worked example (simplified IDs).** Organisation `BHO201` has five affiliated doctors in master data: `BH101`, `BH201`, `BH301`, `BH401`, `BH501`. Three call records exist:

| HCP_ID | CALL_ID | PAR_CALL_ID | Record class | What happened | Belongs to |
| --- | --- | --- | --- | --- | --- |
| BH101 | VC101 | - | `HCP_INTERACTION` | A rep visited doctor BH101 | BH101 |
| BHO201 | VC201 | VC101 | `BHO_CHILD` | Veeva automatically copied VC101 onto BH101's organisation | BH101 (same visit as VC101) |
| BHO201 | VC301 | NULL | `BHO_TOP_LEVEL` | A rep logged a call on the organisation itself (for example a practice meeting) | Whole organisation: BH101, BH201, BH301, BH401, BH501 |

How each doctor is counted:

| Doctor | NBA 3.0: BHO calls received | NBA 3.0: personal calls | NBA 3.1: own HCP interactions | NBA 3.1: organisation context |
| --- | --- | --- | --- | --- |
| BH101 | 2 (VC201 + VC301) | 1 (VC101) | 1 (VC101) | VC301 only, after B2 is confirmed (his own visit VC201 is excluded, Rule 2) |
| BH201 | 2 (VC201 + VC301) | 0 | 0 | 1 colleague visited (BH101, via VC201) + VC301 after B2 |
| BH301 | 2 (VC201 + VC301) | 0 | 0 | same as BH201 |
| BH401 | 2 (VC201 + VC301) | 0 | 0 | same as BH201 |
| BH501 | 2 (VC201 + VC301) | 0 | 0 | same as BH201 |
| **Total activity counted** | **10 BHO calls + 1 personal call = 11** from 2 real events | | **1 visit** | context counts, not new visits |

What the example shows:
* There were only **two real events**: the visit to BH101 (VC101, with its copy VC201) and the organisation call VC301.
* NBA 3.0 turned them into 11 counted calls. BH101's visit was counted twice for him (VC101 as a personal call, VC201 as a BHO call), and BH201 – BH501 each "received" BH101's visit as if they had been visited.
* NBA 3.1 counts the visit once, on BH101. Colleagues only learn that a colleague was visited. The top-level call VC301 is kept apart until the CRM team confirms what such calls are (B2); if confirmed, it is an organisation-level signal for all five doctors.
* In the V3 data, the first two rows are the common pattern (1,127,036 children with an `HCP_INTERACTION` parent); the third row is the 216,069 top-level records.

* **What V3 shows about these rules (Nov 2024 – Oct 2026, all products).**

| BHO records | Count | Share | Meaning for the rules |
| --- | --- | --- | --- |
| All BHO records | 1,493,555 | 100% | |
| `BHO_CHILD` (has parent) | 1,277,486 | 85.5% (Y1 80.5%, Y2 89.2%) | Copies; NBA 3.0 counted all of them as new activity |
| of which parent is an `HCP_INTERACTION` | 1,127,036 | 88.2% of children | Rule 1 confirmed by data: the visit is already counted on the doctor |
| of which parent is `ACCOUNT_OFFICE` or `MEDICAL` | about 112K | 8.8% of children | Rule 4: copies of no-HCP visits and MSL visits |
| of which parent not found in the extract | about 38K (incl. 7,096 empty `PAR_CALL_ID`) | 3.0% of children | Parent outside the period, not submitted, or a data issue |
| `BHO_TOP_LEVEL` (no parent) | 216,069 | 14.5% (Y1 123,869, Y2 92,200) | Rule 3: the only records that may be real organisation activity |
| Organisations per parent | 1 | | A copy goes to one organisation, not several |

* **Impact of the business rule.**
  * *Double counting removed.* In NBA 3.0 a doctor visit was counted on the doctor (Sales Rep Calls) and again on every doctor of his organisation, including himself (BHO calls). With 85 – 89% of BHO records being copies, most of the 30M BHO rows in NBA 3.0 repeat visits that are already in the personal features. NBA 3.1 counts each visit once.
  * *Feature size and meaning change.* BHO totals in the millions (6.2M face-to-face in 3 months) disappear. The new features are small counts that mean "how many colleagues at your organisation were visited", which Field Analytics can explain to a rep (S6).
  * *Fewer doctors with an organisation signal.* NBA 3.0 linked doctors through MDM affiliations (about 80 doctors per organisation call). NBA 3.1 links only doctors who appear in call data with the organisation, so coverage will be lower; it reflects real field contact rather than master-data membership.
  * *Possible loss of real organisation activity.* Until V3 is confirmed, 216,069 top-level BHO records (about 14.5%) are not used. If they are real organisation calls (for example staff meetings, practice lunches), this is a temporary signal loss.
  * *Account / office and MSL copies* (about 112K) no longer look like rep visits to colleagues. They can feed the account / office feature (C6) and the MSL flag (MD-1) instead, once confirmed.
  * *Comparison caveat.* V3 covers all products and two years; NBA 3.0 used Kerendia calls over one year. The review figure (494K of about 502K BHO calls are copies, 98%) is higher than V3 (85.5%); the difference is likely the product filter and period and should be reconciled before quoting one number.

* **Where we need client confirmation (based on V3 output).**

| # | Question for the CRM team | V3 evidence | Why it matters |
| --- | --- | --- | --- |
| B1 | Is a BHO record with `PAR_CALL_ID` always created automatically by Veeva when a doctor call is logged at an organisation? | 85.5% of BHO records have a parent; 88.2% of those point to a doctor call; one organisation per parent | Confirms Rule 1. If reps also create children by hand, some children would be real activity |
| B2 | When does a rep log a top-level organisation call (no parent), and what does it represent? | 216,069 top-level records | Decides whether Rule 3 is lifted and `FLD_ORG_TOP_LEVEL_CALLS_6M` is built |
| B3 | Why did top-level records fall (123,869 to 92,200) while children rose (512,127 to 765,359) between Year 1 and Year 2? | Opposite trends | A Veeva or process change would look like a change in organisation activity |
| B4 | Are BHO copies of account / office and MSL calls expected? Should they count as organisation context? | About 112K children (8.8%) | Confirms Rule 4 |
| B5 | What are BHO children with an empty or unknown parent? | About 38K (3.0%), including 7,096 empty `PAR_CALL_ID` | Decides whether to treat them as top-level, drop them, or fix the extract |
| B6 | Which definition of "doctors of an organisation" should the model use: MDM affiliations (NBA 3.0) or doctors seen with the organisation in call data (NBA 3.1)? | NBA 3.0: about 80 doctors per organisation call | Changes who receives organisation context and how many doctors have it |

* **Raise with client (CRM team).** Questions B1 – B6 above (summarised as C4 in section 6.4). Reason: without these answers we cannot use top-level BHO calls as a signal and may misread a process change as a behaviour change.
* **Suggestions.** Treat empty parent IDs as missing; keep top-level BHO calls out of features until the answer arrives (already done in notebook 41).

#### V4 – Key-message entry

* **Why we expect this.** NBA 3.0 had no information on what was discussed. Key messages tell whether the rep led with CKD or HF, which Field Analytics uses. They are only useful if reps enter them consistently; otherwise the feature describes the rep, not the doctor.
* **NBA 3.0 or new.** New.
* **Status.** Partly met. Indication codes exist only from July 2025 and are on 86 – 88% of Kerendia visits in 2026 (likely above 95% once account / office records are removed). Not done: the per-rep and per-territory check and the material share. Two concerns: the HF share fell from 52.6% to 30.5%, and the current training cohorts end in April 2025, before any codes exist.
* **Raise with client.**
  * Is entering key messages mandatory, and did the rules or the HF message change in 2026? Reason: a process change would look like doctors losing interest in HF.
  * Can training include cohorts after July 2025? Reason: without them, message features are 0 for every training row and cannot be learned.
* **Suggestions.** Add rep and territory to the extract and run the consistency check; build only a coarse feature first (any CKD vs any HF in 6 months) with a data-available flag; decide keep / coarse / drop at G2.

#### V5 – Sample reconciliation

* **Why we expect this.** NBA 3.0 used samples only as "call with sample", with no quantity, and the market access block uses a second sample table. Two sources for the same activity risk double counting.
* **NBA 3.0 or new.** New.
* **Status.** Met (30 Oct, `22_`). Both are the same records, but the market access table misses `AOC Received` and counts in-transit samples, so it holds only 13% of received units in Year 2.
* **What we found (`22_`, Nov 2024 – 23 Oct 2026).**
  * *Same source.* The market access table (`ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER`, read by notebook 17) is a status-filtered copy of `FACT_CALL_SAMPLE`: 100% line match on sample record, product, doctor, date and quantity. "Call samples" and "samples received / dropped" are the same records, so they must be built once (R1).
  * *Wrong status filter.* The table keeps `DELIVERED`, `Delivered_vod` and `Shipped_vod`. It misses `aoc_received__c`, the status used for almost all completed lines since the Vault CRM change (late July 2025), and it counts `Shipped_vod` (in transit) as received. It holds 87% of received units in Year 1 but only 13% in Year 2 (59K of 449K), and 23% of doctors who received samples. NBA 3.0 sample features collapse from August 2025 for a data reason, not a field reason (R2, R4).
  * *Orders settle in two to three weeks.* Orders older than three weeks are 95 – 98% received; the last week of data is only 14% received. There is no delivery date (`SYS_MODIFIED_ON` is touched by the weekly reload, `LAST_ACTY_DATE` is empty): only the order date and the **current** status (R7).
  * *Strength.* The 10 / 20 mg mix is stable (about 61% / 37%), so a split adds little. 40 mg exists from August 2025, reaches about 1,000 doctors a quarter and is HF-related (58 – 62% of 40 mg sample calls carry an HF key message vs 25 – 32% for 10 / 20 mg) (R5).
* **Business rule (status map, aligned with MV; R3, Q-S1 answered).** `aoc_received__c` counts as received; `Shipped_vod` does not.

| Mapped status | Raw statuses | Used in features |
| --- | --- | --- |
| RECEIVED | `DELIVERED`, `Delivered_vod`, `aoc_received__c` | Yes |
| PENDING (not yet received) | `Shipped_vod`, `In_Progress_vod`, `on_hold__c` | No |
| FAILED | `rejected__c`, `Returned`, `Cancelled_vod`, `lost_in_transit__c` | No |

* **Why the settling rule (R7) is needed, even with the `aoc_received__c` status.** The problem is not whether the status exists but *when* an order gets it. Status is overwritten, not stored over time.
  * *At scoring:* features are built from the data on the scoring date. Orders from the last two to three weeks are still `Shipped_vod` or pending, so the rule leaves them out and the most recent weeks look under-counted (for example, on the 23 Oct 2026 cut the week of 19 Oct is 14% received).
  * *In training:* history is queried today, so every order before a past anchor has already settled. The same weeks look complete.
  * *Effect:* the model learns from complete recent counts but is scored on incomplete ones (a training / scoring mismatch of the kind gate G1 checks for). Training must reproduce the state of the data on the day it would have been pulled.
* **Phase 4 solution (X1, proposed).**
  1. *One source, one build.* Build an intermediate table `field_sample_line` from `FACT_CALL_SAMPLE` (`SYS_DELETE_FLAG = '0'`, Kerendia 10 / 20 / 40 mg BRC, BHID from `MAP_CUSTOMER_XREF`): one row per sample line with BHID, call ID, order date, strength, quantity, raw status and mapped status. Notebook 17 either reads it or applies the same rule (Q-S2); the market access table is no longer used for sample features.
  2. *Status map in a config table* (table above). A status that is not in the map fails the run instead of being dropped silently, which is how NBA 3.0 lost `aoc_received__c`.
  3. *Settling rule.* For every cohort with lookback end L, count only orders placed before L − 21 days, in training, testing, back-testing and scoring alike. Drop the 1-month window (21 of its days would be excluded); use 3 / 6 / 12-month windows ending at L − 21. Optional: a "sample requests in the last 21 days" count over all lines, whatever their status (the order exists on the call date, so no leakage). Later option: weekly status snapshots (Q-S5); test against the 21-day cutoff in E5.
  4. *Features (about 10 columns).* `SMPL_RCVD_UNITS_3M/6M/12M`; `SMPL_RCVD_CALLS_3M/6M/12M` (distinct calls with at least one received line); `SMPL_DAYS_SINCE_LAST_RCVD` (999 when no history); `SMPL_40MG_RCVD_6M/12M`. No 10 vs 20 mg split. `SMPL_40MG_AVAILABLE` (cohort lookback after August 2025) is kept for checks only, not as a model input: it is the same for every doctor in a cohort, so it would act as a time marker and pick up period effects (Vault change, 2026 volume rise) instead of doctor behaviour.
  5. *Checks before E5.* Year 2 totals match `22_` (449,246 received units, 20,270 doctors); no PENDING or FAILED units and no order after L − 21 in the features; monthly units by status; October 2026 status shift rechecked in December 2026 (R6); fixed schema, no duplicate keys.
* **Cohorts and the 40 mg flag.** Phase 1 still reads the 26-cohort file `promotional_features_hcp_model_cohort_anchor_dates.csv` (C01 2023-03-17 to C26 2025-04-16), which ends before 40 mg, co-detail and the Vault change. With it, every 40 mg flag is 0 in training. NBA 3.1 should use the 28-cohort promotional file `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/cohorts/promotional/cohorts.parquet` (offset 17, 12-month lookback; c1 – c24 training, c25 – c26 testing, c27 – c28 back-testing):

| Cohorts | Lookback end | 40 mg in lookback (orders before L − 21) |
| --- | --- | --- |
| c1 – c15 (training) | 2024-06-17 to 2025-08-17 | None (c15 cutoff 2025-07-27) |
| c16 (training) | 2025-09-17 | Partly, about 3 – 4 weeks |
| c17 – c24 (training) | 2025-10-17 to 2026-05-17 | Yes |
| c25 – c26 (testing) | 2026-06-17, 2026-07-17 | Yes |
| c27 – c28 (back-testing) | 2026-08-17, 2026-09-17 | Yes |

  * 9 training cohorts contain 40 mg (8 with more than a few weeks); a full 6 months of 40 mg history only from about c21. This meets the proposed minimum of 6 training cohorts before the flag goes into E5.
  * The `aoc_received__c` fix is now needed in training, not only at scoring: 10 of 24 training cohorts (c15 – c24) end after the Vault change.
  * The same file also gives co-detail training data (c20 – c24 end after January 2026), which addresses P2 / N2 / Q5 in the Phase 1 analysis.
  * Do not fill 40 mg for older cohorts (it did not exist), and do not use HF key messages as a substitute (they also start only in July 2025).
  * c27 – c28 have prediction months September and October 2026 while the data runs to 23 Oct 2026: confirm that their target windows are complete in the target source before back-testing.
* **Raise with client.**
  * Who fixes the market access table or notebook 17, and when (Q-S2, C7). Reason: until then the existing sample features are wrong for Year 2, and wrong in training for every cohort after July 2025.
  * Can CareTria provide a delivery or status-change date, or can weekly status snapshots be kept from now on (Q-S5, C12)? Reason: it would replace the 21-day cutoff with real receipt dates.
  * Is 40 mg sampled mainly for HF patients (Q-S4, C13)? Reason: it decides whether the 40 mg flag can be explained to reps as an HF signal.
  * Modelling team: confirm the switch to the 28-cohort promotional file and the c27 – c28 target windows (C6).
* **Suggestions.** Build samples once with the agreed rule (received = `Delivered` + `AOC Received`) and let both blocks read the same output. Point Phase 1 and X1 to the 28-cohort file. Apply the 21-day cutoff to all cohorts. Keep the status map in config and report units by status every month.

#### V6 – Event states

* **Why we expect this.** NBA 3.0 counted a doctor as attending if `ATND = 'Attended'`, mixed speaker programs with scientific presentations and round tables, and had about 8,000 registrations a year (`Signed_vod`) without attendance. Registration is not attendance (example: 22 registered, 12 attended). NBA 3.1 keeps invited, registered and attended apart.
* **NBA 3.0 or new.** Attendance existed in 3.0; separate states and event-type groups are new.
* **Status.** Partly met (V6 cell fixed 4 Nov 2026). The first version had two errors: (1) no brand filter, so it counted events of every brand (67,173 records, including Lynkuet and Nubeqa); (2) it read `EVNT_STAT`, the status of the *event* (Closed, Completed), as the attendee status, so the `Signed_vod` check always returned 0. The cell now uses the NBA 3.0 filters (`PROD_BRAND_NM = 'KERENDIA'`, `CUST_HCP_ID` like `BH`) and the attendee status column `EVNT_ATNDE_RSVP_STAT`. Numbers below are from the same logic run directly on Snowflake (4 Nov 2026); the notebook cell itself still needs to be run.
* **What we found (Kerendia, doctor-event pairs).**

  *Event types among confirmed attendances (`ATND = 'Attended'`, the NBA 3.0 rule):*

  | Category (`EVNT_CAT`) | Type (`EVNT_TYP`) | Year 1 | Year 2 |
  | --- | --- | --- | --- |
  | SPEAKER PROGRAMS | Speaker Program | 3,375 | 3,736 |
  | NON-SPEAKER PROGRAMS | Scientific Presentation | 1,015 | 967 |
  | NON-SPEAKER PROGRAMS | Scientific Round Tables | 55 | 206 |
  | NON-SPEAKER PROGRAMS | `medical_event__c` | 0 | 90 |
  | NON-SPEAKER PROGRAMS | Sponsorship, Advisory Board, Other External Meeting, Symposium, Congress, Market Access, Investigator Meeting | 70 | 86 |
  | **Total** | | **4,515** (4,220 doctors, 507 events) | **5,085** (4,812 doctors, 607 events) |

  About 25% (Year 1) and 27% (Year 2) of the attendances NBA 3.0 counts as "speaker programs" are other event types.

  *NBA 3.0 type features.* NBA 3.0 tests the labels `SPEAKER PROGRAMS` and `NON-SPEAKER PROGRAMS` on `EVNT_TYP`, but these labels are the values of a different column, `EVNT_CAT` (event category). `EVNT_TYP` holds `Speaker Program`, `Scientific Presentation`, ... So `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM` and `TOTAL_SPKR_EVNT_TYP_NON_SPKR_PRGM` are always 0. The split exists in the data: testing the same labels on `EVNT_CAT` gives 3,375 / 1,140 (Year 1) and 3,736 / 1,349 (Year 2).

  *Attendee states:*

  | Attendee status (`EVNT_ATNDE_RSVP_STAT`) | `ATND` | Year 1 | Year 2 |
  | --- | --- | --- | --- |
  | (empty) | Attended | 4,515 | 5,085 |
  | `Signed_vod` | empty | 5,851 | 8,098 |
  | `Invited_vod` | empty | 456 | 1,125 |
  | `Accepted_vod` | empty | 343 | 893 |
  | `Nominated` | empty | 213 | 302 |
  | `Confirmed` | empty | 2 | 33 |

  `Attended` rows carry no attendee status, and `Signed_vod` rows carry no attendance value. Only 1 `Signed_vod` pair (Year 2) also has an `Attended` row for the same doctor and event. So the two are separate groups of doctors, not two records of the same attendance: if `Signed_vod` means "signed in", NBA 3.0 misses more than half of the real attendances (8,098 vs 5,085 in Year 2).
* **Raise with client (events team).**
  * What does `Signed_vod` without `ATND` mean on a closed event: no-show, not recorded, or attended? (Q-D1)
  * Which event types count as speaker programs, scientific events, medical events, sponsorship? (Q-D2)
  * Confirm access to attendee-level status (`FACT_EVENT_ATTENDEE`).
  * Reason: without these, an event feature mixes doctors who attended with doctors who only registered.
* **Suggestions.** Run the fixed V6 cell in the notebook. Build the event type from `EVNT_CAT` (speaker programs vs non-speaker programs) plus `EVNT_TYP` for the sub-groups, not from the NBA 3.0 labels on `EVNT_TYP`. Keep `Signed_vod` as its own state (`SPKR_SIGNED_12M`) next to confirmed attendance until Q-D1 is answered; do not merge it into attendance. Cross-check a sample of `Signed_vod` pairs against `FACT_EVENT_ATTENDEE`.

#### V7 – iRep checks

* **Why we expect this.** NBA 3.0 filtered delivered emails on `Delivered`, but Veeva stores `Delivered_vod`, so the feature was always 0. Separately, the open rate dropped in April 2026, possibly because tracking changed.
* **NBA 3.0 or new.** Correction of a 3.0 feature.
* **Status.** Fix met; opens not cleared, but the evidence now points clearly to a tracking change (re-checked 4 Nov 2026).
  * *Caveat on the first V7 cell:* it has no brand filter, so its figures are for **all brands** (481,973 emails, `Delivered_vod` 462,108, open rate 33 – 38% then 19 – 20%). A new cell `V7b` repeats the checks for Kerendia (NBA 3.1 Kerendia rule below, with the NBA 3.0 name rule shown alongside) and compares with other brands. Numbers below come from the same logic run directly on Snowflake; the V7b cell still needs to be run in the notebook.
  * *Delivered fix (Kerendia):* 72,981 `Delivered_vod`, 0 with the exact value `Delivered` that NBA 3.0 tests, so `TOTAL_IREP_EMAILS_DELIVERED` is 0 for every doctor. Other statuses: `Bounced_vod` 1,477, `Dropped_vod` 1,039, `Unsubscribed_vod` 367, `Marked_Spam_vod` 39. Delivered Kerendia emails: Year 1 40,257 (16,470 opened, 941 clicked); Year 2 32,724 (8,705 opened, 631 clicked).
  * *Which emails count as Kerendia (decided 4 Nov 2026).* NBA 3.1 keeps iRep emails that promote Kerendia, alone or co-promoted with another brand such as Lynkuet. The NBA 3.0 rule (name contains "Kerendia") is not enough: many Kerendia templates use the abbreviation `KER`. Delivered emails by template group:

  | Template group | Example | Year 1 | Year 2 | Counted in NBA 3.1 |
  | --- | --- | --- | --- | --- |
  | Name contains `Kerendia` (NBA 3.0 rule) | `Kerendia HF Content Share iRep Template` | 40,250 (37 templates) | 32,632 (19) | Yes |
  | Word `KER` / `PP-KER-` | `PP-KER-US-3624-1 KER CKD HCP Branded Content Share iRep Refresh 2025`, `KER HF National Broadcast iRep`, `KER T1D Now Approved`, `Ker Veeva Dig Live Invite Compliance` | 42,920 (18) | 41,533 (8) | Yes (missed by NBA 3.0) |
  | CKD / HF / T1D speaker-program pre- / post-meeting | `HF Speaker Program Pre-Meeting iRep` | 0 | 465 (6) | Yes |
  | Kerendia + Lynkuet co-promotion | — | 0 | 0 | Yes, when they appear (no approved document names both brands) |
  | Cardiorenal | `Cardiorenal Connection_Live` (Y1), `Cardiorenal Unbranded Content Share` (Y2) | 481 | 1,920 | To confirm (unbranded) |
  | Kerendia medical | `KER HF Indication Approval Medical Email to HCPs`, unsolicited request | 2,222 | 92 | No (medical, not rep promotion) |
  | Lynkuet only | `LYNKUET HCP iRep Email : Now Approved` | 0 | 68,602 (23) | No (not Kerendia) |

  With the NBA 3.1 rule, Kerendia iRep is about 83,200 delivered emails in Year 1 and 74,600 in Year 2, about **2.1 – 2.3 times** what NBA 3.0 sees. The open / click figures above use the NBA 3.0 name rule; the V7b cell now uses the NBA 3.1 rule and also flags co-promotion templates.
  * *Open-rate drop is not Kerendia-specific:*

  | Period | Kerendia open % | Other brands open % | Kerendia click % | Other brands click % |
  | --- | --- | --- | --- | --- |
  | Nov 2024 – Dec 2025 | 36.3 – 43.6 | 30.3 – 36.7 | 1.8 – 3.3 | 2.3 – 4.3 |
  | Jan – Mar 2026 | 28.2 – 36.0 | 29.8 – 33.9 | 1.6 – 2.3 | 2.7 – 3.6 |
  | Apr 2026 | 24.8 | 25.9 | 1.9 | 3.2 |
  | May – Oct 2026 | 18.5 – 23.5 | 18.6 – 23.6 | 1.3 – 3.1 | 2.2 – 2.8 |

  Both Kerendia and other brands fall at the same time and to the same level (about 18 – 24%), while **click rates stay in their usual range** (Kerendia 1.3 – 3.1%, other brands 2.2 – 2.8%). The same Kerendia templates also drop: `Kerendia HF Content Share iRep Template` 34.8% (Nov 2025 – Mar 2026) to 19.9% (Jun – Oct 2026), `BACC Kerendia - Medicare Access` 32.6% to 17.6%, `Prior Authorization Support Resources` 35.9% to 22.2%, `HF Epic` 43.0% to 16.3%. A real drop in doctor interest would be specific to a brand or template and would also show in clicks. This pattern fits a change in how opens are tracked (for example image blocking or a new email client privacy setting) in April 2026.
* **Raise with client (CRM email team).** Was there a tracking, vendor or privacy change around April 2026 (Q-C1)? The data now strongly suggests it; we need the date and the cause. Reason: opens before and after are not comparable, so an opens feature would teach the model a false trend (all training cohorts end before April 2026, while inference is after).
* **Suggestions.** Use delivered and clicked now (both stable). Keep opens out of the model (I-3) until Q-C1 is answered; if it is confirmed as a tracking change, either drop opens or use them only with a before / after flag. Also note that rep emails are counted again in the digital block (`IREP_EMAILS` channel), which breaks S3; the digital plan moves iRep to this block, so the digital block must drop it.

#### V8 – Asundexian readiness

* **Why we expect this.** The NBA 3.0 failure (V1) came from a new co-detailed product. Asundexian will be co-promoted by ISS reps, so the same risk returns.
* **NBA 3.0 or new.** New.
* **Status.** Not due: Asundexian appears only in MSL records so far. Its MSL activity is growing fast (6,452 records in Year 2 vs 1,908 in all of Jan 2022 – Apr 2025), but it is **not** part of the MSL flag (decision 5 Nov 2026, see V10).
* **Raise with client (sales operations).** Launch date, and whether ISS reps record Asundexian as a separate product detail in the same Veeva setup (Q5 / F-2). Reason: the Kerendia rule relies on separate detail rows.
* **Suggestions.** Schedule a re-run of V1d for the first month of co-promotion; add an alert if Kerendia first-priority share moves by more than 5 points.

#### V9 – Fixed schema and config

* **Why we expect this.** The model needs the same columns every run. If columns depend on the values present in the data (for example a new product or event type), a run can add or drop columns and break scoring.
* **NBA 3.0 or new.** New success criterion in 3.1 (S4).
* **Status.** Not met for G0: notebook 41 builds 53 columns from a config, but the two-run check was not done.
* **Raise with client.** No; internal.
* **Suggestions.** Run notebook 41 for two cohort sets or dates, compare column names, order and types, and record the result (A7).

#### V10 – MSL records

* **Why we expect this.** MSL (medical) visits are not sales calls and must never count as rep visits. NBA 3.0 did not handle them explicitly; they were mostly left out only because their product text (`Finerenone [...]`) did not equal `KERENDIA`. NBA 3.1 adds an MSL flag, approved by compliance on 30 Oct 2026. The review counted about 10,500 – 10,900 MSL visits a year with about 6,400 – 6,800 doctors.
* **NBA 3.0 or new.** New.
* **Status.** Met after the 3 Nov fix.
  * *Volume (Finerenone MSL):* 10,496 interactions / 6,409 doctors in Year 1 (bottom of the review range) and 11,401 / 6,947 in Year 2 (about 5% above the top, consistent with more Finerenone MSL activity).
  * *All medical products:* 22,773 (Y1) and 30,673 (Y2), about 2.8 times the target in Year 2, because MSL teams for Asundexian and Elinzanetant are now active.
  * *Classification:* 0 medical records among HCP interactions (independent check: any `MED` record type, `Event Call Report` or Finerenone product text). Before the fix, 5,045 Year 2 MSL records sat in doctor visits (none with Kerendia), and the notebook's own check could not see them because it reused the rule's list.
* **How MD-1 uses these records (notebook 43, step 3; built in Phase 3).** MD-1 is a yes / no flag per doctor and cohort (`FLD_MSL_INTERACTION_6M`, `FLD_MSL_INTERACTION_12M`); compliance allowed a flag only, no counts or topics.
  1. *Medical set:* submitted calls on non-BHO doctor IDs that pass the V2 medical pattern (record type **or** `Finerenone` product text). This is the `ALL_MEDICAL` set.
  2. *Scope (`MSL_SCOPE` in the config cell):* `FINERENONE` (default) keeps only records whose product text contains `Finerenone`; `ALL_MEDICAL` keeps the whole set. Under the default the record-type pattern does not change MD-1 (every Finerenone record already passes step 1); it matters for `ALL_MEDICAL` and for removing medical records from rep calls in notebook 41.
* **Scope check: Finerenone only vs all medical (5 Nov 2026, Snowflake `FACT_CALL`, same rule as notebook 43).**
  * *What the extra records are.* Year 2 medical records by product: Finerenone 11,187; Asundexian 6,452; Elinzanetant 4,918; other 7,542 (oncology: Nubeqa, Xofigo, Vitrakvi, Stivarga; haematology: Jivi, Kovaltry; PAH: Adempas; women's health: Mirena, portfolio; radiology: Gadoquatrane); empty 66. Finerenone product text is always `Finerenone [Kerendia/Firialta]`, sometimes with a `DKD`, `CKD` or `HFpEF` suffix.
  * *Overlap with Kerendia rep coverage* (doctor had a Kerendia rep call in the same period, MSL records excluded):

  | Doctors with an MSL visit | Apr 2024 – Apr 2025 | Year 2 | Kerendia-called (Apr 2024 – Apr 2025 / Y2) |
  | --- | --- | --- | --- |
  | Finerenone only | 5,522 | 6,456 | 53.7% / 58.8% |
  | Finerenone + other medical | 114 | 515 | 49.1% / 41.6% |
  | No Finerenone, Asundexian | 476 | 3,855 | 1.3% / 3.1% |
  | No Finerenone, other products only | 4,166 | 7,292 | 2.3% / 7.6% |

  * *Check on the promotional cohorts* (`cohorts/promotional/cohorts.parquet`, offset 17; 12-month lookback after `lookback_start_date` up to and including `lookback_end_date`; c1 – c24 Training, c25 – c26 Testing, c27 – c28 Holdout / Backtesting):

  | Set | Finerenone-flagged doctors | Of these Kerendia-called | Non-Finerenone-only doctors | Of these Kerendia-called | Asundexian-only doctors | `ALL_MEDICAL` ÷ Finerenone doctors |
  | --- | --- | --- | --- | --- | --- | --- |
  | Training c1 – c24 | 3,860 – 6,683 | 53.1 – 58.7% | 3,973 – 8,862 | 1.9 – 4.5% | 355 – 1,774 | 1.82 – 2.38 |
  | Testing c25 / c26 | 6,636 / 6,641 | 56.6 / 58.1% | 9,128 / 9,410 | 4.7 / 4.8% | 1,959 / 2,118 | 2.38 / 2.42 |
  | Holdout c27 / c28 | 6,798 / 6,915 | 58.3 / 58.2% | 9,839 / 10,390 | 5.2 / 5.9% | 2,453 / 2,935 | 2.45 / 2.50 |

  * *Reading.* The Finerenone flag is stable (about 6,400 – 6,900 doctors per cohort from c16, 53 – 59% Kerendia-called in every set). `ALL_MEDICAL` roughly doubles the flagged doctors but adds few Kerendia doctors: in c24 about 390 of 8,862 extra doctors are Kerendia-called vs about 3,600 from Finerenone; in c28 about 610 vs 4,000 (approximate, from rounded shares). The extra part grows from c11 (ratio 1.82) to c28 (2.50), so `ALL_MEDICAL` would mean something different in training than in testing and holdout.
  * *Asundexian (not added, decided 5 Nov 2026).* It is the only non-Finerenone MSL product with a link to Kerendia (cardiovascular audience; future ISS co-promotion, V8), but: only 1.3 – 3.1% of its doctors are Kerendia-called; its doctors grow from 355 – 1,774 in training to 2,935 in c28 (drift); it is not approved, so its MSL visits are pre-launch scientific exchange, a higher compliance risk in a promotional model; and the 30 Oct approval covers a Kerendia-related flag only. Revisit at co-promotion launch (V8 re-run), and only as a separate flag with its own compliance approval, never merged into MD-1.
  * *Caveats.* Doctor counts are not restricted to the HCP universe; "Kerendia-called" is a proxy for Kerendia relevance, not a link to prescribing.
* **Raise with client (medical affairs / compliance).**
  * Confirm the MSL flag counts only Finerenone visits (recommended), not any MSL visit to the doctor. Reason: non-Finerenone MSL doctors are almost all outside Kerendia rep coverage, grow over the cohorts, and fall outside the Kerendia-related compliance approval (evidence above).
  * Confirm the full list of medical record types (C3). Reason: the pattern covers the 12 types seen today; a new naming scheme would need a config update.
* **Suggestions.** Keep `MSL_SCOPE = "FINERENONE"` (no Asundexian); keep the independent sanity check in every run; drop medical-type records from the BHO classes (see V2); remove medical records before any Kerendia product-text filter (see V1). Optional, once C11 is confirmed: require both a medical record type and `Finerenone` text, so a non-medical record with Finerenone text cannot enter MD-1 (none exist today). Test E4 with and without MD-1, and keep MD-1 out of rep-facing driver text unless agreed.

### 6.4 Questions to send to the client

| # | Question | Team | Blocks |
| --- | --- | --- | --- |
| C1 | Confirm the Year 2 target as about 606K doctor visits + about 70K account / office records | Field Analytics | V1, V2 |
| C2 | Do the five no-HCP key messages always mean no doctor present? Are they used consistently? When a call has both an HCP message and an account message, which wins? | Field Analytics | V2 |
| C3 | Full list of medical record types; should the about 34K medical-type records on BHO IDs be dropped from organisation context? | CRM team, medical affairs | V2, V10 |
| C4 | BHO questions B1 – B6 (section 6.3, V3): copies vs real organisation calls; meaning of top-level calls; Year 2 drop in top-level records; copies of account / office and MSL calls; empty parent IDs; MDM vs call-based organisation membership | CRM team | V3 |
| C5 | Is key-message entry mandatory? Any change in HF messaging in 2026? | Maria Kontorinakis | V4 |
| C6 | Can training cohorts be extended past July 2025? Proposed: use the 28-cohort promotional file (`cohorts/promotional/`, c1 – c24 training up to lookback end 2026-05-17); confirm the switch and that the c27 – c28 target windows are complete | Modelling team | V4, V5 |
| C7 | Owner and date for the market access sample fix (Q-S2): fix the table or notebook 17, or read the shared `FACT_CALL_SAMPLE` build | Market access block owner | V5 |
| C8 | Meaning of `Signed_vod` without `ATND`; event-type groups; access to attendee status | Events team | V6 |
| C9 | Tracking change behind the April 2026 open-rate drop | CRM email team | V7 |
| C10 | Asundexian co-promotion date and how it is recorded | Sales operations | V8 |
| C11 | MSL flag: confirm Finerenone only (recommended, evidence in V10: c1 – c28 check, 5 Nov 2026). Asundexian and other medical products not included; Asundexian to be revisited only at co-promotion launch, as a separate flag | Medical affairs, compliance | V10 |
| C12 | Delivery or status-change date from CareTria, or weekly status snapshots from now on (Q-S5) | Samples operations, data team | V5 |
| C13 | Is 40 mg sampled mainly for HF patients (Q-S4)? | Kerendia brand team | V5 |
