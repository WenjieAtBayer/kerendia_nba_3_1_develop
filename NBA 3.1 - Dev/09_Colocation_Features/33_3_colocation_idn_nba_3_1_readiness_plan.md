# Colocation and IDN Features: NBA 3.1 Readiness Plan

**Group:** HCP peer influence (colocation) for the NBA 3.1 HCP-level model  
**Purpose:** a step-by-step plan to move colocation beyond the NBA 3.0 building feature to practice (L1) and IDN (L4) peer adoption, as a clean, leakage-safe and tested feature block  
**Builds on:** `33_1_colocation_nba_3_0_profile.md` (NBA 3.0 building / sub-premise profile), `33_2_colocation_idn_data_assessment.md` (sources, coverage, signal checks), `07_2_physician_attributes_data_assessment.md` section 3.3 (IDN and account checks), and the combined colocation / IDN / Veeva signal test (`kerendia_nba_3_1_develop` repo, `Veeva Link To People Analysis/60_veeva_colocation_idn_combined_signal_test`, results in `50_veeva_link_nba_3_1_readiness_plan.md` section 5.2)  
**Same structure as:** `50_veeva_link_nba_3_1_readiness_plan.md`  
**Sources:** all in Unity Catalog; no new data feed for phases 0 to 2. **Writers (peer writers and the new-writer view) come from the Kerendia metric views**: KER-10 `active_nbrx_writers` in `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_metric_views.mv_kerendia_nbrx` (the shared Kerendia KPI layer for all Kerendia users). PACE writer counts are not used  
**Status:** draft for discussion  
**Date:** November 18, 2026

---

## 1. Scope

| In scope | Out of scope (owned elsewhere) |
| --- | --- |
| **Building** colocation (3.0 feature, fixed) | Account profile features (`ACCT_MD_DO_COUNT`, `EMPLOYMENT_FLAG`): physician-attributes notebook (nb 07, `07_2_...` section 6) |
| **Practice (L1)** peer writers: count, share, practice size | HCP affiliation counts and types (`AFFL_*`): nb 07 |
| **IDN (L4)** peer writer share + zero flag | Veeva expert cross features (`veeva_idn_expert_share`, `veeva_practice_expert_peer_flag`): Veeva plan R5 / E7 |
| **Regional HQ (L3)**, specialty and HF peer writers: test only | Area context (census / SDoH): `08_2_census_data_assessment.md` |
| Business use: IDN adoption view for key account teams | Shared-patient network from LAAD claims: later phase (Q7) |

## 2. Goals and success criteria

| # | Criterion | How it is checked |
| --- | --- | --- |
| S1 | One grouping spine for every HCP-month: building, L1, L3, L4, with placeholder IDNs removed | Coverage reproduces `33_2_...` section 2 (282,881 L1, 210,425 real IDN, 33,062 IDNs) |
| S2 | Peer writing always from a window before the anchor; the HCP never counts in their own group | Leakage test (no claim on or after the anchor); toy self-exclusion test |
| S3 | 3.0 building defects fixed: count excludes the HCP; 0 (not null) when no writer is nearby | Profile of the new output vs `33_1_...` data-quality findings |
| S4 | Practice and IDN features add value on top of the fixed building feature | Experiments C2 and C3 beat C1, also in the new-writer view and within specialty |
| S5 | Peer writers and the new-writer view from the Kerendia metric view (KER-10), shared with the physician-attributes and Veeva work | D8 applied in every notebook; IDN share rho recomputed once on the metric-view writers |
| S6 | Fixed schema and documented features | Same columns on two runs; feature dictionary written |

## 3. Starting point

### 3.1 Evidence so far (one-feature-at-a-time checks, look-back 2025-07-25 to 2025-10-23, outcome 2025-10-24 to 2026-10-23, baseline 9.7%)

These checks used LRx V7 writers. From now on writers come from the metric view (D8), so P4 restates the numbers on KER-10 writers before they are used for decisions.

| Feature | Result | New-writer view | Source | Verdict |
| --- | --- | --- | --- | --- |
| Building peer writer (3.0) | `NUM_HCPS_IN_BUILDING` rank 8 of 752 (SHAP 1.22%); flag rank 64. Building writer only (no practice writer): 14.6% vs 7.5% | 7.8% vs 4.3% | `33_1`, `33_2` 3.3 | **Keep, fix defects** |
| Practice (L1) peer writer presence | 15.7% vs 7.4% | 7.4% vs 4.4% | `33_2` 3.1 | **Build** |
| Practice (L1) peer writer share | Top fifth 19.0% vs about 7.5% | Top fifth 8.7% | `33_2` 3.2 | **Build** |
| Practice adds over building | 44,279 HCPs (15.0%) with a practice writer but no building writer write at 12.2% vs 7.5%; both 23.1% | 6.1% vs 4.3%; both 10.7% | `33_2` 3.3 | Not redundant |
| L2 local group | Identical to L1 (90,739 vs 90,861 groups) | Identical | `33_2` 2 | **Skip** |
| L3 HQ share | Top fifth 19.8%; overlap with L1 not checked | Top fifth 8.9% | `33_2` 3.2 | **Test** |
| IDN (L4) presence flag | 9.1% vs 9.1% (53.2% of HCPs have an IDN writer) | 5.0% vs 5.0% | `33_2` 3.1 | **Skip** |
| IDN (L4) peer share | Top fifth 14.9%; bands 0: 7.6%, 0-5%: 4.8%, 5-10%: 8.1%, 10-20%: 12.4%, >20%: 28.4%; rho 0.125 (0.088 in the 07 recommendations) | Top fifth 7.0% | `33_2` 3.2, `07_2` 3.3 | **Build** + zero flag |
| HCP_IN_IDN, IDN_HCP_COUNT | 9.3% vs 10.6%; rho -0.039 | 5.3% vs 5.7% | `07_2` 3.3 | HCP_IN_IDN **Test**, count **Skip** |
| Specialty / HF peer writers | Building versions were Build in the 33 recommendations; not checked at L1 | - | `33_2` 4 | **Test** at L1 |
| PACE health-system metrics | 100% of universe L3 / L4 accounts. **Writer counts not used** (D8); only non-writer context fields (HF / CKD patients, H1 hospitals, formulary win) | - | `33_2` 1 (source 5) | Context fields **Test** |
| Veeva expert share in IDN (cross) | Q1 6.4% to Q5 12.3%; adds beyond IDN writer share | Q1 4.1% to Q5 6.8% | Veeva `50_` 5.2 | Owned by Veeva plan |

### 3.2 Defects in the NBA 3.0 building feature (`33_1_...`)

* `NUM_HCPS_IN_BUILDING` includes the HCP: 19,629 self-only writers have count 1 and flag 0; another 20,962 writers have counts that include themselves.
* The count is null, not 0, when no writer is nearby (57.4% null), so the model reads "no writer" as missing.
* 8,558 universe HCPs (3.7%) have no colocation row at all.
* Built on LRx V6 and the 3.0 universe (234,405); 3.1 uses the metric-view writers (D8) and 294,727 HCPs.
* Sub-premise features did not make the 752; sub-premise stays dropped.

### 3.3 Data facts that shape the build (`33_2_...` section 5)

* The hierarchy has no HCP rows in UC, so the HCP link is BEST_AFFL `BRAND_RANK = 1` BHO_ID = `L1_CHILD_BHO_ID` (exactly one account per HCP, all accounts match one L1 row).
* L4 names 'NA' and 'Multiple Doctors' are placeholders (68,448 universe HCPs have 'NA'); treat as no IDN.
* **No affiliation history is available** (Q3, user 2026-11-18). BEST_AFFL and the hierarchy are current (Q4-2026) snapshots, so the build uses the current affiliation for every anchor (D7). The quarterly copies in `kerendia_cp` (2026 Q2 to Q4) cover call-plan HCPs only; they are used to size how much affiliations move (F4), not as history. The request for history is logged as DR-01 / DR-02 in `01_data_improvement_requests.md`.
* 23,516 HCPs are the only universe HCP in their IDN, so their share is null.

## 4. Design principles

1. **Same grain as the 3.0 output:** one row per PROVIDER_ID x SVC_DT_M, joined by `99_Combine_Physician_Data` on `['PROVIDER_ID', 'SVC_DT_M']`.
2. **Look-back only, from the metric view:** peer writers = HCPs counted by KER-10 `active_nbrx_writers` (`mv_kerendia_nbrx`, by `provider_id`, `week_ending` in the 3 months before the anchor month); never the anchor month or later. The new-writer view = HCPs not counted by KER-10 in that look-back.
3. **Self excluded everywhere:** counts, shares and flags use the other HCPs in the group.
4. **Three states for missing:** no group (null), alone in group (share null, count 0), group with no writer (0). The IDN zero share gets its own flag.
5. **Shares, not flags, for large groups:** presence flags only at building and L1; share at L3 and L4.
6. **One spine, many groupings:** each grouping level is a column on the spine, so a new level is a new group-by, not a new pipeline.
7. **Peers = universe HCPs** by default; all-HCP peers tested once (Q5).
8. **Fixed schema:** columns do not depend on the data; prefix `COLOC_` for all new features (D6).

## 5. Work plan

### Phase 0: Foundations (in-house; blocks Phase 1)

| ID | Task | Detail | Done when |
| --- | --- | --- | --- |
| F1 | Grouping spine | PROVIDER_ID to BH_ID (`SOURCE_PROVIDER_BHID_NPI_MAPPING`) to BEST_AFFL rank-1 BHO_ID (L1) to hierarchy L3 / L4 (placeholders removed), plus building and premise from the geocoding snapshot | Reproduces `33_2` section 2 counts |
| F2 | Writer input from the metric view | One helper that returns, per anchor month, the set of HCPs counted by `MEASURE(active_nbrx_writers)` in `mv_kerendia_nbrx` (grouped by `provider_id`, `week_ending` in the 3-month look-back). Used for peer writers, the new-writer view and the specialty / HF versions (`specialty_group`, `indication_group` dimensions). Recompute the IDN share rho once on these writers (was 0.125 in `07_2`, 0.088 in the 07 recommendations) | Writer counts per month match KER-10 in the metric view |
| F3 | New-writer view | HCPs not counted by KER-10 in the look-back. Replaces the earlier rules (no Kerendia LRx activity in `33_2`; no Kerendia TRx in `07_2`, `08_2` and the Veeva test). Restate the baselines once | One rule in every notebook |
| F4 | Size the snapshot limitation | Use the current BEST_AFFL and hierarchy for all anchors (D7). On the call-plan quarterly copies (2026 Q2 to Q4), measure the share of HCPs whose practice or IDN changes per quarter, and record it in DR-01 | Change rate known and logged |
| F5 | Monthly anchor spine | 12 anchors matching the NBA 3.1 training window; 3-month look-back per anchor from F2 (metric view data start Jan 2024, enough for the window) | Leakage test passes (S2) |
| F6 | Fix the building feature | Rebuild on the metric-view writers (F2) and the 3.1 universe; peer-only count; 0 when no writer; keep the flag; drop sub-premise | Profile matches S3 |

### 5.1 Candidate feature list, first version

| Family | Example features | Count | Readiness | Evidence |
| --- | --- | --- | --- | --- |
| Building (fixed) | `COLOC_BLDG_PEER_WRITERS_3M`, `COLOC_BLDG_PEER_WRITER_FLAG` | 2 | Build | 3.1 table, `33_1` |
| Practice (L1) | `COLOC_PRAC_PEER_WRITERS_3M`, `COLOC_PRAC_PEER_SHARE_3M`, `COLOC_PRAC_HCP_COUNT` | 3 | Build | 15.7% vs 7.4%; top fifth 19.0% |
| IDN (L4) | `COLOC_IDN_PEER_SHARE_3M`, `COLOC_IDN_PEER_SHARE_ZERO_FLAG` | 2 | Build | Top fifth 14.9%; zero band 7.6% vs 4.8% |
| HQ (L3) | `COLOC_HQ_PEER_SHARE_3M` | 1 | Test | Top fifth 19.8%; overlap with L1 open |
| Specialty / HF at L1 | `COLOC_PRAC_PEER_WRITERS_{NEPH,CARD,ENDO,PCP}_3M`, `COLOC_PRAC_HF_PEER_WRITERS_3M` (metric view `specialty_group`, `indication_group`) | 5 | Test | Building versions Build in 3.0 recs |
| IDN membership | `COLOC_HCP_IN_IDN` | 1 | Test | Weak negative |
| IDN context (PACE, non-writer fields only) | `COLOC_IDN_HF_CKD_PATIENTS`, `COLOC_IDN_H1_HOSPITALS`, `COLOC_IDN_FORMULARY_WIN` | 3 | Test | Not checked; PACE writer counts not used (D8) |

Candidate set: 7 Build + up to 10 Test columns.

### Phase 1: Build block (low risk)

| ID | Task | Detail | Dependency |
| --- | --- | --- | --- |
| P1 | Build building + practice features | Self-excluded count, share, size per HCP-month | F1, F2, F5, F6 |
| P2 | Build IDN share | Real IDNs only; share null if alone; zero flag | F1, F2, F5 |
| P3 | Profile and leakage test | Nulls, zeros, distribution per month; no peer claim on or after the anchor; toy self-exclusion | P1, P2 |
| P4 | Restate the signal | Latest anchor re-run of `33_2` sections 3.1 to 3.3 on the metric-view writers; report any change of more than 1 point from the LRx V7 numbers | P1, P2 |

### Phase 2: Test features

| ID | Task | Detail | Dependency |
| --- | --- | --- | --- |
| T1 | L3 overlap check | Signal of L3 share within L1 share bands; keep only if it adds | P1 |
| T2 | Specialty and HF peer writers | L1 versions from the metric view `specialty_group` and `indication_group` dimensions; within-specialty check | P1 |
| T3 | All-HCP peers | Peers = all HCPs in the account, not only universe HCPs (Q5) | P1 |
| T4 | PACE context fields | HF / CKD patients, H1 hospitals and formulary win at the HCP's L4 (or L3); confirm field definitions and refresh with the PACE owners (Q4). No PACE writer counts | Q4 |

### Phase 3: Business use

| ID | Task | Detail |
| --- | --- | --- |
| B1 | IDN adoption view | IDN peer share by IDN, specialty and segment for key account teams; combine with the Veeva low-adoption expert list (Veeva plan B4) |
| B2 | Reason codes | "Colleagues in your practice / health system prescribe Kerendia" as an NBA reason when the practice or IDN feature drives the score |

### Phase 4: Operations

| ID | Task | Detail |
| --- | --- | --- |
| O1 | Quarterly affiliation refresh and archive | Re-pull BEST_AFFL and the hierarchy each quarter for the full universe, keep each pull with a snapshot date (so our own history builds up until DR-01 / DR-02 are delivered), and log L1 / L4 coverage and the placeholder IDN count |
| O2 | Drift check | Monthly share of HCPs with a practice or IDN peer writer; warn on a jump of more than 5 points |
| O3 | Documentation | Feature dictionary with business descriptions in this folder |

## 6. Model experiments

All experiments use the NBA 3.1 HCP-level model, target and validation split; only the colocation block changes.

| Exp. | Colocation block | Question answered |
| --- | --- | --- |
| C0 | 3.0 building features as they are | Baseline |
| C1 | Fixed building (F6) | Does fixing self-count and nulls change the result? |
| C2 | C1 + practice (P1) | Does the practice level add value over building? |
| C3 | C2 + IDN share (P2) | Does the IDN share add value over practice? |
| C4 | C3 + Test features passing T1 to T4 | Do L3, specialty, HF or PACE context fields add value? |
| C5 | C3 + Veeva cross features | Same as Veeva E7; run once, reported in both plans |

**Measures:** validation metric, SHAP share of the block, rank of the best colocation feature, gain in the new-writer view and within specialty (PCP, CARD, NEPH, ENDO), and stability across time folds.

## 7. Readiness gates

| Gate | Ready when |
| --- | --- |
| G0 (after Phase 0) | Spine reproduces `33_2` coverage (S1); metric-view writer helper in place (F2, F3); snapshot change rate measured and logged (F4); data requests sent to the data team (`01_data_improvement_requests.md`); building fix specified |
| G1 (after Phase 1) | Build block for all training anchors; leakage and self-exclusion tests pass; signal reproduced (P4); fixed schema on two runs; C1 to C3 run |
| G2 (after Phase 2) | Decision per Test feature; C4 run |
| G3 (before NBA 3.1 freeze) | Final block chosen; dictionary written; IDN adoption view reviewed with brand and key account teams |

## 8. Decisions and open questions

### 8.1 Proposed decisions

| # | Decision | Proposal |
| --- | --- | --- |
| D1 | Practice key | BEST_AFFL `BRAND_RANK = 1` BHO_ID; one practice per HCP |
| D2 | IDN key | Hierarchy L4 via `L1_CHILD_BHO_ID`; 'NA' and 'Multiple Doctors' = no IDN |
| D3 | Levels | Building + L1 + L4 built; L3 test; L2 and sub-premise dropped |
| D4 | Ownership | IDN peer share built here (as agreed in `07_2` 3.3); account profile and employment in nb 07; Veeva cross features in the Veeva plan |
| D5 | Missing values | Three states (principle 4) + IDN zero-share flag |
| D6 | Feature prefix | `COLOC_` for new features; keep 3.0 names only if C1 shows no change |
| D7 | Affiliations over time (decided by the user, 2026-11-18) | Use the current BEST_AFFL and hierarchy snapshot for all anchors. History is requested from the data team (DR-01, DR-02); switch to point-in-time affiliations when it is delivered |
| D8 | Writer source (decided by the user, 2026-11-18) | Peer writers and the new-writer view come from KER-10 `active_nbrx_writers` in `kerendia_metric_views.mv_kerendia_nbrx`. Do not use PACE writer counts or a separate LRx writer rule |

### 8.2 Open questions

| # | Question | Proposed answer | Owner |
| --- | --- | --- | --- |
| Q1 | Which peer-writer definition? | **Closed:** KER-10 writers from the metric view (D8). Still recompute the IDN share rho once (0.125 vs 0.088) | NBA team |
| Q2 | Which new-writer rule? | **Closed:** not counted by KER-10 in the look-back (D8, F3); also answers Veeva Q11 | NBA team |
| Q3 | Is there BEST_AFFL history for non-call-plan HCPs? | **Closed: no** (user, 2026-11-18). Use the current snapshot (D7); history requested as DR-01 | NBA team, data team |
| Q4 | What do the PACE context fields (patients, hospitals, formulary win) mean and how often are they refreshed? | Ask the PACE owners before T4. PACE writer counts are not used | PACE team |
| Q5 | Should peers include HCPs outside the universe? | Test once (T3) | NBA team |
| Q6 | HCPs in several practices: best account only, or all practices? | Best account for 3.1; all-affiliations proxy links too many HCPs (median 357) | NBA team |
| Q7 | When to build the shared-patient network from LAAD? | NBA 3.2; biggest build effort | NBA team |
| Q8 | Which 3.1 notebook builds this block, and does it replace the 3.0 colocation notebook? | One 3.1 colocation notebook writing the 3.0 output path and grain | NBA team |

## 9. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Current affiliations applied to past months | Practice and IDN groups reflect today, not the anchor; HCPs who moved get today's peers | F4 sizes it; D7; O1 archives our own quarterly pulls; DR-01 / DR-02 |
| Writer source changes from LRx V7 to the metric view | Earlier signal numbers shift; LAAD paid NBRx differs slightly from LRx (about 0.5% on monthly KER-10 vs ground truth) | P4 restates the numbers before decisions; one helper (F2) in every notebook |
| Existing writers cluster with writers | Features look strong but only track continued writing | New-writer view on every check; S4 |
| Group size drives the signal | Large practices and IDNs look different for reasons other than peers | Share features + size feature; within-size checks |
| Placeholder IDNs | One fake IDN holds tens of thousands of HCPs | D2; O1 logs the placeholder count |
| PACE writer counts include the outcome window | Target leakage | Not used (D8) |
| Overlap between levels | Redundant features | 3.3 grid; T1; C2 / C3 / C4 sequence |
