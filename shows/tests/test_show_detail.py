"""Phase 5: complete show details page (AC16–AC20, AC22)."""

import pytest

from shows import services, tvmaze
from shows.models import CollectionEntry, Show
from shows.tests.conftest import FAILURES, FakeResponse, raw_show


def make_show(tvmaze_id, name, genres="", **fields):
    return Show.objects.create(tvmaze_id=tvmaze_id, name=name, genres=genres,
                               tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}", **fields)


def with_extras(raw):
    raw["_embedded"] = {
        "seasons": [{"number": 1, "episodeOrder": 9, "premiereDate": "2022-02-18", "endDate": "2022-04-08"},
                    {"number": 2, "episodeOrder": None, "premiereDate": "2025-01-17", "endDate": None}],
        "cast": [{"person": {"name": f"Actor {i}", "image": {"medium": f"https://img/{i}.jpg"} if i % 2 else None},
                  "character": {"name": f"Character {i}"}} for i in range(1, 11)],
    }
    return raw


# --- AC16: saved shows render from local data --------------------------------------------------

def test_saved_show_default_and_suggested_tabs_make_no_tvmaze_calls(logged_in, user, tvmaze_stub):
    show = make_show(1, "Saved Show", "Drama")
    CollectionEntry.objects.create(user=user, show=show)
    for url in ["/shows/1/", "/shows/1/?tab=tracking", "/shows/1/?tab=suggested"]:
        assert logged_in.get(url).status_code == 200
    assert tvmaze_stub.calls == []


def test_saved_show_defaults_to_tracking_tab(logged_in, user, db):
    CollectionEntry.objects.create(user=user, show=make_show(1, "Saved Show"))
    html = logged_in.get("/shows/1/").content.decode()
    assert 'data-panel="tracking"' in html


# --- AC17: unsaved shows are fetched live and never stored --------------------------------------

def test_unsaved_show_is_fetched_once_and_not_saved(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(44933, "Severance")))
    response = logged_in.get("/shows/44933/")
    assert response.status_code == 200
    html = response.content.decode()
    assert "Severance" in html and "Add to my collection" in html
    assert 'name="tvmaze_id" value="44933"' in html
    assert len(tvmaze_stub.calls) == 1
    assert Show.objects.count() == 0 and CollectionEntry.objects.count() == 0


def test_unsaved_show_defaults_to_suggested_tab(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(5, "Unsaved")))
    html = logged_in.get("/shows/5/").content.decode()
    assert 'data-panel="suggested"' in html and 'data-tab="tracking"' not in html


def test_unknown_show_returns_404(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(404, {}))
    assert logged_in.get("/shows/999999999/").status_code == 404


@pytest.mark.parametrize("failure, phrase", FAILURES)
def test_tvmaze_outage_for_unsaved_show_shows_friendly_page(logged_in, tvmaze_stub, failure, phrase):
    tvmaze_stub.queue(failure)
    response = logged_in.get("/shows/5/")
    assert response.status_code == 503
    html = response.content.decode()
    assert 'data-state="show-unavailable"' in html and "Try again" in html
    assert Show.objects.count() == 0


def test_show_saved_by_another_user_renders_locally_with_add_button(logged_in, other_user, tvmaze_stub):
    CollectionEntry.objects.create(user=other_user, show=make_show(8, "Their Show"))
    html = logged_in.get("/shows/8/").content.decode()
    assert "Add to my collection" in html and 'data-tab="tracking"' not in html
    assert tvmaze_stub.calls == []


# --- AC18: tabs ------------------------------------------------------------------------------------

def test_saved_show_has_exactly_three_tabs_and_no_franchise(logged_in, user, db):
    CollectionEntry.objects.create(user=user, show=make_show(1, "Saved Show"))
    html = logged_in.get("/shows/1/").content.decode()
    assert html.count("data-tab=") == 3
    for key in ["tracking", "suggested", "extras"]:
        assert f'data-tab="{key}"' in html
    assert "franchise" not in html.lower()


def test_unsaved_show_has_two_tabs(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(5, "Unsaved")))
    html = logged_in.get("/shows/5/").content.decode()
    assert html.count("data-tab=") == 2 and "franchise" not in html.lower()


def test_unknown_tab_falls_back_to_default(logged_in, user, db):
    CollectionEntry.objects.create(user=user, show=make_show(1, "Saved Show"))
    html = logged_in.get("/shows/1/?tab=franchise").content.decode()
    assert 'data-panel="tracking"' in html


# --- AC19: Suggested ------------------------------------------------------------------------------

@pytest.mark.django_db
def test_suggested_ranks_by_shared_genres_then_name_and_excludes_current():
    make_show(1, "Current", "Drama, Thriller, Science-Fiction")
    make_show(2, "Zed Two Shared", "Drama, Thriller")
    make_show(3, "Alpha Two Shared", "Thriller, Drama, Comedy")
    make_show(4, "Beta One Shared", "Science-Fiction")
    make_show(5, "Melodrama Only", "Melodrama")        # substring of Drama, but not the same genre
    make_show(6, "No Genres", "")
    names = [s.name for s in services.suggested_shows(1, "Drama, Thriller, Science-Fiction")]
    assert names == ["Alpha Two Shared", "Zed Two Shared", "Beta One Shared"]


@pytest.mark.django_db
def test_suggested_is_empty_for_show_without_genres():
    make_show(2, "Other", "Drama")
    assert services.suggested_shows(1, "") == []


def test_suggested_tab_shows_honest_label_and_saved_marker(logged_in, user, db):
    current = make_show(1, "Current", "Drama")
    mine = make_show(2, "Mine Drama", "Drama")
    make_show(3, "Other Drama", "Drama")
    CollectionEntry.objects.create(user=user, show=current)
    CollectionEntry.objects.create(user=user, show=mine, status="watching", current_season=1, current_episode=4)
    html = logged_in.get("/shows/1/?tab=suggested").content.decode()
    assert "Matched locally by genre; not a TVmaze recommendation." in html
    mine_tile = html[html.index('data-tile="2"'):html.index('data-tile="3"')]
    other_tile = html[html.index('data-tile="3"'):]
    assert "tile-flag" in mine_tile and "Season 1, Episode 4" in mine_tile
    assert "tile-flag" not in other_tile[:600] and "Not in your collection" in other_tile


def test_suggested_empty_state(logged_in, user, db):
    CollectionEntry.objects.create(user=user, show=make_show(1, "Lonely", "Western"))
    html = logged_in.get("/shows/1/?tab=suggested").content.decode()
    assert 'data-empty="suggested"' in html


# --- AC20: Extras ------------------------------------------------------------------------------------

def test_extras_tab_for_saved_show_makes_one_call(logged_in, user, tvmaze_stub):
    CollectionEntry.objects.create(user=user, show=make_show(44933, "Severance"))
    tvmaze_stub.queue(FakeResponse(200, with_extras(raw_show(44933, "Severance"))))
    html = logged_in.get("/shows/44933/?tab=extras").content.decode()
    assert len(tvmaze_stub.calls) == 1
    assert tvmaze_stub.calls[0]["params"] == {"embed[]": ["seasons", "cast"]}
    assert "Season 1" in html and "9 episodes" in html and "2022" in html
    assert "Season 2" in html and "Episodes TBA" in html
    assert "Actor 8" in html and "Actor 9" not in html  # at most 8 cast members
    assert "Character 1" in html


def test_extras_for_unsaved_show_uses_a_single_combined_call(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, with_extras(raw_show(5, "Unsaved"))))
    html = logged_in.get("/shows/5/?tab=extras").content.decode()
    assert len(tvmaze_stub.calls) == 1
    assert tvmaze_stub.calls[0]["params"] == {"embed[]": ["images", "seasons", "cast"]}
    assert "Unsaved" in html and "Actor 1" in html
    assert Show.objects.count() == 0


@pytest.mark.parametrize("failure, phrase", FAILURES)
def test_extras_failure_does_not_break_the_page(logged_in, user, tvmaze_stub, failure, phrase):
    CollectionEntry.objects.create(user=user, show=make_show(1, "Saved Show", summary="Still here."))
    tvmaze_stub.queue(failure)
    response = logged_in.get("/shows/1/?tab=extras")
    assert response.status_code == 200
    html = response.content.decode()
    assert "data-extras-error" in html and "Still here." in html


def test_map_extras_handles_missing_data():
    assert tvmaze.map_extras({}) == {"seasons": [], "cast": []}
    assert tvmaze.map_extras(None) == {"seasons": [], "cast": []}


# --- AC22: only verified information --------------------------------------------------------------

@pytest.mark.parametrize("channel_type, heading, subtitle", [
    ("network", "Where to watch · original network", "Original network · United States · verified by TVmaze"),
    ("web channel", "Where to watch · original web channel", "Original web channel · United States · verified by TVmaze"),
])
def test_where_to_watch_heading_and_subtitle(logged_in, db, channel_type, heading, subtitle):
    make_show(1, "Show", network="Some Channel", channel_type=channel_type, channel_country="United States")
    html = logged_in.get("/shows/1/").content.decode()
    assert heading in html and subtitle in html


def test_channel_country_only_shown_when_stored(logged_in, db):
    make_show(1, "Show", network="Apple TV", channel_type="web channel", channel_country="")
    html = logged_in.get("/shows/1/").content.decode()
    assert "Original web channel · verified by TVmaze" in html


def test_no_made_up_availability_or_ratings(logged_in, user, db):
    CollectionEntry.objects.create(user=user, show=make_show(1, "Show", "Drama", network="ABC", channel_type="network"))
    for tab in ["tracking", "suggested"]:
        html = logged_in.get(f"/shows/1/?tab={tab}").content.decode().lower()
        for invented in ["illustrative", "stream on", "tv-ma", "tv-14", "closed captions", ">hd<", ">cc<"]:
            assert invented not in html


def test_styled_404_page_when_debug_is_off(logged_in, tvmaze_stub, settings):
    settings.DEBUG = False
    tvmaze_stub.queue(FakeResponse(404, {}))
    response = logged_in.get("/shows/999999999/")
    assert response.status_code == 404
    assert 'data-state="not-found"' in response.content.decode()
