"""TVmaze client: request details, mapping rules and error handling (Phase 3)."""

import pytest

from shows import tvmaze
from shows.tests.conftest import FAILURES, FakeResponse, raw_show


def search_payload(*shows):
    return [{"score": 1.0 - i / 100, "show": show} for i, show in enumerate(shows)]


def test_search_sends_query_timeout_and_user_agent(tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, []))
    tvmaze.search_shows("café")
    call = tvmaze_stub.calls[0]
    assert call["url"] == "https://api.tvmaze.com/search/shows"
    assert call["params"] == {"q": "café"}
    assert call["timeout"] == 10
    assert call["headers"] == {"User-Agent": "HTTP.tv/0.1"}


def test_search_keeps_tvmaze_order_and_limits_to_ten(tvmaze_stub):
    shows = [raw_show(i, f"Show {i}") for i in range(1, 13)]
    tvmaze_stub.queue(FakeResponse(200, search_payload(*shows)))
    results = tvmaze.search_shows("show")
    assert [r["tvmaze_id"] for r in results] == list(range(1, 11))


def test_search_with_no_matches_returns_empty_list(tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, []))
    assert tvmaze.search_shows("xqzzvvnotashow") == []


@pytest.mark.parametrize("failure, phrase", FAILURES)
def test_search_failures_raise_friendly_errors(tvmaze_stub, failure, phrase):
    tvmaze_stub.queue(failure)
    with pytest.raises(tvmaze.TVmazeError) as excinfo:
        tvmaze.search_shows("anything")
    assert phrase in str(excinfo.value)


def test_search_result_missing_required_fields_is_unreadable(tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, [{"score": 1, "show": {"id": 5}}]))
    with pytest.raises(tvmaze.TVmazeError):
        tvmaze.search_shows("x")


def test_map_show_converts_every_field():
    mapped = tvmaze.map_show(raw_show(123, "Abbott Elementary"))
    assert mapped == {
        "tvmaze_id": 123,
        "name": "Abbott Elementary",
        "tvmaze_url": "https://www.tvmaze.com/shows/123/sample-show",
        "image_url": "https://static.tvmaze.com/medium/123.jpg",
        "premiered": "2021-12-07",
        "ended": None,
        "show_status": "Running",
        "genres": "Comedy, Drama",
        "summary": "A sample show & its story.",
        "network": "ABC",
        "channel_type": "network",
        "channel_country": "United States",
        "background_url": "",
        "runtime": 30,
        "tvmaze_rating": 7.9,
        "language": "English",
        "show_type": "Scripted",
    }


def test_map_show_handles_missing_optional_values():
    mapped = tvmaze.map_show(raw_show(
        9, "Sparse", image=None, premiered=None, genres=[], rating={"average": None},
        runtime=None, averageRuntime=None, summary=None, network=None, language=None, type=None, status=None,
    ))
    assert mapped["image_url"] == "" and mapped["premiered"] is None and mapped["genres"] == ""
    assert mapped["tvmaze_rating"] is None and mapped["runtime"] is None and mapped["summary"] == ""
    assert mapped["network"] == mapped["channel_type"] == mapped["channel_country"] == ""
    assert mapped["language"] == mapped["show_type"] == mapped["show_status"] == ""


def test_runtime_falls_back_to_average_runtime():
    assert tvmaze.map_show(raw_show(runtime=None, averageRuntime=52))["runtime"] == 52


def test_strip_html_removes_tags_and_decodes_entities():
    html = "<p><b>Mark</b> leads a team.</p><p>Caf&eacute; &amp; more&#39;s</p>"
    assert tvmaze.strip_html(html) == "Mark leads a team. Café & more's"
    assert tvmaze.strip_html(None) == ""
