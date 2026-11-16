"""Business operations shared by the web pages and the REST API."""

from collections import Counter

from django.db import IntegrityError, transaction
from django.db.models import Q

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


def _genre_set(genres):
    return {genre.strip().lower() for genre in (genres or "").split(",") if genre.strip()}


def suggested_shows(tvmaze_id, genres, limit=20):
    """Shows already on HTTP.tv that share at least one genre with this show.

    Ranked by how many genres they share, then by name, excluding the show itself.
    This is a local genre match, not a TVmaze recommendation.
    """
    wanted = _genre_set(genres)
    if not wanted:
        return []
    candidates = Q()
    for genre in wanted:
        candidates |= Q(genres__icontains=genre)
    scored = []
    for show in Show.objects.filter(candidates).exclude(tvmaze_id=tvmaze_id):
        shared = len(wanted & _genre_set(show.genres))
        if shared:
            scored.append((-shared, show.name.lower(), show))
    scored.sort(key=lambda item: item[:2])
    return [show for _, _, show in scored[:limit]]


def _show_value(show, field):
    return show.get(field) if isinstance(show, dict) else getattr(show, field, None)


def recommended_for_user(user, extra_candidates=(), limit=20):
    """Shows not in the user's collection that share genres with it (the same local genre match).

    Candidates are shows stored on HTTP.tv plus `extra_candidates` (e.g. this week's TVmaze
    schedule, as show dicts). Ranked by how many genres they share with the collection,
    then by how many collection shows have those genres, then by name.
    """
    collection_genres = Counter()
    saved_ids = set()
    for entry in CollectionEntry.objects.filter(user=user).select_related("show"):
        saved_ids.add(entry.show.tvmaze_id)
        collection_genres.update(_genre_set(entry.show.genres))
    if not collection_genres:
        return []

    candidates = {}
    for show in list(Show.objects.exclude(tvmaze_id__in=saved_ids)) + list(extra_candidates):
        tvmaze_id = _show_value(show, "tvmaze_id")
        if tvmaze_id not in saved_ids and tvmaze_id not in candidates:
            candidates[tvmaze_id] = show

    scored = []
    for show in candidates.values():
        shared = _genre_set(_show_value(show, "genres")) & set(collection_genres)
        if shared:
            weight = sum(collection_genres[genre] for genre in shared)
            scored.append(((-len(shared), -weight, _show_value(show, "name").lower()), show))
    scored.sort(key=lambda item: item[0])
    return [show for _, show in scored[:limit]]
