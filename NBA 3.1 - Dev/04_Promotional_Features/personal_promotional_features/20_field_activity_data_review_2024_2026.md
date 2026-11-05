# Field Activity Data Review (Nov 2024 – Oct 2026)

**Group:** Personal promotional features (promotion that involves a sales rep, or a speaker in person or live)  
**Purpose:** look at how Kerendia field activity (rep calls, organisation calls, iRep emails, speaker programs) changed over the last two years, check whether the NBA 3.0 features still capture it, and list extra columns and tables that could be added to the NBA 3.1 feature build.  
**Built from:** direct queries of Snowflake `CPH_DB_PROD.MODEL_V2` (Veeva CRM tables) and `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM`, compared with the NBA 3.0 notebook code  
**Date:** October 28, 2026

## What is this document about?

The files `10_` to `14_` in this folder explain how NBA 3.0 builds the personal-promotion features. This file looks at the **data itself** over two years (Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026) and asks three questions: what is the trend, does NBA 3.0 still see the activity, and what else is in the data that NBA 3.1 could use. CLM / clickstream is reviewed separately in `21_clickstream_clm_data_review_2024_2026.md`.

**How to read names.** Anything written `like this` is the exact name used in the data or the code.

**About the numbers.** `FACT_CALL` was last loaded on 24 October 2026 and has calls up to **23 October 2026**, so October 2026 is a partial month. A "call" is a submitted Veeva call record (`STAT = 'Submitted_vod'`). "Doctor" means a Bayer ID starting with `BH` but not `BHO`. These figures are my own queries and have not been checked by the CRM team.

---

## 1. In short

* **Since January 2026, NBA 3.0 misses about 40 – 46% of Kerendia doctor calls.** From January 2026 reps detail Kerendia together with Lynkuet (and a few other brands) in one call. Veeva then stores the product as `Kerendia  Lynkuet` (or `Lynkuet  Kerendia`). The NBA 3.0 filter `UPPER(DETL_PROD) = 'KERENDIA'` only keeps calls with Kerendia alone. In Year 2 it keeps 413K of 660K doctor calls (62%) and 84K of 104K called doctors; about **20,000 doctors** called only in combined calls get no call features at all.
* **Field activity grew in 2026 once co-detail calls are counted.** Doctor calls: 549K in Year 1, 660K in Year 2 (+20%). Doctors called each month rose from about 25,000 – 31,000 (H1 2025) to about 42,000 (Jun – Sep 2026). Reps active each month went from about 450 to about 650 – 690.
* **BHO (organisation) calls are mostly copies of doctor calls.** When a rep logs a call at a doctor who belongs to an organisation, Veeva also creates a "child" call on the organisation. 494K of the BHO calls in the last 12 months point back to a doctor call. NBA 3.0 then spreads every BHO call to all doctors linked to that organisation (about 80 each), so the BHO features mostly repeat the doctor-call signal, spread across colleagues.
* **Call length no longer carries information.** Until July 2025 most calls had no length recorded; from the week of 28 July 2025, 97% of calls show exactly `30` (a default value). `TOTAL_CALL_DURATION_*` is now just another call count.
* **"Group Detail" does not mean a group meeting.** 77 – 80% of doctor calls in 2026 have call type `Group Detail`, while only 3 – 4% are group calls by record type. It seems to mark "detail at an affiliated account" (to confirm, Q-A3).
* **There is much richer call information that NBA 3.0 does not use:** the **key message** of every call (which indication was presented first: CKD or HF), the **detail position** of Kerendia in the call, **samples** dropped (quantity and dose), the **rep and territory**, **medical (MSL) interactions** and the **Veeva suggestions** sent to reps (section 6).
* **iRep emails: volume flat, opens halved, and the template features are empty.** About 2,000 – 4,000 delivered emails a month. Open rate fell from about 40% to about 20% from April 2026. Only **0.4%** of the emails of the last 12 months use a template in the NBA 3.0 lists, so the 11 template features are almost always 0; the "delivered" feature is always 0 because the status is `Delivered_vod`, not `Delivered`.
* **Speaker programs: stable, but the topic and type features are empty.** About 4,500 – 5,000 attendances a year (4,200 – 4,700 doctors). None of the current presentation topics (HF LVEF ≥ 40%, CV risk in CKD + T2D, T1D) is in the NBA 3.0 topic lists. Another 8,000 registrations a year have status `Signed_vod` but no attendance flag, which may be real sign-ins (Q-D1).

## 2. Sales rep calls

### 2.1 Monthly activity

"Kerendia-only" = `DETL_PROD = 'Kerendia'` (what NBA 3.0 keeps). "Co-detail" = product text contains Kerendia plus another brand. "BHO" = calls on organisations (both kinds). "Medical" = medical / MSL interactions (product text `Finerenone [Kerendia/Firialta] ...`, see 6.6). "Doctors (all)" counts doctors with a Kerendia-only or co-detail call.

| Month | Kerendia-only doctor calls | Co-detail doctor calls | % missed by NBA 3.0 | BHO calls | Medical interactions | Doctors (all) | Doctors (Kerendia-only) | Reps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nov 2024 | 41,546 | 493 | 1.2 | 28,078 | 1,439 | 28,159 | 27,813 | 494 |
| Dec 2024 | 30,278 | 324 | 1.1 | 20,580 | 692 | 22,785 | 22,539 | 477 |
| Jan 2025 | 33,166 | 351 | 1.0 | 22,182 | 642 | 23,519 | 23,281 | 464 |
| Feb 2025 | 46,079 | 384 | 0.8 | 30,673 | 1,471 | 29,821 | 29,575 | 456 |
| Mar 2025 | 48,466 | 396 | 0.8 | 32,757 | 2,641 | 30,594 | 30,366 | 456 |
| Apr 2025 | 50,294 | 428 | 0.8 | 34,873 | 1,612 | 30,952 | 30,712 | 442 |
| May 2025 | 45,293 | 271 | 0.6 | 31,622 | 1,329 | 28,660 | 28,503 | 435 |
| Jun 2025 | 41,369 | 231 | 0.6 | 30,044 | 1,310 | 27,145 | 27,008 | 471 |
| Jul 2025 | 37,688 | 431 | 1.1 | 25,976 | 1,478 | 26,093 | 25,843 | 867 |
| Aug 2025 | 49,233 | 839 | 1.7 | 34,065 | 1,672 | 33,695 | 33,391 | 528 |
| Sep 2025 | 58,051 | 718 | 1.2 | 41,561 | 1,591 | 37,936 | 37,648 | 552 |
| Oct 2025 | 61,882 | 688 | 1.1 | 45,995 | 2,119 | 38,879 | 38,633 | 542 |
| Nov 2025 | 45,414 | 448 | 1.0 | 34,529 | 1,543 | 32,306 | 32,100 | 540 |
| Dec 2025 | 36,634 | 405 | 1.1 | 28,363 | 1,283 | 27,672 | 27,462 | 539 |
| Jan 2026 | 23,112 | 10,020 | 30.2 | 25,302 | 859 | 24,710 | 17,925 | 542 |
| Feb 2026 | 27,979 | 21,851 | 43.9 | 39,344 | 1,253 | 33,708 | 19,684 | 539 |
| Mar 2026 | 32,049 | 23,615 | 42.4 | 42,908 | 1,672 | 35,302 | 21,003 | 543 |
| Apr 2026 | 35,497 | 24,302 | 40.6 | 45,690 | 1,445 | 37,534 | 23,106 | 612 |
| May 2026 | 35,176 | 24,478 | 41.0 | 44,243 | 1,440 | 38,236 | 23,787 | 670 |
| Jun 2026 | 38,063 | 28,628 | 42.9 | 49,540 | 2,128 | 41,262 | 24,963 | 680 |
| Jul 2026 | 37,565 | 29,975 | 44.4 | 50,309 | 1,619 | 42,096 | 24,894 | 688 |
| Aug 2026 | 35,957 | 30,994 | 46.3 | 50,664 | 1,737 | 41,940 | 23,641 | 671 |
| Sep 2026 | 37,592 | 31,450 | 45.6 | 52,890 | 2,040 | 42,714 | 24,665 | 656 |
| Oct 2026 (to 23rd) | 27,525 | 21,512 | 43.9 | 37,851 | 1,241 | 34,630 | 20,108 | 624 |

**Year totals (doctor calls):**

| | Year 1 (Nov 2024 – Oct 2025) | Year 2 (Nov 2025 – Oct 2026) |
| --- | --- | --- |
| Kerendia-only calls (NBA 3.0) | 543,345 | 412,563 |
| All Kerendia calls (incl. co-detail) | 548,899 | 660,241 |
| Doctors called, Kerendia-only | 86,134 | 83,947 |
| Doctors called, all | 86,825 | 103,946 |
| Doctors with at least one co-detail call | 2,216 | 52,672 |
| Average reps per called doctor | 1.65 | 1.34 |
| % of called doctors seen by more than one rep | 51% | 30% |
| Median calls per called doctor | 4 | 4 |
| % of called doctors with only one call | 27% | 26% |

So the **real** trend is growth (+20% calls, +20% doctors); the NBA 3.0 view shows a 24% **drop** in calls in Year 2, only because of the filter.

The main co-detail values in Year 2 are `Kerendia  Lynkuet` (334K calls), `Lynkuet  Kerendia` (90K), `Adempas  Kerendia` (11K), and small combinations with `Cardiovascular Unbranded`, `Nubeqa`, `Elinzanetant` and the women's-health brands. The order of the words follows the detail order (6.2).

The peak of 867 reps in July 2025 is a one-month spike (possibly a training / alignment change; not checked).

### 2.2 How calls are held and why (doctor calls, all Kerendia)

| Measure | Nov 2024 – Jun 2025 | Jul 2025 – Dec 2025 | Jan 2026 – Oct 2026 |
| --- | --- | --- | --- |
| Face-to-face record type | 97 – 98% | 96 – 97% | 96% |
| Group call record type | 2% | 2.5 – 3.3% | 3.4 – 3.6% |
| Remote record type | 0.3 – 0.9% | 0.4% | 0.3 – 0.5% |
| Call type `Group Detail` / `Group Detail with Sample` | 67 – 74% | 70 – 79% | 77 – 81% |
| Call type with sample | 7.5 – 10.5% | 7 – 9% | 9 – 16% (peak Jan – Feb 2026) |
| Purpose "with meal" | 12 – 13% | 12 – 14% | 11 – 14% |
| Call length exactly 30 | 27 – 29% | 97% (from 28 Jul 2025) | 96 – 97% |

Record types now in use: `Face2Face Signed`, `Group Call Signed`, `BPH_REMOTE_MEETING`, `BPH_REMOTE_GROUP_MEETING`, `Face2Face KAM Call`. No phone (`BPH_NON_FACE2FACE`) calls exist any more, so `TOTAL_PHONE_*` is always 0. Purposes are almost only `Promotional Activity` (87%) and `Promotional Activity with meal` (13%); the other purpose features are close to 0.

## 3. BHO (organisation) calls

* BHO calls are about 43% of all Kerendia call records (column "BHO calls" above), following the same trend as doctor calls.
* In the last 12 months, **494,177 BHO calls are "child" records of a doctor call** (`PAR_CALL_ID` points to a doctor call, `PAR_CALL_FLAG = 0`); only about 7,500 BHO calls are top-level calls of their own. In the other direction, 22,279 doctor calls are children of a BHO call (group calls where the doctor attended).
* NBA 3.0 (`13_promotional_features_bho_calls`) gives each BHO call to every doctor linked to the organisation. So a call to Dr. A at Clinic X becomes a BHO call for every doctor at Clinic X, **including Dr. A again**. The BHO features therefore measure "how many colleagues at my organisations were called", not separate organisation-level activity.
* For NBA 3.1 it is cleaner to build organisation-level features from the doctor calls directly (number of calls / called colleagues at the doctor's organisations, excluding the doctor), and to use only the top-level BHO calls as true organisation calls (Q-A2).

## 4. iRep emails

Kerendia = template name (`DIM_APPROVED_DOCUMENT.NM`) contains "Kerendia", as in NBA 3.0. Rates are per delivered email.

| Month | Sent | Delivered | Doctors | Reps | Opened | Open % | Clicked | Click % | Templates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nov 2024 | 3,333 | 3,204 | 2,726 | 133 | 1,329 | 41.5 | 82 | 2.6 | 17 |
| Dec 2024 | 3,796 | 3,697 | 2,721 | 115 | 1,598 | 43.2 | 78 | 2.1 | 16 |
| Jan 2025 | 4,382 | 4,155 | 3,656 | 121 | 1,860 | 44.8 | 129 | 3.1 | 18 |
| Feb 2025 | 3,727 | 3,589 | 3,362 | 152 | 1,584 | 44.1 | 138 | 3.8 | 17 |
| Mar 2025 | 2,538 | 2,435 | 2,417 | 116 | 1,027 | 42.2 | 76 | 3.1 | 13 |
| Apr 2025 | 1,262 | 1,205 | 1,157 | 83 | 493 | 40.9 | 30 | 2.5 | 14 |
| May 2025 | 3,394 | 3,321 | 3,050 | 118 | 1,344 | 40.5 | 81 | 2.4 | 15 |
| Jun 2025 | 2,639 | 2,575 | 2,201 | 95 | 1,056 | 41.0 | 60 | 2.3 | 11 |
| Jul 2025 | 3,484 | 3,355 | 3,413 | 163 | 1,326 | 39.5 | 67 | 2.0 | 12 |
| Aug 2025 | 6,216 | 5,946 | 4,728 | 165 | 2,330 | 39.2 | 136 | 2.3 | 11 |
| Sep 2025 | 4,060 | 3,901 | 3,489 | 167 | 1,702 | 43.6 | 88 | 2.3 | 10 |
| Oct 2025 | 2,994 | 2,874 | 2,730 | 160 | 1,127 | 39.2 | 81 | 2.8 | 12 |
| Nov 2025 | 2,878 | 2,771 | 2,761 | 140 | 1,021 | 36.8 | 64 | 2.3 | 12 |
| Dec 2025 | 2,432 | 2,362 | 1,973 | 98 | 918 | 38.9 | 54 | 2.3 | 11 |
| Jan 2026 | 939 | 825 | 895 | 98 | 237 | 28.7 | 20 | 2.4 | 11 |
| Feb 2026 | 2,451 | 2,232 | 2,259 | 151 | 813 | 36.4 | 39 | 1.7 | 12 |
| Mar 2026 | 3,345 | 3,215 | 2,559 | 154 | 1,138 | 35.4 | 60 | 1.9 | 12 |
| Apr 2026 | 4,348 | 4,218 | 3,326 | 165 | 1,058 | 25.1 | 80 | 1.9 | 11 |
| May 2026 | 4,236 | 4,109 | 3,156 | 153 | 883 | 21.5 | 55 | 1.3 | 12 |
| Jun 2026 | 2,608 | 2,510 | 2,368 | 176 | 471 | 18.8 | 46 | 1.8 | 13 |
| Jul 2026 | 2,302 | 2,217 | 2,053 | 163 | 415 | 18.7 | 69 | 3.1 | 12 |
| Aug 2026 | 2,939 | 2,821 | 2,722 | 162 | 608 | 21.6 | 40 | 1.4 | 14 |
| Sep 2026 | 1,879 | 1,819 | 1,813 | 125 | 397 | 21.8 | 36 | 2.0 | 15 |
| Oct 2026 (to 28th) | 3,012 | 2,927 | 2,669 | 137 | 704 | 24.1 | 70 | 2.4 | 14 |

Year 1: 40,257 delivered, 16,776 opened, 1,046 clicked, 23,743 doctors, 620 reps. Year 2: 32,026 delivered (−20%), 8,663 opened (−48%), 633 clicked, 17,330 doctors, 482 reps. Statuses: `Delivered_vod` 96%, `Bounced_vod` 2%, `Dropped_vod` 1.4%, `Unsubscribed_vod` 0.5%.

**Templates of the last 12 months** (delivered emails):

| Template | Emails | Open % | Click % | In NBA 3.0 lists? |
| --- | --- | --- | --- | --- |
| `Kerendia HF Content Share iRep Template` | 14,822 | 28.0 | 1.8 | No |
| `Kerendia Prior Authorization Support Resources iRep Email` | 4,474 | 27.0 | 1.7 | No |
| `BACC Kerendia - Medicare Access iRep - Vault` | 2,561 | 25.2 | 1.6 | No |
| `KERENDIA HCP Introductory IRep` (from Jun 2026) | 1,889 | 16.0 | 1.7 | No |
| `Kerendia HF Epic iRep Email` | 1,322 | 26.9 | 0.9 | No |
| `Kerendia T1D Content Share iRep Template` (from 19 Oct 2026) | 1,319 | 14.3 | 0.9 | No |
| `KERENDIA Indication Agnostic Thank You IRep` | 1,137 | 22.9 | 1.1 | No |
| `BACC Kerendia - Improved / Unrestricted / Commercial Access iRep - Vault` | 2,340 | 21 – 31 | 1.9 – 3.1 | No |
| `KERENDIA Digital Live Speaker Program Invite` (from 30 Sep 2026) | 837 | 39.3 | 4.9 | No |
| `Kerendia CKD assoc. with T1D PA and Appeal Support Resources iRep` | 428 | 22.0 | 2.1 | No |
| `Kerendia Remote Meeting Engage or Zoom Invitation` | 139 | 78.4 | 0.0 | Yes (`INVITE`) |

Only 0.4% of emails fall in an NBA 3.0 template group. New natural groups would be: HF content, T1D content, access / prior authorisation (BACC + PA), EHR (Epic / Oracle), introduction / thank you, and event invitation.

The drop in opens from April 2026 happens across templates, so it looks like a tracking change (for example email privacy features that pre-load or block images) rather than a change in doctor interest. To confirm (Q-C1) before using open counts as a feature.

## 5. Speaker programs

Kerendia = `PROD_BRAND_NM` contains "KERENDIA". "Attended" = `ATND = 'Attended'` (the NBA 3.0 rule); counts are distinct doctor-event pairs.

| Quarter | Attended | `Signed_vod`, no attendance flag | Invited / accepted / nominated only | Doctors attended |
| --- | --- | --- | --- | --- |
| Nov – Dec 2024 | 655 | 682 | 235 | 646 |
| Q1 2025 | 793 | 893 | 214 | 748 |
| Q2 2025 | 1,170 | 1,708 | 159 | 1,166 |
| Q3 2025 | 1,038 | 1,253 | 196 | 1,014 |
| Q4 2025 | 1,858 | 3,253 | 469 | 1,820 |
| Q1 2026 | 935 | 1,734 | 328 | 930 |
| Q2 2026 | 1,301 | 2,136 | 542 | 1,279 |
| Q3 2026 | 1,314 | 1,810 | 445 | 1,288 |
| Oct 2026 | 416 | 393 | 783 | 415 |

Year 1: 4,530 attendances by 4,236 doctors, 1,767 events. Year 2: 4,950 attendances by 4,687 doctors, 2,382 events (+35% events). Counting `Signed_vod` too, about 9,500 (Year 1) and 12,100 (Year 2) doctors.

Points that affect the NBA 3.0 features:

* **Topics.** The main topics in Year 2 are "The next beat: KERENDIA for your patients with HF with LVEF ≥40%" (full and condensed, about 2,100 attendances), "KERENDIA: At the heart of reducing CV risk in adult patients with CKD and T2D" (about 1,480), "Heart to Heart with KERENDIA: A Case Based Dialogue" and a new T1D topic (from 25 Sep 2026). **None is in the NBA 3.0 lists**, so `TOTAL_SPKR_TOPIC_CKD / CVR / INTRO` are 0; 1,164 attendances have no topic and land in `SPKR_TOPIC_OTHER`.
* **Event types.** Speaker programs are 3,694 of the attendances; there are also `Scientific Presentation` (917), `Scientific Round Tables` (163) and `medical_event__c` (90). NBA 3.0 counts all of them as speaker programs, and its type labels (`SPEAKER PROGRAMS`, `NON-SPEAKER PROGRAMS`) never match.
* **Format.** Mostly face-to-face; remote 0 – 66 a month; hybrid in some months; **no** `In-Office Meal` in two years.
* **Who attends.** Of registrations in Year 2, 9,738 are prescribers, 3,206 non-prescribing staff (nurses, pharmacists, etc.) and 2,046 business professionals (office staff). NBA 3.0 keeps any `BH` ID.
* **Speakers.** 320 (Year 1) and 229 (Year 2) distinct speakers in `FACT_EVENT_SPEAKER` for Kerendia events. Being a Kerendia speaker is not a feature in NBA 3.0.

## 6. Columns and tables not used by NBA 3.0

### 6.1 `FACT_CALL` columns (247 columns; NBA 3.0 uses 8)

Fill rate over Kerendia calls of the last 12 months:

| Column | Filled | Values / meaning | Use for NBA 3.1 |
| --- | --- | --- | --- |
| `DETL_PROD` (full text) | 100% | Product(s) detailed in the call, in detail order | Co-detail flag, Kerendia position (fix the filter) |
| `SOURCE_EMP_ID`, `TERR_ID` | 100% | Rep and territory | Number of reps, rep change, territory call intensity |
| `PAR_CALL_ID`, `PAR_CALL_FLAG` | 45% / 100% | Parent – child link between doctor and organisation records | Remove BHO double counting |
| `CALL_ATNDE_TYP` | 100% | `Person_Account_vod` / `Group_Account_vod` | Same as doctor vs BHO |
| `SMPL_CALL_FLAG` | 100% | 1 on 5.6% of calls | Sample call flag (better: `FACT_CALL_SAMPLE`) |
| `CALL_DATE_TM` | 100% | Date and time | Day-of-week / time-of-day pattern (low priority) |
| `CALL_ETY_DISPLAY_NM`, `CUST_ZIP`, `CUST_STATE` | 100% / 99.8% | Account name and address of the call | Call location (office vs hospital), geography |
| `CALL_CHNL` | 100% | `Face_to_face_vod` 99.6%, `Other_vod`, `Video_vod` | Duplicate of record type |
| `ATNDE_CNT` | 99.7% | 0 on 99% of calls | Attendees per group call (small) |
| `CLM_ID` | 13% | Call has CLM content | See file `21_` |
| `DBL_VST`, `UNPLANNED_CALL_FLAG` | 100% | Almost always 0 | Not useful |
| `CALL_DUR` | 100% | 30 on 97% since Aug 2025 | Not useful any more |
| Key message, notes, objective, subject, priority columns (`ZVOD_KEY_MSG`, `ADDL_KEY_MSG`, `NEXT_CALL_NOTE`, `PRE_CALL_NOTE`, `CALL_SUBJ`, `PROD_PRTY_*`, `ZVOD_CALL_OBJV`, `ACCOMPANIED_BY*`, `RMT_MT`) | 0% | Empty in this table | Use the child tables below |

### 6.2 `FACT_CALL_DETAIL`: product detail order

One row per product detailed in a call (`SOURCE_PROD_NM`, `CALL_DETL_PRTY` = position 1, 2, ...; `CALL_DETL_TYP` = `Paper_Detail_vod` or `EDetail_vod`). Every Kerendia call has detail rows.

| Quarter | Kerendia doctor calls | Kerendia in position 1 |
| --- | --- | --- |
| Q4 2024 (Nov – Dec) | 72,640 | 99.0% |
| Q1 – Q4 2025 | 128,842 – 146,960 | 99.1 – 99.5% |
| Q1 2026 | 138,626 | 87.2% |
| Q2 2026 | 186,144 | 92.3% |
| Q3 2026 | 203,533 | 91.8% |

About 14% of Kerendia details over the two years are `EDetail_vod` (detail on the tablet), much more than CLM content (under 1%). What `EDetail_vod` means exactly should be confirmed (Q-A4).

### 6.3 `FACT_CALL_KEY_MESSAGE`: what was presented

Almost every Kerendia call (99.9%) has key-message rows (`KEY_MSG_NM`, plus CLM presentation and slide names). Since **July 2025** reps record the **indication and position** of the detail:

| Quarter | Calls with key message | CKD message (position 1 or 2) | HF message (position 1 or 2) | Kerendia in position 1 | Lynkuet message | "Account call" (no doctor) | "vOffice call (no HCP)" |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Q3 2025 | 146,960 | 73,493 | 62,715 | 91,965 | 0 | 16,372 | 0 |
| Q4 2025 | 145,471 | 88,198 | 69,291 | 111,604 | 1 | 17,850 | 0 |
| Q1 2026 | 138,626 | 86,174 | 50,716 | 102,767 | 52,468 | 14,286 | 364 |
| Q2 2026 | 186,142 | 115,324 | 58,806 | 140,449 | 68,065 | 20,197 | 4,433 |
| Q3 2026 | 203,530 | 127,416 | 62,841 | 156,579 | 80,966 | 19,420 | 4,809 |

Message names: `1-Position 1 KER CKD (HCP call)`, `2-Position 2 KER CKD (HCP call)`, `3- Position 1 KER HF (HCP call)`, `4-Position 2 KER HF (HCP Call)`, `5- Acct Call`, `Position 1 LYN`, `Position 2 LYN`, `vOffice call (no HCP)`. Before July 2025 the codes were generic (`1-HCP Call`, `2-Account Call Only`). The same table also lists the materials shown (MVAs, leave-behinds, patient profiles, prior authorisation checklist, `26 ACC HFpEF ECDP Leave Behind`, `UACR Brochure`, ...).

Two uses: (1) **indication of the call** (CKD vs HF), which NBA 3.1 needs now that Kerendia has both indications; (2) **call quality**: about 10 – 12% of calls are flagged as account calls or virtual-office calls without the doctor, which NBA 3.0 counts as full doctor calls.

### 6.4 `FACT_CALL_SAMPLE`: samples

Kerendia samples are recorded as BRC (business reply card) items by strength (`Kerendia 10mg / 20mg / 40mg BRC`, with quantity `SMPL_QTY`).

| Quarter | Sample lines | Calls with samples | Customers | Quantity |
| --- | --- | --- | --- | --- |
| Q4 2024 (Nov – Dec) | 10,248 | 6,431 | 5,345 | 79,528 |
| Q1 2025 | 18,759 | 11,734 | 8,348 | 145,734 |
| Q2 2025 | 16,821 | 10,607 | 7,476 | 128,894 |
| Q3 2025 | 9,689 | 5,595 | 5,059 | 69,494 |
| Q4 2025 | 5,615 | 3,208 | 2,875 | 39,748 |
| Q1 2026 | 10,203 | 6,022 | 4,943 | 72,520 |
| Q2 2026 | 24,528 | 14,296 | 10,335 | 167,466 |
| Q3 2026 | 25,687 | 15,097 | 10,955 | 173,509 |

Samples fell in H2 2025 and more than doubled in 2026. NBA 3.0 only knows "call type with sample". Strength mix (10 mg 54%, 20 mg 41%, 40 mg 5% in Year 2) may hint at the patient type (the HF dose goes up to 40 mg; to confirm with the brand team).

### 6.5 `DIM_SUGGESTION` / `FACT_SUGGESTION_FEEDBACK`: Veeva suggestions to reps (= our NBA output)

`DIM_SUGGESTION` is the data team's Snowflake copy of the Veeva CRM **Suggestion** object (loaded by process `PROC_SURVEYNSUGGESTION` from `VAULT_CRM_AC2`). Every suggestion that reps see in Veeva lands here, together with what the rep did with it. For Kerendia it holds **our own NBA output** (checked 28 Oct 2026, see Q-B1):

* `BPH_USE_CASE_DESC` = `Kerendia NBA ML Alert` and `Kerendia NBA NW Alert` (`BPH_SOURCE = 'Analytical Model'`) are exactly the `Alert_Name` values of our monthly NBA file in Databricks, `kerendia_nba_3.kerendia_veeva_nba_alerts_pilot`, with the same text ("This HCP will likely write Kerendia this month. Strongly consider scheduling/making a call on this HCP. If this HCP is an absolute no-see consider sending iRep email and invite to P2P." / "Machine learning model indicates Dr. X is more likely to write Kerendia in the next 30 days.").
* Each month they are posted in Veeva on or the day before our NBA cycle date (for example 6 Mar, 7 Apr, 11 May, 10 Jun, 7 Jul, 6 Aug 2026), with an expiry date about one month later, matching `Suggestion_Expiry_Date` in our file.
* **HCP match** (Bayer ID, by month, Jan 2025 – Oct 2026): 99.9% of the HCPs in `DIM_SUGGESTION` are in our NBA file; 90 – 95% of the HCPs in our file appear in `DIM_SUGGESTION` (about 450 – 2,100 a month do not; reason not checked, possibly no Veeva account or no aligned rep). Example: Aug 2026 8,493 in both, 939 only in our file, 9 only in Veeva.
* `BPH_SOURCE = 'Business Rule'` is **not** the NBA model: it was `HCP iRep Email Engagement_Kerendia` (Nov 2024 – Jun 2025) and is `Weekly New Writer` since 15 May 2026 (posted every Friday: "Your New Writer attempted a Kerendia prescription that requires access support...", "Your New Writer has a Kerendia NBRx approved..."). The Friday dates match the weekly snapshots of `kerendia_nba_3_pace.new_path_analysis_new_writers_*` (PACE new-writer work), but this link is not confirmed.

**Row duplication.** Each suggestion appears about 8 times in the table (for example Aug 2026: 87,304 rows for 10,913 `SGTN_ID`). Always count distinct `SGTN_ID`.

Kerendia suggestions per quarter (distinct `SGTN_ID`; a suggestion is per HCP x rep, so one HCP can have several):

| Quarter | Use case | Suggestions | HCPs | Actioned % | Dismissed % | Marked complete % | Any response % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Q4 2024 (from Nov) | NBA ML | 34,979 | 19,640 | 5.4 | 5.2 | 31.8 | 42.4 |
| Q1 2025 | NBA ML | 57,941 | 20,551 | 5.2 | 5.0 | 33.7 | 44.0 |
| Q2 2025 | NBA ML | 44,758 | 22,176 | 5.6 | 4.7 | 30.1 | 40.4 |
| Q3 2025 | NBA ML | 46,424 | 33,203 | 4.8 | 5.2 | 31.7 | 41.7 |
| Q4 2025 | NBA ML | 51,435 | 27,033 | 4.3 | 3.9 | 24.4 | 32.6 |
| Q1 2026 | NBA ML | 46,113 | 18,737 | 5.4 | 3.7 | 28.4 | 37.4 |
| Q2 2026 | NBA ML | 33,600 | 16,336 | 4.8 | 3.5 | 20.3 | 28.6 |
| Q3 2026 | NBA ML | 27,585 | 9,793 | 2.4 | 3.5 | 13.2 | 19.2 |
| Q1 2026 | NBA NW | 6,781 | 3,643 | 3.6 | 8.1 | 16.5 | 28.2 |
| Q3 2026 | NBA NW | 5,483 | 2,272 | 4.6 | 5.7 | 17.3 | 27.6 |
| Q3 2026 | Weekly New Writer (business rule) | 7,273 | 4,296 | 2.7 | 1.1 | 8.3 | 12.1 |

The October 2026 cycle is still open (expires 6 Nov), so its response rates are not final. The number of NBA HCPs sent to Veeva halved from May 2026 (about 16,000 to about 8,500 a month), in line with our file (`kerendia_veeva_nba_alerts_pilot`: about 17,000 to about 9,500 HCPs). Rep response also fell: "any response" went from about 40 – 44% (2025) to about 19% (Q3 2026).

Use for NBA 3.1: as **features** they are risky (the model would learn from its own past output). As an **evaluation / feedback** source they are valuable: per HCP and rep we can see whether the NBA was actioned, dismissed (with reason in `FACT_SUGGESTION_FEEDBACK.DISMISS_FDBK1-4`) or marked complete, and link to the resulting call (`FACT_SUGGESTION_FEEDBACK.CALL_ID`). This is the field-adoption measure for the F2F NBA, like the speaker-program NBA tracker.

### 6.6 Medical (MSL) interactions in `FACT_CALL`

Records with product text `Finerenone [Kerendia/Firialta] ...` (1,073 different combinations, by indication: CKD, DKD, HF, HFpEF, CVD, T1D) and record types `Face2Face Interaction Med`, `BPH_MED_*`, `Remote Interaction Med`, `Event Call Report`. About 10,500 – 10,900 interactions a year with about 6,400 – 6,800 doctors, flat. Not used by NBA 3.0. A "medical interaction in the last N months" flag would show scientific engagement, if compliance allows medical data in a commercial model (Q-B2).

### 6.7 Other Veeva tables found (not profiled in detail)

| Table | What it holds | Note |
| --- | --- | --- |
| `MODEL_V2.FACT_EMAIL_ACTIVITY` | One row per iRep email event (open, click, with `CLK_URL`, `LINK_NM`, device) | Which link / document was clicked |
| `MODEL_V2.FACT_REMOTE_MEETING`, `FACT_REMOTE_MEETING_ATTENDEE` | Veeva Engage remote meetings (about 11K meetings, all brands) | Small; remote calls are 0.4% |
| `MODEL_V2.FACT_EVENT_SPEAKER`, `FACT_EVENT_ATTENDEE`, `FACT_EVENT_BUDGET` | Speakers, attendees and budgets of events | Speaker flag, event spend |
| `MODEL_V2.FACT_MEDICAL_EVENT` | Medical events | With 6.6 |
| `ANALYTICS_V2.ANLT_BASE_FACT_CUST_CALL_ACTY_ALIGNED` | Enriched call activity aligned to territories | Could replace the `FACT_CALL` + cross-reference join; to compare |
| `ANALYTICS_V2.REP_CALL_ACTIVITY_MONTHLY` | Rep-level monthly call activity | Rep capacity / reach |

## 7. Candidate additions for NBA 3.1 (facts, not decisions)

**Fixes to existing features (needed whatever else is added):**

| Code | Fix | Why | Size of effect |
| --- | --- | --- | --- |
| PF-1 | Keep calls where `DETL_PROD` contains Kerendia (not equal to) | Co-detail with Lynkuet since Jan 2026 | +60% calls, +20K doctors in Year 2 |
| PF-2 | Build BHO features without the doctor's own calls (use `PAR_CALL_ID`), or replace by "calls to colleagues at my organisations" | BHO calls are copies of doctor calls | 494K of about 502K BHO calls in 12 months |
| PF-3 | Drop `TOTAL_CALL_DURATION_*` or replace by call count | 97% default value 30 | |
| PF-4 | Drop `PHONE`, `EVENT_DETAIL` and rare purpose features; keep a single "with meal" feature | Always or almost always 0 | |
| PF-5 | iRep delivered: test `STAT ILIKE 'Delivered%'` | Always 0 now | 32K emails in Year 2 |
| PF-6 | iRep template groups: rebuild from current templates (HF content, T1D, access / PA, EHR, intro / thank-you, invite) | 0.4% coverage | |
| PF-7 | Speaker topics: rebuild from current topics (HF, CKD / CV, T1D, case-based) using the approval code or keywords instead of exact names | All topic features 0 | |
| PF-8 | Speaker programs: split speaker programs from scientific presentations / round tables; decide on `Signed_vod` | Mixed event types; possibly 2x attendance | |

**New features (in rough order of expected value):**

| Code | Feature idea | Source | Notes |
| --- | --- | --- | --- |
| PN-1 | Calls by indication of the main message: CKD-first, HF-first (last 1 / 3 / 6 months) | `FACT_CALL_KEY_MESSAGE` | From Jul 2025 only; enough history for NBA 3.1 |
| PN-2 | Co-detail share and Kerendia-in-position-1 share | `FACT_CALL_DETAIL` / `DETL_PROD` | Measures attention given to Kerendia |
| PN-3 | Recency: days since last call; regularity (gap between calls) | `FACT_CALL` | NBA 3.0 only has sums over 90 days |
| PN-4 | Samples: quantity and number of sample calls, by strength | `FACT_CALL_SAMPLE` | Strong rise in 2026 |
| PN-5 | Number of reps and rep change in the last 6 months | `SOURCE_EMP_ID` | Share of doctors with more than one rep fell from 51% to 30% |
| PN-6 | Account-only / virtual-office calls (no doctor present) counted separately | `FACT_CALL_KEY_MESSAGE` | About 10 – 12% of calls |
| PN-7 | Materials shown (MVA, patient profile, access / PA checklist, leave-behind), grouped like the HCP digital content groups | `FACT_CALL_KEY_MESSAGE` | Links field and digital content features |
| PN-8 | E-detail share | `FACT_CALL_DETAIL.CALL_DETL_TYP` | After Q-A4 |
| PN-9 | Medical interaction flag | `FACT_CALL` (Finerenone records) | After Q-B2 |
| PN-10 | Speaker-program registration without attendance; is a Kerendia speaker | `ANLT_BASE_FACT_EVNT_PRSNL_PROM`, `FACT_EVENT_SPEAKER` | Small groups |
| PN-11 | iRep clicked link / document group | `FACT_EMAIL_ACTIVITY` | Volumes are small (about 50 – 80 clicks a month) |

All new features need history: key messages from July 2025, co-detail from January 2026. Training windows earlier than these dates will show 0 and should be handled (for example train only on recent instances, or add a "data available" flag).

## 8. Open questions

| Code | Question | Who to ask |
| --- | --- | --- |
| Q-A1 | Since January 2026 reps detail Kerendia together with Lynkuet. Is this a permanent co-promotion, and which teams do it? Should a co-detail call count as a full Kerendia call? | Kerendia brand / sales operations |
| Q-A2 | Is it right that a BHO call with `PAR_CALL_ID` is an automatic copy of the doctor call? Which BHO calls are real organisation-level calls? | CRM team |
| Q-A3 | What does call type `Group Detail` mean for a call with one doctor (77 – 80% of calls)? | CRM team |
| Q-A4 | What is `EDetail_vod` in `FACT_CALL_DETAIL` (tablet detail without CLM, digital MVA)? Why is it about 14% when CLM is under 1%? | CRM / CLM team |
| Q-A5 | Why is call length 30 on 97% of calls from 28 July 2025? Is it a default in the new Vault CRM? | CRM team |
| Q-A6 | Are the key-message codes (`Position 1 KER CKD`, `5- Acct Call`, `vOffice call (no HCP)`) mandatory for reps, and will they stay stable? | Sales operations |
| Q-B1 | Are the `Analytical Model` suggestions in `DIM_SUGGESTION` the NBA output or another model? Who owns them? | NBA / field analytics team (answered, see section 9) |
| Q-B3 | Why do 5 – 10% of the HCPs in our monthly NBA file never appear as a Veeva suggestion? Who owns the `Weekly New Writer` business rule? | Data team / CRM team |
| Q-B2 | May medical (MSL) interactions be used as a feature in a commercial model? | Compliance / medical affairs |
| Q-C1 | Why did the iRep open rate fall from about 40% to about 20% in April 2026 (tracking change, email client privacy)? | CRM email team |
| Q-C2 | Is there an official grouping of iRep templates by message (HF, T1D, access, EHR)? | Kerendia brand team |
| Q-D1 | What does `Signed_vod` with no `ATND` value mean for a closed speaker program: did the doctor attend? | Events team |
| Q-D2 | Should scientific presentations and round tables (medical events) be kept with speaker programs? | Events team / compliance |
| Q-D3 | Is there a grouping of speaker-program topics (HF, CKD / CV, T1D, case-based)? | Kerendia brand team |

## 9. Answers (to fill in)

| Code | Answer | Source (who / meeting / date) |
| --- | --- | --- |
| Q-A1 | Yes, it is a permanent co-promotion. Asundexian will soon be added as another co-promoted brand, so the filter must keep any call where Kerendia is one of the products. | Wenjie Chen, 28 Oct 2026 |
| Q-A2 | | |
| Q-A3 | | |
| Q-A4 | | |
| Q-A5 | | |
| Q-A6 | | |
| Q-B1 | Yes. `Analytical Model` = our Kerendia NBA output (`Kerendia NBA ML Alert`, `Kerendia NBA NW Alert`), same names and text as `kerendia_nba_3.kerendia_veeva_nba_alerts_pilot`, posted on the NBA cycle date, 99.9% HCP match. Content owner = NBA team (file built in Databricks); `DIM_SUGGESTION` itself is the data team's Veeva copy (`PROC_SURVEYNSUGGESTION`). `Business Rule` = other use cases (iRep engagement until Jun 2025, `Weekly New Writer` since May 2026; owner to confirm). See 6.5. | My check, 28 Oct 2026 (to confirm owner of `Weekly New Writer` with the data team) |
| Q-B2 | Yes: an MSL interaction flag is within compliance. Built as MD-1 in `40_field_activity_nba_3_1_readiness_plan.md`; anything beyond a flag needs a separate confirmation | Wenjie Chen, 30 Oct 2026 |
| Q-B3 | | |
| Q-C1 | | |
| Q-C2 | | |
| Q-D1 | | |
| Q-D2 | | |
| Q-D3 | | |

## 10. References

* `00_README_folder_guide.md`: folder guide and shared ideas
* `10_sales_rep_calls_nba_3_0.md`, `11_bho_calls_nba_3_0.md`, `12_irep_emails_nba_3_0.md`, `14_speaker_programs_nba_3_0.md`: how the NBA 3.0 features are built
* `21_clickstream_clm_data_review_2024_2026.md`: CLM / iVA review (its Q4 on Lynkuet / Kerendia tagging is linked to Q-A1 here)
* NBA 3.0 notebooks `25_promotional_features_call`, `13_promotional_features_bho_calls`, `16_promotional_features_irep`, `14_promotional_features_speaker_program` (NBA 3.0 Ops pipeline)
* Snowflake tables: `CPH_DB_PROD.MODEL_V2.FACT_CALL`, `MAP_CUSTOMER_XREF`, `FACT_CALL_DETAIL`, `FACT_CALL_KEY_MESSAGE`, `FACT_CALL_SAMPLE`, `DIM_SUGGESTION`, `FACT_SENT_EMAIL`, `DIM_APPROVED_DOCUMENT`, `FACT_EVENT_SPEAKER`; `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM`
