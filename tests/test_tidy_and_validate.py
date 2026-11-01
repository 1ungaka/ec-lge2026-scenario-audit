import pandas as pd
import pytest

from ecaudit.constants import MUNICIPALITY_CODES, SHARE_METRICS
from ecaudit.harmonise.tidy import build_municipal_table, turnout_numerator
from ecaudit.harmonise.validate import ValidationError, require_all_passed, validate_results


def validate(year_data, table=None, detailed=None, turnout=None):
    detailed = year_data.detailed if detailed is None else detailed
    turnout = year_data.turnout_report if turnout is None else turnout
    table = build_municipal_table(detailed, turnout, 2021) if table is None else table
    return validate_results(
        table, detailed, turnout, year_data.results_summary, year_data.municipal_summaries
    )


def failed_names(checks):
    return {check.name for check in checks if not check.passed}


def test_numerator_takes_higher_ballot_per_district(synthetic_year):
    numerator = turnout_numerator(synthetic_year.detailed)
    # Per municipality the higher ballot would give 205, the PR total.
    assert (numerator == 215).all()


def test_table_values(synthetic_year):
    table = build_municipal_table(
        synthetic_year.detailed, synthetic_year.turnout_report, 2021
    ).set_index("municipality_code")
    row = table.loc["BUF"]
    assert list(table.index) == sorted(MUNICIPALITY_CODES)
    assert row["registered_voters"] == 1000
    assert row["turnout_pct"] == pytest.approx(215 / 1010 * 100)
    assert row["pr_turnout_pct"] == pytest.approx(205 / 1000 * 100)
    assert row["share_ANC"] == pytest.approx(70.0)
    assert row["share_DA"] == pytest.approx(25.0)
    assert row["share_OTHER"] == pytest.approx(5.0)
    assert row["share_EFF"] == 0
    assert row[list(SHARE_METRICS)].sum() == pytest.approx(100)
    assert row["largest_party"] == "ANC"
    assert row["runner_up"] == "DA"
    assert row["winning_margin_pts"] == pytest.approx(45.0)
    assert row["effective_parties"] == pytest.approx(1 / (0.7**2 + 0.25**2 + 0.05**2))


def test_all_checks_pass_on_consistent_data(synthetic_year):
    require_all_passed(validate(synthetic_year))


def test_changed_vote_is_caught(synthetic_year):
    tampered = synthetic_year.detailed.copy()
    row = tampered.query("municipality_code == 'NMA' and ballot == 'PR'").index[0]
    tampered.loc[row, "valid_votes"] += 1
    checks = validate(synthetic_year, detailed=tampered)
    assert "municipal PR votes per party match the municipal summaries" in failed_names(checks)
    assert "provincial PR votes per party match the results summary" in failed_names(checks)
    with pytest.raises(ValidationError):
        require_all_passed(checks)


def test_changed_registration_is_caught(synthetic_year):
    turnout = synthetic_year.turnout_report.copy()
    turnout.loc[turnout["municipality_code"] == "EC101", "registered_voters"] += 1
    checks = validate(synthetic_year, turnout=turnout)
    assert "registered voters match the turnout report" in failed_names(checks)


def test_missing_municipality_is_caught(synthetic_year):
    detailed = synthetic_year.detailed.query("municipality_code != 'EC444'")
    checks = validate(synthetic_year, detailed=detailed)
    assert "exactly the 33 municipalities" in failed_names(checks)


def test_party_with_votes_missing_from_detailed_is_caught(synthetic_year):
    detailed = synthetic_year.detailed.query("party != 'LOCAL FORUM'")
    checks = validate(synthetic_year, detailed=detailed)
    assert "provincial PR votes per party match the results summary" in failed_names(checks)


def test_repeated_rows_are_caught(synthetic_year):
    detailed = synthetic_year.detailed
    repeated = pd.concat([detailed, detailed[detailed["ballot"] == "PR"].iloc[[0]]])
    table = build_municipal_table(detailed, synthetic_year.turnout_report, 2021)
    checks = validate(synthetic_year, table=table, detailed=repeated)
    assert "no repeated PR rows" in failed_names(checks)
