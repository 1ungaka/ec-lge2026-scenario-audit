import pandas as pd
import pytest
import requests

from ecaudit.ingest import download
from ecaudit.ingest.download import MissingSourceError, Source, parse_municipality_options
from ecaudit.ingest.parse import clean_text, read_detailed, split_label
from ecaudit.ingest.results import load_year


def test_split_label_keeps_hyphenated_names():
    code, name = split_label("EC443 - Winnie Madikizela-Mandela")
    assert (code, name) == ("EC443", "Winnie Madikizela-Mandela")


def test_clean_text_collapses_whitespace():
    assert clean_text("CONGRESS  OF THE\nPEOPLE ") == "CONGRESS OF THE PEOPLE"


def test_sources_cover_every_report_for_the_event():
    sources = download.sources_for(2026)
    assert len(sources) == 36
    assert sources[0].url == (
        "https://results.elections.org.za/home/LGEPublicReports/1887/"
        "Downloadable%20Party%20Results/EC.csv"
    )
    assert sources[-1].url.endswith("/1887/Detailed%20Results/EC/NMA.xls")


def test_read_detailed_rejects_a_changed_layout(tmp_path):
    path = tmp_path / "changed.csv"
    path.write_text("Province,Municipality\nEastern Cape,BUF - Buffalo City\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected columns"):
        read_detailed(path)


def test_read_detailed_handles_bom_and_labels(tmp_path):
    columns = (
        "Province,Municipality,Ward,VotingDistrict,VotingStationName,RegisteredVoters,"
        "BallotType,SpoiltVotes,PartyName,TotalValidVotes,DateGenerated"
    )
    line = "Eastern Cape,BUF - Buffalo City,Ward 1,10,HALL,500,PR,2,CONGRESS  OF PEOPLE,9,1/1/2021"
    path = tmp_path / "detailed.csv"
    path.write_text(f"{columns}\n{line}\n", encoding="utf-8-sig")
    row = read_detailed(path).iloc[0]
    assert row["municipality_code"] == "BUF"
    assert row["party"] == "CONGRESS OF PEOPLE"


def test_parse_municipality_options():
    page = (
        '<select name="x$ddlResultsSummaryMunicipalities" id="y">'
        '<option value="0">CHOOSE MUNICIPALITY</option>'
        '<option value="1117~1">BUF - Buffalo City</option>'
        '<option value="1101~3">DC10 - Sarah Baartman</option>'
        "</select>"
    )
    assert parse_municipality_options(page) == [
        {"iec_id": "1117", "code": "BUF", "name": "Buffalo City"},
        {"iec_id": "1101", "code": "DC10", "name": "Sarah Baartman"},
    ]


class FakeResponse:
    def __init__(self, status_code, content_type, content=b""):
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self.content = content
        self.ok = status_code < 400


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, url, timeout):
        self.calls += 1
        return self.responses.pop(0)


SOURCE = Source(2026, "detailed_results.csv", "https://example.test/EC.csv")


def test_fetch_retries_a_server_error(monkeypatch):
    monkeypatch.setattr(download.time, "sleep", lambda seconds: None)
    session = FakeSession(
        [FakeResponse(522, "text/html"), FakeResponse(200, "application/octet-stream", b"data")]
    )
    assert download.fetch(SOURCE, session) == b"data"
    assert session.calls == 2


def test_missing_file_names_url_and_destination(monkeypatch):
    monkeypatch.setattr(download.time, "sleep", lambda seconds: None)
    session = FakeSession([FakeResponse(404, "text/html")])
    with pytest.raises(MissingSourceError) as error:
        download.fetch(SOURCE, session)
    assert session.calls == 1
    assert SOURCE.url in str(error.value)
    assert "detailed_results.csv" in str(error.value)


def test_html_is_never_saved_as_data(monkeypatch):
    monkeypatch.setattr(download.time, "sleep", lambda seconds: None)
    session = FakeSession([FakeResponse(200, "text/html", b"<html>")] * download.RETRIES)
    with pytest.raises(MissingSourceError):
        download.fetch(SOURCE, session)


def test_network_failure_is_reported(monkeypatch):
    monkeypatch.setattr(download.time, "sleep", lambda seconds: None)

    class BrokenSession:
        def get(self, url, timeout):
            raise requests.ConnectionError("refused")

    with pytest.raises(MissingSourceError, match="refused"):
        download.fetch(SOURCE, BrokenSession())


def test_load_year_lists_every_missing_file(tmp_path):
    with pytest.raises(MissingSourceError) as error:
        load_year(2026, raw_root=tmp_path)
    message = str(error.value)
    assert "Missing 36 IEC files for 2026" in message
    assert "LGEPublicReports/1887/Voter%20Turnout/EC.xls" in message


def test_manifest_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(download, "MANIFEST_PATH", tmp_path / "MANIFEST.csv")
    row = dict.fromkeys(download.MANIFEST_FIELDS, "value") | {"file": "2021/a.csv"}
    download.save_manifest({"2021/a.csv": row})
    assert download.load_manifest() == {"2021/a.csv": row}
    assert list(pd.read_csv(tmp_path / "MANIFEST.csv").columns) == list(download.MANIFEST_FIELDS)
