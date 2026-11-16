"""Data for the Discover page's browsing rows (shown before the user searches).

Sources, all real:
- Airing This Week: TVmaze's TV and streaming schedules for today and the next 6 days.
- Featured: the highest TVmaze-rated shows among this week's schedule (labelled that way).
- Browse by Genre: genres that actually occur in this week's shows and in shows stored on HTTP.tv.
- Recommended: the local genre match against the user's collection (services.recommended_for_user).

TVmaze responses are cached (Django's cache): schedules for 1 hour, backdrop lookups for
7 days (TVmaze image URLs never change). Failures are never cached, so the next visit retries.
Nothing here writes to the database: browsing never saves a show.
"""

import datetime

from django.core.cache import cache
from django.utils import timezone

from . import tvmaze
from .models import Show
from .services import _genre_set

SCHEDULE_TTL = 60 * 60
BACKDROP_TTL = 7 * 24 * 60 * 60
WEEK_DAYS = 7
FEATURED_COUNT = 10
AIRING_LIMIT = 30
DEFAULT_COUNTRY = "US"


def _cached(key, ttl, fetch):
    value = cache.get(key)
    if value is None:
        value = fetch()  # may raise TVmazeError; errors are not cached
        cache.set(key, value, ttl)
    return value


def _day_label(day, today):
    if day == today:
        return "Today"
    if day == today + datetime.timedelta(days=1):
        return "Tomorrow"
    return day.strftime("%a, %b ") + str(day.day)


def _episode_label(item):
    season, number = item.get("season"), item.get("number")
    return f"S{season} E{number}" if season and number else ""


def week_schedule(country=DEFAULT_COUNTRY, today=None):
    """This week's shows (one per show, at its first airing this week) and an error message or "".

    Two requests per day (TV networks in `country`, and streaming), each cached for an
    hour. If TVmaze fails, fetching stops (to avoid hammering it) and the days already
    loaded are still returned with the error.
    """
    today = today or timezone.localdate()
    shows, error = {}, ""
    for offset in range(WEEK_DAYS):
        day = today + datetime.timedelta(days=offset)
        date = day.isoformat()
        try:
            network = _cached(f"tvmaze:schedule:{country}:{date}", SCHEDULE_TTL,
                              lambda: tvmaze.get_schedule(date, country))
            web = _cached(f"tvmaze:schedule-web:{date}", SCHEDULE_TTL, lambda: tvmaze.get_web_schedule(date))
        except tvmaze.TVmazeError as problem:
            error = str(problem)
            break
        # Streaming channels with no country (e.g. global services) are available everywhere.
        web = [item for item in web if item["channel_country_code"] in ("", country)]
        for item in sorted(network + web, key=lambda i: (i["airtime"], i["show"]["name"].lower())):
            tvmaze_id = item["show"]["tvmaze_id"]
            if tvmaze_id not in shows:
                shows[tvmaze_id] = {**item["show"], "airs_on": day, "airs_label": _day_label(day, today),
                                    "airtime": item["airtime"], "episode_label": _episode_label(item)}
    return list(shows.values()), error


def with_local_backdrops(shows):
    """Fill in `background_url` from shows stored on HTTP.tv or already-cached lookups (no requests).

    Only TVmaze show dicts are filled in; stored `Show` objects already carry their backdrop.
    """
    ids = [show["tvmaze_id"] for show in shows if isinstance(show, dict) and not show.get("background_url")]
    stored = dict(Show.objects.filter(tvmaze_id__in=ids).exclude(background_url="")
                  .values_list("tvmaze_id", "background_url"))
    for show in shows:
        if isinstance(show, dict) and not show.get("background_url"):
            show["background_url"] = stored.get(show["tvmaze_id"]) or cache.get(f"tvmaze:backdrop:{show['tvmaze_id']}") or ""
    return shows


def featured(week_shows):
    """The 10 highest TVmaze-rated shows airing this week, with real backdrops where possible.

    Backdrops not already known are looked up (one request each, cached 7 days). The first
    failed lookup stops further lookups; those cards use the poster fallback instead.
    """
    rated = [show for show in week_shows if show.get("tvmaze_rating")]
    rated.sort(key=lambda show: (-float(show["tvmaze_rating"]), show["name"].lower()))
    picks = with_local_backdrops([dict(show) for show in rated[:FEATURED_COUNT]])
    for show in picks:
        if show["background_url"]:
            continue
        key = f"tvmaze:backdrop:{show['tvmaze_id']}"
        if cache.get(key) is not None:
            continue  # known to have no qualifying backdrop
        try:
            show["background_url"] = _cached(key, BACKDROP_TTL, lambda: tvmaze.get_backdrop(show["tvmaze_id"]))
        except tvmaze.TVmazeError:
            break
    return picks


def airing_this_week(week_shows):
    # Day by day; within a day, highest TVmaze rating first (unrated last), then air time.
    ordered = sorted(week_shows, key=lambda show: (show["airs_on"], -float(show.get("tvmaze_rating") or 0),
                                                   show["airtime"], show["name"].lower()))
    return with_local_backdrops([dict(show) for show in ordered[:AIRING_LIMIT]])


def genre_counts(week_shows):
    """[(genre, number of shows)] from this week's shows and shows stored on HTTP.tv, most first."""
    counts, names = {}, {}
    seen = set()
    stored = [{"tvmaze_id": s.tvmaze_id, "genres": s.genres} for s in Show.objects.only("tvmaze_id", "genres")]
    for show in list(week_shows) + stored:
        if show["tvmaze_id"] in seen:
            continue
        seen.add(show["tvmaze_id"])
        for genre in (show.get("genres") or "").split(","):
            genre = genre.strip()
            if genre:
                key = genre.lower()
                names.setdefault(key, genre)
                counts[key] = counts.get(key, 0) + 1
    return sorted(((names[key], count) for key, count in counts.items()), key=lambda item: (-item[1], item[0].lower()))


def shows_in_genre(genre, week_shows):
    """(this week's shows in the genre, stored HTTP.tv shows in the genre not airing this week)."""
    wanted = genre.strip().lower()
    airing = [show for show in week_shows if wanted in _genre_set(show.get("genres"))]
    airing_ids = {show["tvmaze_id"] for show in airing}
    stored = [show for show in Show.objects.filter(genres__icontains=wanted).order_by("name")
              if wanted in _genre_set(show.genres) and show.tvmaze_id not in airing_ids]
    airing.sort(key=lambda show: (show["airs_on"], show["name"].lower()))
    return with_local_backdrops([dict(show) for show in airing]), stored
