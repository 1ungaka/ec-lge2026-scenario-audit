"""Assemble every prediction set, check it, and write the frozen files."""

import hashlib
from pathlib import Path

import pandas as pd

from ecaudit.constants import FROZEN_DIR, METRICS, MUNICIPALITY_CODES, SHARE_METRICS, TURNOUT_METRIC
from ecaudit.predict import baselines, prior_work

PREDICTIONS_FILE = "predictions.csv"
SETS_FILE = "prediction_sets.csv"
HASH_FILE = "SHA256SUMS"
ROUNDING = 6
SHARE_SUM_TOLERANCE = 1e-3

SET_DESCRIPTIONS = {
    "team_turnout_repeat2021": ("team", "Team scenario: repeat of 2021 turnout conditions"),
    "team_turnout_partial_recovery": ("team", "Team scenario: half of the 2021 drop regained"),
    "team_turnout_return2016": ("team", "Team scenario: return to 2016 participation"),
    "team_party_validated": ("team", "Team scenario: validated status quo party support"),
    "team_party_trend": ("team", "Team scenario: 2016-2021 party trend continues"),
    "baseline_no_change": ("baseline", "Every municipality repeats its 2021 result"),
    "baseline_trend": ("baseline", "Each municipality continues its own 2016-2021 change"),
    "baseline_uniform_swing": ("baseline", "2016-2021 provincial swing added to 2021"),
    "baseline_relative_persistence": (
        "baseline",
        "Provincial mean turnout held at 2021, with the average 2016 and 2021 relative pattern",
    ),
}


def build_predictions(results_2016: pd.DataFrame, results_2021: pd.DataFrame) -> pd.DataFrame:
    """Return all prediction sets in the common long format, in a fixed order."""
    bands = baselines.backtest_bands(results_2016, results_2021)
    frames = [
        prior_work.turnout_sets(),
        prior_work.party_sets(),
        baselines.to_long(baselines.no_change(results_2021), "baseline_no_change", bands),
        baselines.to_long(baselines.trend(results_2016, results_2021), "baseline_trend", bands),
        baselines.to_long(
            baselines.uniform_swing(results_2016, results_2021), "baseline_uniform_swing", bands
        ),
        baselines.to_long(
            baselines.relative_persistence(results_2016, results_2021),
            "baseline_relative_persistence",
            bands,
        ),
    ]
    combined = pd.concat(frames, ignore_index=True)
    combined[["value", "low", "high"]] = combined[["value", "low", "high"]].astype(float)
    combined[["value", "low", "high"]] = combined[["value", "low", "high"]].round(ROUNDING)
    return combined.sort_values(["prediction_set", "metric", "municipality"], ignore_index=True)


def check_predictions(predictions: pd.DataFrame) -> None:
    """Fail if any prediction set is incomplete or internally inconsistent."""
    unknown = set(predictions["prediction_set"]) - set(SET_DESCRIPTIONS)
    if unknown:
        raise ValueError(f"Undescribed prediction sets: {sorted(unknown)}")
    if not set(predictions["metric"]) <= set(METRICS):
        raise ValueError("Unknown metric in predictions")
    if predictions[["value", "low", "high"]].isna().any().any():
        raise ValueError("Missing values in predictions")
    outside = ~predictions["value"].between(predictions["low"], predictions["high"])
    if outside.any():
        raise ValueError(f"{int(outside.sum())} values lie outside their own range")
    if predictions.duplicated(["prediction_set", "metric", "municipality"]).any():
        raise ValueError("Repeated predictions")
    for (name, metric), rows in predictions.groupby(["prediction_set", "metric"]):
        if set(rows["municipality"]) != set(MUNICIPALITY_CODES):
            raise ValueError(f"{name} {metric} does not cover the 33 municipalities")
    shares = predictions[predictions["metric"].isin(SHARE_METRICS)]
    totals = shares.groupby(["prediction_set", "municipality"])["value"].sum()
    if ((totals - 100).abs() > SHARE_SUM_TOLERANCE).any():
        raise ValueError("Party shares do not sum to 100")


def describe_sets(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, group in predictions.groupby("prediction_set"):
        source, description = SET_DESCRIPTIONS[name]
        covers = "turnout" if set(group["metric"]) == {TURNOUT_METRIC} else "party support"
        if len(set(group["metric"])) == len(METRICS):
            covers = "turnout and party support"
        rows.append(
            {
                "prediction_set": name,
                "source": source,
                "covers": covers,
                "description": description,
            }
        )
    return pd.DataFrame(rows)


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_frozen(predictions: pd.DataFrame, folder: Path = FROZEN_DIR) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(
        folder / PREDICTIONS_FILE, index=False, lineterminator="\n", float_format="%.6f"
    )
    describe_sets(predictions).to_csv(folder / SETS_FILE, index=False, lineterminator="\n")
    lines = [f"{sha256_text(folder / name)}  {name}\n" for name in (PREDICTIONS_FILE, SETS_FILE)]
    (folder / HASH_FILE).write_text("".join(lines), encoding="utf-8", newline="\n")
