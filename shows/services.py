"""Business operations shared by the web pages and the REST API."""

from django.db import IntegrityError, transaction

from . import tvmaze
from .models import CollectionEntry, Show


class AlreadySaved(Exception):
    """The user already has this show in their collection."""

    def __init__(self, entry):
        super().__init__(f"{entry.show.name} is already in your collection.")
        self.entry = entry


def save_show_to_collection(user, tvmaze_id):
    """Add a TVmaze show to the user's collection and return the new CollectionEntry.

    Only the TVmaze ID comes from the client. The show's details are always re-fetched
    from TVmaze, so a user can't plant made-up show data. The shared Show row is
    created, or refreshed with TVmaze's latest values (refresh-on-save).

    Raises AlreadySaved, tvmaze.ShowNotFound or tvmaze.TVmazeError. On any error,
    nothing is written to the database.
    """
    existing = CollectionEntry.objects.filter(user=user, show__tvmaze_id=tvmaze_id).select_related("show").first()
    if existing:
        raise AlreadySaved(existing)

    fields = tvmaze.get_show(tvmaze_id)  # Network call happens before any database write.
    fields.pop("tvmaze_id")

    try:
        with transaction.atomic():
            show, _ = Show.objects.update_or_create(tvmaze_id=tvmaze_id, defaults=fields)
            return CollectionEntry.objects.create(user=user, show=show)
    except IntegrityError:
        # A second request saved the same show at the same moment.
        raise AlreadySaved(CollectionEntry.objects.select_related("show").get(user=user, show__tvmaze_id=tvmaze_id))
