import pandas as pd
import pytest

from ecaudit.constants import METRICS, PARTIES, SHARE_METRICS, TURNOUT_METRIC
from ecaudit.predict import baselines


def results(rows):
    """Build a results table from (code, turnout, ANC share, DA share, PR valid votes)."""
    records = []
    for code, turnout, anc, da, votes in rows:
        record = dict.fromkeys(METRICS, 0.0)
        record |= {
            "municipality_code": code,
            TURNOUT_METRIC: turnout,
            "share_ANC": anc,
            "share_DA": da,
            "share_OTHER": 100 - anc - da,
            "pr_valid_votes": votes,
        }
        records.append(record)
    return pd.DataFrame(records)


@pytest.fixture
def earlier():
    return results([("A", 60.0, 70.0, 20.0, 100), ("B", 50.0, 40.0, 50.0, 300)])


@pytest.fixture
def later():
    return results([("A", 50.0, 60.0, 30.0, 100), ("B", 46.0, 40.0, 40.0, 300)])


def test_no_change_repeats_2021(later):
    predicted = baselines.no_change(later)
    assert predicted.loc["A", "turnout_pct"] == 50.0
    assert predicted.loc["B", "share_DA"] == 40.0


def test_trend_continues_each_municipality(earlier, later):
    predicted = baselines.trend(earlier, later)
    assert predicted.loc["A", "turnout_pct"] == 40.0
    assert predicted.loc["B", "turnout_pct"] == 42.0
    assert predicted.loc["A", "share_ANC"] == 50.0
    assert predicted.loc["A", "share_DA"] == 40.0


def test_trend_floors_shares_and_rescales_to_100():
    first = results([("A", 50.0, 10.0, 60.0, 100)])
    second = results([("A", 50.0, 4.0, 80.0, 100)])
    predicted = baselines.trend(first, second)
    assert predicted.loc["A", "share_ANC"] == 0
    assert predicted[list(SHARE_METRICS)].sum(axis=1).iloc[0] == pytest.approx(100)


def test_turnout_trend_stays_within_0_and_100():
    first = results([("A", 90.0, 50.0, 40.0, 100)])
    second = results([("A", 50.0, 50.0, 40.0, 100)])
    third = results([("A", 99.0, 50.0, 40.0, 100)])
    assert baselines.trend(first, second).loc["A", "turnout_pct"] == 10.0
    assert baselines.trend(second, third).loc["A", "turnout_pct"] == 100.0


def test_provincial_swing_weights_shares_by_votes(earlier, later):
    swing = baselines.provincial_swing(earlier, later)
    # ANC: (70*100 + 40*300)/400 = 47.5 becomes (60*100 + 40*300)/400 = 45.
    assert swing["share_ANC"] == pytest.approx(-2.5)
    # Turnout uses the unweighted mean: 55 becomes 48.
    assert swing["turnout_pct"] == pytest.approx(-7.0)


def test_uniform_swing_moves_every_municipality_equally(earlier, later):
    predicted = baselines.uniform_swing(earlier, later)
    assert predicted.loc["A", "turnout_pct"] == pytest.approx(43.0)
    assert predicted.loc["B", "turnout_pct"] == pytest.approx(39.0)
    assert predicted.loc["A", "share_ANC"] == pytest.approx(57.5)
    assert predicted[list(SHARE_METRICS)].sum(axis=1).tolist() == pytest.approx([100, 100])


def test_relative_persistence_holds_the_level_and_averages_the_pattern(earlier, later):
    predicted = baselines.relative_persistence(earlier, later)[TURNOUT_METRIC]
    # Relative patterns are +5/-5 in 2016 and +2/-2 in 2021, so +3.5/-3.5 around 48.
    assert predicted["A"] == pytest.approx(51.5)
    assert predicted["B"] == pytest.approx(44.5)
    assert predicted.mean() == pytest.approx(later[TURNOUT_METRIC].mean())


def test_backtest_band_is_the_90th_percentile_of_absolute_change(earlier, later):
    bands = baselines.backtest_bands(earlier, later)
    assert bands["turnout_pct"] == pytest.approx(4 + 0.9 * 6)


def test_to_long_clips_ranges_and_uses_the_common_columns(later):
    wide = baselines.no_change(later)
    bands = pd.Series(dict.fromkeys(METRICS, 45.0))
    long = baselines.to_long(wide, "demo", bands)
    assert list(long.columns) == baselines.PREDICTION_COLUMNS
    assert len(long) == 2 * len(METRICS)
    row = long.query("municipality == 'A' and metric == 'share_ANC'").iloc[0]
    assert (row["low"], row["value"], row["high"]) == (15.0, 60.0, 100.0)
    assert long["low"].min() >= 0


def test_every_party_has_a_metric():
    assert [f"share_{party}" for party in PARTIES] == list(SHARE_METRICS)
