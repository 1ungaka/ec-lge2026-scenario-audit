"""Command line entry points: `baseline`, `freeze` and `results`."""

import argparse

import pandas as pd

from ecaudit.constants import PROCESSED_DIR, RAW_IEC_DIR
from ecaudit.harmonise.crosswalk import district_moves
from ecaudit.harmonise.tidy import write_table
from ecaudit.harmonise.validate import checks_to_frame, require_all_passed
from ecaudit.ingest.parse import read_detailed
from ecaudit.ingest.results import ingest_year
from ecaudit.predict import freeze, prior_work


def table_path(year: int):
    return PROCESSED_DIR / f"municipal_results_{year}.csv"


def build_year(year: int) -> pd.DataFrame:
    """Build and validate one election, writing its table and validation record."""
    table, checks = ingest_year(year)
    write_table(table, table_path(year))
    checks_to_frame(checks).to_csv(
        PROCESSED_DIR / f"validation_{year}.csv", index=False, lineterminator="\n"
    )
    require_all_passed(checks)
    print(f"{year}: {len(checks)} validation checks passed")
    return table


def run_baseline() -> None:
    for year in (2016, 2021):
        build_year(year)
    earlier = read_detailed(RAW_IEC_DIR / "2016" / "detailed_results.csv")
    later = read_detailed(RAW_IEC_DIR / "2021" / "detailed_results.csv")
    moves = district_moves(earlier, later)
    moves.to_csv(PROCESSED_DIR / "district_moves_2016_2021.csv", index=False, lineterminator="\n")
    print(f"{len(moves)} voting districts changed municipality between 2016 and 2021")


def run_freeze() -> None:
    prior_work.verify_checksums()
    predictions = freeze.build_predictions(
        pd.read_csv(table_path(2016)), pd.read_csv(table_path(2021))
    )
    freeze.check_predictions(predictions)
    freeze.write_frozen(predictions)
    sets = predictions["prediction_set"].nunique()
    print(f"Frozen {len(predictions)} predictions across {sets} prediction sets")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["baseline", "freeze", "results"])
    parser.add_argument("--year", type=int, default=2026, help="election year for `results`")
    args = parser.parse_args()
    if args.command == "baseline":
        run_baseline()
    elif args.command == "freeze":
        run_freeze()
    else:
        build_year(args.year)


if __name__ == "__main__":
    main()
