# project-two-building-with-APIs
CIDM 3312 Project #2 — Django application consuming and providing APIs.

## TVmaze API verification script

HTTP.tv uses the free [TVmaze API](https://www.tvmaze.com/api) to search for TV shows.
`scripts/verify_tvmaze.py` checks that this works before the Django app is built: it sends
one real search request to TVmaze and prints up to 10 matching shows (name, years, genres,
rating, TVmaze ID, and link). No API key or account is needed.

### Setup

Requires [uv](https://docs.astral.sh/uv/). From the repository root:

```
uv sync
```

This creates `.venv` with the exact dependency versions in `uv.lock` (Python 3.14 is pinned
in `.python-version`; uv downloads it if needed).

### Run the script

Pass the search text as an argument (use quotes for multi-word titles):

```
uv run python scripts/verify_tvmaze.py "the office"
```

Or run it with no argument and type the search when prompted:

```
uv run python scripts/verify_tvmaze.py
Search TV shows: the office
```

| Outcome | Message | Exit code |
|---|---|---|
| Shows found | `Found N shows for "..."` and a numbered list | 0 |
| No matches | `No shows found for "..."` | 0 |
| Blank input (TVmaze is not called) | `Please enter a TV show name to search for.` | 1 |
| Timeout (10 s), connection error, HTTP error, or unreadable response | `Error: ...` with a plain-English explanation | 1 |

### Run the tests

```
uv run pytest
```

The tests in `tests/test_verify_tvmaze.py` replace the network call with fake responses, so
they run offline and cover failures that are hard to trigger by hand (timeouts, connection
errors, HTTP 429/5xx, invalid JSON). Real requests are checked manually by running the script.
