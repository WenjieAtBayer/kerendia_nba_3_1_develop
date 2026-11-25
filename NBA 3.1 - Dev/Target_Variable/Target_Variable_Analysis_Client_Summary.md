# Client Summary: NBA 3.1 Target Variable Analysis (LAAD and BlinkRx, Q1 2026)

## 1. Target variable: Paid NBRx

The NBA 3.1 HCP model predicts which HCPs will write a **new paid Kerendia prescription (Paid NBRx)** in the next month.

* **Paid NBRx:** a paid Kerendia claim for a patient who is new to Kerendia. That means the patient's first Kerendia claim, or the first after more than 365 days without one. Only the first claim per patient per day counts.
* **Target (New Writer):** an HCP with at least one Paid NBRx in the month.
* **Scope:** NBA 3.1 HCP universe of 294,726 HCPs, prediction months Jan to Mar 2026 (training cohorts c19 to c21).

## 2. Ablation objectives

1. Size the target: how many HCPs are New Writers each month.
2. Size the "near-miss" group: HCPs whose new patients had a **rejected or reversed** claim (Rejected New Writers), and how much it overlaps with New Writers.
3. Test whether **market access features (FTP and copay)** can tell Rejected New Writers apart from other HCPs.
4. Check whether **BlinkRx**, a pharmacy channel outside IQVIA LAAD, adds paid or non-paid writers that LAAD misses.

## 3. LAAD data source and results

**Source:** IQVIA LAAD prescription claims for Kerendia, Jan 2025 to Mar 2026 (12 months of history before Q1). 1.61M claims: 1.12M paid (PD), 264K rejected (RJ), 225K reversed (RV). The same new-patient rule is applied separately to each claim type.

**Paid Writers (target)**

| Month | Paid Writers | Paid NBRx |
| --- | --- | --- |
| Jan-26 | 5,625 | 8,138 |
| Feb-26 | 5,877 | 8,693 |
| Mar-26 | 6,194 | 9,290 |
| Q1 distinct HCPs | 12,815 | 26,121 |

**Non-paid Writers (rejected or reversed NBRx)**

| Month | Non-paid Writers | Non-paid NBRx | Type 1 Writers (mix of Paid and Non-paid NBRx) | Type 1 Writers Paid NBRx | Type 1 Writers Non-paid NBRx | Type 2 Writers (only Non-paid NBRx) | Type 2 Writers NBRx |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Jan-26 | 8,521 | 14,431 | 3,097 | 5,255 | 7,261 | 5,424 | 7,170 |
| Feb-26 | 7,833 | 12,759 | 3,052 | 5,425 | 6,644 | 4,781 | 6,115 |
| Mar-26 | 8,069 | 12,990 | 3,264 | 5,883 | 6,975 | 4,805 | 6,015 |
| Q1 distinct HCPs | 16,723 | 40,180 | 6,724 | 16,563 | 20,880 | 12,736 | 19,300 |

*Type 1 and Type 2 are set per month. Type 1 Writers Paid NBRx is the paid NBRx those HCPs wrote in the same month. Type 1 Writers Non-paid NBRx and Type 2 Writers NBRx count non-paid NBRx, so together they equal Non-paid NBRx. In the Q1 row, NBRx is the quarter total and writers are distinct HCPs. An HCP can be Type 1 in one month and Type 2 in another, so the Type 1 and Type 2 Q1 counts add up to more than 16,723.*

* **Target size:** about 2% of the universe are Paid Writers each month (12,815 distinct HCPs, 4.3%, over Q1).
* **More HCPs have non-paid new patients than paid ones:** 7.8K to 8.5K per month, writing 12.8K to 14.4K non-paid NBRx, more than the 8.1K to 9.3K paid NBRx.
* **Most non-paid writers get nothing paid that month (Type 2):** 60 to 64% of non-paid writers each month have no paid NBRx. They write about 1.3 non-paid NBRx each, against 2.1 to 2.3 for Type 1 writers.
* **Type 1 writers are the core paid writers:** they also write about 63% of all Paid NBRx (16,563 of 26,121 in Q1).
* **Market access features add little:** FTP and copay features separate Rejected New Writers from the rest moderately (best single feature AUC 0.70). This is mostly because rejected HCPs are already Kerendia writers. Prior writing alone predicts them with AUC 0.909, and adding FTP and copay raises it only to 0.910. The features can't tell a rejected new patient from a paid one (AUC 0.55 or lower).
* **Validation:** Paid NBRx matches the NBA 3.1 target variable for 99.99% of HCP-months, and a separate recount gives the same writer counts.

### 3.1 Finding: what a Paid-NBRx-only target misses

If NBA 3.1 uses only Paid NBRx as its target, there are two problems:

1. **Type 2 writers are missed entirely.** In a month where they write only non-paid NBRx, their target is 0, so the optimization that builds the field lists for each channel will not prioritise them. This is 4.8K to 5.4K HCPs per month (12,736 distinct HCPs in Q1) writing 6.0K to 7.2K non-paid NBRx per month (19,300 in Q1). These HCPs are actively trying to start new Kerendia patients, but access is blocking them.
2. **Type 1 writers' target understates their potential.** In Q1 they wrote 16,563 paid NBRx but 20,880 non-paid NBRx, so the paid target counts only about 44% of their new-patient activity (42% in Jan, 45% in Feb, 46% in Mar). The model ranks them on paid outcomes only, not on their full NBRx potential.

If the aim is to build field lists on Paid NBRx only, the current target is fine. If the aim is to reach every HCP trying to start new patients, including those blocked by access, the target needs to include non-paid NBRx, or Type 2 writers need a separate track.

## 4. BlinkRx data source and results

**Source:** BlinkRx dispense data for Kerendia (BlinkRx's own pharmacy records, Mar 2024 to Nov 2026, 6,200 new-to-Blink scripts from 6,153 patients). BlinkRx is not part of IQVIA LAAD, and its patient IDs can't be linked to LAAD. A script counts as NBRx if it is the patient's first BlinkRx script or comes 12+ months after the previous one. Each patient is counted once, labelled by the outcome of that script:

* **Paid:** coverage code P.
* **Non-paid:** reversed (R) or no coverage outcome recorded (labelled ABANDON).

| Month | BlinkRx Paid Writers | Paid NBRx | BlinkRx Non-paid Writers | R NBRx | ABANDON NBRx | Non-paid, no Paid |
| --- | --- | --- | --- | --- | --- | --- |
| Jan 2026 | 89 | 114 | 100 | 109 | 27 | 79 |
| Feb 2026 | 142 | 171 | 112 | 105 | 46 | 87 |
| Mar 2026 | 173 | 208 | 130 | 120 | 36 | 97 |
| Q1 distinct HCPs | 353 | 493 | 291 | 334 | 109 | 246 |

* **BlinkRx is small:** 936 NBRx in Q1, equal to about 3.6% of LAAD's Q1 Paid NBRx (26,121). Only 53% are paid.
* **Paid writers are growing:** 89 to 173 from Jan to Mar. Non-paid writers grow more slowly (100 to 130).
* **Validation:** monthly totals match the production BlinkRx table (one difference of 1 NBRx in Feb), and a separate recount gives the same writer counts.

### 4.1 Overlap analysis (BlinkRx vs LAAD)

| Group | Q1 BlinkRx writers | Also LAAD writers | BlinkRx only | BlinkRx share of LAAD writers |
| --- | --- | --- | --- | --- |
| Paid (BlinkRx P vs LAAD Paid NBRx) | 353 | 262 (74%) | 91 | 2.0% |
| Non-paid (BlinkRx R/ABANDON vs LAAD RJ/RV) | 291 | 216 (74%) | 75 | 1.3% |

* **Most BlinkRx writers are already in LAAD:** 74% of BlinkRx paid and non-paid writers are also LAAD writers of the same type. Within a single month the share is 44 to 62%.
* **BlinkRx adds few new HCPs to the target:** 45 to 80 paid writers per month are BlinkRx only. That would raise New Writers by about 0.8 to 1.4% per month (91 HCPs, 0.7%, over Q1).
* **Overlap is growing:** shared paid writers rose from 44 to 95 between Jan and Mar, in line with BlinkRx growth.
* **Caveat:** overlap is measured per HCP and month, not per patient, because BlinkRx and LAAD patient IDs can't be linked.

### 4.2 Takeaways

**Bottom line:**

* LAAD Paid NBRx captures nearly all of the NBA 3.1 target population.
* LAAD data also captures about 74% of BlinkRx paid writers and about 74% of BlinkRx non-paid writers.

**Open decision:**

* **Option 1:** add BlinkRx Non-paid NBRx and BlinkRx Non-paid NBRx share as two separate features in the NBA 3.1 model.
* **Option 2:** add BlinkRx-only NBRx to the target variable.