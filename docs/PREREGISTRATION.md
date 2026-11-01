# Pre-registration

**Written on 2026-11-01, before polls open on 4 November 2026 and before any 2026 result
exists.** The git tag `v0.1-preregistration` fixes this file and the frozen predictions. Any
later departure from this plan will be listed and explained in `docs/REPORT.md`.

## Question

How well did pre-election scenarios and simple baselines anticipate turnout and party support
in the Eastern Cape's 33 municipalities in the 4 November 2026 Local Government Elections, and
where and why did they miss?

## Prediction sets

The sets are frozen in `data/processed/predictions_frozen/predictions.csv` with columns
`municipality, metric, prediction_set, value, low, high`, and the file hashes are in
`SHA256SUMS` beside it. Metrics are `turnout_pct` and the PR shares `share_ANC`, `share_DA`,
`share_EFF`, `share_UDM`, `share_ATM` and `share_OTHER`.

| Prediction set | Covers | Rule |
| --- | --- | --- |
| `team_turnout_repeat2021` | Turnout | Published team scenario: repeat of 2021 conditions |
| `team_turnout_partial_recovery` | Turnout | Published team scenario: half the 2021 drop regained |
| `team_turnout_return2016` | Turnout | Published team scenario: return to 2016 participation |
| `team_party_validated` | Party | Published team scenario: validated status quo |
| `team_party_trend` | Party | Published team scenario: trend continues (labelled not validated by the team) |
| `baseline_no_change` | Both | 2021 result repeated |
| `baseline_trend` | Both | 2021 + (2021 - 2016) for each municipality |
| `baseline_uniform_swing` | Both | 2021 + the 2016-2021 provincial swing |
| `baseline_relative_persistence` | Turnout | 2021 provincial mean + the mean of the 2016 and 2021 relative patterns |

Rules applied to the baselines:

- Predicted party shares are floored at zero and rescaled to sum to 100. Turnout is limited to
  0-100.
- The turnout swing is the change in the unweighted mean across municipalities. Party swings
  are changes in the provincial PR vote share.
- ATM did not contest in 2016, so its trend and swing are mechanical extrapolations from zero.

### Ranges

- **Team turnout:** the published `Low_%` and `High_%`, which is plus or minus 3.788 points.
- **Team party:** the published `PartyBand_pts` of plus or minus 2.686 points, limited to 0-100.
  The team publishes this band but no low and high columns.
- **Baselines:** the 90th percentile of the absolute 2016-2021 change across the 33
  municipalities, per metric, limited to 0-100. This is my choice. It comes from the only
  backtest available, and the same band is used for all four baselines even though the trend
  baseline could not be backtested. The bands are 11.27 for turnout, 9.37 for ANC, 6.27 for
  DA, 6.26 for EFF, 2.40 for UDM, 4.35 for ATM and 10.43 for OTHER.

### Known overlaps between sets

These follow from the rules, so they are stated before the results.

- Relative persistence using only the 2021 pattern would equal no-change exactly. The baseline
  therefore averages the 2016 and 2021 patterns.
- The team's three turnout sets differ by a constant, so they have identical relative-pattern
  errors and can only differ in level.
- All three team sets use the 2021 relative pattern. Their correlation with
  `baseline_no_change` is 0.995, and the small gap comes from the definition of turnout below.
- `baseline_no_change` and `baseline_uniform_swing` have identical relative patterns for
  turnout. `baseline_trend` and `baseline_uniform_swing` have the same mean turnout, 39.99.
- `team_party_validated` is close to `baseline_no_change`. The team's stored method for the
  five named parties is no change, with OTHER set by a model and the shares then rescaled. The
  mean absolute gap between the two sets is 2.15 points for ANC and 3.18 for OTHER.

## Targets

- **Source:** the IEC's declared 2026 results, processed by the same code and validation as
  2016 and 2021. The evaluation runs only on results the IEC has declared, not on partial
  counts. If the IEC later republishes a file, the manifest hash change and any effect on
  results will be reported.
- **Turnout (primary):** the IEC's official percentage: the sum across voting districts of the
  higher of ward and PR votes cast, divided by registered voters plus MEC7 votes. This
  reproduces the official figure exactly for all 33 municipalities in 2016 and 2021.
- **Party shares:** PR valid votes for the party divided by all PR valid votes. Every party
  outside ANC, DA, EFF, UDM and ATM counts in OTHER. This includes uMkhonto weSizwe (MK), which
  did not exist in 2021.
- **Municipalities:** all 33, equally weighted. Provincial mean means the unweighted mean of
  the 33.

## Primary metrics

Let `e` be prediction minus actual for a municipality.

**Turnout**

- MAE and RMSE across the 33 municipalities.
- Level error `L`, the mean of `e`.
- Relative error `R`, the root mean square of `e - L`. Note that `RMSE^2 = L^2 + R^2`, so `R`
  can never exceed RMSE. Comparing those two would prove nothing. Claims about the pattern
  therefore compare `R` with `|L|`, or use the correlation.
- Pearson correlation between predicted and actual relative patterns, with Spearman reported
  alongside.

**Party support**

- MAE for each of the six groups, and overall MAE across all 198 municipality-group pairs.
- Largest-party hit rate. A set's predicted leader is the highest of the five named parties,
  never OTHER. The actual leader is the largest individual party, so if a party outside the
  five wins a municipality, every set misses it.
- Close-race calls. A race is close if the top two parties are within 5 points. For each set I
  report which municipalities it called close, with precision and recall against actual close
  races. The same rule applies to every set, and 10 points is a sensitivity check.

**Ranges**

- Coverage: the share of predictions with the actual inside `low` to `high`, per set and metric.
- Closest assumed level: which team turnout level has the smallest `|L|`.

**Uncertainty**

Paired bootstrap over municipalities: 10,000 resamples of the 33 with replacement, seed
20261104, percentile 95% intervals for the difference in MAE and in RMSE between two sets.
Intervals are not adjusted for multiple comparisons. With only 33 municipalities and one
election, they describe variation across municipalities, not across elections.

## Planned comparisons

Each is set A minus set B, for both MAE and RMSE.

| ID | Metric | A | B |
| --- | --- | --- | --- |
| C1 | Turnout | Each team turnout set | `baseline_no_change` |
| C2 | Turnout | Each team turnout set | `baseline_relative_persistence` |
| C3 | Turnout | `baseline_relative_persistence` | `baseline_no_change` |
| C4 | Turnout | `baseline_trend` | `baseline_no_change` |
| C5 | Turnout | `baseline_uniform_swing` | `baseline_no_change` |
| C6 | Party | `team_party_validated` | `baseline_no_change` |
| C7 | Party | `team_party_trend` | `baseline_trend` |
| C8 | Party | `team_party_validated` | `team_party_trend` |
| C9 | Party | `baseline_trend` | `baseline_no_change` |
| C10 | Party | `baseline_uniform_swing` | `baseline_no_change` |

## Hypotheses

Each states in advance what would count as support. Thresholds draw on the 2016-2021 backtest
in the last section. A hypothesis not supported will be reported as such.

| ID | Hypothesis | Supported if |
| --- | --- | --- |
| H1 | The relative turnout pattern is predicted better than the absolute level | For `baseline_no_change`, `R < abs(L)` and Pearson r is at least 0.70 |
| H2 | Of the team's three levels, repeat of 2021 is closest | `team_turnout_repeat2021` has the smallest `abs(L)` of the three |
| H3 | Nelson Mandela Bay is the closest contest | NMA has the smallest actual winning margin of the 33 |
| H4 | Persistence beats extrapolation for party support | `baseline_no_change` has lower overall MAE than `baseline_trend` and `baseline_uniform_swing`, with both 95% intervals (C9, C10) above zero |
| H5 | The validated team scenario does not differ clearly from no change | The 95% interval for C6 overall MAE includes zero |
| H6 | OTHER is the hardest group to predict | OTHER has the largest MAE of the six groups for `baseline_no_change` and `team_party_validated` |
| H7 | The largest party is highly stable | `baseline_no_change` hit rate is at least 30 of 33 |
| H8 | Relative turnout regresses to the mean | Spearman correlation between the 2021 relative pattern and its 2021-2026 change is negative, with a 95% bootstrap interval below zero, and `baseline_relative_persistence` has a lower `R` than `baseline_no_change` |

## Sensitivity checks

| ID | Check |
| --- | --- |
| S1 | Turnout target redefined as PR votes cast divided by registered voters. The team's turnout files follow this definition, which averaged 0.23 points below the official figure in 2021. |
| S2 | All party and turnout results repeated without the four municipalities in the ANC candidate dispute: Sundays River Valley (EC106), Walter Sisulu (EC145), Ngquza Hill (EC153) and Port St Johns (EC154). The Electoral Court upheld the exclusion of ANC candidates there, and the Constitutional Court overturned that on 15 October 2026. |
| S3 | Turnout and party MAE weighted by 2021 registered voters. |
| S4 | Close-race threshold of 10 points. |

## Exceptions decided in advance

- A municipality whose election is postponed, or whose results are not declared when the
  evaluation runs, is excluded and named. If it is declared later, the evaluation will be rerun
  and both versions reported.
- If a named party is not on a municipality's PR ballot, its actual share is 0 and the row is
  kept in the primary analysis. The municipality is flagged in the report.
- If the 2026 voting district test finds that outer boundaries moved, the affected
  municipalities will be flagged. The frozen predictions will not change.

## Exploratory analysis

These parts are planned but confirmatory claims will not rest on them.

- **OTHER:** the actual share of every party in OTHER with at least 1% in a municipality, to
  show how much of each miss comes from MK and other newer parties.
- **Maps:** the size and direction of each set's largest misses.
- **Misses:** for turnout, the absolute value of `e - L`; for party support, each municipality's
  MAE. Each is compared with 2021 winning margin, 2021 turnout and metro status using Spearman
  correlations and a linear regression. There are only two metros, so that comparison has
  little power. All results will be presented as associations, not causes.

## Not scored

The team's expected vote counts are not scored. They are built on the 2021 voters' roll, which
the team's own file labels as a placeholder until the 2026 roll is added.

## Backtest context

Using 2016 to predict 2021 gives the only available test of the no-change rule. These figures
informed the thresholds above and are not evidence about 2026.

| Measure | 2016 predicting 2021 |
| --- | --- |
| Mean turnout, 2016 then 2021 | 56.51, then 48.25 |
| Turnout MAE and RMSE | 8.26 and 8.69 |
| Level error `L` | +8.26 |
| Relative error `R` | 2.71 |
| Pearson r, relative pattern | 0.78 (Spearman 0.67) |
| Correlation of 2016 relative pattern with its 2016-2021 change | -0.48 (Spearman -0.41) |
| Overall party MAE | 2.93 |
| MAE by group: ANC, DA, EFF, UDM, ATM, OTHER | 4.50, 2.81, 3.16, 1.00, 2.00, 4.10 |
| Largest-party hit rate | 33 of 33 |

In 2021 the smallest winning margins were NMA at 0.44 points and Dr Beyers Naude at 6.86. The
2016 geography differs slightly, as two voting districts moved. They held at most 1.2% of the
registered voters of any municipality involved, so the 2016 inputs are used as published (see
`docs/BOUNDARIES.md`).

## Sources for facts used here

- Candidate dispute:
  [Mail & Guardian, 15 October 2026](https://mg.co.za/news/south-africa/2026-10-15-constitutional-court-rules-in-favour-of-anc-in-iec-candidate-nomination-dispute/)
  and
  [Cape Times, 15 October 2026](https://capetimes.co.za/2026-10-15-breaking--concourt-overturns-exclusion-of-181-anc-councillor-candidates/).
- Boundaries: `docs/BOUNDARIES.md`.
- Results: `data/raw/README.md`.
