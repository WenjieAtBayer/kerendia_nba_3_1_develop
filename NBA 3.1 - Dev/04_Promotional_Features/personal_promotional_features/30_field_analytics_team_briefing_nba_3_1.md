# Kerendia NBA 3.1: Field Features Briefing for the Field Analytics Team

**For:** Field Analytics team  
**From:** NBA team (Wenjie Chen)  
**Meeting:** October 29, 2026  
**Detail behind this note:** `20_field_activity_data_review_2024_2026.md` (same folder): all tables, numbers and methods

## Why this note

We are rebuilding the Kerendia **Next Best Action (NBA)** model for version 3.1. The field activity of each doctor (calls, organisation calls, iRep emails, speaker programs) is one of the most important inputs. You know the field, the reps and Veeva much better than we do, so before we build anything we would like your view on:

1. Whether we read the field data correctly (section 3).
2. Whether the changes we propose make sense from the field's point of view (section 4).
3. Anything we have missed, or anything that could worry reps or managers.

The questions are numbered **F-1 to F-16** (section 6) so we can note your answers in the meeting. Nothing in this note is decided yet.

All numbers are from our own queries of the Snowflake Veeva tables (`CPH_DB_PROD.MODEL_V2`), Nov 2024 – Oct 2026, data up to 23 Oct 2026. "Year 1" = Nov 2024 – Oct 2025, "Year 2" = Nov 2025 – Oct 2026.

---

## 1. NBA in one minute

* Once a month (the **NBA cycle**, around the 7th) the model scores each doctor on how likely they are to write Kerendia in the next 30 days.
* The selected doctors are sent to Veeva as **suggestions** to the aligned reps: `Kerendia NBA ML Alert` ("This HCP will likely write Kerendia this month. Strongly consider scheduling/making a call...") and `Kerendia NBA NW Alert` (potential new writer). They expire after about one month.
* To score a doctor, the model uses about 750 **features**: numbers that describe the doctor, for example "Kerendia calls in the last 90 days" or "speaker programs attended in the last year". This note is only about the **field** features.

## 2. What NBA 3.0 uses from the field today

| Channel | What NBA 3.0 counts per doctor | Time windows |
| --- | --- | --- |
| Rep calls | Calls where the product is exactly `Kerendia`, split by record type (face-to-face, group, remote, phone), call type (with / without sample, group detail), purpose (with meal, etc.) and total call length | Last 90 days and last year |
| BHO (organisation) calls | Calls logged on the doctor's organisations (`BHO` accounts), given to every doctor linked to that organisation | Same |
| iRep emails | Emails sent, delivered, opened, clicked, split into 11 template groups | Same |
| Speaker programs | Programs attended, split by format (live, remote, in-office meal) and topic group (CKD, CV risk, intro, other) | Same |
| CLM | Presentations shown on the tablet (reviewed separately) | Same |

## 3. What we found when we looked at two years of data

### 3.1 Calls with Lynkuet are missing (largest issue)

Since January 2026 most calls detail Kerendia **together with Lynkuet**, and Veeva stores the product as `Kerendia  Lynkuet` or `Lynkuet  Kerendia`. NBA 3.0 only keeps calls where the product is exactly `Kerendia`.

| | Year 1 | Year 2 |
| --- | --- | --- |
| All Kerendia doctor calls | 549K | 660K (+20%) |
| Calls NBA 3.0 sees | 543K | 413K (−24%) |
| Doctors called | 87K | 104K |
| Doctors NBA 3.0 sees as called | 86K | 84K |

So field activity **grew**, but NBA 3.0 sees a **drop**, and about 20,000 doctors who were called only in combined calls look "never called". Since February 2026, 40 – 46% of Kerendia calls each month are combined calls. We understand the co-promotion is permanent and Asundexian will be added.

### 3.2 Other things that changed in the field data

| What | What we see | Effect on NBA 3.0 |
| --- | --- | --- |
| Reps per month | About 450 (H1 2025) to about 650 – 690 (mid 2026); one spike of 867 in July 2025 | More coverage; fewer doctors seen by more than one rep (51% to 30%) |
| Organisation (BHO) calls | Almost all (494K of about 502K in 12 months) are automatic "child" records of a doctor call | The BHO features repeat the doctor-call signal and spread it to about 80 colleagues each |
| Call length | `30` on 97% of calls since 28 July 2025; mostly empty before | Call-length features carry no information |
| Call type `Group Detail` | 77 – 80% of doctor calls in 2026, but only 3 – 4% are group calls by record type | Unclear what this feature means |
| Phone calls | None in two years | Phone features always 0 |
| Key messages | Since July 2025 reps record the indication and position: `1-Position 1 KER CKD`, `3- Position 1 KER HF`, `Position 1 LYN`, `5- Acct Call`, `vOffice call (no HCP)` | Not used. About 10 – 12% of calls are account-only or virtual-office calls without the doctor, but NBA 3.0 counts them as doctor calls |
| Samples | Calls with samples fell in H2 2025 (about 3,200 in Q4 2025) and rose to about 15,000 a quarter in 2026; 40 mg started in Year 2 | Only "call type with sample" is used; no quantity or strength |
| Medical (MSL) interactions | About 10,500 a year with about 6,500 doctors, stored with product `Finerenone [...]` | Not used |
| iRep templates | 0.4% of emails in the last 12 months use a template from the NBA 3.0 list. Today: HF content share, prior authorisation support, BACC access, introductory, Epic, T1D | Template features almost always 0 |
| iRep opens | Open rate fell from about 40% to about 20% from April 2026, across all templates | Possibly a tracking change, not lower interest |
| iRep delivered | Status is `Delivered_vod`; the code looks for `Delivered` | Feature always 0 |
| Speaker topics | Current topics (HF LVEF ≥ 40%, CV risk in CKD and T2D, case-based dialogue, T1D) are not in the NBA 3.0 topic lists | Topic features 0 |
| Speaker attendance | About 5,000 attendances a year with `Attended`; about 8,000 more registrations a year with `Signed_vod` and no attendance value | We may be counting half of the real attendance |
| Speaker event types | Speaker programs plus scientific presentations, round tables and medical events, all counted together | Mixed signal |

### 3.3 How reps respond to the NBA suggestions

Veeva keeps every NBA suggestion and what the rep did with it (Snowflake `DIM_SUGGESTION`). For `Kerendia NBA ML Alert`:

| Period | Suggestions per quarter | Actioned | Dismissed | Marked complete | Any response |
| --- | --- | --- | --- | --- | --- |
| 2025 (Q1 – Q3) | 45K – 58K | about 5% | about 5% | about 30 – 34% | about 40 – 44% |
| Q4 2025 – Q2 2026 | 34K – 51K | 4 – 5% | 3.5 – 4% | 20 – 28% | 29 – 37% |
| Q3 2026 | 28K | 2.4% | 3.5% | 13% | 19% |

The NBA list was made smaller from the May 2026 cycle (about 16,000 to about 8,500 doctors a month in Veeva). Even so, rep response has fallen by half. We would like to understand why (F-12 to F-14).

## 4. What we propose for NBA 3.1

### 4.1 Fixes to existing features

| Code | Proposal | Why |
| --- | --- | --- |
| PF-1 | Count every call where Kerendia is **one of** the products (Lynkuet, Asundexian, Adempas, ...) | See 3.1: otherwise about 20,000 called doctors look "never called" |
| PF-2 | Stop giving organisation "child" calls to all colleagues. Replace with "calls to colleagues at my organisations" (excluding the doctor) and keep real organisation-level calls separately | See 3.2 |
| PF-3 | Drop call length | Default value 30 |
| PF-4 | Drop phone and rare purpose/type features; keep "with meal" | Always or almost always 0 |
| PF-5 | Fix iRep "delivered" | Wrong status value |
| PF-6 | Rebuild iRep template groups from today's templates: HF content, T1D content, access / prior authorisation, EHR (Epic / Oracle), introduction / thank-you, event invitation | 0.4% coverage today |
| PF-7 | Rebuild speaker topic groups: HF, CKD / CV risk, T1D, case-based | Topic features 0 today |
| PF-8 | Separate speaker programs from scientific presentations / round tables / medical events; decide whether `Signed_vod` counts as attended | See 3.2 |

### 4.2 New field features

| Code | Proposal | Source | Note |
| --- | --- | --- | --- |
| PN-1 | Calls by indication of the main message: CKD-first vs HF-first (last 1, 3, 6 months) | Key messages | From July 2025 |
| PN-2 | Share of calls that are combined with another brand, and share where Kerendia is detailed first | Call detail | Attention given to Kerendia in the call |
| PN-3 | Days since last call; regularity of calls | Calls | NBA 3.0 only has totals |
| PN-4 | Samples dropped (quantity, number of sample calls, by strength) | Call samples | |
| PN-5 | Number of reps calling the doctor; rep change in the last 6 months | Calls (rep ID) | Coverage and relationship continuity |
| PN-6 | Account-only / virtual-office calls counted separately from real doctor calls | Key messages | About 10 – 12% of calls |
| PN-7 | Materials shown in the call (MVA, patient profile, access / PA checklist, leave-behind) | Key messages | Links with the digital content features |
| PN-8 | Share of e-detail | Call detail | After F-6 |
| PN-9 | Medical (MSL) interaction in the last N months | Medical calls | Only if compliance allows (F-8) |
| PN-10 | Registered for a speaker program but did not attend; doctor is a Kerendia speaker | Events | |
| PN-11 | iRep link / document clicked | Email activity | Small volumes |

Key messages exist only from July 2025 and combined calls only from January 2026, so these features have a short history. We will handle this in training.

### 4.3 Using rep response to the NBA (not as a model input)

We do **not** plan to feed past NBA suggestions into the model (it would learn from its own output). We **do** plan to use rep response (actioned, dismissed with reason, marked complete, call made after the suggestion) to **measure field adoption** of NBA 3.1 and to compare it with 3.0.

## 5. What we would like from you

* Correct anything in section 3 that does not match what you see in the field.
* Tell us which proposals in section 4 you would keep, change or drop, and why.
* Tell us about field changes we may not know (realignments, new call rules, new materials, incentive changes) that would change how the data should be read.
* Help us understand rep response to NBA suggestions.

## 6. Questions for the meeting

**Calls and co-promotion**

| Code | Question |
| --- | --- |
| F-1 | In a combined Kerendia + Lynkuet call, how much time does Kerendia usually get? Should we count it as a full Kerendia call, or weight it (for example by detail position)? |
| F-2 | When will Asundexian be added, and will it be recorded the same way (one product text with both brands)? |
| F-3 | Are organisation (BHO) calls with a parent doctor call automatic copies created by Veeva? When does a rep log a real organisation-level call? |
| F-4 | What does call type `Group Detail` mean when only one doctor is in the call? |
| F-5 | Are the key-message codes (`Position 1 KER CKD`, `5- Acct Call`, `vOffice call (no HCP)`) mandatory, and do reps fill them reliably? Will they stay stable in 2027? |
| F-6 | What is an `EDetail_vod` detail (about 14% of Kerendia details) if CLM is used in under 1% of calls? |
| F-7 | Why do 97% of calls have length 30 since late July 2025? Is it a Vault CRM default? |
| F-8 | Can medical (MSL) interactions be used in a commercial model, and who would approve it? |
| F-9 | What happened in July 2025 (867 reps calling vs about 450 – 550 in other months)? Were there other realignments we should know about? |
| F-10 | Do samples (and the strength) tell you something about the doctor, for example HF patients on 40 mg? |

**iRep and speaker programs**

| Code | Question |
| --- | --- |
| F-11 | Is there an official grouping of iRep templates and speaker topics by message (HF, T1D, access, EHR)? Do you know why opens fell in April 2026? Does `Signed_vod` without an attendance value mean the doctor attended? |

**Rep response to NBA**

| Code | Question |
| --- | --- |
| F-12 | What do reps usually mean by "actioned" vs "marked complete" on an NBA suggestion? Is one of them the real "I acted on it" signal? |
| F-13 | Rep response fell from about 40% to about 19% in 2026. What do you hear from reps and managers: too many suggestions, wrong doctors, timing, Lynkuet focus, something else? |
| F-14 | Which dismiss reasons are most common, and are they useful to us? |
| F-15 | About 5 – 10% of the doctors on our monthly NBA list never appear as suggestions in Veeva. Do you know why (no aligned rep, no Veeva account, filters)? |
| F-16 | Who owns the weekly `Weekly New Writer` suggestions (since May 2026), and should NBA 3.1 coordinate with them to avoid sending the same doctor twice? |

## 7. Answers and actions (to fill in during the meeting)

| Code | Answer / comment | Action | Owner |
| --- | --- | --- | --- |
| F-1 | | | |
| F-2 | | | |
| F-3 | | | |
| F-4 | | | |
| F-5 | | | |
| F-6 | | | |
| F-7 | | | |
| F-8 | | | |
| F-9 | | | |
| F-10 | | | |
| F-11 | | | |
| F-12 | | | |
| F-13 | | | |
| F-14 | | | |
| F-15 | | | |
| F-16 | | | |
| Other | | | |

## 8. Next steps

1. Update the proposals with your feedback and record answers in `20_field_activity_data_review_2024_2026.md` (section 9).
2. Build the fixes (PF-1 to PF-8) first, then the agreed new features.
3. Compare NBA 3.0 and 3.1 features on the same cycle and share the result with you before the model is retrained.

## Appendix: links between this note and the detailed review

| Briefing | Detailed review (`20_`) |
| --- | --- |
| 3.1 | Sections 1, 2.1 |
| 3.2 calls / BHO | Sections 2.2, 3, 6.1 – 6.4, 6.6 |
| 3.2 iRep / speaker | Sections 4, 5 |
| 3.3, 4.3 | Section 6.5 |
| 4.1, 4.2 | Section 7 |
| F-1, F-2 | Q-A1 (answered: permanent co-promotion, Asundexian to be added) |
| F-3 – F-7 | Q-A2 – Q-A6 |
| F-8 | Q-B2 |
| F-11 | Q-C1, Q-C2, Q-D1 – Q-D3 |
| F-15, F-16 | Q-B3 |
