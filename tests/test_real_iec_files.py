"""Checks against the real IEC files.

Raw IEC files are not redistributed, so these are skipped unless `make data` has been run.
"""

import pytest

from ecaudit.constants import RAW_IEC_DIR
from ecaudit.harmonise.validate import require_all_passed
from ecaudit.ingest.parse import read_turnout_report
from ecaudit.ingest.results import ingest_year

needs_raw = pytest.mark.skipif(
    not (RAW_IEC_DIR / "2021" / "detailed_results.csv").exists(),
    reason="raw IEC files are not present",
)


@needs_raw
@pytest.mark.parametrize("year", [2016, 2021])
def test_real_year_passes_every_check(year):
    table, checks = ingest_year(year)
    require_all_passed(checks)
    assert len(table) == 33


@needs_raw
def test_results_day_path_using_2021_files_as_stand_ins():
    """Phase 3 stand-in: a 2026 run with 2021's files must work with no code changes."""
    table, checks = ingest_year(2026, file_year=2021)
    require_all_passed(checks)
    assert set(table["year"]) == {2026}


@needs_raw
def test_turnout_report_total_row():
    report = read_turnout_report(RAW_IEC_DIR / "2021" / "voter_turnout.xls")
    total = report[report["municipality_code"] == "TOTAL"].iloc[0]
    assert total["voter_turnout"] == 1_522_726
    assert total["turnout_pct"] == pytest.approx(46.549, abs=1e-3)
