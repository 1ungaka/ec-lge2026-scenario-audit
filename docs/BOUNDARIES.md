# Municipal boundaries, 2016 to 2026

**Finding: the Eastern Cape has the same 33 municipalities in 2026 as in 2021, with no change
to outer boundaries. Two municipalities were renamed. The crosswalk from 2021 to 2026 is
therefore one to one, keyed on municipal code.**

## Evidence for 2021 to 2026

1. **Municipal Demarcation Board decision.** The MDB's notice
   [Final chance to shape your wards ahead of the 2026 Local Government Elections](https://www.demarcation.org.za/final-chance-to-shape-your-wards-ahead-of-the-2026-local-government-elections/)
   (29 September 2025) reports on the 13 deferred outer-boundary cases, affecting 19
   municipalities, from the 2023/2024 process. The Board "resolved not to re-determine any
   municipal boundaries at this time", in line with its Circular 3 of 2025. The notice cites
   that circular, which was not itself obtained for this check.
2. **The IEC's own list.** The municipal results page for the 2026 election lists the same 33
   municipal codes and six district municipalities as 2021. The IEC's internal id is unchanged
   for all 39 entities. The lists were captured on 2026-11-01 and are stored in
   `data/external/boundaries/iec_municipalities_<year>.csv`.
3. **Pending direct test.** When the 2026 results are published, `district_moves` will compare
   the municipality of every voting district with 2021. This is the check that can actually
   detect a moved boundary, and its result will be reported in the evaluation.

Ward boundaries did change. The MDB's 2026 ward delimitation raised the Eastern Cape from 696
to 703 wards according to secondary reporting. This does not affect the analysis, because PR
ballots are counted across the whole municipality.

## Renamed municipalities

| Code | 2021 name | 2026 name |
| --- | --- | --- |
| EC137 | Engcobo | Dr. A.B. Xuma |
| EC156 | Mhlontlo | Kumkani Mhlontlo |

## Evidence for 2016 to 2021

All 33 codes exist in both elections, but the geography is not perfectly identical. Of the
4,680 voting districts present in both elections, two changed municipality
(`data/processed/district_moves_2016_2021.csv`):

| Voting district | 2016 | 2021 | Registered in 2016 | Registered in 2021 |
| --- | --- | --- | --- | --- |
| 10871298 | EC126 Ngqushwa | BUF Buffalo City | 465 | 452 |
| 11460080 | EC135 Intsika Yethu | EC138 Sakhisizwe | 343 | 360 |

These are small: see the percentages in `docs/PREREGISTRATION.md`. The 2016 figures are used
as published and are not adjusted. Only the trend and uniform swing baselines depend on them.

## Joining on codes, never names

The IEC's 2016 files still carry pre-merger labels, such as `EC101 - Camdeboo` for what is now
Dr Beyers Naude and `EC139 - Tsolwana/Inkwanca/Lukanji` for Enoch Mgijima. The 2016 data is
nonetheless on the merged geography. All joins therefore use municipal codes, and
`data/external/boundaries/municipality_crosswalk.csv` holds the names for display.
