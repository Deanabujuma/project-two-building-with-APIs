"""Phase 6: My Tracking form, update and delete (AC7 web, AC23 web, AC24, AC25)."""

import datetime

import pytest
from django.utils import timezone

from shows.models import CollectionEntry, Show

VALID_POST = {"status": "watching", "current_season": "2", "current_episode": "9", "rating": "4", "notes": "Loving it."}


@pytest.fixture
def show(db):
    return Show.objects.create(tvmaze_id=44933, name="Severance", tvmaze_url="https://www.tvmaze.com/shows/44933", genres="Drama")


@pytest.fixture
def entry(user, show):
    return CollectionEntry.objects.create(user=user, show=show)


def post(client, entry, **changes):
    return client.post(f"/collection/{entry.pk}/", {**VALID_POST, **changes})


# --- Rendering ---------------------------------------------------------------------------------------

def test_tracking_tab_renders_the_form_with_current_values(logged_in, user, show):
    entry = CollectionEntry.objects.create(user=user, show=show, status="on_hold", current_season=1,
                                           current_episode=3, rating=5, notes="Cliffhanger!")
    html = logged_in.get("/shows/44933/?tab=tracking").content.decode()
    assert f'action="/collection/{entry.pk}/"' in html
    assert '<option value="on_hold" selected>' in html
    assert 'name="current_season" value="1"' in html and 'name="current_episode" value="3"' in html
    assert 'id="rating-5" value="5" checked' in html
    assert "Cliffhanger!" in html
    assert 'title="5 stars"' in html and 'title="1 star"' in html
    assert f'href="/collection/{entry.pk}/delete/"' in html


# --- AC24: valid saves ------------------------------------------------------------------------------

def test_valid_save_updates_entry_and_redirects_with_message(logged_in, entry):
    before = entry.updated_at
    response = post(logged_in, entry)
    assert response.status_code == 302 and response.url == "/shows/44933/?tab=tracking"
    entry.refresh_from_db()
    assert (entry.status, entry.current_season, entry.current_episode, entry.rating, entry.notes) == \
        ("watching", 2, 9, 4, "Loving it.")
    assert entry.updated_at > before
    assert "Saved your tracking for Severance." in logged_in.get(response.url).content.decode()


def test_clearing_progress_and_rating_is_allowed(logged_in, user, show):
    entry = CollectionEntry.objects.create(user=user, show=show, current_season=2, current_episode=1, rating=3)
    post(logged_in, entry, current_season="", current_episode="", rating="", notes="")
    entry.refresh_from_db()
    assert entry.current_season is None and entry.current_episode is None and entry.rating is None


def test_status_never_changes_by_itself(logged_in, entry):
    post(logged_in, entry, status="plan_to_watch", current_season="5", current_episode="10")
    entry.refresh_from_db()
    assert entry.status == "plan_to_watch"


def test_notes_at_the_2000_limit_are_saved(logged_in, entry):
    post(logged_in, entry, notes="x" * 2000)
    entry.refresh_from_db()
    assert len(entry.notes) == 2000


# --- AC23 (web): invalid input is rejected with field errors and kept input --------------------------

@pytest.mark.parametrize("changes, message", [
    ({"current_episode": ""}, "Enter both a season and an episode, or leave both blank."),
    ({"current_season": ""}, "Enter both a season and an episode, or leave both blank."),
    ({"current_season": "0"}, "Season must be a whole number of 1 or more."),
    ({"current_episode": "-2"}, "Episode must be a whole number of 1 or more."),
    ({"current_season": "two"}, "Season must be a whole number of 1 or more."),
    ({"current_episode": "1.5"}, "Episode must be a whole number of 1 or more."),
    ({"rating": "0"}, "Rating must be a whole number from 1 to 5"),
    ({"rating": "6"}, "Rating must be a whole number from 1 to 5"),
    ({"notes": "x" * 2001}, "Notes can be at most 2,000 characters"),
    ({"status": "binge"}, "Select a valid choice"),
])
def test_invalid_input_is_rejected_and_redisplayed(logged_in, entry, changes, message):
    response = post(logged_in, entry, **changes)
    assert response.status_code == 400
    html = response.content.decode()
    assert message in html
    assert 'data-panel="tracking"' in html
    entry.refresh_from_db()
    assert entry.status == "plan_to_watch" and entry.current_season is None and entry.notes == ""


def test_invalid_post_keeps_the_users_input(logged_in, entry):
    html = post(logged_in, entry, current_episode="", notes="Keep this text").content.decode()
    assert "Keep this text" in html
    assert 'name="current_season" value="2"' in html
    assert 'id="rating-4" value="4" checked' in html


def test_invalid_post_does_not_change_the_page_header(logged_in, entry):
    html = post(logged_in, entry, status="completed", current_episode="").content.decode()
    eyebrow = html[html.index("data-eyebrow"):html.index("</div>", html.index("data-eyebrow"))]
    assert "Plan to Watch" in eyebrow and "Completed" not in eyebrow


def test_get_on_update_url_redirects_to_tracking_tab(logged_in, entry):
    response = logged_in.get(f"/collection/{entry.pk}/")
    assert response.status_code == 302 and response.url == "/shows/44933/?tab=tracking"


# --- AC25: delete ----------------------------------------------------------------------------------------

def test_delete_get_shows_confirmation_and_deletes_nothing(logged_in, entry):
    response = logged_in.get(f"/collection/{entry.pk}/delete/")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-state="confirm-delete"' in html and "Remove Severance?" in html
    assert CollectionEntry.objects.filter(pk=entry.pk).exists()


def test_delete_post_removes_only_this_entry(logged_in, entry, show, other_user):
    theirs = CollectionEntry.objects.create(user=other_user, show=show)
    response = logged_in.post(f"/collection/{entry.pk}/delete/")
    assert response.status_code == 302 and response.url == "/collection/"
    assert not CollectionEntry.objects.filter(pk=entry.pk).exists()
    assert CollectionEntry.objects.filter(pk=theirs.pk).exists()
    assert Show.objects.filter(pk=show.pk).exists()
    assert "Removed Severance from your collection." in logged_in.get("/collection/").content.decode()


# --- AC7 (web): other users' entries are invisible -------------------------------------------------------

def test_other_users_entry_returns_404_everywhere(client, other_user, entry):
    client.force_login(other_user)
    assert client.post(f"/collection/{entry.pk}/", VALID_POST).status_code == 404
    assert client.get(f"/collection/{entry.pk}/").status_code == 404
    assert client.get(f"/collection/{entry.pk}/delete/").status_code == 404
    assert client.post(f"/collection/{entry.pk}/delete/").status_code == 404
    entry.refresh_from_db()
    assert entry.status == "plan_to_watch"


def test_other_users_show_page_has_no_tracking_tab_for_me(client, other_user, entry):
    client.force_login(other_user)
    html = client.get("/shows/44933/?tab=tracking").content.decode()
    assert 'data-tab="tracking"' not in html and "Add to my collection" in html


@pytest.mark.parametrize("url", ["/collection/1/", "/collection/1/delete/"])
def test_anonymous_users_are_sent_to_login(client, db, url):
    response = client.post(url)
    assert response.status_code == 302 and response.url.startswith("/accounts/login/")


@pytest.mark.parametrize("changes, message", [
    ({"current_season": "0"}, "Season must be a whole number of 1 or more."),
    ({"current_season": "two"}, "Season must be a whole number of 1 or more."),
    ({"rating": "9"}, "Rating must be a whole number from 1 to 5"),
    ({"current_episode": ""}, "Enter both a season and an episode, or leave both blank."),
])
def test_each_error_message_appears_once(logged_in, entry, changes, message):
    assert post(logged_in, entry, **changes).content.decode().count(message) == 1


def test_rejected_season_does_not_also_claim_episode_is_missing(logged_in, entry):
    html = post(logged_in, entry, current_season="-1", current_episode="4").content.decode()
    assert "Season must be a whole number of 1 or more." in html
    assert "Enter both a season and an episode" not in html
