# Kerendia NBA 3.1 — Competitor & Comorbidity Features: Briefing for Josh Buffington

**For:** Josh Buffington, PharmD — Competitive Intelligence  
**From:** NBA modelling team (Wenjie)  
**Purpose:** Walk through what the model currently knows (and doesn’t know) about the competitive landscape and patient populations, then share what we’re planning to fix for NBA 3.1 — most of which is a direct response to your CI report  
**Date:** November 2026  
**Status:** Pre-meeting draft — nothing built yet, all feedback welcome

---

## 1. What we need from you

Your CI report gave us five market developments that point directly at gaps in the model. Before we build, we want to make sure we’re:

1. **Capturing the right drugs.** Does the list we’re tracking match what you consider the live competitive set?
2. **Reading the right signals.** Are there HCP-level patterns in the competitive data that a model should look for, that we haven’t thought of?
3. **Not building something that looks good in data but is wrong in the market.** For example, is high Jardiance prescribing always a proxy for a CKD-active HCP, or does it sometimes mean something else?
4. **Answering the specific questions at the end** — your view on six of them directly changes what we build.

---

## 2. The short version

| Feature area | Today (NBA 3.0) | NBA 3.1 plan |
| --- | --- | --- |
| **Who the HCP’s patients are** (comorbidity) | We see kidney-disease patients (CKD, diabetic CKD, cardio-renal CKD). **No heart failure. No T1D. CKD stage 3 almost invisible.** 3 of 39 columns kept by the model. | Add HF, T1D, CKD stage 3, and a “growing indicated panel” signal. Target: ~15 columns |
| **Which SGLT2s the HCP writes** (competitor share) | Track Farxiga, Invokana, Jardiance, Steglatro — but **across all indications mixed together** (most is T2D, not CKD). After Farxiga’s generic launch, the signal is now partly noise. Invokana and Steglatro are near-zero. **No Baxfendy.** | Filter to CKD-labeled prescribing only. Split Farxiga brand vs generic. Add steroidal MRAs. Track Baxfendy once it appears in the data. |
| **How fast the HCP adopts new CKD therapies** (adoption speed) | One strong feature: how quickly a CKD patient got Farxiga from the same HCP. Rank 13 of 752, very predictive. **Nothing for HF drugs (no Entresto).** | Keep Farxiga. Add Jardiance, spironolactone/eplerenone, **Entresto** (your report’s LOE finding is exactly why), Invokana. |
| **New competitors** | **None.** Baxfendy approved May 2026, 4,712 HCPs writing it — model cannot see any of this. GLP-1 in HFpEF not tracked. | Add Baxfendy, GLP-1 with HF indication. Flag ASI trial zip codes as a risk/opportunity signal. |

**Bottom line: the model currently ignores HF patients, mislabels most of the SGLT2 activity as CKD when it’s actually T2D, and has no visibility into Baxfendy at all.** These are fixable, and most of the fixes come directly from your report.

---

## 3. How the model works (for context)

NBA (Next Best Action) scores around 315,000 HCPs each month and recommends the next promotional action for each one. It uses ~750 data signals (features) built from claims, diagnoses, promotional activity and prescribing history. The model learns which signals predict that an HCP will write a new Kerendia prescription in the next 30 days.

The competitor and comorbidity features we’re discussing today try to answer two questions:

* **Who does this HCP see?** (patients with CKD, T2D+CKD, HF+CKD, T1D+CKD)
* **What does this HCP already prescribe?** (Jardiance, Farxiga, MRAs, Entresto — how much, how fast, how recently)

HCPs who already treat the right patient types and have adopted related drugs quickly are the most likely to also adopt Kerendia. The problem is that the current features don’t describe the patient types or drugs accurately enough.

---

## 4. NBA 3.0 today: what the model sees and what it misses

### 4.1 Comorbidity — the patient-panel features

**What we measure:** For each HCP, how many patients they billed a kidney-related diagnosis for each month. We track three groups:
- Kidney disease only (CKD stages, hypertensive CKD)
- Diabetic kidney disease (T2D with CKD)
- Cardio-renal CKD (hypertensive heart and CKD together)

**What the model kept:** 3 of 39 features.

| Rank | What it says | Signal direction |
| --- | --- | --- |
| 88 | Share of the HCP’s kidney patients who have cardio-renal CKD | *Inverse* — a higher share actually correlates with **fewer** Kerendia writers. Likely reflects small, specialty-heavy panels where one or two cardio-renal patients inflate the percentage |
| 133 | Running total of diabetic-CKD patients since 2021 | Positive — longer/larger diabetic-CKD experience |
| 237 | Running total of all kidney patients since 2021 | Positive — overall kidney practice size |

**What we miss entirely:**

| Missing | Why it matters |
| --- | --- |
| **Heart failure patients** | Kerendia now has an HF (LVEF ≥ 40%) indication. The model has never seen an HF patient in any HCP’s panel. |
| **T1D + CKD patients** | New indication. The model has seen zero T1D features ever. |
| **CKD stage 3 (eGFR 30–60)** | This is where Kerendia is started. Our diagnosis code list is missing the ICD-10 codes for stage 3a and 3b (N18.30/31/32) — a billing standard change from October 2020 that was never picked up. The data shows only 26,200 stage-3 coded patients vs 10.5 million stage-4 coded patients. Most stage 3 patients only appear through their hypertensive CKD or diabetic CKD codes. |

### 4.2 Competitor drug features

**What we measure:** For each HCP, the 12-month rolling count and percentage share of new prescriptions (NBRx) for four SGLT2 drugs: Farxiga, Invokana, Jardiance, Steglatro.

**The problem with how we built it:** We pull all prescriptions regardless of what diagnosis they were written for. Here is the breakdown for October 2025 – September 2026:

| Drug | % of NBRx for a CKD-labeled patient | What the rest mostly is |
| --- | --- | --- |
| Jardiance | ~15% | T2D, T2D+CVD (~55%) |
| Farxiga (brand + generic) | ~32% | T2D, T2D+CVD (~43%) |
| Kerendia | ~57% | T2D alone or T2D+CVD (~24%) |

So when the model sees a high Jardiance share for an HCP, it mostly reflects a **general T2D/cardiology prescriber**, not specifically a CKD-active one. These are related but different HCP profiles.

**Market trend (last two years, all indications):**

| | Nov 2024 | Aug 2026 | Direction |
| --- | --- | --- | --- |
| Jardiance monthly NBRx | 163K | 134K | Stable/flat |
| Farxiga (incl. generic) | 94K | **291K** | Surged after LOE (April 2026) |
| Kerendia | 6.3K | 9.4K | Growing (+49% over 2 years) |
| Invokana | 1.6K | 0.7K | Declining to near-zero |
| Steglatro | 1.3K | 0.5K | Declining to near-zero |

The Farxiga surge is entirely the generic dapagliflozin launch. The model currently lumps brand Farxiga (early adopter signal) and generic dapagliflozin (cost-driven, broad T2D use) into one feature.

### 4.3 Adoption-speed features

**What we measure:** For each HCP, the shortest number of days between a CKD patient’s first CKD diagnosis from that HCP and the patient’s first Farxiga prescription from the same HCP. A lower number means the HCP adopted Farxiga quickly for CKD patients.

**This is the strongest feature in this entire family: rank 13 of 752, 1.1% of total model weight.** The intuition is simple: an HCP who put CKD patients on Farxiga quickly is likely to do the same with Kerendia.

**What we miss:** We built this for Farxiga and Invokana only. Invokana was too sparse to be useful. We have nothing for Jardiance, spironolactone, or — critically — **Entresto**.

---

## 5. What your CI report tells us, and how we’re responding

Your September 2026 CI report gave us five market developments. Here is how each one maps to a specific gap in the model and what we’re planning.

### 5.1 Farxiga LOE (April 6, 2026) — HIGH impact

**What you found:** Generic dapagliflozin entered at ~$40/month. SGLT2i OOP costs fell sharply, reducing the polypharmacy cost objection to adding Kerendia.

**Model gap:** Our Farxiga share feature no longer distinguishes between brand Farxiga CKD advocacy and generic dapagliflozin cost-driven T2D prescribing. An HCP who switched all their T2D patients to cheap generic dapagliflozin looks identical to an HCP who’s been prescribing brand Farxiga for CKD patients for years.

**NBA 3.1 response:** Split Farxiga brand vs. generic as separate features, both filtered to CKD-labeled indications only (C1).

### 5.2 Entresto LOE (July 2025) — new HF adoption signal

**What you found:** Generic sacubitril/valsartan now available at ~$40/month.

**Model gap:** Kerendia now has an HF indication. The model has no HF-practice adoption feature at all. We proved with Farxiga that “time to adopt a guideline-backed HF/CKD drug” is one of the model’s strongest signals. We have not applied the same logic to Entresto — the defining HF drug.

**NBA 3.1 response:** Add `TIME_TO_ADOPT_ENTRESTO` — days from a patient’s HF diagnosis to their first Entresto from that HCP (C2). HCPs who adopted Entresto early (before the LOE, when it was expensive) are the most likely early adopters of Kerendia for HF.

### 5.3 Baxfendy (May 2026 approval) — invisible competitor

**What you found:** 4,712 HCPs have prescribed Baxfendy; 898 weekly NBRx. 71% PCPs, 41% outside our target segment. Currently Step 4 (resistant HTN), later-line than Kerendia. BaxDuo-CKD trial reads out ~Feb 2028.

**Model gap:** The model has no Baxfendy feature of any kind. Baxfendy prescribers overlap 20% with Kerendia Segment A — these are MRA-class-aware HCPs who may be high-propensity Kerendia adopters. We can’t see them.

**NBA 3.1 response:** Add Baxfendy NBRx share and adoption-speed features once the product appears in IQVIA LAAD data (C3). See Q1 below.

**Steroidal MRA parallel:** Your report’s ACC ECDP footnote (steroidal MRA as cost/tolerance alternative to nsMRA in HFpEF) confirms what we independently proposed in the adoption features: track how quickly HCPs adopt spironolactone/eplerenone for CKD patients. HCPs already using an MRA are the nearest-neighbour to Kerendia adoption.

### 5.4 EASi-KIDNEY halted (September 15, 2026)

**What you found:** Boehringer’s vicadrostat discontinued for futility. Clear runway until BaxDuo-CKD ~Feb 2028. But ASI trials exclude MRAs from enrollment, affecting 19% of US zip codes.

**Model gap:** No geographic signal. If an HCP’s patients are enrolled in an ASI trial (and therefore excluded from MRAs), a different NBA recommendation may be appropriate — but the model can’t see that.

**NBA 3.1 response:** Explore a zip-code-level trial-enrollment flag as an optional signal (C5). Lower priority, depends on whether zip-code data is cleanly available.

### 5.5 GLP-1 in HFpEF guidelines (ESC / ACC 2026)

**What you found:** Semaglutide and tirzepatide are now Class IIa in HFpEF (BMI ≥ 30) in both ESC 2026 and the updated ACC pathway. Neither carries an FDA HF label, but prescribing is happening. Wegovy OOP is rising above $490/90 days, which may limit uptake.

**Model gap:** No GLP-1 feature. The same obese HFpEF + T2D patient who might get semaglutide is also eligible for Kerendia’s new HF indication. An HCP who already writes GLP-1 in HF patients is treating exactly this population.

**NBA 3.1 response:** Add GLP-1 (semaglutide, tirzepatide) NBRx feature filtered to HF-labeled indications (C4).

---

## 6. What we’re planning to build (full list)

### Comorbidity — patient-panel signals (~15 new features)

| What | Clinical meaning |
| --- | --- |
| Share of panel with T2D + CKD | Core Kerendia indication — the first time the model will see this directly |
| Share of panel with HF (LVEF ≥ 40% proxy) | New HF indication — completely new to the model |
| Share of panel with HF + CKD | Combined cardio-renal indication |
| Share of panel with T1D + CKD | New T1D indication |
| CKD stage 3 share (N18.30/31/32) | Core Kerendia prescribing population; currently missing |
| CKD stage 4 share | Highest model signal in backtesting |
| Growth in indicated panel (3M vs prior 9M) | Is this HCP seeing more eligible patients recently? |

### Competitor drug signals (~17 new or rebuilt features)

| What | Why |
| --- | --- |
| Jardiance CKD share (12M and 3M) | Best SGLT2 CKD adoption signal, fixed to CKD-labeled prescribing |
| Farxiga BRAND CKD share | Early-adopter signal, separated from generic |
| Farxiga GENERIC share | Generic dapagliflozin cost-switching signal |
| Steroidal MRA (spironolactone + eplerenone) CKD share | Closest existing MRA user to Kerendia adoption; ACC ECDP listed as alternative |
| Baxfendy NBRx and share | MRA-class-aware HCPs; 20% overlap with Segment A |
| GLP-1 NBRx with HF indication | Same HFpEF + T2D patient population |

### Adoption-speed signals (14 new features across 5 drugs)

For each drug: *How fast does this HCP start a CKD patient on the drug after diagnosis?*

| Drug | Why |
| --- | --- |
| Farxiga (rebuilt, any-provider CKD date) | Existing model signal, improved |
| Jardiance | Largest SGLT2 CKD brand; strong backtest signal |
| Spironolactone + eplerenone | MRA class predecessor to Kerendia |
| **Entresto** | **HF early adopter signal — the most important new addition for the HF indication** |
| Invokana | Retained for completeness; sparse |

---

## 7. Questions for Josh

Your answers directly change what we build. We’d like to go through these in the meeting.

| # | Question | Why it matters |
| --- | --- | --- |
| Q1 | Is Baxfendy (baxdrostat) expected to appear in IQVIA LAAD data soon? We can’t find it yet in the prescribing feed (KERENDIA_LAAD_BASED_LRX_V6). Do you have a rough timeline for when IQVIA captures it? | Determines whether we can build a Baxfendy feature in time for NBA 3.1 training |
| Q2 | Which specialty drives early Entresto adoption — cardiologists, HF specialists, PCPs? And does the pattern vary by practice size? | Helps us validate whether the `TIME_TO_ADOPT_ENTRESTO` feature will have enough coverage in the HCP types we target |
| Q3 | 41% of Baxfendy prescribers are outside our target segment. Is there a way to tell, from the competitive data, which of those 4,712 HCPs are genuinely MRA-aware vs. just prescribed it once for a resistant-HTN patient with no CKD? | If the non-target group is noise, we may want to filter the Baxfendy feature to specialty or prior CKD prescribing |
| Q4 | Your report says Balcinrenone + dapagliflozin (AstraZeneca) is in Phase III. Should we plan a monitoring feature now — even if it’s just an ‘HCP is enrolled in AstraZeneca trials’ flag — so the model is ready when enrollment data becomes visible? | Shapes how we approach the ASI/competitor monitoring pipeline |
| Q5 | For GLP-1 in HFpEF: in your view, is the main risk to Kerendia that GLP-1 *replaces* the prescribing moment (doctor picks one drug) or that it *delays* it (doctor addresses obesity first, then comes back to Kerendia)? | Changes whether we model GLP-1 HF prescribing as a negative signal (competitor risk) or a positive one (same-practice indicator) |
| Q6 | You noted that Finerenone holds a mechanistic edge over ASIs because it also blocks cortisol-driven MR activation. Is this messaging already landing with HCPs, and if so, through which channels or specialties? | If certain HCP profiles already respond to this differentiation, we may be able to build a ‘receptive to MRA class distinction’ signal from their engagement data |

---

## 8. What happens next

| Step | Owner | When |
| --- | --- | --- |
| Meeting: review this doc, collect answers to Q1–Q6 | Josh + Wenjie | Nov 2026 |
| Confirm Baxfendy and GLP-1 data availability in IQVIA | Data engineering | After meeting |
| Build comorbidity features (H1–H3, M1–M3) | NBA team | Nov–Dec 2026 |
| Build competitor features (H4–H5, M4–M5, C1–C2) | NBA team | Nov–Dec 2026 |
| Build adoption-speed features (M6, C2 Entresto) | NBA team | Dec 2026 |
| Feature selection + backtest review | NBA + BA | Jan 2027 |
| NBA 3.1 training | NBA team | Q1 2027 |

*Reference: full technical detail is in `90_competitor_comorbidity_summary_and_trends.md` (same folder). The CI report this doc references is “Competitive Intelligence Overview, Joshua Buffington PharmD, 9/23/26” (internal).*
