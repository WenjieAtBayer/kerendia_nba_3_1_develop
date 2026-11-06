# Kerendia NBA 3.1 — Competitor & Comorbidity Features: Briefing for Josh Buffington

> **Data source update (Nov 2026):** NBA 3.1 now reads `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (LAAD-based LRx V7, weekly, history from Dec 2021) instead of `KERENDIA_LAAD_BASED_LRX_V6` and `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021`. Read V6 references below as V7. V7 `WEEK_ENDING_DATE` / `PERIOD_ID` are DATEs, and `PRODUCT_GROUP` uses the shorter lrx_nbrx names. Numbers in this document were computed on V6.

**For:** Josh Buffington, PharmD — Competitive Intelligence  
**From:** NBA modelling team (Wenjie)  
**Purpose:** Walk through what the model currently knows (and doesn’t know) about the competitive landscape and patient populations, then share what we’re planning to fix for NBA 3.1 — most of which is a direct response to your CI report  
**Date:** November 2026  
**Status:** Updated after meeting with Josh (Nov 2026), see Section 9 for decisions. Nothing built yet.

---

## 1. What we need from you

Your CI report gave us five market developments that point directly at gaps in the model. Before we build, we want to make sure we’re:

1. **Capturing the right drugs.** Does the list we’re tracking match what you consider the live competitive set?
2. **Reading the right signals.** Are there HCP-level patterns in the competitive data that a model should look for, that we haven’t thought of?
3. **Not building something that looks good in data but is wrong in the market.** For example, is high Jardiance prescribing always a proxy for a CKD-active HCP, or does it sometimes mean something else?
4. **Answering the specific questions at the end** — your view on eight of them directly changes what we build.

---

## 2. The short version

| Feature area | Today (NBA 3.0) | NBA 3.1 plan |
| --- | --- | --- |
| **Who the HCP’s patients are** (comorbidity) | We see kidney-disease patients (CKD, diabetic CKD, cardio-renal CKD). **No heart failure. No T1D. CKD stage 3 almost invisible.** 3 of 39 columns kept by the model. | Add HF, T1D, CKD stage 3, and a “growing indicated panel” signal. Target: ~15 columns |
| **Which SGLT2s the HCP writes** (competitor share) | Track Farxiga, Invokana, Jardiance, Steglatro — but **across all indications mixed together** (most is T2D, not CKD). After Farxiga’s generic launch, the signal is now partly noise. Invokana and Steglatro are near-zero. **No Baxfendy.** | Filter to CKD-labeled prescribing only. Split Farxiga brand vs generic. Add steroidal MRAs. Track Baxfendy once it appears in the data. |
| **How fast the HCP adopts new CKD therapies** (adoption speed) | One strong feature: how quickly a CKD patient got Farxiga from the same HCP. Rank 13 of 752, very predictive. **Nothing for HF drugs (no Entresto).** | Keep Farxiga. Add Jardiance, spironolactone/eplerenone, **Entresto** (your report’s LOE finding is exactly why), Invokana. |
| **New competitors** | **None.** Baxfendy approved May 2026, 4,712 HCPs writing it — model cannot see any of this. GLP-1 in HFpEF not tracked. | Add Baxfendy, GLP-1 with HF indication. Flag ASI trial zip codes as a risk/opportunity signal. |
| **Market event timing** | **None.** A Farxiga share of 0.6 in 2024 and 2026 are indistinguishable to the model. The pre-LOE Entresto brand adopter looks identical to a post-LOE generic switcher. | Add regime-state, event-response, and behaviour-change features anchored on CI report event dates. |

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

*Meeting update (Nov 2026): deferred. Josh views Baxfendy as an overlapping (hyperkalemia-risk) therapy, not a direct Kerendia competitor, and volume after about 6 months is too low to model. Monitor the ASI class instead (see Section 9).*

**Steroidal MRA parallel:** Your report’s ACC ECDP footnote (steroidal MRA as cost/tolerance alternative to nsMRA in HFpEF) confirms what we independently proposed in the adoption features: track how quickly HCPs adopt spironolactone/eplerenone for CKD patients. HCPs already using an MRA are the nearest-neighbour to Kerendia adoption.

### 5.4 EASi-KIDNEY halted (September 15, 2026)

**What you found:** Boehringer’s vicadrostat discontinued for futility. Clear runway until BaxDuo-CKD ~Feb 2028. But ASI trials exclude MRAs from enrollment, affecting 19% of US zip codes.

**Model gap:** No geographic signal. If an HCP’s patients are enrolled in an ASI trial (and therefore excluded from MRAs), a different NBA recommendation may be appropriate — but the model can’t see that.

**NBA 3.1 response:** Explore a zip-code-level trial-enrollment flag as an optional signal (C5). Lower priority, depends on whether zip-code data is cleanly available.

*Meeting update (Nov 2026): dropped. Josh's study-mapping analysis found no meaningful relationship between ongoing ASI trial sites and Kerendia providers, and only zip codes (not provider names) are available.*

### 5.5 GLP-1 in HFpEF guidelines (ESC / ACC 2026)

**What you found:** Semaglutide and tirzepatide are now Class IIa in HFpEF (BMI ≥ 30) in both ESC 2026 and the updated ACC pathway. Neither carries an FDA HF label, but prescribing is happening. Wegovy OOP is rising above $490/90 days, which may limit uptake.

**Model gap:** No GLP-1 feature. The same obese HFpEF + T2D patient who might get semaglutide is also eligible for Kerendia’s new HF indication. An HCP who already writes GLP-1 in HF patients is treating exactly this population.

**NBA 3.1 response:** Add GLP-1 (semaglutide, tirzepatide) NBRx feature filtered to HF-labeled indications (C4).

### 5.6 The time dimension — market events as prescribing breakpoints

Your CI report is a log of dated events that changed how HCPs should prescribe. Each event is also a **breakpoint** where the same raw number means something different on either side of it. The model currently has no way to see any of this.

The strongest feature in the competitor family today — `TIME_TO_ADOPT_FARXIGA` (rank 13 of 752) — is already an event-time feature: it measures how many days an HCP took to respond to a clinical event (patient CKD diagnosis) with a drug decision. We want to generalise the same logic to the market events in your report.

Three types of signal come out of this:

| Type | What it captures | Example |
| --- | --- | --- |
| **Regime state** | Which side of the event is this scoring cohort on? | `DAYS_SINCE_FARXIGA_LOE` (negative = pre-LOE, positive = post-LOE). Without this, a Farxiga share of 0.6 in October 2024 and in October 2026 look identical to the model — but in 2026 it is a generic-flooded market. |
| **Event response speed** | How fast did this HCP react to the market event? | `ENTRESTO_BRAND_ADOPTER_FLAG`: was the HCP's first Entresto Rx written before the LOE, when it was expensive? That HCP made an active evidence-based choice against a cost barrier — the exact profile expected to adopt Kerendia for HF. |
| **Behaviour change** | Did volume or mix shift around the event? | Log-ratio: Farxiga NBRx (3M post-LOE) / (3M pre-LOE). An HCP whose Farxiga volume tripled post-LOE was cost-constrained before; their patients now have freed-up OOP budget for Kerendia alongside generic dapagliflozin. |

**Proposed event-date reference table (one row per event, maintained centrally):**

| Event | Date | Regime feature | Response / change feature |
| --- | --- | --- | --- |
| Farxiga LOE | 2026-04-06 | `DAYS_SINCE_FARXIGA_LOE` | Brand vs generic volume ratio pre/post; days to first generic Rx |
| Entresto LOE (amorphous) | 2025-07-15 | `DAYS_SINCE_ENTRESTO_LOE` | `ENTRESTO_BRAND_ADOPTER_FLAG`; Entresto volume log-ratio |
| Baxfendy approval | 2026-05-15 | `DAYS_SINCE_BAXFENDY_APPROVAL` | Days from approval to first Baxfendy Rx (deferred: volume too low, per meeting) |
| EASi-KIDNEY halted | 2026-09-15 | `DAYS_SINCE_EASI_KIDNEY_HALT` | Dropped: no trial-site impact observed (per meeting) |
| Entresto fully generic (crystalline form) | 2027 (expected) | `DAYS_SINCE_ENTRESTO_FULL_GENERIC` | Future row: add once the date is confirmed (per meeting) |
| GLP-1 in HFpEF guidelines | 2026-08 (approx.) | `DAYS_SINCE_GLP1_HF_GUIDELINE` | GLP-1 HF NBRx pre/post guideline |

Adding new events in the future (e.g., BaxDuo-CKD readout ~Feb 2028, Jardiance LOE) requires only a new row in the reference table — no code changes. See Q7 and Q8 below.

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

### Market event signals (new family, ~10 features)

| What | Event anchor | Signal type |
| --- | --- | --- |
| Regime state at each cohort date | Farxiga LOE, Entresto LOE, Baxfendy approval, GLP-1 guidelines | Tells the model which competitive era the cohort belongs to. Same share value means different things before vs after each date. |
| Farxiga brand vs generic volume log-ratio (post/pre LOE) | Farxiga LOE (Apr 2026) | Cost-sensitive prescribers vs committed CKD brand users. HCPs with tripled generic volume post-LOE had previously cost-constrained patients. |
| Entresto brand adopter flag | Entresto LOE (Jul 2025) | First Rx before LOE = evidence-based HF adopter. Strongest proxy for Kerendia HF adoption propensity. |
| Days from Baxfendy approval to first Rx | Baxfendy approval (May 2026) | Early Baxfendy adopters are MRA-class-aware. Same logic as TIME_TO_ADOPT_FARXIGA applied to a market event date. |
| GLP-1 HF volume shift (post/pre guideline) | ESC/ACC GLP-1 HFpEF guidelines (Aug 2026) | HCPs who responded to the guideline treat the same obese HFpEF + T2D population as Kerendia's new HF indication. |

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
| Q7 | Are there other dated market events from the last two years — guideline publications, label expansions, key trial readouts — that you believe caused a visible step-change in HCP prescribing in the CKD/HF space? We have five events in the reference table; you likely track more. | Each additional event becomes a new feature family. Once the reference table pattern is in place, adding a new event requires only one new row — no code changes. |
| Q8 | Before the Entresto LOE (pre-July 2025), brand Entresto was ~$400+/month. Which specialties were writing the most brand Entresto in 2023–2024? We expect HF specialists and cardiologists — but if adoption was significant among nephrologists or PCPs, that changes how we interpret the brand-adopter flag. | The flag's predictive value for Kerendia HF adoption depends on whether pre-LOE Entresto writers overlap meaningfully with the Kerendia target segment. |

---

## 8. What happens next

| Step | Owner | When |
| --- | --- | --- |
| Meeting: review this doc, collect answers to Q1–Q8 | Josh + Wenjie | Nov 2026 |
| Confirm Baxfendy and GLP-1 data availability in IQVIA | Data engineering | After meeting |
| Build comorbidity features (H1–H3, M1–M3) | NBA team | Nov–Dec 2026 |
| Build competitor features (H4–H5, M4–M5, C1–C2) | NBA team | Nov–Dec 2026 |
| Build adoption-speed features (M6, C2 Entresto) | NBA team | Dec 2026 |
| Build market event features (regime state, event response, behaviour change) | NBA team | Dec 2026 |
| Feature selection + backtest review | NBA + BA | Jan 2027 |
| NBA 3.1 training | NBA team | Q1 2027 |

---

## 9. Meeting outcomes (Josh Buffington, November 2026)

### 9.1 Decisions

| Topic | What Josh said | Effect on NBA 3.1 |
| --- | --- | --- |
| CKD-scoped competitor features | SGLT2s are generally second-line for T2D-only patients. Capturing CKD is important to avoid over-counting | **Confirmed.** Keep CKD-scoped SGLT2 shares (H4/H5, C1) as the primary version |
| Diagnosis coverage in LAAD | Physicians often leave out diagnosis codes. Transaction coverage is much stronger than diagnosis coverage | **New caveat.** CKD-scoped features will undercount. Build both all-indication and CKD-scoped versions and let feature selection pick. Record the share of Rx with any diagnosis attached as a quality check |
| Entresto | Effectively generic since 2025. One formulation is patented until full generic in about 2027. It is often prescribed for HF before Kerendia | **Confirmed and expanded.** Track brand and generic Entresto together for HF adoption (C2) and keep the brand-adopter flag. Add the 2027 full-generic date to the event table |
| Baxfendy / ASI class | Overlaps with Kerendia through hyperkalemia risk, but it is not a direct competitor and is mainly prescribed for hypertension. About 6 months on market, so volume is too low to judge. Three ASI agents have approval timelines | **Deferred (C3).** No Baxfendy feature in NBA 3.1. Start from the weekly Baxfendy dashboard in Databricks. Later, expand monitoring to lorundrostat and the rest of the class |
| DPP-4 inhibitors | Still used but largely replaced by GLP-1s, and appear mutually exclusive with GLP-1 | **Excluded.** Do not track |
| GLP-1 (semaglutide, tirzepatide) | The new ACC/AHA guidance lists GLP-1 as a second-line add-on in HF. SGLT2 plus Kerendia together are first-line. GLP-1 matters in both T2D and HF populations. It can be co-prescribed with Kerendia; the risk is cost, since a provider may choose the GLP-1 if the patient cannot afford both | **Confirmed (C4), broadened.** Build GLP-1 NBRx share for both T2D and HF. Treat it as a same-population signal, not a replacement. It may interact with payer/OOP-cost features |
| Obesity prevalence | Correction: about 40% of US adults have BMI over 30 (not 60%). An internal Kerendia patient-record study found 56.3% of current Kerendia patients have obesity | Supports GLP-1 overlap as a relevant signal |
| SGLT2 plus Kerendia guideline pairing | First-line combination in HF per ACC/AHA | SGLT2 adoption should be read as **complementary** to Kerendia, not competitive. High CKD-scoped SGLT2 share is expected to be a positive signal |
| Pipeline: direct nsMRA competitor (readout expected April) | No data yet, not on market | **No feature.** The model is trained on history. Add an event row when it launches |
| Balcinrenone + dapagliflozin | Not needed now. The combination may affect Jardiance volume in about 2 years | **No feature.** Revisit for NBA 3.2+ |
| ASI trial-site mapping (C5) | No meaningful link between trial sites and Kerendia providers. Only zip codes are available | **Dropped** |
| Segment-level signals | Wenjie: the model can use a signal in specific HCP or patient segments to tailor promotion, even if it does not apply broadly | Narrow signals (e.g., GLP-1 in HF, Entresto brand adopters) are still worth building |

### 9.2 Status of pre-meeting questions

| # | Status | Answer / next step |
| --- | --- | --- |
| Q1 | Answered | Baxfendy is too early to model. Use the weekly Baxfendy dashboard for monitoring |
| Q2 | Partly answered | Entresto is actively prescribed in HF, often before Kerendia. The specialty split is still open; check it in LAAD |
| Q3 | Deferred | Revisit when Baxfendy volume can support a feature |
| Q4 | Answered | Balcinrenone is not needed now. Revisit in about 2 years for its Jardiance impact |
| Q5 | Answered | GLP-1 is not a replacement. It can be co-prescribed, and the risk is cost-driven prioritization |
| Q6 | Not discussed | Carry forward |
| Q7 | Answered | New events: Entresto full generic (about 2027), the direct-competitor readout (April), and future ASI approvals including lorundrostat |
| Q8 | Not discussed | Derive the 2023-2024 brand-Entresto specialty mix from LAAD ourselves |

### 9.3 Revised NBA 3.1 scope (competitor / event features)

* **Build:** CKD-scoped SGLT2 shares (Jardiance, Farxiga brand and generic split), all-indication variants as a fallback, Entresto adoption speed and brand-adopter flag, GLP-1 share (T2D and HF), and Farxiga LOE and Entresto LOE event flags (`DAYS_SINCE_*`).
* **Defer:** Baxfendy / ASI class features (monitor through the dashboard), the Balcinrenone combination, and the direct nsMRA competitor (add as an event when launched).
* **Drop:** ASI trial zip-code flag (C5) and DPP-4 tracking.

*Reference: full technical detail is in `90_competitor_comorbidity_summary_and_trends.md` (same folder). The CI report this doc references is “Competitive Intelligence Overview, Joshua Buffington PharmD, 9/23/26” (internal).*
