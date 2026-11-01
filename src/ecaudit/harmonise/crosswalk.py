"""The municipal crosswalk across the 2016, 2021 and 2026 elections.

Municipal codes are the join key. Names are never used, because the IEC's 2016 files still
carry pre-merger labels such as 'EC101 - Camdeboo' and names change between elections.
"""

import argparse

import pandas as pd

from ecaudit.constants import BOUNDARIES_DIR, METROS, MUNICIPALITY_CODES
from ecaudit.ingest.download import fetch_municipality_list

ELECTION_YEARS = (2016, 2021, 2026)
CROSSWALK_PATH = BOUNDARIES_DIR / "municipality_crosswalk.csv"


def snapshot_path(year: int):
    return BOUNDARIES_DIR / f"iec_municipalities_{year}.csv"


def save_snapshots() -> None:
    """Record the IEC's own municipality list for each election."""
    BOUNDARIES_DIR.mkdir(parents=True, exist_ok=True)
    for year in ELECTION_YEARS:
        frame = pd.DataFrame(fetch_municipality_list(year))
        frame.to_csv(snapshot_path(year), index=False, lineterminator="\n")


def district_code(code: str) -> str:
    """Return the district of a local municipality, whose code embeds it: EC121 is in DC12."""
    if code in METROS:
        return code
    return f"DC{code[2:4]}"


def build_crosswalk(snapshots: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Join the IEC's lists on municipal code, and fail if the set of codes ever differs."""
    expected = set(MUNICIPALITY_CODES)
    names = {}
    for year, frame in snapshots.items():
        local = frame[~frame["code"].str.startswith("DC")]
        found = set(local["code"])
        if found != expected:
            raise ValueError(
                f"{year}: codes differ from the 33 expected: "
                f"missing {sorted(expected - found)}, new {sorted(found - expected)}"
            )
        names[year] = local.set_index("code")["name"]
    latest = snapshots[max(snapshots)]
    districts = latest[latest["code"].str.startswith("DC")].set_index("code")["name"]
    crosswalk = pd.DataFrame({"municipality_code": sorted(expected)})
    crosswalk["category"] = [
        "metro" if code in METROS else "local" for code in crosswalk["municipality_code"]
    ]
    crosswalk["district_code"] = crosswalk["municipality_code"].map(district_code)
    crosswalk["district_name"] = [
        districts.get(code, "Metropolitan municipality") for code in crosswalk["district_code"]
    ]
    for year, series in names.items():
        crosswalk[f"name_{year}"] = crosswalk["municipality_code"].map(series)
    crosswalk["renamed_2021_2026"] = crosswalk["name_2021"] != crosswalk["name_2026"]
    return crosswalk


def load_crosswalk() -> pd.DataFrame:
    return pd.read_csv(CROSSWALK_PATH)


def district_moves(earlier: pd.DataFrame, later: pd.DataFrame) -> pd.DataFrame:
    """Find voting districts that appear in a different municipality in a later election.

    This is an empirical boundary test: a district that changes municipality shows that an
    outer boundary moved, whatever the published notices say.
    """
    columns = ["voting_district", "municipality_code", "registered_voters"]

    def districts(frame: pd.DataFrame) -> pd.DataFrame:
        pr_rows = frame[frame["ballot"] == "PR"]
        return pr_rows.drop_duplicates("voting_district")[columns]

    merged = districts(earlier).merge(
        districts(later), on="voting_district", suffixes=("_earlier", "_later")
    )
    moved = merged["municipality_code_earlier"] != merged["municipality_code_later"]
    return merged[moved].sort_values("voting_district", ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", action="store_true", help="refresh the IEC lists first")
    args = parser.parse_args()
    if args.snapshot:
        save_snapshots()
    snapshots = {year: pd.read_csv(snapshot_path(year)) for year in ELECTION_YEARS}
    build_crosswalk(snapshots).to_csv(CROSSWALK_PATH, index=False, lineterminator="\n")


if __name__ == "__main__":
    main()
