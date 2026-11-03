## 6. Guide for new readers: why each expectation exists, and what to raise with the client

### 6.1 Background in five points

1. **NBA (Next Best Action)** is a model that ranks doctors (HCPs) for Kerendia reps to visit. NBA 3.0 is the current model; NBA 3.1 is the next version.
2. **Field activity** is what reps do with doctors: calls (visits), emails sent by reps (iRep), speaker events, MSL (medical) visits. These become model features such as "number of Kerendia calls in the last 3 months".
3. The **readiness plan** (`40_..._readiness_plan.md`, section 3) lists what is wrong with the NBA 3.0 field features. Each Phase 0 step (V1 – V10) checks that the data can support the fix before features are built.
4. The **expected figures** (for example about 660K calls) come from the earlier data review (`20_`), which counted the same data by hand. Phase 0 checks that the notebook reproduces them.
5. **Gate G0** is the checkpoint at the end of Phase 0: Phase 1 features are only trusted once the foundations pass.

**Status of this section:** updated 3 Nov 2026 after two fixes in the Phase 0 notebook: (1) `KEY_MSG_NM` is now brought into the V1a query, so account / office records are found; (2) medical record types are matched by pattern instead of a fixed list. V2, V3 and V10 below reflect the re-run.

### 6.2 Overview

| ID | NBA 3.0 problem behind the expectation | In NBA 3.0 or new in 3.1? | Expectation met? | Raise with client? |
| --- | --- | --- | --- | --- |
| V1 | Kerendia calls found by product text; co-detail calls missed | Calls existed in 3.0; the interaction grain and detail rule are new | Yes | Yes: confirm the split target (606K + 70K) |
| V2 | Account / office visits counted as doctor calls; BHO copies given to every colleague | New | Yes on rules (fixed 3 Nov); 3 points to confirm | Yes: no-HCP key-message list, calls with both HCP and account messages, medical records on BHO IDs |
| V3 | BHO calls repeated to about 80 colleagues per organisation | New (3.0 used BHO calls without this logic) | Data yes; business answer missing | Yes: CRM team questions |
| V4 | No key-message information in 3.0 | New | Partly | Yes: entry process and HF decline |
| V5 | Samples only as "call type with sample" | New | Yes (30 Oct) | Yes: who fixes the market access table |
| V6 | Registration treated as attendance; all event types mixed | Attendance existed in 3.0; separate states are new | No | Yes: `Signed_vod` meaning, event groups, attendee data |
| V7 | Delivered filter never matched (feature always 0) | Fix of a 3.0 feature | Fix yes; opens open | Yes: April 2026 open-rate drop |
| V8 | Text rule would break again with a new co-detailed product | New | Not due | Yes: launch date and recording |
| V9 | Columns not driven by a config | New (engineering standard) | No | No (internal) |
| V10 | MSL visits not handled explicitly | New (MSL flag, compliance-approved 30 Oct 2026) | Yes (volume and classification, fixed 3 Nov) | Yes: Finerenone-only scope |

### 6.3 Step by step

#### V1 – Interaction grain

* **Why we expect this.** NBA 3.0 kept a call only when the product text on the call equals `KERENDIA`. When a rep also presents Lynkuet in the same visit, the text holds both products, so the call is dropped. Since January 2026 (Lynkuet co-detailing) this loses 40 – 46% of Kerendia calls each month, and about 20,000 doctors look "never called". NBA 3.1 counts one visit once and checks the product detail rows instead of the text. The review counted about 660K calls and about 104K doctors in Year 2 this way, and Kerendia as first product on 87 – 92% of visits.
* **NBA 3.0 or new.** Call counts existed in 3.0. The rule (any Kerendia detail row) and the grain (one row per visit, products below it) are new in 3.1.
* **Status.** Met: 676,136 calls / 104,752 doctors; first priority 91.6%.
* **Raise with client.** Confirm that the target is two numbers: about 606K doctor visits plus about 70K account / office records. Reason: the 660K in the review included account / office records, which NBA 3.1 deliberately separates (V2).
* **Suggestions.** Use the same detail rule in every block that filters on Kerendia calls (for example samples, CLM). Run E1 (NBA 3.0 features with only this fix) to show the client how much the co-detail gap alone changes the model.

#### V2 – Record classification

* **Why we expect this.** NBA 3.0 counted every call record as a doctor call. About 10 – 12% of them are account-only or virtual-office records with no doctor present, and many are organisation (BHO) copies or MSL visits. NBA 3.1 gives every record one class so only true doctor visits feed the core counts.
* **NBA 3.0 or new.** New.
* **Status.** Met on rules after the 3 Nov fixes; three business points to confirm.
  * *What went wrong first:* `ACCOUNT_OFFICE` was 0, because the plan assumed "no HCP present" is stored in the record type; Veeva stores it as a key message (`FACT_CALL_KEY_MESSAGE.KEY_MSG_NM`). The medical list also used spaces where Veeva uses underscores and missed the Non Face2Face / Group types.
  * *Fix 1:* the V1a query now joins the key messages (one row per call: `KEY_MSG_NMS`, `HAS_ACCT_OFFICE_MSG`). Account / office: 76,662 Kerendia doctor calls in Year 1 (14.0%) and 69,897 in Year 2 (10.3%), within the expected 10 – 12% range in Year 2. Kerendia HCP interactions: 472,236 (Y1) and 606,239 (Y2).
  * *Fix 2:* medical record types matched by pattern (ends with ` Med` / `_Med`, starts with `BPH_MED_`, or `Event Call Report`; product text contains `Finerenone`). An independent check finds 0 medical records left among HCP interactions (was 5,045 in Year 2).
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
* **Raise with client.** Who fixes the market access table or notebook 17, and when (Q-S2). Reason: until then the existing sample features are wrong for Year 2.
* **Suggestions.** Build samples once with the agreed rule (received = `Delivered` + `AOC Received`) and let both blocks read the same output.

#### V6 – Event states

* **Why we expect this.** NBA 3.0 counted a doctor as attending if `ATND = 'Attended'`, mixed speaker programs with scientific presentations and round tables, and had about 8,000 registrations a year (`Signed_vod`) without attendance. Registration is not attendance (example: 22 registered, 12 attended). NBA 3.1 keeps invited, registered and attended apart.
* **NBA 3.0 or new.** Attendance existed in 3.0; separate states and event-type groups are new.
* **Status.** Not met. The event-type split works. The state map cannot be built: the table used (`ANLT_BASE_FACT_EVNT_PRSNL_PROM`) gives the status of the *event* (Closed, Completed), not of the attendee, so the `Signed_vod` check always returns 0.
* **Raise with client (events team).**
  * What does `Signed_vod` without `ATND` mean on a closed event: no-show, not recorded, or attended? (Q-D1)
  * Which event types count as speaker programs, scientific events, medical events, sponsorship? (Q-D2)
  * Confirm access to attendee-level status (`FACT_EVENT_ATTENDEE`).
  * Reason: without these, an event feature mixes doctors who attended with doctors who only registered.
* **Suggestions.** Re-run V6 on the attendee table; until Q-D1 is answered, use only confirmed attendance (`Attended`).

#### V7 – iRep checks

* **Why we expect this.** NBA 3.0 filtered delivered emails on `Delivered`, but Veeva stores `Delivered_vod`, so the feature was always 0. Separately, the open rate dropped in April 2026, possibly because tracking changed.
* **NBA 3.0 or new.** Correction of a 3.0 feature.
* **Status.** Fix met (`Delivered` = 0, `Delivered_vod` = 462,108). Opens not cleared: about 33 – 38% until March 2026, 19 – 20% from June, with similar email volumes.
* **Raise with client (CRM email team).** Was there a tracking or privacy change around April 2026 (Q-C1)? Reason: if so, opens before and after are not comparable and an opens feature would teach the model a false trend.
* **Suggestions.** Use delivered and clicked now; add opens only after the answer, with a before / after flag if needed.

#### V8 – Asundexian readiness

* **Why we expect this.** The NBA 3.0 failure (V1) came from a new co-detailed product. Asundexian will be co-promoted by ISS reps, so the same risk returns.
* **NBA 3.0 or new.** New.
* **Status.** Not due: Asundexian appears only in MSL records so far.
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
* **Raise with client (medical affairs / compliance).**
  * Should the MSL flag count only Finerenone visits, or any MSL visit to the doctor? Reason: the compliance approval covered a Kerendia-related flag, and non-Finerenone visits doubled in Year 2.
  * Confirm the full list of medical record types (C3). Reason: the pattern covers the 12 types seen today; a new naming scheme would need a config update.
* **Suggestions.** Default MD-1 to Finerenone only; keep the independent sanity check in every run; drop medical-type records from the BHO classes (see V2).

### 6.4 Questions to send to the client

| # | Question | Team | Blocks |
| --- | --- | --- | --- |
| C1 | Confirm the Year 2 target as about 606K doctor visits + about 70K account / office records | Field Analytics | V1, V2 |
| C2 | Do the five no-HCP key messages always mean no doctor present? Are they used consistently? When a call has both an HCP message and an account message, which wins? | Field Analytics | V2 |
| C3 | Full list of medical record types; should the about 34K medical-type records on BHO IDs be dropped from organisation context? | CRM team, medical affairs | V2, V10 |
| C4 | BHO questions B1 – B6 (section 6.3, V3): copies vs real organisation calls; meaning of top-level calls; Year 2 drop in top-level records; copies of account / office and MSL calls; empty parent IDs; MDM vs call-based organisation membership | CRM team | V3 |
| C5 | Is key-message entry mandatory? Any change in HF messaging in 2026? | Maria Kontorinakis | V4 |
| C6 | Can training cohorts be extended past July 2025? | Modelling team | V4 |
| C7 | Owner and date for the market access sample fix | Market access block owner | V5 |
| C8 | Meaning of `Signed_vod` without `ATND`; event-type groups; access to attendee status | Events team | V6 |
| C9 | Tracking change behind the April 2026 open-rate drop | CRM email team | V7 |
| C10 | Asundexian co-promotion date and how it is recorded | Sales operations | V8 |
| C11 | MSL flag: Finerenone only or any medical visit | Medical affairs, compliance | V10 |
