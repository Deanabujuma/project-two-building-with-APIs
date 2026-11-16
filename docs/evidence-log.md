# HTTP.tv Evidence Log

Running record of real events, used for the Design Defense and `REFLECTION.md`. Entries are added **when they happen**, never reconstructed or invented.

**Privacy rule:** only the demo account (`demo_user`) and test data appear here. Never record API tokens (mask as `Token ****`), secret keys, passwords, email addresses or personal information.

Sections:
1. [Bugs and corrections](#1-bugs-and-corrections): before and after evidence (REFLECTION topic 5)
2. [Requests and responses](#2-requests-and-responses): real API traffic (REFLECTION topics 3–4)
3. [Screenshots](#3-screenshots): files in `docs/evidence/` (REFLECTION topic 2, Design Defense)
4. [Verification notes](#4-verification-notes): compatibility checks, manual test results

---

## 1. Bugs and corrections

### B1 — Prototype backdrop had the show title printed into the artwork (2026-11-15, design)
- **Before:** The first Direction D hero used Severance's first TVmaze "background" image. That image has "Severance" printed in large letters on the left, behind our own title text, so the two titles overlapped. Screenshot: `evidence/prototype-D-home-before-backdrop-fix.png`.
- **How found:** visual review of the headless-Edge screenshot of the prototype.
- **Investigation:** downloaded all 5 Severance backgrounds from `/shows/44933/images`. None is flagged `main`. Two (or more) have baked-in title text.
- **Fix:** switched the prototype to a clean backdrop (`…/397/992687.jpg`).
- **After:** `evidence/prototype-D-details-after-backdrop-fix.png`.
- **Lesson / design impact:** the production app can't hand-pick images. Decision 14 adopted an automatic rule (widest background ≥1920 px) and accepts baked-in text as a known limitation, softened by the dark gradient.

### B2 — Prototype showed made-up "streaming provider" tiles (2026-11-15, design)
- **Before:** the details page showed two dashed "Illustrative only · not real availability" provider tiles next to the verified network. Screenshot: `evidence/prototype-D-details-with-illustrative-providers.png`.
- **Why it was wrong:** TVmaze has no streaming-availability data, so even labelled placeholders suggested data HTTP.tv can't verify.
- **Fix (user refinement 1):** removed them. Where to Watch shows only the verified original network or web channel.
- **After:** `evidence/prototype-D-revised-abbott-tracking.png`.

### B3 — Hero backdrop showed thin borders baked into the image (2026-11-15, design)
- **Before:** the Abbott Elementary backdrop showed a dark strip on the left edge and a grey strip on the right, because the source image has thin borders.
- **Fix:** scaled the hero background layer by 4% (`transform: scale(1.04)`) so the borders fall outside the visible area.
- **After:** `evidence/prototype-D-revised-suggested.png` (no edge strips).

### B4 — PRD acceptance criterion contradicted the token endpoint (2026-11-15, PRD review)
- **Before:** AC33 said "Every API endpoint returns 401 or 403 without credentials".
- **Problem:** the token endpoint must accept anonymous requests, because that's how a client logs in.
- **Fix:** AC33 now covers collection endpoints and the API root, and names the token endpoint as the only open one.

### B5 — Logged-out home page linked to a login-only page (2026-11-15, PRD consistency check)
- **Before:** the PRD gave anonymous visitors a welcome hero with a Discover button, but Discover requires login, so a visitor would bounce straight to the login page.
- **Fix:** logged-out visitors get Sign up and Log in calls to action. Discover appears only for logged-in users with an empty collection (AC26 updated).

### B6 — Same-named search results couldn't be told apart (2026-11-15, Phase 3 manual test)
- **Before:** a real Discover search for "the office" returned five cards that all read "The Office · Not in your collection · Comedy" (US, UK, Indian, Indian Hindi-language and 1995 versions). Screenshot: `evidence/app-p3-discover-before-identity-fix.png`.
- **How found:** manual browser testing against live TVmaze. The mocked tests passed, because the sample data had different titles.
- **Fix:** the third caption line of an unsaved card now shows years and channel, falling back to genres. New filter `identity_line` with tests; PRD shared-card rule updated.
- **After:** "2005–2013 · NBC", "2001–2003 · BBC Two", "2024 · Prime Video", "2019 · JioHotstar"… Screenshot: `evidence/app-p3-discover-after-identity-fix.png`.
- **Lesson:** mocked data proves the code paths; only real data reveals what users actually see.

### B7 — Fallback poster hidden behind the summary panel (2026-11-15, Phase 4b manual test)
- **Before:** for a show with no backdrop ≥1920 px (The Naked Office, TVmaze 36116), the fallback poster was absolutely positioned at the hero's bottom right, the same spot as the details page's summary panel, so the panel covered most of it. Screenshot: `evidence/app-p4-poster-fallback-before-fix.png`. The prototype's "Missing backdrop" toggle has the same overlap; it had only been reviewed on the home hero.
- **How found:** saving a real show without a qualifying backdrop and looking at the page.
- **Fix:** on the details page the poster is now part of the right-hand column's normal layout, above the summary, so it can't overlap. It's hidden under the large breakpoint, where the blurred poster background remains. Two tests cover the fallback and backdrop cases.
- **After:** `evidence/app-p4-poster-fallback-after-fix.png`.

### B8 — Stray space before punctuation in summaries (2026-11-15, Phase 5 manual test)
- **Before:** the unsaved US *The Office* page (TVmaze 526) read "Steve Carell stars in The Office , a fresh and funny…". TVmaze's real HTML is `<p>Steve Carell stars in <b>The Office</b>, a fresh…`, and `strip_html` replaced *every* tag with a space. Screenshot: `evidence/app-p5-summary-spacing-before-fix.png`.
- **How found:** reading a live details page; the Phase 3 test used `<b>Mark</b> leads`, where a space follows the tag anyway.
- **Test first:** added `test_strip_html_does_not_add_space_before_punctuation_after_inline_tags`, using the real HTML. Result: `1 failed, 16 passed`.
- **Fix:** only block tags (`p`, `br`, `div`, `li`, `ul`, `ol`, `h1`–`h6`) become spaces; inline tags are removed with nothing in their place. Result: `203 passed`.
- **Side bug while fixing:** a shell-quoted edit wrote the regex's word boundary `\b` as a literal backspace character (byte `0x08`), so block tags stopped matching ("First.Second.Linebreakend"). It was caught by the existing tests (2 failed) and replaced with the lookahead `(?=[\s/>])`.
- **After:** "Steve Carell stars in The Office, a fresh…" (`evidence/app-p5-unsaved-show-after-fix.png`).

### B9 — Extras accepted a response that wasn't a show (2026-11-15, Phase 5 automated test)
- **Before:** if TVmaze returned JSON that wasn't a show object (e.g. `{"not": "a list"}`), `get_extras` showed "No seasons / No cast" as if the show had none.
- **How found:** the shared failure test cases, run against the Extras tab (`1 failed, 200 passed`).
- **Fix:** `get_extras` now requires a show object with an `id`, and otherwise raises the same "couldn't read" error as other calls. Result: `201 passed`.

### B10 — Database rule let "season only" rows in (2026-11-15, Phase 6, caught by a test written first)
- **Before:** the first version of the progress check constraint was `(season IS NULL AND episode IS NULL) OR (season >= 1 AND episode >= 1)`. The TDD test `test_database_constraints_block_invalid_rows_that_skip_validation` failed for `{season: 2, episode: NULL}` and `{season: NULL, episode: 2}`: `2 failed, 239 passed`.
- **Why:** in SQL, `NULL >= 1` is *unknown*, so the condition became `FALSE OR UNKNOWN` = unknown, and a CHECK constraint **passes** when its result is unknown.
- **Fix:** the "started" branch now also requires `season IS NOT NULL AND episode IS NOT NULL`. The migration was regenerated before it was ever applied. Result: `241 passed`.

### B11 — The same error message appeared twice (2026-11-15, Phase 6)
- **Before:** posting Season `0` or Rating `9` showed "Season must be a whole number of 1 or more." twice. The new test `test_each_error_message_appears_once` failed (`2 failed, 267 passed`).
- **Wrong first guess:** I assumed the form field and the model were both reporting it, and added a filter for that case. The test still failed. Inspecting `form.errors.as_data()` showed the field accepted `0`. Both copies came from the model stage: a `MinValueValidator(1)` on the field *and* the shared `validate_tracking` rule.
- **Fix:** removed the duplicate range validators from the model fields, so the shared rules (plus the database constraints) are the single source. The filter is kept for a related case: a rejected Season no longer also triggers a misleading "enter both" error on Episode (`test_rejected_season_does_not_also_claim_episode_is_missing`). Result: `270 passed`.
- **Lesson:** inspect the actual data before fixing; my first fix addressed a cause that wasn't there.

### B12 — API and web form disagreed on two error messages (2026-11-15, Phase 10, found by a parity test)
- **Before:** the first parity test only checked that both reject each case. A stricter test comparing the exact messages, `test_api_and_web_messages_match_for_every_case`, failed for "notes too long": the API said "(you entered 2,001)", the web form "(you entered 2001)". (Text input like "two" also differed until the serializer was given the shared wording.)
- **Cause:** the web form's built-in length check ran before the shared rule and used its own formatting.
- **Fix:** removed the form's duplicate length check; the shared rule produces the message in both places. The textarea's `maxlength` attribute still limits typing. Result: `1 failed, 396 passed` → `397 passed`.

### B13 — The client rejected `--ordering -rating` (2026-11-15, Phase 12, found by a test)
- **Before:** `test_list_sends_token_and_parameters_and_prints_table` failed with `argparse.ArgumentError: argument --ordering: expected one argument`. argparse treats a value that starts with `-` as a new option.
- **Choice:** changing the test to `--ordering=-rating` would have hidden the problem, because descending sorts are exactly the ones people type with a minus. The client now joins `--ordering <value>` before parsing, so both forms work.

---

## 2. Requests and responses

Captured from the running dev server (`127.0.0.1:8000`) as `demo_user`. Tokens are shown as `****`; passwords are never recorded.

### R1 — No credentials → 401 (2026-11-15, Phase 9)
```
$ curl -i http://127.0.0.1:8000/api/collection/
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Token
{"detail":"Authentication credentials were not provided."}
```

### R2 — Getting a token (2026-11-15, Phase 9)
```
$ curl -X POST http://127.0.0.1:8000/api/auth/token/ -H "Content-Type: application/json"        -d '{"username": "demo_user", "password": "****"}'
{"token":"****"}          (a 40-character key, saved only in the Git-ignored .env as HTTPTV_API_TOKEN)
```

### R3 — Authenticated list, two per page (2026-11-15, Phase 9)
```
$ curl -i "http://127.0.0.1:8000/api/collection/?page_size=2" -H "Authorization: Token ****"
HTTP/1.1 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json

{"count":19,"next":"http://127.0.0.1:8000/api/collection/?page=2&page_size=2","previous":null,
 "results":[{"id":17,"show":{"tvmaze_id":179,"name":"The Wire","tvmaze_url":"https://www.tvmaze.com/shows/179/the-wire",
   ...,"network":"HBO","channel_type":"network","channel_country":"United States","runtime":60,"tvmaze_rating":"8.9",...},
   "status":"completed","current_season":5,"current_episode":10,"rating":4,"notes":"", "created_at":"...","updated_at":"..."}, ...]}
```
(Show summary and timestamps shortened with `...`. `Allow: GET, HEAD, OPTIONS` shows the read-only Phase 9 endpoint.)

### R4–R9 — Create, validate, update, delete (2026-11-15, Phase 10)
All requests are sent with `-H "Authorization: Token ****" -H "Content-Type: application/json"` to `http://127.0.0.1:8000/api/collection/`.
```
POST   {"tvmaze_id": 6508}                 -> 201 Created, Location: .../api/collection/20/
                                              show "Atlanta" (FX, fetched from TVmaze), status plan_to_watch, progress null/null
POST   {"tvmaze_id": 6508}  (again)        -> 400 {"tvmaze_id":["Atlanta is already in your collection."]}
PATCH  20/ {"current_season": 2}           -> 400 {"current_episode":["Enter both a season and an episode, or leave both blank."]}
PATCH  20/ {"status":"watching","current_season":1,"current_episode":3,"rating":4}
                                           -> 200, entry 20: Atlanta watching 1 3 4
POST   {"tvmaze_id": 999999999}            -> 400 {"tvmaze_id":["TVmaze has no show with that ID."]}
DELETE 20/                                 -> 204 No Content
GET    20/                                 -> 404 {"detail":"No CollectionEntry matches the given query."}
```
The season-only PATCH shows the merged-values check: the request sent no episode, the saved entry had none, so the final state would break the rule.

### R10–R16 — Search, filters, ordering, pages, invalid values (2026-11-15, Phase 11)
`GET http://127.0.0.1:8000/api/collection/?…` with `Authorization: Token ****` (19 entries; output trimmed to id, name, status, rating):
```
?search=breaking                      -> 200 count=1:  4 Breaking Bad | watching | 5
?status=watching&min_rating=4         -> 200 count=3:  10 Ted Lasso 4 · 4 Breaking Bad 5 · 2 Severance 4
?ordering=rating                      -> 200 count=19, page 1 of 2 (12):
      Chernobyl 1, Succession 2, The Bear 3, Better Call Saul 4, Severance 4, Ted Lasso 4, The Wire 4,
      Breaking Bad 5, Shōgun 5, The Office 5, Abbott Elementary None, Andor None      <- unrated LAST even ascending
?ordering=-rating&page_size=5&page=2  -> 200 count=19
      next=…?ordering=-rating&page=3&page_size=5   previous=…?ordering=-rating&page_size=5
      Ted Lasso 4, The Wire 4, The Bear 3, Succession 2, Chernobyl 1
?status=banana                        -> 400 {"status": ["Select a valid choice. banana is not one of the available choices."]}
?min_rating=9                         -> 400 {"min_rating": ["Ensure this value is less than or equal to 5."]}
?ordering=notes                       -> 400 {"ordering": ["Unknown ordering 'notes'. Choose from: created_at, rating, show__name,
                                              show__premiered, show__tvmaze_rating, updated_at."]}
```
Ties (several 4-star shows) are broken by show name, the same rule the web page uses.

### R17 — The command-line client against the live server (2026-11-15, Phase 12)
`C="uv run --env-file .env python scripts/httptv_client.py"` (token read from the Git-ignored `.env`):
```
$ $C list --status watching --ordering -rating
   ID  Show                              Status         Progress                Rating
    4  Breaking Bad                      watching       Season 2, Episode 4     5/5
    2  Severance                         watching       Season 2, Episode 3     4/5
   10  Ted Lasso                         watching       Season 1, Episode 6     4/5
   14  Dark                              watching       Season 3, Episode 2     Not rated
    6  Stranger Things                   watching       Season 4, Episode 8     Not rated

Page 1 of 1 (5 entries)                                            [exit 0]
$ $C next 2
Severance: Season 2, Episode 3 -> Season 2, Episode 4             [exit 0]
$ $C update 2 --season 3
Updated entry 2: Severance | watching | Season 3, Episode 4 | 4/5   [exit 0]
$ $C update 2 --rating 9
Error: HTTP.tv refused the change:
  rating: Rating must be a whole number from 1 to 5, or blank.     [exit 1]
$ $C next 999
Error: No entry with ID 999 in your collection.                   [exit 1]
$ HTTPTV_API_TOKEN=wrong ... list
Error: HTTP.tv rejected your token (HTTP 401). Check HTTPTV_API_TOKEN in .env.   [exit 1]
$ HTTPTV_API_URL=http://127.0.0.1:8999/api/ $C list    (nothing listening there)
Error: Could not connect to HTTP.tv at http://127.0.0.1:8999/api/. Is the server running?   [exit 1]
```
Afterwards, `update 2 --season 2 --episode 3` restored the sample entry.

### R18 — The server's side of R17 (dev-server log, 2026-11-15)
The Django dev server's request log at the moment R17 ran (copied from the server's console output):
```
[15/Nov/2026 17:29:25] "GET /api/collection/2/ HTTP/1.1" 200 1164       <- next 2: read the entry
[15/Nov/2026 17:29:25] "PATCH /api/collection/2/ HTTP/1.1" 200 1164     <- next 2: send {"current_episode": 4}
[15/Nov/2026 17:29:25] "PATCH /api/collection/2/ HTTP/1.1" 200 1164     <- update 2 --season 3
Bad Request: /api/collection/2/
[15/Nov/2026 17:29:26] "PATCH /api/collection/2/ HTTP/1.1" 400 67       <- update 2 --rating 9 (the 67-byte rating error)
```
`next` makes two requests (GET, then PATCH), and the rejected update reached the server and was refused there, not by the client.

---

## 3. Screenshots

All taken with headless Microsoft Edge from `prototypes/` during the 2026-11-15 design session.

| File | Shows |
|---|---|
| `evidence/prototype-v1-A-poster-grid.png` | v1 variant A: light poster grid |
| `evidence/prototype-v1-B-dense-table.png` | v1 variant B: dark sidebar and dense table |
| `evidence/prototype-v1-C-list-detail.png` | v1 variant C: library list and detail panel |
| `evidence/prototype-D-home-before-backdrop-fix.png` | Direction D, first build: backdrop title clash (B1 before) |
| `evidence/prototype-D-details-with-illustrative-providers.png` | Direction D details with illustrative providers (B2 before) |
| `evidence/prototype-D-details-after-backdrop-fix.png` | Clean backdrop, tracking form before the width refinement |
| `evidence/prototype-D-revised-abbott-tracking.png` | Revised: verified-only Where to Watch, three-panel tracking |
| `evidence/prototype-D-revised-home-rows.png` | Revised: consistent rows and captions |
| `evidence/prototype-D-revised-suggested.png` | Revised: Suggested row, flags only on saved shows |
| `evidence/prototype-D-revised-collection.png` | Revised: My Collection grid |
| `evidence/prototype-D-revised-discover.png` | Revised: Discover results with saved and unsaved states |
| `evidence/app-p2-home-public.png` | Built app: logged-out home with Sign up and Log in |
| `evidence/app-p2-signup.png` | Built app: sign-up page |
| `evidence/app-p2-home-public-phone.png` | Built app: logged-out home at phone width |
| `evidence/app-p2-home-logged-in.png` | Built app: logged-in nav, empty-collection welcome |
| `evidence/app-p2-home-logged-in-phone.png` | Built app: icon-only nav at phone width |
| `evidence/app-p3-discover-before-identity-fix.png` | Discover "the office": identical captions (B6 before) |
| `evidence/app-p3-discover-after-identity-fix.png` | Discover "the office": years · channel captions (B6 after) |
| `evidence/app-p3-discover-phone.png` | Discover "severance" at phone width |
| `evidence/app-p4-abbott-saved.png` | Saved Abbott Elementary: network, backdrop, flash message |
| `evidence/app-p4-severance-baked-title.png` | Severance: the automatic backdrop has the title printed in the art (known limitation) |
| `evidence/app-p4-severance-phone.png` | Severance details stacked at phone width |
| `evidence/app-p4-poster-fallback-before-fix.png` | No-backdrop show: poster covered by the summary (B7 before) |
| `evidence/app-p4-poster-fallback-after-fix.png` | No-backdrop show: poster above the summary (B7 after) |
| `evidence/app-p5-abbott-extras.png` | Abbott Elementary Extras: 6 seasons and 7 cast from live TVmaze |
| `evidence/app-p5-abbott-extras-phone.png` | Extras at phone width |
| `evidence/app-p5-suggested-empty.png` | Severance Suggested: honest label, empty state (no other matching shows saved yet) |
| `evidence/app-p5-summary-spacing-before-fix.png` | Unsaved The Office: "The Office , a" (B8 before) |
| `evidence/app-p5-unsaved-show-after-fix.png` | Unsaved The Office, live and not saved: fixed summary (B8 after) |
| `evidence/app-p6-tracking-error.png` | Tracking: season without episode rejected, input kept, header unchanged |
| `evidence/app-p6-tracking-saved.png` | Tracking saved: Watching · Season 2, Episode 3, 4 of 5, notes |
| `evidence/app-p6-delete-confirm.png` | Remove confirmation page |
| `evidence/app-p6-tracking-phone.png` | Tracking panels stacked at phone width |
| `evidence/app-p7-collection.png` | My Collection: 19 real shows, chips with counts, stars |
| `evidence/app-p7-collection-page2.png` | Page 2 of 2 (12 per page) |
| `evidence/app-p7-watching.png` | Watching nav link: filtered page with its own title |
| `evidence/app-p7-no-match.png` | `q=goats`: title-only search, no-match state with Clear filters |
| `evidence/app-p7-collection-phone.png` | Collection at phone width; chips scroll inside their row |
| `evidence/app-p8-home.png` | Personalized home: featured hero (Dark) and four rows with consistent cards |
| `evidence/app-p8-home-phone.png` | Home at phone width |
| `evidence/app-p9-api-root.png` | Browsable API root (logged-in session) |
| `evidence/app-p9-api-collection.png` | Browsable API collection list, paginated |
| `evidence/app-p11-api-browsable-filters.png` | Browsable API with the Filters button (status=watching, ordering=-rating) |
| `evidence/app-p13-fresh-home-empty.png` | Fresh clone: new user's home right after sign-up |
| `evidence/app-p13-fresh-collection.png` | Fresh clone: collection after saving and tracking one show |
| `evidence/app-p13-discover-cafe.png` | Real search for "café" (accented characters) |
| `evidence/app-p13-discover-no-results.png` | Real search with no results |
| `evidence/app-p13-phone-home.png` | Final phone-width home |
| `evidence/app-p13-phone-discover.png` | Final phone-width Discover |
| `evidence/app-p13-phone-collection.png` | Final phone-width collection |

---

## 4. Verification notes

### V0 — Baseline before Django work (2026-11-15, Phase 0)
- `uv run pytest -q` → `44 passed in 0.12s` (TVmaze verification script tests only).

### V1 — Package compatibility check (2026-11-15, Phase 1)
Source: each package's official PyPI metadata (`https://pypi.org/pypi/<package>/json`), checked before installing.

| Package | Version | `requires_python` | Python classifiers | Django classifiers |
|---|---|---|---|---|
| Django | 6.1.3 (2026-11-03) | >=3.12 | 3.12, 3.13, 3.14, 3.15 | — |
| djangorestframework | 3.18.3 (2026-10-06) | >=3.10 | 3.10–3.15 | 5.2, 6.0, 6.1 |
| django-filter | 26.2 (2026-10-03) | >=3.11 | 3.11–3.15 | 5.2, 6.0, 6.1 |
| pytest-django | 4.14.0 (2026-08-10) | >=3.10 | 3.10–3.14 | 5.2, 6.0 |

- **Result:** all four support the project's `requires-python >=3.12` and local Python 3.14.
- **Caveat:** pytest-django's classifiers stop at Django 6.0. That's packaging metadata, not a declared incompatibility. It was resolved by running the real suite on Django 6.1.3 (see V2). Fallback if it had failed: Django 6.0.
- **Supporting evidence:** the student's Project #1 (Applicant-Tracking-System) already runs Django 6.1 with pytest-django 4.14.

### V2 — Foundation verified (2026-11-15, Phase 1)
- The custom `accounts.User` was set as `AUTH_USER_MODEL` before the first `migrate`. `accounts/migrations/0001_initial.py` was created, and no migration references `auth.User`.
- `uv run pytest -q` → `50 passed` (44 original + 6 new setup tests), without `.env`.
- `manage.py check` → "System check identified no issues". Dev server: `/admin/login/` → HTTP 200.
- `git status` confirms `.env` and `db.sqlite3` are ignored.

### V3 — Public shell and accounts (2026-11-15, Phase 2)
- `uv run pytest -q` → `76 passed` (44 original + 32 new).
- Browser check (headless Edge driven by Playwright, `demo_user` test account) at 1440×900 and 390×844: no horizontal overflow on any page. The only console error was a `/favicon.ico` 404, fixed by adding an inline SVG icon to the base template.
- Screenshots: `evidence/app-p2-home-public.png`, `app-p2-signup.png`, `app-p2-home-public-phone.png`, `app-p2-home-logged-in.png`, `app-p2-home-logged-in-phone.png`.

### V4 — TVmaze client and Discover (2026-11-15, Phase 3)
- `uv run pytest -q` → `114 passed` (44 original + 70 new). Every failure type (timeout, connection, 429, 5xx, other HTTP, invalid JSON, unexpected shape) is tested for the client and the page.
- Real searches through the running app against live TVmaze:
  - "the office" → 10 results (the maximum);
  - "xqzzvvnotashow" → "No shows found";
  - "café" → 10 results (accented input is URL-encoded correctly);
  - "   " → guidance with no TVmaze call.
- `git diff scripts/verify_tvmaze.py tests/test_verify_tvmaze.py` → empty (unchanged).

### V5 — Data models (2026-11-15, Phase 4a)
- `makemigrations shows` → `0001_initial` (Show, CollectionEntry); `migrate` applied cleanly. pytest also builds its test database from the migrations on every run.
- `uv run pytest -q` → `126 passed`: defaults, the unique (user, show) constraint, unique `tvmaze_id`, cascade on user delete, protect on show delete, and admin list/add/search pages.

### V6 — Secure save flow with real TVmaze data (2026-11-15, Phase 4b)
- `uv run pytest -q` → `167 passed`.
- Saved three real shows from Discover with the `+` button, as `demo_user`. Rows stored (checked in the Django shell):

  | TVmaze ID | Show | `network` | `channel_type` | `channel_country` | Backdrop |
  |---|---|---|---|---|---|
  | 55350 | Abbott Elementary | ABC | network | United States | `original_untouched/381/953579.jpg` |
  | 44933 | Severance | Apple TV | web channel | (blank) | `original_untouched/384/960581.jpg` |
  | 36116 | The Naked Office | Channel One | network | United Kingdom | none (poster fallback) |

- **Known limitation confirmed:** the automatic rule picked a Severance backdrop with "Severance" printed in the artwork (`evidence/app-p4-severance-baked-title.png`), as predicted in B1 and accepted in design decision 14.
- Discover then showed Severance's card as "Plan to Watch · Not started" with the green check instead of `+`.

### V7 — Complete details page (2026-11-15, Phase 5)
- `uv run pytest -q` → `204 passed`.
- **Live checks:**
  - Abbott Elementary Extras showed 6 seasons (13/22/14/22/22/22 episodes) and the cast (Quinta Brunson as Janine Teagues, …).
  - The unsaved *The Office* (526) displayed from live TVmaze, with **Add to my collection**. The `Show` count stayed at 3 afterwards, so viewing didn't save it.
  - `/shows/999999999/` → 404.
- **AC21 (manual):** the details layout matches the approved prototype: metadata on the left, summary on the right at 1440 px, stacked at 390 px, and the poster fallback (see B7).

### V8 — Tracking and delete (2026-11-15, Phase 6)
- **TDD:** `shows/tests/test_validation.py` was written before `shows/validation.py` existed (collection error → red), then the shared rules were implemented (green), and the tests then caught B10.
- `uv run pytest -q` → `270 passed`.
- **Browser (demo_user, Severance):**
  - Season 2 with a blank Episode → "Enter both a season and an episode, or leave both blank." (HTTP 400), input kept;
  - then Episode 3 and 4 stars → "Saved your tracking for Severance.", header "Watching · Season 2, Episode 3";
  - Remove → confirmation page; nothing deleted on GET.
- While scripting the browser check, clicking the hidden radio input itself failed (the 1 px inputs were stacked on top of each other). Real users click the star labels. The inputs are now anchored inside the star group with `pointer-events: none`.

### V9 — My Collection with shared query logic (2026-11-15, Phase 7)
- **TDD:** `shows/tests/test_queries.py` was written before `shows/queries.py` existed (collection error → red), then implemented (`18 passed`). It covers unrated-last for `rating` **and** `-rating`, and missing values last for TVmaze rating and premiere date in both directions, case-insensitive titles, stable tie-breaks, and rejection of unknown ordering fields.
- **Small decision beyond the PRD:** missing premiere dates also sort last in both directions (the PRD named only the two rating fields).
- `uv run pytest -q` → `308 passed`.
- **Demo data:** 16 more real shows were saved through the real save service (live TVmaze, paced at 0.6 s per call). Their tracking values were then set by hand for the demo account. That data is invented sample data in the Git-ignored local database.
- **Browser:**
  - chips All 19 / Plan to Watch 5 / Watching 5 / On Hold 2 / Completed 5 / Dropped 2;
  - pages 1–2;
  - `sort=-rating` lists 5-star shows first and unrated last;
  - `status=watching` shows the "Watching" title;
  - `q=goats` → "No shows match" (titles only).

### V10 — Personalized home page (2026-11-15, Phase 8)
- `uv run pytest -q` → `318 passed`.
- **One test-setup mistake:** my rendering test assumed the first-saved Watching entry would be featured, but the most recently *updated* one (saved last) correctly was. The template was right; the test setup was fixed by updating the intended entry first.
- **AC32 (manual):** across all four rows, Discover, Suggested and the collection grid, cards share the 20 px gap, the 4% hover, and the title / status / "Season X, Episode Y" caption. Check marks appear only in mixed rows (Discover, Suggested).

### V11 — API authentication and read access (2026-11-15, Phase 9)
- `uv run pytest -q` → `338 passed`.
- Pagination (`count`/`next`/`previous`/`results`, 12 by default, max 50) was switched on in this phase rather than Phase 11, so the list format never changes for clients. Phase 11 tests the size rules.
- Real requests R1–R3 above; browsable API checked in a logged-in browser.

### V12 — API create/update/delete (2026-11-15, Phase 10)
- **TDD:** `shows/tests/test_api_write.py` was written first, against the read-only API (`38 failed, 11 passed`; the passing ones were mostly the web-form half of the parity checks). Then the serializer and viewset were implemented: `387 passed`. The parity work then reached `397 passed`.
- The parity tests run the same 10 invalid cases (AC23) against **both** the web form and the API, comparing the field, the status code (400 for both), that nothing was saved, and the exact message.
- **Decision:** `PUT` behaves like `PATCH` (every field optional; omitted fields keep their saved values), because all writable fields are optional in the model. Documented in the README.

### V13 — API search, filters, ordering, pagination (2026-11-15, Phase 11)
- **TDD:** `shows/tests/test_api_query.py` was written first (`43 failed, 8 passed`), then the filters, search and shared ordering were added: `449 passed`.
- **Test mistakes I made and fixed** (the code was right both times):
  - a pagination assertion mixed `and`/`or` and could pass for the wrong reason; it was rewritten before implementing;
  - a combined-filter case expected "Dark" for `search=e`, but "Dark" has no "e".
- **AC43:** a parametrized test compares the web page and the API for 4 status values × 3 equivalent sorts (12 combinations); they return identical lists.
- **Decision:** an unknown `ordering` returns 400 (DRF's default silently ignores it), matching the strict filters.
- **AC44 (manual):** the browsable API's Filters form lists status, minimum rating, genre, show status, network, search and ordering.

### V14 — Command-line client (2026-11-15, Phase 12)
- `tests/test_httptv_client.py` (23 tests, all HTTP mocked) was written before `scripts/httptv_client.py`.
- **TDD for `next`:** `list` and `update` were built first. With them in place, only the four `next` tests failed (`4 failed, 19 passed`). After adding `next`: `472 passed`.
- **`next` rule:** episode + 1; season and status never change; "Not started" becomes Season 1, Episode 1. Moving to a new season is left to `update --season N --episode 1`, because the API doesn't know how many episodes a season has.
- Real run R17 above; error messages go to stderr with exit code 1.

### V15 — Fresh clone and full manual checklist (2026-11-15, Phase 13)
- **AC3 audit:** `git ls-files` lists no `.env`, database, token or secret key. The only passwords in tracked files are throwaway test-fixture values and the `.env.example` placeholder. A search of every commit found neither the real API token nor the real secret key.
- **AC1 fresh clone:** cloned into a temporary folder and followed the README exactly (`uv sync`, copy `.env.example`, generate a key, `migrate`, `check`, `runserver` on port 8001): `472 passed` in the clone. `scripts/verify_tvmaze.py` and `tests/test_verify_tvmaze.py` are unchanged since before the Django work.
- **New-user journey on the empty clone database:**
  - sign up → welcome home;
  - search "severance" → save ("Saved Severance to your collection as Plan to Watch.");
  - track Watching, S1E4, 5 stars, notes → collection shows 1 entry → the home hero switches to "Continue tracking · Season 1, Episode 4".
- **API on the clone:**
  - got a token; `POST {"tvmaze_id": 169}` → 201;
  - client `next` → "Breaking Bad: Not started -> Season 1, Episode 1";
  - `update --status watching --rating 5`; `list` shows both entries.
  - *My mistake while testing:* my first curl used `.../api//collection/` (a double slash), which returned 404. The correct URL worked. The client itself strips a trailing slash from `HTTPTV_API_URL`, so it can't make this mistake.
- **Manual checklist (README items 2–13, dev server, `demo_user`):**

| Check | Result |
|---|---|
| Discover "café" | 10 results, first "Café · 1994–1995 · RCN Televisión" |
| Discover "zzqxjvk" | No shows found for "zzqxjvk" + spelling hint |
| Footer on home, Discover, results, collection, show tabs, delete confirm, login, sign-up | TVmaze + CC BY-SA 4.0 on all |
| Show page TVmaze link | "View on TVmaze" → show's TVmaze page |
| Tracking: season 3, blank episode | 400, "Enter both a season and an episode, or leave both blank."; saved S2E3 unchanged |
| Phone width (390 px): home, Discover, tracking, collection | no horizontal overflow |
| `verify_tvmaze.py "café"` | Found 10 shows, exit 0 |
| Client `list`/`update`/`next` + errors | see R17 |

- **Gap found and closed (AC50 is marked T/M):** no automated test checked the attribution footer.
  - Added `shows/tests/test_attribution.py` (13 tests): every page type, including the custom 404 and the 503 "show unavailable" page, plus the show's own TVmaze link.
  - My first version expected `https://www.tvmaze.com/` with a trailing slash; the footer uses no slash, so the test was corrected, not the page.
  - Result: `485 passed`.
- **Note:** with `DJANGO_DEBUG=true` (local development), an unknown URL shows Django's yellow debug 404 page rather than the custom `404.html`. That's standard Django behaviour; the test above checks the custom page with debug off.

### V16 — PRD acceptance-criteria audit before pushing (2026-11-15, after Phase 13)
Every one of the 57 criteria in `prd/httptv.md` (AC1–AC54, with AC5a, AC5b and AC15a) was checked against a test or recorded evidence:

| Kind | Criteria | Where |
|---|---|---|
| Tests (T) | AC2, AC4–AC20, AC23–AC31, AC33–AC43, AC45–AC48, AC52, AC53 | test files (most name their AC in the test or docstring); `uv run pytest` → `485 passed` |
| Test + manual (T/M) | AC22, AC50 | `test_show_detail.py` (no invented providers, ratings or badges); `test_attribution.py`; V15 |
| Manual (M) | AC1, AC3 | V15 (fresh clone, `git ls-files` audit) |
| Manual (M) | AC21, AC32 | V4–V8 screenshots; Design Defense table below |
| Manual (M) | AC44 | V13, `app-p11-api-browsable-filters.png` |
| Manual (M) | AC49 | R17, plus the web check below |
| Manual (M) | AC51 | README sections listed in Phase 13 |
| Manual (M) | AC54 | REFLECTION.md, Phase 14 (pending your review) |

- **AC49, completed now:** R17 showed the client's own output but hadn't checked the web app.
  - `next 2` → "Season 2, Episode 3 -> Season 2, Episode 4"; `update 2 --notes "Changed from the command-line client."`.
  - In the browser, My Collection then showed "Severance · Watching · Season 2, Episode 4", and the tracking form's notes counter read "37 / 2,000", the length of that note.
  - The sample entry was restored afterwards.
- **Interpretation to note:** AC45 asks for a "numbered table". The client's table is numbered by entry **ID** (the number `update` and `next` take) rather than a 1, 2, 3 row count, so the number you see is the one you type next.

## 5. Design Defense: prototype → built app

| View | Prototype | Built app |
|---|---|---|
| First layouts considered | `prototype-v1-A-poster-grid.png`, `prototype-v1-B-dense-table.png`, `prototype-v1-C-list-detail.png` | Direction D chosen (cinematic, poster-led) |
| Home | `prototype-D-revised-home-rows.png` | `app-p8-home.png`, `app-p8-home-phone.png`, `app-p13-fresh-home-empty.png` |
| Discover | `prototype-D-revised-discover.png` | `app-p3-discover-after-identity-fix.png` (B6), `app-p13-discover-cafe.png` |
| Show page + tracking | `prototype-D-revised-abbott-tracking.png`, `prototype-D-details-after-backdrop-fix.png` | `app-p4-abbott-saved.png`, `app-p6-tracking-saved.png`, `app-p6-tracking-error.png` |
| Suggested / Extras | `prototype-D-revised-suggested.png` | `app-p5-suggested-empty.png`, `app-p5-abbott-extras.png` |
| My Collection | `prototype-D-revised-collection.png` | `app-p7-collection.png`, `app-p7-collection-phone.png` |
| Where to Watch | `prototype-D-details-with-illustrative-providers.png` (invented streaming providers) | Only the network or web channel TVmaze reports, labelled "verified by TVmaze", plus a link to TVmaze |
| API | (no prototype) | `app-p9-api-root.png`, `app-p11-api-browsable-filters.png` |

All files are in `docs/evidence/`.

---

## 6. Post-submission improvements (after the `project2-submission` tag)

These entries are for work on the `post-submission-improvements` branch. Sections 1–5
describe the submitted project.

### P1 — Discover browsing rows (2026-11-15, Phase A)
- **Live TVmaze probes before designing** (one request each):
  - `/schedule?country=US` (today) returned 57 episodes from 56 shows (131 KB). Only 28 of those shows had genres and 27 had a rating. Every show had a portrait poster and none had a landscape image.
  - `/schedule/web?country=US` returned 4 items, while `/schedule/web` without a country returned 76. Global streamers have no country, so the app filters by country itself.
  - Web schedule entries put the show under `_embedded.show`; network entries put it under `show`.
- **Constraint found in the existing tests:** `test_first_visit_makes_no_tvmaze_call` and the AC8 blank-search test require `/discover/` itself to make no TVmaze calls. Rather than edit them, the rows load from `/discover/browse/?partial=1`; all 485 original tests pass unchanged.
- **Tests:** `shows/tests/test_discover_browse.py` (34 tests, using a URL-routing fake TVmaze). `uv run pytest -q` → `519 passed`.
- **Test mistakes I made (the code was right):**
  - a test looked for `data-browse-slot` anywhere in the page and found it inside the script text;
  - an "escaping" test used the genre `<b>x</b>`, whose `/` splits the URL, so the page was a correct 404.
- **Found in the live browser check and fixed:**
  - Browse by Genre listed 33 real genres in five rows (a very long column on a phone). It's now a two-row strip that scrolls sideways.
  - Airing This Week opened with obscure foreign streaming titles, because entries without an air time sorted first. Each day is now ordered by TVmaze rating (unrated last), and the row says so. A test was added.
  - On phones, row subtitles squeezed beside the titles; they now wrap underneath.
- **Live result (demo_user):**
  - Featured: Dexter: Resurrection 8.4, Gold Rush 8.1, MobLand 8.1, …, with real backdrops (some have the title printed in the artwork, the known limitation from B1);
  - the genre tiles start Drama 94, Comedy 60, Crime 47;
  - Airing This Week starts The Simpsons (Today · 20:30 · S38 E7), Last Week Tonight, The Gilded Age;
  - Recommended starts Elsbeth, Furia, The Lowdown, Tulsa King;
  - `/discover/genre/Comedy/` lists 54 shows airing this week;
  - no horizontal overflow at 1440 px or 390 px.
- **Screenshots:** `evidence/post-discover-desktop.png`, `post-discover-desktop-full.png`, `post-discover-phone.png`, `post-discover-genre.png`, `post-discover-genre-phone.png`.

### P2 — Profile & Settings and Delete Account (2026-11-15, Phase B)
- **Database:** migration `accounts/0002_profile_preferences` adds `schedule_country` (default `US`) and `default_collection_sort` (default `-updated`). `sqlmigrate` shows SQLite's usual table rebuild, filling the defaults for existing users. demo_user's 19 entries were unchanged afterwards.
- **Tests:** `accounts/tests/test_profile.py` has 32 tests. `uv run pytest -q` → `551 passed` (485 original + 34 Discover + 32 Profile).
- **Test mistakes I made:** my fixture used a rating of 8 and a status of `planned`. HTTP.tv's database checks (ratings 1–5; status `plan_to_watch`) rejected them, which shows those checks work.
- **Live browser check (desktop 1440 px and phone 390 px):**
  - The profile page showed all panels with the Danger Zone last, and demo_user's real counts (19 saved: 5 Plan to Watch, 5 Watching, 2 On Hold, 5 Completed, 2 Dropped).
  - The delete flow used a temporary `throwaway_user` with 2 entries, never demo_user:
    - a wrong password returned `POST /accounts/delete/ 400` and showed "That password is incorrect.", and the account remained;
    - the correct password returned `302`, the user was logged out, and the home page showed "Your account has been permanently deleted.";
    - after the run: throwaway_user gone, entries 21 → 19, Show rows still 20, demo_user still 19 entries.
  - A button-state probe on demo_user's page (never submitted) found the button disabled when empty, with only a password, and with lowercase `delete`; enabled with both fields filled; disabled again when the password was cleared.
- **Found while checking and fixed:**
  - The browser required exactly `DELETE` while the server ignored surrounding spaces; the browser now trims too, so both agree. A test was added.
  - Django's password form autofocuses "Old password", which made the settings page jump to that box. Autofocus was removed and a test added.
  - The delete button faded in over 0.15 s, which looked disabled in a screenshot; the danger button now changes instantly.
  - The Cancel button wrapped under the delete button; the card was widened.
- **Screenshots:** `evidence/post-profile-desktop.png`, `post-profile-phone.png`, `post-delete-ready.png`, `post-delete-wrong-password.png`, `post-delete-done.png`, `post-delete-phone.png`.
