# Field Activity Phase 2: Output Analysis (NBA 3.1)

**Notebook:** `42_field_activity_phase2_message_features`  
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 2: M1 – M3, condition V4; design principles 5 and 9; risk "key messages entered unevenly")  
**Run analysed:** 6 Nov 2026, serverless (re-run on the NBA 3.1 HCP universe and the 28 promotional cohorts; first run 4 Nov 2026 on BHID and the 26-cohort CSV; confirmed end-to-end in-notebook run 6 Nov 2026, results unchanged)  
**Date:** 6 Nov 2026

**Set-up of the re-run.** Same as notebooks 44 (samples) and 45 (MSL flag): cohorts `cohorts/promotional/cohorts.parquet` (28 cohorts, offset 17: c1 – c24 Training, lookback end 2024-06-17 to 2026-05-17; c25 – c26 Testing; c27 – c28 Holdout, to 2026-09-17); grain one row per `PROVIDER_ID` x `COHORT_ID` on `HCP_Universe_without_call_hcps/` (294,726 HCPs after removing the placeholder `PROVIDER_ID` '0'); BHID mapped through `SOURCE_PROVIDER_BHID_NPI_MAPPING`. Years: Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026.

**How to read this file.** Section 1 is the summary. Section 2 gives the background for a first-time reader. Section 3 explains what the notebook does. Section 4 goes through every expectation: why we expected it (from NBA 3.0), whether it is new, what we got, and what to raise with the client. Sections 5 – 8 list the gate, issues, client questions and next actions.

---

## 1. Summary

| ID | Expectation (readiness plan) | NBA 3.0 or new | Status | One-line result |
| --- | --- | --- | --- | --- |
| R0 | Same Kerendia HCP interactions as Phase 1 | — | **Met** | Year 1 472,236 / 77,308 doctors (exact); Year 2 606,357 / 96,719 (+0.02% / +0.11%, late entries); 88.4% of Year 2 doctors and 95.3% of interactions are on universe HCPs |
| V4-a | Indication code on a high share of interactions every month | New | **Met (T1 PASS)** | 92.7 – 97.2% each month in 2026; on position codes only 88.8 – 90.7%; 0% before Jun 2025 |
| V4-b | High share across territories | New (action A4) | **Met, borderline (T2)** | 94.9% of 746 territories at or above 70%; on position codes only 89.9% (69 territories below 50%) |
| V4-c | No reps always entering the same code | New | **Not met as stated (T3 FAIL)** | Unchanged: 24.8% of reps always put CKD first, concentrated in teams CR4 (60%) and CR1 (33%) |
| M1 | Indication of the main message | New | **Built (coarse)** | `FLD_CKD_FIRST_SHARE_6M`, `FLD_HF_FIRST_SHARE_6M`; among HCPs with M3 = 1, mean HF-first share falls from 0.37 (c15) to 0.29 (c28) |
| M2 | Materials shown | New | **Dropped** | 71 material names on 13 – 15% of interactions; the "dual indication" code is a visual aid, so the dual share is dropped too |
| M3 | Data-available flag | New (principle 9) | **Built** | `FLD_KEYMSG_AVAILABLE` = 1 on 0 HCPs up to c14, 14,789 in c15, 56,858 in c24, 65,419 in c28 |
| Coverage | Training cohorts contain indication codes | — | **Lifted, partly** | 11 of 24 training cohorts (c14 – c24); the full 6-month window is after Aug 2025 only from c21 |
| Checks | Keys, nulls, invariants, leakage, recompute | — | **Pass** | 8,252,328 rows = 294,726 x 28; 0 duplicates, 0 nulls, 4 / 4 invariants, 28 / 28 cohorts consistent, 12 / 12 HCPs match in Snowflake |

**Bottom line.** The gate results of 4 Nov hold. With the 28 promotional cohorts the coverage blocker is lifted (11 of 24 training cohorts contain codes), so the coarse features decided on 4 Nov are now **built** on the NBA 3.1 universe: two M1 shares (CKD first, HF first) and the M3 flag; M2 and the planned dual share are dropped. All checks pass. Three rule fixes came out of the re-run: the June – July 2025 code names (`P1 KER ...`) are now counted, materials no longer count as indication codes in the M3 territory rule, and the "dual indication" code is a visual aid, not a message. On position codes only, T2 is borderline (89.9% against 90%). Open points: K2 (always-CKD teams, T3) and K3 (low-entry territories); the features carry signal in only the last 11 training cohorts, so experiment E6 is needed.

*Sections 2 – 8 keep the 4 Nov analysis and add the 6 Nov results, marked **Re-run 6 Nov**.*

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

**Re-run 6 Nov: notebook as modified.**

| Step | Cell | What it does |
| --- | --- | --- |
| Setup | 3 | Config: NBA 3.1 paths, `EXCLUDE_PROVIDER_IDS = ["0"]`, data range 2023-12-01 – 2026-10-31, 6-month window (182 days), `FULL_CODE_START = 2025-08-01`, low-entry threshold 50%, 4 Nov reference counts, `expected_feature_columns()` (3 columns) |
| Inputs | 4 | 28 promotional cohorts, HCP universe, BHID to `PROVIDER_ID` mapping (universe only) |
| 1 – 2 | 5 | Same SQL rules as on 4 Nov, plus `P1 KER ...` position-1 names and a `HAS_IND_CODE` flag (position codes only); writes `field_interaction_message`; reconciles with 4 Nov; Year 2 universe coverage |
| 3 – 5 | 6 – 8 | As on 4 Nov; Step 3 adds the position-code share |
| 6 | 9 | Coverage of indication codes on the 28 cohorts |
| 7 | 10 | Gate T1 – T3 as on 4 Nov, plus T1 / T2 on position codes only |
| 8a | 11 | Attaches interactions to each cohort window (`LOOKBACK_END_DATE` − 182 days, `LOOKBACK_END_DATE`]; leakage check; low-entry territories per cohort from the cohort's own window; maps to `PROVIDER_ID` |
| 8b | 12 | M1 shares and M3 flag per `PROVIDER_ID` x cohort |
| 8c | 13 | Universe x cohort skeleton, defaults 0, fixed schema, write; cohort diagnostics |
| Checks | 14 – 16 | Keys / nulls / invariants and consistency; profile by cohort; independent Snowflake recompute for 12 HCPs in c24 |
| Decision | 17 | Gate and results |

Fixes in the re-run: (1) `P1 KER CKD` / `P1 KER HF` (June – July 2025 naming) added to the position-1 patterns; (2) the planned `FLD_DUAL_IND_SHARE_6M` gave values up to 20 because `%Dual Indication%` is a visual-aid name present on calls without an indication code, so the column was dropped; (3) operator precedence in the share-range invariant fixed. Outputs (`notebook_output/field_activity_nba_3_1/`): `kerendia_nba_3_1_hcp_model_field_message_features.parquet`, `field_message_cohort_diagnostics.parquet`, `field_interaction_message.parquet`.

---

## 4. Expectation by expectation

### R0 — Same base as Phase 1

* **Why we expect this.** Message features must describe the same interactions as the Phase 1 counts, otherwise shares and counts disagree.
* **NBA 3.0 or new.** New check.
* **What we got.** Year 1 472,236 calls / 77,308 doctors; Year 2 606,239 / 96,610. Identical to notebook 41 and Phase 0 V2.
* **Re-run 6 Nov.** Year 1 472,236 / 77,308 (exact); Year 2 606,357 / 96,719 (+0.02% / +0.11%, calls entered after 4 Nov). Universe: 85,501 of 96,719 Year 2 doctors (88.4%) and 578,071 of 606,357 interactions (95.3%) are on universe HCPs.
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
* **Re-run 6 Nov.** Monthly shares unchanged except July 2025 position 1: 50.1% (was 32.5%) after adding the `P1 KER ...` names used in June – July 2025. New check: on position codes only (excluding material names such as `KER CKD/HF Digital MVA Refresh Dual Indication`, from Jan 2026), the 2026 share is 88.8 – 90.7% a month; 31,755 calls are flagged only through a material.
* **Status.** Met (T1: lowest month 92.7% against a proposed 80%; 88.8% on position codes only).
* **Raise with client.** Confirm the threshold. Confirm with Maria Kontorinakis that the codes became mandatory in July / August 2025 (Phase 0 C5).

### V4-b — Consistency across territories (action A4)

* **Why we expect this.** A high national share can hide territories that never enter codes; for those doctors a message feature would always be 0 for a reason unrelated to the doctor.
* **NBA 3.0 or new.** New.
* **What we got.** 746 territories and 733 reps with at least 50 interactions in 2026; every interaction has a territory and a rep. Territory share P10 93.6%, median 100%. 94.9% of territories at or above 70%. Stricter version (at least 70% in every single month): 89.9%. 26 territories below 50% hold 19,445 of 533,256 interactions (3.6%); three enter no indication code at all (`US_PH_CR1_033A` 1,256 interactions, `US_PH_CR1_328A` 1,203, `US_PH_CR5_608B` 133).
* **Re-run 6 Nov.** Same territory figures (746 territories, P10 93.6%, 26 below 50%, 3 at 0%). On position codes only: 89.9% of territories at or above 70% and 69 territories below 50% (51,745 interactions): the CKD / HF material names hide part of the low entry.
* **Status.** Met (T2 PASS); borderline on the strict monthly version and on position codes only (89.9% against 90%).
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
* **What we got (4 Nov).** The inputs exist and are clean (one flag per call for CKD first, HF first, dual). No feature built.
* **Re-run 6 Nov: built.** `FLD_CKD_FIRST_SHARE_6M` and `FLD_HF_FIRST_SHARE_6M` = share of the HCP's position-1 indication codes in the 6-month window that are CKD / HF (0 when there is none). 29,808 calls carry both codes, so the shares can sum to more than 1 (55,544 rows).

| Set | HCPs with M1 > 0 | Mean CKD-first share (M3 = 1) | Mean HF-first share (M3 = 1) | Only CKD first | Only HF first |
| --- | --- | --- | --- | --- | --- |
| c1 – c13 | 0 (4 in c13) | — | — | — | — |
| c14 | 2,842 | — (M3 = 0) | — | — | — |
| c15 – c20 | 21,358 – 52,050 | 0.59 – 0.66 | 0.37 – 0.35 | 50 – 54% | 34 – 30% |
| c21 – c24 | 53,086 – 53,944 | 0.67 – 0.68 | 0.33 – 0.30 | 56 – 60% | 29 – 27% |
| Testing c25 / c26 | 55,745 / 59,847 | 0.69 / 0.70 | 0.29 / 0.29 | 61 / 61% | 26 / 26% |
| Holdout c27 / c28 | 61,797 / 63,081 | 0.70 / 0.70 | 0.29 / 0.29 | 62 / 61% | 26 / 26% |

  The HF-first share keeps falling through training and is flat in testing and holdout, the same drift as the monthly HF share (40% Aug 2025 to about 30% in 2026; C5).
* **Status.** Built (coarse), to use with caution until K2.
* **Raise with client.** K2 (always-CKD teams); C5 (change in HF messaging in 2026).
* **Suggestions.** Compare M1 with doctor specialty and team before E3 (N3); prefer the HF-first share as the single M1 input if E3 shows the two are redundant.

### M2 — Materials shown

* **Why we expect this.** Materials (visual aid, patient profile, access brochure) show what the rep discussed; the plan asks for a grouping aligned with digital content groups (PN-7).
* **NBA 3.0 or new.** New.
* **What we got.** 71 material names on Kerendia calls in 2026. Top: `KER CKD/HF Digital MVA Refresh Dual Indication` 54,227 calls, `KER HF Digital MVA Refresh Cardiologist` 23,077, `LYNKUET DIGITAL MASTER VISUAL AID` 21,376, `26 ACC HFpEF ECDP Leave Behind` 11,121, `BACC Kerendia - Standalone - Vault` 10,324, `Tipping Point Brochure` 6,480, `Lynkuet TV Commercial` 6,279, `Cardiology Patient Profile - Armand` 4,245, `Neph CKD Patient Profile` 1,617. But only 13 – 15% of interactions have a material. Lynkuet and Adempas materials appear on Kerendia calls through co-detail.
* **Status.** Drop for now.
* **Raise with client (brand / digital team).** Official material grouping (PN-7) and whether material entry is expected on every call. Reason: with 85% of calls empty, a material feature mostly measures whether the rep uses the digital aid.
* **Suggestions.** Keep only a coarse "digital visual aid used" flag as a candidate; revisit after PN-7.
* **Re-run 6 Nov: dual indication is a material too.** `%Dual Indication%` matches `Dual Indication MVA` (Jul 2025 – Jan 2026, up to 8,900 Kerendia calls a month) and then `KER CKD/HF Digital MVA Refresh Dual Indication` (from Jan 2026, about 6,000 a month). 36,827 of 54,701 dual calls have no indication code, and the planned dual share reached values up to 20. It describes the visual aid used, so it is dropped with M2.

### M3 — Data-available flag

* **Why we expect this.** Principle 9: features that depend on codes from July 2025 need a flag so the model does not read "no code" as "no message".
* **NBA 3.0 or new.** New.
* **What we got (4 Nov).** Codes start July 2025 (52% that month, 88% from August). Not built.
* **Re-run 6 Nov: built at HCP level.** `FLD_KEYMSG_AVAILABLE` = 1 if the HCP had a Kerendia HCP interaction in the 6-month window on or after 1 Aug 2025 in a territory that enters codes. A territory is low-entry in a cohort if it has at least 50 interactions since 1 Aug 2025 in that cohort's window and a position-code share below 50% (computed from the window only, no look-ahead): 17 in c15, 44 – 53 in c16 – c24, 63 – 68 in c25 – c28. An HCP flag, not a cohort-level date flag, so it does not act as a time marker on its own.

| Set | HCPs with M3 = 1 | Zero rate |
| --- | --- | --- |
| c1 – c14 | 0 | 100% |
| c15 – c20 | 14,789 – 52,278 | 95.0 – 82.3% |
| c21 – c24 | 55,039 – 56,858 | 81.3 – 80.7% |
| Testing c25 / c26 | 58,455 / 62,497 | 80.2 / 78.8% |
| Holdout c27 / c28 | 64,144 / 65,419 | 78.2 / 77.8% |

  About 4 – 6% of HCPs with M3 = 1 (9.8% in c15) have no position-1 code in the window (calls with only a position-2 code or without codes).
* **Status.** Built.
* **Suggestions.** Keep M3 next to M1 in every experiment; c14 has 2,842 HCPs with M1 > 0 from the July 2025 start but M3 = 0 by design.

### Coverage — Training cohorts

* **Why we expect this.** A feature can only be learned if training rows contain it.
* **What we got.** 26 cohorts, first ends 2023-03-17, last 2025-04-16; 0 cohorts end after July 2025.
* **Status (4 Nov).** Blocker: M1 – M3 would be 0 for every training row.
* **Raise with client (modelling team).** Extend cohort anchors past July 2025, ideally past January 2026 (also needed for co-detail, Phase 1 C3, and experiment E6).
* **Re-run 6 Nov.** With the 28 promotional cohorts: c14 – c24 (11 of 24 training cohorts) contain codes in the 6-month window; the window lies fully after 1 Aug 2025 from c21 (4 training cohorts); testing and holdout are fully covered. **Blocker lifted**, but c1 – c13 carry no message signal, so E6 (training on recent cohorts) is needed.

---

## 5. Gate (V4 / G2 part)

Thresholds are **proposals** to agree with the client.

| # | Proposed threshold | Result | Status |
| --- | --- | --- | --- |
| T1 | Monthly indication share >= 80% in every month since Jan 2026 | Lowest 92.7% (position codes only: 88.8%) | PASS |
| T2 | >= 90% of territories (>= 50 interactions) with share >= 70% | 94.9% (strict monthly: 89.9%; position codes only: 89.9%) | PASS (borderline strict and on position codes) |
| T3 | No large group of reps always entering the same code | 24.8% always CKD first | FAIL as stated, pending explanation |
| Coverage | At least one training cohort with codes | 4 Nov: 0 of 26; 6 Nov: 11 of 24 (c14 – c24) | Lifted (6 Nov) |
| Checks (6 Nov) | Keys, nulls, invariants, leakage, recompute | 8,252,328 rows; 0 duplicates, 0 nulls; 4 / 4 invariants; 28 / 28 cohorts consistent; 12 / 12 HCPs match in Snowflake (c24) | PASS |

**Decision (4 Nov):** coarse M1 + M3 only, after cohort extension and the T3 answer; M2 dropped for now; no columns built. G2 also requires the V4 decision to be taken (keep / coarse / drop); the proposal is "coarse".

**Decision (6 Nov):** V4 decision = **coarse**. Built: `FLD_CKD_FIRST_SHARE_6M`, `FLD_HF_FIRST_SHARE_6M`, `FLD_KEYMSG_AVAILABLE`; dropped: M2 and the dual share. To use with caution until K2 and K3 are answered; E3 (and E6) still to run.

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
| P7 | (6 Nov) June – July 2025 position codes named `P1 KER CKD` / `P1 KER HF` | July 2025 position-1 share understated (32.5% instead of 50.1%); M1 short in c14 – c20 windows | Fixed: patterns added |
| P8 | (6 Nov) `%KER CKD%` / `%KER HF%` also match material names | Indication share overstated in 2026 (31,755 calls); T2 borderline on position codes | `HAS_IND_CODE` (position codes only) used for the M3 territory rule; gate reported both ways |
| P9 | (6 Nov) `%Dual Indication%` is a visual aid, not an indication message | Planned dual share up to 20 | Dual share dropped (with M2) |
| P10 | (6 Nov) 29,808 calls carry both CKD-first and HF-first codes | M1 shares can sum to more than 1 (55,544 rows) | Kept as is; ask K7 |
| P11 | (6 Nov) Only 11 of 24 training cohorts contain codes; HF-first share drifts down in training | Model learns M1 from part of training only | E6; watch M1 importance by cohort |
| P12 | (6 Nov) 11.6% of Year 2 called doctors are not in the universe | Their messages are not in the output | Same universe point as notebooks 44 / 45 |

---

## 7. Questions to send to the client

| # | Question | Team | Blocks |
| --- | --- | --- | --- |
| K1 | Agree the V4 thresholds T1 – T3 | Field Analytics, modelling team | Gate |
| K2 | What do teams CR1, CR2, CR4, CR5 and CAR cover? Are CR4 / CR1 reps expected to give only the CKD message? | Field Analytics | T3, M1 |
| K3 | Why do 26 territories (three at 0%) not enter indication codes? | Maria Kontorinakis | T2, M3 |
| K4 | Did indication codes become mandatory in Jul / Aug 2025? Any change planned? | Maria Kontorinakis | M3 |
| K5 | Official material grouping (PN-7); is material entry expected on every call? | Brand / digital team | M2 |
| K6 | Can training cohorts be extended past Jul 2025, ideally Jan 2026? | Modelling team | **Answered 6 Nov:** 28 promotional cohorts (to 2026-09-17) used |
| K7 | (6 Nov) What does a call with both `Position 1 KER CKD` and `Position 1 KER HF` mean (29,808 calls)? Were `P1 KER ...` codes the July 2025 pilot names? | Maria Kontorinakis | M1 |

---

## 8. Next actions

| # | Action | Closes | Owner |
| --- | --- | --- | --- |
| N1 | Send K1 – K6 | Gate, T3 | NBA team |
| N2 | Extend cohort anchors and re-run notebooks 41 and 42 | P1 | Modelling team, NBA team — **42 done 6 Nov** (41 still on the 26-cohort CSV) |
| N3 | Compare first-message pattern with doctor specialty | P2 | NBA team |
| N4 | After K2 / K6: build coarse M1 (CKD-first, HF-first, dual shares, 6 months) and M3 in config | M1, M3 | NBA team — **done 6 Nov** (without the dual share; K2 still open) |
| N7 | (6 Nov) Send K7; re-check the territory list behind P8 with Maria Kontorinakis (K3) | P8, P10 | NBA team |
| N8 | (6 Nov) Run E6 (recent cohorts only) with M1 + M3 | P11 | NBA team, modelling team |
| N9 | (6 Nov) Join the message output with the other 3.1 field blocks on `HCP_COHORT_ID` | Integration | NBA team |
| N5 | Run E3 (E2 + message features) once E2 exists | G2 | NBA team, modelling team |
| N6 | Update readiness plan Phase 2 status with this decision | Documentation | NBA team |
