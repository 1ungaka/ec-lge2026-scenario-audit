"""Read the team's published scenario files into the common long format.

Only their output CSVs are read. Each assumption level stays a separate prediction set.
"""

import hashlib
from pathlib import Path

import pandas as pd

from ecaudit.constants import PARTIES, PRIOR_WORK_DIR
from ecaudit.predict.baselines import PREDICTION_COLUMNS

TURNOUT_SETS = {
    "Repeat2021": "team_turnout_repeat2021",
    "PartialRecovery": "team_turnout_partial_recovery",
    "Return2016": "team_turnout_return2016",
}
PARTY_SETS = {
    "Validated status quo": "team_party_validated",
    "Trend continues (not validated)": "team_party_trend",
}


def verify_checksums(folder: Path = PRIOR_WORK_DIR) -> None:
    """Fail if any stored file differs from the bytes recorded when it was copied."""
    for line in (folder / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split(maxsplit=1)
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"{name} has changed since it was copied")


def turnout_sets(folder: Path = PRIOR_WORK_DIR) -> pd.DataFrame:
    """Return the three turnout assumption levels with their published low-high ranges."""
    raw = pd.read_csv(folder / "turnout_scenarios_2026.csv")
    long = pd.DataFrame(
        {
            "municipality": raw["MuniCode"],
            "metric": "turnout_pct",
            "prediction_set": raw["ScenarioKey"].map(TURNOUT_SETS),
            "value": raw["Turnout_%"],
            "low": raw["Low_%"],
            "high": raw["High_%"],
        }
    )
    return long[PREDICTION_COLUMNS]


def party_sets(folder: Path = PRIOR_WORK_DIR) -> pd.DataFrame:
    """Return the two party scenarios.

    The team publishes one symmetric band, `PartyBand_pts`, not low and high columns, so
    the range is the share plus or minus that band, limited to 0-100.
    """
    raw = pd.read_csv(folder / "party_scenarios_2026.csv")
    bands = pd.read_csv(folder / "municipality_scenarios_2026.csv")
    bands = bands.set_index("MuniCode")["PartyBand_pts"]
    long = raw.melt(
        id_vars=["MuniCode", "Scenario"], value_vars=list(PARTIES), var_name="party", value_name="v"
    )
    band = long["MuniCode"].map(bands)
    frame = pd.DataFrame(
        {
            "municipality": long["MuniCode"],
            "metric": "share_" + long["party"],
            "prediction_set": long["Scenario"].map(PARTY_SETS),
            "value": long["v"],
            "low": (long["v"] - band).clip(lower=0),
            "high": (long["v"] + band).clip(upper=100),
        }
    )
    return frame[PREDICTION_COLUMNS]
