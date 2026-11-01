"""Download the IEC's result files for the Eastern Cape.

Every file comes from a stable path under the IEC's public reports folder. Files are
stored byte for byte in data/raw/iec/<year>/ and recorded in data/raw/MANIFEST.csv. If a
download fails the error names the exact file and URL, so it can be fetched by hand.
"""

import argparse
import csv
import hashlib
import re
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import requests

from ecaudit.constants import (
    EVENT_IDS,
    MANIFEST_PATH,
    MUNICIPALITY_CODES,
    PROVINCE_FILE,
    PROVINCE_ID,
    RAW_IEC_DIR,
)

REPORTS_BASE = "https://results.elections.org.za/home/LGEPublicReports"
PICKER_URL = "https://results.elections.org.za/home/Downloads/ME-Results"
USER_AGENT = "ec-lge2026-scenario-audit (+https://github.com/1ungaka/ec-lge2026-scenario-audit)"
MANIFEST_FIELDS = ("year", "file", "url", "sha256", "bytes", "downloaded_utc")
RETRIES = 4


class MissingSourceError(RuntimeError):
    """A source file is not available. The message says what to fetch and where to put it."""


@dataclass(frozen=True)
class Source:
    year: int
    relative_path: str
    url: str

    @property
    def destination(self) -> Path:
        return RAW_IEC_DIR / str(self.year) / self.relative_path


def report_url(year: int, *parts: str) -> str:
    path = "/".join(quote(part) for part in parts)
    return f"{REPORTS_BASE}/{EVENT_IDS[year]}/{path}"


def sources_for(year: int) -> list[Source]:
    province = PROVINCE_FILE
    sources = [
        Source(
            year,
            "detailed_results.csv",
            report_url(year, "Downloadable Party Results", f"{province}.csv"),
        ),
        Source(year, "voter_turnout.xls", report_url(year, "Voter Turnout", f"{province}.xls")),
        Source(
            year, "results_summary.xls", report_url(year, "Detailed Results", f"{province}.xls")
        ),
    ]
    sources += [
        Source(
            year,
            f"municipal_summaries/{code}.xls",
            report_url(year, "Detailed Results", province, f"{code}.xls"),
        )
        for code in MUNICIPALITY_CODES
    ]
    return sources


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return {}
    with MANIFEST_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["file"]: row for row in csv.DictReader(handle)}


def save_manifest(rows: dict[str, dict[str, str]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows[key] for key in sorted(rows))


def fetch(source: Source, session: requests.Session) -> bytes:
    """Return the file's bytes, retrying the 5xx responses the IEC site gives under load."""
    failure = "no response"
    for attempt in range(RETRIES):
        try:
            response = session.get(source.url, timeout=300)
        except requests.RequestException as error:
            failure = str(error)
        else:
            content_type = response.headers.get("content-type", "")
            if response.ok and "text/html" not in content_type:
                return response.content
            failure = f"HTTP {response.status_code} ({content_type})"
            if response.status_code == 404:
                break
        time.sleep(5 * (attempt + 1))
    raise MissingSourceError(
        f"Could not download {source.relative_path} for {source.year}: {failure}.\n"
        f"  Source: {source.url}\n"
        f"  Save it by hand to: {source.destination}"
    )


def download_year(year: int, force: bool = False) -> list[str]:
    """Fetch every file for a year and return a list of manifest mismatches."""
    manifest = load_manifest()
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    mismatches = []
    for source in sources_for(year):
        key = f"{year}/{source.relative_path}"
        path = source.destination
        if force or not path.exists():
            content = fetch(source, session)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        digest = sha256_of(path)
        known = manifest.get(key)
        if known and known["sha256"] != digest:
            mismatches.append(key)
            continue
        if not known:
            manifest[key] = {
                "year": str(year),
                "file": key,
                "url": source.url,
                "sha256": digest,
                "bytes": str(path.stat().st_size),
                "downloaded_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
    save_manifest(manifest)
    return mismatches


def _form_fields(page: str) -> dict[str, str]:
    """Collect the fields a browser would submit from an ASP.NET page."""
    fields = {}
    for tag in re.findall(r"<input\b[^>]*>", page):
        name = re.search(r'name="([^"]+)"', tag)
        kind = re.search(r'type="([^"]+)"', tag)
        kind = kind.group(1).lower() if kind else "text"
        if not name or kind in ("submit", "image", "button"):
            continue
        if kind in ("radio", "checkbox") and "checked" not in tag:
            continue
        value = re.search(r'value="([^"]*)"', tag)
        fields[name.group(1)] = value.group(1) if value else ""
    for select in re.findall(r"<select\b.*?</select>", page, flags=re.S):
        name = re.search(r'name="([^"]+)"', select)
        option = re.search(r'<option[^>]*selected[^>]*value="([^"]*)"', select)
        option = option or re.search(r'<option[^>]*value="([^"]*)"', select)
        if name and option:
            fields[name.group(1)] = option.group(1)
    return fields


def _postback(session: requests.Session, page: str, target: str, **changes: str) -> str:
    fields = _form_fields(page) | changes | {"__EVENTTARGET": target, "__EVENTARGUMENT": ""}
    response = session.post(PICKER_URL, data=fields, timeout=120, headers={"Referer": PICKER_URL})
    response.raise_for_status()
    return response.text


def parse_municipality_options(page: str) -> list[dict[str, str]]:
    """Read the municipality dropdown of the results summary report."""
    match = re.search(r"<select[^>]*ddlResultsSummaryMunicipalities.*?</select>", page, flags=re.S)
    if match is None:
        raise ValueError("The IEC page has no municipality dropdown")
    rows = []
    for value, label in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', match.group(0)):
        if " - " not in label:
            continue
        code, name = label.split(" - ", 1)
        rows.append({"iec_id": value.split("~")[0], "code": code.strip(), "name": name.strip()})
    return rows


def fetch_municipality_list(year: int) -> list[dict[str, str]]:
    """Ask the IEC which Eastern Cape municipalities exist for an election."""
    election_field = "ctl00$MainContent$ddlElections"
    province_field = "ctl00$MainContent$ddlResultsSummaryProvinces"
    event = str(EVENT_IDS[year])
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    response = session.get(PICKER_URL, timeout=60)
    response.raise_for_status()
    page = _postback(session, response.text, election_field, **{election_field: event})
    report_field = re.search(r'name="([^"]*radReports)"', page).group(1)
    report_ids = re.findall(r'<input[^>]*name="[^"]*radReports"[^>]*value="(\d+)"', page)
    position = report_ids.index("22")  # 22 is the IEC's id for the results summary report
    page = _postback(
        session,
        page,
        f"{report_field}${position}",
        **{election_field: event, report_field: "22"},
    )
    page = _postback(session, page, province_field, **{province_field: PROVINCE_ID})
    return parse_municipality_options(page)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=[2016, 2021])
    parser.add_argument("--force", action="store_true", help="download even if the file exists")
    args = parser.parse_args(argv)
    for year in args.years:
        try:
            mismatches = download_year(year, force=args.force)
        except MissingSourceError as error:
            print(error, file=sys.stderr)
            return 1
        if mismatches:
            print(f"{year}: these files differ from the manifest:", *mismatches, file=sys.stderr)
            return 1
        print(f"{year}: all files present and matching the manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
