"""Phase 9: API authentication, token endpoint and read access (AC33, AC34, AC35 read, AC7 API)."""

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from shows.models import CollectionEntry, Show


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def token(user):
    return Token.objects.create(user=user)


@pytest.fixture
def token_api(api, token):
    api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api


def add(user, tvmaze_id, name, **fields):
    show, _ = Show.objects.get_or_create(
        tvmaze_id=tvmaze_id,
        defaults={"name": name, "tvmaze_url": f"https://www.tvmaze.com/shows/{tvmaze_id}", "network": "Apple TV",
                  "channel_type": "web channel", "genres": "Drama", "tvmaze_rating": "7.7"},
    )
    return CollectionEntry.objects.create(user=user, show=show, **fields)


# --- AC33: authentication required -----------------------------------------------------------------------

@pytest.mark.parametrize("url", ["/api/", "/api/collection/", "/api/collection/1/"])
def test_anonymous_requests_are_rejected(api, db, url):
    assert api.get(url).status_code in (401, 403)


def test_anonymous_gets_401_with_token_challenge(api, db):
    response = api.get("/api/collection/")
    assert response.status_code == 401
    assert response["WWW-Authenticate"] == "Token"


def test_bad_token_is_rejected(api, db):
    api.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")
    assert api.get("/api/collection/").status_code == 401


@pytest.mark.parametrize("url", ["/api/", "/api/collection/"])
def test_valid_token_succeeds(token_api, url):
    assert token_api.get(url).status_code == 200


def test_logged_in_session_succeeds(api, user):
    api.force_login(user)
    assert api.get("/api/collection/").status_code == 200


def test_session_writes_need_csrf_but_token_writes_do_not(user, token):
    # SessionAuthentication enforces CSRF for unsafe methods; tokens are exempt.
    entry = add(user, 1, "Show")
    session_client = APIClient(enforce_csrf_checks=True)
    session_client.force_login(user)
    assert session_client.delete(f"/api/collection/{entry.pk}/").status_code in (403, 405)


# --- AC34: token endpoint ---------------------------------------------------------------------------------

def test_token_endpoint_returns_the_users_token(api, user):
    response = api.post("/api/auth/token/", {"username": "demo_user", "password": "a-strong-pass-123"}, format="json")
    assert response.status_code == 200
    assert response.json()["token"] == Token.objects.get(user=user).key


def test_token_endpoint_returns_the_same_token_each_time(api, user):
    first = api.post("/api/auth/token/", {"username": "demo_user", "password": "a-strong-pass-123"}).json()["token"]
    second = api.post("/api/auth/token/", {"username": "demo_user", "password": "a-strong-pass-123"}).json()["token"]
    assert first == second


@pytest.mark.parametrize("credentials", [{"username": "demo_user", "password": "wrong"},
                                         {"username": "nobody", "password": "x"}, {}])
def test_token_endpoint_rejects_bad_credentials(api, user, credentials):
    response = api.post("/api/auth/token/", credentials, format="json")
    assert response.status_code == 400
    assert "token" not in response.json()


# --- AC35 (read) and AC7 (API) ------------------------------------------------------------------------------

def test_list_returns_only_my_entries_with_nested_show(token_api, user, other_user):
    mine = add(user, 44933, "Severance", status="watching", current_season=2, current_episode=3, rating=4, notes="Wow")
    add(other_user, 44933, "Severance")
    add(other_user, 2, "Their Show")
    data = token_api.get("/api/collection/").json()
    assert data["count"] == 1 and data["previous"] is None and data["next"] is None
    item = data["results"][0]
    assert item["id"] == mine.pk
    assert (item["status"], item["current_season"], item["current_episode"], item["rating"], item["notes"]) == \
        ("watching", 2, 3, 4, "Wow")
    assert item["show"]["tvmaze_id"] == 44933 and item["show"]["name"] == "Severance"
    assert set(item) == {"id", "show", "status", "current_season", "current_episode", "rating", "notes",
                         "created_at", "updated_at"}


def test_nested_show_includes_channel_fields(token_api, user):
    add(user, 44933, "Severance")
    show = token_api.get("/api/collection/").json()["results"][0]["show"]
    assert (show["network"], show["channel_type"], show["channel_country"]) == ("Apple TV", "web channel", "")
    assert show["tvmaze_rating"] == "7.7"
    for field in ["tvmaze_url", "premiered", "ended", "show_status", "genres", "runtime", "language", "show_type", "summary"]:
        assert field in show


def test_retrieve_my_entry(token_api, user):
    entry = add(user, 1, "Show")
    response = token_api.get(f"/api/collection/{entry.pk}/")
    assert response.status_code == 200 and response.json()["id"] == entry.pk


def test_another_users_entry_is_404(token_api, other_user):
    theirs = add(other_user, 1, "Theirs")
    assert token_api.get(f"/api/collection/{theirs.pk}/").status_code == 404


def test_missing_entry_is_404(token_api):
    assert token_api.get("/api/collection/999999/").status_code == 404


def test_api_root_lists_the_collection_endpoint(token_api):
    assert token_api.get("/api/").json() == {"collection": "http://testserver/api/collection/"}
