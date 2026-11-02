# Report

Findings will appear here after the 4 November 2026 election.

## Departures from the pre-registration

### 1. Tag `v0.1-preregistration` re-created on 2 November 2026

This happened before polls opened and before any 2026 result existed.

**What changed:** the commit history was rewritten to remove a co-author line from all three commit
messages, and the tag was re-created on the rewritten commit. Authors, dates, subjects and files
were kept. The new tag is dated 2 November 2026, not backdated.

**Why:** the author wanted the history to carry only their own name.

**Effect on the plan:** none. `docs/PREREGISTRATION.md` and the frozen predictions are unchanged, and
each commit keeps the same git tree hash:

| Phase | Original commit | New commit | Tree |
| --- | --- | --- | --- |
| 0 | `2653a6ca507d29ad7d9daf5966ded878a9e5a2a5` | `f83cd20e8ca0ff515a6f3c5a4c0843ae69b0faf2` | `6ccd938664ae72dbea54c3fcd78c351e0c064868` |
| 1 | `a51dbeaf9d1383d36bcd22df3a36738039bf5b53` | `082d2c66236bc31f16c6f0a3c02eae9bef7ac579` | `76f2089023f3073ce3db3663762792b12df72cc5` |
| 2 (tagged) | `799fa6b7170a486b61685c62aec1dfc7f12ee99e` | `ef96504d1d09128c0e9d82464aad3b316e9bf14a` | `bab747a31e280a7d673247cc625d3661a29531f2` |

**Timing evidence:** the original tag was object `7976a9eed146c5b542500cd9aa16a266ee2417a3`, dated
1 November 2026. GitHub showed the repository's last push before this change at
2026-11-01T21:33:21Z. The time the new tag reached GitHub is 2 November 2026, so that is now the
public timestamp for the pre-registration.
