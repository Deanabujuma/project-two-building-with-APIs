"""Discover browsing rows: Featured, Browse by Genre, Airing This Week, Recommended (post-submission feature).

TVmaze is replaced by FakeTVmaze, which answers schedule and image requests by URL and date.
"""

import datetime
import re

import pytest
import requests
from django.utils import timezone

from shows import browse, services
from shows.models import CollectionEntry, Show
from shows.tests.conftest import FakeResponse, raw_show


def network_entry(show, airtime="20:00", season=1, number=4):
    return {"airtime": airtime, "season": season, "number": number, "show": show}


def web_entry(show, airtime="03:00", season=1, number=1):
    return {"airtime": airtime, "season": season, "number": number, "_embedded": {"show": show}}


def streaming_show(tvmaze_id, name, country=None, **overrides):
    channel = {"id": 1, "name": "Global Stream", "country": {"name": "X", "code": country} if country else None}
    return raw_show(tvmaze_id, name, network=None, webChannel=channel, **overrides)


def backdrop_images(tvmaze_id):
    return [{"type": "background", "resolutions": {"original": {"url": f"https://img/{tvmaze_id}-bg.jpg", "width": 1920}}}]


class FakeTVmaze:
    """Answers /schedule, /schedule/web and /shows/<id>/images by date and ID; records calls."""

    def __init__(self):
        self.today = timezone.localdate()
        self.network, self.web, self.images, self.fail = {}, {}, {}, {}
        self.calls = []

    def day(self, offset):
        return (self.today + datetime.timedelta(days=offset)).isoformat()

    def __call__(self, url, params=None, headers=None, timeout=None):
        path = url.replace("https://api.tvmaze.com", "")
        self.calls.append((path, dict(params or {})))
        if path in self.fail:
            failure = self.fail[path]
            if isinstance(failure, Exception):
                raise failure
            return failure
        if path == "/schedule":
            return FakeResponse(200, self.network.get(params["date"], []))
        if path == "/schedule/web":
            return FakeResponse(200, self.web.get(params["date"], []))
        match = re.fullmatch(r"/shows/(\d+)/images", path)
        if match:
            return FakeResponse(200, self.images.get(int(match.group(1)), []))
        raise AssertionError(f"Unexpected TVmaze call: {path} {params}")

    def schedule_calls(self):
        return [c for c in self.calls if c[0].startswith("/schedule")]

    def image_calls(self):
        return [c for c in self.calls if c[0].endswith("/images")]


@pytest.fixture
def tv(monkeypatch):
    fake = FakeTVmaze()
    monkeypatch.setattr("shows.tvmaze.requests.get", fake)
    return fake


def rows(client):
    response = client.get("/discover/browse/?partial=1")
    assert response.status_code == 200
    return response.content.decode()


def row_html(html, key):
    match = re.search(rf'data-row="{key}"(.*?)</section>', html, re.S)
    return match.group(1) if match else ""


def tile_ids(fragment):
    return [int(i) for i in re.findall(r'data-tile="(\d+)"', fragment)]


# --- The Discover page itself -----------------------------------------------------------------------

def test_discover_page_has_search_and_a_browse_slot_without_calling_tvmaze(logged_in, tv):
    html = logged_in.get("/discover/").content.decode()
    assert 'name="q"' in html and 'data-state="start"' in html
    assert 'data-src="/discover/browse/?partial=1"' in html
    assert "Featured Shows" in html and "Airing This Week" in html  # placeholders while loading
    assert tv.calls == []


def test_search_results_page_has_no_browse_rows(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, [{"show": raw_show(1, "Found")}]))
    html = logged_in.get("/discover/", {"q": "found"}).content.decode()
    assert 'data-state="results"' in html and "data-browse-slot data-src" not in html and "fetch(" not in html


def test_blank_search_still_offers_the_browse_rows(logged_in, tv):
    html = logged_in.get("/discover/", {"q": "  "}).content.decode()
    assert 'data-state="blank"' in html and "data-browse-slot" in html
    assert tv.calls == []


@pytest.mark.parametrize("url", ["/discover/browse/", "/discover/browse/?partial=1", "/discover/genre/Drama/"])
def test_browsing_requires_login(client, db, tv, url):
    response = client.get(url)
    assert response.status_code == 302 and "/accounts/login/" in response.url
    assert tv.calls == []


def test_no_javascript_page_renders_rows_inline_with_search(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Inline Show"))]
    html = logged_in.get("/discover/browse/").content.decode()
    assert 'name="q"' in html and 'data-browse="rows"' in html and "Inline Show" in html


# --- Airing This Week -----------------------------------------------------------------------------------

def test_week_uses_two_requests_per_day_for_seven_days(logged_in, tv):
    rows(logged_in)
    calls = tv.schedule_calls()
    assert len(calls) == 14
    days = [tv.day(i) for i in range(7)]
    assert [c[1]["date"] for c in calls if c[0] == "/schedule"] == days
    assert all(c[1]["country"] == "US" for c in calls if c[0] == "/schedule")
    assert [c[1]["date"] for c in calls if c[0] == "/schedule/web"] == days


def test_airing_lists_each_show_once_at_its_first_airing_in_date_order(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Today Show"), airtime="21:00", season=2, number=5)]
    tv.network[tv.day(1)] = [network_entry(raw_show(2, "Tomorrow Show"))]
    tv.network[tv.day(3)] = [network_entry(raw_show(1, "Today Show")), network_entry(raw_show(3, "Later Show"))]
    airing = row_html(rows(logged_in), "airing")
    assert tile_ids(airing) == [1, 2, 3]
    assert "Today · 21:00 · S2 E5" in airing and "Tomorrow" in airing


def test_streaming_shows_are_filtered_by_country(logged_in, tv):
    tv.web[tv.day(0)] = [web_entry(streaming_show(10, "Global")), web_entry(streaming_show(11, "US Stream", "US")),
                         web_entry(streaming_show(12, "UK Stream", "GB"))]
    assert tile_ids(row_html(rows(logged_in), "airing")) == [10, 11]


def test_malformed_schedule_entries_are_skipped(logged_in, tv):
    tv.network[tv.day(0)] = [{"show": {"name": "no id"}}, "junk", network_entry(raw_show(5, "Good"))]
    assert tile_ids(row_html(rows(logged_in), "airing")) == [5]


# --- Featured -----------------------------------------------------------------------------------------------

def test_featured_is_the_ten_highest_rated_shows_airing_this_week(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(i, f"Show {i:02d}", rating={"average": 5 + i / 10})) for i in range(1, 13)]
    tv.network[tv.day(1)] = [network_entry(raw_show(99, "Unrated", rating={"average": None}))]
    featured = row_html(rows(logged_in), "featured")
    assert tile_ids(featured) == list(range(12, 2, -1))
    assert "6.2 on TVmaze" in featured


def test_featured_uses_real_backdrops_and_poster_fallbacks(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Has Backdrop", rating={"average": 9})),
                             network_entry(raw_show(2, "No Backdrop", rating={"average": 8}))]
    tv.images[1] = backdrop_images(1)
    featured = row_html(rows(logged_in), "featured")
    assert 'data-tile="1" data-art="backdrop"' in featured and "https://img/1-bg.jpg" in featured
    assert 'data-tile="2" data-art="poster-fallback"' in featured and 'class="wf-poster"' in featured
    assert len(tv.image_calls()) == 2


def test_stored_show_backdrops_are_used_without_a_request(logged_in, tv, db):
    Show.objects.create(tvmaze_id=1, name="Stored", tvmaze_url="https://www.tvmaze.com/shows/1",
                        background_url="https://img/stored-bg.jpg")
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Stored", rating={"average": 9}))]
    html = rows(logged_in)
    assert "https://img/stored-bg.jpg" in row_html(html, "featured") and tv.image_calls() == []


def test_a_failed_backdrop_lookup_stops_further_lookups_and_falls_back(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(i, f"S{i}", rating={"average": 10 - i})) for i in (1, 2, 3)]
    tv.fail["/shows/1/images"] = FakeResponse(429)
    featured = row_html(rows(logged_in), "featured")
    assert len(tv.image_calls()) == 1
    assert featured.count('data-art="poster-fallback"') == 3


def test_missing_poster_and_backdrop_shows_the_initial(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Zed", image=None, rating={"average": 7}))]
    assert 'data-art="initial"' in row_html(rows(logged_in), "featured")


# --- Caching and failures -----------------------------------------------------------------------------------

def test_second_visit_uses_the_cache(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Cached", rating={"average": 8}))]
    tv.images[1] = backdrop_images(1)
    first = rows(logged_in)
    calls_after_first = len(tv.calls)
    second = rows(logged_in)
    assert len(tv.calls) == calls_after_first == 15
    assert tile_ids(row_html(first, "featured")) == tile_ids(row_html(second, "featured")) == [1]


@pytest.mark.parametrize("failure", [requests.Timeout(), FakeResponse(503), FakeResponse(200, invalid_json=True)])
def test_schedule_failure_shows_a_note_and_local_rows_still_render(logged_in, tv, user, failure):
    show = Show.objects.create(tvmaze_id=50, name="Saved Drama", tvmaze_url="https://www.tvmaze.com/shows/50", genres="Drama")
    CollectionEntry.objects.create(user=user, show=show)
    Show.objects.create(tvmaze_id=51, name="Other Drama", tvmaze_url="https://www.tvmaze.com/shows/51", genres="Drama")
    tv.fail["/schedule"] = failure
    html = rows(logged_in)
    assert 'data-state="schedule-error"' in html
    assert tile_ids(row_html(html, "recommended")) == [51]
    assert 'data-row="genres"' in html and 'data-row="airing"' not in html


def test_failures_are_not_cached(logged_in, tv):
    tv.fail["/schedule"] = FakeResponse(503)
    rows(logged_in)
    del tv.fail["/schedule"]
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Back Again"))]
    assert tile_ids(row_html(rows(logged_in), "airing")) == [1]


def test_partial_week_is_shown_when_a_later_day_fails(logged_in, tv, monkeypatch):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Day Zero"))]
    real = tv.__call__

    def fail_on_day_two(url, params=None, **kwargs):
        if params and params.get("date") == tv.day(2):
            raise requests.ConnectionError()
        return real(url, params=params, **kwargs)

    monkeypatch.setattr("shows.tvmaze.requests.get", fail_on_day_two)
    html = rows(logged_in)
    assert tile_ids(row_html(html, "airing")) == [1] and 'data-state="schedule-error"' in html
    assert len(tv.schedule_calls()) == 4  # days 0 and 1 (two calls each); stopped at day 2


# --- Browse by Genre ------------------------------------------------------------------------------------------

def test_genre_tiles_count_week_and_stored_shows(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "A", genres=["Comedy"])),
                             network_entry(raw_show(2, "B", genres=["Comedy", "Drama"]))]
    Show.objects.create(tvmaze_id=3, name="C", tvmaze_url="https://www.tvmaze.com/shows/3", genres="Drama, Horror")
    Show.objects.create(tvmaze_id=2, name="B", tvmaze_url="https://www.tvmaze.com/shows/2", genres="Comedy, Drama")
    genres = row_html(rows(logged_in), "genres")
    tiles = re.findall(r'href="(/discover/genre/[^"]+/)" data-genre="([^"]+)">\s*<span class="gname">[^<]+</span><span class="gcount">(\d+) show', genres)
    assert [(g, int(n)) for _, g, n in tiles] == [("Comedy", 2), ("Drama", 2), ("Horror", 1)]
    assert tiles[0][0] == "/discover/genre/Comedy/"


def test_genre_page_lists_airing_and_stored_shows(logged_in, tv):
    tv.network[tv.day(1)] = [network_entry(raw_show(1, "Airing Sci", genres=["Science-Fiction"])),
                             network_entry(raw_show(2, "Airing Comedy", genres=["Comedy"]))]
    Show.objects.create(tvmaze_id=3, name="Stored Sci", tvmaze_url="https://www.tvmaze.com/shows/3", genres="Drama, Science-Fiction")
    Show.objects.create(tvmaze_id=4, name="Not Quite", tvmaze_url="https://www.tvmaze.com/shows/4", genres="Science")
    html = logged_in.get("/discover/genre/science-fiction/").content.decode()
    assert "<h1" in html and ">Science-Fiction</h1>" in html
    airing = re.search(r'data-section="airing"(.*?)</section>', html, re.S).group(1)
    stored = re.search(r'data-section="stored"(.*?)</section>', html, re.S).group(1)
    assert tile_ids(airing) == [1] and tile_ids(stored) == [3]


def test_unknown_genre_shows_an_empty_state(logged_in, tv):
    html = logged_in.get("/discover/genre/Polka/").content.decode()
    assert 'data-state="genre-empty"' in html and "No Polka shows found" in html


def test_genre_name_is_escaped(logged_in, tv):
    response = logged_in.get("/discover/genre/<em>Sneaky/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "<em>Sneaky" not in html and "&lt;em&gt;Sneaky" in html


# --- Recommended From My Collection -------------------------------------------------------------------------

def test_recommended_ranks_by_shared_genres_and_excludes_saved_shows(logged_in, tv, user):
    for tvmaze_id, name, genres in [(1, "Mine A", "Drama, Crime"), (2, "Mine B", "Drama, Thriller")]:
        CollectionEntry.objects.create(user=user, show=Show.objects.create(
            tvmaze_id=tvmaze_id, name=name, tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}", genres=genres))
    Show.objects.create(tvmaze_id=3, name="Crime Only", tvmaze_url="https://www.tvmaze.com/shows/3", genres="Crime")
    Show.objects.create(tvmaze_id=4, name="Comedy Only", tvmaze_url="https://www.tvmaze.com/shows/4", genres="Comedy")
    tv.network[tv.day(0)] = [network_entry(raw_show(5, "Drama Crime Live", genres=["Drama", "Crime"])),
                             network_entry(raw_show(1, "Mine A", genres=["Drama", "Crime"]))]
    recommended = row_html(rows(logged_in), "recommended")
    assert tile_ids(recommended) == [5, 3]
    assert "not a TVmaze recommendation" in recommended


def test_recommended_explains_itself_when_the_collection_is_empty(logged_in, tv):
    assert 'data-state="recommend-empty"' in rows(logged_in)


def test_recommended_for_user_weights_genres_by_how_often_they_appear(user):
    for tvmaze_id, genres in [(1, "Drama"), (2, "Drama"), (3, "Comedy")]:
        CollectionEntry.objects.create(user=user, show=Show.objects.create(
            tvmaze_id=tvmaze_id, name=f"Mine {tvmaze_id}", tvmaze_url="https://x", genres=genres))
    candidates = [{"tvmaze_id": 10, "name": "Comedy Pick", "genres": "Comedy"},
                  {"tvmaze_id": 11, "name": "Drama Pick", "genres": "Drama"}]
    assert [s["name"] for s in services.recommended_for_user(user, candidates)] == ["Drama Pick", "Comedy Pick"]


# --- Cards, honesty and safety ------------------------------------------------------------------------------

def test_every_card_opens_its_details_page_and_saved_shows_are_flagged(logged_in, tv, user):
    show = Show.objects.create(tvmaze_id=7, name="Saved", tvmaze_url="https://www.tvmaze.com/shows/7")
    CollectionEntry.objects.create(user=user, show=show, status="watching")
    tv.network[tv.day(0)] = [network_entry(raw_show(7, "Saved")), network_entry(raw_show(8, "Unsaved"))]
    airing = row_html(rows(logged_in), "airing")
    links = re.findall(r'<a class="tile[^"]*" href="([^"]+)" data-tile="(\d+)"', airing)
    assert links == [("/shows/7/", "7"), ("/shows/8/", "8")]
    assert "In your collection" in airing.split('data-tile="8"')[0]


def test_rows_never_claim_trending_or_popular(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Any", rating={"average": 9}))]
    html = rows(logged_in).lower()
    assert "trending" not in html and "popular" not in html


def test_browsing_never_saves_anything(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Just Looking", rating={"average": 9}))]
    rows(logged_in)
    logged_in.get("/discover/genre/Comedy/")
    assert Show.objects.count() == 0 and CollectionEntry.objects.count() == 0


def test_week_schedule_unit_labels(tv):
    tv.network[tv.day(2)] = [network_entry(raw_show(1, "Later"))]
    shows, error = browse.week_schedule("US", today=tv.today)
    assert error == "" and shows[0]["airs_label"] == browse._day_label(tv.today + datetime.timedelta(days=2), tv.today)
    assert shows[0]["airs_label"] not in ("Today", "Tomorrow")


def test_within_a_day_higher_tvmaze_ratings_come_first_and_unrated_last(logged_in, tv):
    tv.network[tv.day(0)] = [network_entry(raw_show(1, "Unrated Early", rating={"average": None}), airtime="06:00"),
                             network_entry(raw_show(2, "Good", rating={"average": 7.0}), airtime="22:00"),
                             network_entry(raw_show(3, "Best", rating={"average": 8.5}), airtime="23:00")]
    tv.network[tv.day(1)] = [network_entry(raw_show(4, "Tomorrow Best", rating={"average": 9.9}))]
    assert tile_ids(row_html(rows(logged_in), "airing")) == [3, 2, 1, 4]
