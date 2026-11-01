# Raw data

Raw IEC files live in `data/raw/iec/<year>/` and are not committed. The IEC's copyright notice
allows its material to be reproduced unaltered for personal, non-commercial use or use within
an organisation, which does not clearly cover a public repository. Run this to fetch them:

```bash
make data
```

`MANIFEST.csv` is committed. It records the source URL, SHA-256 hash, size and download time
of every file, and the downloader stops if a file no longer matches it.

## Files for each election

All paths are under `https://results.elections.org.za/home/LGEPublicReports/<event>/`.
The events are 402 (2016), 1091 (2021) and 1887 (2026).

| Local file | IEC path |
| --- | --- |
| `detailed_results.csv` | `Downloadable Party Results/EC.csv` |
| `voter_turnout.xls` | `Voter Turnout/EC.xls` |
| `results_summary.xls` | `Detailed Results/EC.xls` |
| `municipal_summaries/<code>.xls` | `Detailed Results/EC/<code>.xls` |

## If the download fails

The IEC site can return server errors under load. The downloader retries, then prints the
exact file, URL and destination. To fetch a file by hand, use the
[municipal results page](https://results.elections.org.za/home/Downloads/ME-Results) and save
it to that destination. Then rerun `make data`, which checks it against the manifest.
