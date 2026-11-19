# Data Improvement Requests (NBA 3.1 static features)

**Purpose:** one list of data gaps found while preparing the NBA 3.1 static feature families (07 physician attributes, 08 census, 33 colocation and IDN), written so they can be proposed to the data team. Each request states the problem, why it matters for NBA, the evidence, what we ask for, and what NBA 3.1 does in the meantime.  
**Status values:** Open (not yet raised), Raised (sent to the data team), Accepted, Delivered, Rejected  
**Started:** November 18, 2026

## Summary

| ID | Request | Source | Feature family | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| DR-01 | Keep history of the Kerendia best affiliation for all HCPs | `pace_ker_in_house_schema.cust_mdm_best_affl_publish_pd_outp_static` | 33 colocation / IDN, 07 | High | Open |
| DR-02 | Keep history of the MDM account hierarchy | `pace_ker_in_house_schema.mdm_stg_acct_hrchy_ker` | 33 IDN | High | Open |
| DR-03 | Populate (or document) the HCP level of the hierarchy | `mdm_stg_acct_hrchy_ker` (`L0_HCP_BH_ID`, `KERENDIA_RANK`) | 33 | Medium | Open |
| DR-04 | Flag placeholder IDNs ('NA', 'Multiple Doctors') | `mdm_stg_acct_hrchy_ker` (L4) | 33 IDN | Medium | Open |
| DR-05 | Governed UC table for HCP geocoding, with history | `PHCDW_STG.MDM_STG_HCP_ADDR` (read today from a saved query output) | 33 building | Medium | Open |
| DR-06 | UC copy of all HCP-account affiliations, with effective dates | `MDM_STG_HCP_ACCT_AFFL` (Snowflake only) | 07, 33 | Medium | Open |
| DR-07 | Improve fill of account size fields | `pace_ker_in_house_schema.mdm_stg_acct_prfl_ker` | 07, 33 (test) | Low | Open |
| DR-08 | Document PACE health-system metric fields and refresh | `pace_ker_in_house_schema.ph_hs_metrics_static` | 33 (test) | Low | Open |

## Details

### DR-01: History of the Kerendia best affiliation (BEST_AFFL)

* **Problem:** only the current (Q4-2026) BEST_AFFL is available. The quarterly copies in `kerendia_cp` (`cust_mdm_best_affl_publish_pd_outp_static_cp_2026q{N}`) are filtered to call-plan HCPs, so they are not a history for the 294,727-HCP universe.
* **Why it matters:** practice (L1) and IDN (L4) colocation features are built for 12 monthly anchors. With one snapshot, an HCP who changed practice gets today's colleagues for every past month. Practice colocation is the strongest new 3.1 signal (15.7% vs 7.4% forward writer rate, `33_2` section 3.1), so its training rows should reflect the practice at the time.
* **Evidence:** `33_2_colocation_idn_data_assessment.md` section 5 item 3; `33_3_...` section 3.3 and F4.
* **Ask:** keep each refresh of BEST_AFFL for all HCPs (not only call-plan HCPs) with a snapshot or effective date, at least quarterly, back to January 2024 if possible (start of the Kerendia metric views).
* **NBA 3.1 workaround:** use the current snapshot for all anchors (`33_3` D7); size the change rate on the call-plan copies (F4); archive our own quarterly pulls (O1).
* **Change rate measured (F4, 2026-11-19, `33_colocation_idn_features`):** among universe HCPs in the call-plan copies, the rank-1 practice changed for 6.57% (Q2->Q3 2026, 68,945 HCPs) and 12.2% (Q3->Q4 2026, 83,985 HCPs); the real IDN changed for 3.27% and 6.31%.

### DR-02: History of the MDM account hierarchy

* **Problem:** `mdm_stg_acct_hrchy_ker` is a Q4-2026 snapshot only (563,271 L1 accounts, each with one L4).
* **Why it matters:** IDN peer share (top fifth 14.9% vs about 7.5%) depends on which IDN each practice belongs to. Mergers and acquisitions move practices between IDNs.
* **Evidence:** `33_2` section 5 item 3; `07_2_physician_attributes_data_assessment.md` section 5 item 2.
* **Ask:** keep each refresh with a snapshot date, at least quarterly.
* **NBA 3.1 workaround:** current snapshot for all anchors (`33_3` D7).

### DR-03: HCP level of the hierarchy is empty in UC

* **Problem:** the HCP columns `L0_HCP_BH_ID` and `KERENDIA_RANK` are empty, so HCPs cannot be linked to the hierarchy directly.
* **Why it matters:** HCPs have to be linked through their BEST_AFFL rank-1 account, so each HCP gets exactly one practice and IDN; HCPs who work in several practices are counted in one only.
* **Evidence:** `33_2` section 1 (source 3) and section 5 item 1.
* **Ask:** populate the HCP level, or confirm it is not supported and that BEST_AFFL rank 1 is the intended link.
* **NBA 3.1 workaround:** BEST_AFFL `BRAND_RANK = 1` BHO_ID = `L1_CHILD_BHO_ID` (`33_3` D1, D2).

### DR-04: Placeholder IDNs

* **Problem:** L4 names 'NA' and 'Multiple Doctors' are used as placeholders; 68,448 universe HCPs have L4 name 'NA'.
* **Why it matters:** treated as real IDNs, one fake IDN would hold tens of thousands of HCPs and distort every IDN feature.
* **Evidence:** `33_2` section 5 item 2.
* **Ask:** null the L4 IDN for these rows, or add a flag that marks a placeholder; document any other placeholder values.
* **NBA 3.1 workaround:** treat 'NA' and 'Multiple Doctors' as no IDN (`33_3` D2); log the count each refresh (O1).

### DR-05: Governed geocoding table for building colocation

* **Problem:** the NBA 3.0 building feature reads a saved query output (`query_output/kerendia_nba_3_0_hcp_model_hcp_profile_geocoding_addreess_information`, 8 columns from `MDM_STG_HCP_ADDR`), not a governed table. Missing geocodes are imputed as -999.99 and missing buildings as 'NOT_AVAILABLE'.
* **Why it matters:** `NUM_HCPS_IN_BUILDING` is rank 8 of the 752 NBA 3.0 features; it has no refresh owner or history today.
* **Evidence:** `33_1_colocation_nba_3_0_profile.md` (data sources, business rules); `33_2` section 1 (source 1).
* **Ask:** a UC table of HCP address and geocoding (latitude, longitude, premise, sub-premise) with a refresh schedule, address history, and nulls instead of imputed codes.
* **NBA 3.1 workaround:** keep the saved snapshot; apply the 3.0 rules for -999.99 and 'NOT_AVAILABLE'.

### DR-06: UC copy of all HCP-account affiliations

* **Problem:** `MDM_STG_HCP_ACCT_AFFL` exists only in Snowflake and is a current snapshot (START_DATE = load date, END_DATE empty). The UC proxy (`whc_data_zone1_prod.mdm_hcp_hco_affl`) has more rows per HCP.
* **Why it matters:** physician-attribute affiliation features (nb 07) keep a Snowflake read and get today's affiliations for back-dated training rows.
* **Evidence:** `07_2` section 5 item 1; `33_2` section 5 item 6.
* **Ask:** a UC copy with real start and end dates.
* **NBA 3.1 workaround:** keep the Snowflake read in nb 07.

### DR-07: Account size fields are sparsely filled

* **Problem:** in `mdm_stg_acct_prfl_ker`, `COUNT_MD_DO` is filled for 51.4% (46,662 of 90,861) of the HCPs' best accounts and `COUNT_BEDS` for 6.0% (hospitals only); `PERCENT_MEDICAID` / `PERCENT_MEDICARE` are empty.
* **Why it matters:** account size and type are candidate test features (`ACCT_MD_DO_COUNT` in nb 07; account context in `33_3` 5.1).
* **Evidence:** `33_2` section 1 (source 4); `07_2` section 3.3.
* **Ask:** confirm whether these fields can be filled more widely, or whether they apply only to some account types.
* **NBA 3.1 workaround:** test with nulls kept; no decision depends on it yet.

### DR-08: PACE health-system metrics documentation

* **Problem:** `ph_hs_metrics_static` has no documented field definitions or refresh cadence. Its writer counts are **not used** in NBA 3.1 (writers come from KER-10 in `kerendia_metric_views.mv_kerendia_nbrx`, `33_3` D8).
* **Why it matters:** the context fields (HF / CKD patients, H1 hospitals, formulary status and win date) are test features at IDN level (`33_3` T4).
* **Evidence:** `33_2` section 1 (source 5).
* **Ask:** field definitions, time window and refresh cadence for the non-writer fields.
* **NBA 3.1 workaround:** test only after the definitions are confirmed (`33_3` Q4).

## Adding a request

Use the next free `DR-NN`, add a row to the summary, and a details block with: problem, why it matters, evidence (file and section), ask, and NBA 3.1 workaround. Update the status when a request is raised or answered.
