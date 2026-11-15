"""The shared tracking rules (AC23), tested once at the source.

The same `validate_tracking` function backs the model, the web form and (Phase 10) the
API serializer, and the database check constraints enforce the same rules.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from shows.models import CollectionEntry, Show
from shows.validation import validate_tracking

VALID = {"status": "watching", "current_season": 2, "current_episode": 9, "rating": 4, "notes": "Great."}


def errors_for(**changes):
    return validate_tracking(**{**VALID, **changes})


def test_valid_values_have_no_errors():
    assert errors_for() == {}


@pytest.mark.parametrize("changes", [
    {"current_season": None, "current_episode": None},   # not started
    {"rating": None},                                    # not rated
    {"notes": ""},
    {"notes": "x" * 2000},                               # exactly the limit
    {"rating": 1}, {"rating": 5},
    {"current_season": 1, "current_episode": 1},
])
def test_valid_boundaries(changes):
    assert errors_for(**changes) == {}


@pytest.mark.parametrize("status", ["plan_to_watch", "watching", "on_hold", "completed", "dropped"])
def test_every_status_choice_is_valid(status):
    assert errors_for(status=status) == {}


@pytest.mark.parametrize("changes, field", [
    ({"status": "binge_watching"}, "status"),
    ({"status": ""}, "status"),
    ({"current_season": 3, "current_episode": None}, "current_episode"),   # season only
    ({"current_season": None, "current_episode": 4}, "current_season"),    # episode only
    ({"current_season": 0}, "current_season"),
    ({"current_episode": 0}, "current_episode"),
    ({"current_season": -1}, "current_season"),
    ({"current_episode": -3}, "current_episode"),
    ({"rating": 0}, "rating"),
    ({"rating": 6}, "rating"),
    ({"rating": -1}, "rating"),
    ({"notes": "x" * 2001}, "notes"),
])
def test_invalid_values_are_rejected_on_the_right_field(changes, field):
    errors = errors_for(**changes)
    assert field in errors and errors[field]


def test_missing_half_of_progress_explains_the_rule():
    errors = errors_for(current_season=3, current_episode=None)
    assert errors["current_episode"] == "Enter both a season and an episode, or leave both blank."


@pytest.mark.parametrize("value", ["two", 2.5, True])
def test_non_integer_progress_and_rating_are_rejected(value):
    assert "current_season" in errors_for(current_season=value)
    assert "rating" in errors_for(rating=value)


# --- The model and the database use the same rules ----------------------------------------------

@pytest.fixture
def show(db):
    return Show.objects.create(tvmaze_id=1, name="Show", tvmaze_url="https://www.tvmaze.com/shows/1")


def test_model_full_clean_uses_the_shared_rules(user, show):
    entry = CollectionEntry(user=user, show=show, current_season=2)
    with pytest.raises(ValidationError) as excinfo:
        entry.full_clean()
    assert "current_episode" in excinfo.value.message_dict


@pytest.mark.parametrize("fields", [
    {"current_season": 2, "current_episode": None},
    {"current_season": None, "current_episode": 2},
    {"current_season": 0, "current_episode": 1},
    {"rating": 0},
    {"rating": 6},
    {"status": "binge_watching"},
    {"notes": "x" * 2001},
])
def test_database_constraints_block_invalid_rows_that_skip_validation(user, show, fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        CollectionEntry.objects.create(user=user, show=show, **fields)
