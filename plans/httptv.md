# Plan: HTTP.tv — TV Show Discovery and Tracking

> Source PRD: `prd/httptv.md` (approved 2026-11-15). User stories (US) and acceptance criteria (AC) below use that PRD's numbering.
> Visual reference: `prototypes/ui-convention.html` (Direction D, approved). Design history: `prototypes/ui-convention-v1-variants.html`.
> Research: `docs/research/free-media-apis.md`.

## Architectural decisions

Durable decisions that apply across all phases:

- **Project layout:** configuration package `config`, with `manage.py` at the repo root next to the existing `scripts/`, `tests/`, `docs/`, `prototypes/`, `prd/` and `plans/`.
- **Apps:**
  - `accounts`: the custom `User` (subclasses `AbstractUser`, no extra fields), sign-up, auth templates.
  - `shows`: `Show` and `CollectionEntry`, the TVmaze client module, the shared validation and query logic, web views and templates, and the DRF API.
- **Custom user before the first migration.** `AUTH_USER_MODEL` points to `accounts.User` before `migrate` is ever run.
- **Models:**
  - `Show`: unique `tvmaze_id` and the fields listed in the PRD, including `network`, `channel_type`, `channel_country`, `background_url`, `runtime`, `tvmaze_rating`, `language` and `show_type`.
  - `CollectionEntry`: foreign keys to `User` (cascade) and `Show` (protect); `status`, `current_season`, `current_episode`, `rating`, `notes` and timestamps.
  - Constraints: unique (`user`, `show`) and check constraints that mirror the validation rules.
- **Web URLs** (named and namespaced):
  - `/` (public home);
  - accounts: login, logout (POST), sign-up;
  - `/discover/`;
  - `/shows/<tvmaze_id>/` with `?tab=tracking|suggested|extras`;
  - `/collection/`, `/collection/add/` (POST only), `/collection/<id>/` and `/collection/<id>/delete/`;
  - `/admin/`.
- **API URLs:**
  - `/api/` (browsable root);
  - `/api/auth/token/`;
  - `/api/collection/` and `/api/collection/<id>/`.
- **Authentication:**
  - Web: Django sessions; login required everywhere except home, login and sign-up.
  - API: DRF Token and Session authentication, `IsAuthenticated` by default (only the token endpoint is open).
  - Ownership: every entry lookup is limited to the requesting user, so other users' entries return 404.
- **External calls:** only the TVmaze client module talks to TVmaze. Tests always mock it.
- **Configuration:**
  - environment variables from a Git-ignored `.env` via `uv run --env-file .env`, documented in a committed `.env.example`;
  - `DJANGO_SECRET_KEY` is required;
  - tests use a throwaway key.
- **Testing:** `uv run pytest` (pytest + pytest-django), offline. The existing **44 verification-script tests stay unchanged and must pass at every checkpoint**.
- **UI:**
  - Bootstrap 5 from a CDN plus custom CSS ported from the Direction D prototype (tokens, nav, hero, shared card, tabs, tracking panels);
  - plain Django forms.

## Rules for every phase

- **Before coding:** read the phase, confirm the scope with the user, and follow the PRD's acceptance criteria.
- **Tests come with the work, never after it.** Use the `tdd` skill for the behaviors marked **TDD**.
- **Definition of done:**
  - all listed tests written and passing;
  - the full suite passes, including the 44 original tests;
  - the manual checks are done;
  - the evidence is recorded.
- **Evidence log** (new, `docs/evidence-log.md`), started in Phase 0 and appended in every phase:
  - **Bugs and corrections:** what broke, how it was found, the fix, and before-and-after output (a failing then passing test, an error then success). This feeds REFLECTION topic 5.
  - **Real requests and responses:** captured from the running app for REFLECTION topics 3–4.
  - **Design Defense screenshots:** saved to `docs/evidence/` when a phase changes the UI.
  - **Write only what actually happened.** Never invent entries.
- **Privacy in evidence:** screenshots and logs use only the demo account (`demo_user`) and test data. Never include API tokens, secret keys, passwords, email addresses, real names or other personal information. Mask tokens in captured requests (e.g. `Token ****`).
- **Documentation is incremental:** each phase updates the README section for what it delivered, and appends to the evidence log. Phase 13 finishes and checks the documentation; it doesn't write it from scratch.
- **Commit checkpoint at the end of every phase:**
  - The user pre-approved local commits at verified checkpoints. Once the phase's tests pass and the summary is shown, commit locally, staging only that phase's files.
  - **Never push without asking.**
  - Commit messages end with the session's attribution line.
  - Show a concise completion summary at each phase boundary.
- **At the end of each working session,** the user asks for the PROMPTS.md log entry, following that file's rules.

---

## Phase 0: Commit design artifacts and start the evidence log

**User stories:** none (process)

### What to build

Save the approved design work to Git before any code, so the Design Defense history is preserved: the PRD, this plan, both prototypes and an empty evidence log.

### Tasks

- Create the evidence log with its three sections (bugs and corrections, requests and responses, screenshots). Seed it with real items from the design sessions that already happened:
  - the Severance backdrop with the title baked into the art, swapped for a clean one;
  - the illustrative provider tiles that were added, then removed;
  - the AC33 token-endpoint wording fix;
  - the logged-out Discover-link conflict.
- Run the full test suite as the starting baseline.

### Acceptance criteria

- [ ] `prd/httptv.md`, `plans/httptv.md`, both prototype files and the evidence log are committed. No other files change.
- [ ] `uv run pytest` reports exactly 44 passing tests.

### Commit checkpoint

"Add HTTP.tv PRD, implementation plan, UI prototypes, and evidence log", after user approval.

---

## Phase 1: Compatibility check, Django foundation and custom User

**User stories:** 73, 74, 75 (partial), 72 (admin shell)

### What to build

A runnable Django project with secure configuration and a custom user model in place **before any migration exists**, plus a pytest setup that runs the old and new tests together.

### Tasks

1. **Compatibility check (before installing anything):**
   - From official sources, confirm the current stable Django, Django REST Framework, django-filter and pytest-django versions, and that they support Python 3.12–3.14 and each other.
   - Record the findings (versions plus source links) in the evidence log.
   - Stop and ask the user if any of them doesn't support the project's Python range.
2. Add the dependencies with uv (runtime: Django, DRF, django-filter; dev: pytest-django), updating `pyproject.toml` and `uv.lock`.
3. Create the `config` project at the repo root and the `accounts` and `shows` apps.
4. Define the custom `User` and set `AUTH_USER_MODEL`. **Only then** create the first migrations and run `migrate`.
5. Settings:
   - read the secret key, debug flag and allowed hosts from the environment;
   - fail clearly if the secret key is missing;
   - add DRF and django-filter to installed apps (configured later).
6. Create `.env.example` with placeholders for all five variables. Create a local `.env` (Git-ignored) with a freshly generated secret key.
7. pytest configuration:
   - point pytest-django at the settings;
   - supply a throwaway test secret key;
   - keep the existing tests discoverable and unchanged.
8. Register the custom User in the admin and create a superuser for local use (never committed).

### Tests

- Settings refuse to load without the secret key, with a message naming the variable (**AC2**).
- The custom user model is the active user model.
- The full suite runs: the 44 original tests plus the new ones.

### Manual verification

- `uv run --env-file .env manage.py runserver` starts; `/admin/` lets the superuser log in.
- `git status` shows `.env` and the database as ignored.

### Acceptance criteria

- [ ] AC2 passes.
- [ ] AC3 (partial): `.env.example` has placeholders for all five variables, and `.env` and `db.sqlite3` are untracked.
- [ ] AC4: `uv run pytest` passes without `.env` and still includes all 44 original tests.
- [ ] The first migration for `accounts` creates the custom user table, and no migration references `auth.User` directly.
- [ ] The compatibility findings are recorded in the evidence log.

### Commit checkpoint

"Set up Django project with custom User, env-based settings, and pytest-django", after user approval.

---

## Phase 2: Public shell, accounts and Direction D base layout

**User stories:** 1, 2, 3, 4, 77, 76 (partial)

### What to build

The site frame from the prototype, ported to Django templates:
- dark base layout, design tokens and the Inter font;
- the two-version nav bar (logged in and logged out);
- the TVmaze/CC BY-SA footer;
- the public home page's logged-out welcome hero with Sign up and Log in;
- working sign-up, login and logout (POST);
- login-protected placeholder pages for Discover and My Collection, so redirects can be tested end to end.

### Tasks

- Port the prototype's shared CSS into a static stylesheet: tokens, nav, buttons, hero, footer and responsive rules.
- Base template with the CDN links (Bootstrap 5, Bootstrap Icons, Inter) and message display.
- Sign-up (built on `UserCreationForm`; it logs the new user in), login and logout, with dark-themed forms.
- Home view: welcome hero for anonymous users; a temporary logged-in placeholder until Phase 8.

### Tests

- **AC5** (for pages that exist now): anonymous Discover and My Collection redirect to login; home, login and sign-up return 200.
- **AC5a:** nav contents for anonymous vs. logged-in users.
- **AC6:** sign-up creates a user and logs them in; logout by POST ends the session.
- **AC26 (anonymous part):** the welcome hero shows Sign up and Log in, with no Discover link.
- **AC50 (footer part):** every page links to TVmaze and CC BY-SA 4.0.

### Manual verification and evidence

- Compare the home page, sign-up and login with the prototype's look at desktop and phone widths (F12 device toolbar).
- Save screenshots of the logged-out home and the sign-up page.

### Acceptance criteria

- [ ] AC5 (current pages), AC5a, AC6 and AC26 (anonymous part) pass.
- [ ] The visual match with the prototype's nav, hero and footer is confirmed manually.
- [ ] All tests pass (44 original included).

### Commit checkpoint

"Add accounts, Direction D base layout, and public home", after user approval.

---

## Phase 3: TVmaze client and Discover search

**User stories:** 6, 7, 8, 9, 10

### What to build

A logged-in user searches TVmaze on `/discover/` and sees up to 10 poster cards in relevance order, with friendly messages for no results, blank input and every failure type. No saving yet.

### Tasks

- TVmaze client module with a search operation:
  - 10-second timeout and the HTTP.tv User-Agent;
  - separate errors for timeout, connection error, 429, other HTTP errors and invalid JSON or unexpected shape;
  - the same error categories as `verify_tvmaze.py`, but in its own module. The script is not modified.
- Discover page:
  - GET `?q=`; blank or whitespace input shows guidance and makes **no** TVmaze call;
  - result cards use the shared card markup (unsaved state);
  - inline "No shows found" and error messages.
- Port the shared card CSS from the prototype (one card component, 20 px gap, 4% hover, captions).

### Tests

- **AC8:** results rendered in mocked order, at most 10; blank query makes zero calls.
- **AC9:** each failure type shows its specific message; never a 500 error.
- Client unit tests: request parameters, timeout and User-Agent are sent; each error is mapped correctly.

### Manual verification and evidence

- **Real searches:** "the office", "xqzzvvnotashow", "café". Record the results in the manual-checklist notes.
- Save a screenshot of Discover results.

### Acceptance criteria

- [ ] AC8 and AC9 pass.
- [ ] `scripts/verify_tvmaze.py` and its 44 tests are unchanged (`git diff` is empty for both).
- [ ] All tests pass.

### Commit checkpoint

"Add TVmaze client and Discover search", after user approval.

---

## Phase 4a: Data models and migrations

**User stories:** 72 (admin), and the foundation for 22–38

### What to build

`Show` and `CollectionEntry` exist in the database with every field from the PRD, the unique (user, show) constraint, and the on-delete rules. They're inspectable in the admin. No views yet. The slice is verifiable through migrations, the admin and model tests.

### Tasks

- `Show`: unique `tvmaze_id` and all PRD fields, including `network`, `channel_type`, `channel_country`, `background_url`, `runtime`, `tvmaze_rating`, `language` and `show_type`.
- `CollectionEntry`: user FK (cascade), show FK (protect), status choices with Plan to Watch as the default, optional season, episode and rating, notes up to 2,000 characters, and timestamps.
- The unique (`user`, `show`) constraint. Migrations.
- Admin registration with list display, search and status filter.

### Tests

- Defaults: a new entry is Plan to Watch with blank progress, rating and notes.
- The unique constraint blocks a duplicate (user, show) pair (database half of **AC12**).
- Deleting a user deletes their entries. Deleting a `Show` that still has entries is blocked.
- `tvmaze_id` is unique.

### Manual verification and evidence

- `migrate` from an empty database; create a show and an entry in the admin.

### Acceptance criteria

- [ ] Migrations apply cleanly from an empty database, and the model tests pass.
- [ ] All tests pass (44 original included).
- [ ] README updated (data model overview, admin usage).

### Commit checkpoint

"Add Show and CollectionEntry models with constraints and admin". Local commit after verification.

---

## Phase 4b: Secure save flow and basic saved-show page

**User stories:** 11, 22, 23, 24 (redirect target exists), 25, 26, 27

### What to build

On Discover, the user clicks Save: `POST /collection/add/` sends only `tvmaze_id`, and the server fetches the show from TVmaze with embedded images, creates or refreshes the `Show`, and creates a `CollectionEntry`. Then it redirects to `/shows/<tvmaze_id>/?tab=tracking`.

A **basic** version of that page renders from local data: hero (backdrop or poster fallback), badges, Where to Watch, summary, and a status/progress eyebrow. Discover marks shows already saved.

### Tasks

- TVmaze client "get show for saving" (`embed[]=images`). It maps:
  - summary HTML to plain text;
  - runtime, with average runtime as the fallback;
  - rating, language and type;
  - the channel (name, type and country, from network or web channel);
  - the backdrop rule: widest background ≥1920 px, otherwise blank;
  - TVmaze 404 as "unknown show".
- Save service, reused by the API in Phase 10: fetch, then refresh-on-save `Show`, then create the entry, all in one transaction, with duplicate and failure handling that leaves no partial rows.
- Save endpoint: POST only (GET returns 405), login required, messages, and the redirect.
- Basic show page for a saved show, ported from the prototype; Where to Watch links to `tvmaze_url`.
- Discover shows "In your collection" for saved shows.

### Tests

- **TDD:** the backdrop rule (AC15) and channel mapping (AC15a): network, web channel only, and neither.
- **AC10:** only `tvmaze_id` is used.
- **AC11:** refresh-on-save.
- **AC12:** a duplicate save is refused with a message.
- **AC13:** a TVmaze failure leaves no rows.
- **AC14:** defaults, redirect and message.
- **AC5** (anonymous POST redirects) and **AC5b** (GET returns 405).
- **AC53:** the Where to Watch link is `tvmaze_url`.
- Discover's "In your collection" marker.

### Manual verification and evidence

- Save real shows: one with a network (e.g. Abbott Elementary) and one web-channel show (e.g. Severance). Check the admin rows and the page visuals against the prototype.
- Record backdrops with baked-in title text.
- Save screenshots.

### Acceptance criteria

- [ ] AC5 (save), AC5b, AC10–AC15, AC15a and AC53 pass.
- [ ] All tests pass. README updated (saving shows).

### Commit checkpoint

"Add secure save-from-TVmaze flow and basic show page". Local commit after verification.

---

## Phase 5: Complete show details page — unsaved shows, Suggested and Extras

**User stories:** 12, 13, 14, 15, 16, 17, 18, 19, 20, 21

### What to build

`/shows/<tvmaze_id>/` works for any show:
- local data when a `Show` row exists;
- otherwise a live TVmaze fetch that **writes nothing**;
- 404 for unknown IDs; a friendly message on outages;
- an "Add to my collection" button for unsaved shows.

Tab bar with Suggested and Extras (and My Tracking for saved shows, filled in during Phase 6). There is no Franchise tab.

### Tasks

- Show page data source: local first, otherwise a live fetch through the same mapping, never saved.
- **Suggested tab:** local genre match over `Show` rows, ranked by shared-genre count then name, excluding the current show, using shared wide cards and the honest label.
- **Extras tab:** a TVmaze call only when this tab is opened (`embed[]=seasons&embed[]=cast`). Shows season cards and up to 8 cast members, with a friendly message on failure.
- Default tab: My Tracking when saved, Suggested otherwise.
- Responsive stacking and the poster fallback, matching the prototype.

### Tests

- **AC16:** a saved show makes no TVmaze call on its default and Suggested tabs.
- **AC17:** an unsaved show makes one call and creates zero rows; unknown ID → 404; outage → friendly message.
- **AC18:** exactly the expected tabs, and no "Franchise" text.
- **AC19:** Suggested membership, exclusion and ordering.
- **AC20:** Extras makes one call when opened and none on other tabs; a failure doesn't break the page.
- **AC22 (T part):** Where to Watch heading and subtitle by `channel_type`, the country only when stored, and the "no channel" message.

### Manual verification and evidence

- Compare the Abbott Elementary details page with the approved prototype at desktop width (**AC21**), then at phone width.
- Open Extras live.
- Check that **AC22** holds: no provider placeholders, content ratings or HD/CC badges anywhere.
- Save screenshots: the details page (left/right layout), Extras, and the poster fallback.

### Acceptance criteria

- [ ] AC16–AC20 and AC22 pass; AC21 is confirmed manually.
- [ ] All tests pass.

### Commit checkpoint

"Complete show details page with live fallback, Suggested, and Extras", after user approval.

---

## Phase 6: Tracking — shared validation, My Tracking tab and delete

**User stories:** 5, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38

### What to build

The My Tracking tab's three-panel form (Status & progress, My rating, Notes) saves to `/collection/<id>/` and redirects back with a message. Invalid input re-renders with field errors and the user's input kept. Removing a show goes through `/collection/<id>/delete/`. Other users' entries return 404 everywhere.

### Tasks

- **Shared validation rules (TDD)**, written once:
  - status choices;
  - season and episode both blank or both ≥1;
  - rating blank or 1–5;
  - notes ≤2,000 characters.

  They're used by model validation now and by the API serializer in Phase 10. Add the matching database check constraints (migration).
- Tracking form and update view: POST only (GET redirects to the tab), owner-scoped, success message, and errors re-rendered on the show page.
- The prototype's three-panel layout:
  - live "N of 5" label and Clear control (minimal JavaScript, works without it);
  - notes counter;
  - saved and updated dates.
- Delete confirmation page (GET) and delete (POST): removes only the entry, then redirects to My Collection.

### Tests

- **TDD AC23:** every invalid case is rejected (season only, episode only, 0, negative, non-integer, rating 0 and 6, notes of 2,001 characters). Valid boundaries are accepted (notes of 2,000 characters, blank rating).
- **AC24:** a valid save updates `updated_at`, and the status never changes on its own.
- **AC25:** delete GET doesn't delete; POST deletes only the entry; the `Show` and other users' entries remain.
- **AC7 (web part):** user B gets 404 on user A's tracking and delete URLs.
- The database constraints reject invalid rows that bypass the form.

### Manual verification and evidence

- Try each invalid input in the browser and confirm the messages.
- Save screenshots of the tracking tab: valid, with errors, and the delete confirmation.
- Record any bug found while doing this as a before-and-after entry in the evidence log.

### Acceptance criteria

- [ ] AC7 (web), AC23, AC24 and AC25 pass.
- [ ] All tests pass.

### Commit checkpoint

"Add tracking form with shared validation and delete confirmation", after user approval.

---

## Phase 7: My Collection — shared query logic, filters, sorting and pagination

**User stories:** 43, 44, 45, 46, 47, 48, 49, 50

### What to build

`/collection/` is the poster grid from the prototype, with:
- status chips with counts, a title-only search and a sort dropdown;
- 12 per page with numbered pagination, all driven by URL parameters;
- empty and no-match states.

The Watching and Completed nav links open it filtered. The ordering logic is built as a **shared component** the API will reuse in Phase 11.

### Tasks

- **Shared query logic (TDD):** owner scope, status filter and ordering, with **unrated entries last in both directions** via explicit nulls-last ordering. Web-only title search with `q`.
- Collection view and template:
  - chips with counts, search and sort form, grid of shared cards with stars;
  - pagination that handles out-of-range pages without an error;
  - both empty states;
  - page title changing for Watching and Completed.

### Tests

- **TDD AC30** and nulls-last in both directions at the query-logic level.
- **AC28:** 14 entries → page 2 has 2; out-of-range page handled.
- **AC29:** chip counts; combinations of `status`, `q` and `sort`; the Watching and Completed links.
- **AC31:** both empty states.
- **AC52 (web half):** `q` matches titles only, not notes.

### Manual verification and evidence

- With 14 or more real saved shows, try every chip, sort and page.
- Save screenshots of the collection page and the empty state.

### Acceptance criteria

- [ ] AC28–AC31 and AC52 (web half) pass.
- [ ] All tests pass.

### Commit checkpoint

"Add My Collection with shared filtering, sorting, and pagination", after user approval.

---

## Phase 8: Personalized home page

**User stories:** 39, 40, 41, 42

### What to build

The logged-in home from the prototype:
- the cinematic hero for the most recently updated Watching entry (falling back to the latest entry, then to the empty-collection welcome hero with Discover);
- "More info" and "In your collection" buttons;
- rows for Continue Tracking (wide cards), My Watchlist, Recently Added (up to 10, any status) and Completed Shows, using the shared card;
- empty rows hidden, horizontal scrolling and the scroll buttons.

### Tasks

- Home view selection logic and row querysets, limited to the current user.
- Hero and rail templates ported from the prototype, with lazy-loaded wide images.
- Unify card captions ("Season X, Episode Y" / "Not started") across Discover, the show page, the collection and the home page. Show the green check only in mixed rows.

### Tests

- **AC26** (logged-in parts): hero selection and its fallbacks.
- **AC27:** row membership, the Recently Added limit and ordering, empty rows hidden, and only the user's own entries.

### Manual verification and evidence

- **AC32:** the spacing, hover and captions are consistent across all rows and grids. Compare against the prototype at desktop and phone widths.
- Save screenshots of the home page with the hero and rows.

### Acceptance criteria

- [ ] AC26 and AC27 pass; AC32 is confirmed manually.
- [ ] All tests pass.

### Commit checkpoint

"Add personalized cinematic home page", after user approval.

---

## Phase 9: REST API — authentication, token endpoint and read access

**User stories:** 51, 52, 53, 63

### What to build

The first API tracer bullet:
- DRF configured with Token and Session authentication and `IsAuthenticated`;
- `POST /api/auth/token/`;
- `GET /api/collection/` and `GET /api/collection/<id>/`, returning only the caller's entries with nested read-only show data (including the channel fields);
- the browsable API root at `/api/`.

### Tasks

- DRF settings (authentication, permissions), the token app and its migration, the token endpoint.
- Entry serializer with the nested read-only show (fields as listed in the PRD).
- Viewset scoped to `request.user`, registered with a router under `/api/`.

### Tests

- **AC33:** collection endpoints and the API root return 401/403 anonymously and succeed with a token or session. The token endpoint is the only open one.
- **AC34:** the token endpoint, with valid and invalid credentials.
- **AC35 (read):** list and retrieve the caller's entries; 404 for another user's entry (**AC7, API part**).
- **AC15a (API part):** channel fields appear in the output.

### Manual verification and evidence

- Get a real token with a terminal request and put it in `.env`. **Never commit it.**
- Browse `/api/` while logged in.
- **Record a real request and response** in the evidence log (REFLECTION topic 3 groundwork).

### Acceptance criteria

- [ ] AC33, AC34, AC35 (read) and AC7 (API) pass.
- [ ] AC44 (browsable API) is checked manually for the read endpoints.
- [ ] All tests pass.

### Commit checkpoint

"Add authenticated read-only collection API with token endpoint", after user approval.

---

## Phase 10: REST API — create, update and delete with validation parity

**User stories:** 54, 55, 56, 57

### What to build

The full CRUD API:
- `POST /api/collection/` with `{"tvmaze_id": N}` reuses the Phase 4 save service;
- `PATCH`, `PUT` and `DELETE` on the caller's entries;
- the serializer calls the **shared validation rules**, applied to the merged final values on PATCH;
- read-only fields are protected; the show can't be changed;
- error responses: 400 (duplicate or unknown TVmaze ID), 503 (TVmaze outage) and 400 field errors, all with JSON messages.

### Tasks

- Writable fields: status, season, episode, rating and notes. `tvmaze_id` is write-only and used on create only.
- Serializer validation that delegates to the shared rules, including the cross-field rule on partial updates.
- Map save-service errors to 400 and 503 responses.

### Tests

- **AC35 (write):** create, PATCH, PUT and DELETE (204); 404 for another user's entry.
- **AC36:** create returns 201, 400 for a duplicate, 400 for an unknown ID, 503 for an outage, with no rows on error.
- **TDD AC37:** every AC23 invalid case is rejected by the API, including a PATCH of `current_season` alone when there's no episode. This is a parity test that runs the same cases against the web form and the API.
- **AC38:** read-only fields are never changed.

### Manual verification and evidence

- In the browsable API: create, PATCH and DELETE an entry, and check the changes on the web pages.
- Record one real validation-error response.

### Acceptance criteria

- [ ] AC35–AC38 pass.
- [ ] All tests pass.

### Commit checkpoint

"Add collection API create/update/delete with shared validation", after user approval.

---

## Phase 11: REST API — search, filtering, ordering and pagination

**User stories:** 58, 59, 60, 61, 62, 64

### What to build

On `GET /api/collection/`:
- `?search=` over titles and notes;
- strict django-filter filters `status`, `min_rating`, `genre`, `show_status` and `network`, with 400 for invalid values;
- `?ordering=` over the six approved fields, using the **shared nulls-last ordering** from Phase 7 for the rating fields;
- page-number pagination, 12 by default, `page_size` up to 50.

### Tasks

- Filter set (strict), the search filter, and a custom ordering filter that applies nulls-last for `rating` and `tvmaze_rating` in both directions.
- Pagination class (12 by default, maximum 50); the browsable filters form.

### Tests

- **AC39:** search and each filter, alone and combined.
- **AC40:** invalid values → 400.
- **TDD AC41:** every ordering field in both directions, unrated last for `rating` and `-rating`, and the default order.
- **AC42:** default page size, `page_size`, the 50 cap, and `count`/`next`/`previous`.
- **AC43:** web and API give the same order for the status filter and the three shared sorts.
- **AC52 (API half):** `search` finds an entry by its notes.

### Manual verification and evidence

- **AC44:** the browsable filters form works.
- **Record real example requests and responses** for search, a filter, an ordering and a second page in the evidence log (REFLECTION topic 4).

### Acceptance criteria

- [ ] AC39–AC43 and AC52 pass; AC44 is confirmed manually.
- [ ] All tests pass.

### Commit checkpoint

"Add API search, filtering, nulls-last ordering, and pagination", after user approval.

---

## Phase 12: Client script — `httptv_client` (list, update, next)

**User stories:** 65, 66, 67, 68, 69, 70

### What to build

`scripts/httptv_client.py`, a standalone `requests`-based CLI configured by `HTTPTV_API_TOKEN` and `HTTPTV_API_URL`.
- `list`: `--status`, `--search`, `--ordering` and `--page`; prints a numbered table plus a page summary.
- `update <id>`: PATCHes only the given fields; at least one is required.
- `next <id>`: adds 1 to the episode only, turns "Not started" into S1E1, and never changes the season or status.

It has friendly errors for every failure and exits 0 or 1. It's kept separate from the Django app, and `verify_tvmaze.py` is untouched.

### Tasks

- Argument parsing; configuration loading with a "how to get a token" message; one request helper that maps errors (connection, timeout, 401/403, 404, 400 field errors, unexpected response).
- Output formatting that matches the web labels ("Season X, Episode Y" / "Not started").

### Tests (mocked HTTP; no server needed)

- **AC45:** `list` sends the token header and query parameters, prints the table and page summary, and exits 0.
- **AC46:** `update` sends a PATCH with only the given fields; no options → exit 1; 400 field errors are printed.
- **TDD AC47:** `next` turns S2E9 into S2E10 and "Not started" into S1E1, and never sends `status`.
- **AC48:** each error path prints its message and exits 1.

### Manual verification and evidence

- **AC49:** with the server running and a real token from `.env`, run `list`, `update` and `next` and confirm the changes in the web app.
- **Capture the real terminal output** of one `update` or `next` run, and the matching API request and response, for **REFLECTION topic 3** (the full trace).

### Acceptance criteria

- [ ] AC45–AC48 pass; AC49 is confirmed manually.
- [ ] The 44 original tests and `verify_tvmaze.py` are unchanged.
- [ ] All tests pass.

### Commit checkpoint

"Add httptv_client script for reading and updating via the API", after user approval.

---

## Phase 13: Documentation, full manual verification and Design Defense evidence

**User stories:** 71, 72, 73, 74, 75, 76 (all complete)

### What to build

A README that lets a grader run and evaluate everything, a full end-to-end manual run, and a complete evidence set.

### Tasks

- **Extend the README** without rewriting it. Add:
  - project overview;
  - setup with uv, `.env` and `.env.example`;
  - migrate, create a superuser and run the server;
  - getting a token;
  - every API endpoint and parameter with examples, including the **title-only vs. titles-and-notes search difference**;
  - both scripts, running tests, the manual verification checklist, TVmaze attribution and licensing, and where the prototypes, PRD and plan are.
- **Fresh-clone check (AC1):** clone into a temporary folder and follow the README exactly. Fix any README gaps found, and record them as evidence.
- **Run the full manual checklist:**
  - real TVmaze search (including no results and "café"), saving, backdrops, Extras, and tracking validation;
  - collection features and the home page;
  - the browsable API and the token;
  - all three client commands;
  - `verify_tvmaze.py` with a real search;
  - responsive checks at desktop and phone widths.
- Confirm **AC3** (`git ls-files` audit) and **AC50** (attribution on every page).
- **Design Defense evidence pack:** final screenshots of every main page next to the matching prototype view, plus the v1 → Direction D progression.

### Acceptance criteria

- [ ] AC1, AC3, AC50 and AC51 are confirmed. Every manual checklist item is done, with results recorded.
- [ ] The full suite passes; the test count is reported (44 original plus all new).
- [ ] The evidence log contains real entries for the bugs and corrections, the requests and responses, and the screenshots.

### Commit checkpoint

"Document setup, API, scripts, and manual verification checklist", after user approval.

---

## Phase 14: REFLECTION.md

**User stories:** 78

### What to build

`REFLECTION.md` at the repository root, written **from the completed work and the evidence log**, with one section per assigned topic:

1. API research and provider decision (from the research document and the TVmaze choice).
2. The prototype (v1 variants A–C, then Direction D and its four refinements, with screenshots and the reasoning).
3. Tracing one real `update` or `next` command: the CLI, the HTTP request with token, authentication, the viewset, serializer validation through the shared rules, the database save, the JSON response and the printed output.
4. Local search, filtering, sorting and pagination, with the real requests and responses captured in Phases 7 and 11, including the nulls-last rule and the web/API search difference.
5. Bugs and corrections, with before-and-after evidence taken from the evidence log, at least one with real failing-then-passing output.

### Tasks

- Draft each section only from recorded evidence. Wherever evidence is missing, flag it to the user rather than inventing it.
- **The user reviews and edits the draft.** It's their reflection, and the final wording is theirs.

### Acceptance criteria

- [ ] AC54: all five topics are present and refer to real artifacts, with at least one documented before-and-after bug.
- [ ] No invented output: every command and response quoted appears in the evidence log.

### Commit checkpoint

"Add Project #2 reflection", after user approval. Then, when the user asks, push to the public GitHub repository and ask the user for the final PROMPTS.md session entry.
