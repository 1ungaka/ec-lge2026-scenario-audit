"""Parse the IEC's detailed results CSV and its .xls summary reports.

Report parsers find columns by their header text, not by position, because the layout of
the .xls reports differs between metros and local municipalities.
"""

import io
import re
from pathlib import Path

import pandas as pd
import xlrd

DETAILED_COLUMNS = [
    "Province",
    "Municipality",
    "Ward",
    "VotingDistrict",
    "VotingStationName",
    "RegisteredVoters",
    "BallotType",
    "SpoiltVotes",
    "PartyName",
    "TotalValidVotes",
    "DateGenerated",
]
SUMMARY_TOTALS = ("Total Valid Votes", "Total Spoilt Votes", "Total Votes Cast")


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def split_label(label: str) -> tuple[str, str]:
    """Split an IEC label such as 'BUF - Buffalo City' into code and name."""
    code, name = clean_text(label).split(" - ", 1)
    return code, name


def read_detailed(path: Path) -> pd.DataFrame:
    """Read a detailed results file: one row per voting district, ballot and party."""
    raw = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if list(raw.columns) != DETAILED_COLUMNS:
        raise ValueError(f"{path}: unexpected columns {list(raw.columns)}")
    labels = raw["Municipality"].map(split_label)
    return pd.DataFrame(
        {
            "municipality_code": labels.str[0],
            "municipality_label": labels.str[1],
            "ward": raw["Ward"],
            "voting_district": raw["VotingDistrict"],
            "registered_voters": raw["RegisteredVoters"],
            "ballot": raw["BallotType"],
            "spoilt_votes": raw["SpoiltVotes"],
            "party": raw["PartyName"].map(clean_text),
            "valid_votes": raw["TotalValidVotes"],
        }
    )


def _read_sheet(path: Path) -> list[list[object]]:
    # The IEC's files trigger a harmless xlrd size warning, so its log goes to a buffer.
    book = xlrd.open_workbook(path, logfile=io.StringIO())
    sheet = book.sheet_by_index(0)
    return [sheet.row_values(index) for index in range(sheet.nrows)]


def _header_row(rows: list[list[object]], first_cell: str) -> int:
    for index, row in enumerate(rows):
        if any(clean_text(cell) == first_cell for cell in row):
            return index
    raise ValueError(f"No header row containing {first_cell!r}")


def _column(header: list[object], pattern: str) -> int:
    for index, cell in enumerate(header):
        if re.fullmatch(pattern, clean_text(cell)):
            return index
    raise ValueError(f"No column matching {pattern!r} in {header}")


def _number(value: object) -> float:
    """Read a numeric cell. The IEC writes '-' where a ballot does not apply."""
    if value in ("", "-"):
        return 0.0
    return float(value)


def read_turnout_report(path: Path) -> pd.DataFrame:
    """Read the Voter Turnout report, with the province total as municipality_code 'TOTAL'."""
    rows = _read_sheet(path)
    start = _header_row(rows, "Municipality")
    header = rows[start]
    name = _column(header, "Municipality")
    registered = _column(header, "Registered Voters")
    mec7 = _column(header, "MEC7 Votes")
    voters = _column(header, "Voter Turnout")
    percent = _column(header, "% Voter Turnout")
    records = []
    for row in rows[start + 1 :]:
        label = clean_text(row[name])
        if label == "Total":
            code, municipality = "TOTAL", "Total"
        elif " - " in label:
            code, municipality = split_label(label)
        else:
            continue
        records.append(
            {
                "municipality_code": code,
                "municipality_label": municipality,
                "registered_voters": int(_number(row[registered])),
                "mec7_votes": int(_number(row[mec7])),
                "voter_turnout": int(_number(row[voters])),
                "turnout_pct": _number(row[percent]) * 100,
            }
        )
    return pd.DataFrame(records)


def read_results_summary(path: Path) -> pd.DataFrame:
    """Read a Results Summary report: valid votes per party and ballot, plus the total rows."""
    rows = _read_sheet(path)
    start = _header_row(rows, "Party Name")
    header = rows[start]
    name = _column(header, "Party Name")
    ballots = {"ward": _column(header, "Ward"), "pr": _column(header, "PR")}
    records = []
    for row in rows[start + 2 :]:
        label = clean_text(row[name])
        if not label or label == "Total Voter Turnout":
            continue
        record = {"party": label}
        for ballot, column in ballots.items():
            record[ballot] = int(_number(row[column]))
        records.append(record)
    return pd.DataFrame(records)
