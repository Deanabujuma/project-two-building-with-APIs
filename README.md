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
prototypes in `prototypes/`.

**Where things are**

| Path | What it is |
|---|---|
| `accounts/` | custom user model, sign up, log in/out |
| `shows/` | models, TVmaze client (`tvmaze.py`), save logic (`services.py`), shared validation and queries, web views |
| `shows/api/` | REST API: serializers, viewset, filters, pagination |
| `templates/`, `static/css/` | pages (Direction D design) |
| `scripts/verify_tvmaze.py` | TVmaze check script (built first; unchanged) |
| `scripts/httptv_client.py` | command-line client for the HTTP.tv API |
| `prd/httptv.md`, `plans/httptv.md` | requirements and phased build plan |
| `prototypes/` | `ui-convention-v1-variants.html` (three first layouts) and `ui-convention.html` (Direction D, the chosen design) |
| `docs/research/free-media-apis.md` | API research that led to TVmaze |
| `docs/evidence-log.md`, `docs/evidence/` | bugs and fixes, real requests/responses, screenshots, verification notes |

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

### Data model

- **Show:** one row per TVmaze show, shared by all users and keyed by the unique `tvmaze_id`. It
  stores TVmaze facts: name, links, poster and backdrop URLs, dates, status, genres, plain-text
  summary, original network or web channel (with type and country), runtime, TVmaze rating,
  language and type. Images are linked from TVmaze, never downloaded.
- **CollectionEntry:** one user's tracking of one show: status (Plan to Watch by default,
  Watching, On Hold, Completed or Dropped), current season and episode, a 1–5 rating, notes of up
  to 2,000 characters, and created/updated times. A user can save each show only once (a
  database constraint). Deleting a user deletes their entries; a show that is still in someone's
  collection can't be deleted.
- Both models are in the Django admin (`/admin/`) with search and filters, for inspecting data
  while developing.

### Saving a show

Click **+** on a Discover result (or **Add to my collection** on a show page). The form sends
only the show's TVmaze ID as a POST to `/collection/add/`. The server then fetches the show from
TVmaze itself, so a browser can never plant made-up show details. It creates or refreshes the
shared `Show` row, adds it to your collection as **Plan to Watch**, and opens
`/shows/<tvmaze_id>/?tab=tracking`. Saving the same show twice is refused with a message. If
TVmaze is unavailable, nothing is saved and you see why. Opening `/collection/add/` in the
browser (a GET request) returns 405.

The show page's backdrop is the widest TVmaze background at least 1920 px wide. When there
isn't one, the page uses the poster. **Where to watch** shows only the original network or web
channel that TVmaze lists, and links to the show's TVmaze page; HTTP.tv never claims streaming
availability. Known limitation: some TVmaze backdrops have the show's title printed in the
artwork (e.g. Severance), because there's no reliable automatic way to detect it.

### Show pages and tabs

`/shows/<tvmaze_id>/` works for any TVmaze show. Shows that are already saved load from
HTTP.tv's database. Any other show is fetched live from TVmaze and **not** saved until you click
**Add to my collection**. An unknown ID returns 404; if TVmaze is down, you see a friendly
"can't be loaded right now" page.

| Tab (`?tab=`) | Shown when | Content |
|---|---|---|
| `tracking` (My Tracking) | the show is in your collection (default) | your status, progress, rating and notes |
| `suggested` (Suggested) | always (default for unsaved shows) | other saved shows sharing at least one genre, ranked by shared genres then name; a local match, not a TVmaze recommendation |
| `extras` (Extras) | always | seasons and up to 8 cast members, fetched from TVmaze only when this tab is opened |

### Tracking a show

On a saved show's **My Tracking** tab you can set the status, season and episode, a 1–5 star
rating and notes. The form POSTs to `/collection/<id>/`. The same rules apply everywhere: in this
form, the admin, the API, and as database check constraints:

- the status must be one of the five choices; it never changes automatically;
- season and episode: **both** blank (not started) or **both** whole numbers of 1 or more;
- rating: blank or 1–5;
- notes: at most 2,000 characters.

Invalid input is shown again with a message under the field, and nothing is saved. **Remove**
opens a confirmation page (`/collection/<id>/delete/`); confirming deletes only your tracking,
and the show stays on HTTP.tv for other users. Another user's entry URLs return 404.

### My Collection

`/collection/` shows your saved shows, 12 per page. Everything is controlled by URL parameters,
so any view can be bookmarked:

| Parameter | Values | Meaning |
|---|---|---|
| `status` | `plan_to_watch`, `watching`, `on_hold`, `completed`, `dropped` | show one status (the Watching and Completed nav links use this) |
| `q` | any text | show **titles** containing the text (case-insensitive). Notes are *not* searched here; the API's `search` does search notes |
| `sort` | `-updated` (default), `title`, `-rating` | recently updated, title A–Z, or your rating high–low |
| `page` | 1, 2, … | out-of-range values show the nearest valid page |

Unrated shows always sort after rated ones. The owner scoping, status filter and ordering come
from `shows/queries.py`, the same code the API uses, so both list the same entries in the same
order.

### Home page

Logged-in users see a large hero for the show they're currently tracking (the most recently
updated **Watching** entry; if there is none, the most recently updated entry). Below it are
rows of their own shows: **Continue Tracking**, **My Watchlist**, **Recently Added** (newest 10
saves of any status) and **Completed Shows**. Empty rows are hidden. With an empty collection,
the page shows a welcome hero with a **Discover shows** button.

### Discover browsing (post-submission improvement)

Before you search, Discover shows rows of wide cards built from real TVmaze data:

- **Featured Shows:** the 10 highest TVmaze-rated shows with new episodes this week.
- **Browse by Genre:** genre tiles with counts. Each opens a genre page (`/discover/genre/Comedy/`) listing that genre's shows airing this week, plus shows saved on HTTP.tv.
- **Airing This Week:** today plus the next 6 days of TVmaze's TV schedule for your schedule country (US by default) and its streaming schedule.
- **Recommended From My Collection:** shows that share genres with the shows you've saved. This uses the same local genre match as the Suggested tab, not a TVmaze recommendation.

Every card opens the show's page. Cards use the show's real backdrop when one is known;
otherwise they use the poster on a blurred background. TVmaze schedule responses are cached
in memory for 1 hour and backdrop lookups for 7 days, so repeat visits make no TVmaze calls.
The rows load right after the page appears, from `/discover/browse/`; without JavaScript,
a link opens them as a full page. If TVmaze is unavailable, a note appears and the local
rows still show. Searching works exactly as before. Details are in `prd/httptv-post-submission.md`.

### Profile & Settings (post-submission improvement)

Click your username or avatar in the nav bar to open **Profile & Settings** (`/accounts/profile/`). There you can:

- see your account details and collection counts;
- change your username;
- change your password. You stay logged in here, other browsers are logged out, and your API token is revoked, so get a new one for scripts;
- choose your **schedule country** (Discover's Airing This Week) and your **default collection order** (used when My Collection's URL has no `sort`);
- log out.

**Delete Account** is at the bottom, in the Danger Zone. It opens a separate confirmation page. You must enter your current password and type `DELETE` before the button turns on, and the server checks both again. Deleting removes your account, your collection entries (with their ratings, notes and progress) and your API token. Shows other people have saved, and other users' data, are not affected. It cannot be undone.

After pulling this branch, run `uv run python manage.py migrate` once: it adds the two preference fields.

### REST API

All endpoints are under `/api/` and require authentication, **except** the token endpoint.
Show data in responses comes from TVmaze (CC BY-SA 4.0).

- **Token (for scripts):** send your username and password once to get your token:

  ```
  curl -X POST http://127.0.0.1:8000/api/auth/token/ -H "Content-Type: application/json"        -d '{"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"}'
  ```

  Put the returned token in `.env` as `HTTPTV_API_TOKEN` (never commit it). Then send it as
  `Authorization: Token <your token>`.
- **Browser:** while logged in to the site, open http://127.0.0.1:8000/api/ to use DRF's
  browsable API with your session.

| Method and path | What it does |
|---|---|
| `GET /api/collection/` | list your entries (paginated: `count`, `next`, `previous`, `results`) |
| `GET /api/collection/<id>/` | one entry, with nested read-only `show` data |
| `POST /api/collection/` | add a show: body `{"tvmaze_id": 169}`. 201 with the new entry; 400 if it's already saved or TVmaze has no such ID; 503 if TVmaze is unavailable |
| `PATCH /api/collection/<id>/` | change any of `status`, `current_season`, `current_episode`, `rating`, `notes` |
| `PUT /api/collection/<id>/` | same as PATCH (all fields optional; omitted fields keep their values) |
| `DELETE /api/collection/<id>/` | remove the entry (204); the show stays for other users |

`id`, `show`, `created_at` and `updated_at` are read-only and ignored if sent. An entry's show
can't be changed (sending `tvmaze_id` on PATCH/PUT returns 400). Updates use the **same
validation and messages as the web form**, checked against the entry's final values. For
example, PATCHing only `{"current_season": 2}` onto an entry with no episode returns
`400 {"current_episode": ["Enter both a season and an episode, or leave both blank."]}`.

Another user's entry, or a missing ID, returns 404. Requests without credentials return 401.

#### Searching, filtering, sorting and paging the API

Add these to `GET /api/collection/` in any combination:

| Parameter | Example | Meaning |
|---|---|---|
| `search` | `search=goats` | show name **or notes** contain the text (the web page's `q` searches titles only) |
| `status` | `status=watching` | one of `plan_to_watch`, `watching`, `on_hold`, `completed`, `dropped` |
| `min_rating` | `min_rating=4` | your rating is at least this (1–5) |
| `genre` | `genre=comedy` | genres contain the text (case-insensitive) |
| `show_status` | `show_status=ended` | TVmaze status matches exactly (case-insensitive), e.g. Running, Ended |
| `network` | `network=hbo` | network or web channel name contains the text |
| `ordering` | `ordering=-rating` | `updated_at` (default `-updated_at`), `created_at`, `show__name`, `rating`, `show__premiered`, `show__tvmaze_rating`; prefix `-` for descending |
| `page`, `page_size` | `page=2&page_size=25` | 12 per page by default, at most 50 |

Unrated entries (and shows without a TVmaze rating or premiere date) always sort **last**, in
both directions. Invalid values such as `status=banana`, `min_rating=9` or `ordering=notes`
return 400 with a message. Example:

```
curl "http://127.0.0.1:8000/api/collection/?status=watching&min_rating=4&ordering=-rating"      -H "Authorization: Token $HTTPTV_API_TOKEN"
```

### Command-line client (`scripts/httptv_client.py`)

A small script that reads and updates **your** collection through the REST API. It needs the
server running and `HTTPTV_API_TOKEN` in `.env` (see "Token" above). `HTTPTV_API_URL` is
optional; the default is `http://127.0.0.1:8000/api/`.

```
uv run --env-file .env python scripts/httptv_client.py list --status watching --ordering -rating
uv run --env-file .env python scripts/httptv_client.py list --search office --page 2 --page-size 5
uv run --env-file .env python scripts/httptv_client.py update 2 --status on_hold --rating 4 --notes "Paused"
uv run --env-file .env python scripts/httptv_client.py update 2 --season none --episode none   # clear progress
uv run --env-file .env python scripts/httptv_client.py next 2      # Season 2, Episode 3 -> Season 2, Episode 4
```

- `list` prints a table plus `Page X of Y (N entries)`.
- `update` sends only the options you give; `none` clears season, episode or rating.
- `next` adds one to the episode. An entry with no progress starts at Season 1, Episode 1. It never changes the season or status.

Errors (server not running, bad token, unknown entry ID, a rejected value) print one clear message
to stderr and exit with code 1. Tests: `uv run pytest tests/test_httptv_client.py` (no server needed).

### Manual verification checklist

Automated tests mock every network call, so these checks use the real TVmaze API and a real
browser. Results from the last full run are in `docs/evidence-log.md` (V15).

1. **Fresh clone:** follow "First-time setup" in a new folder; `uv run pytest` passes.
2. **Accounts:** sign up, log out, log in; logged-out users are sent to log in for My Collection.
3. **Discover:** search `the office`, `café` (accented), and nonsense such as `zzqxjvk` (no-results message).
4. **Save:** save a show from Discover; saving it again says it's already saved.
5. **Show page:** backdrop or poster fallback, Where to Watch, View on TVmaze link, Extras (seasons and cast), Suggested.
6. **Tracking:** enter a season without an episode (error, nothing saved), then a valid update; delete asks to confirm.
7. **My Collection:** status chips with counts, title search, the three sorts, page 2.
8. **Home:** the continue-tracking hero and rows reflect your updates.
9. **API:** get a token; list, filter, order and page `/api/collection/`; browse `/api/` while logged in.
10. **Client:** `list`, `update` and `next`, plus a wrong token and a stopped server (clear error, exit code 1).
11. **verify_tvmaze.py:** `uv run python scripts/verify_tvmaze.py "café"`.
12. **Phone width:** pages at ~390 px wide have no sideways scrolling.
13. **Attribution:** every page footer credits TVmaze and CC BY-SA 4.0.

## Data source and license

Show information and images come from the [TVmaze API](https://www.tvmaze.com/api), licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). HTTP.tv credits TVmaze in the
footer of every page and links each show to its TVmaze page. HTTP.tv only tracks what you
watch; it doesn't stream video. Tracking values in screenshots and prototypes (statuses,
progress, ratings, notes) are invented sample data.
