import pandas as pd
import pytest

from ecaudit.constants import MUNICIPALITY_CODES
from ecaudit.harmonise.crosswalk import (
    ELECTION_YEARS,
    build_crosswalk,
    district_code,
    district_moves,
    load_crosswalk,
    snapshot_path,
)


def snapshots():
    return {year: pd.read_csv(snapshot_path(year)) for year in ELECTION_YEARS}


def test_crosswalk_covers_33_municipalities():
    crosswalk = load_crosswalk()
    assert sorted(crosswalk["municipality_code"]) == sorted(MUNICIPALITY_CODES)
    assert crosswalk["category"].value_counts().to_dict() == {"local": 31, "metro": 2}


def test_committed_crosswalk_matches_the_snapshots():
    rebuilt = build_crosswalk(snapshots())
    pd.testing.assert_frame_equal(rebuilt, load_crosswalk(), check_dtype=False)


def test_only_two_municipalities_were_renamed_for_2026():
    crosswalk = load_crosswalk().set_index("municipality_code")
    renamed = crosswalk[crosswalk["renamed_2021_2026"]]
    assert sorted(renamed.index) == ["EC137", "EC156"]
    assert renamed.loc["EC137", "name_2026"] == "Dr. A.B. Xuma"
    assert renamed.loc["EC156", "name_2026"] == "Kumkani Mhlontlo"


def test_iec_ids_are_unchanged_from_2021_to_2026():
    earlier = pd.read_csv(snapshot_path(2021)).set_index("code")["iec_id"]
    later = pd.read_csv(snapshot_path(2026)).set_index("code")["iec_id"]
    pd.testing.assert_series_equal(earlier.sort_index(), later.sort_index())


def test_a_new_code_stops_the_build():
    changed = snapshots()
    changed[2026] = changed[2026].replace({"code": {"EC444": "EC445"}})
    with pytest.raises(ValueError, match="EC445"):
        build_crosswalk(changed)


def test_district_code():
    assert district_code("EC121") == "DC12"
    assert district_code("EC443") == "DC44"
    assert district_code("BUF") == "BUF"


def test_district_moves_finds_only_moved_districts():
    def frame(rows):
        return pd.DataFrame(
            rows, columns=["voting_district", "municipality_code", "registered_voters", "ballot"]
        )

    earlier = frame([(1, "EC126", 465, "PR"), (2, "EC101", 100, "PR"), (3, "EC102", 50, "PR")])
    later = frame([(1, "BUF", 452, "PR"), (2, "EC101", 110, "PR"), (4, "EC102", 40, "PR")])
    moves = district_moves(earlier, later)
    assert moves["voting_district"].tolist() == [1]
    assert moves.loc[0, "municipality_code_later"] == "BUF"
