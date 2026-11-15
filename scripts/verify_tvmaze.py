"""Verify that HTTP.tv can search the TVmaze API.

Sends one real search request to TVmaze and prints the matching TV shows.

Usage (from the repository root):
    uv run python scripts/verify_tvmaze.py "the office"
    uv run python scripts/verify_tvmaze.py            # prompts for a search term

Exit codes:
    0  results found, or the search returned no matches
    1  blank input, or the request to TVmaze failed
"""

import sys

import requests

TVMAZE_SEARCH_URL = "https://api.tvmaze.com/search/shows"
TIMEOUT_SECONDS = 10
USER_AGENT = "HTTP.tv-verify/0.1"
MAX_RESULTS = 10
MISSING = "N/A"


class SearchError(Exception):
    """A problem the user should see as a friendly message (the script then exits with 1)."""


def get_search_term(argv=None):
    """Return the trimmed search term, or None if it is blank.

    Uses the command-line arguments if any were given; otherwise prompts the user.
    """
    if argv is None:
        argv = sys.argv[1:]

    if argv:
        # Join the words so that `verify_tvmaze.py the office` also works without quotes.
        term = " ".join(argv)
    else:
        try:
            term = input("Search TV shows: ")
        except EOFError:
            # The input stream ended (e.g. Ctrl+Z / Ctrl+D) before anything was typed.
            term = ""

    term = term.strip()
    return term or None


def search_shows(term):
    """Search TVmaze for shows matching `term` and return a list of show dictionaries.

    The list keeps TVmaze's relevance order (best match first) and may be empty.
    Raises SearchError with a user-friendly message if the request fails or the
    response is not what TVmaze normally sends.
    """
    try:
        response = requests.get(
            TVMAZE_SEARCH_URL,
            params={"q": term},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        raise SearchError(
            f"TVmaze did not respond within {TIMEOUT_SECONDS} seconds. Please try again later."
        )
    except requests.ConnectionError:
        raise SearchError("Could not connect to TVmaze. Check your internet connection.")
    except requests.RequestException as error:
        # Any other problem raised by requests while sending the request.
        raise SearchError(f"The request to TVmaze failed: {error}")

    if response.status_code != 200:
        status = response.status_code
        if status == 429:
            raise SearchError(
                "TVmaze returned HTTP 429 (too many requests). "
                "Wait a few seconds and try again."
            )
        if status >= 500:
            raise SearchError(
                f"TVmaze returned HTTP {status} (a problem on TVmaze's side). "
                "Please try again later."
            )
        raise SearchError(f"TVmaze returned HTTP {status}. The search could not be completed.")

    try:
        data = response.json()
    except ValueError:
        raise SearchError("TVmaze sent a response that could not be read (invalid JSON).")

    # A normal response is a list of {"score": ..., "show": {...}} items.
    if not isinstance(data, list):
        raise SearchError("TVmaze sent a response that could not be read (unexpected data).")

    shows = []
    for item in data:
        show = item.get("show") if isinstance(item, dict) else None
        if not isinstance(show, dict) or not all(key in show for key in ("id", "name", "url")):
            raise SearchError("TVmaze sent a response that could not be read (unexpected data).")
        shows.append(show)
    return shows


def format_show(show, number):
    """Return the display text for one show, using fallbacks for missing values."""
    premiered = show.get("premiered")  # e.g. "2005-03-24", or None
    ended = show.get("ended")
    status = show.get("status")

    if premiered:
        start = premiered[:4]
        if ended:
            end = ended[:4]
            # A show that began and ended in the same year shows one year, e.g. "2024".
            years = start if end == start else f"{start}–{end}"
        elif status == "Running":
            years = f"{start}–present"
        else:
            years = f"{start}–{MISSING}"
    elif status == "In Development":
        years = f"Not yet aired, {status}"
    else:
        years = MISSING

    genres = ", ".join(show.get("genres") or []) or MISSING

    rating = (show.get("rating") or {}).get("average")
    rating_text = str(rating) if rating is not None else MISSING

    # Right-align the number to two characters (" 1." ... "10.") so every title
    # and every detail line starts in the same column.
    return (
        f"{number:>2}. {show['name']} ({years})\n"
        f"    Genres:    {genres}\n"
        f"    Rating:    {rating_text}\n"
        f"    TVmaze ID: {show['id']}\n"
        f"    Link:      {show['url']}"
    )


def main(argv=None):
    """Run the verification and return the exit code (0 = success, 1 = error)."""
    term = get_search_term(argv)
    if term is None:
        print("Please enter a TV show name to search for.", file=sys.stderr)
        return 1

    try:
        shows = search_shows(term)
    except SearchError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if not shows:
        print(f'No shows found for "{term}". Try a different search.')
        return 0

    noun = "show" if len(shows) == 1 else "shows"
    summary = f'Found {len(shows)} {noun} for "{term}"'
    if len(shows) > MAX_RESULTS:
        summary += f" (showing the first {MAX_RESULTS})"
    print(summary + "\n")

    for number, show in enumerate(shows[:MAX_RESULTS], start=1):
        print(format_show(show, number))
        print()

    return 0


if __name__ == "__main__":
    # Always write UTF-8 so names like "A Konyhafőnök" print correctly,
    # even when the output is redirected to a file on Windows.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
