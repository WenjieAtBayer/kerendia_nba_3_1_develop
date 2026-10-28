# Market Access in NBA 3.1: Where We Are and What We Propose

**For:** Kerendia Market Access team  
**From:** NBA team  
**Purpose of the meeting:** show how access is used in the NBA model today (DRG), what we learned from MMIT, and what we propose for NBA 3.1, then **collect your concerns and suggestions** before we build anything  
**Status:** draft for discussion; nothing is decided. Updated after Market Access feedback on payer mapping (section 4.2)  
**Date:** October 2026

---

## 1. What we need from you

You know DRG, MMIT and Kerendia access far better than the data shows. We would like your view on four things:

1. **Does our reading of DRG and MMIT match how you read them?** (sections 3 and 4)
2. **Is the proposed set-up sensible from a Market Access point of view?** (section 5)
3. **What are we missing?** Payer events, coding conventions, known data issues, upcoming changes (for example the heart failure indication).
4. **The specific questions in section 6**, where your answer changes what we build.

A short note on the model, for context: NBA (Next Best Action) predicts, for each HCP and month, how many Kerendia prescriptions to expect, and how that changes with rep visits and digital touches. Access is one of the inputs that explains **why** two similar HCPs prescribe differently. We do not use access to judge payers, only to describe each HCP's patient environment.

---

## 2. The short version

| | Today (NBA 3.0) | What we propose (NBA 3.1) |
| --- | --- | --- |
| **Source** | DRG formulary history | **DRG for history (to Sep 2025) + MMIT going forward (from Oct 2025)** in one continuous access history |
| **Payer mapping** (IQVIA claims to formulary) | DRG: MASA mapping file (Jan 2025 snapshot). Our MMIT analysis so far: MMIT's own IQVIA bridge | **Bayer Payer Spine** (Galaxy Payer Spine IQVIA Bridge + Payer Hierarchy), as recommended by Market Access. Interim tables expected Monday; a broader enterprise solution is in progress |
| **What a feature says** | "Share of the HCP's **payer plans** where Kerendia is unrestricted / PA / Preferred ..." | "Share of the HCP's **patients** whose plan covers Kerendia unrestricted / with PA or ST / as Preferred ..." |
| **Drugs** | Kerendia, Jardiance, Farxiga | Same, plus Kerendia vs SGLT2 relative access |
| **Detail** | Status categories only | Adds MMIT detail: step requirements (e.g. SGLT2 first), PA criteria (eGFR, UACR), Bayer HPM groups, monthly access changes |
| **Weight in the model** | About 5% of what the model uses; best access feature ranks 25th of 752 | Goal: recover and modestly improve; access is a supporting signal, not a top driver |

The main message: **DRG and MMIT agree well on the simple questions (is Kerendia covered, is it restricted), and disagree on two definitions (Non-Preferred and step therapy).** We want to build on what they agree on, and we need your help on the two definitions. Following your feedback, we will also **replace MMIT's IQVIA bridge with the Bayer Payer Spine** and re-run the checks in this document on it.

---

## 3. Access in NBA 3.0 today (DRG)

### 3.1 How the features are built

| Step | What happens |
| --- | --- |
| 1. Which plans | For each HCP and month, every **paid** LAAD claim of the HCP (all products, not only Kerendia), so HCPs who do not yet write Kerendia also get an access picture |
| 2. Plan to formulary | IQVIA `PAYER_PLAN_ID` -> DRG plan through the **MASA file** `MASA_MA_Kerendia_IQVIA_Access_Mapping_at_Plan_Level_01_28_25.xlsb` (3,680 payer plans -> 1,300 DRG plans) |
| 3. Status | DRG `ANLT_DRG_FRMLRY_HIST` **for that month**: `PHARMACY_ST_CRITERIA` (Unrestricted, Covered (PA) without ST, Covered - ST or PA/ST, Not Covered, Unspecified) and `DUAL_COVERAGE_NOMENCLATURE` (Preferred, Covered, Non-Preferred, Not Covered, Specialty) |
| 4. Feature | Share of the HCP's distinct payer plans in each status, for the month and over the last 12 months (`PCT_PLANS_KERENDIA_UNRESTRICTED`, `..._COVERED_LOOKBACK`, ...) |

Two points worth knowing:
* **The status is monthly; only the plan mapping is fixed.** The MASA file is used only to link IQVIA plans to DRG plans. Its `KERENDIA ACCESS (FINGERTIP)` column is not used. The DRG status itself moves every month (on mapped plans, Kerendia status changed for about 1.5% of plans per month in 2024-2025).
* **Each plan counts once**, whether it covers one of the HCP's patients or hundreds.

### 3.2 What the model keeps

* 44 access features are used; together they carry **about 5%** of what the model relies on.
* The strongest are Kerendia **covered over the last 12 months** (rank 25 of 752) and Kerendia **unrestricted** (rank 28). Jardiance and Farxiga access features rank lower (152 and 189 at best).
* LAAD rejected-claim features (e.g. running total of rejected Kerendia claims, rank 11) also carry access information and will stay in the model.

### 3.3 Limits of the current set-up

| Limit | Effect |
| --- | --- |
| DRG ends in **November 2025** | No access data for 2026 without MMIT |
| MASA plan mapping is a **Jan 2025 snapshot** | Plans created or re-pointed after Jan 2025 drop out (in Oct-Nov 2025, 12% of paid claims map only through MMIT, 3.5% only through DRG) |
| DRG month labels are inconsistent in 2025 | Some months have two files and some none; we re-derive the month from the file date |
| Plan count, not patients | A plan with one patient weighs the same as a plan with hundreds |
| Status categories only | No step product, PA criteria or lab requirements |

---

## 4. What we learned about MMIT

### 4.1 What we have and how we link it

* **Full weekly MMIT feed from October 2025** (202510); Bayer HPM (`Bayer_ChronicKidneyDisease_HPM_Pharm`) from **January 2026**. Earlier uploads (Jun-Aug 2025) were a 31-drug pilot without Kerendia.
* **Link to claims (so far):** MMIT's own `bronze_iqvia_bridge` maps IQVIA payer plans to MMIT organisations, refreshed with every weekly feed. When one IQVIA plan maps to several MMIT plans, we take the formulary with the **most lives** in that month. We will replace this with the Bayer Payer Spine (section 4.2).
* We read the **Chronic Kidney Disease** indication for PA / ST detail, and the CKD therapeutic class for status.
* Coverage: about **90% of Kerendia claims** (Oct 2025 - Aug 2026) find an MMIT status; the rest have no payer match (6.5%) or no Kerendia row for the formulary (4.1%, rising to about 7% after the March 2026 drop in formulary count from 2,133 to 2,036).

### 4.2 Payer mapping: moving to the Bayer Payer Spine

**Your feedback.** The MMIT-to-IQVIA mapping in MMIT's bridge does not match how Bayer masters payers across the two sources. It is an acceptable stopgap, but NBA should use the **Bayer Payer Spine**.

**What we will receive.** The payer data support team will provide the **Galaxy Payer Spine IQVIA Bridge and Payer Hierarchy** (tables and / or a mapping file). An updated set of Payer Spine tables arrives at the end of this week, and we expect it **on Monday**.

**Caveats from the support team:**
* This is an **interim** source. It should not become the permanent foundation in Databricks; a broader solution is being built.
* Our results may differ slightly from **Galaxy AI and Athena**, because those apply **Kerendia-specific business rules** to the hierarchy (for example, patient assistance and copay card plans).

**What this changes for us:**
* All coverage and agreement numbers in this document used the **MASA file** (DRG) and **MMIT's bridge** (MMIT). We will re-run them on the Payer Spine once it arrives: match rate, DRG vs MMIT agreement (4.3) and the patient-basis test (4.7).
* MMIT's bridge will be kept only as a cross-check, not as the production mapping.
* We will build the mapping step so the interim spine can later be swapped for the enterprise solution without changing the features.
* We would like to apply the same Kerendia business rules as Galaxy AI and Athena, so NBA numbers reconcile with what you see (questions B7-B10).

### 4.3 Do DRG and MMIT tell the same story? (overlap Oct-Nov 2025)

For the two months covered by both, we compared DRG and MMIT on the **same IQVIA payer plan and month**, weighted by paid claims. Mapping used: MASA file for DRG, MMIT's bridge for MMIT (to be repeated on the Payer Spine).

| Question | Kerendia | Jardiance | Farxiga |
| --- | --- | --- | --- |
| Is the drug covered? | 96% | 100% | 98% |
| Preferred / Covered or Non-Preferred / Not Covered | 90% | 95% | 92% |
| Same tier number (Tier 1-5) | 91% | 92% | 91% |
| Unrestricted (covered, no PA, no ST)? | 93% | 92% | 91% |
| Any PA or ST? | 91% | 92% | 89% |
| Quantity limit? | 96% | 95% | 93% |
| **DRG 5-level status (`DUAL_COVERAGE_NOMENCLATURE`)** | **60%** | 94% | 81% |
| **DRG PA vs ST split (`PHARMACY_ST_CRITERIA`)** | **67%** | 91% | 89% |

**Where they disagree for Kerendia (definitions, not random noise):**
* **Non-Preferred.** 29% of claims are on plans DRG calls **Non-Preferred (Tier 3/4)** and MMIT calls **Covered (PA/ST)** with raw status Tier 3/4. MMIT's rollup has no Non-Preferred level, but the tier numbers agree.
* **Step therapy.** MMIT flags a step on **44%** of Kerendia claims, DRG on **5%**. Most of the gap (35% of claims) is plans DRG records as **PA + QL** and MMIT codes with a step, mostly MMIT `Preferred (PA/ST)` Tier 3. Our guess: MMIT codes the label prerequisite (for example background ACEi / ARB) as a step, while DRG records it as part of the PA. **We need your view (question A2).**
* **By channel.** Agreement on PA is 99% in Medicare Part D and FFS Medicaid, but 80% in Commercial.

### 4.4 Bayer HPM

* HPM gives each formulary a Bayer access group every month (e.g. Preferred - Unrestricted, Preferred (PA to Label), Covered (Step[s]), PA+, APR, Medical Exception).
* It uses the same vocabulary as the `KERENDIA ACCESS (FINGERTIP)` label in the MASA file (both have **APR**), but it is refreshed monthly.
* HPM and the MMIT rollup **disagree on what "Preferred" means for 119 formularies.**
* We still have a mapping issue on our side (about 73% of claims fall into an "Other" HPM group); we will fix this before drawing conclusions.

### 4.5 What changes over time

* Kerendia access is **improving**: about two improvements for every deterioration since Oct 2025.
* **Farxiga access deteriorated sharply in April-July 2026**; by July-August 2026 it affected plans covering about a third of Kerendia claims. We would like to know whether this is the generic dapagliflozin event (question C1).

### 4.6 Which access signals relate to new Kerendia patients

On Kerendia writers (Oct 2025 - Aug 2026), we checked how well each MMIT feature on its own separates HCPs who start a new Kerendia patient next month from those who do not:

* **Share of commercial patients** is the most stable positive signal.
* **Any restriction (PA, ST or QL)** is the clearest signal in the expected direction: more restricted plans, fewer new patients.
* **Step requires SGLT2** looked strong at first, but most of it reflects HCP size.
* Bayer HPM and access-change features show little signal on their own so far (short history).

All signals are modest. This matches NBA 3.0: access helps explain differences between HCPs, it does not drive the model.

### 4.7 Plans or patients?

You told us Market Access reads MMIT on a **patient** basis. We tested this on DRG history (March-May 2025):

* Patient-based and claim-based shares are almost identical; the NBA 3.0 plan count is quite different from both.
* Patient-based shares carry **about 1.5x the signal** of the plan count for unrestricted, PA / ST and Preferred, and move less from month to month for reasons unrelated to real access changes.

So we propose to switch to patients (section 5).

---

## 5. What we propose for NBA 3.1

### 5.1 One access history: DRG then MMIT

* **DRG up to September 2025, MMIT from October 2025**, in one table at IQVIA payer plan x month x drug. MMIT covers more claims in the overlap, so we switch at the first full MMIT month (to be confirmed on the Payer Spine).
* **Payer mapping through the Bayer Payer Spine** for MMIT, and for the DRG history too if the spine can link to DRG plans (question B10), so 2023-2026 uses one mapping.
* A flag records which source each month comes from, and we check that the switch itself does not create artificial "access changes".

### 5.2 Patient basis

* **Patients:** every LAAD patient with a paid claim with the HCP in the month counts once (split equally if the patient has more than one plan that month).
* **All the HCP's patients**, not only Kerendia patients, so non-writers also get an access picture. We will also test a narrower basket (CKD / T2D patients).
* The NBA 3.0 plan-count version is kept only as a comparison.

### 5.3 Features

**A. Continuous from 2023 (DRG history + MMIT), for Kerendia, Jardiance and Farxiga**

| Feature | Built on |
| --- | --- |
| % of patients whose plan covers the drug / does not cover it | Both sources agree 96-100% |
| % of patients with unrestricted access | 91-93% agreement |
| % of patients with any PA or ST | 89-92% agreement |
| % of patients with a quantity limit | 93-96% agreement |
| % Preferred / Covered or Non-Preferred / Not Covered | 90-95% agreement |
| % by tier number (Tier 1-2, Tier 3, Tier 4+) | about 91% agreement; replaces DRG "Non-Preferred" |
| Same shares over the last 12 months | |
| Kerendia vs SGLT2 relative access (e.g. % of patients where Kerendia is worse than Jardiance) | |
| Plan mix: % commercial / Medicare / Medicaid, top PBMs | LAAD + plan data |
| Access improved / worsened in the last 3 months | Within each source, with a guard at the switch month |

We would **not** carry over the NBA 3.0 features "Non-Preferred", "Covered (PA) without ST" and "Covered - ST or PA/ST" as they are, because DRG and MMIT define them differently for Kerendia (section 4.3).

**B. MMIT only (from Oct 2025 / Jan 2026)**

| Feature | Notes |
| --- | --- |
| % of patients where the step requires an SGLT2 first | MMIT step detail |
| PA burden: number of criteria, eGFR / UACR requirements, PA ARS rating | Links to the lab features already in the model |
| Bayer HPM group shares | From Jan 2026, after our mapping fix |
| MMIT step-therapy flag (as MMIT codes it) | Kept separate from the continuous PA / ST feature |
| Lives-weighted access in the HCP's ZIP / CBSA / state | Fallback for HCPs with no mapped plan |

Medical-benefit coverage is low priority for an oral drug, and we do not plan to use it.

### 5.4 How we will decide what stays

We add the access features in steps and keep a step only if it improves the model on later months it has not seen:

1. Model without access features.
2. Plus NBA 3.0-style rejected-claim features.
3. Plus the continuous access features (A), patient-based; compared with the plan-count version.
4. Plus the MMIT-only features (B).

Access features will be refreshed **weekly** between monthly model runs, so recommendations can react to formulary wins and losses.

---

## 6. Questions for you

### A. Definitions

| # | Question | Why it matters |
| --- | --- | --- |
| A1 | **Which source should define "Preferred" for Kerendia: the MMIT rollup or Bayer HPM?** They disagree on 119 formularies. | Decides the Preferred feature |
| A2 | **Step therapy:** MMIT flags a step on 44% of Kerendia claims, DRG on 5%, mostly plans DRG records as PA + QL. Is MMIT coding a label prerequisite (e.g. ACEi / ARB) as a step? For Kerendia, which definition reflects the real barrier for the HCP? | Decides whether PA and ST can be separate features |
| A3 | **Non-Preferred:** DRG Non-Preferred (Tier 3/4) is MMIT "Covered (PA/ST)" with Tier 3/4. Is the **tier number** the right common language, or is there a better way to get Non-Preferred from MMIT? | Decides the tier features |
| A4 | What do **HPM** and the code **APR** stand for? Is HPM the monthly successor of the FINGERTIP label in the MASA file? | Decides how we name and group HPM |
| A5 | **Quantity limits:** NBA 3.0 treats QL-only as unrestricted. Is a QL a real barrier for Kerendia (one tablet a day)? | Decides whether QL counts as a restriction |
| A6 | Should **Not Listed** be treated like Not Covered? | Small effect on coverage shares |

### B. Data and mapping

| # | Question | Why it matters |
| --- | --- | --- |
| B1 | Is the MASA mapping file maintained after Jan 2025? Is there a newer version? | Better DRG history for 2025 |
| B2 | When one IQVIA plan maps to several MMIT plans, MMIT's bridge forces us to pick one (we take the most lives). Does the Payer Spine give one formulary per IQVIA plan, or should we split by lives? | Linkage rule |
| B3 | Do you know why the Kerendia formulary count dropped from 2,133 to 2,036 in March 2026? | Data quality |
| B4 | How should PBM-unspecified, discount-card and voucher plans be treated (exclude, or a separate group)? | Denominators |
| B5 | Commercial plans agree less between DRG and MMIT (PA 80% vs 99% in Medicare). Is that expected? | Confidence in commercial features |
| B6 | Is lives by plan and state in MMIT reliable enough for a geographic fallback? | Coverage for HCPs without mapped plans |
| B7 | **Payer Spine keys:** which IDs does the Spine IQVIA Bridge carry (IQVIA `PAYER_PLAN_ID` to which Bayer payer / plan IDs), and how do they link to MMIT (`OrgId` / `FormularyId`) and to DRG plans? | How we join the spine |
| B8 | **Kerendia business rules:** which rules do Galaxy AI and Athena apply to the hierarchy (e.g. patient assistance and copay card plans)? Can we get them written down so NBA can apply the same ones? | Reconcile NBA with Galaxy AI / Athena |
| B9 | **Interim period:** how often will the interim spine tables be refreshed, and when is the broader Databricks solution expected? | Weekly access refresh; when to switch |
| B10 | Can the spine also be used for the **DRG history** (replacing the Jan 2025 MASA file), or was the MASA file itself built from the spine? | One mapping for 2023-2026 |

### C. Market events

| # | Question | Why it matters |
| --- | --- | --- |
| C1 | Is the **Farxiga deterioration (April-July 2026)** linked to generic dapagliflozin? Should we treat it as a market event? | Competitor access feature |
| C2 | Which events should we flag: January plan-year resets, Medicare Part D changes, large PBM contract changes? | Avoids reading events as HCP behaviour |
| C3 | **Heart failure indication:** we currently read CKD-indication PA / ST. Will HF coverage differ by plan, and should NBA 3.1 read both? | Indication scope |
| C4 | Any Kerendia access wins or losses expected in 2027 that we should prepare for? | Planning |

### D. Use of the features

| # | Question | Why it matters |
| --- | --- | --- |
| D1 | Is our **patient** definition close to yours (patients seen by the HCP in the month, split across their plans)? Or do you use lives or Kerendia-eligible patients? | Core definition |
| D2 | Which comparators matter most: Jardiance and Farxiga, also Invokana, ACEi / ARB? | Competitor set |
| D3 | Which MMIT details are most meaningful in your experience: step product, PA criteria, eGFR / UACR requirements, HPM? | Priorities for section 5.3 B |
| D4 | Would an "access improved for this HCP's patients" signal be useful for rep messaging? | Possible NBA trigger |

---

## 7. Answers (to fill in during the meeting)

| # | Answer | Owner | Follow-up |
| --- | --- | --- | --- |
| A1 | | | |
| A2 | | | |
| A3 | | | |
| A4 | | | |
| A5 | | | |
| A6 | | | |
| B1 | | | |
| B2 | | | |
| B3 | | | |
| B4 | | | |
| B5 | | | |
| B6 | | | |
| B7 | | | |
| B8 | | | |
| B9 | | | |
| B10 | | | |
| C1 | | | |
| C2 | | | |
| C3 | | | |
| C4 | | | |
| D1 | | | |
| D2 | | | |
| D3 | | | |
| D4 | | | |

---

## Appendix: where the detail is

| Topic | Document |
| --- | --- |
| Full technical plan | `MMIT_EDA_Checks/07_MMIT_NBA_Readiness_Plan.md` |
| How MMIT is joined to claims, step by step | `MMIT_Access_Features_Client_Walkthrough.md` |
| MMIT checks 1-6 (coverage, HPM, signal, status changes) | `MMIT_EDA_Checks/00_MMIT_Claim_Level_EDA_Client_Summary.md` and files 01-06 |
| DRG vs MMIT comparison | `MMIT_EDA_Checks/DRG_MMIT_History_Linkage_Checks` |
| Bayer Payer Spine (Galaxy Payer Spine IQVIA Bridge + Payer Hierarchy) | Interim tables / mapping file from the payer data support team, expected Monday |

**Terms used:** *LAAD* = IQVIA longitudinal prescription claims; *paid claim* = claim approved by the payer; *lives* = enrolled members of a plan; *new patient (NBRx)* = first Kerendia prescription for a patient; *Payer Spine* = Bayer's internal master mapping of payers and plans across data sources.
