"""The only part of HTTP.tv that talks to the TVmaze API.

Every function returns plain Python data shaped like HTTP.tv's `Show` model fields
(see `map_show`), or raises `TVmazeError` with a message that is safe to show to a
user. Views never call `requests` directly, and tests mock this module's HTTP calls.

TVmaze data is licensed CC BY-SA 4.0; the site footer gives the required credit.
"""

import html
import re

import requests

BASE_URL = "https://api.tvmaze.com"
TIMEOUT_SECONDS = 10
USER_AGENT = "HTTP.tv/0.1"
MAX_SEARCH_RESULTS = 10
MIN_BACKDROP_WIDTH = 1920  # Backdrops narrower than this look blurry in the full-width hero.


class TVmazeError(Exception):
    """A TVmaze problem described in words a user can understand."""


class ShowNotFound(TVmazeError):
    """TVmaze has no show with the requested ID (HTTP 404)."""


# --- Low-level request ------------------------------------------------------------------

def _get(path, params=None):
    """GET a TVmaze endpoint and return the decoded JSON, or raise TVmazeError."""
    try:
        response = requests.get(
            f"{BASE_URL}{path}",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        raise TVmazeError(
            f"TVmaze didn't respond within {TIMEOUT_SECONDS} seconds. Please try again in a moment."
        )
    except requests.ConnectionError:
        raise TVmazeError("HTTP.tv couldn't connect to TVmaze. Check your internet connection and try again.")
    except requests.RequestException:
        raise TVmazeError("The request to TVmaze failed. Please try again.")

    status = response.status_code
    if status == 404:
        raise ShowNotFound("TVmaze has no show with that ID.")
    if status == 429:
        raise TVmazeError("TVmaze is receiving too many requests right now. Wait a few seconds and try again.")
    if status >= 500:
        raise TVmazeError(f"TVmaze is having problems (HTTP {status}). Please try again later.")
    if status != 200:
        raise TVmazeError(f"TVmaze returned an unexpected response (HTTP {status}).")

    try:
        return response.json()
    except ValueError:
        raise TVmazeError("TVmaze sent a response HTTP.tv couldn't read.")


def _unreadable():
    return TVmazeError("TVmaze sent a response HTTP.tv couldn't read.")


# --- Mapping TVmaze data to HTTP.tv fields -------------------------------------------------

def strip_html(value):
    """Turn TVmaze's HTML summary into plain text (tags removed, entities decoded)."""
    if not value:
        return ""
    # Block tags separate words, so they become spaces; inline tags such as <b> and <i>
    # are removed without a space (otherwise "<b>The Office</b>, a" -> "The Office , a").
    text = re.sub(r"</?(p|br|div|li|ul|ol|h[1-6])(?=[\s/>])[^>]*>", " ", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def pick_backdrop(images):
    """Return the URL of the widest 'background' image at least 1920 px wide, or "".

    TVmaze never marks a background as the main one, so HTTP.tv uses a fixed rule.
    Ties keep TVmaze's order. Anything narrower is skipped, and the page falls back to
    the poster instead of stretching a small image.
    """
    best_url, best_width = "", 0
    for image in images or []:
        if not isinstance(image, dict) or image.get("type") != "background":
            continue
        original = (image.get("resolutions") or {}).get("original") or {}
        width = original.get("width") or 0
        url = original.get("url")
        if url and width >= MIN_BACKDROP_WIDTH and width > best_width:
            best_url, best_width = url, width
    return best_url


def channel_info(raw):
    """Return (name, channel_type, country) from TVmaze's network / webChannel objects.

    A TV network wins when both are present; channel_type is "network",
    "web channel", or "" when TVmaze lists neither.
    """
    for key, kind in (("network", "network"), ("webChannel", "web channel")):
        channel = raw.get(key)
        if isinstance(channel, dict) and channel.get("name"):
            country = (channel.get("country") or {}).get("name") or ""
            return channel["name"], kind, country
    return "", "", ""


def map_show(raw):
    """Map one TVmaze show object to a dict of HTTP.tv `Show` field values.

    Raises TVmazeError if the object lacks the fields every show must have.
    """
    if not isinstance(raw, dict) or not all(raw.get(key) for key in ("id", "name", "url")):
        raise _unreadable()
    network, channel_type, channel_country = channel_info(raw)
    embedded_images = (raw.get("_embedded") or {}).get("images")
    rating = (raw.get("rating") or {}).get("average")
    return {
        "tvmaze_id": raw["id"],
        "name": raw["name"],
        "tvmaze_url": raw["url"],
        "image_url": (raw.get("image") or {}).get("medium") or "",
        "premiered": raw.get("premiered") or None,
        "ended": raw.get("ended") or None,
        "show_status": raw.get("status") or "",
        "genres": ", ".join(raw.get("genres") or []),
        "summary": strip_html(raw.get("summary")),
        "network": network,
        "channel_type": channel_type,
        "channel_country": channel_country,
        "background_url": pick_backdrop(embedded_images),
        "runtime": raw.get("runtime") or raw.get("averageRuntime") or None,
        "tvmaze_rating": rating,
        "language": raw.get("language") or "",
        "show_type": raw.get("type") or "",
    }


# --- Public operations ---------------------------------------------------------------------

def search_shows(term):
    """Search TVmaze and return up to 10 mapped shows in TVmaze's relevance order."""
    data = _get("/search/shows", {"q": term})
    if not isinstance(data, list):
        raise _unreadable()
    shows = []
    for item in data[:MAX_SEARCH_RESULTS]:
        if not isinstance(item, dict):
            raise _unreadable()
        shows.append(map_show(item.get("show")))
    return shows


MAX_CAST = 8


def _fetch_show(tvmaze_id, embeds):
    return _get(f"/shows/{int(tvmaze_id)}", {"embed[]": list(embeds)})


def map_extras(raw):
    """Seasons and up to 8 cast members from a show fetched with seasons and cast embedded."""
    embedded = (raw.get("_embedded") or {}) if isinstance(raw, dict) else {}
    seasons = []
    for season in embedded.get("seasons") or []:
        if isinstance(season, dict) and season.get("number") is not None:
            seasons.append({
                "number": season["number"],
                "episodes": season.get("episodeOrder"),
                "start": season.get("premiereDate") or "",
                "end": season.get("endDate") or "",
            })
    cast = []
    for member in (embedded.get("cast") or [])[:MAX_CAST]:
        person = (member or {}).get("person") or {}
        character = (member or {}).get("character") or {}
        if person.get("name"):
            cast.append({
                "person": person["name"],
                "character": character.get("name") or "",
                "image": (person.get("image") or {}).get("medium") or "",
            })
    return {"seasons": seasons, "cast": cast}


def get_show(tvmaze_id):
    """Fetch one show with its images embedded (one request) and return mapped fields.

    Raises ShowNotFound for an unknown ID, or TVmazeError for any other problem.
    """
    return map_show(_fetch_show(tvmaze_id, ["images"]))


def get_extras(tvmaze_id):
    """Fetch a show's seasons and cast (one request), for the Extras tab."""
    raw = _fetch_show(tvmaze_id, ["seasons", "cast"])
    if not isinstance(raw, dict) or not raw.get("id"):
        raise _unreadable()
    return map_extras(raw)


def get_show_and_extras(tvmaze_id):
    """Fetch show details, seasons and cast in a single request (unsaved show on Extras)."""
    raw = _fetch_show(tvmaze_id, ["images", "seasons", "cast"])
    return map_show(raw), map_extras(raw)


# --- Schedules and images (Discover browsing) --------------------------------------------------

def _schedule_items(data, show_key):
    """Map schedule entries to {"show", "airtime", "season", "number"}. Malformed entries are skipped."""
    if not isinstance(data, list):
        raise _unreadable()
    items = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("show") if show_key == "show" else (entry.get("_embedded") or {}).get("show")
        try:
            show = map_show(raw)
        except TVmazeError:
            continue
        country = ""
        for key in ("network", "webChannel"):
            channel = (raw or {}).get(key)
            if isinstance(channel, dict) and channel.get("name"):
                country = ((channel.get("country") or {}).get("code") or "")
                break
        items.append({"show": show, "channel_country_code": country, "airtime": entry.get("airtime") or "",
                      "season": entry.get("season"), "number": entry.get("number")})
    return items


def get_schedule(date, country):
    """TV-network episodes airing on `date` (YYYY-MM-DD) in `country` (ISO code), one request."""
    return _schedule_items(_get("/schedule", {"country": country, "date": date}), "show")


def get_web_schedule(date):
    """Streaming (web channel) episodes released on `date`, worldwide, one request.

    TVmaze's country filter drops global streamers whose channel has no country, so the
    caller filters by country instead (see shows.browse).
    """
    return _schedule_items(_get("/schedule/web", {"date": date}), "_embedded")


def get_backdrop(tvmaze_id):
    """The show's backdrop URL by the usual rule (widest background >= 1920 px), or "". One request."""
    images = _get(f"/shows/{int(tvmaze_id)}/images")
    if not isinstance(images, list):
        raise _unreadable()
    return pick_backdrop(images)
