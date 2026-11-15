"""Automated tests for scripts/verify_tvmaze.py.

Every test replaces `requests.get` with a fake, so no real request is sent to
TVmaze. Real requests are checked manually instead.

Run from the repository root:
    uv run pytest
"""

import sys
from pathlib import Path

import pytest
import requests

# The script lives in scripts/, which is not an installed package, so add that
# folder to Python's import path to be able to `import verify_tvmaze`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import verify_tvmaze  # noqa: E402  (import must come after the path change)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeResponse:
    """Stands in for a requests.Response: just a status code and a JSON body."""

    def __init__(self, status_code=200, json_data=None, json_error=None):
        self.status_code = status_code
        self._json_data = json_data
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._json_data


def make_show(**overrides):
    """Return a realistic TVmaze show dict (based on The Office, ID 526)."""
    show = {
        "id": 526,
        "name": "The Office",
        "premiered": "2005-03-24",
        "ended": "2013-05-16",
        "status": "Ended",
        "genres": ["Comedy"],
        "rating": {"average": 8.5},
        "url": "https://www.tvmaze.com/shows/526/the-office",
    }
    show.update(overrides)
    return show


def fake_get_returning(response, calls=None):
    """Build a fake requests.get that returns `response` and records its arguments."""

    def fake_get(url, **kwargs):
        if calls is not None:
            calls.append((url, kwargs))
        return response

    return fake_get


def fake_get_raising(error):
    """Build a fake requests.get that raises `error`, like a failed request."""

    def fake_get(url, **kwargs):
        raise error

    return fake_get


# ---------------------------------------------------------------------------
# get_search_term
# ---------------------------------------------------------------------------


def test_search_term_from_arguments_is_joined_and_trimmed():
    assert verify_tvmaze.get_search_term(["  the", "office  "]) == "the office"


def test_blank_argument_returns_none():
    assert verify_tvmaze.get_search_term(["   "]) is None


def test_search_term_from_prompt_is_trimmed(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "  breaking bad  ")
    assert verify_tvmaze.get_search_term([]) == "breaking bad"


def test_blank_prompt_returns_none(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "   ")
    assert verify_tvmaze.get_search_term([]) is None


def test_closed_input_stream_counts_as_blank(monkeypatch):
    def raise_eof(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert verify_tvmaze.get_search_term([]) is None


# ---------------------------------------------------------------------------
# search_shows: successful requests
# ---------------------------------------------------------------------------


def test_request_uses_search_url_term_user_agent_and_timeout(monkeypatch):
    calls = []
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=[]), calls)
    )

    verify_tvmaze.search_shows("café")

    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://api.tvmaze.com/search/shows"
    assert kwargs["params"] == {"q": "café"}
    assert kwargs["headers"] == {"User-Agent": "HTTP.tv-verify/0.1"}
    assert kwargs["timeout"] == 10


def test_shows_are_returned_in_tvmaze_relevance_order(monkeypatch):
    data = [
        {"score": 0.9, "show": make_show(id=1, name="First")},
        {"score": 0.5, "show": make_show(id=2, name="Second")},
    ]
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=data))
    )

    shows = verify_tvmaze.search_shows("anything")

    assert [show["name"] for show in shows] == ["First", "Second"]


def test_empty_result_returns_empty_list(monkeypatch):
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=[]))
    )
    assert verify_tvmaze.search_shows("xqzzvvnotashow") == []


# ---------------------------------------------------------------------------
# search_shows: failed requests
# ---------------------------------------------------------------------------


def test_timeout_gives_friendly_message(monkeypatch):
    monkeypatch.setattr(verify_tvmaze.requests, "get", fake_get_raising(requests.Timeout()))
    with pytest.raises(verify_tvmaze.SearchError, match="did not respond within 10 seconds"):
        verify_tvmaze.search_shows("the office")


def test_connection_error_gives_friendly_message(monkeypatch):
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_raising(requests.ConnectionError())
    )
    with pytest.raises(verify_tvmaze.SearchError, match="Could not connect to TVmaze"):
        verify_tvmaze.search_shows("the office")


def test_other_request_error_gives_friendly_message(monkeypatch):
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_raising(requests.RequestException("boom"))
    )
    with pytest.raises(verify_tvmaze.SearchError, match="The request to TVmaze failed"):
        verify_tvmaze.search_shows("the office")


@pytest.mark.parametrize(
    "status_code, expected_message",
    [
        (429, "HTTP 429 \\(too many requests\\)"),
        (500, "HTTP 500 \\(a problem on TVmaze's side\\)"),
        (503, "HTTP 503 \\(a problem on TVmaze's side\\)"),
        (400, "HTTP 400\\. The search could not be completed"),
        (404, "HTTP 404\\. The search could not be completed"),
    ],
)
def test_http_error_status_gives_friendly_message(monkeypatch, status_code, expected_message):
    monkeypatch.setattr(
        verify_tvmaze.requests,
        "get",
        fake_get_returning(FakeResponse(status_code=status_code, json_data=[])),
    )
    with pytest.raises(verify_tvmaze.SearchError, match=expected_message):
        verify_tvmaze.search_shows("the office")


def test_invalid_json_gives_friendly_message(monkeypatch):
    bad_json = requests.JSONDecodeError("Expecting value", "<html>", 0)
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_error=bad_json))
    )
    with pytest.raises(verify_tvmaze.SearchError, match="invalid JSON"):
        verify_tvmaze.search_shows("the office")


@pytest.mark.parametrize(
    "data",
    [
        {"error": "not a list"},  # the body is not a list
        ["just a string"],  # an item is not a dictionary
        [{"score": 0.9}],  # an item has no "show"
        [{"score": 0.9, "show": None}],  # "show" is not a dictionary
        [{"score": 0.9, "show": {"name": "No ID", "url": "https://x"}}],  # missing "id"
        [{"score": 0.9, "show": {"id": 1, "url": "https://x"}}],  # missing "name"
        [{"score": 0.9, "show": {"id": 1, "name": "No URL"}}],  # missing "url"
    ],
)
def test_unexpected_data_gives_friendly_message(monkeypatch, data):
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=data))
    )
    with pytest.raises(verify_tvmaze.SearchError, match="unexpected data"):
        verify_tvmaze.search_shows("the office")


# ---------------------------------------------------------------------------
# format_show: fallbacks and layout
# ---------------------------------------------------------------------------


def first_line(show, number=1):
    return verify_tvmaze.format_show(show, number).splitlines()[0]


def test_full_show_is_formatted():
    assert verify_tvmaze.format_show(make_show(), 1) == (
        " 1. The Office (2005–2013)\n"
        "    Genres:    Comedy\n"
        "    Rating:    8.5\n"
        "    TVmaze ID: 526\n"
        "    Link:      https://www.tvmaze.com/shows/526/the-office"
    )


@pytest.mark.parametrize(
    "overrides, expected_years",
    [
        ({"premiered": "2024-10-18", "ended": "2024-10-18"}, "2024"),  # same year
        ({"premiered": "2012-04-15", "ended": None, "status": "Running"}, "2012–present"),
        ({"premiered": "2017-06-07", "ended": None, "status": "To Be Determined"}, "2017–N/A"),
        ({"premiered": None, "ended": None, "status": "In Development"},
         "Not yet aired, In Development"),
        ({"premiered": None, "ended": None, "status": "Ended"}, "N/A"),
        ({"premiered": None, "ended": None, "status": None}, "N/A"),
    ],
)
def test_years_fallbacks(overrides, expected_years):
    assert first_line(make_show(**overrides)) == f" 1. The Office ({expected_years})"


@pytest.mark.parametrize("genres", [[], None])
def test_missing_genres_show_na(genres):
    assert "Genres:    N/A" in verify_tvmaze.format_show(make_show(genres=genres), 1)


def test_multiple_genres_are_comma_separated():
    text = verify_tvmaze.format_show(make_show(genres=["Drama", "Comedy"]), 1)
    assert "Genres:    Drama, Comedy" in text


@pytest.mark.parametrize("rating", [{"average": None}, None, {}])
def test_missing_rating_shows_na(rating):
    assert "Rating:    N/A" in verify_tvmaze.format_show(make_show(rating=rating), 1)


def test_results_1_and_10_are_aligned():
    one = verify_tvmaze.format_show(make_show(), 1).splitlines()
    ten = verify_tvmaze.format_show(make_show(), 10).splitlines()

    # The title text starts in the same column for 1 and 10.
    assert one[0].index("The Office") == ten[0].index("The Office")
    # Every detail line is identical, so the details line up too.
    assert one[1:] == ten[1:]


# ---------------------------------------------------------------------------
# main: messages and exit codes
# ---------------------------------------------------------------------------


def test_blank_input_exits_1_without_calling_tvmaze(monkeypatch, capsys):
    def must_not_be_called(*args, **kwargs):
        raise AssertionError("TVmaze must not be called for blank input")

    monkeypatch.setattr(verify_tvmaze.requests, "get", must_not_be_called)

    assert verify_tvmaze.main(["   "]) == 1
    assert "Please enter a TV show name" in capsys.readouterr().err


def test_results_exit_0_and_are_numbered(monkeypatch, capsys):
    data = [
        {"score": 0.9, "show": make_show(id=1, name="First")},
        {"score": 0.5, "show": make_show(id=2, name="Second")},
    ]
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=data))
    )

    assert verify_tvmaze.main(["the office"]) == 0
    out = capsys.readouterr().out
    assert 'Found 2 shows for "the office"' in out
    assert out.index(" 1. First") < out.index(" 2. Second")


def test_single_result_uses_singular_wording(monkeypatch, capsys):
    data = [{"score": 0.9, "show": make_show()}]
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=data))
    )

    assert verify_tvmaze.main(["zz"]) == 0
    assert 'Found 1 show for "zz"' in capsys.readouterr().out


def test_more_than_10_results_shows_only_first_10(monkeypatch, capsys):
    data = [{"score": 1, "show": make_show(id=n, name=f"Show {n}")} for n in range(1, 13)]
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=data))
    )

    assert verify_tvmaze.main(["show"]) == 0
    out = capsys.readouterr().out
    assert 'Found 12 shows for "show" (showing the first 10)' in out
    assert "10. Show 10" in out
    assert "Show 11" not in out


def test_empty_result_exits_0_with_message(monkeypatch, capsys):
    monkeypatch.setattr(
        verify_tvmaze.requests, "get", fake_get_returning(FakeResponse(json_data=[]))
    )

    assert verify_tvmaze.main(["xqzzvvnotashow"]) == 0
    assert 'No shows found for "xqzzvvnotashow"' in capsys.readouterr().out


def test_failed_request_exits_1_with_error_on_stderr(monkeypatch, capsys):
    monkeypatch.setattr(verify_tvmaze.requests, "get", fake_get_raising(requests.Timeout()))

    assert verify_tvmaze.main(["the office"]) == 1
    captured = capsys.readouterr()
    assert captured.err.startswith("Error: TVmaze did not respond within 10 seconds")
    assert captured.out == ""
