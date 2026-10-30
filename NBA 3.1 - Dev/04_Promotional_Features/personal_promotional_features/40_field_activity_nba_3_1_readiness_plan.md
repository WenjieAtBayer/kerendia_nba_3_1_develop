# Field Activity: NBA 3.1 Readiness Plan

**Group:** Personal promotional features (rep calls, organisation calls, iRep emails, speaker programs)  
**Purpose:** a step-by-step plan to turn field activity into a clean, validated and tested feature block for NBA 3.1  
**Builds on:** `20_field_activity_data_review_2024_2026.md` (data review, PF-1 to PF-8, PN-1 to PN-11, Q-codes), `30_field_analytics_team_briefing_nba_3_1.md` (Field Analytics feedback, 29 Oct 2026, F-1 to F-16), `21_clickstream_clm_data_review_2024_2026.md` (CLM), legacy files `10_` to `14_`  
**NBA 3.1 notebooks concerned:** `04_Promotional_Features/25_promotional_features_call`, `14_promotional_features_speaker_program`, `16_promotional_features_irep`, `18_promotional_ClickStream_features`; BHO logic from NBA 3.0 `13_promotional_features_bho_calls`; coordination with `17_promotional_features_samples` (market access block)  
**Status:** draft for discussion  
**Date:** October 30, 2026

## 1. Scope

| In scope | Out of scope (owned elsewhere or pending) |
| --- | --- |
| **HCP interactions** (rep calls) from Veeva: interaction, product details, detail priority, key messages, materials, meal, rep | **Samples shipped / dropped** as a volume signal: market access block (`17_promotional_features_samples`, `ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER`). This plan only reconciles call-level samples against it (V5) |
| **Account / office engagement** (account-only, virtual office, staff / PA work) as its own signal | **MSL interaction detail** beyond a flag (counts by indication, topics, notes): not covered by the compliance confirmation |
| **Organisation (BHO) context**: activity on colleagues at the HCP's organisations, excluding the HCP | **HCP digital and HQ email**: digital block (`non_personal_promotional_features/13_hcp_digital_nba_3_1_readiness_plan.md`) |
| **iRep emails** (rep-sent; the digital plan moves iRep to this block) | **CLM / clickstream**: kept as a low-priority candidate only (under 1% of calls; 0 of 24 NBA 3.0 CLM features kept in the model; see `21_`) |
| **Speaker programs and other events**, with separate invited / registered / attended states | Changing Veeva, call rules or rep processes |
| **MSL interaction flag** (medical interaction with the HCP in the last N months; confirmed within compliance, 30 Oct 2026, F-8 / Q-B2) | |
| **Field adoption measurement** of NBA 3.1 (evaluation, not a model input) | |

## 2. Goal and how we will judge success

**Goal.** Replace the NBA 3.0 field block, which misses about 40 – 46% of Kerendia doctor calls since January 2026 and carries several empty or default-valued features, with a block that **counts every HCP interaction once**, keeps the signals Field Analytics actually uses (face-to-face activity, products detailed, product priority, meals, key messages), and is validated before any message- or sample-derived feature is relied on.

**Success criteria** (to agree with the modelling team):

| # | Criterion | How it is measured |
| --- | --- | --- |
| S1 | **Full coverage** of Kerendia HCP interactions | Interaction counts reconcile with the review: about 660K doctor calls and about 104K called doctors in Year 2 (Nov 2025 – Oct 2026), versus 413K / 84K seen by NBA 3.0 |
| S2 | **One count per interaction** | Each HCP interaction counted once regardless of how many products were detailed; BHO child records never counted as HCP activity; account / office records never counted as HCP interactions |
| S3 | **No double counting across blocks** | Samples: one volume source (market access block); iRep: this block only; CLM: one source |
| S4 | **Stable schema** | Same column list every run, generated from a config (products, interaction classes, event states, windows) |
| S5 | **Model value** | The new block improves the NBA 3.1 validation metric over the NBA 3.0 field block (E0 vs E2 to E5, section 7) |
| S6 | **Explainable to the field** | Every kept feature maps to a signal Field Analytics recognises; driver text in Veeva can be read by a rep or manager |
| S7 | **Adoption measured on field activity** | NBA 3.0 and 3.1 compared on downstream HCP interactions after the suggestion, with CRM status as secondary information |

## 3. Starting point (NBA 3.0)

| What NBA 3.0 does | Problem | Where it is explained |
| --- | --- | --- |
| Keeps calls where `UPPER(DETL_PROD) = 'KERENDIA'` | Misses all Kerendia + Lynkuet (and Adempas, ...) calls: 40 – 46% of calls each month since Feb 2026; about 20,000 called doctors look "never called" | `20_`, 2.1; `30_`, 3.1 |
| Treats the product text as the call | A call is the HCP interaction; products are details within it, with a priority (F-1) | `30_`, 3.1 and section 4 |
| Gives every BHO call to every doctor of the organisation | 494K of about 502K BHO calls (12 months) are child copies of a doctor call; the signal is repeated and spread to about 80 colleagues each, including the doctor | `20_`, 3 |
| Counts account-only / virtual-office records as doctor calls | About 10 – 12% of calls have no HCP present | `20_`, 6.3 |
| Call length features | `30` on 97% of calls since 28 Jul 2025 | `20_`, 2.2 |
| Phone and `Group Detail` features | Phone always 0; `Group Detail` on 77 – 81% of calls, not used by Field Analytics (F-4) | `20_`, 2.2 |
| Samples only as "call type with sample" | No quantity or strength; call-level samples not reconciled with shipped / dropped data (F-10) | `20_`, 6.4 |
| iRep delivered = `'Delivered'` | Status is `Delivered_vod`: feature always 0 | `20_`, 4 |
| iRep template groups | 0.4% of last-12-month emails fall in an NBA 3.0 group | `20_`, 4 |
| Speaker attendance = `ATND = 'Attended'`, all event types together | About 8,000 `Signed_vod` registrations a year without attendance value; registration is not attendance (22 registered / 12 attended example); speaker programs mixed with scientific presentations and round tables; current topics not in the topic lists | `20_`, 5 |
| Only 90-day and 1-year totals | No recency, regularity, rep coverage, indication or message information | `20_`, 7 |

## 4. Design principles for NBA 3.1

1. **Interaction first.** The base grain is one **HCP interaction** (one submitted Veeva call on a doctor). Product details and their priority hang below it; nothing is weighted by product.
2. **Kerendia = Kerendia is one of the details.** An interaction is a Kerendia interaction if any of its details is Kerendia (`FACT_CALL_DETAIL`), whatever the other brands (Lynkuet now, Asundexian later). No text matching on `DETL_PROD` combinations.
3. **Classify every record once.** Each call record gets exactly one class: `HCP_INTERACTION`, `ACCOUNT_OFFICE` (no HCP present), `BHO_CHILD` (organisation copy of a doctor call), `BHO_TOP_LEVEL` (organisation call without a parent), `MEDICAL` (MSL). Only `HCP_INTERACTION` feeds the core counts.
4. **Field-recognised signals first.** Build first what Field Analytics uses (face-to-face interactions, products detailed, priority, meals, key messages); drop what they do not use and what carries no information (call length, phone, `Group Detail`).
5. **Validate before relying.** Key-message and sample-derived features are built only after their validation step passes (V4, V5). Until then they are candidates, not inputs.
6. **One source per activity.** Samples are built once from `FACT_CALL_SAMPLE` with an explicit status map (V5 showed the market access table is a filtered copy of it); the market access block either uses the same corrected logic or reads the same output. iRep only here.
7. **Event states kept apart.** Invited, registered and attended are separate states; confirmed attendance is the primary event signal.
8. **Windows aligned to the anchor.** Same lookback logic as the rest of the pipeline (`promotional_cohort_inference_dates`); windows of 1, 3, 6 and 12 months ending at the lookback end; plus recency in days.
9. **Short history handled explicitly.** Indication key messages exist from July 2025 and co-detail from January 2026. Features that depend on them get a data-available flag, and experiment E6 tests training on recent instances only.
10. **Fixed schema.** Output columns generated from a config of classes, products, states and windows; missing combinations filled with 0.
11. **Language.** In documents and Veeva text, use "NBA suggestion" / "NBA list", not "alert" (technical names such as `Kerendia NBA ML Alert` stay as they are).

## 5. Target data model

```
HCP interaction (one row per call on a doctor, class = HCP_INTERACTION)
  |-- product detail(s)  (one row per product: Kerendia, Lynkuet, Asundexian, ...; priority 1, 2, ...; paper / e-detail)
  |-- key messages       (indication and position codes; materials shown)
  |-- attributes         (record type, meal, sample flag, rep, territory, date)

Outside the HCP-interaction level:
  account / office records (class = ACCOUNT_OFFICE)  -> account / office engagement features
  BHO child / top-level records                       -> organisation context features (focal HCP excluded)
  speaker events (one row per HCP x event x state)   -> event features (attended primary)
  iRep emails (one row per email, events)            -> iRep features
  medical records (class = MEDICAL)                   -> MSL interaction flag only
  NBA suggestions (DIM_SUGGESTION)                    -> adoption measurement only
```

| Intermediate table (proposal) | Grain | Main sources | Key columns |
| --- | --- | --- | --- |
| `field_interaction` | Call record | `FACT_CALL`, `MAP_CUSTOMER_XREF`, `FACT_CALL_KEY_MESSAGE` | `CALL_ID`, `BHID`, `CALL_DATE`, `SOURCE_EMP_ID`, `TERR_ID`, record type, meal flag, sample flag, `RECORD_CLASS`, `HAS_KERENDIA_DETAIL`, `PAR_CALL_ID` |
| `field_interaction_detail` | Call x product | `FACT_CALL_DETAIL` | `CALL_ID`, product, `CALL_DETL_PRTY`, `CALL_DETL_TYP` |
| `field_interaction_message` | Call x key message | `FACT_CALL_KEY_MESSAGE` | `CALL_ID`, message code, indication (CKD / HF / LYN), position, material group |
| `field_record_class_rules` | Config | Hand-maintained | Message / record-type patterns to `RECORD_CLASS`; material name patterns to material group |
| `field_event_state` | HCP x event | `ANLT_BASE_FACT_EVNT_PRSNL_PROM`, `FACT_EVENT_ATTENDEE`, `FACT_EVENT_SPEAKER` | `BHID`, event ID, event type, topic group, format, state (invited / registered / attended), speaker flag |
| `field_irep_email` | Email | `FACT_SENT_EMAIL`, `DIM_APPROVED_DOCUMENT`, `FACT_EMAIL_ACTIVITY` | `BHID`, template group, delivered / opened / clicked, link group |

The intermediate tables are built once per run and feed all feature notebooks, so every feature uses the same Kerendia rule and the same record classes.

## 6. Work plan

The work is split into phases. Each phase ends with a gate (section 8).

### Phase 0: Foundations and validation (blocking)

| ID | Task | Detail | Depends on / owner |
| --- | --- | --- | --- |
| V1 | Interaction grain | Build `field_interaction` and `field_interaction_detail`; Kerendia rule from detail rows. Reconcile with the review: Year 2 about 660K doctor calls and about 104K doctors; Kerendia in position 1 on 87 – 92% of 2026 interactions | NBA team |
| V2 | Record classification | Rules for `ACCOUNT_OFFICE` (`5- Acct Call`, `vOffice call (no HCP)`; before July 2025 `2-Account Call Only`), `BHO_CHILD` / `BHO_TOP_LEVEL` (`PAR_CALL_ID`, `PAR_CALL_FLAG`, `BHO` IDs), `MEDICAL` (`Finerenone [...]`, medical record types). Report the share per class per month | NBA team |
| V3 | BHO parent / child logic | Confirm with the CRM team which BHO records are automatic copies and when a rep logs a real organisation call (F-3 / Q-A2 still open) | CRM team |
| V4 | Key-message entry consistency | Measure per month, rep and territory: share of Kerendia interactions with an indication / position code, share with a material, unusual patterns (a rep always entering the same code). Review the reporting process with Maria Kontorinakis (F-5 / Q-A6) | NBA team, Maria Kontorinakis |
| V5 | Sample reconciliation | **Done 30 Oct 2026, see `22_samples_reconciliation_call_vs_shipped_dropped_2024_2026.md`.** The market access table is a status-filtered copy of `FACT_CALL_SAMPLE` (100% line match) but misses the post-Vault status `aoc_received__c` and counts in-transit `Shipped_vod` as received: it holds 87% of received units in Year 1 and only 13% in Year 2. Business rule (aligned with MV): received = `Delivered` + `AOC Received` only. Orders settle in two to three weeks; no delivery date, so training must mimic the unsettled last weeks at inference (R7). Strength is reliable; 40 mg (since Aug 2025, about 1,000 doctors a quarter) is HF-related | NBA team, market access block owner |
| V6 | Event states | Map Veeva statuses to invited / registered / attended; confirm what `Signed_vod` without `ATND` means for a closed event (Q-D1); split speaker programs from scientific presentations / round tables / medical events (Q-D2) | Events team |
| V7 | iRep data checks | Delivered status fix (`STAT ILIKE 'Delivered%'`); check the April 2026 open-rate drop (tracking change?) before using opens (Q-C1) | NBA team, CRM email team |
| V8 | Asundexian readiness | When ISS reps start co-promoting, check that Asundexian appears as a separate detail row and that the Kerendia rule still holds (F-2) | NBA team, sales operations |
| V9 | Fixed schema and config | `field_record_class_rules`, product list, event states, window list; two runs produce identical columns | NBA team |
| V10 | MSL records | Identify `MEDICAL` records (product text `Finerenone [...]`; record types `Face2Face Interaction Med`, `BPH_MED_*`, `Remote Interaction Med`, `Event Call Report`); check volume against the review (about 10,500 – 10,900 interactions a year with about 6,400 – 6,800 doctors) and that none is counted as an `HCP_INTERACTION` | NBA team |

### Phase 1: Core interaction features (high confidence)

Built from `field_interaction` (class `HCP_INTERACTION`, Kerendia detail) and `field_interaction_detail`. Windows: 1, 3, 6 and 12 months. Names are illustrative.

| ID | Feature family | Example names | Approx. count | Origin |
| --- | --- | --- | --- | --- |
| C1 | HCP interactions by record type | `FLD_INT_F2F_3M`, `FLD_INT_REMOTE_6M`, `FLD_INT_GROUP_6M`, `FLD_INT_TOTAL_12M` | 12 – 16 | PF-1 (replaces NBA 3.0 call counts) |
| C2 | Meal | `FLD_INT_MEAL_3M`, `FLD_INT_MEAL_SHARE_12M` | 4 – 6 | PF-4 (kept) |
| C3 | Product detail and priority | `FLD_INT_KER_ONLY_6M`, `FLD_INT_KER_CODETAIL_6M`, `FLD_INT_KER_PRIMARY_6M`, `FLD_KER_PRIMARY_SHARE_6M` | 8 – 12 | PN-2 (revised) |
| C4 | Recency and regularity | `FLD_DAYS_SINCE_LAST_INT`, `FLD_N_ACTIVE_MONTHS_6M`, `FLD_MEDIAN_GAP_DAYS_12M` | 3 – 5 | PN-3 |
| C5 | Rep coverage and continuity | `FLD_N_REPS_6M`, `FLD_REP_CHANGE_6M`, `FLD_MAIN_REP_SHARE_12M` | 3 – 4 | PN-5 |
| C6 | Account / office engagement | `FLD_ACCT_OFFICE_3M`, `FLD_ACCT_OFFICE_12M`, `FLD_DAYS_SINCE_LAST_ACCT_OFFICE` | 4 – 6 | PN-6 (revised; separate from C1) |
| C7 | Organisation context (focal HCP excluded) | `FLD_ORG_COLLEAGUE_INT_3M`, `FLD_ORG_N_COLLEAGUES_CALLED_6M`, `FLD_ORG_TOP_LEVEL_CALLS_6M` | 4 – 6 | PF-2 (top-level calls only after V3) |
| C8 | Trend | `FLD_INT_3M_VS_PRIOR_3M` | 1 – 2 | New |

**Dropped:** call length (PF-3), phone, `Group Detail` call type and rare purpose / type features (PF-4).

Candidate set: about 40 to 60 columns.

### Phase 2: Message-derived features (only if V4 passes)

| ID | Feature family | Example names | Condition |
| --- | --- | --- | --- |
| M1 | Indication of the main message | `FLD_INT_CKD_FIRST_3M`, `FLD_INT_HF_FIRST_3M`, `FLD_HF_SHARE_6M` | V4: indication code present on a stable, high share of interactions across territories (PN-1) |
| M2 | Materials shown | `FLD_MAT_ACCESS_PA_6M`, `FLD_MAT_PATIENT_PROFILE_6M`, `FLD_MAT_LEAVE_BEHIND_6M` | V4, plus a material grouping aligned with the digital content groups (PN-7) |
| M3 | Data-available flag | `FLD_KEYMSG_AVAILABLE` | Needed for instances before July 2025 |

If V4 shows uneven entry, keep only the indication split at a coarse level (any CKD vs any HF in 6 months) or drop the family.

### Phase 3: Events and iRep

| ID | Feature family | Example names | Origin |
| --- | --- | --- | --- |
| E-1 | Confirmed attendance | `SPKR_ATTENDED_6M`, `SPKR_ATTENDED_12M`, `SPKR_DAYS_SINCE_ATTENDED` | PF-8 (revised) |
| E-2 | Registration and invitation (separate states) | `SPKR_REGISTERED_NOT_ATTENDED_12M`, `SPKR_INVITED_12M` | PF-8, PN-10 |
| E-3 | Event type and topic | `SPKR_ATTENDED_HF_12M`, `SPKR_ATTENDED_CKD_CV_12M`, `SCI_EVENT_ATTENDED_12M` | PF-7, PF-8 (topic groups after Q-D3) |
| E-4 | Kerendia speaker | `SPKR_IS_KERENDIA_SPEAKER` | PN-10 |
| I-1 | iRep delivered / clicked | `IREP_DELIVERED_3M`, `IREP_CLICKED_6M` | PF-5 |
| I-2 | iRep template groups | `IREP_HF_CONTENT_6M`, `IREP_ACCESS_PA_6M`, `IREP_EHR_6M`, `IREP_INVITE_6M` | PF-6 (grouping after F-11 / Q-C2) |
| I-3 | iRep opens | `IREP_OPENED_3M` | Only after V7 explains the April 2026 drop |
| I-4 | iRep link group clicked | `IREP_CLICK_ACCESS_6M` | PN-11 (small volumes) |
| MD-1 | MSL interaction flag | `FLD_MSL_INTERACTION_6M`, `FLD_MSL_INTERACTION_12M` (1 if any medical interaction with the HCP in the window, else 0) | PN-9 (confirmed within compliance, 30 Oct 2026). Flag only; not part of Field Analytics reporting, so it is kept out of rep-facing driver text unless agreed |

### Phase 4: Conditional and deprioritised candidates

| ID | Candidate | Condition | Origin |
| --- | --- | --- | --- |
| X1 | Samples (one block, shared with market access): received units and sample-call counts (received = `Delivered` + `AOC Received`; `Shipped` excluded), 40 mg flag (6 / 12 months, data-available flag), no 10 vs 20 mg split; settling rule for the last 21 days (R7 in `22_`) | V5 done; agree with the market access block owner where the block lives | PN-4 (revised after V5) |
| X2 | E-detail share | After F-6 / Q-A4 explains `EDetail_vod` (about 14% of details) | PN-8 |
| X3 | Richer MSL features (counts, indication of the medical interaction, recency in days) | Only if MD-1 adds value (E4) **and** compliance confirms that more than a flag is allowed | PN-9 |
| X4 | CLM presentation time | Only if CLM use grows; under 1% of calls today | `21_` |

### Phase 5: Field adoption measurement (not a model input)

| ID | Task | Detail |
| --- | --- | --- |
| A1 | Primary measure | Share of NBA suggestions followed by an `HCP_INTERACTION` with the suggested doctor during the suggestion window (by the aligned rep, and by any rep). Built from `DIM_SUGGESTION` (distinct `SGTN_ID`, rows are duplicated about 8 times) joined to `field_interaction` |
| A2 | Secondary measures | Actioned, dismissed (with reason, `FACT_SUGGESTION_FEEDBACK.DISMISS_FDBK1-4`), marked complete; linked call (`FACT_SUGGESTION_FEEDBACK.CALL_ID`) |
| A3 | Baseline | Compute A1 and A2 by NBA cycle for NBA 3.0 (2025 – 2026); note the list cut from May 2026 (about 16,000 to about 8,500 doctors in Veeva) |
| A4 | Comparison design | Same metric for NBA 3.1 after release; compare with a matched group of non-suggested doctors with similar scores to separate the NBA effect from normal call activity |
| A5 | Coordination | Agree with the owner of `Weekly New Writer` how to avoid sending the same doctor twice (F-16) |

## 7. Model experiments

All experiments use the NBA 3.1 HCP-level model, target and validation split; only the field block changes. All other blocks stay fixed.

| Exp. | Field block | Question answered |
| --- | --- | --- |
| E0 | NBA 3.0 field block as is | Baseline |
| E1 | E0 with the interaction grain only (PF-1: all Kerendia interactions, counted once) | How much does fixing the co-detail gap change results? |
| E2 | Phase 1 core block (C1 – C8), NBA 3.0 events and iRep with PF-5 fix | Does a clean, field-recognised core beat the baseline? |
| E3 | E2 + message-derived features (M1 – M3) | Do key messages add value? (only if V4 passes) |
| E4 | E3 (or E2) + rebuilt events, iRep and the MSL flag (Phase 3) | Do attendance states, rebuilt topic / template groups and the MSL flag add value? (MSL flag also tested on its own: E4 with vs without MD-1) |
| E5 | E4 + conditional candidates (X1, X2) that passed their condition | Do call-level samples or e-detail add anything? |
| E6 | Best of E2 – E5, trained on instances from January 2026 only | Does the co-detail period change what works? |

**Measures for each experiment:** validation metric of the NBA 3.1 model, SHAP share of the field block, rank of the best field feature, number of field features kept after selection, and stability of importance across time folds. Also check that the top field drivers read sensibly to Field Analytics (S6).

## 8. Readiness gates

| Gate | Ready when |
| --- | --- |
| G0 (after Phase 0) | V1 reconciles with the review figures; record classes reported by month; fixed schema produced twice with identical columns; V3 – V7 outcomes recorded (pass / fail / open); E1 run |
| G1 (after Phase 1) | Core block built for all training instances; leakage check passed (no activity after the lookback end); account / office and BHO records excluded from core counts; E2 run and compared with E0 |
| G2 (after Phases 2 – 3) | V4 decision taken (keep / coarse / drop message features); event states agreed with the events team; iRep template groups agreed; V10 done and MSL flag built; E3 and E4 run |
| G3 (before NBA 3.1 freeze) | Final field block chosen; documented in this folder with the same structure as files `10_` to `14_`; adoption baseline (A1 – A3) computed for NBA 3.0; reviewed with Field Analytics |

## 9. Decisions and open questions

| # | Question | Proposed answer / status | Owner |
| --- | --- | --- | --- |
| D1 | How to count a co-detail call | Decided: one HCP interaction; product details and priority as separate features, no weighting (F-1) | NBA team, Field Analytics |
| D2 | Account / office records | Decided: separate engagement feature; not HCP interactions, not discarded | NBA team, Field Analytics |
| D3 | BHO records | Decided direction: organisation context excluding the focal HCP; real organisation calls after V3 | NBA team; CRM team for V3 |
| D4 | Call length, phone, `Group Detail` | Decided: drop | NBA team |
| D5 | Speaker attendance | Decided: confirmed attendance is primary; states kept separate; meaning of `Signed_vod` to confirm (Q-D1) | Events team |
| D6 | Rep response as model input | Decided: no; evaluation only, with downstream field activity as the primary measure | NBA team |
| D7 | MSL interactions | Decided: an MSL interaction flag is within compliance (30 Oct 2026); built as MD-1. Anything beyond a flag needs a separate confirmation (X3) | NBA team; compliance / medical affairs |
| Q1 | Are key messages entered consistently? | Open: V4, follow-up with Maria Kontorinakis | NBA team, Maria Kontorinakis |
| Q2 | Are call-level samples consistent with dropped samples? | Answered by V5 (`22_`): same records; the market access table drops `aoc_received__c` (87% of Year 2 received units) and includes in-transit `Shipped_vod`. Received = `Delivered` + `AOC Received` (business rule aligned with MV). Open: fix the table or notebook 17 (Q-S2); delivery date or status snapshots (Q-S5) | NBA team, market access block owner, samples / CRM team |
| Q3 | What is `EDetail_vod`? | Open (F-6 / Q-A4) | CRM / CLM team |
| Q5 | Asundexian timing and recording | Open (F-2); ISS reps will co-promote, separate field force too | Sales operations |
| Q6 | Official iRep template and speaker topic groups; reason for the April 2026 open drop | Open (F-11 / Q-C1 / Q-C2 / Q-D3) | Brand team, CRM email team |
| Q7 | Why rep response fell to about 19% in Q3 2026 | Open (F-12 – F-14) | Field Analytics |
| Q8 | Why 5 – 10% of NBA doctors never appear as Veeva suggestions; owner of `Weekly New Writer` | Open (F-15 / F-16 / Q-B3) | Data team / CRM team |

## 10. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Co-detail history is short (from Jan 2026) | Product-detail features are 0 or uninformative for older training instances | Data-available flags; E6 tests recent-only training |
| Key messages entered unevenly | Message features reflect rep habits rather than doctor behaviour | V4 before use; coarse fallback; per-territory check of importance |
| Account / office classification depends on key-message codes | Misclassified records move between C1 and C6 | Report class shares monthly; keep classification rules in a config |
| BHO logic misunderstood | Organisation context still duplicates the HCP's own calls | Exclude the focal HCP by construction; use top-level BHO calls only after V3 |
| Asundexian changes the detail structure | Kerendia rule or priority features break | V8 check at launch; detail-based rule instead of text |
| Samples counted twice (call block and market access block) | Inflated importance, confused drivers | One samples block built once from `FACT_CALL_SAMPLE` (V5) |
| Sample status mapping wrong or changing | Sample features collapse again (as in NBA 3.0 since Aug 2025) | Status map in config; monthly report of units by status; recheck the Oct 2026 shift in December |
| Field reorganisations (July 2025 expansion with strikers, 2026 growth to about 650 – 690 reps) | Rep-coverage features shift with headcount, not doctor behaviour | Use shares and changes relative to territory; check stability across time folds |
| NBA list size changes | Adoption trends reflect list size rather than rep behaviour | Compare rates, not volumes; report per NBA cycle |
| MSL flag used beyond its confirmed scope | Compliance issue; medical activity shown to reps as a commercial driver | Flag only (MD-1); keep it out of rep-facing driver text unless agreed; any extension through X3 with a new confirmation |

## 11. References

* `20_field_activity_data_review_2024_2026.md`: data review, sections 2 – 7, open questions (section 8), answers (section 9)
* `30_field_analytics_team_briefing_nba_3_1.md`: Field Analytics feedback (sections 3 – 4, 4.4) and answers (section 7)
* `21_clickstream_clm_data_review_2024_2026.md`: CLM / iVA
* `22_samples_reconciliation_call_vs_shipped_dropped_2024_2026.md`: V5 samples reconciliation
* `../market_access_promotional_features/samples.md`: samples shipped / dropped (NBA 3.0)
* `../non_personal_promotional_features/13_hcp_digital_nba_3_1_readiness_plan.md`: HCP digital plan (iRep moved to this block)
* Snowflake tables: `CPH_DB_PROD.MODEL_V2.FACT_CALL`, `FACT_CALL_DETAIL`, `FACT_CALL_KEY_MESSAGE`, `FACT_CALL_SAMPLE`, `MAP_CUSTOMER_XREF`, `DIM_SUGGESTION`, `FACT_SUGGESTION_FEEDBACK`, `FACT_SENT_EMAIL`, `FACT_EMAIL_ACTIVITY`, `DIM_APPROVED_DOCUMENT`, `FACT_EVENT_SPEAKER`, `FACT_EVENT_ATTENDEE`; `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM`, `ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER`
