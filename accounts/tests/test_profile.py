"""Post-submission Phase B: Profile & Settings, password change, preferences, Delete Account."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from shows.models import CollectionEntry, Show

User = get_user_model()
PASSWORD = "a-strong-pass-123"
WARNING = "Are you sure you want to permanently delete your account? This action cannot be undone."
PROFILE = reverse("accounts:profile")
DELETE = reverse("accounts:delete")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="demo_user", password=PASSWORD)


@pytest.fixture
def other(db):
    return User.objects.create_user(username="other_user", password="a-strong-pass-456")


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


def make_show(tvmaze_id, name):
    return Show.objects.create(tvmaze_id=tvmaze_id, name=name, tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}",
                               genres=["Drama"])


@pytest.fixture
def data(user, other):
    """Both users save the same shared show; each also has one of their own."""
    shared, mine, theirs = make_show(1, "Shared Show"), make_show(2, "Only Mine"), make_show(3, "Only Theirs")
    CollectionEntry.objects.create(user=user, show=shared, status="watching", rating=3, notes="my note")
    CollectionEntry.objects.create(user=user, show=mine, status="completed")
    CollectionEntry.objects.create(user=other, show=shared, status="plan_to_watch", notes="their note")
    CollectionEntry.objects.create(user=other, show=theirs, status="watching")
    return {"shared": shared, "mine": mine, "theirs": theirs}


def post_delete(client, password=PASSWORD, confirm="DELETE"):
    return client.post(DELETE, {"password": password, "confirm": confirm})


# --- Navigation and access -------------------------------------------------------------

def test_nav_username_and_avatar_link_to_profile(logged_in):
    html = logged_in.get(reverse("home")).content.decode()
    assert f'class="profile ' in html and f'href="{PROFILE}"' in html


@pytest.mark.parametrize("url", [PROFILE, DELETE])
def test_anonymous_users_are_sent_to_login(client, db, url):
    for response in (client.get(url), client.post(url, {"password": "x", "confirm": "DELETE"})):
        assert response.status_code == 302 and response.url.startswith(reverse("accounts:login"))


def test_profile_page_shows_every_section_with_danger_zone_last(logged_in, data):
    response = logged_in.get(PROFILE)
    html = response.content.decode()
    assert response.status_code == 200
    panels = ["account", "shortcuts", "username", "password", "preferences", "session", "danger"]
    positions = [html.index(f'data-panel="{name}"') for name in panels]
    assert positions == sorted(positions)
    assert "demo_user" in html and "Shows saved</dt><dd>2" in html
    assert reverse("shows:collection") in html and reverse("accounts:logout") in html and DELETE in html
    assert "Delete Account" in html
    assert "autofocus" not in html  # opening settings must not jump to the password box


def test_anonymous_profile_post_changes_nothing(client, user):
    client.post(PROFILE, {"form": "username", "username-username": "hijacked"})
    user.refresh_from_db()
    assert user.username == "demo_user"


# --- Username --------------------------------------------------------------------------

def test_username_can_be_changed(logged_in, user):
    response = logged_in.post(PROFILE, {"form": "username", "username-username": "new_name"}, follow=True)
    user.refresh_from_db()
    assert user.username == "new_name"
    assert "Your username is now new_name." in response.content.decode()


@pytest.mark.parametrize("taken", ["other_user", "OTHER_USER"])
def test_username_must_be_unique_ignoring_case(logged_in, user, other, taken):
    response = logged_in.post(PROFILE, {"form": "username", "username-username": taken})
    user.refresh_from_db()
    assert response.status_code == 400 and user.username == "demo_user"
    assert "That username is already taken." in response.content.decode()


def test_invalid_username_is_rejected_and_page_still_shows_the_old_name(logged_in, user):
    response = logged_in.post(PROFILE, {"form": "username", "username-username": "bad name!"})
    user.refresh_from_db()
    assert response.status_code == 400 and user.username == "demo_user"
    assert '<h1 class="page-title mb-0" data-username>demo_user</h1>' in response.content.decode()


def test_unknown_form_name_just_redirects(logged_in, user):
    response = logged_in.post(PROFILE, {"form": "is_superuser", "is_superuser": "on"})
    user.refresh_from_db()
    assert response.status_code == 302 and not user.is_superuser


# --- Password --------------------------------------------------------------------------

def password_post(old=PASSWORD, new="brand-new-pass-789", again=None):
    return {"form": "password", "password-old_password": old, "password-new_password1": new,
            "password-new_password2": new if again is None else again}


def test_password_change_keeps_session_and_revokes_api_token(logged_in, user):
    token = Token.objects.create(user=user)
    response = logged_in.post(PROFILE, password_post(), follow=True)
    user.refresh_from_db()
    assert user.check_password("brand-new-pass-789")
    assert "Your password was changed. Your API token was revoked" in response.content.decode()
    assert logged_in.get(reverse("shows:collection")).status_code == 200  # still logged in
    assert not Token.objects.filter(user=user).exists()
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    assert api.get("/api/collection/").status_code == 401


@pytest.mark.parametrize("post, message", [
    (password_post(old="wrong-old-pass"), "Your old password was entered incorrectly"),
    (password_post(again="does-not-match-1"), "The two password fields"),
    (password_post(new="short"), "too short"),
])
def test_bad_password_changes_are_rejected(logged_in, user, post, message):
    token = Token.objects.create(user=user)
    response = logged_in.post(PROFILE, post)
    user.refresh_from_db()
    assert response.status_code == 400 and message in response.content.decode()
    assert user.check_password(PASSWORD) and Token.objects.filter(key=token.key).exists()


def test_other_sessions_are_logged_out_after_a_password_change(logged_in, user):
    second = Client()
    second.force_login(user)
    logged_in.post(PROFILE, password_post())
    assert second.get(reverse("shows:collection")).status_code == 302


# --- Preferences -----------------------------------------------------------------------

def test_new_users_get_the_default_preferences(user):
    assert user.schedule_country == "US" and user.default_collection_sort == "-updated"


def test_preferences_are_saved(logged_in, user):
    logged_in.post(PROFILE, {"form": "preferences", "preferences-schedule_country": "GB",
                             "preferences-default_collection_sort": "title"})
    user.refresh_from_db()
    assert (user.schedule_country, user.default_collection_sort) == ("GB", "title")


def test_invalid_preferences_are_rejected(logged_in, user):
    response = logged_in.post(PROFILE, {"form": "preferences", "preferences-schedule_country": "XX",
                                        "preferences-default_collection_sort": "-pk"})
    user.refresh_from_db()
    assert response.status_code == 400 and user.schedule_country == "US"


def collection_titles(client, query=""):
    html = client.get(reverse("shows:collection") + query).content.decode()
    names = ["Shared Show", "Only Mine"]
    return sorted(names, key=html.index)


def test_default_collection_sort_is_used_when_no_sort_is_chosen(logged_in, user, data):
    CollectionEntry.objects.filter(user=user, show__name="Shared Show").update(rating=5)
    user.default_collection_sort = "title"
    user.save()
    assert collection_titles(logged_in) == ["Only Mine", "Shared Show"]
    assert collection_titles(logged_in, "?sort=-rating") == ["Shared Show", "Only Mine"]  # an explicit choice wins


def test_schedule_country_preference_drives_discover(logged_in, user, monkeypatch):
    seen = []
    monkeypatch.setattr("shows.browse.week_schedule", lambda country, today=None: (seen.append(country), ([], None))[1])
    user.schedule_country = "CA"
    user.save()
    logged_in.get(reverse("shows:discover_browse") + "?partial=1")
    assert seen == ["CA"]


# --- Delete Account --------------------------------------------------------------------

def test_profile_delete_link_opens_a_confirmation_page_and_deletes_nothing(logged_in, user, data):
    response = logged_in.get(DELETE)
    html = response.content.decode()
    assert response.status_code == 200 and WARNING in html
    for word in ("collection", "rating", "note", "progress"):
        assert word in html
    assert 'name="password"' in html and 'name="confirm"' in html
    assert "data-delete-button disabled" in html and "csrfmiddlewaretoken" in html
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.parametrize("password, confirm, message", [
    ("wrong-password", "DELETE", "That password is incorrect."),
    ("", "DELETE", "This field is required."),
    (PASSWORD, "", "This field is required."),
    (PASSWORD, "delete", "Type DELETE exactly"),
    (PASSWORD, " DELETE ", None),  # surrounding spaces are ignored (server strips, page script trims)
])
def test_delete_requires_the_right_password_and_the_word_delete(logged_in, user, data, password, confirm, message):
    response = post_delete(logged_in, password, confirm)
    if message is None:
        assert not User.objects.filter(pk=user.pk).exists()
        return
    assert response.status_code == 400 and message in response.content.decode()
    assert User.objects.filter(pk=user.pk).exists()
    assert CollectionEntry.objects.filter(user=user).count() == 2


def test_get_never_deletes(logged_in, user):
    logged_in.get(DELETE + "?password=a-strong-pass-123&confirm=DELETE")
    assert User.objects.filter(pk=user.pk).exists()


def test_delete_without_csrf_token_is_refused(user):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    response = post_delete(client)
    assert response.status_code == 403
    assert User.objects.filter(pk=user.pk).exists()


def test_successful_delete_removes_only_this_users_data(logged_in, user, other, data):
    token = Token.objects.create(user=user)
    other_token = Token.objects.create(user=other)
    response = post_delete(logged_in, PASSWORD, "DELETE")
    assert response.status_code == 302 and response.url == reverse("home")

    assert not User.objects.filter(pk=user.pk).exists()
    assert not CollectionEntry.objects.filter(user_id=user.pk).exists()
    assert not Token.objects.filter(key=token.key).exists()
    # Shared Show rows and the other user's account, entries and token are untouched.
    assert Show.objects.count() == 3
    assert User.objects.filter(pk=other.pk).exists()
    assert sorted(CollectionEntry.objects.filter(user=other).values_list("notes", flat=True)) == ["", "their note"]
    assert Token.objects.filter(key=other_token.key).exists()


def test_after_delete_the_user_is_logged_out_and_sees_a_message(logged_in, user, data):
    response = logged_in.post(DELETE, {"password": PASSWORD, "confirm": "DELETE"}, follow=True)
    html = response.content.decode()
    assert response.redirect_chain[-1][0] == reverse("home")
    assert "Your account has been permanently deleted." in html
    assert "_auth_user_id" not in logged_in.session
    assert logged_in.get(reverse("shows:collection")).status_code == 302


def test_deleted_user_cannot_log_in_or_use_the_api(client, user, data):
    token = Token.objects.create(user=user)
    client.force_login(user)
    post_delete(client)
    assert not Client().login(username="demo_user", password=PASSWORD)
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    assert api.get("/api/collection/").status_code == 401


def test_a_user_cannot_delete_someone_else(logged_in, user, other):
    # The form only ever deletes request.user; another user's password does not help.
    response = post_delete(logged_in, "a-strong-pass-456", "DELETE")
    assert response.status_code == 400
    assert User.objects.filter(pk=other.pk).exists() and User.objects.filter(pk=user.pk).exists()
