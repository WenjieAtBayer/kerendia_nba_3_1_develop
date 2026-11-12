# NPP Inference vs MMX Combined Aggregate – Column and Value Comparison

**Date:** 2026-10-26

## Tables compared

| Alias | Table | Platform | Columns |
| --- | --- | --- | --- |
| NPP | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_oe_journey.oe_kerendia_fact_npp_inference` | Databricks Unity Catalog | 41 |
| MMX | `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` | Snowflake | 66 |

MMX was read with `Get_Data_Snowflakes` (key-pair auth) from the `00_connection` helper notebook in `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks`. Database `PHCDW`, schema `PHCDW_CDM`, warehouse `PROD_CYRUS_BI_WH`, role `BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF`.

## 1. Column name comparison

Only 2 column names match exactly: `CF_INDICATION` and `LITCODE` (string in both).

### Semantic (name/meaning-based) matches

| Concept | NPP | MMX |
| --- | --- | --- |
| HCP ID | `BAYER_HCP_ID` / `CUST_ID` | `BH_ID` |
| Date | `DATE_ID` (string) | `DATE_ACT` (date) |
| Brand | `PROD_BRAND_NM` | `BRND_NM` |
| Vendor / tactic | `VEND_NM`, `TACT_NM`, `TACT_TYP` | `SRC_SYS_CD`, `VNDR_TACTC_NM`, `TACTIC_NAME` |
| Channel | `CHNL_NM` / `RPT_CHNL` | `CHANNEL` |
| Campaign | `CPGN_NM` | `CAMPIGN` / `CF_CAMPAIGN` |
| Content | `CNTT_NM` / `CRTV_NM` | `CONTENT` / `CF_CONTENT` |
| URL | `LINK_URL` | `URL` |
| Specialty | `HCP_PRMRY_SPCL`, `HCP_PAR_SPCL_GRP` | `PRIMARY_SPECIALTY_DESC`, `PRIMARY_SPECIALTY_GRP` |
| Location | `HCP_PRMRY_CITY/STATE/ZIP` | `CITY`, `STATE`, `ZIP` |
| Segment | `HCP_SEG_1`, `TRGT_FLAG` | `TGT_SGMNT` |

### Structural differences
- NPP: event-level digital touchpoint data; all columns are strings (including date); no numeric measures.
- MMX: aggregated table with `WEEK_END`, `MONTH_END`, `NBA_MONTH`, engagement measures (`EXPOSURE`, `LIGHT_ENGAGEMENT`, `DEEP_ENGAGEMENT`, `TOTAL_ENGAGEMENT`, `ENGAGEMENT_SCORE`) and HCP attributes (value pool, microsegment, HF/CKD flags, access).

## 2. Value comparison (channel, vendor/tactic, brand)

Values compared after `UPPER(TRIM())`; overlap = count of shared distinct values.

| Concept | NPP column (distinct) | Best MMX match (distinct) | Overlap / notes |
| --- | --- | --- | --- |
| Brand | `PROD_BRAND_NM` (68) | `BRND_NM` (55) | 48 shared. Top-brand volumes close (KERENDIA 129.5M vs 126.6M; LYNKUET 49.3M vs 50.2M). MMX mixes `KERENDIA_HF`/`KERENDIA_CKD` with `KERENDIA HF`/`KERENDIA CKD` – needs normalization. NPP has suffixed variants (`NUBEQA-V4`, `MIRENA-2ND-SOW`). |
| Channel | `CHNL_NM` (6) / `RPT_CHNL` (9) | `CHANNEL` (7) | 5 shared: BANNER, HQ EMAIL, 3RD PARTY EMAIL, CUSTOM, IREP EMAIL. MMX adds CALL, SAMPLE (field). NPP adds WEBSITE VISIT and THIRD PARTY EMAIL (spelling variant). `CHNL_TYP` (PAID/OWNED MEDIA) has no MMX match. |
| Vendor | `VEND_NM` (39) | `SRC_SYS_CD` (53) | `VEND_NM` vs `VNDR_TACTC_NM` overlap is only 1. True match is `SRC_SYS_CD` (PULSEPOINT, MEDSCAPE, DOXIMITY, DOCEREE, PEERDIRECT, DMD, POCN, OPENEVIDENCE) – based on value inspection, overlap not yet computed. |
| Tactic detail | `TACT_NM` (2,136) | `VNDR_TACTC_NM` (1,338) | 1,238 shared – strong match. `TACT_NM` is null on ~381M NPP rows. `TACT_NM` vs `TACTIC_NAME` overlap only 56. |
| Tactic type | `TACT_TYP` (127) | `TACTIC_NAME` (149) | Similar values by inspection (HQ EMAIL, DOCNEWS, EHR BANNER, BA360, MDFI - EMAIL). MMX splits PROGRAMATIC into PROGRAMATIC_DISPLAY / PROGRAMATIC_CTV. |

## 3. Recommended join / mapping keys
- Brand: `PROD_BRAND_NM` ↔ `BRND_NM` (after normalizing underscores/spaces and suffixes)
- Channel: `CHNL_NM` ↔ `CHANNEL`
- Vendor: `VEND_NM` ↔ `SRC_SYS_CD`
- Tactic detail: `TACT_NM` ↔ `VNDR_TACTC_NM`
- Tactic type: `TACT_TYP` ↔ `TACTIC_NAME`

## 4. Observations and open items
- Volumes differ within shared channels (e.g., 3RD PARTY EMAIL 12.4M in NPP vs 6.5M in MMX), suggesting different date coverage or filtering.
- Pending: compute `VEND_NM` vs `SRC_SYS_CD` and `TACT_TYP` vs `TACTIC_NAME` overlap; validate `BAYER_HCP_ID` ↔ `BH_ID`; align date ranges before comparing volumes.