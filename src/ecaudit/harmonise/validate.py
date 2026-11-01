"""Check a municipal table against the IEC's separately published reports."""

from dataclasses import dataclass

import pandas as pd

from ecaudit.constants import MUNICIPALITY_CODES, SHARE_METRICS
from ecaudit.harmonise.tidy import PR, pr_party_votes

SHARE_TOLERANCE = 1e-9
TURNOUT_TOLERANCE = 1e-6


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


class ValidationError(RuntimeError):
    """A table disagrees with the official reports."""


def _compare(name: str, ours: pd.Series, official: pd.Series) -> Check:
    """Compare two series, reporting how many entries differ.

    An entry missing from one side counts as zero: the IEC lists ward-only parties in its
    summaries with 0 PR votes, but they have no PR rows in the detailed file.
    """
    aligned = pd.concat([ours.rename("ours"), official.rename("official")], axis=1).fillna(0)
    differing = aligned[aligned["ours"] != aligned["official"]]
    detail = f"{len(aligned) - len(differing)} of {len(aligned)} match"
    if not differing.empty:
        detail += f"; first difference: {differing.iloc[0].to_dict()} at {differing.index[0]}"
    return Check(name, differing.empty, detail)


def validate_results(
    table: pd.DataFrame,
    detailed: pd.DataFrame,
    turnout_report: pd.DataFrame,
    results_summary: pd.DataFrame,
    municipal_summaries: dict[str, pd.DataFrame],
) -> list[Check]:
    """Run every check and return all outcomes, passing or not."""
    indexed = table.set_index("municipality_code")
    official = turnout_report[turnout_report["municipality_code"] != "TOTAL"].set_index(
        "municipality_code"
    )
    total = turnout_report[turnout_report["municipality_code"] == "TOTAL"].iloc[0]
    checks = []

    missing = set(MUNICIPALITY_CODES) - set(indexed.index)
    extra = set(indexed.index) - set(MUNICIPALITY_CODES)
    checks.append(
        Check(
            "exactly the 33 municipalities",
            not missing and not extra,
            f"missing {sorted(missing)}, unexpected {sorted(extra)}",
        )
    )

    checks.append(
        _compare(
            "registered voters match the turnout report",
            indexed["registered_voters"].astype(int),
            official["registered_voters"],
        )
    )
    checks.append(
        _compare(
            "votes cast match the turnout report",
            indexed["votes_cast"].astype(int),
            official["voter_turnout"],
        )
    )
    turnout_gap = (indexed["turnout_pct"] - official["turnout_pct"]).abs().max()
    checks.append(
        Check(
            "turnout matches the official percentage",
            bool(turnout_gap < TURNOUT_TOLERANCE),
            f"largest gap {turnout_gap:.2e} points",
        )
    )
    registered_sum = int(indexed["registered_voters"].sum())
    checks.append(
        Check(
            "municipal registered voters sum to the provincial total",
            registered_sum == int(total["registered_voters"]),
            f"{registered_sum} against {int(total['registered_voters'])}",
        )
    )

    party_votes = pr_party_votes(detailed)
    provincial = results_summary.set_index("party")["pr"]
    is_party = ~provincial.index.str.startswith("Total ")
    checks.append(
        _compare(
            "provincial PR votes per party match the results summary",
            party_votes.groupby("party")["valid_votes"].sum().astype(int),
            provincial[is_party],
        )
    )
    checks.append(
        Check(
            "provincial PR spoilt votes match the results summary",
            int(indexed["pr_spoilt_votes"].sum()) == int(provincial["Total Spoilt Votes"]),
            f"{int(indexed['pr_spoilt_votes'].sum())} against "
            f"{int(provincial['Total Spoilt Votes'])}",
        )
    )

    party_differences, total_differences, missing_files = [], [], []
    for code in indexed.index:
        summary = municipal_summaries.get(code)
        if summary is None:
            missing_files.append(code)
            continue
        summary = summary.set_index("party")["pr"]
        is_party = ~summary.index.str.startswith("Total ")
        ours = party_votes[party_votes["municipality_code"] == code].set_index("party")
        ours = ours["valid_votes"].astype(int)
        parties = summary[is_party]
        joined = pd.concat([ours.rename("ours"), parties.rename("official")], axis=1).fillna(0)
        if (joined["ours"] != joined["official"]).any():
            party_differences.append(code)
        row = indexed.loc[code]
        if (
            int(row["pr_valid_votes"]) != int(summary["Total Valid Votes"])
            or int(row["pr_spoilt_votes"]) != int(summary["Total Spoilt Votes"])
            or int(row["pr_votes_cast"]) != int(summary["Total Votes Cast"])
        ):
            total_differences.append(code)
    checks.append(
        Check(
            "a results summary exists for every municipality",
            not missing_files,
            f"missing {missing_files}",
        )
    )
    checks.append(
        Check(
            "municipal PR votes per party match the municipal summaries",
            not party_differences,
            f"differences in {party_differences}",
        )
    )
    checks.append(
        Check(
            "municipal PR totals match the municipal summaries",
            not total_differences,
            f"differences in {total_differences}",
        )
    )

    share_gap = (indexed[list(SHARE_METRICS)].sum(axis=1) - 100).abs().max()
    checks.append(
        Check(
            "party shares sum to 100",
            bool(share_gap < SHARE_TOLERANCE),
            f"largest gap {share_gap:.2e} points",
        )
    )

    pr_rows = detailed[detailed["ballot"] == PR]
    duplicates = int(pr_rows.duplicated(["voting_district", "party"]).sum())
    checks.append(
        Check("no repeated PR rows", duplicates == 0, f"{duplicates} repeated district-party rows")
    )
    return checks


def require_all_passed(checks: list[Check]) -> None:
    failed = [check for check in checks if not check.passed]
    if failed:
        lines = [f"  {check.name}: {check.detail}" for check in failed]
        raise ValidationError("Validation failed:\n" + "\n".join(lines))


def checks_to_frame(checks: list[Check]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "check": [check.name for check in checks],
            "passed": [check.passed for check in checks],
            "detail": [check.detail for check in checks],
        }
    )
