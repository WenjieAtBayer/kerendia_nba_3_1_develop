# Phase 0 iRep Emails Explained (V7)

**For:** readers new to the Kerendia rep email data  
**Validation step:** V7 of `40_field_activity_nba_3_1_readiness_plan.md`  
**Sources:** `40_field_activity_phase0_output_analysis.md` (V7 / V7b, 4 Nov 2026), `12_irep_emails_nba_3_0.md` (NBA 3.0 logic), Phase 3 notebook `43_field_activity_phase3_events_irep_msl` (run 4 Nov 2026), direct Snowflake checks (5 Nov 2026)  
**Years:** Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026

**V7 in one sentence.** V7 checks that we can count, per doctor, the Kerendia emails reps sent that were **delivered**, **opened** and **clicked**, and that we pick the right emails as "Kerendia".

**Status.** Met for delivered and clicks (Phase 3 matches Phase 0 within 0.1%). Opens on hold because of a tracking change in April 2026 (Q-C1). Template groups are proposals (Q-C2).

---

## 1. What is an iRep email?

* A rep can send a doctor an email **from Veeva CRM** (the reps' tool). This is called **iRep email** (also "approved email" or "rep-triggered email").
* The rep cannot write freely: he picks an **approved template** (text and layout approved by medical / legal / regulatory), e.g. "Kerendia HF Content Share" or "Speaker Program Invitation".
* Veeva then records what happened: **delivered** to the inbox, **opened**, **clicked** a link, bounced, unsubscribed.
* For the model: a doctor who opens and clicks his rep's emails is engaged with the rep and the brand.
* iRep emails are **personal** promotion (sent by the rep). **HQ emails** are different: sent centrally by marketing, in the digital block.

---

## 2. The tables

| Table | One row per | Key columns | Used for |
| --- | --- | --- | --- |
| `CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL` | Email sent | `SNT_EMAIL_ID`, `SOURCE_CUST_ID` (doctor), `SOURCE_EMP_ID` (rep), `EMAIL_SNT_DATE`, `APV_EMAIL_TEMPLATE` (template ID), `STAT` (status), `OPENED` (opens), `CLK_CNT` (clicks) | Delivered / opened / clicked per email |
| `CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT` | Approved template | `APV_DOC_ID`, `NM` (template name) | Which brand / content the email is |
| `CPH_DB_PROD.MODEL_V2.FACT_EMAIL_ACTIVITY` | Event on an email (open, click, ...) | `SNT_EMAIL`, `EVNT_TYP`, `CLK_URL` (clicked link), `LINK_NM` | Which link was clicked |
| `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` | Veeva customer | `SOURCE_CUST_ID` → `BAYER_CUST_ID` (BHID) | Doctor ID |

There is **no brand column** on the email: the brand is only in the **template name**.

---

## 3. What NBA 3.0 did

(from `12_irep_emails_nba_3_0.md`)

1. Keep emails whose **template name contains "Kerendia"**.
2. Count per doctor over **3 months only**: delivered, opened, clicked, plus 11 template groups: **14 features**.
3. Template groups use **hard-coded lists of exact template names**.
4. The same iRep emails are **also counted in the digital block** (via MMX), so they enter the model twice.

---

## 4. Which values the tables hold

### 4.1 `FACT_SENT_EMAIL.STAT` (status of the email)

Kerendia templates (simple name rule: contains `Kerendia`, word `KER` or `PP-KER-`; no customer filter, so a little higher than the final counts):

| `STAT` | Year 1 | Year 2 | Plain meaning |
| --- | --- | --- | --- |
| `Delivered_vod` | 85,392 | 74,257 | Reached the inbox |
| `Bounced_vod` | 1,812 | 1,879 | Rejected by the mail server |
| `Dropped_vod` | 1,233 | 1,234 | Not sent (e.g. address blocked) |
| `Unsubscribed_vod` | 461 | 226 | Doctor unsubscribed |
| `Marked_Spam_vod` | 42 | 34 | Doctor marked it as spam |
| `Sent_vod` | 8 | 9 | Sent, no delivery yet |
| `Failed_vod` | 0 | 2 | Failed |

Every value ends in `_vod` (Veeva naming). **There is no value `Delivered`.**

### 4.2 `FACT_EMAIL_ACTIVITY.EVNT_TYP` (events on the email)

Same Kerendia emails, Year 1 + 2:

| `EVNT_TYP` | Events | Emails |
| --- | --- | --- |
| `Delivered_vod` | 168,349 | 162,007 |
| `Opened_vod` | 109,684 | 59,637 |
| `Clicked_vod` | 12,328 | 4,165 |
| `Bounced_vod` | 3,811 | 3,697 |
| `Dropped_vod` | 2,514 | 2,471 |
| `Viewed_vod` | 921 | 461 |
| `Unsubscribed_vod` | 703 | 657 |
| `Marked_Spam_vod` | 77 | 76 |
| `Unsubscribed_All_vod` | 60 | 55 |
| `Downloaded_vod` | 38 | 21 |

One email can have several opens and clicks, so events are higher than emails. `LINK_NM` is always empty; the link is only in `CLK_URL`.

---

## 5. Issues found

### Issue 1: delivered tested on the wrong value (NBA 3.0 feature always 0)

NBA 3.0's query keeps statuses starting with "Delivered", but the feature tests the exact value `Delivered`. Veeva stores **`Delivered_vod`**, so `TOTAL_IREP_EMAILS_DELIVERED` is **0 for every doctor**. Fix: test `STAT ILIKE 'Delivered%'` (or `= 'Delivered_vod'`).

### Issue 2: Kerendia emails missed by the name rule

NBA 3.0 keeps templates whose name contains "Kerendia". Many Kerendia templates are named with the short code **`KER`** or the document number **`PP-KER-...`**, e.g. `PP-KER-US-3624-1 KER CKD HCP Branded Content Share iRep Refresh 2025`, `KER HCP National Broadcast April 2025`, `KER T1D Now Approved`.

**NBA 3.1 Kerendia rule** (agreed with the user, 4 Nov 2026):

* **Include:** name contains `Kerendia`, the word `KER`, or `PP-KER-`, or a CKD / HF / T1D speaker-program pre / post meeting template.
* **Include when they appear:** co-promotion templates naming Kerendia and Lynkuet (none exist yet).
* **Exclude:** medical templates and Lynkuet-only templates (68,602 Lynkuet-only delivered in Year 2).

| Delivered Kerendia emails | Year 1 | Year 2 |
| --- | --- | --- |
| NBA 3.0 rule (name contains Kerendia) | 40,209 | 32,638 |
| NBA 3.1 rule | **83,090** | **74,525** |
| Ratio | 2.1x | 2.3x |

NBA 3.0 sees **less than half** of the Kerendia iRep emails.

### Issue 3: template groups by exact name (almost all 0)

NBA 3.0 lists 11 groups of exact template names. Only **0.4%** of recent emails fall in a group, and only `INVITE` is above 0. NBA 3.1 groups by pattern (proposal, Q-C2):

| Group | Year 1 | Year 2 | Example template |
| --- | --- | --- | --- |
| EHR | 1,211 | 1,853 | (templates about electronic health record tools) |
| ACCESS_PA | 8,736 | 9,824 | (access, prior authorisation, patient support, free trial templates) |
| EVENT_INVITE | 34,584 | 9,132 | `KER HCP National Broadcast April 2025`, `Ker Veeva Dig Live Invite Compliance` |
| T1D | 0 | 10,214 | `KER T1D Now Approved` |
| HF_CONTENT | 8,787 | 22,662 | `Kerendia HF Content Share iRep Template` |
| CKD_CONTENT | 27,178 | 16,480 | `PP-KER-US-3624-1 KER CKD HCP Branded Content Share iRep Refresh 2025` |
| INTRO_THANKYOU | 2,594 | 4,540 | (introduction and thank-you templates) |
| OTHER | 0 | 0 | |

### Issue 4: open rate drops in April 2026 (tracking change)

Monthly open rate (NBA 3.1 rule): **31.9 – 39.9%** from Jul 2025 to Mar 2026, **26.1%** in Apr 2026, **18.5 – 22.8%** from May to Oct 2026. The **click rate stays at 1.7 – 3.2%** throughout, and the drop hits **all brands and all templates equally**.

**Open-rate drop is not Kerendia-specific** (from `40_field_activity_phase0_output_analysis.md`, V7; open / click figures use the NBA 3.0 name rule):

| Period | Kerendia open % | Other brands open % | Kerendia click % | Other brands click % |
| --- | --- | --- | --- | --- |
| Nov 2024 – Dec 2025 | 36.3 – 43.6 | 30.3 – 36.7 | 1.8 – 3.3 | 2.3 – 4.3 |
| Jan – Mar 2026 | 28.2 – 36.0 | 29.8 – 33.9 | 1.6 – 2.3 | 2.7 – 3.6 |
| Apr 2026 | 24.8 | 25.9 | 1.9 | 3.2 |
| May – Oct 2026 | 18.5 – 23.5 | 18.6 – 23.6 | 1.3 – 3.1 | 2.2 – 2.8 |

Both Kerendia and other brands fall at the same time and to the same level (about 18 – 24%), while **click rates stay in their usual range** (Kerendia 1.3 – 3.1%, other brands 2.2 – 2.8%). The same Kerendia templates also drop: `Kerendia HF Content Share iRep Template` 34.8% (Nov 2025 – Mar 2026) to 19.9% (Jun – Oct 2026), `BACC Kerendia - Medicare Access` 32.6% to 17.6%, `Prior Authorization Support Resources` 35.9% to 22.2%, `HF Epic` 43.0% to 16.3%. A real drop in doctor interest would be specific to a brand or template and would also show in clicks. This pattern fits a change in how opens are tracked (for example image blocking or a new email client privacy setting) in April 2026.

Doctors did not suddenly stop reading; most likely the way opens are **tracked** changed (e.g. image blocking or email privacy features). Since all training cohorts are before April 2026 and scoring is after, an opens feature would learn a relationship the scoring data no longer has. **Opens are on hold** until the CRM email team confirms (Q-C1).

### Issue 5: link names are empty

`FACT_EMAIL_ACTIVITY.LINK_NM` is always empty, so the type of link clicked must come from the URL (`CLK_URL`). Top clicked URLs: `kerendiahcp.com` (1,351), `kerendiahcp.com/pi` (507), `bayer.com` (473), Vault viewer (445), unsubscribe (302). Access / savings links are rare: 56 emails in Year 1, 122 in Year 2.

### Issue 6: iRep counted twice in NBA 3.0

The same iRep emails also appear in MMX (vendor `IREP EMAIL`) and feed the NBA 3.0 digital block. NBA 3.1 counts them **once**, in the field activity block, and removes them from the digital block.

### Issue 7: unbranded templates to confirm

`Cardiorenal Unbranded Content Share` and `Cardiorenal Connection_Live` (481 / 1,920 delivered in Year 1 / Year 2) are excluded for now. Brand team to confirm whether they belong to Kerendia.

### Issue 8: only 3 months in NBA 3.0

NBA 3.0 uses a 3-month window only. NBA 3.1 uses 3, 6 and 12 months plus "days since last", like the call features.

---

## 6. A small example

Dr. D receives three emails from his rep in Feb 2026:

| Email | Template | `STAT` | Opened | Clicked | NBA 3.0 | NBA 3.1 |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | `Kerendia HF Content Share iRep Template` | `Delivered_vod` | Yes | Yes | Kept; delivered = 0 (Issue 1); opened 1; clicked 1 | Delivered, opened, clicked; group HF_CONTENT |
| E2 | `KER T1D Now Approved` | `Delivered_vod` | Yes | No | **Not seen** (no "Kerendia" in name) | Delivered, opened; group T1D |
| E3 | `PP-KER-US-3624-1 KER CKD HCP Branded Content Share iRep Refresh 2025` | `Bounced_vod` | No | No | Not seen | Not delivered, not counted |

NBA 3.0: 0 delivered, 1 opened, 1 clicked. NBA 3.1: **2 delivered**, 2 opened, 1 clicked.

---

## 7. What NBA 3.1 builds (Phase 3)

* Delivered Kerendia iRep emails (NBA 3.1 rule) per doctor: 3 / 6 / 12 months and days since last.
* Clicked (12 months), template groups (6 months), link-type clicks (access / content).
* Opens and the tracking-change flag built but kept out of the model (on hold).
* Results: Year 1 / Year 2 delivered **83,090 / 74,525**, to **36,479 / 32,128** doctors, from 55 / 33 templates; open rate 38.1% / 26.8%; click rate 2.6% / 2.1%. Within 0.1% of Phase 0.
* In training: 27,443 – 55,570 doctors per cohort have a delivered email in 12 months (19 – 35% zero); clicks are 97 – 99.6% zero; HF content and T1D groups are 100% zero (they start after the last training cohort).

---

## 8. Open questions

| # | Question | Why it matters | Who |
| --- | --- | --- | --- |
| Q-C1 | Did open tracking change in April 2026? | Opens on hold until confirmed | CRM email team |
| Q-C2 | Official iRep template groups | Template group features | Brand team |
| — | Are the Cardiorenal unbranded templates Kerendia? | 481 / 1,920 emails excluded | Brand team |
| — | Confirm the Kerendia rule (Kerendia alone or co-promoted; Lynkuet-only and medical excluded) | Defines which emails count | Brand team |
