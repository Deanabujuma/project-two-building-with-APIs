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

## HTTP.tv Django app

HTTP.tv is a Django web app for finding TV shows on TVmaze, saving them to a personal
collection, and tracking status, progress, ratings and notes. It also has its own authenticated
REST API. The design is in `prd/httptv.md`, the build order in `plans/httptv.md`, and the UI
prototypes in `prototypes/`. Sections below are added as each feature is built.

Stack: Python ≥3.12 (3.14 pinned locally), Django 6.1, Django REST Framework 3.18,
django-filter 26.2, SQLite, and pytest with pytest-django.

### First-time setup

1. Install dependencies: `uv sync`
2. Create your environment file from the example (`.env` is Git-ignored, so secrets stay local):

   ```
   cp .env.example .env
   ```

   Then replace the `DJANGO_SECRET_KEY` placeholder with a real key. This command generates one:

   ```
   uv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
   ```

   Django refuses to start if `DJANGO_SECRET_KEY` is missing.
3. Create the database: `uv run --env-file .env python manage.py migrate`
4. (Optional) Create an admin account: `uv run --env-file .env python manage.py createsuperuser`
5. Run the site: `uv run --env-file .env python manage.py runserver`, then open http://127.0.0.1:8000/
   (the admin is at http://127.0.0.1:8000/admin/).

Every `manage.py` command needs `--env-file .env` so Django can read your settings.

| Variable | Used by | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django | Required secret key |
| `DJANGO_DEBUG` | Django | `true` for local development |
| `DJANGO_ALLOWED_HOSTS` | Django | Comma-separated host names |
| `HTTPTV_API_TOKEN` | `httptv_client.py` | Your API token (never commit it) |
| `HTTPTV_API_URL` | `httptv_client.py` | API base URL (default `http://127.0.0.1:8000/api/`) |

### Tests

`uv run pytest` runs every test, including the original 44 TVmaze verification-script tests.
It needs no `.env` and no network, because the tests use `config.test_settings`, which supplies a
test-only secret key, and every external HTTP call is mocked.

### Accounts and pages

- Anyone can view the home page (`/`), log in (`/accounts/login/`) and sign up (`/accounts/signup/`).
  Signing up logs you straight in.
- Every other page requires login. Anonymous visitors are redirected to the login page and sent
  back to the page they asked for afterwards.
- Logging out is a POST request (the icon at the far right of the nav bar), so a plain link
  can't log you out.
- The navigation bar has two versions. Visitors see only the wordmark, **Log in** and **Sign up**.
  Logged-in users see their username, Home, Discover, My Collection, Watching, Completed, search
  and log out.
- Every page's footer credits TVmaze and the CC BY-SA 4.0 license.

### Discover (searching TVmaze)

`/discover/?q=<title>` searches TVmaze's public API and shows up to 10 shows in TVmaze's relevance
order. A blank search shows a hint and never calls TVmaze. Timeouts (10 seconds), connection
problems, rate limiting (HTTP 429) and unreadable responses each show a friendly message instead
of an error page. All TVmaze requests go through `shows/tvmaze.py`, which sends the generic
User-Agent `HTTP.tv/0.1`. Unsaved results show years and channel (e.g. "2005–2013 · NBC"), so
shows with the same title can be told apart.
