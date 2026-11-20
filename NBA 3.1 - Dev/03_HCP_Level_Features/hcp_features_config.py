"""Shared constants for the NBA 3.1 HCP-level feature notebooks (03_HCP_Level_Features).

One place for values that several notebooks use, so they cannot drift apart:
  1. paths and source tables
  2. Product Basket loader (latest dated file in final_product_mapping/) and Dx code sets
  3. market events (LOE dates), FDA approval dates, date floors
  4. drug groups and claim type groups

Keep feature-specific choices (windows, column names, checks) in the notebooks.
Temporary: to be merged with 00_cohort_config (dev/hcp-claims-features) into one global config during Ops.

Use in a notebook in this folder:
    import sys, os
    sys.path.insert(0, os.getcwd())          # notebook folder
    import hcp_features_config as cfg
    import importlib; importlib.reload(cfg)  # pick up edits without restarting
"""
import csv
import os
import re

# ============================================================
# 1. Paths and source tables
# ============================================================
CATALOG = "ph-com-ai-us-prod-catalog-2553213839599380"
VOL31 = f"/Volumes/{CATALOG}/kerendia_nba_3/kerendia_nba_3_1_volume"
VOL30 = f"/Volumes/{CATALOG}/kerendia_nba_3/kerendia_nba_3_volume"
HCP_UNIVERSE_PATH = f"{VOL31}/HCP_Universe_without_call_hcps"      # 294,727 HCPs (C1-C4, no call-only HCPs)
COHORTS_DIR = f"{VOL31}/cohorts/claims"
PROMO_COHORTS_DIR = f"{VOL31}/cohorts/promotional"
DEV_PIPELINE = f"{VOL31}/hcp_level_model/dev_pipeline"
QUERY_OUTPUT_31 = f"{DEV_PIPELINE}/query_output"
NB_OUT_31 = f"{DEV_PIPELINE}/notebook_output"
HCP_FEATURES_OUT_31 = f"{NB_OUT_31}/hcp_features"
DX_EVENTS_PATH = f"{QUERY_OUTPUT_31}/dx_input_claims_all_events_features_input"   # Dx event list, ICD-10, 2021-01-02 on
LRX_V7_TABLE = f"`{CATALOG}`.`kerendia_laad_based_lrx`.kerendia_laad_based_lrx_v7"


def assert_31_output(*paths):
    """Stop if an output path is outside the 3.1 volume."""
    bad = [p for p in paths if "kerendia_nba_3_1_volume" not in p]
    assert not bad, f"never write outside the 3.1 volume: {bad}"


# ============================================================
# 2. Product Basket (same logic as product_mapping_path in 00_cohort_config)
# ============================================================
# One dated file per type: <stem>_YYYY_MM_DD.csv. To change a basket, upload a new dated file; the latest is used.
# PRODUCT_MAPPING_DATE pins a date (None = latest).
PRODUCT_MAPPING_DIR = f"{VOL31}/final_product_mapping/"
PRODUCT_MAPPING_DATE = None
_DX_COLS = ["MATCH_TYPE", "MATCH_VALUE", "CLUB_ID", "DIAGNOSIS_DESCRIPTION", "CONDITION", "ACTIVE_STAGING", "CKD_STAGE",
            "CKD_SUBSTAGE", "DM_TYPE", "HF_TYPE", "FLAG", "IS_DEFINING", "IN_752_FEATURES", "PATIENTS_TOTAL", "NOTE"]
PRODUCT_MAPPING_FILES = {   # kind: (file name stem, required columns)
    "rx":  ("Kerendia_Rx_Final_Product_Mapping",
            ["MATCH_TYPE", "MATCH_VALUE", "CLUB_ID", "PRODUCT_GROUP", "TREATMENT_CATEGORY", "BRAND_LABEL", "STRENGTH",
             "CONDITION", "ACTIVE_JOURNEY", "PATIENTS_TOTAL", "IN_752_FEATURES", "NOTE"]),
    "px":  ("Kerendia_Px_Final_Product_Mapping",
            ["MATCH_TYPE", "MATCH_VALUE", "CLUB_ID", "PROCEDURE_DESCRIPTION", "PROC_CATEGORY", "CONDITION", "PX_GROUP",
             "ACTIVE_DIALYSIS", "IS_DEFINING", "IN_752_FEATURES", "PATIENTS_TOTAL", "NOTE"]),
    "dx":  ("Kerendia_Dx_Final_Product_Mapping", _DX_COLS),
    "lab": ("Kerendia_Lab_Final_Product_Mapping",
            ["MATCH_TYPE", "MATCH_VALUE", "TEST_TYPE", "ACTIVE", "ROLE", "PRIORITY", "UNITS", "VALID_MIN", "VALID_MAX",
             "STAGE_CUTOFFS", "TEST_FAMILY", "NOTE"]),
    "dx_flag_additions": ("Kerendia_Dx_Flag_Additions", _DX_COLS),
}


def product_mapping_dates(kind):
    """All dates (YYYY_MM_DD, sorted) of the product mapping files of this kind."""
    stem, _ = PRODUCT_MAPPING_FILES[kind]
    return sorted(m.group(1) for f in os.listdir(PRODUCT_MAPPING_DIR)
                  for m in [re.fullmatch(re.escape(stem) + r"_(\d{4}_\d{2}_\d{2})\.csv", f)] if m)


def product_mapping_path(kind, date=None):
    """Path of the product mapping file: the given date / PRODUCT_MAPPING_DATE, else the latest. Checks the columns."""
    stem, cols = PRODUCT_MAPPING_FILES[kind]
    found = product_mapping_dates(kind)
    assert found, f"No {stem}_<date>.csv in {PRODUCT_MAPPING_DIR}"
    _date = date or PRODUCT_MAPPING_DATE or found[-1]
    assert _date in found, f"{stem}_{_date}.csv not found; available dates: {found}"
    path = f"{PRODUCT_MAPPING_DIR}{stem}_{_date}.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    missing = [c for c in cols if c not in header]
    assert not missing, f"{path}: columns missing {missing}. Use the columns of the previous version."
    return path


def read_product_mapping(kind, date=None):
    """Product mapping as a list of dicts, one row per real code (LIST rows split on '|'), values stripped."""
    path = product_mapping_path(kind, date)
    with open(path, newline="", encoding="utf-8") as fh:
        raw = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
    rows = []
    for r in raw:
        for code in r["MATCH_VALUE"].split("|"):
            rows.append({**r, "CODE": code.strip().upper()})
    return rows


def dx_codes(condition=None, ckd_stage=None, ckd_substage=None, flag=None, dm_type=None, exclude_dm_type=None,
             defining_only=False, date=None):
    """Sorted Dx codes from the latest Dx basket matching every given filter.
    Each filter takes one value or a list, e.g. dx_codes(condition="CKD", ckd_stage=3)."""
    def _set(v):
        return None if v is None else {str(x).upper() for x in (v if isinstance(v, (list, tuple, set)) else [v])}
    want = {"CONDITION": _set(condition), "CKD_STAGE": _set(ckd_stage), "CKD_SUBSTAGE": _set(ckd_substage),
            "FLAG": _set(flag), "DM_TYPE": _set(dm_type)}
    excl = _set(exclude_dm_type) or set()
    out = set()
    for r in read_product_mapping("dx", date):
        if any(v is not None and r[k].upper() not in v for k, v in want.items()):
            continue
        if r["DM_TYPE"].upper() in excl or (defining_only and r["IS_DEFINING"] != "Y"):
            continue
        out.add(r["CODE"])
    return sorted(out)


def dx_code_sets(date=None):
    """CKD code sets used by the HCP feature notebooks, built from the Dx basket columns (no code lists).
      ST3 / ST4  : CONDITION = CKD and CKD_STAGE = 3 / 4
      ESRD       : CKD_SUBSTAGE = ESRD; plus stage 5 combination codes (not N18.x, e.g. hypertensive CKD I12 / I13,
                   where the code does not separate stage 5 from ESRD); plus staged dialysis codes
                   (CONDITION = DIALYSIS with a CKD_STAGE, i.e. Z99.2). Current 3.1 rule; open decision on the
                   unstaged Z49 dialysis codes and on treating I12.0 / I13.11 / I13.2 as ESRD.
      CKD        : CONDITION = CKD, IS_DEFINING = Y, DM_TYPE not OTHER, minus ESRD          (09_claim_comorbidity)
      CKD_ANY    : CONDITION = CKD, DM_TYPE not OTHER (incl. D63.1 anemia in CKD), plus ESRD (11_adoption_features)
    """
    rows = read_product_mapping("dx", date)
    ckd = [r for r in rows if r["CONDITION"] == "CKD"]
    esrd = ({r["CODE"] for r in ckd if r["CKD_SUBSTAGE"] == "ESRD"}
            | {r["CODE"] for r in ckd if r["CKD_STAGE"] == "5" and not r["CODE"].startswith("N18")}
            | {r["CODE"] for r in rows if r["CONDITION"] == "DIALYSIS" and r["CKD_STAGE"] != ""})
    not_other = [r for r in ckd if r["DM_TYPE"] != "OTHER"]
    return {
        "ST3": sorted({r["CODE"] for r in ckd if r["CKD_STAGE"] == "3"}),
        "ST4": sorted({r["CODE"] for r in ckd if r["CKD_STAGE"] == "4"}),
        "ESRD": sorted(esrd),
        "CKD": sorted({r["CODE"] for r in not_other if r["IS_DEFINING"] == "Y"} - esrd),
        "CKD_ANY": sorted({r["CODE"] for r in not_other} | esrd),
    }


# ICD-10 prefix rules (09_claim_comorbidity); code starts with any of the prefixes
DX_PREFIXES = {"T2D": ["E11"], "T1D": ["E10"], "HF": ["I50"], "HF_SYS": ["I50.2"], "HF_DIA": ["I50.3"]}


# ============================================================
# 3. Market events, approval dates, date floors
# ============================================================
# status: build = used for features; defer = known event, not built in 3.1
MARKET_EVENTS = [
    {"event_id": "FARXIGA_LOE",           "event_date": "2026-04-06", "status": "build", "note": "Farxiga generic launch"},
    {"event_id": "ENTRESTO_LOE",          "event_date": "2025-07-01", "status": "build", "note": "Entresto amorphous generic, Jul 2025; exact day to confirm (Q6)"},
    {"event_id": "ENTRESTO_FULL_GENERIC", "event_date": None,         "status": "defer", "note": "Full generic expected 2027"},
    {"event_id": "BAXFENDY_LAUNCH",       "event_date": None,         "status": "defer", "note": "Too few post-event cohorts for NBA 3.1"},
    {"event_id": "EASI_KIDNEY_READOUT",   "event_date": None,         "status": "defer", "note": "Too few post-event cohorts for NBA 3.1"},
    {"event_id": "GLP1_GUIDELINES",       "event_date": None,         "status": "defer", "note": "Too few post-event cohorts for NBA 3.1"},
]


def event_date(event_id):
    """Date (YYYY-MM-DD) of a market event; stops if unknown or without a date."""
    hit = [e for e in MARKET_EVENTS if e["event_id"] == event_id]
    assert hit and hit[0]["event_date"], f"No date for market event {event_id}"
    return hit[0]["event_date"]


FARXIGA_LOE_DATE = event_date("FARXIGA_LOE")
ENTRESTO_LOE_DATE = event_date("ENTRESTO_LOE")

# FDA approval dates (confirm with Medical); no entry = feature not built
APPROVAL_DATES = {"INVOKANA": "2013-03-29", "FARXIGA": "2014-01-08", "JARDIANCE": "2014-08-01", "ENTRESTO": "2015-07-07"}
# NBA 3.0 date floors: Dx and Rx on or after the CKD-indication approval
DATE_FLOORS = {"INVOKANA": "2019-10-01", "FARXIGA": "2021-04-01"}

# ============================================================
# 4. Drug groups and claim types
# ============================================================
# Rx_01_new PRODUCT_NAME groups (11_adoption_features)
ENTRESTO_BRAND_PRODUCTS = ["ENTRESTO"]
ENTRESTO_PRODUCTS = ENTRESTO_BRAND_PRODUCTS + ["SACUBITRIL/VALSARTAN", "SACUBITRIL/VALSART"]   # LAAD generic names (from 2024-11-27)
RX01_DRUG_GROUPS = {
    "INVOKANA":      ["INVOKANA"],
    "FARXIGA":       ["FARXIGA"],
    "JARDIANCE":     ["JARDIANCE"],
    "STEROIDAL_MRA": ["SPIRONOLACTONE", "EPLERENONE"],
    "ENTRESTO":      ENTRESTO_PRODUCTS,
}

# LRx V7 PRODUCT_GROUP groups (31_Competitor_drugs_NBRX_share, 36_market_event_features)
V7_DRUG_GROUPS = {
    "FARXIGA_BRAND":   ["FARXIGA BRAND"],
    "FARXIGA_GENERIC": ["FARXIGA GENERIC"],
    "JARDIANCE":       ["JARDIANCE"],
    "INVOKANA":        ["INVOKANA"],
    "STEGLATRO":       ["STEGLATRO"],
    "GLP1":            ["OZEMPIC", "WEGOVY", "WEGOVY HD", "RYBELSUS", "MOUNJARO", "ZEPBOUND"],
}
V7_FARXIGA_GROUPS = V7_DRUG_GROUPS["FARXIGA_BRAND"] + V7_DRUG_GROUPS["FARXIGA_GENERIC"]
V7_SMRA_CLASS = "sMRA"   # STEROIDAL_MRA = every V7 product with PRODUCT_CLASS sMRA
# Open decision: steroidal MRA and SGLT2 lists differ between 11, 31 and 31_..._nba31 (dev/nbrx-nrx-trx-features).

# Claim types (10_kerendia_prior_writing): PD paid, RJ rejected, RV reversed; approved = paid + reversed
APPROVED_CLAIM_TYPES = ["PD", "RV"]
