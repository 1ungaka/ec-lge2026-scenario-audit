"""Shared fixtures. All data built here is synthetic and exists only to exercise the code."""

from dataclasses import dataclass

import pandas as pd
import pytest

from ecaudit.constants import MUNICIPALITY_CODES


@dataclass
class SyntheticYear:
    detailed: pd.DataFrame
    turnout_report: pd.DataFrame
    results_summary: pd.DataFrame
    municipal_summaries: dict[str, pd.DataFrame]


def _district_rows(code: str, district: int, ballot: str, votes: dict, spoilt: int) -> list[dict]:
    return [
        {
            "municipality_code": code,
            "municipality_label": code,
            "ward": f"Ward {district % 2}",
            "voting_district": district,
            "registered_voters": 500,
            "ballot": ballot,
            "spoilt_votes": spoilt,
            "party": party,
            "valid_votes": count,
        }
        for party, count in votes.items()
    ]


@pytest.fixture
def synthetic_year() -> SyntheticYear:
    """Two districts per municipality, with the higher ballot differing by district."""
    rows = []
    for index, code in enumerate(MUNICIPALITY_CODES):
        first, second = 1000 + 2 * index, 1001 + 2 * index
        rows += _district_rows(
            code,
            first,
            "PR",
            {"AFRICAN NATIONAL CONGRESS": 90, "DEMOCRATIC ALLIANCE": 20, "LOCAL FORUM": 10},
            4,
        )
        rows += _district_rows(code, first, "Ward", {"AFRICAN NATIONAL CONGRESS": 100}, 2)
        rows += _district_rows(
            code,
            second,
            "PR",
            {"AFRICAN NATIONAL CONGRESS": 50, "DEMOCRATIC ALLIANCE": 30, "LOCAL FORUM": 0},
            1,
        )
        rows += _district_rows(code, second, "Ward", {"AFRICAN NATIONAL CONGRESS": 90}, 1)
        rows += _district_rows(code, second, "DC 40%", {"AFRICAN NATIONAL CONGRESS": 40}, 1)
    detailed = pd.DataFrame(rows)

    # First district: PR 124 beats ward 102. Second: ward 91 beats PR 81. So 215 in all.
    votes_cast, registered, mec7 = 215, 1000, 10
    count = len(MUNICIPALITY_CODES)
    turnout_rows = [
        {
            "municipality_code": code,
            "municipality_label": code,
            "registered_voters": registered,
            "mec7_votes": mec7,
            "voter_turnout": votes_cast,
            "turnout_pct": votes_cast / (registered + mec7) * 100,
        }
        for code in MUNICIPALITY_CODES
    ]
    turnout_rows.append(
        {
            "municipality_code": "TOTAL",
            "municipality_label": "Total",
            "registered_voters": registered * count,
            "mec7_votes": mec7 * count,
            "voter_turnout": votes_cast * count,
            "turnout_pct": votes_cast / (registered + mec7) * 100,
        }
    )

    def summary(scale: int) -> pd.DataFrame:
        lines = [
            ("AFRICAN NATIONAL CONGRESS", 140),
            ("DEMOCRATIC ALLIANCE", 50),
            ("LOCAL FORUM", 10),
            ("WARD ONLY PARTY", 0),
            ("Total Valid Votes", 200),
            ("Total Spoilt Votes", 5),
            ("Total Votes Cast", 205),
        ]
        return pd.DataFrame(
            [{"party": name, "ward": 0, "pr": value * scale} for name, value in lines]
        )

    return SyntheticYear(
        detailed=detailed,
        turnout_report=pd.DataFrame(turnout_rows),
        results_summary=summary(count),
        municipal_summaries={code: summary(1) for code in MUNICIPALITY_CODES},
    )
