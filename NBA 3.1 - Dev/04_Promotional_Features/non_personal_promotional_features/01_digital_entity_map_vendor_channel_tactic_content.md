# Digital Entity Map: Vendors, Channels, Tactics and Content — with NBA 3.0 and OE 2.0 Coverage

**Group:** Non-personal promotional features (HCP digital and DTC)  
**Purpose:** one picture of how the digital operation is organised (audience → channel → vendor → tactic / placement → content → metric), and where the NBA 3.0 model and the OE 2.0 model touch it  
**Built from:** `kerendia_oe_journey.mmx_fnl_combined_aggr_tab` (Kerendia, January 2025 to October 2026), `kerendia_oe_journey.content_matrix_oe_2`, the OE 2.0 training table `final_mdb_oe_2_0_22_instances_append_full`, the NBA 3.0 model run `f583bcbc9d56477fae983d44c16f8c70`, and the tactic rules of notebook `24_Features_Digital` (see `10_hcp_digital_paid_media_nba_3_0.md`)  
**Date:** October 26, 2026

**Diagrams.** The diagrams are written in Mermaid. They render in GitHub and in most Markdown viewers; if your viewer shows code instead, every diagram is followed by a table with the same information.

## 1. How to read the map

**The levels.** Every digital touch can be described by six levels. The same word ("channel") means different things in the two systems, so this map uses the names below.

| Level | Meaning | In the MMX table (NBA 3.0) | In OE 2.0 | Example |
| --- | --- | --- | --- | --- |
| Audience | Who receives it | (not a column) | (not a column) | HCP digital, DTC |
| Channel | The format group | `CHANNEL` (5 values) | (not used on its own) | Banner, 3rd Party Email, Custom, HQ Email, iRep Email |
| Vendor | The media partner or system that delivers and reports it | `SRC_SYS_CD` | `VEND_NM` | Doximity, Medscape, PulsePoint |
| Tactic / placement | The specific product of the vendor | `TACTIC_NAME`, then mapped to 15 NBA labels | `CHNL_NM_NEW`, combined with vendor (e.g. `DOXIMITY_DOCSPOT`); this is what OE calls a "channel" | DocSpot, Email Alert, MDFI - Email |
| Content | What the message is about | (none) | Content category from litcode tagging | `GUIDELINES`, `ACCESS_COVERAGE` |
| Metric | What the doctor did | `EXPOSURE`, `LIGHT_ENGAGEMENT`, `DEEP_ENGAGEMENT`, `TOTAL_ENGAGEMENT` | `R` (reach), `I` (interaction), `E` (engagement) per vendor metric | DocSpot `VIEW` = R, `VIDEO_PLAY_5S` = I, `CLICK_THROUGH` = E |

**The labels (colours in the diagrams, tags in the tables).**

| Tag | Colour | Meaning |
| --- | --- | --- |
| `NBA-M` | Blue | Used by the **NBA 3.0 model** (feature selected in run `f583bcbc...`) |
| `OE-R` | Orange | **Recommended by OE 2.0**: one of the 12 placements the OE optimiser plans and sends to vendors (also an OE model input) |
| `OE-F` | Yellow | Used by the **OE 2.0 model** as a feature or journey channel, but not recommended |
| `BOTH` | Purple | Used by both the NBA 3.0 model and the OE 2.0 model |
| `NBA-B` | Grey | NBA 3.0 **builds** features for it, but neither model uses them |

**Volumes.** "Rows" are activity rows in the MMX table (one doctor, one day, one vendor, one tactic), January 2025 to October 2026. They show relative size, not impressions.

**Important caveat on tactic labels.** The mapping from vendor tactic name to NBA tactic label in this document is **reconstructed**: the rules of notebook `24` (any name containing "Banner" becomes `BANNER_TACTIC`, a fixed list of exact names, everything else becomes `OTHER_TACTIC`) were applied to the current MMX data. Empty tactic names are assumed to fall into `OTHER_TACTIC`. NBA 3.0 was trained on an earlier window, where some tactic names were different.

## 2. The big picture

```mermaid
flowchart LR
    HCP["HCP digital<br/>doctor level (NPI)"]
    DTC["DTC<br/>region level (DMA)"]

    HCP --> BAN["Banner<br/>106.4M rows"]
    HCP --> TPE["3rd Party Email<br/>2.4M rows"]
    HCP --> CUS["Custom<br/>4.2M rows"]
    HCP --> HQ["HQ Email<br/>9.4M rows"]
    HCP --> IREP["iRep Email<br/>0.5M rows"]

    BAN --> V_PP["PulsePoint"]
    BAN --> V_MS1["Medscape"]
    BAN --> V_PD1["PeerDirect"]
    BAN --> V_DO["Doceree, OpenEvidence"]
    BAN --> V_BO["Biopharm, ConnectiveRx, Nativo,<br/>Haymarket, ..."]

    TPE --> V_MS2["Medscape"]
    TPE --> V_PD2["PeerDirect"]
    TPE --> V_TO["Haymarket, Biopharm,<br/>Healthcast, MJH Life Sciences"]

    CUS --> V_DOX["Doximity"]
    CUS --> V_MS3["Medscape"]
    CUS --> V_EPO["Epocrates"]
    CUS --> V_PRP["Prescriber Point"]
    CUS --> V_PD3["PeerDirect"]
    CUS --> V_CO["Impiricus, MD Calc,<br/>ReachMD, Haymarket, MJH"]

    HQ --> V_HQ["Bayer HQ email (SFMC)"]
    IREP --> V_IR["Rep-triggered email (iRep)"]

    DTC --> V_DTC["WebMD, Healthline, Health Union,<br/>Sharecare, Facebook / Instagram"]
    DTC -.-> V_DTCX["PulsePoint DTC, The Trade Desk<br/>(loaded but never used)"]

    classDef nbaM fill:#cfe2ff,stroke:#0d6efd,color:#000
    classDef oeR fill:#ffd8a8,stroke:#fd7e14,color:#000
    classDef oeF fill:#fff3bf,stroke:#f59f00,color:#000
    classDef both fill:#d0bfff,stroke:#6f42c1,color:#000
    classDef nbaB fill:#f1f3f5,stroke:#adb5bd,color:#495057

    class BAN both
    class TPE,CUS oeF
    class HQ both
    class IREP both
    class V_PP,V_MS1,V_MS2,V_PD2,V_PD3,V_DOX,V_MS3 oeR
    class V_HQ both
    class V_IR both
    class V_EPO,V_PRP oeF
    class V_PD1 both
    class V_DO nbaM
    class V_BO,V_TO,V_CO nbaB
    class V_DTC both
    class V_DTCX nbaB
```

**What the picture shows.**

* **HCP digital** has five channels. Banner is by far the largest by rows (PulsePoint programmatic display alone is 99% of banner rows); Custom (vendor-specific programs such as Doximity DocNews or Medscape BrandAlert) and HQ email carry most of the content-rich touches.
* **NBA 3.0** uses digital only at a coarse level: the **Banner channel**, a **banner tactic** total, **HQ email** and **iRep email**, plus the **DTC** consumer media. It never uses a media partner (Doximity, Medscape, ...) or a placement by name.
* **OE 2.0** works at the **vendor + placement** level for Doximity, Medscape, PeerDirect, PulsePoint and SFMC (these are the placements it recommends), and uses MMX totals for Epocrates and Prescriber Point, which it does not recommend.
* **DTC** is a separate world: region-level consumer media. Both models use the same 9 DTC features.

## 3. Channel by channel

### 3.1 Banner

```mermaid
flowchart LR
    BAN["Banner channel<br/>NBA: DIGITAL_BANNER_* (3 in model)<br/>OE: DIGITAL_BANNER_* (2 in model)"]

    BAN --> PP["PulsePoint<br/>Programatic_DISPLAY<br/>105.5M rows"]
    BAN --> MSB["Medscape<br/>(empty) / Brand Alert<br/>274k rows"]
    BAN --> DOC["Doceree<br/>EHR Banner<br/>99k rows"]
    BAN --> OEV["OpenEvidence<br/>Direct Banner<br/>26k rows"]
    BAN --> PDB["PeerDirect<br/>MDFI / MD Minute / MD Shuffle /<br/>PV Compendium - Banner<br/>8k rows"]
    BAN --> BIO["Biopharm, ConnectiveRx, Nativo<br/>(empty tactic) 460k rows"]
    BAN --> HAY["Haymarket, Healthcast, ReachMD,<br/>LinkedIn, MJH (campaign names) 14k rows"]

    PP --> T_OTH["OTHER_TACTIC"]
    MSB --> T_OTH
    BIO --> T_OTH
    HAY --> T_OTH
    MSB --> T_BA["BRAND_ALERT_TACTIC"]
    DOC --> T_BAN["BANNER_TACTIC<br/>NBA model rank 68"]
    OEV --> T_BAN
    PDB --> T_BAN

    classDef nbaM fill:#cfe2ff,stroke:#0d6efd,color:#000
    classDef oeR fill:#ffd8a8,stroke:#fd7e14,color:#000
    classDef oeF fill:#fff3bf,stroke:#f59f00,color:#000
    classDef both fill:#d0bfff,stroke:#6f42c1,color:#000
    classDef nbaB fill:#f1f3f5,stroke:#adb5bd,color:#495057

    class BAN both
    class PP,MSB oeR
    class DOC,PDB both
    class OEV nbaM
    class BIO oeF
    class HAY nbaB
    class T_BAN nbaM
    class T_OTH oeF
    class T_BA nbaB
```

| Vendor | Tactic name in MMX | Rows | NBA tactic label | NBA 3.0 | OE 2.0 |
| --- | --- | --- | --- | --- | --- |
| PulsePoint | `Programatic_DISPLAY` | 105.5M | `OTHER_TACTIC` | Banner channel only (`NBA-M` at channel level) | `OE-R` `PULSEPOINT_BANNER` (R impressions, I clicks) |
| Medscape | (empty), `Brand Alert` | 274k | `OTHER_TACTIC`, `BRAND_ALERT_TACTIC` | Banner channel only | `OE-R` `MEDSCAPE_BANNER` |
| Doceree | `EHR Banner` | 99k | `BANNER_TACTIC` | `NBA-M` (banner tactic); overall `BOTH` | `OE-F` journey `DOCEREE_BANNER` |
| OpenEvidence | `Direct Banner` | 26k | `BANNER_TACTIC` | `NBA-M` (banner tactic) | not used |
| PeerDirect | `MDFI - Banner`, `MD Minute - Banner`, `MD Shuffle - Banner`, `PV Compendium Quiz Series - Banner` | 8k | `BANNER_TACTIC` | `NBA-M` (banner tactic); overall `BOTH` | `OE-F` journey `PEERDIRECT_MDFI_BANNER`, `PEERDIRECT_MD_MINUTE_BANNER` |
| Biopharm, ConnectiveRx, Nativo | (empty) | 460k | `OTHER_TACTIC` | Banner channel only | `OE-F` journey `NATIVO_BANNER` |
| Haymarket, Healthcast, ReachMD, LinkedIn, MJH | campaign names, `Impression`, `PP SMART PIXEL` | 14k | `OTHER_TACTIC` | Banner channel only | not used |

**Key point.** PulsePoint is 99% of banner rows, but its tactic name (`Programatic_DISPLAY`) does not contain "Banner", so it falls into `OTHER_TACTIC`. On current data, the NBA 3.0 feature `DIGITAL_BANNER_TACTIC_EXPOSURE_IN_LAST_3_MONTH` (the strongest digital feature in the model, rank 68) therefore reflects only Doceree, OpenEvidence and PeerDirect banners, while the Banner **channel** features (`DIGITAL_BANNER_EXPOSURE_*`, `DIGITAL_RUNNING_BANNER_EXPOSURE`) are almost entirely PulsePoint.

### 3.2 3rd Party Email

```mermaid
flowchart LR
    TPE["3rd Party Email channel<br/>NBA: built only<br/>OE: DIGITAL_3RD_PARTY_EMAIL_EXPOSURE_IN_LAST_3_MONTH"]

    TPE --> MSE["Medscape<br/>Email Alert 1.16M<br/>(empty) 556k<br/>Formulary Access Package, Digital Data Trends 28k"]
    TPE --> PDE["PeerDirect<br/>MDFI - Email, MD Minute - Email<br/>200k rows"]
    TPE --> HAYE["Haymarket<br/>conference / campaign names<br/>245k rows"]
    TPE --> BIOE["Biopharm (empty) 190k<br/>MJH (empty) 13k<br/>Healthcast Clinical Conversation 13k"]

    MSE --> T_EA["EMAIL_ALERT_TACTIC"]
    MSE --> T_OTH2["OTHER_TACTIC"]
    PDE --> T_OTH2
    HAYE --> T_OTH2
    BIOE --> T_OTH2

    classDef oeR fill:#ffd8a8,stroke:#fd7e14,color:#000
    classDef oeF fill:#fff3bf,stroke:#f59f00,color:#000
    classDef nbaB fill:#f1f3f5,stroke:#adb5bd,color:#495057

    class TPE oeF
    class MSE,PDE oeR
    class HAYE,BIOE nbaB
    class T_EA nbaB
    class T_OTH2 oeF
```

| Vendor | Tactic name in MMX | Rows | NBA tactic label | NBA 3.0 | OE 2.0 |
| --- | --- | --- | --- | --- | --- |
| Medscape | `Email Alert` | 1.16M | `EMAIL_ALERT_TACTIC` | `NBA-B` | `OE-R` `MEDSCAPE_3RD_PARTY_EMAIL` (R delivery, I open, E click) |
| Medscape | (empty), `Formulary Access Package`, `Digital Data Trends` | 584k | `OTHER_TACTIC` | `NBA-B` | same placement as above |
| PeerDirect | `MDFI - Email`, `MD Minute - Email` | 200k | `OTHER_TACTIC` | `NBA-B` | `OE-R` `PEERDIRECT_MDFI_EMAIL` (R), `PEERDIRECT_MD_MINUTE_EMAIL` (R) |
| Haymarket | conference and campaign names (AHA, HFSA, ...) | 245k | `OTHER_TACTIC` | `NBA-B` | not used |
| Biopharm, MJH Life Sciences, Healthcast | (empty), `Clinical Conversation` | 215k | `OTHER_TACTIC` | `NBA-B` | `OE-F` journey `MJHLIFESCIENCES_3RD_PARTY_EMAIL` |

**Key point.** NBA 3.0 uses nothing from 3rd-party email. OE uses it at two levels: the MMX channel total, and event-level open / click counts for Medscape and PeerDirect, which it also recommends.

### 3.3 Custom (vendor-specific programs)

```mermaid
flowchart LR
    CUS["Custom channel<br/>NBA: built only<br/>OE: DIGITAL_CUSTOM_* (5 in model)"]

    CUS --> DOX["Doximity<br/>vendor: OE DIGITAL_DOXIMITY_EXPOSURE_IN_LAST_6_MONTH"]
    DOX --> DX_N["DocNews 1.14M"]
    DOX --> DX_P["DocPoint 131k"]
    DOX --> DX_S["DocSpot 112k"]
    DOX --> DX_F["FormularyOne 29k"]
    DOX --> DX_A["Announcement 18k"]

    CUS --> MS["Medscape<br/>vendor: OE DIGITAL_MEDSCAPE_EXPOSURE_IN_LAST_12_MONTH"]
    MS --> MS_BA["BA360 - Brand Alert 1.01M<br/>Brand Alert 106k"]
    MS --> MS_O["Offsite Media, Media,<br/>BA360 - Email Alert 950k"]
    MS --> MS_X["ReCAP, Fast Five Quiz, BrandSpot,<br/>XC On Demand, others 95k"]

    CUS --> EPO["Epocrates<br/>vendor: OE DIGITAL_EPOCRATES_* (12 in model)"]
    EPO --> EP_M["Monograph Message 81k"]
    EPO --> EP_S["Search Suggestion 55k"]
    EPO --> EP_D["DocAlert 47k"]

    CUS --> PRP["Prescriber Point<br/>Monograph 115k (Mar to Jun 2025)<br/>vendor: OE DIGITAL_PRESCRIBER_POINT_* (7 in model)"]

    CUS --> PDW["PeerDirect<br/>MDFI - Web, MD Minute - Web,<br/>MD Shuffle - Web, PV Compendium - Web 11k"]

    CUS --> CO["Impiricus SMS, MD Calc, ReachMD,<br/>Haymarket, MJH 39k"]

    classDef oeR fill:#ffd8a8,stroke:#fd7e14,color:#000
    classDef oeF fill:#fff3bf,stroke:#f59f00,color:#000
    classDef nbaB fill:#f1f3f5,stroke:#adb5bd,color:#495057

    class CUS,DOX,MS,EPO,PRP oeF
    class DX_N,DX_P,DX_S,DX_A,MS_BA,PDW oeR
    class DX_F,MS_X,EP_M,EP_S,EP_D,CO oeF
    class MS_O nbaB
```

| Vendor | Tactic name in MMX | Rows | NBA tactic label | NBA 3.0 | OE 2.0 |
| --- | --- | --- | --- | --- | --- |
| Doximity | `DocNews` | 1.14M | `DOCNEWS_TACTIC` | `NBA-B` | `OE-R` `DOXIMITY_DOCNEWS` (R headline view; also DocNews email R) |
| Doximity | `DocPoint` | 131k | `OTHER_TACTIC` | `NBA-B` | `OE-R` `DOXIMITY_DOCPOINT` (R view, I video 5s, E click-through) |
| Doximity | `DocSpot` | 112k | `DOCSPOT_TACTIC` | `NBA-B` | `OE-R` `DOXIMITY_DOCSPOT` (R view, I video 5s, E click-through) |
| Doximity | `FormularyOne` | 29k | `FORMULARY_TACTIC` | `NBA-B` | `OE-F` journey `DOXIMITY_FORMULARYONE` |
| Doximity | `Announcement` | 18k | `OTHER_TACTIC` | `NBA-B` | `OE-R` `DOXIMITY_ANNOUNCEMENT` |
| Medscape | `BA360 - Brand Alert`, `Brand Alert` | 1.12M | `OTHER_TACTIC`, `BRAND_ALERT_TACTIC` | `NBA-B` | `OE-R` `MEDSCAPE_BRANDALERT` |
| Medscape | `Offsite Media`, `Media`, `BA360 - Email Alert`, (empty) | 1.23M | `OTHER_TACTIC` | `NBA-B` | vendor total only (`OE-F`) |
| Medscape | `Research Capsule (ReCAP)`, `Fast Five Quiz`, `BrandSpot`, `XC On Demand`, `Digital Data Trends`, `Formulary Access Package` | 95k | `OTHER_TACTIC` | `NBA-B` | `OE-F` journey `MEDSCAPE_RECAP`, `MEDSCAPE_FFQ`, `MEDSCAPE_BRANDSPOT`, `MEDSCAPE_XCOD` |
| Epocrates | `Monograph Message` | 81k | `MONOGRAPH_MESSAGE_TACTIC` | `NBA-B` | `OE-F` vendor (12) + monograph tactic (3) features; journey `EPOCRATES_MONOGRAPH_MESSAGE` |
| Epocrates | `Search Suggestion` | 55k | `OTHER_TACTIC` | `NBA-B` | `OE-F` journey `EPOCRATES_SEARCH_SUGGESTIONS` |
| Epocrates | `DocAlert` | 47k | `DOC_ALERT_TACTIC` | `NBA-B` | `OE-F` journey `EPOCRATES_DOCALERT` |
| Prescriber Point | `Monograph` | 115k | `OTHER_TACTIC` | `NBA-B` | `OE-F` vendor features (7) |
| PeerDirect | `MDFI - Web`, `MD Minute - Web`, `MD Shuffle - Web`, `PV Compendium Quiz Series - Web` | 11k | `OTHER_TACTIC` | `NBA-B` | `OE-R` `PEERDIRECT_MDFI_WEB`; `OE-F` journey `PEERDIRECT_MD_MINUTE_WEB` |
| Impiricus, MD Calc, ReachMD, Haymarket, MJH | `SMS Messages`, `MDSpotlight`, `Email`, `Page View`, ... | 39k | mostly `OTHER_TACTIC` (`Email` → `EMAIL_TACTIC`) | `NBA-B` | `OE-F` journey `IMPIRICUS_MOBILE`, `MD_CALC_BRANDALERT`, `REACHMD_EMAIL`, `REACHMD_DESKTOP` |

**Key points.**

* Custom is where most **recommended** OE placements live (Doximity DocNews / DocPoint / DocSpot / Announcement, Medscape BrandAlert, PeerDirect MDFI web). NBA 3.0 uses nothing from this channel.
* Several of the most important placements fall into NBA's `OTHER_TACTIC`: Medscape `BA360 - Brand Alert` (1.01M rows), Doximity `DocPoint`, Prescriber Point `Monograph`, all PeerDirect web. `OTHER_TACTIC` is therefore a mixture, which may explain why OE's feature selection kept 8 `OTHER_TACTIC` features without knowing what they represent.
* Epocrates and Prescriber Point are strong in OE's model (19 features together) but are **not** recommended by OE: OE learns from them but does not plan them.

### 3.4 HQ Email and iRep Email

```mermaid
flowchart LR
    HQ["HQ Email channel<br/>OE: DIGITAL_HQ_EMAILS_EXPOSURE_IN_LAST_2_MONTH"]
    HQ --> HQV["Vendor code HQ EMAIL (Bayer HQ, SFMC) 9.19M rows<br/>NBA: DIGITAL_HQ_EMAIL_EXPOSURE_IN_LAST_3_MONTH,<br/>DIGITAL_HQ_EMAIL_LIGHT_ENGAGEMENT_IN_LAST_6_MONTH"]
    HQ --> HQJ["Journey codes used as vendor: COPAY 120k,<br/>KERENDIA_FTO 36k, free-trial voucher journeys,<br/>KERENDIA_SIGNUP, Phreesia, BlinkRx, ... 60k"]
    HQV --> T_HQ["HQ_EMAIL_TACTIC<br/>NBA: DIGITAL_RUNNING_HQ_EMAIL_TACTIC_LIGHT_ENGAGEMENT<br/>OE: DIGITAL_HQ_EMAIL_TACTIC_EXPOSURE (2, 3 months)"]
    HQJ --> T_HQ
    HQV --> SFMC["OE placement SFMC_HQ_EMAIL<br/>R delivered, I opened, E clicked<br/>+ TOTAL_SENT_IN_LAST_n_MONTH"]

    IR["iRep Email channel"]
    IR --> IRV["Vendor code IREP EMAIL 532k rows<br/>NBA: DIGITAL_IREP_EMAIL_EXPOSURE_IN_LAST_3 / 6_MONTH"]
    IRV --> T_IR["IREP_EMAIL_TACTIC<br/>OE: DIGITAL_IREP_EMAIL_TACTIC_DEEP_ENGAGEMENT_IN_LAST_12_MONTH"]
    IRV --> IRE["OE placement IREP_EMAIL<br/>I opened, E clicked"]

    classDef nbaM fill:#cfe2ff,stroke:#0d6efd,color:#000
    classDef oeR fill:#ffd8a8,stroke:#fd7e14,color:#000
    classDef oeF fill:#fff3bf,stroke:#f59f00,color:#000
    classDef both fill:#d0bfff,stroke:#6f42c1,color:#000
    classDef nbaB fill:#f1f3f5,stroke:#adb5bd,color:#495057

    class HQ oeF
    class HQV nbaM
    class HQJ nbaB
    class T_HQ both
    class SFMC oeR
    class IR nbaB
    class IRV nbaM
    class T_IR,IRE oeF
```

| Entity | Rows | NBA 3.0 | OE 2.0 |
| --- | --- | --- | --- |
| HQ email, vendor code `HQ EMAIL` | 9.19M | `NBA-M`: `DIGITAL_HQ_EMAIL_EXPOSURE_IN_LAST_3_MONTH` (rank 688), `DIGITAL_HQ_EMAIL_LIGHT_ENGAGEMENT_IN_LAST_6_MONTH` (695) | `OE-R` `SFMC_HQ_EMAIL` (R / I / E), `TOTAL_SENT_IN_LAST_2/3/6/12_MONTH` |
| HQ email, journey codes in the vendor column (`COPAY`, `KERENDIA_FTO`, voucher journeys, ...) | 180k | counted in the HQ email channel and tactic | not separately |
| HQ email tactic (`HQ_EMAIL_TACTIC`) | 9.37M | `NBA-M`: `DIGITAL_RUNNING_HQ_EMAIL_TACTIC_LIGHT_ENGAGEMENT` (698) | `OE-F`: `DIGITAL_HQ_EMAIL_TACTIC_EXPOSURE_IN_LAST_2/3_MONTH` |
| HQ email channel | 9.37M | `NBA-B` | `OE-F`: `DIGITAL_HQ_EMAILS_EXPOSURE_IN_LAST_2_MONTH` |
| iRep email, vendor code `IREP EMAIL` | 532k | `NBA-M`: `DIGITAL_IREP_EMAIL_EXPOSURE_IN_LAST_6_MONTH` (738), `..._3_MONTH` (743) | `OE-F` event `IREP_EMAIL` (I opened, E clicked) |
| iRep email tactic | 532k | `NBA-B` | `OE-F`: `DIGITAL_IREP_EMAIL_TACTIC_DEEP_ENGAGEMENT_IN_LAST_12_MONTH` |

**Key points.**

* In the MMX table, HQ email and iRep email appear as **vendors** (`SRC_SYS_CD` = `HQ EMAIL`, `IREP EMAIL`), so the NBA 3.0 features `DIGITAL_HQ_EMAIL_*` and `DIGITAL_IREP_EMAIL_*` are vendor-level features for Bayer's own email systems, not for a media partner.
* For HQ email, the vendor column also holds **journey codes** (`COPAY`, `KERENDIA_FTO`, free-trial vouchers, ...). These look like separate vendors in NBA's vendor pivot.
* iRep email is sent by reps, so OE uses it as an input but does not recommend it.

## 4. Content layer (OE 2.0 only)

NBA 3.0 has no content dimension. OE tags each message with a content category (from litcode, subject line, creative, ...), and its content matrix (`content_matrix_oe_2`) defines which categories each recommended placement can carry.

```mermaid
flowchart LR
    subgraph Placements["OE recommended placements"]
        P_DXN["Doximity DocNews"]
        P_DXP["Doximity DocPoint / DocSpot"]
        P_DXA["Doximity Announcement"]
        P_MSB["Medscape Brand Alert"]
        P_MSE["Medscape Email Alert"]
        P_PDM["PeerDirect MDFI"]
        P_PDN["PeerDirect MD Minute"]
        P_PP["PulsePoint Banner"]
        P_HQ["SFMC HQ Email"]
    end
    subgraph Content["Content categories"]
        C_UN["UNMET_NEED"]
        C_SE["SAFETY_EFFICACY"]
        C_MOA["MECHANISM_OF_ACTION"]
        C_PP["PATIENT_PROFILE"]
        C_GU["GUIDELINES"]
        C_BPI["BASIC_PRODUCT_INFO"]
        C_AC["ACCESS_COVERAGE"]
        C_DA["DOSING_ADMINISTRATION"]
        C_CO["COST"]
        C_SD["STUDY_DESIGN"]
        C_RWE["REAL_WORLD_EVIDENCE"]
        C_SA["SAMPLES"]
        C_DAM["DISEASE_AWARENESS_MANAGEMENT"]
    end

    P_DXN --> C_GU & C_MOA & C_PP & C_SE & C_UN
    P_DXP --> C_BPI & C_MOA & C_PP & C_SE & C_UN
    P_DXA --> C_AC & C_BPI
    P_MSB --> C_AC & C_DA & C_GU & C_MOA & C_PP & C_SE & C_UN
    P_MSE --> C_DA & C_GU & C_MOA & C_PP & C_SE & C_UN
    P_PDM --> C_MOA & C_PP & C_SE & C_SD & C_UN
    P_PDN --> C_SE
    P_PP --> C_AC & C_BPI & C_CO & C_GU & C_MOA & C_SE & C_UN
    P_HQ --> C_AC & C_DA & C_GU & C_MOA & C_PP & C_RWE & C_SE & C_SA & C_UN & C_DAM

    classDef oeR fill:#ffd8a8,stroke:#fd7e14,color:#000
    classDef oeF fill:#fff3bf,stroke:#f59f00,color:#000
    classDef nbaB fill:#f1f3f5,stroke:#adb5bd,color:#495057
    class P_DXN,P_DXP,P_DXA,P_MSB,P_MSE,P_PDM,P_PDN,P_PP,P_HQ oeR
    class C_UN,C_SE,C_MOA,C_PP,C_GU,C_BPI,C_AC,C_DA,C_CO,C_SD,C_SA,C_DAM oeF
    class C_RWE nbaB
```

**Content allowed per placement** (`content_matrix_oe_2`; X = at least one content item):

| Placement | UNMET_NEED | SAFETY_EFFICACY | MECHANISM_OF_ACTION | PATIENT_PROFILE | GUIDELINES | BASIC_PRODUCT_INFO | ACCESS_COVERAGE | DOSING_ADMINISTRATION | COST | STUDY_DESIGN | REAL_WORLD_EVIDENCE | SAMPLES | DISEASE_AWARENESS_MANAGEMENT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Doximity DocNews | X | X | X | X | X | | | | | | | | |
| Doximity DocPoint | X | X | X | X | | X | | | | | | | |
| Doximity DocSpot | X | X | X | X | | X | | | | | | | |
| Doximity Announcement | | | | | | X | X | | | | | | |
| Medscape Brand Alert | X | X | X | X | X | | X | X | | | | | |
| Medscape Email Alert | X | X | X | X | X | | | X | | | | | |
| PeerDirect MDFI | X | X | X | X | | | | | | X | | | |
| PeerDirect MD Minute | | X | | | | | | | | | | | |
| PeerDirect MD Shuffle | X | | | | | | | | | | | | |
| PulsePoint Banner | X | X | X | | X | X | X | | X | | | | |
| SFMC HQ Email | X | X | X | X | X | | X | X | | | X | X | |
| SFMC Email 1 to 6 | | | | | | | | | | | | | X |

**How content enters the OE 2.0 model.** 13 content counts over the previous 3 months are model features (`UNMET_NEED_COUNT_P3`, `GUIDELINES_COUNT_P3`, ..., plus `GENERAL_COUNT_P3` for untagged touches). `REAL_WORLD_EVIDENCE` can be sent (SFMC HQ email) but is **not** one of the model's content features; it appears only in the journey. The journey input carries 21 content categories in total.

**Gaps between the matrix and the 12 recommended placements.** Medscape Banner and PeerDirect MDFI web are recommended but have no rows of their own in the content matrix (MDFI content is shared between email and web); PeerDirect MD Shuffle has content rows but is not one of the 12 recommended placements.

## 5. DTC (consumer media)

```mermaid
flowchart LR
    DTC["DTC<br/>region (DMA) x month,<br/>linked to doctor by practice location"]
    DTC --> HU["Health Union<br/>impressions (rank 32), clicks (392)"]
    DTC --> FB["Facebook / Instagram<br/>clicks (93), impressions (124)"]
    DTC --> WMD["WebMD<br/>impressions (107), clicks (431)"]
    DTC --> SC["Sharecare<br/>impressions (283), clicks (559)"]
    DTC --> HL["Healthline<br/>impressions (632)"]
    DTC -.-> PPD["PulsePoint DTC, The Trade Desk<br/>prepared but never joined"]

    classDef both fill:#d0bfff,stroke:#6f42c1,color:#000
    classDef nbaB fill:#f1f3f5,stroke:#adb5bd,color:#495057
    class DTC,HU,FB,WMD,SC,HL both
    class PPD nbaB
```

| Vendor | Measures | NBA 3.0 model (rank of 752) | OE 2.0 model |
| --- | --- | --- | --- |
| Health Union | impressions, clicks | 32, 392 | both kept |
| Facebook / Instagram | clicks, impressions | 93, 124 | both kept |
| WebMD | impressions, clicks | 107, 431 | both kept |
| Sharecare | impressions, clicks | 283, 559 | both kept |
| Healthline | impressions | 632 | kept |
| PulsePoint DTC, The Trade Desk | (loaded and prepared) | never added to the table | not used |

**Key point.** DTC is the only area where NBA 3.0 and OE 2.0 use exactly the same features (9 each). DTC is at the region level, so it describes the doctor's area rather than the doctor; OE does not recommend DTC.

## 6. Coverage summary

| Level | NBA 3.0 model uses | OE 2.0 model uses | OE 2.0 recommends |
| --- | --- | --- | --- |
| Channel | Banner | Banner, 3rd Party Email, Custom, HQ Email | (none at channel level) |
| Vendor | `HQ EMAIL`, `IREP EMAIL` (Bayer's own systems) | Doximity, Medscape, Epocrates, Prescriber Point (MMX); Doximity, Medscape, PeerDirect, PulsePoint, SFMC, iRep (event level) | Doximity, Medscape, PeerDirect, PulsePoint, SFMC |
| Tactic / placement | `BANNER_TACTIC`, `HQ_EMAIL_TACTIC` | `OTHER_TACTIC`, `HQ_EMAIL_TACTIC`, `MONOGRAPH_MESSAGE_TACTIC`, `IREP_EMAIL_TACTIC`; 51 journey placements; 12 event-level placements with R / I / E | 12 placements |
| Content | none | 13 content counts; 21 categories in the journey | 14 categories |
| Metric | exposure, light engagement | R, I, E per vendor metric; touchpoint totals | (planned touches) |
| DTC | 9 features | same 9 features | none |

**What this means for NBA 3.1.**

* NBA 3.0 sees digital through a **keyhole**: one channel total (banner, dominated by PulsePoint), a banner tactic that excludes PulsePoint, and Bayer's own emails. Every media partner placement OE recommends is invisible to the NBA 3.0 model.
* `OTHER_TACTIC` hides large and important placements (Medscape BA360 Brand Alert, PulsePoint display, Doximity DocPoint, Prescriber Point, PeerDirect web). A fixed vendor + placement list, as OE uses, would make these visible and stable.
* Content exists only on the OE side. Reusing OE's content tagging is the only way for NBA to know what a touch was about.

## 7. Sources and how to refresh

| Item | Source |
| --- | --- |
| Channel, vendor, tactic and row counts | `kerendia_oe_journey.mmx_fnl_combined_aggr_tab`, `BRND_NM = 'KERENDIA'`, channels other than Call and Sample, January 2025 to October 2026 |
| NBA tactic labels | Rules of notebook `24_Features_Digital`, reconstructed (see section 1 caveat and `10_hcp_digital_paid_media_nba_3_0.md` step 4) |
| NBA 3.0 model features and ranks | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, artifact `Shap_Importances.csv` |
| OE 2.0 model features | Columns of `kerendia_oe_journey.final_mdb_oe_2_0_22_instances_append_full` (champion model `bayer_kerendia_ga_model_oe_2@champion`) |
| OE journey placements and recommended placements | OE 2.0 model configuration (51 journey channels, 12 recommended); see `12_hcp_oe_digital_review_for_nba_3_1.md` |
| Content per placement | `kerendia_oe_journey.content_matrix_oe_2` |
| DTC | `20_dtc_direct_buy_social_nba_3_0.md` |
