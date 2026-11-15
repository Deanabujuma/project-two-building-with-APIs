"""Discover search page (AC8, AC9)."""

import pytest

from shows.tests.conftest import FAILURES, FakeResponse, raw_show


def payload(*shows):
    return [{"score": 1, "show": s} for s in shows]


def test_results_are_shown_in_tvmaze_order(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, payload(raw_show(2, "Zeta Show"), raw_show(1, "Alpha Show"))))
    html = logged_in.get("/discover/", {"q": "show"}).content.decode()
    assert 'data-state="results"' in html
    assert html.index("Zeta Show") < html.index("Alpha Show")
    assert "2 results for" in html
    assert "Not in your collection" in html


def test_at_most_ten_results(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, payload(*[raw_show(i, f"Show number {i}") for i in range(1, 16)])))
    html = logged_in.get("/discover/", {"q": "show"}).content.decode()
    assert html.count('class="pcard') == 10


@pytest.mark.parametrize("query", ["", "   "])
def test_blank_query_shows_guidance_without_calling_tvmaze(logged_in, tvmaze_stub, query):
    html = logged_in.get("/discover/", {"q": query}).content.decode()
    assert 'data-state="blank"' in html
    assert tvmaze_stub.calls == []


def test_first_visit_makes_no_tvmaze_call(logged_in, tvmaze_stub):
    html = logged_in.get("/discover/").content.decode()
    assert 'data-state="start"' in html
    assert tvmaze_stub.calls == []


def test_query_is_trimmed_before_searching(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, []))
    logged_in.get("/discover/", {"q": "  the office  "})
    assert tvmaze_stub.calls[0]["params"] == {"q": "the office"}


def test_no_results_message(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, []))
    html = logged_in.get("/discover/", {"q": "xqzzvvnotashow"}).content.decode()
    assert 'data-state="no-results"' in html and "No shows found" in html


@pytest.mark.parametrize("failure, phrase", FAILURES)
def test_tvmaze_failures_show_a_friendly_message_not_an_error_page(logged_in, tvmaze_stub, failure, phrase):
    tvmaze_stub.queue(failure)
    response = logged_in.get("/discover/", {"q": "the office"})
    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-state="error"' in html
    assert phrase.replace("'", "&#x27;") in html or phrase in html


def test_search_text_is_escaped(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, []))
    html = logged_in.get("/discover/", {"q": "<script>alert(1)</script>"}).content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
