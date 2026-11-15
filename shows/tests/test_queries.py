"""Shared collection query logic used by the web page and the API (AC30 and the ordering half of AC41/AC43)."""

import datetime
from decimal import Decimal

import pytest

from shows.models import CollectionEntry, Show
from shows.queries import ORDERING_FIELDS, InvalidOrdering, collection_entries, order_entries


def add(user, tvmaze_id, name, rating=None, status="plan_to_watch", tvmaze_rating=None, premiered=None):
    show = Show.objects.create(tvmaze_id=tvmaze_id, name=name, tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}",
                               tvmaze_rating=tvmaze_rating, premiered=premiered)
    return CollectionEntry.objects.create(user=user, show=show, rating=rating, status=status)


@pytest.fixture
def mixed(user):
    """Five entries: three rated, two unrated (created in this order)."""
    return [
        add(user, 1, "Charlie", rating=3, tvmaze_rating=Decimal("7.5"), premiered=datetime.date(2010, 1, 1)),
        add(user, 2, "alpha", rating=None, status="watching", tvmaze_rating=None, premiered=datetime.date(2020, 1, 1)),
        add(user, 3, "Echo", rating=5, status="watching", tvmaze_rating=Decimal("8.9"), premiered=datetime.date(2001, 1, 1)),
        add(user, 4, "Delta", rating=None, status="completed", tvmaze_rating=Decimal("6.0"), premiered=None),
        add(user, 5, "Bravo", rating=1, status="completed", tvmaze_rating=None, premiered=datetime.date(2015, 1, 1)),
    ]


def names(qs):
    return [entry.show.name for entry in qs]


# --- Scope and filter -----------------------------------------------------------------------------------

def test_only_the_users_own_entries(user, other_user, mixed):
    add(other_user, 99, "Not Mine")
    assert "Not Mine" not in names(collection_entries(user))
    assert len(collection_entries(user)) == 5


def test_status_filter(user, mixed):
    assert sorted(names(collection_entries(user, status="watching"))) == ["Echo", "alpha"]


def test_blank_status_means_all(user, mixed):
    assert len(collection_entries(user, status="")) == 5


# --- AC30 / AC41: unrated last in BOTH directions ------------------------------------------------------

def test_rating_descending_puts_unrated_last(user, mixed):
    assert names(order_entries(collection_entries(user), "-rating")) == ["Echo", "Charlie", "Bravo", "alpha", "Delta"]


def test_rating_ascending_also_puts_unrated_last(user, mixed):
    # SQLite would put NULLs first in ascending order without the explicit nulls-last rule.
    assert names(order_entries(collection_entries(user), "rating")) == ["Bravo", "Charlie", "Echo", "alpha", "Delta"]


@pytest.mark.parametrize("ordering, expected", [
    ("show__tvmaze_rating", ["Delta", "Charlie", "Echo", "alpha", "Bravo"]),
    ("-show__tvmaze_rating", ["Echo", "Charlie", "Delta", "alpha", "Bravo"]),
])
def test_tvmaze_rating_puts_missing_values_last_in_both_directions(user, mixed, ordering, expected):
    assert names(order_entries(collection_entries(user), ordering)) == expected


def test_ties_are_broken_by_name_case_insensitively(user, mixed):
    # alpha and Delta are both unrated: tie broken by name, ignoring case.
    ordered = names(order_entries(collection_entries(user), "-rating"))
    assert ordered[-2:] == ["alpha", "Delta"]


# --- Other ordering fields -------------------------------------------------------------------------------

def test_show_name_is_case_insensitive(user, mixed):
    assert names(order_entries(collection_entries(user), "show__name")) == ["alpha", "Bravo", "Charlie", "Delta", "Echo"]
    assert names(order_entries(collection_entries(user), "-show__name")) == ["Echo", "Delta", "Charlie", "Bravo", "alpha"]


def test_created_at_both_directions(user, mixed):
    assert names(order_entries(collection_entries(user), "created_at")) == ["Charlie", "alpha", "Echo", "Delta", "Bravo"]
    assert names(order_entries(collection_entries(user), "-created_at")) == ["Bravo", "Delta", "Echo", "alpha", "Charlie"]


def test_updated_at_default_is_most_recent_first(user, mixed):
    mixed[0].notes = "touched"
    mixed[0].save()
    assert names(order_entries(collection_entries(user), None))[0] == "Charlie"
    assert names(order_entries(collection_entries(user), "-updated_at"))[0] == "Charlie"
    assert names(order_entries(collection_entries(user), "updated_at"))[-1] == "Charlie"


def test_premiered_both_directions(user, mixed):
    assert names(order_entries(collection_entries(user), "show__premiered"))[:4] == ["Echo", "Charlie", "Bravo", "alpha"]
    assert names(order_entries(collection_entries(user), "-show__premiered"))[:4] == ["alpha", "Bravo", "Charlie", "Echo"]


def test_exactly_the_six_approved_fields():
    assert ORDERING_FIELDS == {"updated_at", "created_at", "show__name", "rating", "show__premiered", "show__tvmaze_rating"}


@pytest.mark.parametrize("bad", ["notes", "user__password", "-", "rating,notes", "show__summary"])
def test_unknown_ordering_is_rejected(user, bad):
    with pytest.raises(InvalidOrdering):
        order_entries(collection_entries(user), bad)
