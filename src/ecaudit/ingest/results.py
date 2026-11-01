"""Load one election's IEC files, build its municipal table and validate it.

The same steps run for every election, so results day needs only the new files.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ecaudit.constants import MUNICIPALITY_CODES, RAW_IEC_DIR
from ecaudit.harmonise.tidy import build_municipal_table
from ecaudit.harmonise.validate import Check, validate_results
from ecaudit.ingest.download import MissingSourceError, sources_for
from ecaudit.ingest.parse import read_detailed, read_results_summary, read_turnout_report


@dataclass(frozen=True)
class YearFiles:
    detailed: pd.DataFrame
    turnout_report: pd.DataFrame
    results_summary: pd.DataFrame
    municipal_summaries: dict[str, pd.DataFrame]


def load_year(year: int, raw_root: Path = RAW_IEC_DIR, file_year: int | None = None) -> YearFiles:
    """Read a year's files. `file_year` lets a test read another year's files as stand-ins."""
    folder = raw_root / str(file_year or year)
    missing = [s for s in sources_for(year) if not (folder / s.relative_path).exists()]
    if missing:
        listing = "\n".join(f"  {folder / s.relative_path}\n    from {s.url}" for s in missing)
        raise MissingSourceError(f"Missing {len(missing)} IEC files for {year}:\n{listing}")
    return YearFiles(
        detailed=read_detailed(folder / "detailed_results.csv"),
        turnout_report=read_turnout_report(folder / "voter_turnout.xls"),
        results_summary=read_results_summary(folder / "results_summary.xls"),
        municipal_summaries={
            code: read_results_summary(folder / "municipal_summaries" / f"{code}.xls")
            for code in MUNICIPALITY_CODES
        },
    )


def ingest_year(
    year: int, raw_root: Path = RAW_IEC_DIR, file_year: int | None = None
) -> tuple[pd.DataFrame, list[Check]]:
    """Return the validated municipal table and every validation outcome."""
    files = load_year(year, raw_root, file_year)
    table = build_municipal_table(files.detailed, files.turnout_report, year)
    checks = validate_results(
        table,
        files.detailed,
        files.turnout_report,
        files.results_summary,
        files.municipal_summaries,
    )
    return table, checks
