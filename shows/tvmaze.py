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
    text = re.sub(r"<[^>]+>", " ", value)
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
