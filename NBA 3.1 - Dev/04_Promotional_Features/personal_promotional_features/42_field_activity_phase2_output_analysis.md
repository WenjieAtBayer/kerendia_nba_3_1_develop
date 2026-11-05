# Field Activity Phase 2: Output Analysis (NBA 3.1)

**Notebook:** `42_field_activity_phase2_message_features`  
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 2: M1 – M3, condition V4; design principles 5 and 9; risk "key messages entered unevenly")  
**Run analysed:** 4 Nov 2026, serverless  
**Date:** 4 Nov 2026

**How to read this file.** Section 1 is the summary. Section 2 gives the background for a first-time reader. Section 3 explains what the notebook does. Section 4 goes through every expectation: why we expected it (from NBA 3.0), whether it is new, what we got, and what to raise with the client. Sections 5 – 8 list the gate, issues, client questions and next actions.

---

## 1. Summary

| ID | Expectation (readiness plan) | NBA 3.0 or new | Status | One-line result |
| --- | --- | --- | --- | --- |
| R0 | Same Kerendia HCP interactions as Phase 1 | — | **Met** | Year 1 472,236 / 77,308 doctors; Year 2 606,239 / 96,610; exact match with notebook 41 |
| V4-a | Indication code on a high share of interactions every month | New | **Met (T1 PASS)** | 92.7 – 97.2% each month in 2026; 0% before Jul 2025 |
| V4-b | High share across territories | New (action A4) | **Met (T2 PASS)** | 94.9% of 746 territories at or above 70%; 26 territories below 50% hold 3.6% of interactions |
| V4-c | No reps always entering the same code | New | **Not met as stated (T3 FAIL)** | 24.8% of reps always put CKD first, concentrated in teams CR4 (60%) and CR1 (33%); likely team specialty |
| M1 | Indication of the main message | New | **Coarse only, not built** | HF share of first message about 30% in 2026; needs T3 answer and 2026 cohorts |
| M2 | Materials shown | New | **Drop for now** | 71 material names, but recorded on only 13 – 15% of interactions; no grouping (PN-7) yet |
| M3 | Data-available flag | New (principle 9) | **Needed with M1, not built** | Codes exist only from Jul 2025 |
| Coverage | Training cohorts contain indication codes | — | **Blocker** | 0 of 26 cohorts (last ends 2025-04-16) |

**Bottom line.** Reps do enter indication codes, consistently and across almost all territories, since August 2025. But (1) a quarter of reps always put the same indication first, which looks like team specialty rather than a doctor-level signal, and (2) no training cohort contains any code. M1 – M3 are therefore **not built**. Decision: **coarse M1 + M3 only, after the cohorts are extended and the client explains the always-CKD teams; M2 dropped for now.**

---

## 2. Background for a new reader

1. **What a key message is.** When a rep logs a Kerendia call in Veeva, he also records which message he delivered, as a code. Since July 2025 the codes include the indication and position, for example `1-Position 1 KER CKD (HCP call)` (CKD message first) or `3- Position 1 KER HF (HCP call)` (heart failure message first). Reps can also record the material they showed (visual aid, brochure).
2. **Why it matters.** Kerendia has two indications: chronic kidney disease (CKD, with type 2 diabetes) and heart failure (HF, approved 2025). Which message a doctor hears first tells the model whether the field treats him as a CKD or an HF prescriber.
3. **What NBA 3.0 did.** NBA 3.0 used no key-message information at all: only call counts by type and purpose (plan section 3: "no recency, regularity, rep coverage, indication or message information").
4. **Why there is a gate.** Key messages are typed by reps. If reps enter them unevenly (some always, some never, some always the same code), a feature built on them describes the rep, not the doctor. The plan therefore says: build message features **only if V4 passes** (principle 5).
5. **What Phase 2 is.** The second feature block: M1 (indication of the main message), M2 (materials) and M3 (a flag that says whether codes can exist for that period).

---

## 3. How the notebook works

| Step | Cell | What it does |
| --- | --- | --- |
| 1 – 2 | 4 | Loads Kerendia HCP interactions Nov 2024 – Oct 2026 with key-message flags, using the notebook 41 rules written in Snowflake SQL (not BHO, not medical, no account / office message); reconciles with notebook 41 |
| 3 | 5 | Monthly share with any message, indication code, indication in position 1, CKD / HF first, HF share of first message, dual indication, material |
| 4 | 6 | Territory and rep consistency (Jan – Oct 2026, at least 50 interactions), lowest territories, month-by-month stability |
| 5 | 7 | Material names on Kerendia calls in 2026 |
| 6 | 8 | Do training cohorts contain indication codes? |
| 7 | 9 | Gate metrics for the proposed thresholds; reps with a single first-message pattern by team |
| Decision | 10 | Gate table and decision |

Fix during the run: in Step 3, the HF share of the first message divided by zero for months before July 2025 (no position-1 codes); replaced by `try_divide` (empty value for those months).

---

## 4. Expectation by expectation

### R0 — Same base as Phase 1

* **Why we expect this.** Message features must describe the same interactions as the Phase 1 counts, otherwise shares and counts disagree.
* **NBA 3.0 or new.** New check.
* **What we got.** Year 1 472,236 calls / 77,308 doctors; Year 2 606,239 / 96,610. Identical to notebook 41 and Phase 0 V2.
* **Status.** Met.

### V4-a — Monthly entry share

* **Why we expect this.** The plan risk table says "key messages entered unevenly: message features reflect rep habits rather than doctor behaviour". The first test is whether codes are entered on most calls every month.
* **NBA 3.0 or new.** New (NBA 3.0 used no messages).
* **What we got.**

| Period | Indication code | Indication in position 1 | HF share of first message | Dual indication | Material |
| --- | --- | --- | --- | --- | --- |
| Nov 2024 – Jun 2025 | 0.0 – 0.3% | 0 – 0.2% | — | 0% | 13.5 – 17.0% |
| Jul 2025 | 52.2% | 32.5% | 27.1% | 9.5% | 21.5% |
| Aug – Dec 2025 | 88.3 – 89.4% | 84.3 – 86.5% | 40.1% → 31.1% | 8.3 – 10.4% | 15.4 – 17.2% |
| Jan – Oct 2026 | 92.7 – 97.2% | 80.5 – 85.2% | 29.6 – 34.7% | 5.2 – 6.5% | 12.7 – 15.0% |

  Some message is entered on almost 100% of calls throughout; the indication codes start in July 2025. Phase 0 V4 showed 77 – 80% and 86 – 88%; the difference is consistent with Phase 0 including account / office records (10 – 14% of doctor records, which carry account codes, not indication codes). The position-1 share drops from 86.5% to 80.5% in January 2026, when Lynkuet co-detail starts (Lynkuet takes position 1 on part of the calls).
* **Status.** Met (T1: lowest month 92.7% against a proposed 80%).
* **Raise with client.** Confirm the threshold. Confirm with Maria Kontorinakis that the codes became mandatory in July / August 2025 (Phase 0 C5).

### V4-b — Consistency across territories (action A4)

* **Why we expect this.** A high national share can hide territories that never enter codes; for those doctors a message feature would always be 0 for a reason unrelated to the doctor.
* **NBA 3.0 or new.** New.
* **What we got.** 746 territories and 733 reps with at least 50 interactions in 2026; every interaction has a territory and a rep. Territory share P10 93.6%, median 100%. 94.9% of territories at or above 70%. Stricter version (at least 70% in every single month): 89.9%. 26 territories below 50% hold 19,445 of 533,256 interactions (3.6%); three enter no indication code at all (`US_PH_CR1_033A` 1,256 interactions, `US_PH_CR1_328A` 1,203, `US_PH_CR5_608B` 133).
* **Status.** Met (T2 PASS; borderline on the strict monthly version).
* **Raise with client (Maria Kontorinakis).** Why do these 26 territories, three of them at 0%, not enter indication codes? Reason: their doctors would look "no message" in M1.
* **Suggestions.** Treat territories below 50% as "not available" in M3 rather than as 0.

### V4-c — No reps always entering the same code

* **Why we expect this.** The plan asks for "unusual patterns (a rep always entering the same code)". If a rep always records CKD first, the feature tells the model who the rep is, not what the doctor needs.
* **NBA 3.0 or new.** New.
* **What we got.** Reps with at least 20 position-1 codes in 2026:

| Pattern | Reps | Share | Interactions |
| --- | --- | --- | --- |
| Mixed (CKD and HF first) | 535 | 72.8% | 368,405 |
| Always CKD first | 182 | 24.8% | 119,148 |
| Always HF first | 18 | 2.4% | 6,418 |

| Team (territory prefix) | Reps | Always CKD first | Always HF first |
| --- | --- | --- | --- |
| CR1 | 337 | 111 (33%) | 0 |
| CR2 | 205 | 3 | 7 |
| CR4 | 111 | 67 (60%) | 0 |
| CR5 | 62 | 1 | 2 |
| CAR | 20 | 0 | 9 (45%) |

  The single-code reps cluster by team, which suggests that teams are aligned to a specialty (CKD-focused teams calling on nephrologists / PCPs, the CAR team on cardiologists). In that case the code reflects the doctor's specialty correctly, but it adds little beyond specialty and the team.
* **Status.** Not met as stated (T3 FAIL). Probably explained by team specialty; not confirmed.
* **Raise with client (Field Analytics, Maria Kontorinakis).** (1) What do teams CR1, CR2, CR4, CR5 and CAR cover, and are CR4 / CR1 reps expected to deliver only the CKD message? (2) Are HF messages allowed for these reps? Reason: if the pattern is by design, M1 mostly repeats specialty and team; if not, it reflects entry habits.
* **Suggestions.** Build M1 at doctor level across all reps who call on him; compare M1 against doctor specialty before using it; check importance per team (plan risk mitigation "per-territory check of importance").

### M1 — Indication of the main message

* **Why we expect this.** Field Analytics wants to know whether a doctor is approached as a CKD or an HF prescriber (PN-1); HF is the new indication and its share of first messages fell from about 40% (Aug 2025) to about 30% (2026).
* **NBA 3.0 or new.** New.
* **What we got.** The inputs exist and are clean (one flag per call for CKD first, HF first, dual). No feature built.
* **Status.** Coarse only, not built.
* **Raise with client.** V4-c questions; modelling team: cohort extension.
* **Suggestions.** Coarse version: `FLD_CKD_FIRST_SHARE_6M`, `FLD_HF_FIRST_SHARE_6M` at doctor level, plus a dual-indication share; no monthly counts.

### M2 — Materials shown

* **Why we expect this.** Materials (visual aid, patient profile, access brochure) show what the rep discussed; the plan asks for a grouping aligned with digital content groups (PN-7).
* **NBA 3.0 or new.** New.
* **What we got.** 71 material names on Kerendia calls in 2026. Top: `KER CKD/HF Digital MVA Refresh Dual Indication` 54,227 calls, `KER HF Digital MVA Refresh Cardiologist` 23,077, `LYNKUET DIGITAL MASTER VISUAL AID` 21,376, `26 ACC HFpEF ECDP Leave Behind` 11,121, `BACC Kerendia - Standalone - Vault` 10,324, `Tipping Point Brochure` 6,480, `Lynkuet TV Commercial` 6,279, `Cardiology Patient Profile - Armand` 4,245, `Neph CKD Patient Profile` 1,617. But only 13 – 15% of interactions have a material. Lynkuet and Adempas materials appear on Kerendia calls through co-detail.
* **Status.** Drop for now.
* **Raise with client (brand / digital team).** Official material grouping (PN-7) and whether material entry is expected on every call. Reason: with 85% of calls empty, a material feature mostly measures whether the rep uses the digital aid.
* **Suggestions.** Keep only a coarse "digital visual aid used" flag as a candidate; revisit after PN-7.

### M3 — Data-available flag

* **Why we expect this.** Principle 9: features that depend on codes from July 2025 need a flag so the model does not read "no code" as "no message".
* **NBA 3.0 or new.** New.
* **What we got.** Codes start July 2025 (52% that month, 88% from August). Not built.
* **Status.** Needed together with M1.
* **Suggestions.** Flag = 1 when the cohort lookback starts on or after 1 Aug 2025 (full coverage), and 0 for territories with share below 50%.

### Coverage — Training cohorts

* **Why we expect this.** A feature can only be learned if training rows contain it.
* **What we got.** 26 cohorts, first ends 2023-03-17, last 2025-04-16; 0 cohorts end after July 2025.
* **Status.** Blocker: M1 – M3 would be 0 for every training row.
* **Raise with client (modelling team).** Extend cohort anchors past July 2025, ideally past January 2026 (also needed for co-detail, Phase 1 C3, and experiment E6).

---

## 5. Gate (V4 / G2 part)

Thresholds are **proposals** to agree with the client.

| # | Proposed threshold | Result | Status |
| --- | --- | --- | --- |
| T1 | Monthly indication share >= 80% in every month since Jan 2026 | Lowest 92.7% | PASS |
| T2 | >= 90% of territories (>= 50 interactions) with share >= 70% | 94.9% (strict monthly: 89.9%) | PASS (borderline strict) |
| T3 | No large group of reps always entering the same code | 24.8% always CKD first | FAIL as stated, pending explanation |
| Coverage | At least one training cohort with codes | 0 of 26 | Blocker |

**Decision:** coarse M1 + M3 only, after cohort extension and the T3 answer; M2 dropped for now; no columns built. G2 also requires the V4 decision to be taken (keep / coarse / drop); the proposal is "coarse".

---

## 6. Issues found

| # | Issue | Effect | Fix |
| --- | --- | --- | --- |
| P1 | No training cohort contains indication codes | M1 – M3 carry no training signal | Extend cohorts past Jul 2025 / Jan 2026 |
| P2 | 24.8% of reps always put CKD first, by team | M1 may repeat team / specialty | Client explanation; compare with specialty |
| P3 | 26 territories below 50% indication share, three at 0% | Doctors there look "no message" | Client follow-up; M3 = 0 for them |
| P4 | Material on only 13 – 15% of interactions, no grouping | M2 not usable | Wait for PN-7 |
| P5 | Phase 0 V4 shares were lower (account / office in the denominator) | Two numbers in circulation | Quote HCP-interaction shares from now on |
| P6 | Step 3 divided by zero before Jul 2025 | Cell failed | Fixed with `try_divide` |

---

## 7. Questions to send to the client

| # | Question | Team | Blocks |
| --- | --- | --- | --- |
| K1 | Agree the V4 thresholds T1 – T3 | Field Analytics, modelling team | Gate |
| K2 | What do teams CR1, CR2, CR4, CR5 and CAR cover? Are CR4 / CR1 reps expected to give only the CKD message? | Field Analytics | T3, M1 |
| K3 | Why do 26 territories (three at 0%) not enter indication codes? | Maria Kontorinakis | T2, M3 |
| K4 | Did indication codes become mandatory in Jul / Aug 2025? Any change planned? | Maria Kontorinakis | M3 |
| K5 | Official material grouping (PN-7); is material entry expected on every call? | Brand / digital team | M2 |
| K6 | Can training cohorts be extended past Jul 2025, ideally Jan 2026? | Modelling team | M1 – M3, C3, E6 |

---

## 8. Next actions

| # | Action | Closes | Owner |
| --- | --- | --- | --- |
| N1 | Send K1 – K6 | Gate, T3 | NBA team |
| N2 | Extend cohort anchors and re-run notebooks 41 and 42 | P1 | Modelling team, NBA team |
| N3 | Compare first-message pattern with doctor specialty | P2 | NBA team |
| N4 | After K2 / K6: build coarse M1 (CKD-first, HF-first, dual shares, 6 months) and M3 in config | M1, M3 | NBA team |
| N5 | Run E3 (E2 + message features) once E2 exists | G2 | NBA team, modelling team |
| N6 | Update readiness plan Phase 2 status with this decision | Documentation | NBA team |
