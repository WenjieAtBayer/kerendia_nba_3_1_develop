# Phase 0 Speaker Programs Explained (V6)

**For:** readers new to the Kerendia event data  
**Validation step:** V6 of `40_field_activity_nba_3_1_readiness_plan.md`  
**Sources:** `40_field_activity_phase0_output_analysis.md` (V6, fixed 4 Nov 2026), `14_speaker_programs_nba_3_0.md` (NBA 3.0 logic), Phase 3 notebook `43_field_activity_phase3_events_irep_msl` (run 4 Nov 2026), direct Snowflake checks (5 Nov 2026)  
**Years:** Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026

**V6 in one sentence.** V6 checks whether the event data can tell apart doctors who were **invited**, who **registered**, and who really **attended** a Kerendia speaker program, and whether speaker programs can be separated from other event types.

**Status.** Partly met. The data supports separate states and event types, and NBA 3.1 builds them (Phase 3). Open: what `Signed_vod` means (Q-D1), which event types count as promotional (Q-D2), official topic groups (Q-D3).

---

## 1. What is a speaker program?

* A **speaker program** is an educational Kerendia event. A doctor paid by Bayer (the **speaker**) presents approved slides to other doctors (the **attendees**), often over dinner, sometimes online (remote) or both (hybrid).
* Reps **invite** doctors; doctors **register**; on the day, attendance is **recorded** (sign-in).
* Besides speaker programs there are **other events**: scientific presentations, scientific round tables, medical events, symposia, sponsorships, advisory boards.
* For the model, a doctor who keeps attending Kerendia talks is clearly interested in the medicine. That is why attendance is a feature.

---

## 2. The tables

### 2.1 `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` (main table, used by NBA 3.0)

One row per **doctor and event** (with some duplicate rows). Key columns:

| Column | What it holds | Example values |
| --- | --- | --- |
| `CUST_HCP_ID` | Doctor's Bayer ID | `BH...` (doctor), `BHO...` (organisation) |
| `EVNT_ID` | Event | |
| `EVNT_START_DATE` | Event date | |
| `PROD_BRAND_NM` | Brand of the event | `KERENDIA`, `LYNKUET`, `NUBEQA` |
| `EVNT_CAT` | **Event category** | `SPEAKER PROGRAMS`, `NON-SPEAKER PROGRAMS` |
| `EVNT_TYP` | **Event type** (finer) | `Speaker Program`, `Scientific Presentation`, `Scientific Round Tables`, `medical_event__c`, `Symposium`, ... |
| `EVNT_FMT` | Format | `Face-to-Face`, `Hybrid`, `Remote` |
| Topic column | Presentation title | `The next beat: KERENDIA (finerenone) for your patients with HF ...` |
| `EVNT_STAT` | Status of the **event** | `Closed`, `Completed` |
| `EVNT_ATNDE_RSVP_STAT` | Status of the **doctor** for this event (RSVP) | `Signed_vod`, `Invited_vod`, `Accepted_vod`, ... (section 4) |
| `ATND` | Attendance | `Attended` or empty (section 4) |
| Attendee type column | Attendee type | Prescriber, Non-Prescribing HCP, Business Professional, ... |

### 2.2 `CPH_DB_PROD.MODEL_V2.FACT_EVENT_SPEAKER` (speakers)

One row per **speaker and event**, with a speaker status (`Attended_vod`, `Signed_vod`, `Accepted_vod`, `No Show`). Not used by NBA 3.0. NBA 3.1 uses it for the "Kerendia speaker" flag (E-4).

### 2.3 `CPH_DB_PROD.MODEL_V2.FACT_EVENT_ATTENDEE` (attendee detail)

Attendee-level status (`STAT` column, different from `EVNT_STAT` and `EVNT_ATNDE_RSVP_STAT`). Planned cross-check for `Signed_vod` (Q-D1).

---

## 3. What NBA 3.0 did

(from `14_speaker_programs_nba_3_0.md`)

1. Keep Kerendia rows (`PROD_BRAND_NM = 'KERENDIA'`, doctor IDs like `BH`) with `ATND = 'Attended'`.
2. Count attended events over 1 – 6 months, by format, by type and by topic: **66 features** (11 measures x 6 periods).
3. Every row without `ATND = 'Attended'` is dropped, so invitations, registrations and `Signed_vod` are never seen.

---

## 4. Which values the two status columns hold

A doctor's situation at an event is stored in **two columns**: `EVNT_ATNDE_RSVP_STAT` (RSVP) and `ATND`.

### 4.1 `ATND`: only two values

| `ATND` value | Rows (all Kerendia) |
| --- | --- |
| `Attended` | 96,207 |
| Empty | 825,001 |

There is **no "No Show" or "Not Attended" value**. A doctor who did not come cannot be told apart from one whose attendance was never recorded.

### 4.2 `EVNT_ATNDE_RSVP_STAT`: 13 values

| RSVP value | Rows | With `ATND = 'Attended'` | Years seen | Plain meaning |
| --- | --- | --- | --- | --- |
| Empty | 807,901 | 55,992 | 2019 – 2026 | No status (mostly 2023) |
| `Signed_vod` | 55,747 | **0** | Jun 2022 – 2026 | Signed (meaning open, Q-D1) |
| `Walk-in` | 20,980 | 20,980 | 2021 – Sep 2022 | Came without registering |
| `Registered` | 18,682 | 18,682 | 2021 – Sep 2022 | Registered (old style) |
| `Invited_vod` | 9,933 | 334 | 2021 – 2027 | Invited |
| `Nominated` | 4,059 | 0 | 2022 – 2027 | Proposed by the rep |
| `Accepted_vod` | 3,128 | 0 | 2022 – 2027 | Accepted the invitation |
| `Confirmed` | 542 | 0 | 2022 – 2026 | Confirmed |
| `Wait-Listed` | 204 | 204 | 2021 – 2022 | On the waiting list |
| `Registration_Pending_vod` | 13 | 0 | Nov 2026 | Registration pending |
| `Cancelled` | 12 | 12 | 2021 – 2022 | Cancelled |
| `Cleared_Signature_vod` | 4 | 0 | Aug 2023 | Signature removed |
| `Undecided` | 3 | 3 | Feb 2022 | Undecided |

### 4.3 Two recording styles

* **Until September 2022:** the RSVP value sat on the attended row (`Walk-in`, `Registered`, `Wait-Listed`, ... together with `ATND = 'Attended'`). 2,906 doctor-event rows have both values, all between July 2021 and September 2022.
* **From June 2022:** the `_vod` values start, and **never** appear together with `Attended`. Attended rows have an empty RSVP, and RSVP rows have an empty `ATND`.

### 4.4 Kerendia states in Year 1 and Year 2 (doctor-event pairs)

| RSVP | `ATND` | Year 1 | Year 2 |
| --- | --- | --- | --- |
| Empty | `Attended` | 4,515 | 5,085 |
| `Signed_vod` | Empty | 5,851 | 8,098 |
| `Invited_vod` | Empty | 456 | 1,125 |
| `Accepted_vod` | Empty | 343 | 893 |
| `Nominated` | Empty | 213 | 302 |
| `Confirmed` | Empty | 2 | 33 |

---

## 5. Issues found

### Issue 1: event type tested on the wrong column (NBA 3.0 features always 0)

NBA 3.0 tests the labels `SPEAKER PROGRAMS` / `NON-SPEAKER PROGRAMS` on `EVNT_TYP`. These labels are values of **`EVNT_CAT`**; `EVNT_TYP` holds `Speaker Program`, `Scientific Presentation`, ... So `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM` and `TOTAL_SPKR_EVNT_TYP_NON_SPKR_PRGM` are **0 for every doctor**. Tested on `EVNT_CAT`, the split exists: 3,375 / 1,140 (Year 1), 3,736 / 1,349 (Year 2).

### Issue 2: other events counted as speaker programs

NBA 3.0 counts every attended Kerendia event as a speaker program. About **25% (Year 1) and 27% (Year 2)** are other event types:

| Category (`EVNT_CAT`) | Type (`EVNT_TYP`) | Year 1 | Year 2 |
| --- | --- | --- | --- |
| SPEAKER PROGRAMS | Speaker Program | 3,375 | 3,736 |
| NON-SPEAKER PROGRAMS | Scientific Presentation | 1,015 | 967 |
| NON-SPEAKER PROGRAMS | Scientific Round Tables | 55 | 206 |
| NON-SPEAKER PROGRAMS | `medical_event__c` | 0 | 90 |
| NON-SPEAKER PROGRAMS | Sponsorship, Advisory Board, Symposium, Congress, other | 70 | 86 |
| **Total** | | **4,515** | **5,085** |

### Issue 3: `Signed_vod` is bigger than attendance, and its meaning is unknown

* Year 2: **8,098** `Signed_vod` pairs vs **5,085** attended pairs. NBA 3.0 drops all `Signed_vod`.
* `Signed_vod` never has an attendance value. Only **1** doctor-event pair in Year 2 has both a `Signed_vod` row and an `Attended` row.
* By doctor: in Year 2, 7,617 doctors have `Signed_vod` and 4,853 have attended-only records; only **204 (about 3%)** have both, and almost always for **different** events.
* `Cleared_Signature_vod` exists (4 rows), which hints that `Signed_vod` relates to an attendance signature.
* **Two readings:** (a) `Signed_vod` = registered but not attended; (b) `Signed_vod` = signed the sign-in sheet, i.e. **attended**, recorded by a different process (event setup or vendor). If (b), NBA 3.0 misses **more than half of real attendance**. The low overlap between the two groups fits (b) better, but only the events team can confirm (Q-D1).

### Issue 4: the first V6 check was wrong (fixed 4 Nov 2026)

* No brand filter: it counted events of every brand (67,173 records, including Lynkuet and Nubeqa).
* It read `EVNT_STAT` (status of the **event**: Closed, Completed) as the doctor status, so the `Signed_vod` check always returned 0.
* Fix: Kerendia filter, doctor status from `EVNT_ATNDE_RSVP_STAT`, category from `EVNT_CAT`.

### Issue 5: topics matched by exact name

NBA 3.0 lists topic titles one by one. New presentations (HF from July 2025, T1D from 2026, new CKD decks) fall outside every group. NBA 3.1 groups topics by pattern (`CKD_CV`, `HF`, `CASE`, `T1D`); `OTHER_TOPIC` falls to 7 attendances in Year 1 and 0 in Year 2 (Phase 3).

### Issue 6: other NBA 3.0 label problems

(from `14_speaker_programs_nba_3_0.md`) The "format other" feature checks the topic, not the format; in-office meal programs are not counted.

### Issue 7: small gaps in the state map

`Registration_Pending_vod` (13 rows, future events) and `Cleared_Signature_vod` (4) are not mapped to a state in NBA 3.1 yet. `Cancelled`, `Undecided`, `Walk-in` always come with attendance, so they already count as attended.

### Issue 8: attendees are not only prescribers

Year 2 attended: 2,977 prescribers, 1,264 non-prescribing HCPs, 715 business professionals, others small. They only matter for the model if their BHID is in the HCP universe.

---

## 6. A small example

Three doctors and one Kerendia HF speaker program on 10 Sep 2026:

| Doctor | RSVP | `ATND` | NBA 3.0 counts | NBA 3.1 state |
| --- | --- | --- | --- | --- |
| Dr. A | Empty | `Attended` | 1 attended | Attended |
| Dr. B | `Signed_vod` | Empty | 0 | Signed, not attended (kept apart until Q-D1) |
| Dr. C | `Accepted_vod` | Empty | 0 | Registered, not attended |

NBA 3.0 sees 1 attendee and, because of Issue 1, `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM = 0` even for Dr. A. NBA 3.1 records Dr. A as attended (speaker program, HF topic), Dr. B as signed, Dr. C as registered. If Q-D1 says `Signed_vod` = attended, Dr. B moves to attended.

---

## 7. What NBA 3.1 builds (Phase 3)

* **States:** one state per doctor and event, strongest wins: attended > signed > registered (`Accepted_vod`, `Confirmed`, 2022 `Registered` / `Wait-Listed`) > invited (`Invited_vod`, `Nominated`).
* **Event group** from `EVNT_CAT` (speaker program vs scientific / other), **topic group** by pattern, **remote flag** from `EVNT_FMT`, **Kerendia speaker flag** from `FACT_EVENT_SPEAKER`.
* Results (Year 1 / Year 2): attended 4,515 / 5,082; speaker programs attended 3,375 / 3,733; `Signed_vod` 5,851 / 8,096; registered 345 / 926; invited 669 / 1,427; Kerendia speakers 197 / 223. All within 0.1% of Phase 0.
* In the training cohorts (all end by April 2025), HF and T1D topic features are 100% zero, and registered / invited are above 97% zero.

---

## 8. Open questions

| # | Question | Why it matters | Who |
| --- | --- | --- | --- |
| Q-D1 | What does `Signed_vod` without `ATND` mean on a closed event? Does the recording style depend on the event setup or vendor? Same question for speaker `Signed_vod` | Up to more than half of real attendance may be missing | Events team |
| Q-D2 | Which event types are promotional for the model (scientific presentations, round tables, `medical_event__c`, symposia)? | Decides the scientific-event feature | Events team |
| Q-D3 | Official topic groups; keep NBA 3.0's separate INTRO group? | Topic features | Brand team |
| — | What are the rows with neither RSVP nor attendance (751,909 rows, mostly 2023)? | Not used today | Events team |
| — | Access to `FACT_EVENT_ATTENDEE` to cross-check `Signed_vod` | Independent check of Q-D1 | Events team |
