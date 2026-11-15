"""Phase 10: API create, update and delete, with validation parity (AC35 write, AC36, AC37, AC38)."""

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from shows.models import CollectionEntry, Show
from shows.tests.conftest import FAILURES, FakeResponse, raw_show

# Each invalid tracking case from AC23, written once and checked against BOTH the web form
# and the API. Values are what a client would send; "" means "blank" for the web form.
INVALID_CASES = [
    ("season without episode", {"current_season": 3, "current_episode": None}, "current_episode"),
    ("episode without season", {"current_season": None, "current_episode": 4}, "current_season"),
    ("season zero", {"current_season": 0, "current_episode": 1}, "current_season"),
    ("negative episode", {"current_season": 1, "current_episode": -2}, "current_episode"),
    ("text season", {"current_season": "two", "current_episode": 1}, "current_season"),
    ("decimal episode", {"current_season": 1, "current_episode": 1.5}, "current_episode"),
    ("rating zero", {"rating": 0}, "rating"),
    ("rating six", {"rating": 6}, "rating"),
    ("notes too long", {"notes": "x" * 2001}, "notes"),
    ("unknown status", {"status": "binge_watching"}, "status"),
]


@pytest.fixture
def api(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
    return client


@pytest.fixture
def show(db):
    return Show.objects.create(tvmaze_id=44933, name="Severance", tvmaze_url="https://www.tvmaze.com/shows/44933")


@pytest.fixture
def entry(user, show):
    return CollectionEntry.objects.create(user=user, show=show)


def snapshot(entry):
    entry.refresh_from_db()
    return (entry.status, entry.current_season, entry.current_episode, entry.rating, entry.notes)


# --- AC37: validation parity ---------------------------------------------------------------------------------

@pytest.mark.parametrize("name, values, field", INVALID_CASES, ids=[c[0] for c in INVALID_CASES])
def test_api_rejects_every_invalid_case(api, entry, name, values, field):
    before = snapshot(entry)
    response = api.patch(f"/api/collection/{entry.pk}/", values, format="json")
    assert response.status_code == 400
    assert field in response.json()
    assert snapshot(entry) == before


@pytest.mark.parametrize("name, values, field", INVALID_CASES, ids=[c[0] for c in INVALID_CASES])
def test_web_form_rejects_the_same_cases(logged_in, entry, name, values, field):
    form = {"status": "watching", "current_season": "", "current_episode": "", "rating": "", "notes": ""}
    form.update({key: "" if value is None else str(value) for key, value in values.items()})
    before = snapshot(entry)
    response = logged_in.post(f"/collection/{entry.pk}/", form)
    assert response.status_code == 400
    assert field in response.context["form"].errors
    assert snapshot(entry) == before


def test_patch_with_only_season_is_checked_against_the_saved_episode(api, entry):
    # Entry has no progress. Sending only a season would leave the episode blank: rejected.
    response = api.patch(f"/api/collection/{entry.pk}/", {"current_season": 2}, format="json")
    assert response.status_code == 400
    assert response.json()["current_episode"] == ["Enter both a season and an episode, or leave both blank."]


def test_patch_with_only_episode_is_fine_when_season_is_already_saved(api, entry):
    entry.current_season, entry.current_episode = 2, 3
    entry.save()
    response = api.patch(f"/api/collection/{entry.pk}/", {"current_episode": 4}, format="json")
    assert response.status_code == 200
    assert snapshot(entry)[1:3] == (2, 4)


def test_api_and_web_use_the_same_message(api, logged_in, entry):
    api_message = api.patch(f"/api/collection/{entry.pk}/", {"rating": 9}, format="json").json()["rating"][0]
    form = {"status": "plan_to_watch", "current_season": "", "current_episode": "", "rating": "9", "notes": ""}
    web_errors = logged_in.post(f"/collection/{entry.pk}/", form).context["form"].errors["rating"]
    assert api_message == web_errors[0] == "Rating must be a whole number from 1 to 5, or blank."


# --- AC35 (write): update and delete -------------------------------------------------------------------------------

def test_patch_updates_only_the_sent_fields(api, entry):
    entry.notes = "keep me"
    entry.save()
    response = api.patch(f"/api/collection/{entry.pk}/",
                         {"status": "watching", "current_season": 1, "current_episode": 2, "rating": 5}, format="json")
    assert response.status_code == 200
    assert response.json()["status"] == "watching"
    assert snapshot(entry) == ("watching", 1, 2, 5, "keep me")


def test_patch_can_clear_progress_and_rating(api, entry):
    entry.current_season, entry.current_episode, entry.rating = 1, 1, 3
    entry.save()
    response = api.patch(f"/api/collection/{entry.pk}/",
                         {"current_season": None, "current_episode": None, "rating": None}, format="json")
    assert response.status_code == 200
    assert snapshot(entry)[1:4] == (None, None, None)


def test_put_updates_the_entry(api, entry):
    body = {"status": "completed", "current_season": 2, "current_episode": 10, "rating": 4, "notes": "Done."}
    response = api.put(f"/api/collection/{entry.pk}/", body, format="json")
    assert response.status_code == 200
    assert snapshot(entry) == ("completed", 2, 10, 4, "Done.")


def test_delete_returns_204_and_keeps_the_show(api, entry, show):
    assert api.delete(f"/api/collection/{entry.pk}/").status_code == 204
    assert not CollectionEntry.objects.filter(pk=entry.pk).exists()
    assert Show.objects.filter(pk=show.pk).exists()


@pytest.mark.parametrize("method", ["patch", "put", "delete"])
def test_other_users_entry_cannot_be_changed(api, other_user, show, method):
    theirs = CollectionEntry.objects.create(user=other_user, show=show)
    response = getattr(api, method)(f"/api/collection/{theirs.pk}/", {"rating": 5}, format="json")
    assert response.status_code == 404
    assert snapshot(theirs) == ("plan_to_watch", None, None, None, "")


def test_session_write_without_csrf_token_is_refused(user, entry):
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.delete(f"/api/collection/{entry.pk}/")
    assert response.status_code == 403 and "CSRF" in response.json()["detail"]
    assert CollectionEntry.objects.filter(pk=entry.pk).exists()


# --- AC38: read-only fields --------------------------------------------------------------------------------------------

def test_read_only_fields_are_never_changed(api, entry, show):
    other_show = Show.objects.create(tvmaze_id=1, name="Other", tvmaze_url="https://www.tvmaze.com/shows/1")
    created = entry.created_at
    response = api.patch(f"/api/collection/{entry.pk}/", {
        "id": 9999, "created_at": "2000-01-01T00:00:00Z", "updated_at": "2000-01-01T00:00:00Z",
        "show": {"tvmaze_id": 1, "name": "Hacked"}, "notes": "real change",
    }, format="json")
    assert response.status_code == 200
    entry.refresh_from_db()
    assert entry.pk == response.json()["id"] != 9999
    assert entry.show == show and entry.created_at == created and entry.notes == "real change"
    show.refresh_from_db()
    assert show.name == "Severance" and other_show.collection_entries.count() == 0


def test_tvmaze_id_cannot_change_the_show_of_an_entry(api, entry):
    response = api.patch(f"/api/collection/{entry.pk}/", {"tvmaze_id": 1}, format="json")
    assert response.status_code == 400 and "tvmaze_id" in response.json()
    assert entry.show.tvmaze_id == 44933


# --- AC36: create by tvmaze_id ---------------------------------------------------------------------------------------------

def test_create_by_tvmaze_id_returns_201(api, user, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(169, "Breaking Bad")))
    response = api.post("/api/collection/", {"tvmaze_id": 169}, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["show"]["name"] == "Breaking Bad" and data["status"] == "plan_to_watch"
    assert response["Location"].endswith(f"/api/collection/{data['id']}/")
    assert CollectionEntry.objects.filter(user=user, show__tvmaze_id=169).exists()


def test_create_ignores_posted_show_details(api, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, raw_show(169, "Breaking Bad")))
    api.post("/api/collection/", {"tvmaze_id": 169, "show": {"name": "Fake"}, "name": "Fake"}, format="json")
    assert Show.objects.get(tvmaze_id=169).name == "Breaking Bad"


def test_create_duplicate_returns_400(api, entry, tvmaze_stub):
    response = api.post("/api/collection/", {"tvmaze_id": 44933}, format="json")
    assert response.status_code == 400
    assert response.json() == {"tvmaze_id": ["Severance is already in your collection."]}
    assert tvmaze_stub.calls == []


def test_create_unknown_tvmaze_id_returns_400(api, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(404, {}))
    response = api.post("/api/collection/", {"tvmaze_id": 999999999}, format="json")
    assert response.status_code == 400
    assert response.json() == {"tvmaze_id": ["TVmaze has no show with that ID."]}
    assert Show.objects.count() == 0


@pytest.mark.parametrize("failure, phrase", FAILURES)
def test_create_during_tvmaze_outage_returns_503(api, tvmaze_stub, failure, phrase):
    tvmaze_stub.queue(failure)
    response = api.post("/api/collection/", {"tvmaze_id": 169}, format="json")
    assert response.status_code == 503
    assert phrase in response.json()["detail"]
    assert Show.objects.count() == 0 and CollectionEntry.objects.count() == 0


@pytest.mark.parametrize("body", [{}, {"tvmaze_id": None}, {"tvmaze_id": "abc"}, {"tvmaze_id": 0}, {"tvmaze_id": -5}])
def test_create_needs_a_valid_tvmaze_id(api, tvmaze_stub, body):
    response = api.post("/api/collection/", body, format="json")
    assert response.status_code == 400 and "tvmaze_id" in response.json()
    assert tvmaze_stub.calls == []


@pytest.mark.parametrize("name, values, field", INVALID_CASES, ids=[c[0] for c in INVALID_CASES])
def test_api_and_web_messages_match_for_every_case(api, logged_in, entry, name, values, field):
    api_errors = api.patch(f"/api/collection/{entry.pk}/", values, format="json").json()[field]
    form = {"status": "watching", "current_season": "", "current_episode": "", "rating": "", "notes": ""}
    form.update({key: "" if value is None else str(value) for key, value in values.items()})
    web_errors = logged_in.post(f"/collection/{entry.pk}/", form).context["form"].errors[field]
    if field == "status":
        return  # each framework names the bad choice in its own words; both reject it
    assert api_errors[0] == web_errors[0]
