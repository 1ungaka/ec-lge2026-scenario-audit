"""Checks on the committed tables and on the frozen prediction sets."""

import hashlib

import pandas as pd
import pytest

from ecaudit.constants import FROZEN_DIR, METRICS, PROCESSED_DIR, SHARE_METRICS, TURNOUT_METRIC
from ecaudit.predict import freeze, prior_work


@pytest.fixture(scope="module")
def results_2016():
    return pd.read_csv(PROCESSED_DIR / "municipal_results_2016.csv")


@pytest.fixture(scope="module")
def results_2021():
    return pd.read_csv(PROCESSED_DIR / "municipal_results_2021.csv")


@pytest.fixture(scope="module")
def frozen():
    return pd.read_csv(FROZEN_DIR / freeze.PREDICTIONS_FILE)


def test_2021_table_matches_the_iec_provincial_totals(results_2021):
    assert len(results_2021) == 33
    assert results_2021["registered_voters"].sum() == 3_253_307
    assert results_2021["mec7_votes"].sum() == 17_923
    assert results_2021["votes_cast"].sum() == 1_522_726
    assert results_2021["pr_valid_votes"].sum() == 1_471_069
    assert results_2021["pr_spoilt_votes"].sum() == 37_034


def test_2016_table_matches_the_iec_provincial_totals(results_2016):
    assert len(results_2016) == 33
    assert results_2016["registered_voters"].sum() == 3_337_532
    assert results_2016["pr_valid_votes"].sum() == 1_832_048
    assert results_2016["pr_spoilt_votes"].sum() == 42_790


def test_recorded_validations_all_passed():
    for year in (2016, 2021):
        record = pd.read_csv(PROCESSED_DIR / f"validation_{year}.csv")
        assert len(record) == 12
        assert record["passed"].all()


def test_frozen_files_match_their_recorded_hashes():
    lines = (FROZEN_DIR / freeze.HASH_FILE).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        expected, name = line.split(maxsplit=1)
        assert hashlib.sha256((FROZEN_DIR / name).read_bytes()).hexdigest() == expected


def test_prior_work_files_are_unmodified():
    prior_work.verify_checksums()


def test_frozen_predictions_can_be_rebuilt_exactly(results_2016, results_2021, frozen):
    rebuilt = freeze.build_predictions(results_2016, results_2021)
    pd.testing.assert_frame_equal(rebuilt, frozen, check_exact=False, atol=1e-6)


def test_frozen_predictions_pass_their_own_checks(frozen):
    freeze.check_predictions(frozen)


def test_frozen_format_and_size(frozen):
    assert list(frozen.columns) == ["municipality", "metric", "prediction_set"] + [
        "value",
        "low",
        "high",
    ]
    counts = frozen.groupby("prediction_set").size().to_dict()
    assert counts == {
        "baseline_no_change": 33 * len(METRICS),
        "baseline_relative_persistence": 33,
        "baseline_trend": 33 * len(METRICS),
        "baseline_uniform_swing": 33 * len(METRICS),
        "team_party_trend": 33 * len(SHARE_METRICS),
        "team_party_validated": 33 * len(SHARE_METRICS),
        "team_turnout_partial_recovery": 33,
        "team_turnout_repeat2021": 33,
        "team_turnout_return2016": 33,
    }


def test_each_team_level_is_stored_as_published(frozen):
    published = pd.read_csv(prior_work.PRIOR_WORK_DIR / "turnout_scenarios_2026.csv")
    row = published.query("MuniCode == 'EC102' and ScenarioKey == 'Return2016'").iloc[0]
    stored = frozen.query(
        "municipality == 'EC102' and prediction_set == 'team_turnout_return2016'"
    ).iloc[0]
    assert stored["value"] == pytest.approx(row["Turnout_%"], abs=1e-6)
    assert stored["low"] == pytest.approx(row["Low_%"], abs=1e-6)
    assert stored["high"] == pytest.approx(row["High_%"], abs=1e-6)


def test_team_party_band_comes_from_the_published_column(frozen):
    stored = frozen.query(
        "municipality == 'BUF' and prediction_set == 'team_party_validated' "
        "and metric == 'share_ANC'"
    ).iloc[0]
    assert stored["high"] - stored["value"] == pytest.approx(2.68619, abs=1e-5)


def test_no_change_equals_the_2021_results(frozen, results_2021):
    stored = frozen[frozen["prediction_set"] == "baseline_no_change"]
    stored = stored.pivot(index="municipality", columns="metric", values="value")
    actual = results_2021.set_index("municipality_code")[list(METRICS)]
    pd.testing.assert_frame_equal(
        stored[list(METRICS)], actual, check_names=False, check_exact=False, atol=1e-6
    )


def test_relative_persistence_differs_from_no_change_but_keeps_the_level(frozen):
    turnout = frozen[frozen["metric"] == TURNOUT_METRIC].pivot(
        index="municipality", columns="prediction_set", values="value"
    )
    persistence = turnout["baseline_relative_persistence"]
    no_change = turnout["baseline_no_change"]
    assert persistence.mean() == pytest.approx(no_change.mean(), abs=1e-5)
    assert (persistence - no_change).abs().max() > 1


def test_incomplete_set_is_rejected(frozen):
    with pytest.raises(ValueError, match="33 municipalities"):
        freeze.check_predictions(frozen.iloc[1:])


def test_value_outside_its_range_is_rejected(frozen):
    broken = frozen.copy()
    broken.loc[0, "value"] = broken.loc[0, "high"] + 1
    with pytest.raises(ValueError, match="outside their own range"):
        freeze.check_predictions(broken)
