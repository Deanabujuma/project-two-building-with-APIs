"""Phase 11: API search, filters, ordering and pagination (AC39–AC43, AC52 API half)."""

import datetime
import re
from decimal import Decimal

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from shows.models import CollectionEntry, Show


@pytest.fixture
def api(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
    return client


def add(user, tvmaze_id, name, genres="Drama", show_status="Running", network="HBO", tvmaze_rating=None,
        premiered=None, **entry_fields):
    show, _ = Show.objects.get_or_create(tvmaze_id=tvmaze_id, defaults=dict(
        name=name, tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}", genres=genres, show_status=show_status,
        network=network, tvmaze_rating=tvmaze_rating, premiered=premiered))
    return CollectionEntry.objects.create(user=user, show=show, **entry_fields)


@pytest.fixture
def library(user, other_user):
    add(user, 1, "Severance", "Drama, Science-Fiction, Mystery", "Running", "Apple TV", Decimal("8.4"),
        datetime.date(2022, 2, 18), status="watching", rating=5, notes="The goats scene!")
    add(user, 2, "The Office", "Comedy", "Ended", "NBC", Decimal("8.5"), datetime.date(2005, 3, 24),
        status="completed", rating=4)
    add(user, 3, "Abbott Elementary", "Comedy", "Running", "ABC", Decimal("6.3"), datetime.date(2021, 12, 7),
        status="plan_to_watch")
    add(user, 4, "Dark", "Drama, Science-Fiction, Supernatural", "Ended", "Netflix", None, datetime.date(2017, 12, 1),
        status="watching", rating=3)
    add(user, 5, "Chernobyl", "Drama, History", "Ended", "HBO", Decimal("9.0"), None, status="dropped")
    add(other_user, 1, "Severance", status="watching", rating=1, notes="goats")


def names(response):
    assert response.status_code == 200, response.content
    return [item["show"]["name"] for item in response.json()["results"]]


# --- AC39 / AC52: search and filters -------------------------------------------------------------------------

def test_search_matches_show_name(api, library):
    assert names(api.get("/api/collection/?search=office")) == ["The Office"]


def test_search_matches_notes_unlike_the_web_page(api, library):
    assert names(api.get("/api/collection/?search=goats")) == ["Severance"]


@pytest.mark.parametrize("query, expected", [
    ("status=watching", {"Severance", "Dark"}),
    ("min_rating=4", {"Severance", "The Office"}),
    ("min_rating=1", {"Severance", "The Office", "Dark"}),
    ("genre=science", {"Severance", "Dark"}),
    ("genre=COMEDY", {"The Office", "Abbott Elementary"}),
    ("show_status=ended", {"The Office", "Dark", "Chernobyl"}),
    ("show_status=Running", {"Severance", "Abbott Elementary"}),
    ("network=hb", {"Chernobyl"}),
    ("network=apple", {"Severance"}),
])
def test_each_filter_alone(api, library, query, expected):
    assert set(names(api.get(f"/api/collection/?{query}"))) == expected


@pytest.mark.parametrize("query, expected", [
    ("status=watching&genre=drama&min_rating=4", {"Severance"}),
    ("show_status=ended&genre=comedy", {"The Office"}),
    ("search=dar&status=watching&network=netflix", {"Dark"}),
    ("search=e&status=watching", {"Severance"}),
    ("status=completed&min_rating=5", set()),
])
def test_filters_combine(api, library, query, expected):
    assert set(names(api.get(f"/api/collection/?{query}"))) == expected


# --- AC40: strict filters ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("query, field", [
    ("status=banana", "status"),
    ("min_rating=9", "min_rating"),
    ("min_rating=0", "min_rating"),
    ("min_rating=abc", "min_rating"),
    ("min_rating=2.5", "min_rating"),
    ("ordering=notes", "ordering"),
    ("ordering=-user__password", "ordering"),
])
def test_invalid_filter_values_return_400(api, library, query, field):
    response = api.get(f"/api/collection/?{query}")
    assert response.status_code == 400
    assert field in response.json()


# --- AC41: ordering ------------------------------------------------------------------------------------------------

def test_default_order_is_most_recently_updated(api, library, user):
    dark = CollectionEntry.objects.get(user=user, show__name="Dark")
    dark.notes = "touched"
    dark.save()
    assert names(api.get("/api/collection/"))[0] == "Dark"


@pytest.mark.parametrize("ordering, expected", [
    ("rating", ["Dark", "The Office", "Severance", "Abbott Elementary", "Chernobyl"]),
    ("-rating", ["Severance", "The Office", "Dark", "Abbott Elementary", "Chernobyl"]),
    ("show__name", ["Abbott Elementary", "Chernobyl", "Dark", "Severance", "The Office"]),
    ("-show__name", ["The Office", "Severance", "Dark", "Chernobyl", "Abbott Elementary"]),
    ("show__tvmaze_rating", ["Abbott Elementary", "Severance", "The Office", "Chernobyl", "Dark"]),
    ("-show__tvmaze_rating", ["Chernobyl", "The Office", "Severance", "Abbott Elementary", "Dark"]),
    ("show__premiered", ["The Office", "Dark", "Abbott Elementary", "Severance", "Chernobyl"]),
    ("-show__premiered", ["Severance", "Abbott Elementary", "Dark", "The Office", "Chernobyl"]),
    ("created_at", ["Severance", "The Office", "Abbott Elementary", "Dark", "Chernobyl"]),
    ("-created_at", ["Chernobyl", "Dark", "Abbott Elementary", "The Office", "Severance"]),
])
def test_every_ordering_field_in_both_directions(api, library, ordering, expected):
    assert names(api.get(f"/api/collection/?ordering={ordering}")) == expected


def test_updated_at_ascending(api, library, user):
    first = CollectionEntry.objects.get(user=user, show__name="Severance")
    first.notes = "now newest"
    first.save()
    assert names(api.get("/api/collection/?ordering=updated_at"))[-1] == "Severance"
    assert names(api.get("/api/collection/?ordering=-updated_at"))[0] == "Severance"


# --- AC42: pagination ------------------------------------------------------------------------------------------------

@pytest.fixture
def sixty(user):
    for i in range(1, 61):
        add(user, 1000 + i, f"Show {i:02d}")


def test_default_page_size_is_12(api, sixty):
    data = api.get("/api/collection/").json()
    assert data["count"] == 60 and len(data["results"]) == 12
    assert data["previous"] is None and "page=2" in data["next"]


def test_page_size_parameter(api, sixty):
    data = api.get("/api/collection/?page_size=25&page=2").json()
    assert len(data["results"]) == 25
    assert data["previous"] is not None and "page_size=25" in data["previous"]
    assert "page=3" in data["next"] and "page_size=25" in data["next"]


def test_page_size_is_capped_at_50(api, sixty):
    data = api.get("/api/collection/?page_size=500").json()
    assert len(data["results"]) == 50


def test_last_page_has_no_next(api, sixty):
    data = api.get("/api/collection/?page=5").json()
    assert len(data["results"]) == 12 and data["next"] is None


def test_page_out_of_range_is_404(api, sixty):
    assert api.get("/api/collection/?page=99").status_code == 404


# --- AC43: same results as the web collection page ---------------------------------------------------------------

def web_names(client, query):
    html = client.get(f"/collection/?{query}").content.decode()
    return re.findall(r'<div class="cap-t clamp-1">([^<]+)</div>', html)


@pytest.mark.parametrize("status", ["", "watching", "completed", "plan_to_watch"])
@pytest.mark.parametrize("web_sort, api_ordering", [("-updated", "-updated_at"), ("title", "show__name"),
                                                    ("-rating", "-rating")])
def test_web_and_api_return_the_same_order(api, logged_in, library, status, web_sort, api_ordering):
    api_list = names(api.get(f"/api/collection/?status={status}&ordering={api_ordering}"))
    assert web_names(logged_in, f"status={status}&sort={web_sort}") == api_list
