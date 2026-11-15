"""Phase 4b: backdrop and channel rules, get_show, and the secure save flow
(AC5, AC5b, AC10–AC15a, AC53)."""

import pytest

from shows import tvmaze
from shows.models import CollectionEntry, Show
from shows.tests.conftest import FAILURES, FakeResponse, raw_show


def background(width, url=None, kind="background"):
    return {"type": kind, "main": False,
            "resolutions": {"original": {"url": url or f"https://img/{kind}-{width}.jpg", "width": width, "height": 1080}}}


# --- AC15: backdrop rule ----------------------------------------------------------------------

def test_backdrop_picks_the_widest_background_at_least_1920():
    images = [background(1920, "a"), background(3840, "widest"), background(2560, "b")]
    assert tvmaze.pick_backdrop(images) == "widest"


def test_backdrop_ties_keep_tvmaze_order():
    assert tvmaze.pick_backdrop([background(1920, "first"), background(1920, "second")]) == "first"


def test_backdrop_ignores_backgrounds_narrower_than_1920():
    assert tvmaze.pick_backdrop([background(1280), background(1919)]) == ""


def test_backdrop_ignores_posters_and_banners_even_when_wide():
    assert tvmaze.pick_backdrop([background(4000, kind="poster"), background(4000, kind="banner")]) == ""


@pytest.mark.parametrize("images", [None, [], [{"type": "background"}], [{"type": "background", "resolutions": {}}]])
def test_backdrop_handles_missing_data(images):
    assert tvmaze.pick_backdrop(images) == ""


def test_embedded_images_feed_the_backdrop():
    raw = raw_show(_embedded={"images": [background(1280), background(1920, "big")]})
    assert tvmaze.map_show(raw)["background_url"] == "big"


# --- AC15a: channel mapping ---------------------------------------------------------------------

def test_channel_from_network():
    assert tvmaze.channel_info(raw_show()) == ("ABC", "network", "United States")


def test_channel_from_web_channel_only_with_no_country():
    raw = raw_show(network=None, webChannel={"id": 310, "name": "Apple TV+", "country": None})
    assert tvmaze.channel_info(raw) == ("Apple TV+", "web channel", "")


def test_network_wins_when_both_are_present():
    raw = raw_show(webChannel={"name": "Hulu", "country": None})
    assert tvmaze.channel_info(raw)[:2] == ("ABC", "network")


def test_no_channel():
    assert tvmaze.channel_info(raw_show(network=None, webChannel=None)) == ("", "", "")


# --- get_show -------------------------------------------------------------------------------------

def test_get_show_requests_images_in_one_call(tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(44933, "Severance")))
    assert tvmaze.get_show(44933)["name"] == "Severance"
    assert len(tvmaze_stub.calls) == 1
    assert tvmaze_stub.calls[0]["url"] == "https://api.tvmaze.com/shows/44933"
    assert tvmaze_stub.calls[0]["params"] == {"embed[]": ["images"]}


def test_get_show_unknown_id_raises_show_not_found(tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(404, {"name": "Not Found"}))
    with pytest.raises(tvmaze.ShowNotFound):
        tvmaze.get_show(999999999)


# --- Save flow --------------------------------------------------------------------------------------

def save(client, tvmaze_id, **extra):
    return client.post("/collection/add/", {"tvmaze_id": tvmaze_id, **extra})


def test_save_creates_show_and_entry_with_defaults_and_redirects(logged_in, user, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(169, "Abbott Elementary", _embedded={"images": [background(1920, "bd")]})))
    response = save(logged_in, 169)
    assert response.status_code == 302
    assert response.url == "/shows/169/?tab=tracking"
    show = Show.objects.get(tvmaze_id=169)
    assert show.name == "Abbott Elementary" and show.background_url == "bd" and show.network == "ABC"
    entry = CollectionEntry.objects.get(user=user, show=show)
    assert entry.status == "plan_to_watch" and entry.current_season is None and entry.rating is None
    page = logged_in.get(response.url).content.decode()
    assert "Saved Abbott Elementary to your collection as Plan to Watch." in page


def test_save_uses_only_tvmaze_id_and_ignores_posted_show_fields(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(7, "Real Name")))
    save(logged_in, 7, name="Fake Name", network="Fake Network", image_url="https://evil.example/x.jpg", summary="lies")
    show = Show.objects.get(tvmaze_id=7)
    assert show.name == "Real Name" and show.network == "ABC"
    assert "evil" not in show.image_url and show.summary != "lies"


def test_saving_refreshes_an_existing_show_row(logged_in, other_user, tvmaze_stub):
    old = Show.objects.create(tvmaze_id=7, name="Old Name", tvmaze_url="https://www.tvmaze.com/shows/7", show_status="Running")
    CollectionEntry.objects.create(user=other_user, show=old)
    tvmaze_stub.queue(FakeResponse(200, raw_show(7, "New Name", status="Ended", ended="2024-01-01")))
    save(logged_in, 7)
    assert Show.objects.filter(tvmaze_id=7).count() == 1
    old.refresh_from_db()
    assert old.name == "New Name" and old.show_status == "Ended"


def test_saving_twice_is_refused_without_calling_tvmaze(logged_in, user, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(7, "Show Seven")))
    save(logged_in, 7)
    response = save(logged_in, 7)
    assert len(tvmaze_stub.calls) == 1
    assert CollectionEntry.objects.filter(user=user).count() == 1
    assert response.url == "/shows/7/?tab=tracking"
    assert "Show Seven is already in your collection." in logged_in.get(response.url).content.decode()


@pytest.mark.parametrize("failure, phrase", FAILURES)
def test_tvmaze_failure_saves_nothing_and_explains(logged_in, tvmaze_stub, failure, phrase):
    tvmaze_stub.queue(failure)
    response = save(logged_in, 7, next="/discover/?q=seven")
    assert response.url == "/discover/?q=seven"
    assert Show.objects.count() == 0 and CollectionEntry.objects.count() == 0
    tvmaze_stub.queue(FakeResponse(200, []))
    html = logged_in.get(response.url).content.decode()
    assert "The show wasn&#x27;t saved." in html


def test_unknown_tvmaze_id_saves_nothing(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(404, {}))
    response = save(logged_in, 999999999)
    assert Show.objects.count() == 0
    assert "TVmaze has no show with that ID" in logged_in.get(response.url).content.decode()


@pytest.mark.parametrize("bad_id", ["", "abc", "0", "-5", "1.5"])
def test_invalid_tvmaze_id_is_rejected_without_calling_tvmaze(logged_in, tvmaze_stub, bad_id):
    response = save(logged_in, bad_id)
    assert response.status_code == 302 and tvmaze_stub.calls == []
    assert Show.objects.count() == 0


def test_next_url_cannot_redirect_off_site(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(503))
    response = save(logged_in, 7, next="https://evil.example/")
    assert response.url == "/discover/"


def test_anonymous_save_redirects_to_login(client, db, tvmaze_stub):
    response = save(client, 7)
    assert response.status_code == 302 and response.url.startswith("/accounts/login/")
    assert tvmaze_stub.calls == []


def test_get_on_save_url_is_not_allowed(logged_in):
    assert logged_in.get("/collection/add/").status_code == 405


# --- Basic show page and Discover marker -------------------------------------------------------

def test_saved_show_page_shows_details_and_tvmaze_links(logged_in, user, db):
    show = Show.objects.create(tvmaze_id=44933, name="Severance", tvmaze_url="https://www.tvmaze.com/shows/44933/severance",
                               network="Apple TV+", channel_type="web channel", genres="Drama, Thriller",
                               show_status="Running", premiered="2022-02-18", summary="Mark leads a team.")
    CollectionEntry.objects.create(user=user, show=show, status="watching", current_season=2, current_episode=3)
    html = logged_in.get("/shows/44933/?tab=tracking").content.decode()
    assert "Severance" in html and "Mark leads a team." in html and "2022–present" in html
    assert "Watching · Season 2, Episode 3" in html
    assert "Where to watch · original web channel" in html
    watch = html[html.index("data-watch-link") - 200: html.index("data-watch-link")]
    assert 'href="https://www.tvmaze.com/shows/44933/severance"' in watch
    assert "View on TVmaze" in html


def test_show_page_without_channel_says_so(logged_in, db):
    Show.objects.create(tvmaze_id=1, name="No Channel", tvmaze_url="https://www.tvmaze.com/shows/1")
    html = logged_in.get("/shows/1/").content.decode()
    assert "No network or web channel listed on TVmaze." in html


def test_discover_marks_shows_already_saved(logged_in, user, tvmaze_stub):
    show = Show.objects.create(tvmaze_id=2, name="Saved Show", tvmaze_url="https://www.tvmaze.com/shows/2")
    CollectionEntry.objects.create(user=user, show=show)
    tvmaze_stub.queue(FakeResponse(200, [{"score": 1, "show": raw_show(1, "Unsaved Show")},
                                         {"score": 1, "show": raw_show(2, "Saved Show")}]))
    html = logged_in.get("/discover/", {"q": "show"}).content.decode()
    saved_card = html[html.index('data-tvmaze-id="2"'):]
    unsaved_card = html[html.index('data-tvmaze-id="1"'):html.index('data-tvmaze-id="2"')]
    assert 'data-saved="1"' in saved_card[:60] and "Plan to Watch" in saved_card
    assert 'name="tvmaze_id" value="1"' in unsaved_card and "Not in your collection" in unsaved_card


def test_other_users_saves_do_not_mark_my_results(logged_in, other_user, tvmaze_stub):
    show = Show.objects.create(tvmaze_id=2, name="Their Show", tvmaze_url="https://www.tvmaze.com/shows/2")
    CollectionEntry.objects.create(user=other_user, show=show)
    tvmaze_stub.queue(FakeResponse(200, [{"score": 1, "show": raw_show(2, "Their Show")}]))
    html = logged_in.get("/discover/", {"q": "their"}).content.decode()
    assert 'data-saved="1"' not in html


def test_poster_fallback_when_show_has_no_backdrop(logged_in, db):
    Show.objects.create(tvmaze_id=3, name="No Backdrop", tvmaze_url="https://www.tvmaze.com/shows/3",
                        image_url="https://static.tvmaze.com/p.jpg", background_url="")
    html = logged_in.get("/shows/3/").content.decode()
    assert "hero--poster" in html and "data-poster-fallback" in html


def test_backdrop_used_when_present(logged_in, db):
    Show.objects.create(tvmaze_id=4, name="Has Backdrop", tvmaze_url="https://www.tvmaze.com/shows/4",
                        image_url="https://static.tvmaze.com/p.jpg", background_url="https://static.tvmaze.com/bg.jpg")
    html = logged_in.get("/shows/4/").content.decode()
    assert "background-image:url('https://static.tvmaze.com/bg.jpg')" in html
    assert "hero--poster" not in html and "data-poster-fallback" not in html
