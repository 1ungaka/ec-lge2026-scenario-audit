"""Fixed facts about the elections, the geography and the common data layout."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
RAW_IEC_DIR = RAW_DIR / "iec"
MANIFEST_PATH = RAW_DIR / "MANIFEST.csv"
EXTERNAL_DIR = REPO_ROOT / "data" / "external"
BOUNDARIES_DIR = EXTERNAL_DIR / "boundaries"
PRIOR_WORK_DIR = EXTERNAL_DIR / "prior_work"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
FROZEN_DIR = PROCESSED_DIR / "predictions_frozen"

# The IEC's electoral event ids, as listed on its municipal results download page.
EVENT_IDS = {2016: 402, 2021: 1091, 2026: 1887}

# IEC province id for the Eastern Cape, and the name it gives province-level report files.
PROVINCE_ID = "1"
PROVINCE_FILE = "EC"

MUNICIPALITY_CODES = (
    "BUF",
    "EC101",
    "EC102",
    "EC104",
    "EC105",
    "EC106",
    "EC108",
    "EC109",
    "EC121",
    "EC122",
    "EC123",
    "EC124",
    "EC126",
    "EC129",
    "EC131",
    "EC135",
    "EC136",
    "EC137",
    "EC138",
    "EC139",
    "EC141",
    "EC142",
    "EC145",
    "EC153",
    "EC154",
    "EC155",
    "EC156",
    "EC157",
    "EC441",
    "EC442",
    "EC443",
    "EC444",
    "NMA",
)
METROS = ("BUF", "NMA")

# Parties scored by name. Every other party on a PR ballot falls in OTHER.
PARTY_ABBREVIATIONS = {
    "AFRICAN NATIONAL CONGRESS": "ANC",
    "DEMOCRATIC ALLIANCE": "DA",
    "ECONOMIC FREEDOM FIGHTERS": "EFF",
    "UNITED DEMOCRATIC MOVEMENT": "UDM",
    "AFRICAN TRANSFORMATION MOVEMENT": "ATM",
}
NAMED_PARTIES = ("ANC", "DA", "EFF", "UDM", "ATM")
PARTIES = (*NAMED_PARTIES, "OTHER")

TURNOUT_METRIC = "turnout_pct"
SHARE_METRICS = tuple(f"share_{party}" for party in PARTIES)
METRICS = (TURNOUT_METRIC, *SHARE_METRICS)
