"""Tests for scripts/httptv_client.py (AC45–AC48). Every HTTP call is mocked; no server needed."""

import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import httptv_client as client  # noqa: E402

TOKEN = "test-token-123"
BASE = "http://127.0.0.1:8000/api/"


class FakeResponse:
    def __init__(self, status_code=200, payload=None, invalid_json=False):
        self.status_code = status_code
        self._payload = payload
        self._invalid_json = invalid_json

    def json(self):
        if self._invalid_json:
            raise ValueError("not JSON")
        return self._payload


class FakeHTTP:
    """Records requests.request(...) calls and returns queued responses (or raises queued errors)."""

    def __init__(self):
        self.calls, self.queue = [], []

    def __call__(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        result = self.queue.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture
def http(monkeypatch):
    fake = FakeHTTP()
    monkeypatch.setattr(client.requests, "request", fake)
    monkeypatch.setenv("HTTPTV_API_TOKEN", TOKEN)
    monkeypatch.delenv("HTTPTV_API_URL", raising=False)
    return fake


def entry(entry_id=2, name="Severance", status="watching", season=2, episode=9, rating=4, notes=""):
    return {"id": entry_id, "show": {"tvmaze_id": 44933, "name": name}, "status": status,
            "current_season": season, "current_episode": episode, "rating": rating, "notes": notes}


def page(*entries, count=None, next_url=None, previous=None):
    return {"count": len(entries) if count is None else count, "next": next_url, "previous": previous,
            "results": list(entries)}


# --- Configuration ---------------------------------------------------------------------------------------

def test_missing_token_explains_how_to_get_one(monkeypatch, capsys):
    monkeypatch.delenv("HTTPTV_API_TOKEN", raising=False)
    assert client.main(["list"]) == 1
    err = capsys.readouterr().err
    assert "HTTPTV_API_TOKEN is not set" in err and "/api/auth/token/" in err


def test_api_url_can_be_configured(http, monkeypatch):
    monkeypatch.setenv("HTTPTV_API_URL", "http://localhost:9000/api")   # no trailing slash
    http.queue.append(FakeResponse(200, page()))
    client.main(["list"])
    assert http.calls[0]["url"] == "http://localhost:9000/api/collection/"


# --- AC45: list -----------------------------------------------------------------------------------------------

def test_list_sends_token_and_parameters_and_prints_table(http, capsys):
    http.queue.append(FakeResponse(200, page(entry(), entry(5, "The Office", "completed", None, None, None),
                                             count=14, next_url=BASE + "collection/?page=2")))
    code = client.main(["list", "--status", "watching", "--search", "sev", "--ordering", "-rating", "--page", "1"])
    assert code == 0
    call = http.calls[0]
    assert call["method"] == "GET" and call["url"] == BASE + "collection/"
    assert call["headers"]["Authorization"] == f"Token {TOKEN}"
    assert call["params"] == {"status": "watching", "search": "sev", "ordering": "-rating", "page": 1, "page_size": 12}
    assert call["timeout"] == 10
    out = capsys.readouterr().out
    assert "Severance" in out and "Season 2, Episode 9" in out and "4/5" in out
    assert "The Office" in out and "Not started" in out and "Not rated" in out
    assert "Page 1 of 2 (14 entries)" in out


def test_list_without_options_sends_only_paging(http):
    http.queue.append(FakeResponse(200, page()))
    client.main(["list"])
    assert http.calls[0]["params"] == {"page": 1, "page_size": 12}


def test_list_with_no_entries(http, capsys):
    http.queue.append(FakeResponse(200, page()))
    assert client.main(["list"]) == 0
    assert "No entries found." in capsys.readouterr().out


# --- AC46: update -------------------------------------------------------------------------------------------------

def test_update_sends_only_given_fields(http, capsys):
    http.queue.append(FakeResponse(200, entry(rating=5, notes="Rewatching")))
    code = client.main(["update", "2", "--rating", "5", "--notes", "Rewatching"])
    assert code == 0
    call = http.calls[0]
    assert call["method"] == "PATCH" and call["url"] == BASE + "collection/2/"
    assert call["json"] == {"rating": 5, "notes": "Rewatching"}
    assert "Updated entry 2: Severance" in capsys.readouterr().out


def test_update_all_fields(http):
    http.queue.append(FakeResponse(200, entry()))
    client.main(["update", "2", "--status", "on_hold", "--season", "3", "--episode", "1", "--rating", "2", "--notes", ""])
    assert http.calls[0]["json"] == {"status": "on_hold", "current_season": 3, "current_episode": 1, "rating": 2, "notes": ""}


def test_update_can_clear_progress_and_rating(http):
    http.queue.append(FakeResponse(200, entry(season=None, episode=None, rating=None)))
    client.main(["update", "2", "--season", "none", "--episode", "none", "--rating", "none"])
    assert http.calls[0]["json"] == {"current_season": None, "current_episode": None, "rating": None}


def test_update_without_options_is_an_error(http, capsys):
    assert client.main(["update", "2"]) == 1
    assert http.calls == []
    assert "Give at least one of" in capsys.readouterr().err


def test_update_prints_the_apis_field_errors(http, capsys):
    http.queue.append(FakeResponse(400, {"current_episode": ["Enter both a season and an episode, or leave both blank."]}))
    assert client.main(["update", "2", "--season", "3"]) == 1
    err = capsys.readouterr().err
    assert "current_episode: Enter both a season and an episode, or leave both blank." in err


# --- AC47: next (TDD) -----------------------------------------------------------------------------------------------

def test_next_adds_one_to_the_episode_only(http, capsys):
    http.queue += [FakeResponse(200, entry(season=2, episode=9)), FakeResponse(200, entry(season=2, episode=10))]
    assert client.main(["next", "2"]) == 0
    get, patch = http.calls
    assert get["method"] == "GET" and get["url"] == BASE + "collection/2/"
    assert patch["method"] == "PATCH" and patch["json"] == {"current_episode": 10}
    assert "Severance: Season 2, Episode 9 -> Season 2, Episode 10" in capsys.readouterr().out


def test_next_from_not_started_goes_to_season_1_episode_1(http, capsys):
    http.queue += [FakeResponse(200, entry(season=None, episode=None, status="plan_to_watch")),
                   FakeResponse(200, entry(season=1, episode=1, status="plan_to_watch"))]
    assert client.main(["next", "2"]) == 0
    assert http.calls[1]["json"] == {"current_season": 1, "current_episode": 1}
    assert "Not started -> Season 1, Episode 1" in capsys.readouterr().out


def test_next_never_changes_season_or_status(http):
    http.queue += [FakeResponse(200, entry(season=1, episode=10, status="completed")), FakeResponse(200, entry())]
    client.main(["next", "2"])
    sent = http.calls[1]["json"]
    assert "status" not in sent and "current_season" not in sent and sent == {"current_episode": 11}


def test_next_for_missing_entry_stops_before_patching(http, capsys):
    http.queue.append(FakeResponse(404, {"detail": "Not found."}))
    assert client.main(["next", "99"]) == 1
    assert len(http.calls) == 1
    assert "No entry with ID 99 in your collection." in capsys.readouterr().err


# --- AC48: errors -----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("failure, phrase", [
    (requests.ConnectionError(), "Could not connect to HTTP.tv"),
    (requests.Timeout(), "did not respond within 10 seconds"),
    (FakeResponse(401, {"detail": "Invalid token."}), "rejected your token"),
    (FakeResponse(403, {"detail": "Forbidden"}), "rejected your token"),
    (FakeResponse(500, None), "unexpected response (HTTP 500)"),
    (FakeResponse(200, None, invalid_json=True), "could not be read"),
    (FakeResponse(200, ["not", "a", "page"]), "could not be read"),
])
def test_list_errors_print_a_message_and_exit_1(http, capsys, failure, phrase):
    http.queue.append(failure)
    assert client.main(["list"]) == 1
    assert phrase in capsys.readouterr().err


def test_update_missing_entry(http, capsys):
    http.queue.append(FakeResponse(404, {"detail": "Not found."}))
    assert client.main(["update", "42", "--rating", "3"]) == 1
    assert "No entry with ID 42 in your collection." in capsys.readouterr().err


def test_invalid_command_line_exits_with_usage_error(http, capsys):
    with pytest.raises(SystemExit) as excinfo:
        client.main(["update", "not-a-number", "--rating", "3"])
    assert excinfo.value.code == 2  # argparse's usage-error code
