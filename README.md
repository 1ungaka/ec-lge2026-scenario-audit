# Eastern Cape 2026 Local Elections: A Scenario Audit

> How well did pre-election scenarios and simple baselines anticipate turnout and party support
> in the Eastern Cape's 33 municipalities in the 4 November 2026 Local Government Elections, and
> where and why did they miss?

**Status: pre-registered, awaiting results.** Predictions were frozen before the election. The
evaluation, dashboard and report follow once the IEC declares the 2026 results.

## Headline findings

None yet. No 2026 result existed when this was written, and findings will appear here after the
evaluation.

## Pre-registration

Every prediction set, metric, comparison and hypothesis was fixed before results existed:

- Plan: [docs/PREREGISTRATION.md](docs/PREREGISTRATION.md)
- Frozen predictions: [data/processed/predictions_frozen/](data/processed/predictions_frozen/)
- Tag: [`v0.1-preregistration`](https://github.com/1ungaka/ec-lge2026-scenario-audit/releases/tag/v0.1-preregistration)

Git commit dates are set by the author's machine, so the time the tag reached GitHub is the
better evidence of when it was made.

## What is being compared

| Prediction set | Source | Covers |
| --- | --- | --- |
| Repeat of 2021, partial recovery, return to 2016 | Prior work (below) | Turnout |
| Validated status quo, trend continues | Prior work (below) | Party support |
| No change from 2021 | This repo | Turnout and party support |
| 2016-2021 trend continued | This repo | Turnout and party support |
| Uniform provincial swing | This repo | Turnout and party support |
| Relative turnout persistence | This repo | Turnout |

Party support means PR ballot shares for ANC, DA, EFF, UDM, ATM and OTHER.

## Reproduce

Requires Python 3.11 or later and `make`.

```bash
python -m venv .venv
```

Activate the environment, then:

```bash
make setup
```

```bash
make reproduce
```

This downloads the IEC files, checks them against the hash manifest, rebuilds and validates the
municipal tables, rebuilds the frozen predictions and runs the tests. A rebuilt
`predictions.csv` should be identical to the committed file.

When the IEC publishes the 2026 results, the same code handles them:

```bash
python -m ecaudit.ingest.download --years 2026
```

```bash
python -m ecaudit.pipeline results --year 2026
```

## Validation

The municipal tables for 2016 and 2021 pass all 12 checks against the IEC's separately published
reports. Registered voters, votes cast and turnout match the official turnout report in all 33
municipalities. PR votes for every party match each of the 33 official municipal summaries.
The results are in `data/processed/validation_<year>.csv`.

## Boundaries

The 33 municipalities and their outer boundaries are unchanged from 2021 to 2026. Two were
renamed: EC137 is now Dr. A.B. Xuma and EC156 is now Kumkani Mhlontlo. Between 2016 and 2021, two
voting districts moved between municipalities. See [docs/BOUNDARIES.md](docs/BOUNDARIES.md).

## Data sources

- Electoral Commission of South Africa (IEC).
  [Municipal election results](https://results.elections.org.za/home/Downloads/ME-Results),
  Local Government Elections 2016 and 2021 (Eastern Cape detailed results, Results Summary and
  Voter Turnout reports). Downloaded 2026-11-01. Raw files are not redistributed here; see
  [data/raw/README.md](data/raw/README.md) for the reason and for hashes.
- Municipal Demarcation Board.
  [Final chance to shape your wards ahead of the 2026 Local Government Elections](https://www.demarcation.org.za/final-chance-to-shape-your-wards-ahead-of-the-2026-local-government-elections/),
  29 September 2025.
- Published scenario outputs from the prior work credited below.

## Limitations

- There is one election and 33 municipalities. Bootstrap intervals describe variation across
  municipalities, and cannot say how a method would do in another election.
- OTHER combines every smaller party. It hides new entrants such as MK, which no prediction set
  here models by name.
- The baselines use only two past elections, so the trend baseline has no backtest.
- Misses will be compared with municipal features as associations, not causes.
- The 2016 municipal figures are used as published, although two voting districts later moved.

## Prior work and attribution

The team scenarios evaluated here were created by **Andile Ntombela, Asandiswa Maqam, Monwabisi
Thebe, Sandiso Siqhaza, Asemahle Mdingi and Cebisile Mtyu** of the University of Fort Hare for
the DIRISA SDC 2026 Teams Qualification:
[MonwabisiThebe/TEAM_UFH-DIRISA-TEAM-QUALIFICATION](https://github.com/MonwabisiThebe/TEAM_UFH-DIRISA-TEAM-QUALIFICATION).

This repository is an independent evaluation of their published outputs. It was not produced by
or with that team. Their five published scenario CSV files are stored unmodified in
[data/external/prior_work/](data/external/prior_work/), with
[provenance](data/external/prior_work/PROVENANCE.md) giving the source, commit and hashes. No code,
notebooks, text, figures or documentation from their repository were used, and everything else
here was written fresh.

## Licence

Code and documentation are under the [MIT licence](LICENSE). The prior-work files and IEC source
data are not covered by it.

## Author

Lunga Ngaka, final-year BSc Computer Science and Applied Mathematics, University of Fort Hare.
GitHub: [1ungaka](https://github.com/1ungaka).
