"""Build the one-row-per-municipality results table for an election."""

import pandas as pd

from ecaudit.constants import NAMED_PARTIES, PARTIES, PARTY_ABBREVIATIONS

PR = "PR"
WARD = "Ward"


def votes_cast_by_district(detailed: pd.DataFrame) -> pd.DataFrame:
    """Return valid, spoilt and cast votes for each voting district and ballot."""
    ballots = detailed[detailed["ballot"].isin([PR, WARD])]
    grouped = ballots.groupby(["municipality_code", "voting_district", "ballot"], as_index=False)
    totals = grouped.agg(valid=("valid_votes", "sum"), spoilt=("spoilt_votes", "first"))
    totals["cast"] = totals["valid"] + totals["spoilt"]
    return totals


def turnout_numerator(detailed: pd.DataFrame) -> pd.Series:
    """Rebuild the IEC's votes-cast count per municipality.

    The IEC takes the higher of the ward and PR votes cast in each voting district, then
    adds the districts up. Taking the higher ballot per municipality gives a smaller,
    wrong number.
    """
    totals = votes_cast_by_district(detailed)
    by_district = totals.groupby(["municipality_code", "voting_district"])["cast"].max()
    return by_district.groupby("municipality_code").sum()


def pr_party_votes(detailed: pd.DataFrame) -> pd.DataFrame:
    """Return PR valid votes per municipality and party."""
    pr_rows = detailed[detailed["ballot"] == PR]
    return pr_rows.groupby(["municipality_code", "party"], as_index=False)["valid_votes"].sum()


def _contest_summary(party_votes: pd.DataFrame) -> pd.Series:
    """Work out the largest party, winning margin and effective number of parties."""
    ranked = party_votes.sort_values("valid_votes", ascending=False)
    shares = ranked["valid_votes"] / ranked["valid_votes"].sum()
    labels = ranked["party"].map(lambda name: PARTY_ABBREVIATIONS.get(name, name))
    return pd.Series(
        {
            "largest_party": labels.iloc[0],
            "runner_up": labels.iloc[1],
            "winning_margin_pts": (shares.iloc[0] - shares.iloc[1]) * 100,
            "effective_parties": 1 / (shares**2).sum(),
        }
    )


def build_municipal_table(
    detailed: pd.DataFrame, turnout_report: pd.DataFrame, year: int
) -> pd.DataFrame:
    """Combine a detailed results file and the turnout report into the tidy table."""
    pr_rows = detailed[detailed["ballot"] == PR]
    districts = pr_rows.drop_duplicates(["municipality_code", "ward", "voting_district"])
    table = pd.DataFrame(
        {
            "registered_voters": districts.groupby("municipality_code")["registered_voters"].sum(),
            "votes_cast": turnout_numerator(detailed),
        }
    )
    official = turnout_report.set_index("municipality_code")
    table["mec7_votes"] = official["mec7_votes"]
    table["turnout_pct"] = (
        table["votes_cast"] / (table["registered_voters"] + table["mec7_votes"]) * 100
    )

    totals = votes_cast_by_district(detailed)
    pr_totals = totals[totals["ballot"] == PR].groupby("municipality_code")
    table["pr_valid_votes"] = pr_totals["valid"].sum()
    table["pr_spoilt_votes"] = pr_totals["spoilt"].sum()
    table["pr_votes_cast"] = pr_totals["cast"].sum()
    table["pr_turnout_pct"] = table["pr_votes_cast"] / table["registered_voters"] * 100

    party_votes = pr_party_votes(detailed)
    grouped = party_votes.assign(
        group=party_votes["party"].map(lambda name: PARTY_ABBREVIATIONS.get(name, "OTHER"))
    )
    wide = grouped.pivot_table(
        index="municipality_code", columns="group", values="valid_votes", aggfunc="sum"
    ).reindex(columns=list(PARTIES), fill_value=0)
    wide = wide.fillna(0)
    for party in PARTIES:
        table[f"share_{party}"] = wide[party] / table["pr_valid_votes"] * 100
    contest = {
        code: _contest_summary(rows) for code, rows in party_votes.groupby("municipality_code")
    }
    table = table.join(pd.DataFrame(contest).T)
    table["winning_margin_pts"] = table["winning_margin_pts"].astype(float)
    table["effective_parties"] = table["effective_parties"].astype(float)
    table.insert(0, "year", year)
    table.index.name = "municipality_code"
    return table.reset_index().sort_values("municipality_code", ignore_index=True)


def round_for_output(table: pd.DataFrame) -> pd.DataFrame:
    """Round floats so that output files are identical across platforms."""
    out = table.copy()
    columns = out.select_dtypes("float").columns
    out[columns] = out[columns].round(6)
    return out


def write_table(table: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    round_for_output(table).to_csv(path, index=False, lineterminator="\n")


__all__ = [
    "NAMED_PARTIES",
    "build_municipal_table",
    "pr_party_votes",
    "turnout_numerator",
    "votes_cast_by_district",
    "write_table",
]
