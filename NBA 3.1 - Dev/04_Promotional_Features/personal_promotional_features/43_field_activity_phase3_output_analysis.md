# Field Activity Phase 3: Output Analysis (NBA 3.1)

**Notebook:** `43_field_activity_phase3_events_irep_msl`  
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 3: E-1 – E-4, I-1 – I-4, MD-1; conditions V6, V7, V10; gate G2; design principles 7, 8 and 10)  
**NBA 3.0 references:** `12_irep_emails_nba_3_0.md`, `14_speaker_programs_nba_3_0.md`  
**Run analysed:** 4 Nov 2026, serverless  
**Date:** 4 Nov 2026

**How to read this file.** Section 1 is the summary. Section 2 gives the background for a first-time reader. Section 3 explains what the notebook does. Section 4 goes through every expectation: why we expected it (from NBA 3.0), whether it is new, what we got, and what to raise with the client. Sections 5 – 8 list the gate, issues, client questions and next actions.

**Years.** Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026 (as in Phase 0). **Cohorts.** The 26 training cohorts C01 – C26 end between 2023-03-17 and 2025-04-16; each feature uses the 12 months up to the cohort end.

---

## 1. Summary

| ID | Expectation (readiness plan) | NBA 3.0 or new | Status | One-line result |
| --- | --- | --- | --- | --- |
| E-1 | Confirmed attendance, Kerendia events | Correction of 3.0 | **Met** | Attended Y1 4,515 / Y2 5,082 (Phase 0: 4,515 / 5,085); speaker programs 3,375 / 3,733; 3,715 – 9,407 doctors with an attendance per cohort |
| E-2 | `Signed_vod`, registered, invited kept apart | New | **Built, meaning open (Q-D1)** | `Signed_vod` without attendance Y1 5,851 / Y2 8,096, more than attendances; registered and invited are small (> 97% zero) |
| E-3 | Event type, topic and format | Correction of 3.0 | **Built, groups proposed (Q-D2, Q-D3)** | Type from `EVNT_CAT` (NBA 3.0 type features always 0); topic `OTHER` down from 263 to 7 in Y1 after tightening; HF / T1D topics have no training signal |
| E-4 | Kerendia speaker | New | **Built** | 123 – 362 speakers per cohort; > 99% zero |
| I-1 | iRep delivered / clicked | Correction of 3.0 | **Met** | NBA 3.1 Kerendia rule Y1 83,090 / Y2 74,525 (Phase 0 about 83,170 / 74,630); NBA 3.0 sees 40,209 / 32,638 and its delivered feature is always 0 |
| I-2 | iRep template groups | Correction of 3.0 | **Built, groups proposed (Q-C2)** | 0 Y1 / Y2 emails in `OTHER` (NBA 3.0: 0.4% of emails in a group) |
| I-3 | iRep opens | Kept from 3.0 | **Built, on hold (Q-C1)** | Open rate 32 – 40% to Mar 2026, then 18.5 – 26%; clicks stable; tracking flag 0 in every training cohort |
| I-4 | iRep link clicked | New | **Built, very sparse** | Access-link clicks 56 / 122 emails a year; > 99.9% zero |
| MD-1 | MSL interaction flag (Finerenone) | New | **Built** | Finerenone medical records Y1 10,462 / Y2 11,180; 3,838 – 5,636 doctors per cohort |
| G2 checks | Keys, nulls, invariants, recompute | — | **Pass (after one fix)** | 0 duplicates, 0 nulls, 16 / 16 invariants, 10 / 10 HCPs match in Snowflake |
| G2 gate | Plan section 8 | — | **Not met** | Event states and template groups not agreed; E3 / E4 not run |

**Bottom line.** The Phase 3 block is built and technically sound: it reconciles with Phase 0 within 0.2% (Finerenone medical records within 2.6%), and all G2 data checks pass. It fixes three NBA 3.0 defects that made features always 0 or incomplete: event type read from the wrong column, iRep delivered tested on the wrong status, and Kerendia templates missed when named `KER`. But **19 of the 39 features are above 95% zero in every training cohort**, and several (HF and T1D topics and templates, the open-tracking flag) are **100% zero**, because all cohorts end by April 2025. G2 stays open until the events and brand teams agree the states and groups and E3 / E4 are run.

---

## 2. Background for a new reader

1. **Speaker programs.** Educational Kerendia events: a doctor (the speaker) presents approved slides to other doctors, in person, online or both. Other events are scientific presentations, round tables, medical events and symposia. Veeva stores one row per doctor and event with an attendance value (`ATND`) and an invitation status (`EVNT_ATNDE_RSVP_STAT`).
2. **iRep emails.** Emails a rep sends from Veeva CRM with an approved template. Veeva records delivery (`STAT`), opens and clicks, and the links clicked.
3. **MSL interactions.** Medical science liaisons (medical staff, not sales) meet doctors too. Compliance confirmed on 30 Oct 2026 that a **flag** "had a medical interaction in the window" may be used (MD-1); nothing more detailed.
4. **What NBA 3.0 did.** It counted attended Kerendia events with format, type and topic labels over 1 – 6 months (66 features), and Kerendia iRep emails delivered / opened / clicked with 11 template groups over 3 months (14 features). No invitation states, no speaker flag, no MSL information.
5. **Why Phase 3.** The plan rebuilds these channels with confirmed attendance as the main signal (principle 7), separate invitation states, current topic and template groups, the corrected iRep rules from Phase 0 V7, and the MSL flag, all with the same windows and fixed schema as the Phase 1 block (principles 8 and 10). The output joins to Phase 1 on `HCP_COHORT_ID`.

---

## 3. How the notebook works

| Step | Cell | What it does |
| --- | --- | --- |
| Setup | 2 – 4 | Installs the Snowflake connector, defines `Get_Data_Snowflakes`, and holds the config: windows 3 / 6 / 12 months, state map, topic and template groups (proposals), Kerendia iRep rule, MSL rules, and `expected_feature_columns()` (39 columns) |
| Cohorts | 5 | Reads the 26 cohort end dates (C01 2023-03-17 to C26 2025-04-16) |
| 1a | 6 | Builds `field_event_state`: Kerendia events since 2022, one row per doctor and event (172,988 rows), strongest state wins (attended > signed > registered > invited > other); event group from `EVNT_CAT` / `EVNT_TYP`, topic group, remote flag. Builds the speaker list from `FACT_EVENT_SPEAKER` (6,362 speaker x event rows) |
| 1b | 7 | Reconciles states, event groups, topics and speakers with Phase 0 V6; lists topics left in `OTHER_TOPIC` |
| 2a | 8 | Builds `field_irep_email`: delivered Kerendia iRep emails since 2022 (575,221), with template group, co-promotion flag, NBA 3.0 name-rule flag, and link clicks from `FACT_EMAIL_ACTIVITY` |
| 2b | 9 | Reconciles with Phase 0 V7: NBA 3.1 vs 3.0 rule, groups by year, templates in `OTHER`, template-to-group map, monthly open / click rate |
| 3 | 10 | Medical records (V10 rules, same as notebook 41) and the Finerenone subset used by MD-1 |
| 4a | 11 | Attaches every record to the cohorts whose 12-month lookback contains it; leakage check |
| 4b – 4c | 12 – 13 | Aggregates the event, speaker, iRep and MSL features |
| 4d | 14 | Assembles one row per doctor and cohort, fills defaults (0, or 999 for "days since"), enforces the schema |
| G2 | 15 – 17 | Duplicate / null / 16 invariant checks; profile by cohort; independent Snowflake recompute for 10 C26 doctors |
| Results | 18 | Results summary |

**Changes during the run.**

* **Fix (step 4d).** The first run had 185,871 rows with no activity at all. The row list was taken from every event record, including `OTHER` states (179,487 rows, mostly 2022 – 2023 records with neither invitation status nor attendance) and invitations to non-speaker-program events, which feed no feature. Rows now come only from records that feed a feature. Rows: 1,518,235 down to 1,332,364; the check then passed.
* **Topic groups tightened.** `CKD_CV` now also takes the 2022 – 2024 CKD + T2D decks (`Introduction to KERENDIA`, `KERENDIA CONDENSED`, `Underscoring Early Patient ID`, `Guideline Directed ... Therapy`, `The KERENDIA Patient`, `Heart of the Matter`). These fill every training lookback; before the change 7,226 pre-Year-1 attendances were in `OTHER_TOPIC`.
* **Template groups tightened.** `CKD_CONTENT` now takes branded asset share, ADA and FIGARO templates; `ACCESS_PA` takes patient support and free trial. Emails in `OTHER`: 2022 125,764 to 216; 2023 7,555 to 846.
* **States.** `Registered` and `Wait-Listed` (2022 only, always together with attendance) added to registered.

---

## 4. Expectation by expectation

### E-1 — Confirmed attendance

* **Why we expect this.** NBA 3.0 already counted only attended events (`UPPER(ATND) = 'ATTENDED'`, `14_`, section 2): "A doctor who keeps attending Kerendia talks is clearly interested in learning about the medicine." The plan keeps confirmed attendance as the main event signal (principle 7, D5) and adds recency.
* **NBA 3.0 or new.** Kept from 3.0 (same rule), with 3 / 6 / 12-month windows instead of 1 – 6 months, plus `SPKR_DAYS_SINCE_ATTENDED` and `EVT_ATTENDED_ANY_12M` (all event types).
* **What we got.**

| | Phase 0 Y1 | Notebook Y1 | Phase 0 Y2 | Notebook Y2 |
| --- | --- | --- | --- | --- |
| Attended, any Kerendia event | 4,515 | 4,515 | 5,085 | 5,082 |
| of which speaker programs | 3,375 | 3,375 | 3,736 | 3,733 |
| of which scientific | 1,081 | 1,081 | 1,263 | 1,263 |
| of which other events | 59 | 59 | 86 | 86 |

  The 3 missing pairs in Year 2 are IDs that Phase 0 kept (`CUST_HCP_ID LIKE '%BH%'`) and the notebook drops (`BH%`, not `BHO%`). Phase 0's scientific figure is the sum of its V6 types (presentation, round table, medical event, symposium). In training, 3,715 – 9,407 doctors per cohort have an attendance in the last 12 months (higher in 2022 – 2023 cohorts); `SPKR_ATTENDED_12M` is zero for 83 – 93% of rows, `SPKR_ATTENDED_3M` for 94 – 99%.
  Attendees are not only prescribers: of 5,082 Year 2 attendances, 2,977 are prescribers, 1,264 non-prescribing HCPs and 715 business professionals. They only matter for the model if their BHID is in the HCP universe.
* **Status.** Met.
* **Raise with client.** Nothing new beyond Q-D1 / Q-D2. Inform that format features are reduced to one remote flag (Year 2: 3,357 face-to-face, 350 hybrid, 26 remote speaker-program attendances).
* **Suggestions.** Keep `SPKR_ATTENDED_6M`, `SPKR_ATTENDED_12M`, `SPKR_DAYS_SINCE_ATTENDED`; consider dropping `SPKR_ATTENDED_3M` if E4 gives it no weight.

### E-2 — Other states kept apart

* **Why we expect this.** NBA 3.0 removed everything that was not `Attended`. The data review found about 8,000 `Signed_vod` registrations a year without attendance and showed that registration is not attendance (22 registered / 12 attended example). The plan keeps invited, registered and attended as separate states (principle 7).
* **NBA 3.0 or new.** New.
* **What we got.** One state per doctor and event (strongest wins), speaker programs only:

| State | Veeva values | Y1 | Y2 | Zero rate in training |
| --- | --- | --- | --- | --- |
| Signed, no attendance | `Signed_vod` | 5,851 | 8,096 (8,018 speaker programs) | 87 – 93% |
| Registered | `Accepted_vod`, `Confirmed` (2022 also `Registered`, `Wait-Listed`) | 345 | 926 | 99.4 – 99.7% |
| Invited | `Invited_vod`, `Nominated` | 669 | 1,427 | 97.8 – 99.8% |

  `Signed_vod` almost never overlaps with attendance (one pair in Year 2), and it is larger than attendance. In 2022 – 2023 there are also 99,223 doctor x event records with neither status nor attendance (state `OTHER`, not used).
* **Status.** Built; the meaning of `Signed_vod` is open (Q-D1). If `Signed_vod` means "signed the attendance sheet", NBA 3.0 (and E-1) misses more than half of the real attendance.
* **Raise with client.** Q-D1 (most important event question). Also what the 2022 – 2023 records without any status are.
* **Suggestions.** Keep `SPKR_SIGNED_NO_ATND_12M` separate until Q-D1 is answered; if it means attendance, merge it into E-1. Registered and invited are too sparse to stand alone; combine them into one "invited or registered, not attended" feature if kept.

### E-3 — Event type, topic and format

* **Why we expect this.** NBA 3.0 had type, format and topic features (`14_`, sections 3 – 4) but: the two type features test `EVNT_TYP` for `SPEAKER PROGRAMS` / `NON-SPEAKER PROGRAMS`, labels that sit in `EVNT_CAT`, so they are always 0 (LSP-1); topic lists match exact names, so new presentations fall outside every group; and speaker programs are mixed with scientific events.
* **NBA 3.0 or new.** Correction of 3.0. Type from `EVNT_CAT`; scientific events counted separately; topic groups by pattern; format reduced to one remote flag.
* **What we got.** Speaker-program attendances by proposed topic group:

| Year | CKD_CV | HF | CASE | T1D | OTHER_TOPIC |
| --- | --- | --- | --- | --- | --- |
| Before Y1 (2022 – Oct 2024) | 17,249 | 0 | 93 | 0 | 18 |
| Y1 | 2,447 | 868 | 53 | 0 | 7 |
| Y2 | 1,498 | 2,139 | 85 | 11 | 0 |

  Main Year 2 topics: `KERENDIA: At the heart of reducing CV risk in adult patients with CKD and T2D` (CKD_CV), `The next beat: KERENDIA (finerenone) for your patients with HF with LVEF ≥40%` (HF), `Heart to Heart with KERENDIA: A Case Based Dialogue` (CASE), `The Next Chapter in CKD Associated With Type 1 Diabetes` (T1D). `OTHER_TOPIC` holds only `Kerendia Speaker Training`.
  In training, `SPKR_ATTENDED_HF_12M` and `_T1D_12M` are 100% zero (HF approved Jul 2025, T1D talks from Sep 2026), `CASE` 99.9%, and `SPKR_ATTENDED_CKD_CV_12M` is almost identical to `SPKR_ATTENDED_12M`. `SCI_EVENT_ATTENDED_12M` is above 99% zero, `SPKR_ATTENDED_REMOTE_12M` 94 – 99%.
* **Status.** Built; groups are proposals pending Q-D2 / Q-D3. **No training signal** for the topic split.
* **Raise with client.** Q-D3 (official topic groups; whether to keep NBA 3.0's separate INTRO group for introductory decks, which the proposal puts in CKD_CV); Q-D2 (are scientific presentations, round tables and `medical_event__c` promotional events for the model?).
* **Suggestions.** Do not expect the topic features to matter until cohorts after July 2025 exist (K6). Keep `SCI_EVENT_ATTENDED_12M` only if Q-D2 says these are promotional.

### E-4 — Kerendia speaker

* **Why we expect this.** The review (PN-10) proposed that doctors who speak for Kerendia are a distinct, highly engaged group. NBA 3.0 does not use `FACT_EVENT_SPEAKER`.
* **NBA 3.0 or new.** New.
* **What we got.** Speakers with status `Attended_vod` or `Signed_vod`: 197 doctors / 1,011 events in Year 1, 223 / 1,343 in Year 2. Per training cohort 123 – 362 speakers (falling from 359 in C01 to 134 in C26); `SPKR_IS_KERENDIA_SPEAKER_12M` 99.4 – 99.7% zero.
* **Status.** Built.
* **Raise with client.** Confirm that speaker status `Signed_vod` means the speaker gave the talk (same question as Q-D1, for speakers).
* **Suggestions.** One flag is enough; `SPKR_N_TALKS_12M` adds little. Speakers may need separate handling in the NBA list (they are already highly engaged).

### I-1 — iRep delivered and clicked

* **Why we expect this.** NBA 3.0 asks "Is this doctor reading the emails their rep sends?" (`12_`, section 1), but: its query keeps statuses starting with "Delivered" while the label tests the exact value `Delivered`; Veeva stores `Delivered_vod`, so `TOTAL_IREP_EMAILS_DELIVERED` is always 0 (`12_`, section 6). And its Kerendia rule (template name contains "Kerendia") misses templates named with `KER` (Phase 0 V7).
* **NBA 3.0 or new.** Correction of 3.0, with 3 / 6 / 12-month windows and recency (NBA 3.0 had 3 months only).
* **What we got.**

| Year | NBA 3.1 rule | NBA 3.0 name rule | Co-promotion | Doctors | Templates | Open % | Click % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Y1 | 83,090 | 40,209 | 0 | 36,479 | 55 | 38.1 | 2.6 |
| Y2 (to Oct 2026) | 74,525 | 32,638 | 0 | 32,128 | 33 | 26.8 | 2.1 |

  Phase 0 V7 (direct Snowflake): about 83,170 / 74,630; the gap of 0.1% comes from requiring a customer xref match and excluding BHO IDs. NBA 3.1 sees 2.1 – 2.3 times the emails NBA 3.0 sees. In training, 27,443 – 55,570 doctors per cohort have a delivered email in 12 months; `IREP_DELIVERED_12M` is zero for 19 – 35% of rows. Clicked features are 97 – 99.6% zero (click rate about 2 – 3%).
* **Status.** Met.
* **Raise with client.** Confirm the Kerendia iRep rule (Kerendia alone or co-promoted; Lynkuet-only and medical templates excluded); Cardiorenal unbranded templates.
* **Suggestions.** Keep delivered 3 / 6 / 12 months and days since; keep `IREP_CLICKED_12M` only (the shorter windows are too sparse). Remove iRep from the digital block to avoid double counting (S3; NBA 3.0 counts these emails twice, `12_`, section 6).

### I-2 — iRep template groups

* **Why we expect this.** NBA 3.0 groups templates by exact name; only 0.4% of last-12-month emails fall in one of its 11 groups, and only `INVITE` is above 0 in the saved table (`12_`, section 6). Field Analytics asked for groups that match current content (F-11).
* **NBA 3.0 or new.** Correction of 3.0 (pattern-based groups; proposal pending Q-C2).
* **What we got.** Delivered emails by proposed group:

| Year | EHR | ACCESS_PA | EVENT_INVITE | T1D | HF_CONTENT | CKD_CONTENT | INTRO_THANKYOU | OTHER |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 179 | 72,033 | 5,872 | 0 | 0 | 161,707 | 13,862 | 216 |
| 2023 | 610 | 21,570 | 1,221 | 0 | 0 | 46,989 | 3,730 | 846 |
| Jan – Oct 2024 | 108 | 12,403 | 21,238 | 0 | 0 | 51,716 | 3,074 | 52 |
| Y1 | 1,211 | 8,736 | 34,584 | 0 | 8,787 | 27,178 | 2,594 | 0 |
| Y2 | 1,853 | 9,824 | 9,132 | 10,214 | 22,662 | 16,480 | 4,540 | 0 |

  Largest Year 1 + 2 templates: `Kerendia HF Content Share iRep Template` 23,619 (HF_CONTENT), `PP-KER-US-3624-1 KER CKD HCP Branded Content Share iRep Refresh 2025` 19,962 (CKD_CONTENT), `KER HCP National Broadcast April 2025` 16,355 and `Ker Veeva Dig Live Invite Compliance` 11,878 (EVENT_INVITE), `KER T1D Now Approved` 8,426 (T1D). The full template-to-group map is printed in step 2b for the brand team.
  In training (6 months): `IREP_CKD_CONTENT_6M` 58 – 78% zero, `ACCESS_PA` 82 – 93%, `EVENT_INVITE` 69 – 99.6%; `HF_CONTENT` and `T1D` 100% zero, `EHR` > 99%.
* **Status.** Built; groups are proposals (Q-C2).
* **Raise with client.** Q-C2 with the template map; in particular whether national broadcasts belong with invitations, and whether the 2026 ACC consensus template is HF content.
* **Suggestions.** Keep CKD_CONTENT, ACCESS_PA and EVENT_INVITE; drop or merge EHR, T1D, HF_CONTENT and OTHER until later cohorts exist.

### I-3 — iRep opens (on hold)

* **Why we expect this.** NBA 3.0 counts opened emails (`TOTAL_IREP_EMAILS_OPENED_IN_LAST_3_MONTH`). Phase 0 V7 found a platform-wide drop in open rate in April 2026 with stable clicks, which points to a tracking change (image blocking / email privacy), not to doctors losing interest.
* **NBA 3.0 or new.** Kept from 3.0, plus a tracking-change flag.
* **What we got.** Monthly open rate on the NBA 3.1 rule: 31.9 – 39.9% from Jul 2025 to Mar 2026, 26.1% in Apr 2026, 18.5 – 22.8% from May to Oct 2026; click rate 1.7 – 3.2% throughout. `IREP_OPENED_3M` is 79 – 95% zero in training; `IREP_OPEN_TRACKING_CHANGE_FLAG` is 0 in every training cohort.
* **Status.** Built, on hold. All training cohorts are before April 2026 and scoring is after it, so the model would learn a relationship that the scoring data no longer has.
* **Raise with client.** Q-C1: confirm the tracking change with the CRM email team.
* **Suggestions.** Leave opens out of E4. If later cohorts span April 2026, test opens with the flag, or use open rate relative to the doctor's own pre-change level.

### I-4 — iRep link clicked

* **Why we expect this.** The review (PN-11) suggested the type of link clicked (access / savings vs content) as a more specific interest signal than "clicked".
* **NBA 3.0 or new.** New.
* **What we got.** `FACT_EMAIL_ACTIVITY` link names are empty, so links are grouped by URL. Emails with an access / savings link click: 56 in Year 1, 122 in Year 2; with a content click (system links excluded): 1,593 / 1,271. `IREP_CLICK_ACCESS_6M` > 99.9% zero, `IREP_CLICK_CONTENT_6M` 98.5 – 99.2% zero.
* **Status.** Built; too sparse to help the model.
* **Suggestions.** Drop `IREP_CLICK_ACCESS_6M`; `IREP_CLICK_CONTENT_6M` duplicates `IREP_CLICKED_6M`. Keep the logic for reporting.

### MD-1 — MSL interaction flag

* **Why we expect this.** Compliance confirmed a flag is allowed (30 Oct 2026, F-8 / D7). The plan expects about 10,500 – 10,900 Kerendia-related medical interactions a year with about 6,400 – 6,800 doctors (V10).
* **NBA 3.0 or new.** New.
* **What we got.**

| Year | All medical records | Doctors | Finerenone (MD-1) | Doctors |
| --- | --- | --- | --- | --- |
| 2022 | 22,658 | 11,405 | 8,335 | 4,709 |
| 2023 | 21,175 | 10,818 | 7,914 | 5,159 |
| Jan – Oct 2024 | 11,807 | 7,475 | 5,218 | 3,918 |
| Y1 | 22,715 (Phase 0: 22,715) | 12,883 | 10,462 | 6,409 |
| Y2 | 30,143 (Phase 0: 30,072) | 18,099 | 11,180 | 6,964 |

  Year 2 Finerenone is 2.6% above the rounded range of the review and doctors 2.4% above, but matches the Phase 0 V10 runs (Year 2 11,161 / 6,861 with the first rule, 11,401 / 6,947 with the pattern rule, which also counts BHO-linked records); medical volume is growing (1,704 records in Nov – Dec 2025, 3,207 in Q3 2026) and late MSL entries since the Phase 0 pull add 71 records (0.2%). Year 2 records are mainly `Face2Face Interaction Med` (6,583), `Non Face2Face Interaction Med` (1,737), `Group Interaction Med` (1,440). Per training cohort, 3,838 – 5,636 doctors have the 12-month flag (87 – 93% zero).
* **Status.** Built.
* **Raise with client.** A9: confirm the scope (Finerenone only, or any medical interaction: about 2.7 times more records).
* **Suggestions.** Test with and without MD-1 in E4 (plan section 7). Keep it out of rep-facing driver text unless agreed (plan, MD-1).

---

## 5. Gate G2

The plan's gate G2: "V4 decision taken; event states agreed with the events team; iRep template groups agreed; V10 done and MSL flag built; E3 and E4 run".

| Part | Status | Evidence |
| --- | --- | --- |
| V4 decision taken (Phase 2) | **Pass** | Coarse M1 + M3 after cohort extension; M2 dropped (`42_` output analysis) |
| Event states agreed with the events team | **Open** | States built and kept apart; Q-D1 (`Signed_vod`) and Q-D2 (event types) unanswered |
| Topic groups (part of E-3) | **Open** | Proposed groups; Q-D3 unanswered |
| iRep template groups agreed | **Open** | Proposed groups, 0 Y1 / Y2 emails unassigned; Q-C2 unanswered |
| V10 done and MSL flag built | **Pass** (scope to confirm, A9) | Medical records reconcile (Y1 exact, Y2 +0.2%); MD-1 built |
| Data checks (keys, nulls, invariants, leakage, recompute) | **Pass** | 0 duplicates, 0 nulls, 16 / 16 invariants, leakage check passed, 10 / 10 HCPs match |
| E3 run | **Open** | Not run; M1 not built |
| E4 run | **Open** | Not run; also needs E2 (G1 still open) |

**G2 is not met.** The block can enter E4 now with E-1, I-1, I-2 (proposed groups) and MD-1; E-2, E-3 and I-3 should wait for the client answers.

---

## 6. Issues

| # | Issue | Impact | Proposal |
| --- | --- | --- | --- |
| P1 | All training cohorts end by 2025-04-16 | HF topic and template, T1D, co-promotion and open-tracking features are 100% zero in training; topic split adds nothing | Extend cohorts (K6), as for Phases 1 – 2 |
| P2 | 19 of 39 features above 95% zero in every cohort | Noise and slower selection | Drop or merge after E4 (see suggestions per family) |
| P3 | `Signed_vod` meaning unknown | Up to more than half of real attendance may be missing from E-1 | Q-D1; keep separate until answered |
| P4 | Open-tracking change in April 2026 | Opens would teach a trend that scoring data does not have | Opens on hold (Q-C1) |
| P5 | Topic and template groups are proposals | Group features may change after Q-C2 / Q-D3 | Regenerate from the config once agreed |
| P6 | First-run bug: rows without activity | 185,871 empty rows (fixed) | Fixed in step 4d; invariant kept in G2 checks |
| P7 | 2022 – 2023 event records with no status or attendance (99,223) | Not used; unclear what they are | Ask the events team (with Q-D1) |
| P8 | Non-prescribers among attendees (Y2: 1,979 of 5,082) | None if they are not in the HCP universe | Check against the HCP universe when joining blocks |
| P9 | Output not written (`WRITE_OUTPUT = False`) | Phase 1 + 3 join must re-run both notebooks | Write once the volume path is agreed, as for notebook 41 |
| P10 | NBA 3.0 counts iRep in the digital block too | Double counting (S3) if both blocks are used | Remove iRep from the digital block in NBA 3.1 |

---

## 7. Client questions

| # | Question | Why it matters | Owner |
| --- | --- | --- | --- |
| Q-D1 | What does `Signed_vod` without an attendance value mean on a closed event? Also for speakers (`EVNT_SPEKR_STAT`), and what are the 2022 – 2023 records with no status at all? | 8,096 Year 2 pairs, more than the 5,082 attendances; decides whether E-1 misses half the attendance | Events team |
| Q-D2 | Are scientific presentations, round tables, `medical_event__c` and symposia promotional events the model should use? | Decides whether `SCI_EVENT_ATTENDED_12M` and `EVT_ATTENDED_ANY_12M` stay | Events team |
| Q-D3 | Official topic groups (HF, CKD / CV, case-based, T1D); keep a separate INTRO group as in NBA 3.0? | E-3 groups | Brand team |
| Q-C1 | Did open tracking change in April 2026 (image blocking, privacy)? | I-3 on hold until confirmed | CRM email team |
| Q-C2 | Official iRep template groups (map printed in step 2b) | I-2 groups | Brand team |
| A9 | MSL flag scope: Finerenone interactions only, or any medical interaction? | MD-1 definition (11,180 vs 30,143 records in Year 2) | Medical affairs, compliance |
| — | Are `Cardiorenal Unbranded Content Share` and `Cardiorenal Connection_Live` Kerendia iRep templates? | Currently excluded (481 / 1,920 emails in Y1 / Y2) | Brand team |

---

## 8. Next actions

| # | Action | Owner | Status |
| --- | --- | --- | --- |
| N1 | Send Q-D1, Q-D2, Q-D3, Q-C1, Q-C2, A9 and the Cardiorenal question with the topic and template maps | NBA team | Open |
| N2 | Extend cohort anchors past 2025-04-16 (K6), re-run notebooks 41 – 43 | Modelling team | Open |
| N3 | Run E2 vs E0 (closes G1), then E4 with E-1, I-1, I-2 and MD-1 (with and without MD-1) | NBA team | Open |
| N4 | After answers: update the state map, topic and template groups in the config cell and re-run | NBA team | Waiting for client |
| N5 | Drop or merge features above 95% zero after E4 | NBA team | Open |
| N6 | Write the Phase 3 output to the volume and join with Phase 1 on `HCP_COHORT_ID` | NBA team | Open |
| N7 | Remove iRep from the digital block (S3) | Digital block owner | Open |
| N8 | Update the readiness plan Phase 3 status with these results | NBA team | Open |
