# HCP Digital: NBA 3.1 Readiness Plan

**Group:** Non-personal promotional features, HCP digital  
**Purpose:** a step-by-step plan to turn HCP digital into a clean, stable and tested feature block for NBA 3.1  
**Builds on:** `01_digital_entity_map_vendor_channel_tactic_content.md` (the map), `10_hcp_digital_paid_media_nba_3_0.md`, `11_hcp_hq_emails_nba_3_0.md`, `12_hcp_oe_digital_review_for_nba_3_1.md`, `30_nba_3_1_proposed_additional_features.md` (sections 1 and 2)  
**NBA 3.1 notebooks concerned:** `04_Promotional_Features/24_Features_Digital`, `04_Promotional_Features/15_promotional_features_HQ_Emails`  
**Status:** draft for discussion  
**Date:** October 26, 2026

## 1. Scope

| In scope | Out of scope (owned elsewhere) |
| --- | --- |
| **Paid media to doctors** from the MMX table: Banner, 3rd Party Email, Custom (all vendors and placements) | **DTC** consumer media (`20_dtc_direct_buy_social_nba_3_0.md`); kept as in NBA 3.0 for now |
| **HQ emails** (Bayer head-office email, SFMC) from the MMX table and the email event log (`HCP_EMAIL_LIST`) | **iRep email** (rep-sent): owned by the personal promotional features (`personal_promotional_features/irep_emails.md`); removed from the digital block to avoid double counting |
| Content of digital touches (OE content tagging) | Clickstream / CLM (personal features) |
| Interaction with OE 2.0 (period effect of the roll-out) | Changing OE itself |

## 2. Goal and how we will judge success

**Goal.** Replace the NBA 3.0 digital block (about 684 drifting `DIGITAL_` columns, of which 9 survive in the model) with a **smaller, fixed and documented** block that captures what OE has shown to matter: vendor and placement, engagement depth, content, and timing.

**Success criteria** (to agree with the modelling team):

| # | Criterion | How it is measured |
| --- | --- | --- |
| S1 | **Stable schema**: the same columns every run | Column list fixed in a config table; a run with a new vendor or tactic adds no column |
| S2 | **Full coverage** of Kerendia digital | All Kerendia brand values included; less than 1% of rows in an unmapped `OTHER` bucket |
| S3 | **No double counting** | Each touch counted in exactly one source (HQ email: one source; iRep: personal block only) |
| S4 | **Model value** | The new block improves the NBA 3.1 validation metric over the NBA 3.0 digital block (experiment E0 vs E2 to E5 in section 6) |
| S5 | **Digital importance** | Share of total SHAP importance carried by HCP digital, and rank of the best digital feature (today 68 of 752), both improve |
| S6 | **Explainable to the business** | Every kept feature maps to a vendor, placement or content in the entity map |

## 3. Starting point (NBA 3.0)

| What NBA 3.0 does | Problem | Where it is explained |
| --- | --- | --- |
| Keeps only `UPPER(BRND_NM) = 'KERENDIA'` | Drops indication-tagged rows: 88% of Doceree, 74% of PeerDirect email | map, section 6 |
| Dynamic pivots by channel, vendor and tactic | Columns change from run to run | `10_...`, section 6 |
| Tactic labels by exact, case-sensitive names; "contains Banner" | `OTHER_TACTIC` mixes PulsePoint display, Medscape BA360 Brand Alert, Doximity DocPoint, PeerDirect web; iRep spelling `iRep Email` may now miss `IRep Email` | map, sections 1 and 3 |
| Banner channel features in the model | In practice they are PulsePoint only | map, section 3.1 |
| `BANNER_TACTIC` feature (rank 68) | Zero before April 2025; acts as a period marker | map, section 3.1 |
| HQ email counted in notebook 15, in Digital as a channel, and in Digital as a vendor | Double (triple) counting | `11_...`, section 6 |
| iRep email counted in Digital and in notebook 16 | Double counting | `10_...`, section 6 |
| "Light" and "deep" engagement (our internal definitions, not vendor-reported) | Rule per vendor metric not written down; total is not light + deep | `10_...`, section 2 |
| First lookback month dropped; current month may be incomplete; `RUNNING_` depends on data start | Inconsistent windows between runs | `10_...`, section 6 |
| No content, no recency, no placement | The information OE uses most is missing | `12_...`, sections 5 to 7 |

**What the NBA 3.0 model keeps from HCP digital (9 features):** 3 Banner channel totals (PulsePoint), 1 banner tactic, 2 HQ email vendor, 1 HQ email tactic, 2 iRep email vendor. None is a media-partner placement.

## 4. Design principles for NBA 3.1

1. **One dictionary, fixed.** A placement dictionary (config table) maps `SRC_SYS_CD` + `TACTIC_NAME` (case-insensitive, trimmed, pattern-based) to a fixed **vendor**, **placement** and **channel**. Anything not mapped goes to `OTHER` and is reported, not silently pivoted.
2. **All Kerendia brand values.** Filter `UPPER(BRND_NM) LIKE '%KERENDIA%'` (as the Digital refresh notebook already does). Keep the indication (HF / T1D / CKD) as a dimension, not as a filter, next to the Kerendia total.
3. **One source per activity.** HQ email from one source only; iRep email only in the personal block; journey codes in the HQ email vendor column (`COPAY`, `KERENDIA_FTO`, vouchers) mapped to HQ email, not treated as vendors.
4. **Documented engagement levels.** Use OE's R / I / E definition per vendor metric (flag file and `mdb_prep_config.xlsx`) where event data exists; write down our internal MMX light / deep rule per vendor metric and document a crosswalk between MMX exposure / light / deep and OE's R / I / E.
5. **NPI and month, aligned to the anchor.** Keep NPI and monthly grain; windows end at the last **complete** month before the anchor date; include the first lookback month; no `RUNNING_` features with a moving start (replace with fixed 12-month windows).
6. **Few, meaningful features.** Build a candidate set of about 150 columns and select down (target 30 to 60 in the model), rather than feeding hundreds of sparse pivots.
7. **Language.** When OE output is used, doctors are **recommended** to vendors, not "reached".

## 5. Work plan

The work is split into phases. Each phase ends with a gate (section 7).

### Phase 0: Fix the foundations (blocking)

| ID | Task | Detail | Notebook / asset |
| --- | --- | --- | --- |
| F1 | Brand filter | Replace `= 'KERENDIA'` by `LIKE '%KERENDIA%'`; add `INDICATION` derived from `BRND_NM` | `24_Features_Digital` |
| F2 | Placement dictionary | Build a config table from the entity map: vendor, raw tactic pattern, placement, channel, OE placement name (e.g. `DOXIMITY_DOCSPOT`), recommended by OE (Y/N). First version in section 5.1 | new config table in `kerendia_nba_3` |
| F3 | Case-insensitive mapping | Match on `UPPER(TRIM(TACTIC_NAME))` with patterns; fixes `iRep Email` / `IRep Email` and PulsePoint `Programatic_DISPLAY` | `24_Features_Digital` |
| F4 | Unmapped report | Each run writes the share and list of rows mapped to `OTHER`; alert if above 1% | `24_Features_Digital` |
| F5 | Windows and months | Include the first lookback month; drop the incomplete current month; select the last complete month before the anchor in the combine step | `24_Features_Digital`, combine notebook |
| F6 | Remove `RUNNING_` | Replace by fixed 12-month windows | `24_Features_Digital` |
| F7 | De-duplicate HQ email | Decide one source (proposal: notebook 15 event log for sent / open / click / bounce / unsubscribe; MMX HQ email excluded from the paid-media block) | `15_...`, `24_...` |
| F8 | Remove iRep from digital | Exclude `IREP EMAIL` from the paid-media block; iRep stays in notebook 16 | `24_Features_Digital` |
| F9 | Fixed schema | Output columns generated from the dictionary and a window list; missing combinations filled with 0 | `24_Features_Digital` |

### 5.1 Placement dictionary, first version

From the entity map. Rows are MMX rows January 2025 to October 2026, all Kerendia brand values.

| Channel | Vendor | Placement | Raw tactic names (pattern) | Rows | OE recommends |
| --- | --- | --- | --- | --- | --- |
| Banner | PulsePoint | Programmatic display | `Programatic_DISPLAY` | 105.5M | Yes (`PULSEPOINT_BANNER`) |
| Banner | Medscape | Banner | (empty), `Brand Alert` in Banner channel | 274k | Yes (`MEDSCAPE_BANNER`) |
| Banner | Doceree | EHR banner | `EHR Banner` | 834k | No (journey only) |
| Banner | PeerDirect | MDFI / MD Minute / MD Shuffle / PV Compendium banner | `* - Banner`, `MD Minute`, `MDFI` in Banner channel | 67k | No (journey only) |
| Banner | OpenEvidence | Direct banner | `Direct Banner` | 26k | No |
| Banner | Other banner | Biopharm, ConnectiveRx, Nativo, Haymarket, ... | (empty), campaign names | 474k | No |
| 3rd Party Email | Medscape | Email Alert | `Email Alert`, (empty), `Formulary Access Package`, `Digital Data Trends` | 1.75M | Yes (`MEDSCAPE_3RD_PARTY_EMAIL`) |
| 3rd Party Email | PeerDirect | MDFI email | `MDFI - Email`, `MDFI` | 493k | Yes (`PEERDIRECT_MDFI_EMAIL`) |
| 3rd Party Email | PeerDirect | MD Minute email | `MD Minute - Email`, `MD Minute` | 266k | Yes (`PEERDIRECT_MD_MINUTE_EMAIL`) |
| 3rd Party Email | Other 3rd-party email | Haymarket, Biopharm, MJH, Healthcast | campaign names, (empty) | 460k | No |
| Custom | Doximity | DocNews | `DocNews` | 1.14M | Yes |
| Custom | Doximity | DocPoint | `DocPoint` | 133k | Yes |
| Custom | Doximity | DocSpot | `DocSpot` | 112k | Yes |
| Custom | Doximity | Announcement | `Announcement` | 18k | Yes |
| Custom | Doximity | FormularyOne | `FormularyOne`, `Formulary` | 29k | No |
| Custom | Medscape | BrandAlert | `BA360 - Brand Alert`, `Brand Alert` | 1.12M | Yes (`MEDSCAPE_BRANDALERT`) |
| Custom | Medscape | Offsite media | `Offsite Media`, `Media`, `BA360 - Email Alert`, (empty) | 1.23M | No |
| Custom | Medscape | Education (ReCAP, FFQ, BrandSpot, XCOD) | `Research Capsule (ReCAP)`, `Fast Five Quiz`, `BrandSpot`, `XC On Demand`, ... | 95k | No |
| Custom | Epocrates | Monograph | `Monograph Message` | 81k | No |
| Custom | Epocrates | DocAlert | `DocAlert`, `Doc Alert` | 47k | No |
| Custom | Epocrates | Search suggestion | `Search Suggestion` | 55k | No |
| Custom | Prescriber Point | Monograph | `Monograph` | 115k | No |
| Custom | PeerDirect | Web (MDFI, MD Minute, MD Shuffle, PV Compendium) | `* - Web`, `MD Minute`, `MDFI` in Custom channel | 34k | Yes (`PEERDIRECT_MDFI_WEB`) |
| Custom | Other custom | ReachMD, Impiricus, MD Calc, Haymarket, MJH | various | 71k | No |
| HQ Email | Bayer HQ (SFMC) | HQ email | vendor `HQ EMAIL` and journey codes | 9.37M | Yes (`SFMC_HQ_EMAIL`) |

The dictionary must be reviewed with the digital team (vendor and placement names, and whether "Other" groups are acceptable).

### Phase 1: MMX-based feature block (low risk)

Built from the MMX table and the dictionary. Windows: 1, 3, 6 and 12 complete months before the anchor.

| ID | Feature family | Example names | Approx. count | Why |
| --- | --- | --- | --- | --- |
| P1 | Touchpoint totals | `DIGITAL_TOTAL_EXPOSURE_3M`, `DIGITAL_TOTAL_ENGAGEMENT_3M` | 8 to 16 | OE kept all four touchpoint totals |
| P2 | Channel totals | `DIGITAL_CH_BANNER_EXPOSURE_3M`, `DIGITAL_CH_3P_EMAIL_ENGAGEMENT_6M` | about 24 | Keeps NBA 3.0's working signal (banner = PulsePoint) in a clean form |
| P3 | Placement totals | `DIGITAL_PLC_DOXIMITY_DOCSPOT_EXPOSURE_3M`, `DIGITAL_PLC_EPOCRATES_MONOGRAPH_EXPOSURE_6M` | about 60 to 80 | OE's strongest MMX features are placements (Epocrates, Prescriber Point, Doximity) |
| P4 | Rates | `DIGITAL_ENGAGEMENT_RATE_6M` (engagement / exposure), per channel | about 6 | Separates "shown a lot" from "responds" |
| P5 | Recency | `DIGITAL_DAYS_SINCE_LAST_EXPOSURE`, `DIGITAL_DAYS_SINCE_LAST_ENGAGEMENT` | 4 | OE shows timing matters |
| P6 | Diversity | `DIGITAL_N_VENDORS_3M`, `DIGITAL_N_PLACEMENTS_3M`, `DIGITAL_N_ACTIVE_MONTHS_6M` | 3 | Breadth of exposure |
| P7 | Trend | `DIGITAL_EXPOSURE_3M_VS_PRIOR_3M` | 2 to 4 | Rising or falling pressure |
| P8 | HQ email | sent, unique open, unique click, open rate, click rate, bounce flag, unsubscribe status, days since last open | about 12 | From `30_...` section 2; one source only |

Candidate set: about 120 to 160 columns. Feature selection (section 6) is expected to keep 30 to 60.

### Phase 2: Engagement depth and content (OE reuse)

| ID | Task | Detail | Dependency |
| --- | --- | --- | --- |
| C1 | R / I / E per vendor metric | Reuse OE's flag file (`5_5_2026_Bayer_OE_updated_channel_eng_exp_flag_latest.xlsx`) and `mdb_prep_config.xlsx` metric mappings | Event-level data (C3) |
| C2 | Content counts | Reuse OE's content tagging (litcode, subject, creative, ...) to count touches per content category over 3 and 6 months (13 categories + `GENERAL`) | Event-level data (C3); tagging file maintenance |
| C3 | Event-level source | Build doctor-month features from `kerendia_oe_journey.oe_kerendia_fact_npp_inference` for Doximity, Medscape, PeerDirect, PulsePoint, SFMC; map BH_ID to NPI with `kerendia_oe_npi_bhid_mapping_inference` | NPI / BH_ID coverage check |
| C4 | Response lag | Test OE's 7-day shift (or leaving out the last week) | none |
| C5 | Placement R / I / E | e.g. `DIGITAL_EVT_DOXIMITY_DOCSPOT_E_3M`, `DIGITAL_EVT_MEDSCAPE_3P_EMAIL_I_3M` | C1, C3 |

Phase 2 features replace Phase 1 placement totals for the five event-level vendors only if they test better (E4 vs E3).

### Phase 3: OE roll-out and coordination

| ID | Task | Detail |
| --- | --- | --- |
| O1 | Roll-out stability check | OE ran a 3-month pilot (test and control) and has been fully rolled out since 18 September 2026; there is no control group after that date. Compare digital volume, mix, share of doctors touched and feature importance before and after the roll-out. A per-doctor OE flag is **not** used |
| O2 | Period handling | If features shift, add a period indicator or restrict training to the post-roll-out period |
| O3 | OE recommendation as input (later) | Consider "placements OE recommended for this doctor this quarter" as an NBA input. Risk: circularity (OE also learns from NBA-like features); test only after O1 |
| O4 | Consistent messaging | Agree with the OE team how NBA dropdown list actions and OE recommendations are shown together |

## 6. Model experiments

All experiments use the NBA 3.1 HCP-level model, target and validation split; only the HCP digital block changes. DTC and all other blocks stay fixed.

| Exp. | Digital block | Question answered |
| --- | --- | --- |
| E0 | NBA 3.0 digital block as is (9 features kept, or the full 684 with selection) | Baseline |
| E1 | E0 with foundations fixed (F1 to F9) | How much do the brand filter, fixed mapping and de-duplication change results? |
| E2 | Phase 1: totals, channels, rates, recency, diversity, trend, HQ email | Does a small, clean block beat the baseline? |
| E3 | E2 + placement totals (P3) | Does placement detail add value? |
| E4 | E3 with event-level R / I / E for the five event vendors (C1, C3, C5) | Is event-level better than MMX for those vendors? |
| E5 | E4 + content counts (C2) | Does content add value? |
| E6 | Best of E2 to E5, trained post-roll-out only (O1, O2) | Does the OE roll-out change what works? |

**Measures for each experiment:** validation metric of the NBA 3.1 model (same as the main model), SHAP share of the digital block, rank of the best digital feature, number of digital features kept after selection, and stability of importance across time folds. Feature selection uses the same method as the main NBA 3.1 model so results are comparable.

## 7. Readiness gates

| Gate | Ready when |
| --- | --- |
| G0 (after Phase 0) | Dictionary reviewed by the digital team; unmapped share below 1%; HQ email and iRep single-source decision made; fixed schema produced twice with identical columns; E1 run |
| G1 (after Phase 1) | Candidate block built for all training instances; leakage check passed (no month after the anchor); E2 and E3 run and compared with E0 |
| G2 (after Phase 2) | BH_ID to NPI coverage measured; content tagging up to date (untagged share known); E4 and E5 run |
| G3 (before NBA 3.1 freeze) | Final digital block chosen; documented in this folder with the same structure as files 10 and 11; roll-out check (O1) done |

## 8. Decisions and open questions

| # | Question | Proposed answer | Owner |
| --- | --- | --- | --- |
| Q1 | Source of truth for HQ email | Notebook 15 email event log; drop HQ email from the MMX block | NBA team |
| Q2 | Where iRep email lives | Personal promotional block only | NBA team |
| Q3 | Definitions of MMX "light" and "deep" engagement | Answered: these are our internal engagement definitions, not vendor-reported (digital team meeting, Oct 2026). Next: write down the rule per vendor metric and map it to OE's R / I / E; until then use exposure and total engagement only | NBA and digital teams |
| Q4 | Keep indication (HF / T1D / CKD) as a dimension? | Answered: yes (digital team meeting, Oct 2026). Keep the Kerendia total and add indication as a dimension, following the Q4 target-list rule (HF = cardiologists, T1D = T1D target list, CKD = remaining HCPs). Needs the T1D target-list file (Samantha Meyers) | NBA and brand teams |
| Q5 | Training window relative to the OE roll-out | Decide after O1 | NBA team |
| Q6 | Owner of the placement dictionary and content tagging file updates | Digital team, with a monthly check of unmapped rows | Digital team |
| Q7 | Use OE recommendations as an NBA input | Not in v1; revisit after O1 | NBA and OE teams |

## 9. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Vendors rename tactics | Activity moves to `OTHER` | Pattern-based dictionary, unmapped report and alert (F4) |
| Sparse placements | Many near-zero columns, unstable importance | Group small placements into "Other" per channel; select features |
| PulsePoint dominates volume | Totals reflect PulsePoint only | Keep channel and placement features alongside totals; consider totals excluding programmatic display |
| Different keys (NPI vs BH_ID) | Lost doctors in event-level features | Measure mapping coverage before Phase 2 (G2) |
| Digital effect is weak in NBA | Little gain whatever the design | Judge on S4 and S5; accept a small block if it does not improve the model |
| OE roll-out changes the data | Features learned on pre-roll-out data may not hold | O1 and E6 |

## 10. References

| Topic | File or asset |
| --- | --- |
| Vendor, channel, tactic, content map and coverage | `01_digital_entity_map_vendor_channel_tactic_content.md` |
| NBA 3.0 paid media notebook | `10_hcp_digital_paid_media_nba_3_0.md` |
| NBA 3.0 HQ email notebook | `11_hcp_hq_emails_nba_3_0.md` |
| OE 2.0 digital review and ideas | `12_hcp_oe_digital_review_for_nba_3_1.md` |
| Proposed feature formulas | `30_nba_3_1_proposed_additional_features.md`, sections 1 and 2 |
| MMX source table | `kerendia_oe_journey.mmx_fnl_combined_aggr_tab` (refreshed by notebook `Kerendia/Digital`) |
| OE event-level table | `kerendia_oe_journey.oe_kerendia_fact_npp_inference` |
| OE content per placement | `kerendia_oe_journey.content_matrix_oe_2` |
| BH_ID to NPI mapping | `kerendia_oe_journey.kerendia_oe_npi_bhid_mapping_inference` |
| NBA 3.0 model | MLflow run `f583bcbc9d56477fae983d44c16f8c70` |
| OE 2.0 model | `kerendia_oe_journey.bayer_kerendia_ga_model_oe_2@champion` |
