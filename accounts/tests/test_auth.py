"""Phase 2: accounts, public shell, navigation, footer (AC5, AC5a, AC6, AC26 anonymous, AC50)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

PRIVATE_NAV_LABELS = ["My Collection", "Watching", "Completed", "Discover"]


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="demo_user", password="a-strong-pass-123")


# --- AC5: login required except home, login, sign-up ---------------------------------

@pytest.mark.parametrize("url_name", ["shows:discover", "shows:collection"])
def test_private_pages_redirect_anonymous_users_to_login(client, db, url_name):
    response = client.get(reverse(url_name))
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.parametrize("url_name", ["home", "accounts:login", "accounts:signup"])
def test_public_pages_are_open(client, db, url_name):
    assert client.get(reverse(url_name)).status_code == 200


def test_private_pages_load_when_logged_in(client, user):
    client.force_login(user)
    for url_name in ["shows:discover", "shows:collection"]:
        assert client.get(reverse(url_name)).status_code == 200


# --- AC5a: two versions of the navigation ----------------------------------------------

@pytest.mark.parametrize("url_name", ["home", "accounts:login", "accounts:signup"])
def test_anonymous_nav_shows_only_login_and_signup(client, db, url_name):
    html = client.get(reverse(url_name)).content.decode()
    nav = html[html.index("<header"):html.index("</header>")]
    assert 'data-nav="public"' in nav
    assert "Log in" in nav and "Sign up" in nav
    for label in PRIVATE_NAV_LABELS:
        assert label not in nav
    assert "Log out" not in nav and "demo_user" not in nav


def test_logged_in_nav_shows_username_and_all_links(client, user):
    client.force_login(user)
    html = client.get(reverse("home")).content.decode()
    nav = html[html.index("<header"):html.index("</header>")]
    assert 'data-nav="private"' in nav
    assert "demo_user" in nav and "Log out" in nav
    for label in ["Home", *PRIVATE_NAV_LABELS]:
        assert label in nav
    assert "Sign up" not in nav and ">Log in<" not in nav


@pytest.mark.parametrize(
    "url, active_label",
    [("/", "Home"), ("/discover/", "Discover"), ("/collection/", "My Collection"),
     ("/collection/?status=watching", "Watching"), ("/collection/?status=completed", "Completed")],
)
def test_nav_highlights_the_current_page(client, user, url, active_label):
    client.force_login(user)
    html = client.get(url).content.decode()
    active = html[html.index('aria-current="page"'):]
    assert active_label in active[: active.index("</a>")]
    assert html.count('aria-current="page"') == 1


# --- AC6: sign-up, login, logout ------------------------------------------------------------

def test_signup_creates_user_and_logs_them_in(client, db):
    response = client.post(reverse("accounts:signup"), {
        "username": "new_viewer", "password1": "a-strong-pass-123", "password2": "a-strong-pass-123",
    })
    assert response.status_code == 302 and response.url == reverse("home")
    assert get_user_model().objects.filter(username="new_viewer").exists()
    assert "_auth_user_id" in client.session


def test_signup_rejects_mismatched_passwords(client, db):
    response = client.post(reverse("accounts:signup"), {
        "username": "new_viewer", "password1": "a-strong-pass-123", "password2": "different-pass-456",
    })
    assert response.status_code == 200
    assert not get_user_model().objects.filter(username="new_viewer").exists()


def test_login_with_valid_credentials(client, user):
    response = client.post(reverse("accounts:login"), {"username": "demo_user", "password": "a-strong-pass-123"})
    assert response.status_code == 302
    assert "_auth_user_id" in client.session


def test_login_redirects_back_to_requested_page(client, user):
    response = client.post(
        reverse("accounts:login") + "?next=/collection/",
        {"username": "demo_user", "password": "a-strong-pass-123", "next": "/collection/"},
    )
    assert response.url == "/collection/"


def test_login_with_wrong_password_shows_error(client, user):
    response = client.post(reverse("accounts:login"), {"username": "demo_user", "password": "wrong"})
    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_logout_requires_post_and_ends_session(client, user):
    client.force_login(user)
    assert client.get(reverse("accounts:logout")).status_code == 405
    response = client.post(reverse("accounts:logout"))
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session


# --- AC26 (anonymous part) and AC50 (footer) ----------------------------------------------

def test_anonymous_home_offers_signup_and_login_not_discover(client, db):
    html = client.get(reverse("home")).content.decode()
    main = html[html.index("<main>"):html.index("</main>")]
    assert 'data-hero="welcome-public"' in main
    assert reverse("accounts:signup") in main and reverse("accounts:login") in main
    assert reverse("shows:discover") not in main


def test_logged_in_home_with_empty_collection_offers_discover(client, user):
    client.force_login(user)
    html = client.get(reverse("home")).content.decode()
    main = html[html.index("<main>"):html.index("</main>")]
    assert 'data-hero="welcome-empty"' in main
    assert reverse("shows:discover") in main


@pytest.mark.parametrize("url_name", ["home", "accounts:login", "accounts:signup"])
def test_every_page_credits_tvmaze_license(client, db, url_name):
    html = client.get(reverse(url_name)).content.decode()
    assert "https://www.tvmaze.com" in html
    assert "https://creativecommons.org/licenses/by-sa/4.0/" in html
