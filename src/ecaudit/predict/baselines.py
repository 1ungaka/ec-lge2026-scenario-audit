"""The simple baselines. Each uses only the official 2016 and 2021 municipal results."""

import pandas as pd

from ecaudit.constants import METRICS, SHARE_METRICS, TURNOUT_METRIC

BAND_QUANTILE = 0.9
PREDICTION_COLUMNS = ["municipality", "metric", "prediction_set", "value", "low", "high"]


def metric_table(results: pd.DataFrame) -> pd.DataFrame:
    """Return turnout and party shares indexed by municipal code."""
    return results.set_index("municipality_code")[list(METRICS)].sort_index()


def normalise_shares(wide: pd.DataFrame) -> pd.DataFrame:
    """Floor shares at zero and rescale each municipality to 100."""
    out = wide.copy()
    shares = out[list(SHARE_METRICS)].clip(lower=0)
    out[list(SHARE_METRICS)] = shares.div(shares.sum(axis=1), axis=0) * 100
    return out


def _finish(wide: pd.DataFrame) -> pd.DataFrame:
    out = normalise_shares(wide)
    out[TURNOUT_METRIC] = out[TURNOUT_METRIC].clip(0, 100)
    return out


def no_change(results_2021: pd.DataFrame) -> pd.DataFrame:
    """Predict that every municipality repeats 2021."""
    return metric_table(results_2021)


def trend(results_2016: pd.DataFrame, results_2021: pd.DataFrame) -> pd.DataFrame:
    """Continue each municipality's own 2016-2021 change for one more election."""
    earlier, later = metric_table(results_2016), metric_table(results_2021)
    return _finish(later + (later - earlier))


def provincial_swing(results_2016: pd.DataFrame, results_2021: pd.DataFrame) -> pd.Series:
    """Return the 2016-2021 provincial change in each metric.

    Party swings use provincial PR vote shares. The turnout swing uses the unweighted mean
    across municipalities, which is the provincial level used in the evaluation.
    """

    def provincial(results: pd.DataFrame) -> pd.Series:
        votes = results["pr_valid_votes"]
        shares = {metric: (results[metric] * votes).sum() / votes.sum() for metric in SHARE_METRICS}
        return pd.Series({TURNOUT_METRIC: results[TURNOUT_METRIC].mean(), **shares})

    return (provincial(results_2021) - provincial(results_2016))[list(METRICS)]


def uniform_swing(results_2016: pd.DataFrame, results_2021: pd.DataFrame) -> pd.DataFrame:
    """Add the 2016-2021 provincial swing to every municipality's 2021 result."""
    swing = provincial_swing(results_2016, results_2021)
    return _finish(metric_table(results_2021) + swing)


def relative_persistence(results_2016: pd.DataFrame, results_2021: pd.DataFrame) -> pd.DataFrame:
    """Hold the provincial turnout at 2021 and use the average relative pattern.

    The relative pattern is a municipality's turnout minus the unweighted provincial mean.
    It is averaged over 2016 and 2021 because holding the level at 2021 and keeping the 2021
    pattern alone would reproduce the no-change baseline exactly.
    """
    earlier = metric_table(results_2016)[TURNOUT_METRIC]
    later = metric_table(results_2021)[TURNOUT_METRIC]
    pattern = ((earlier - earlier.mean()) + (later - later.mean())) / 2
    predicted = (later.mean() + pattern).clip(0, 100)
    return predicted.to_frame(TURNOUT_METRIC)


def backtest_bands(results_2016: pd.DataFrame, results_2021: pd.DataFrame) -> pd.Series:
    """Return the 90th percentile of the absolute 2016-2021 change, per metric.

    This is how far the no-change rule would have missed in its only available backtest.
    """
    change = (metric_table(results_2021) - metric_table(results_2016)).abs()
    return change.quantile(BAND_QUANTILE)


def to_long(wide: pd.DataFrame, prediction_set: str, bands: pd.Series) -> pd.DataFrame:
    """Convert a wide prediction table to the common long format."""
    long = (
        wide.rename_axis("municipality")
        .reset_index()
        .melt(id_vars="municipality", var_name="metric", value_name="value")
    )
    long["prediction_set"] = prediction_set
    band = long["metric"].map(bands)
    long["low"] = (long["value"] - band).clip(lower=0)
    long["high"] = (long["value"] + band).clip(upper=100)
    return long[PREDICTION_COLUMNS]
