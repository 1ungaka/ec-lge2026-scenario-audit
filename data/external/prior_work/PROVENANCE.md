# Provenance of the prior-work files

The five CSV files in this folder are the published 2026 scenario outputs of a University of
Fort Hare team, prepared for the DIRISA SDC 2026 Teams Qualification. They are stored here
byte for byte and are evaluated as prediction sets. Nothing in this repository was derived
from that team's code, notebooks, text, figures or documentation.

## Authors

Andile Ntombela, Asandiswa Maqam, Monwabisi Thebe, Sandiso Siqhaza, Asemahle Mdingi and
Cebisile Mtyu.

## Source

- Repository: https://github.com/MonwabisiThebe/TEAM_UFH-DIRISA-TEAM-QUALIFICATION
- Earlier name, which redirects to the above:
  https://github.com/MonwabisiThebe/UFH-DIRISA-TEAM-QUALIFICATION
- Commit: `6a8b1e8d036ffe365b0c31265cf3ff6232ead615` (committed 2026-10-28)
- Path in that repository: `data/processed/scenarios/phase6/`
- Copied on: 2026-11-01

The commit hash comes from the GitHub archive of the repository's main branch. On
2026-11-01 it was the head of main. `municipality_scenarios_2026.csv`,
`party_scenarios_2026.csv` and `turnout_scenarios_2026.csv` were also fetched directly from
raw.githubusercontent.com at that commit and hash identically to the copies here.

## Files

| File | Used for |
| --- | --- |
| `turnout_scenarios_2026.csv` | The three turnout assumption levels and their low-high ranges |
| `party_scenarios_2026.csv` | The two party-support scenarios |
| `municipality_scenarios_2026.csv` | The party-share band (`PartyBand_pts`) |
| `scenario_summary_2026.csv` | Stored for completeness, not scored |
| `swing_sensitivity_2026.csv` | Stored for completeness, not scored |

`SHA256SUMS` records the hash of each file. A test fails if any of them changes.

## Licence

The source repository has no licence file, so these files are not covered by this
repository's MIT licence. Their rights remain with the authors named above.
