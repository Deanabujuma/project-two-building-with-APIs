"""Collection queries shared by the web collection page and the REST API.

Both use these functions for owner scoping, status filtering and ordering, so the same
request returns the same entries in the same order in both places.
"""

from django.db.models import F
from django.db.models.functions import Lower

from .models import CollectionEntry

DEFAULT_ORDERING = "-updated_at"

# The ordering fields the API accepts (`?ordering=`, with "-" for descending).
ORDERING_FIELDS = {"updated_at", "created_at", "show__name", "rating", "show__premiered", "show__tvmaze_rating"}

# Fields that can be empty. Empty values go last in BOTH directions; SQLite would otherwise
# put NULLs first when sorting ascending.
NULLS_LAST_FIELDS = {"rating", "show__tvmaze_rating", "show__premiered"}

# Text is sorted case-insensitively, so "alpha" sits next to "Alpha" instead of after "Zulu".
CASE_INSENSITIVE_FIELDS = {"show__name"}


class InvalidOrdering(ValueError):
    """An ordering value that isn't one of ORDERING_FIELDS (optionally with "-")."""


def collection_entries(user, status=None):
    """The user's entries (never anyone else's), optionally limited to one status."""
    entries = CollectionEntry.objects.filter(user=user).select_related("show")
    if status:
        entries = entries.filter(status=status)
    return entries


def _expression(field, descending):
    expression = Lower(field) if field in CASE_INSENSITIVE_FIELDS else F(field)
    if field in NULLS_LAST_FIELDS:
        return expression.desc(nulls_last=True) if descending else expression.asc(nulls_last=True)
    return expression.desc() if descending else expression.asc()


def order_entries(entries, ordering=None):
    """Order a queryset by one allowed field (default: most recently updated first).

    Ties are broken by show name (case-insensitive) and then by entry ID, so results and
    page boundaries are stable.
    """
    ordering = ordering or DEFAULT_ORDERING
    descending = ordering.startswith("-")
    field = ordering[1:] if descending else ordering
    if field not in ORDERING_FIELDS:
        raise InvalidOrdering(f"Unknown ordering '{ordering}'. Choose from: {', '.join(sorted(ORDERING_FIELDS))}.")
    return entries.order_by(_expression(field, descending), Lower("show__name").asc(), "pk")
