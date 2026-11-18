# Colocation Data Assessment (NBA 3.1)

## Purpose
NBA 3.0 measures colocation only by **physical building** (same latitude, longitude and premise in MDM_STG_HCP_ADDR). For NBA 3.1 we want to know which other sources can tell us that two HCPs work together, for example in the same practice, the same hospital group or the same IDN (health system). This document lists those sources, what each one holds, how well it covers the 3.1 universe, and which colocation features it could support. It is a data assessment that feeds the readiness plan. Nothing here has been built yet.

## Method (2026-11-18)
* Population: NBA 3.1 universe `HCP_Universe_without_call_hcps` (294,727 PROVIDER_IDs). 294,578 (99.9%) map to a BH_ID through `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`.
* Outcome for the signal checks: Kerendia writer in LRx V7 (PERIOD_TYPE 'W', NBRX > 0, 2025-10-24 to 2026-10-23). Baseline 9.7% (28,628 HCPs)
* Peer writers: other universe HCPs in the same group with Kerendia NBRx > 0 in the 3 months **before** the outcome window (2025-07-25 to 2025-10-23). The HCP is always excluded from their own count.
* "New-writer view": only HCPs with no Kerendia LRx activity in that prior window. It shows whether a feature predicts new adoption, not just continued writing.
* These are one-feature-at-a-time checks, not model lift.

## 1. Sources Found

**Usable for colocation feature?** "Yes" only if all three hold: (1) **can be created**, meaning the source links an HCP to exactly one group (or supplies the writers) in a single checked one-to-one join on BH_ID / PROVIDER_ID or the BEST_AFFL rank-1 BHO_ID, with enough coverage; (2) **not redundant**, meaning it does not repeat a feature already in the model or another source in this table; (3) **adds value**, meaning the signal check in section 3 shows a clear lift. "No" if any one fails or has not been shown. The PROVIDER_ID to BH_ID mapping is a common step for every source and is not counted as a linkage.

| # | Source | Grain / key | What it holds | Coverage on the 3.1 universe | Status | Usable for colocation feature? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `query_output/kerendia_nba_3_0_hcp_model_hcp_profile_geocoding_addreess_information` (snapshot of `PHCDW_STG.MDM_STG_HCP_ADDR`) | BH_ID x address | Latitude, longitude, premise (building), sub-building | 282,465 HCPs (95.8%) have a geocoded building | **In use** (3.0 building colocation) | **Yes** (keep existing). Created: direct BH_ID to one address. Not redundant: practice and building flag different HCPs (only 20,843 flagged by both, section 3.3). Value: NUM_HCPS_IN_BUILDING is rank 8 of 752; 14.6% writer rate with a building peer writer only vs 7.5% |
| 2 | `pace_ker_in_house_schema.cust_mdm_best_affl_publish_pd_outp_static` (Kerendia BEST_AFFL, Q4-2026) | BH_ID x BHO_ID, ranked by BRAND_RANK | Kerendia-specific best account per HCP, account type, class of trade, EMPLOYMENT_FLAG, affiliation scores | 4,374,496 rows, 1,368,947 HCPs. BRAND_RANK = 1 gives a best account for **282,881 universe HCPs (96.0%)** | Used only for specialty (nb 20). **Not used for colocation** | **Yes** (L1 practice features). Created: BRAND_RANK = 1 gives exactly one account per HCP (0 of 1,368,947 have more than one). Not redundant: reaches 44,279 HCPs with no building peer writer. Value: 15.7% vs 7.4% (new-writer 7.4% vs 4.4%); top share quintile 19.0% |
| 3 | `pace_ker_in_house_schema.mdm_stg_acct_hrchy_ker` (MDM account hierarchy, Q4 2026) | L1 child account (BHO_ID) | L1 site, L2 local group, L3 HQ, L4 IDN, with IDs, names and addresses | 563,271 L1 accounts, each with exactly one L4. Through BEST_AFFL: 282,881 HCPs linked to L1, **210,425 (71.4%) sit in a real IDN** (L4 not 'NA' / 'Multiple Doctors'), across 33,062 IDNs | **Not used.** HCP columns (L0_HCP_BH_ID, KERENDIA_RANK) are empty, so HCPs must be linked through BEST_AFFL BHO_ID = L1_CHILD_BHO_ID | **Yes** (L4 IDN peer share only). Created: one join BEST_AFFL rank-1 BHO_ID = L1_CHILD_BHO_ID (unique, all 1,368,947 match one row). Value: IDN top share quintile 14.9% vs about 7.5%, a wider peer group than L1. Not used: L2 (redundant, same as L1); L3 (signal shown but overlap with L1 not checked); IDN presence flag (flat, 9.1% vs 9.1%) |
| 4 | `pace_ker_in_house_schema.mdm_stg_acct_prfl_ker` (account profile) | BHO_ID | HCO_TYPE, class of trade, COUNT_BEDS, COUNT_MD_DO, COUNT_MEDSTAFF, TOP_PARENT, VA_DOD_AFFILIATED, EMR vendor/product 1-7 | Matches 89,133 of 90,861 best accounts (98.1%). COUNT_MD_DO filled for 46,662 (51.4%), COUNT_BEDS for 5,449 (6.0%, hospitals only) | **Not used** | **No.** Can be created (one join on the best-account BHO_ID), but it is account context, not peer colocation. Partly redundant with practice size from source 2. COUNT_MD_DO 51.4% and COUNT_BEDS 6.0% filled; signal not checked |
| 5 | `pace_ker_in_house_schema.ph_hs_metrics_static` (PACE health-system metrics) | bho_id (all levels), with L3_parent / L4_parent | Per account: HF-only, HF+CKD, CKD patients; H1 hospital count; A/B call-plan segment counts for CARD, NEPH, ENDO, PCP; Kerendia, Entresto, SGLT2 and sMRA writer counts; formulary status and win date | 1,141,708 accounts. Contains every L3 (63,958) and L4 (33,062) account of the universe | **Not used.** Ready-made account-level aggregates :citation[knowledge_snippet.d66ed76e-5de6-4bb6-81ee-cd410b07eb42] | **No.** Writer counts repeat the peer writer features built from sources 2 + 3 + 9 and may include the outcome window (leakage). Patient and formulary fields are account context, not colocation. Signal not checked |
| 6 | `whc_data_zone1_prod.mdm_hcp_hco_affl` (UC proxy for `MDM_STG_HCP_ACCT_AFFL`) | BH_ID x BHO_ID, all affiliations | Every account an HCP is affiliated with, plus class of trade, specialty, description | 276,246 universe HCPs, 1,337,044 HCP-account pairs | Used for AFFL_COUNT (nb 07). **Not used for colocation** | **No.** Many accounts per HCP (median 357 peer links), so it cannot separate HCPs. Account counts already used as AFFL_COUNT (nb 07) |
| 7 | `kerendia_nba_3_pace.child_parent_link` / `parent_child_link_base_table_v1` | NPI -> practice / parent NPI | Practice ID, parent (lead) HCP, practice DBA and NPI, address, segment | 11,557 NPIs in 1,615 practices. Only **3,141 universe HCPs (1.1%)** appear as a child | Uploaded file (Dec 2025). Too small for a universe-wide feature | **No.** Covers only 1.1% of the universe and repeats the practice grouping from source 2 |
| 8 | `kerendia_nba_3_pace.new_writers_hcp_address` | NPI | BHO_ID plus the L1-L4 level matched by a top-down cascade | 15,223 HCPs (new writers only) | Not usable as a feature source. The cascade logic is reusable | **No.** New writers only; multi-level cascade match |
| 9 | `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` | PROVIDER_ID x week | Kerendia and market-basket LRx with SPECIALTY_GROUP, INDICATION_GROUP, PRODUCT_CLASS | All writers | **In use.** Supplies the "who writes" side of every colocation feature | **Yes** (writer side only). Required input for every peer writer feature; direct PROVIDER_ID; does not define groups |

### 1.1 Explanation: What We Are Trying to Achieve

**The idea.** A colocation feature answers one question: *does this HCP work alongside colleagues who already prescribe Kerendia?* HCPs who see colleagues using a drug are more likely to start using it themselves (peer influence). NBA 3.0 defines "colleagues" only as HCPs in the **same building**. For NBA 3.1 we test other ways to define who an HCP's colleagues are: the same **practice**, the same **local group**, the same **regional HQ**, or the same **IDN (health system)**.

**Every colocation feature needs two inputs:**
1. **A grouping**: which HCPs belong together (sources 1, 2 and 3).
2. **A writer list**: which of those HCPs prescribed Kerendia recently (source 9).

The feature is then the **count** or the **share** of the *other* HCPs in the group who wrote Kerendia in the last 3 months. The HCP themself is never counted.

**Worked example.** Practice A has 6 universe HCPs (Dr 1 to Dr 6). Dr 2 and Dr 5 wrote Kerendia in the last 3 months.

| HCP | Other HCPs in practice | Peer writers (self excluded) | Peer writer present? | Peer writer share |
| --- | --- | --- | --- | --- |
| Dr 1 | 5 | 2 (Dr 2, Dr 5) | Yes | 2 / 5 = 40% |
| Dr 2 | 5 | 1 (Dr 5) | Yes | 1 / 5 = 20% |
| Dr 3 | 5 | 2 (Dr 2, Dr 5) | Yes | 2 / 5 = 40% |

The same calculation is done for each grouping (building, practice, HQ, IDN); only the definition of "group" changes.

### 1.2 Explanation: How the Signal Check Works

The signal check asks: *if we had built this feature in the past, would it have pointed to the HCPs who went on to write Kerendia?*

1. **Take the HCPs**: all 294,727 HCPs in the NBA 3.1 universe.
2. **Group them**: put each HCP in their building, practice, HQ or IDN.
3. **Look back (feature window, 2025-07-25 to 2025-10-23)**: for each HCP, count the other HCPs in the group who wrote Kerendia in this window. This is the feature.
4. **Look forward (outcome window, 2025-10-24 to 2026-10-23)**: did the HCP write Kerendia (NBRx > 0)? Overall 9.7% did. This is the outcome.
5. **Compare**: the forward writer rate of HCPs who have peer writers vs those who do not. A big gap means the feature carries signal.

The feature window ends before the outcome window starts, so the feature only uses information the model would have at prediction time (no leakage).

**Four views are used in this assessment:**
* **Presence (3.1)**: a yes/no, "at least one peer writer in the group". Only HCPs with at least one colleague are included, so HCPs alone in their group do not drag down the "no" side. Example: 15.7% vs 7.4% means HCPs with a practice peer writer wrote Kerendia at 15.7%, those without at 7.4%, about 2.1 times higher.
* **Share (3.2)**: share = peer writers / other HCPs in the group. HCPs are sorted by share and cut into 5 equal-sized groups (quintiles, Q1 lowest to Q5 highest), and the writer rate is shown for each. If Q5 is clearly higher than Q1-Q4, the share works. Many HCPs have a share of exactly 0, so Q1-Q4 look alike; read it as "top fifth vs the rest".
* **Overlap (3.3)**: checks whether a new grouping flags the same HCPs as the building feature we already have. If it does, it is redundant. If it flags different HCPs who still write more, it adds value.
* **New-writer view**: current Kerendia writers tend to keep writing, and they also tend to sit near other writers, which can make any feature look good. So every check is repeated on HCPs with **no** Kerendia activity in the look-back window only. Rates are lower (about 4.4% baseline), but a remaining gap shows the feature predicts **new adoption**.

These are one-feature-at-a-time checks. They show that the feature goes with higher writing; they do not measure how much it lifts the model once all other features are in.

### 1.3 Explanation by Source

**Source 1: Building address (geocoding snapshot of MDM_STG_HCP_ADDR)**
* *What it is:* the HCP's address from MDM with latitude, longitude, building (premise) and sub-building.
* *Role:* grouping = HCPs in the **same building**. This is the NBA 3.0 colocation feature.
* *Feature:* number of Kerendia writers in the building in the last 3 months, plus a yes/no flag.
* *Signal:* 12.9% of the universe has a building peer writer. HCPs with a building peer writer but no practice peer writer write at 14.6% vs 7.5% for HCPs with neither (3.3). NUM_HCPS_IN_BUILDING is rank 8 of 752 in the 3.0 model.
* *Decision:* **Yes, keep.** It flags different HCPs from the practice level, so both are needed.

**Source 2: Kerendia best affiliation (BEST_AFFL)**
* *What it is:* for every HCP, the accounts (practices, clinics, hospitals) they are affiliated with, ranked by how strong the tie is for Kerendia. BRAND_RANK = 1 is the HCP's **main account**.
* *Role:* grouping = HCPs who share the same main account = **same practice (L1)**. Each HCP has exactly one main account. It covers 96.0% of the universe, in 90,861 practices; the typical HCP sits in a practice of 6 universe HCPs.
* *Features:* practice peer writer count, practice peer writer share, practice size.
* *Signal:*
  * Presence: 15.7% vs 7.4% (about 2.1x). New writers: 7.4% vs 4.4% (about 1.7x).
  * Share: top fifth writes at 19.0% vs about 7.5% for the rest.
  * Overlap with building: 44,279 HCPs (15.0% of the universe) have a practice peer writer but **no** building peer writer, and they still write at 12.2% vs 7.5%. The building feature misses them. HCPs with both write at 23.1%.

  **Building vs practice grid (section 3.3).** All 294,727 universe HCPs, split by two questions about the look-back window (2025-07-25 to 2025-10-23), with the HCP excluded: is there a Kerendia writer in the HCP's **building**, and in the HCP's **practice** (BEST_AFFL main account)? The last columns show how many went on to write Kerendia in the outcome window (2025-10-24 to 2026-10-23).

  | Building peer writer? | Practice peer writer? | HCPs | % of universe | Went on to write Kerendia | New-writer view |
  | --- | --- | --- | --- | --- | --- |
  | No | No | 212,375 | 72.1% | 7.5% | 4.3% |
  | **No** | **Yes** | **44,279** | **15.0%** | **12.2%** | **6.1%** |
  | Yes | No | 17,230 | 5.8% | 14.6% | 7.8% |
  | Yes | Yes | 20,843 | 7.1% | 23.1% | 10.7% |

  How to read it:
  * **Row 2 (44,279 HCPs)** have a Kerendia-writing colleague in their practice but **none in their building**, for example a practice with several clinic sites. The 3.0 building feature shows "no peer writer" for them, the same as the 212,375 HCPs in row 1. Yet they wrote Kerendia at 12.2% vs 7.5% (about 1.6x), and new writers at 6.1% vs 4.3%. The practice feature separates HCPs that the building feature lumps together.
  * **Not redundant:** only 20,843 HCPs (row 4) are flagged by both. If the two features flagged mostly the same HCPs, the practice feature would add little.
  * **The two add up:** HCPs with a writer in both write at 23.1%, higher than either alone (12.2% and 14.6%).
  * This is a one-feature-at-a-time check, not a model test.

* *Decision:* **Yes.** Strongest new signal, reaches HCPs the 3.0 feature misses.
* *Limits:* only the main account is used, so an HCP who works in two practices is counted in one. It is a Q4-2026 snapshot applied to past months.

**Source 3: MDM account hierarchy**
* *What it is:* the family tree of every account: L1 site/practice, L2 local group, L3 regional HQ, L4 IDN (health system).
* *Role:* rolls the practice up to wider groups. One join from the HCP's main account (source 2) to the L1 row gives all four levels.
* *What the levels look like (section 2):* L2 has 90,739 groups, almost the same as L1. L3 has 63,958 groups (typical HCP in a group of 17). L4 has 33,062 real IDNs (typical HCP in an IDN of 506); 71.4% of the universe sits in a real IDN.
* *Signal by level:*
  * L2: identical to L1, adds nothing (redundant).
  * L3: presence 12.9% vs 7.1%, share top fifth 19.8%. Promising, but its overlap with L1 has not been checked yet, so it may repeat the practice signal.
  * L4 presence: 9.1% vs 9.1%, no signal. IDNs are so large that 53.2% of HCPs have at least one writer somewhere in their IDN, so yes/no cannot separate anyone.
  * L4 share: top fifth 14.9% vs about 7.5%. The **share** of writing colleagues still works.
* *Decision:* **Yes, for the IDN peer share.** L4 placeholders ('NA', 'Multiple Doctors') are treated as no IDN.

**Source 4: Account profile**
* *What it is:* a description of each account: type (HCO_TYPE), class of trade, number of beds, number of MD/DOs, EMR system.
* *Role:* not a grouping. It describes the HCP's main account (e.g. large hospital vs small clinic).
* *Why No:* it is account context, not peer influence; MD/DO count is filled for only 51.4% and beds for 6.0%; practice size from source 2 already covers size; signal not checked.
* *Decision:* **No** for colocation. Could be tested later as a separate account-context feature.

**Source 5: PACE health-system metrics**
* *What it is:* pre-calculated numbers for every account at every level: HF and CKD patient counts, hospital counts, call-plan segment counts, Kerendia / Entresto / SGLT2 / sMRA writer counts, formulary status.
* *Role:* could give IDN-level context.
* *Why No:* its Kerendia writer counts are what we already build ourselves from source 9, with a controlled time window. We do not know the window behind these counts, so they may include the outcome period (leakage). The other fields are context, not colocation, and the signal has not been checked.
* *Decision:* **No** for colocation.

**Source 6: All HCP-account affiliations**
* *What it is:* every account each HCP is linked to, not just the main one (about 4.8 accounts per HCP).
* *Why No:* big hospitals link huge numbers of HCPs, so 269,179 HCPs share an account with someone and the typical HCP has 357 "colleagues". When almost everyone is colocated, the feature cannot tell HCPs apart. The number of accounts is already used as AFFL_COUNT (nb 07).
* *Decision:* **No.**

**Source 7: Practice / parent link upload**
* *What it is:* a file uploaded in Dec 2025 mapping HCPs to a practice and a lead HCP.
* *Why No:* covers only 3,141 universe HCPs (1.1%), and the practice grouping is already covered by source 2.
* *Decision:* **No.**

**Source 8: New writers address table**
* *What it is:* a table built for another analysis, matching 15,223 new Kerendia writers to an account and hierarchy level.
* *Why No:* it holds new writers only, so it cannot group the whole universe.
* *Decision:* **No.** The matching logic can be reused.

**Source 9: Kerendia LRx V7**
* *What it is:* weekly Kerendia prescriptions per HCP.
* *Role:* not a grouping. It tells us **who wrote Kerendia**: the peer writers in the look-back window, and the outcome in the signal check.
* *Decision:* **Yes.** Required input for every colocation feature.

## 2. What Each Level of Grouping Looks Like

HCPs are linked through their BEST_AFFL rank-1 account (source 2) and rolled up with the hierarchy (source 3). "Group size" is the number of universe HCPs in the HCP's own group, including the HCP.

| Level | Meaning | HCPs linked | Groups | Median group size (HCP view) | HCPs with at least 1 peer | HCPs with at least 1 peer writer |
| --- | --- | --- | --- | --- | --- | --- |
| Building (3.0) | Same lat/long + premise | 282,465 | — | — | — | 38,073 (12.9%) |
| L1 site / practice | Best account | 282,881 | 90,861 | 6 | 233,102 | 65,122 (22.1%) |
| L2 local group | | 282,881 | 90,739 | 6 | 233,168 | 65,345 (22.2%) |
| L3 HQ / regional | | 282,263 | 63,958 | 17 | 245,656 | 115,981 (39.4%) |
| L4 IDN | Health system | 210,425 | 33,062 | 506 | 186,909 | 156,930 (53.2%) |

Observations:
* **L2 is almost the same as L1** (90,739 vs 90,861 groups, identical signal below), so L2 adds nothing and can be skipped.
* Most accounts hold a single universe HCP (median 1 per account), but the typical HCP sits in a 6-HCP practice and a 506-HCP IDN.
* At L4, more than half of all HCPs have a peer writer, so a yes/no IDN flag cannot separate anyone. The IDN level needs a **share**, not a presence flag.
* The all-affiliations proxy (source 6) links almost everyone to everyone: 269,179 HCPs share an account with another universe HCP and the median HCP has 357 peer links, because large hospitals appear as affiliations. Use it for account-type counts (already in 07), not for peer colocation.

## 3. Signal Check

### 3.1 Peer writer presence (yes vs no, among HCPs with at least 1 peer)

| Level | Writer rate: peer writer yes vs no | New-writer view: yes vs no |
| --- | --- | --- |
| L1 practice | 15.7% vs 7.4% | 7.4% vs 4.4% |
| L2 local group | 15.7% vs 7.4% | 7.4% vs 4.4% |
| L3 HQ | 12.9% vs 7.1% | 6.2% vs 4.3% |
| L4 IDN | 9.1% vs 9.1% | 5.0% vs 5.0% |

### 3.2 Peer writer share (share of other group HCPs writing Kerendia), writer rate by quintile Q1-Q5

**How it is calculated:**
1. **Group:** link each HCP to their practice (L1, BEST_AFFL rank-1 account), HQ (L3) or IDN (L4, real IDNs only; 'NA' / 'Multiple Doctors' excluded) through sources 2 and 3.
2. **Other HCPs:** count the other universe HCPs in the same group (group size − 1). HCPs alone in their group have no share (null) and are left out.
3. **Peer writers:** count how many of those other HCPs had Kerendia NBRx > 0 in the look-back window (2025-07-25 to 2025-10-23). The HCP never counts towards their own share.
4. **Share:** peer writers ÷ other HCPs. Example: an IDN with 500 other HCPs, 40 of them writers, gives a share of 40 / 500 = 8%.
5. **Quintiles:** sort HCPs by share from lowest to highest and cut them into 5 equal-sized groups, Q1 (lowest share) to Q5 (highest share).
6. **Writer rate:** for each quintile, the % of HCPs with Kerendia NBRx > 0 in the outcome window (2025-10-24 to 2026-10-23). The new-writer view repeats this for HCPs with no Kerendia activity in the look-back window.

**Writer rate (%) by quintile, Q1 to Q5:**

| Level | All HCPs | New-writer view |
| --- | --- | --- |
| L1 practice | 7.3, 7.6, 7.5, 7.3, **19.0** | 4.4, 4.4, 4.5, 4.4, **8.7** |
| L3 HQ | 7.2, 7.0, 6.4, 8.5, **19.8** | 4.4, 4.3, 3.9, 4.9, **8.9** |
| L4 IDN | 8.0, 5.9, 7.5, 9.3, **14.9** | 4.4, 3.9, 4.4, 5.6, **7.0** |

**How to read it:**
* **Q5 is the signal.** At every level, the fifth of HCPs whose colleagues write Kerendia most went on to write about 2 to 2.7 times as often as the rest: practice 19.0%, HQ 19.8%, IDN 14.9%, vs about 7.5% in Q1-Q4. The pattern holds for new writers (practice 8.7%, HQ 8.9%, IDN 7.0% vs about 4.4%).
* **Q1-Q4 look alike.** Many HCPs have a share of exactly 0 or close to it, so the lower quintiles split near-equal values and do not rank cleanly. Read the table as "top fifth vs the rest", not as a steady climb.
* **Why the IDN needs a share, not a flag.** IDNs are large (median 506 universe HCPs), so 53.2% of HCPs have at least one writer somewhere in their IDN and the yes/no flag is flat (9.1% vs 9.1%, section 3.1). The share still separates HCPs because it measures how much of the IDN writes, not whether anyone does.
* One feature at a time: this does not show how much the L3 or IDN share adds once the practice share is in the model.

### 3.3 Does the practice level add to the building level?

All 294,727 universe HCPs, split by whether they have a peer writer in the building (3.0 logic, self excluded) and in the L1 practice. A detailed reading of this grid is under source 2 in section 1.3.

| Building peer writer | Practice (L1) peer writer | HCPs | Went on to write Kerendia | New-writer view |
| --- | --- | --- | --- | --- |
| No | No | 212,375 | 7.5% | 4.3% |
| No | Yes | 44,279 | 12.2% | 6.1% |
| Yes | No | 17,230 | 14.6% | 7.8% |
| Yes | Yes | 20,843 | 23.1% | 10.7% |

* Only 20,843 HCPs are flagged by both, so building and practice capture **different peer groups**.
* The practice level reaches **44,279 HCPs (15.0% of the universe) who have no building peer writer**, and they still write at 12.2% vs 7.5%.
* HCPs flagged by both write at 23.1%, so the two levels add up rather than repeat each other.

## 4. Candidate Features for the Readiness Plan

| Feature | Source | Logic | Evidence | Readiness |
| --- | --- | --- | --- | --- |
| PRACTICE_PEER_KERENDIA_WRITERS_3M (L1) | 2 + 9 | Count of other universe HCPs in the same BEST_AFFL account with Kerendia NBRx > 0 in the last 3 months | 15.7% vs 7.4%; new-writer 7.4% vs 4.4%; adds 44,279 HCPs over building | **Build.** Data in UC, no new feed |
| PRACTICE_PEER_KERENDIA_SHARE_3M (L1) | 2 + 9 | Peer writers / (practice HCPs - 1); null for single-HCP practices | Top quintile 19.0% vs about 7.5% | **Build** |
| PRACTICE_HCP_COUNT (L1) | 2 | Universe HCPs in the practice | Size denominator; median 6 | **Build** as denominator / size feature (test value on its own) |
| HQ_PEER_KERENDIA_SHARE_3M (L3) | 2 + 3 + 9 | Same as above at L3 | Top quintile 19.8% | **Test.** Check correlation with the L1 share first |
| IDN_PEER_KERENDIA_SHARE_3M (L4) | 2 + 3 + 9 | Same at L4, real IDNs only | Top quintile 14.9%; presence flag flat (9.1% vs 9.1%) | **Build** (share only). Matches 07 section 7.3 |
| IDN_HCP_COUNT / HCP_IN_IDN | 2 + 3 | IDN size; 1 if real IDN | 07 section 7.3: weak (rho -0.039; 9.4% vs 10.6%) | **Test** as a flag only |
| PRACTICE / IDN specialty peer writers (NEPH, CARD, ENDO, PCP) | 2 + 3 + 9 (SPECIALTY_GROUP) | Peer writers by LRx specialty group within L1 / L4 | Building version: NEPH and CARD Build (33 recs section 4) | **Test** at L1 |
| PRACTICE_HF_PEER_WRITERS | 2 + 9 (INDICATION_GROUP contains HF) | HF-indication Kerendia peer writers in the practice | Building version: Build | **Test** at L1 |
| ACCT_MD_DO_COUNT, ACCT_BEDS, ACCT_HCO_TYPE | 4 | Size and type of the HCP's best account | MD/DO 51.4% filled; beds 6.0% | **Test.** Profile signal before committing |
| IDN_HF_CKD_PATIENTS, IDN_H1_HOSPITALS, IDN_KERENDIA / ENTRESTO / SGLT2 / sMRA writers, IDN_FORMULARY_WIN | 5 | Join the HCP's L4 (or L3) bho_id to ph_hs_metrics_static | Covers 100% of universe L3/L4 accounts. Signal not checked | **Test.** Confirm the definitions and refresh cadence with the PACE owners; check that writer counts are not built from the outcome window |
| EMPLOYMENT_FLAG (BEST_AFFL) | 2 | Y / N / NA | 07 section 7.3: Y 10.2% vs N 7.8% | **Test** |
| PRACTICE_PARENT_LINK | 7 | Practice / parent HCP from the uploaded file | 1.1% coverage | **Skip** |
| Shared-patient network | IQVIA LAAD patient claims | HCP pairs that treat the same patients | Not profiled here (33 recs section 6.2) | **Later.** Biggest build effort |

## 5. Data Issues to Resolve Before Build
1. **Hierarchy has no HCP rows in UC.** `mdm_stg_acct_hrchy_ker` L0_HCP_BH_ID is empty, so the HCP link must come from BEST_AFFL rank 1. This gives one account per HCP. HCPs with several practices only count their best one.
2. **Placeholder IDNs.** L4 names 'NA' and 'Multiple Doctors' must be treated as no IDN (68,448 universe HCPs have L4 name 'NA'). Otherwise one fake IDN would hold tens of thousands of HCPs.
3. **Snapshot only.** BEST_AFFL and the hierarchy are Q4-2026 snapshots (quarterly copies 2026Q2-Q4 exist in `kerendia_cp`). The 12-month training spine will use the current affiliation for past months. Use the quarterly copies to see how much it moves.
4. **Leakage.** Peer writing must always come from a window before the outcome, and the HCP must be excluded. `ph_hs_metrics_static` writer counts need the same check before use.
5. **Universe definition of peers.** Peers here are universe HCPs only. Counting all HCPs in the account (including non-universe writers) is an option to test.
6. **MDM_STG_HCP_ACCT_AFFL** has no UC copy; the proxy has more rows per HCP. This matters only if the all-affiliations route is used.

## 6. Recommended Order
1. **Practice (L1) colocation** from BEST_AFFL + LRx V7: peer count, peer share and practice size. All data in UC, strongest new signal, and it reaches HCPs the building feature misses.
2. **IDN (L4) peer share** from the hierarchy, real IDNs only, plus an IDN-size flag.
3. **L3 share** and **specialty / HF practice counts**, kept only if they add over L1.
4. **Account profile and PACE health-system metrics** (sources 4 and 5) as account-context features after a signal check.
5. **Shared-patient network** from LAAD as a later phase.

## Summary
We already have what we need to move colocation beyond the building. Kerendia's best-affiliation table links 96% of the 3.1 universe to a practice, and the MDM account hierarchy rolls 71% of them up to a named IDN (33,062 IDNs). The practice level gives the clearest new signal. HCPs with a Kerendia-writing colleague in their practice write at 15.7% vs 7.4%, and 44,279 of them have no writer in their building, so the 3.0 feature misses them. At the IDN level almost everyone has some writer nearby, so only the share of writing colleagues is useful (top fifth 14.9%). Account profile and PACE health-system tables can add practice size, hospital type and health-system patient and writer counts. All sources are already in Unity Catalog, so no new data feed is needed for the first phase.
