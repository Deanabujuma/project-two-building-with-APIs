# PRD: HTTP.tv — TV Show Discovery and Tracking

*CIDM 3312 Project #2: a Django application that consumes an external API (TVmaze) and provides its own authenticated REST API. Approved design: 23 decisions from the 2026-11-15 design session. Visual design: prototype "Direction D (cinematic dark)", revised and approved.*

## Problem Statement

People who watch a lot of television lose track of it. They forget which episode they stopped on, which shows they meant to start, which ones they paused or gave up on, and what they thought of a show they finished months ago. Streaming apps only remember what was watched on that one service, and general notes apps don't know anything about the shows themselves (posters, years, networks, genres), so keeping a personal list means typing everything by hand.

Users want one private place to find any TV show, save it, and record where they are, how they rate it, and what they think of it. They also want that data to be reachable from their own scripts, not locked inside web pages.

## Solution

HTTP.tv is a Django web application with a premium, cinematic dark interface. A signed-in user:

- **Discovers** shows by searching the free TVmaze catalog (no API key needed) and opening any result's details page.
- **Saves** shows to a personal collection. The server always fetches the show's facts directly from TVmaze, so the shared show data can't be tampered with from the browser.
- **Tracks** each saved show: a viewing status (Plan to Watch, Watching, On Hold, Completed, Dropped), progress as "Season X, Episode Y", an optional 1–5 star rating, and private notes.
- **Browses** their collection on a personalized home page (a cinematic hero for the show they're currently tracking, plus rows of their shows) and on a collection page with status filters, title search, sorting and pagination.

HTTP.tv also provides an **authenticated REST API** for the same collection, with search, filtering, sorting and pagination. A **command-line client script** shows the API in use by listing, updating and advancing progress on entries. The existing **TVmaze verification script** (from the earlier session) stays as the proof that the external API works.

HTTP.tv only shows information it can verify. It shows a show's original network or web channel, but never claims where a show is streaming. It never invents content ratings, franchise links or recommendations. Every page credits TVmaze as required by its CC BY-SA 4.0 license.

## User Stories

### Accounts and access

1. As a visitor, I want to see a home page explaining HTTP.tv with Sign up and Log in buttons, so that I know what the app does and how to start.
2. As a visitor, I want to create an account with a username and password, so that I can keep a private collection.
3. As a registered user, I want to log in and log out, so that only I can see and change my collection.
4. As a visitor who isn't logged in, I want to be sent to the login page when I open any page other than home, login or sign-up, so that private pages are never shown to anonymous users.
5. As a user, I want any attempt to open another user's collection entry to show "not found", so that other people's data stays private and its existence isn't revealed.

### Discovering shows (TVmaze search)

6. As a user, I want to search TVmaze by show title from a Discover page, so that I can find any TV show.
7. As a user, I want results in TVmaze's relevance order, showing each show's poster, name and key information, so that I can recognize the right show quickly.
8. As a user, I want a clear "No shows found" message when nothing matches, so that I know the search worked but found nothing.
9. As a user, I want a blank search to be rejected without contacting TVmaze, so that I don't get a confusing error.
10. As a user, I want a friendly message when TVmaze is slow, unreachable, rate-limiting, or returns unusable data, so that I understand the problem and can try again.
11. As a user, I want shows that are already in my collection to be marked "In your collection" in search results, so that I don't try to save them twice.

### Show details page

12. As a user, I want to open a cinematic details page for any show, saved or not, so that I can learn about it before deciding to save it.
13. As a user, I want the details page to show the title, verified metadata badges (show status, type, runtime, language, TVmaze rating), years and genres on the left, and the summary on the right, over a large background image, so that the page feels immersive and is easy to read.
14. As a user, I want a "Where to watch" section showing only the verified original channel, labelled as a network or web channel and with its country when known, so that I'm never misled about availability.
15. As a user, I want a "View on TVmaze" link on every show, so that I can see the original source.
16. As a user, I want viewing a show I haven't saved to leave my collection unchanged, so that browsing never creates data.
17. As a user, I want an unknown show ID to show a "not found" page, so that broken links fail clearly.
18. As a user, I want a Suggested tab listing other HTTP.tv shows that share a genre with this one, clearly labelled as a genre match, so that I can find similar shows without being told it's a recommendation engine.
19. As a user, I want an Extras tab listing the show's seasons (episode counts and years) and main cast, so that I can see more about the show.
20. As a user, I want a friendly message on the Extras tab if TVmaze can't be reached, so that the rest of the page still works.
21. As a user, I want shows without a wide background image to use a designed poster-based layout, so that the page never shows a stretched or broken image.

### Saving shows

22. As a user, I want to save a show to my collection with one click from search results, the home hero or the details page, so that adding shows is fast.
23. As a user, I want a newly saved show to start as "Plan to Watch" with progress "Not started" and no rating or notes, so that I don't have to fill anything in to save it.
24. As a user, I want to be taken to the saved show's My Tracking tab with a success message after saving, so that I can set my progress right away.
25. As a user, I want saving a show that's already in my collection to be refused with a clear message, so that I never get duplicates.
26. As a user, I want a friendly message and no partial data when TVmaze fails during a save, so that I can simply try again.
27. As a user, I want saving a show to refresh its stored information from TVmaze, so that details like "Running" or "Ended" stay reasonably current.

### Tracking

28. As a user, I want a My Tracking tab on the details page of each show I've saved, so that tracking happens in the same place as the show's information.
29. As a user, I want to set the status to Plan to Watch, Watching, On Hold, Completed or Dropped myself, so that the status always means what I intend.
30. As a user, I want to record the season and episode I last watched, so that I know where to resume.
31. As a user, I want a season without an episode (or the reverse) to be rejected with a clear message, so that my progress is always complete.
32. As a user, I want season and episode to accept only whole numbers of 1 or more, so that progress is always valid.
33. As a user, I want to give a show 1 to 5 stars or leave it unrated, and clear a rating, so that I can record my opinion when I'm ready.
34. As a user, I want to write notes of up to 2,000 characters with a live character counter, so that I can record thoughts without hitting a surprise limit.
35. As a user, I want invalid tracking input to show field-specific errors while keeping what I typed, so that I can fix mistakes quickly.
36. As a user, I want to see when I saved a show and when I last updated it, so that I know how current my tracking is.
37. As a user, I want to remove a show from my collection through a confirmation page that explains what will be deleted, so that I don't delete tracking data by accident.
38. As a user, I want removing a show to delete only my tracking entry, so that other users who saved the same show are unaffected.

### Home page

39. As a user, I want the home page hero to feature my most recently updated "Watching" show with its progress, so that I can continue where I left off.
40. As a user, I want the hero to show my most recently updated show when I'm not watching anything, and a welcome message with a Discover button when my collection is empty, so that the home page is never broken or misleading.
41. As a user, I want rows for Continue Tracking, My Watchlist, Recently Added and Completed Shows, built only from my own collection, so that the home page reflects my real viewing.
42. As a user, I want rows to scroll horizontally, with consistent card sizes, spacing, hover effects and "Season X, Episode Y" labels, so that the interface feels polished and predictable.

### My Collection page

43. As a user, I want a My Collection page showing my shows as poster cards with title, status, progress and stars, so that I can review everything at a glance.
44. As a user, I want status filter chips (All, Watching, Plan to Watch, On Hold, Completed, Dropped) with counts, so that I can focus on one group.
45. As a user, I want "Watching" and "Completed" navigation links that open my collection filtered to that status, so that common views are one click away.
46. As a user, I want to search my collection by title, so that I can find a show in a long list.
47. As a user, I want to sort by recently updated, title, or my rating, with unrated shows last, so that I can organize my list the way I need.
48. As a user, I want 12 shows per page with page links, so that large collections stay fast and readable.
49. As a user, I want a friendly empty state ("Your collection is empty") linking to Discover, and a "No shows match" state with a "Clear filters" link, so that I'm never left on a blank page.
50. As a user, I want filters, search, sort and page to appear in the URL, so that I can bookmark or share a view and use the browser's back button.

### REST API

51. As an API client, I want to obtain a personal token by sending my username and password, so that my scripts can authenticate.
52. As an API client, I want every API request without valid credentials to be rejected, so that collections are never exposed.
53. As an API client, I want to list my collection entries with nested, read-only show details, so that one request gives me everything I need to display.
54. As an API client, I want to add a show by sending only its TVmaze ID, so that show data always comes from TVmaze.
55. As an API client, I want to retrieve, partially update, fully update and delete a single entry, so that I can fully manage my collection.
56. As an API client, I want the same validation as the web form, with clear JSON error messages, so that bad data is rejected the same way everywhere.
57. As an API client, I want duplicate saves and unknown TVmaze IDs to return 400, and TVmaze outages to return 503, so that I can handle each failure correctly.
58. As an API client, I want to search my entries by show name and notes, so that I can find entries by keyword.
59. As an API client, I want to filter by status, minimum rating, genre, show status and network, so that I can ask focused questions of my data.
60. As an API client, I want to sort by updated date, created date, show name, my rating, premiere date and TVmaze rating in either direction, with unrated entries last, so that results come back in a useful order.
61. As an API client, I want paginated results (12 by default, up to 50 on request) with a total count and next/previous links, so that large collections are efficient to read.
62. As an API client, I want invalid filter values to return 400 instead of being silently ignored, so that my mistakes are visible.
63. As a developer, I want a browsable API in my logged-in browser, with a filters form, so that I can explore and demonstrate the API without writing code.
64. As a user, I want the API and the web collection page to filter and sort identically, so that both show the same results.

### Client script (reads and updates through the API)

65. As a script user, I want to list my entries with optional status, search, ordering and page options, so that I can read my collection from the terminal.
66. As a script user, I want to update an entry's status, season, episode, rating or notes with command-line options, so that I can change tracking without the web app.
67. As a script user, I want a "next" command that adds one to an entry's episode number without changing its season or status, and turns "Not started" into Season 1, Episode 1, so that logging one more episode is a single command.
68. As a script user, I want the script to read my token and the API address from environment variables, so that secrets never appear in commands or in Git.
69. As a script user, I want friendly messages for a missing token, a server that isn't running, a rejected token, an entry that doesn't exist or isn't mine, and validation errors, so that I always know what went wrong.
70. As a script user, I want exit code 0 on success and 1 on any error, so that the script works in automation.

### TVmaze verification script (existing, preserved)

71. As a developer, I want the existing TVmaze verification script and its 44 tests kept working unchanged, so that the external API integration remains independently proven.

### Administration, setup and quality

72. As the developer, I want shows and collection entries in the Django admin, so that I can inspect data during development and demos.
73. As a developer cloning the repo, I want setup to use uv and an example environment file, so that I can run the project with documented commands.
74. As a developer, I want Django to refuse to start without a secret key, so that the app never runs with an unsafe default.
75. As a developer, I want one test command that runs every automated test offline, without my personal environment file, so that the suite is reliable for anyone.
76. As a grader, I want a README with setup, run, API, script and manual verification instructions, so that I can evaluate the project without guessing.
77. As a visitor who isn't logged in, I want the navigation to show only Log in and Sign up, so that I'm never shown links to private pages or a profile that doesn't exist.
78. As a grader, I want a REFLECTION.md covering the five assigned topics with evidence from the actual work, so that I can assess the student's understanding of the research, prototype, API flow, query features and debugging.

## Implementation Decisions

### Architecture and apps

- **One Django project** with a configuration package named `config`, and `manage.py` at the repository root alongside the existing `scripts/`, `tests/`, `docs/` and `prototypes/` folders.
- **Two apps:**
  - `accounts`: a minimal custom `User` model that subclasses `AbstractUser` with no added fields, plus the sign-up view and auth templates.
  - `shows`: the `Show` and `CollectionEntry` models, the TVmaze client module, web views and templates, and the DRF API (serializers, viewset, filters) in separate modules.
- **Dependencies are managed with uv:** Django, Django REST Framework and django-filter at runtime, and pytest-django as a dev dependency alongside the existing `requests` and `pytest`. Versions are confirmed compatible with the project's `requires-python >=3.12` range at implementation time.
- **Database:** SQLite (the database file is Git-ignored).
- **Configuration:**
  - `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` and `DJANGO_ALLOWED_HOSTS` are read from environment variables.
  - Local values live in a Git-ignored `.env`, loaded with uv's `--env-file` option.
  - A committed `.env.example` lists every variable with safe placeholder values: the Django variables plus the client script's `HTTPTV_API_TOKEN` (a placeholder, never a real token) and `HTTPTV_API_URL` (the local default, `http://127.0.0.1:8000/api/`).
  - A missing `DJANGO_SECRET_KEY` stops Django with a clear error.
  - The test configuration supplies a throwaway key, so tests never need `.env`.
- **Django admin** is enabled, with `Show` and `CollectionEntry` registered (list display, search and status filter).
- **Local-only:** submitted as a public GitHub repository, with no deployment (the assignment doesn't require one).

### Data model

- **`Show`** (shared by all users, one row per TVmaze show):
  - `tvmaze_id`: unique integer, the stable key.
  - Basic facts: `name`, `tvmaze_url`, `image_url` (poster URL only; images are never downloaded), `premiered` (date, optional), `ended` (date, optional) and `show_status` (e.g. Running, Ended, To Be Determined).
  - `genres`: one comma-separated text field.
  - `network`: the channel name, whether it's a TV network or a web/streaming channel; optional.
  - `channel_type`: optional choice of "network" or "web channel". Set to "network" when TVmaze's `network` object is present, "web channel" when only `webChannel` is present, and blank when neither is.
  - `channel_country`: optional text, the channel's country name from TVmaze. Blank when TVmaze gives no country (common for web channels).
  - `summary`: plain text with TVmaze's HTML tags stripped and entities decoded, rendered with normal escaping.
  - Added for the cinematic design: `background_url` (optional), `runtime` (minutes, optional; uses TVmaze's runtime or average runtime), `tvmaze_rating` (decimal, optional), `language` (optional) and `show_type` (optional, e.g. Scripted).
- **`CollectionEntry`** (one per user per show):
  - `user`: foreign key to the custom user; entries are deleted with the user.
  - `show`: foreign key to `Show`. Deleting a `Show` that still has entries is blocked.
  - `status`: choices Plan to Watch, Watching, On Hold, Completed, Dropped; default Plan to Watch.
  - `current_season` and `current_episode`: optional positive integers.
  - `rating`: optional integer from 1 to 5.
  - `notes`: optional text, at most 2,000 characters.
  - `created_at` and `updated_at`: automatic timestamps.
- **Constraints:**
  - A unique constraint on (`user`, `show`).
  - Check constraints that mirror the validation rules (season and episode both null or both ≥ 1; rating null or 1–5), as a database-level safety net.
- **Shared validation rules** are written once and enforced in three places: model validation (used by the web form), the API serializer's validation (DRF doesn't call model `clean()` automatically), and the database constraints. The rules:
  - status must be one of the five choices;
  - season and episode must both be blank or both be whole numbers ≥ 1;
  - rating must be blank or 1–5;
  - notes must be at most 2,000 characters.
- **Status is always set by the user.** No rule ever changes it automatically.
- **Unused `Show` rows** stay after the last entry is removed. They still feed Suggested.

### TVmaze client module

- A single module in the `shows` app wraps every TVmaze call. Views and API code never call TVmaze directly, so tests have one place to mock.
- **Behavior carried over from the verification script:** a 10-second timeout, a descriptive User-Agent (HTTP.tv plus a version, with no personal contact details), and separate friendly errors for timeout, connection failure, HTTP 429 (with "wait a few seconds"), other HTTP errors, and invalid JSON or unexpected response shape.
- **Operations:**
  - **Search:** TVmaze fuzzy show search (up to 10 results, relevance order).
  - **Get show for saving:** one request for a show by ID with embedded images. It returns the mapped show fields, including the chosen backdrop and the channel name, type and country. A TVmaze 404 is reported as "unknown show", separately from outages.
  - **Channel mapping:** if TVmaze's `network` is present, it supplies the name and country, with type "network". Otherwise `webChannel` supplies them, with type "web channel". If neither is present, all three channel fields are blank. The same mapping is used for unsaved shows fetched live for the show page.
  - **Get extras:** one request for a show by ID with embedded seasons and cast, made only when the Extras tab is opened.
- **Backdrop rule:** among the show's images of type "background", choose the widest one at least 1920 px wide. If none qualifies, store no backdrop, and pages use the poster-based fallback layout. Backdrops containing baked-in title text are an accepted limitation, softened by the dark gradient.
- **Extras mapping:** seasons with a premiere date (number, episode count, start and end year), and up to 8 cast members (person name, character name, character image or person image when available).

### Web pages and URLs

- **Navigation bar,** shown on every page, in two versions:
  - **Logged in:**
    - left: the user's avatar initial and username;
    - centre: the HTTP.tv wordmark and links for Home, Discover, My Collection, Watching and Completed;
    - right: a search icon to Discover and a Log out control (a POST form);
    - a clear active-page indicator; icons only on narrow screens.
  - **Logged out (public):**
    - the HTTP.tv wordmark (linking home) and **Log in** and **Sign up** buttons;
    - no avatar, username, private links or search icon.
- **Footer** on every page: "Show information and images from TVmaze, licensed CC BY-SA 4.0", plus "HTTP.tv is a tracking app; it does not stream video".
- **Home (`/`):**
  - Public. Logged-out visitors see a welcome hero whose calls to action are **Sign up** (primary) and **Log in**, never Discover, which requires login. No rows are shown.
  - Logged-in hero: the most recently updated Watching entry, otherwise the most recently updated entry, otherwise (empty collection) a welcome hero with a Discover button.
  - The hero shows title, verified badges, year, genres and network, a two-line summary, a "More info" button and an "In your collection" or "Add to collection" button.
  - Rows from the user's own entries: Continue Tracking (other Watching entries, wide cards), My Watchlist (Plan to Watch), Recently Added (newest saves, up to 10) and Completed Shows. Empty rows are hidden.
- **Discover (`/discover/`):**
  - Search form submitted by GET (`?q=`); blank input shows guidance without calling TVmaze.
  - Results are poster cards, each with a save button (a POST to `/collection/add/` sending only `tvmaze_id`) or an "In your collection" marker.
  - "No shows found" and TVmaze error messages are shown inline.
- **Show details (`/shows/<tvmaze_id>/`):**
  - Data comes from the local `Show` if it exists, otherwise from a live TVmaze fetch that is **never saved**. An unknown ID gives a 404 page; a TVmaze outage gives a friendly message.
  - **Left column:** a status and progress eyebrow (when saved), the title, verified badges, years and genres, and action buttons ("Edit my progress" when saved, "Add to my collection" otherwise, plus "View on TVmaze").
  - **Where to watch** (also in the left column):
    - The heading reads "Where to watch · original network" or "· original web channel", based on `channel_type`.
    - One card shows the `network` name and a subtitle: "Original network" or "Original web channel", then the country when known, then "verified by TVmaze". For example, "Original network · United States · verified by TVmaze" or "Original web channel · verified by TVmaze".
    - The card links to the show's TVmaze page (the stored `tvmaze_url`). No official-site field is stored.
    - With no channel, the section says "No network or web channel listed on TVmaze."
  - **Right column:** the summary in a translucent panel.
  - **Tabs** (`?tab=`): My Tracking (saved shows only, the default when saved), Suggested (the default otherwise) and Extras. There is **no Franchise tab**.
- **Saving (`POST /collection/add/`):**
  - Every save button (Discover, home hero, show page) posts only `tvmaze_id` here. GET is not allowed (405). The server re-fetches the show from TVmaze, creates or updates the `Show` (refresh-on-save), then creates the entry.
  - Duplicates are refused with a message. TVmaze failures leave no partial data and show a friendly message.
  - Success redirects to the show page's My Tracking tab with a success message.
- **Tracking update (`/collection/<id>/`):**
  - GET redirects to the show page's My Tracking tab. POST validates and saves, then redirects back with a success message; invalid input re-renders the page with field errors and the user's input kept.
  - Desktop layout: three panels side by side (Status & progress, My rating with a live "N of 5" label and a Clear control, and Notes with a live counter), with Save and Remove actions and the saved and updated dates.
- **Delete (`/collection/<id>/delete/`):** a GET confirmation page explaining what is deleted; a POST deletes only the entry and redirects to My Collection with a message.
- **My Collection (`/collection/`):**
  - GET parameters: `status`, `q` (show **title** contains, case-insensitive; notes are not searched on this page), `sort` (recently updated, title, or rating high-to-low with unrated last) and `page`.
  - 12 per page, status chips with counts, poster-card grid, numbered pagination, and both empty states.
  - Watching and Completed in the navigation are this page with `status` preset; the page title changes to match.
- **Accounts:** dark-themed login, logout (POST) and sign-up pages built on Django's auth views and `UserCreationForm`.
- **Ownership and login:**
  - Every view except home, login and sign-up requires login.
  - Every entry lookup is limited to the requesting user's entries, so other users' entries give 404.
  - All changes use POST with CSRF protection.
- **Shared card component:** every row and grid uses one card style with the same width rules, a 20 px gap, a 4% hover scale with a white outline and shadow, and a caption of title, status dot with status, and "Season X, Episode Y" or "Not started". Cards for unsaved shows say "Not in your collection" plus genres. A green check appears only in rows that mix saved and unsaved shows.
- **Shared query logic:**
  - What the collection page and the API share: owner scoping, status filtering, and ordering, including the nulls-last rating rule. Both use the same code for these, so they behave the same.
  - Rating sorts put unrated entries last in both directions, using explicit nulls-last ordering because SQLite would otherwise put nulls first when sorting ascending.
  - **Documented difference (approved):** text search covers different fields.
    - The web collection's `q` matches **show titles only**.
    - The API's `search` matches **show titles and notes**.
    - The README states this explicitly, and each is tested separately.
  - The API also has filters the web page doesn't expose (`min_rating`, `genre`, `show_status`, `network`) and more ordering fields.
- **Suggested:** other `Show` rows that share at least one genre with the current show, ranked by number of shared genres then name, excluding the current show. Labelled "Matched locally by genre; not a TVmaze recommendation".
- **Styling:** Bootstrap 5 from a CDN plus custom CSS that follows the approved prototype. Near-black background (#0B0B0F), white text, gradients over imagery, pill-shaped buttons, rounded cards, and the Inter font with Bootstrap Icons. Plain Django forms with Bootstrap classes on the widgets.
- **Responsive behavior:** shorter heroes and stacked columns (summary below the title) under the large breakpoint, horizontally scrolling rows, nav labels collapse to icons, and no horizontal page overflow.

### REST API

- **Prefix `/api/`,** with the DRF browsable API root at `/api/`.
- **Authentication:** DRF `TokenAuthentication` (header `Authorization: Token <key>`) and `SessionAuthentication` (browsable API). The default permission is `IsAuthenticated`.
- **Token endpoint:** `POST /api/auth/token/` with username and password returns the user's token. Tokens can also be managed in the admin.
- **Collection resource** (a `ModelViewSet` registered with a router):
  - `GET /api/collection/` lists the user's entries.
  - `POST /api/collection/` with `{"tvmaze_id": N}` adds a show, reusing the web save logic: a TVmaze re-fetch and refresh-on-save. It returns 201 with the entry; 400 for a duplicate or an unknown TVmaze ID; 503 for a TVmaze timeout, connection error, 429 or bad response. Errors are JSON with readable messages.
  - `GET /api/collection/<id>/` retrieves an entry. `PATCH` and `PUT` update it. `DELETE` removes it (204). Another user's entry or a missing ID returns 404.
  - The queryset is always limited to `request.user`.
- **Serializer:**
  - Writable fields: `status`, `current_season`, `current_episode`, `rating`, `notes`.
  - Read-only fields: `id`, `created_at`, `updated_at`, and a nested `show` with `tvmaze_id`, name, URLs, dates, `show_status`, genres, `network`, `channel_type`, `channel_country`, `runtime`, `tvmaze_rating`, `language`, `show_type` and summary.
  - `tvmaze_id` is write-only and used only on create; changing the show of an existing entry is not allowed.
  - The serializer's validation calls the shared rules, including the cross-field season/episode rule, which is checked against the merged final values on PATCH.
- **Search:** `?search=` (DRF `SearchFilter`) over show name **and notes**. This is intentionally broader than the web collection's title-only search.
- **Filters** (django-filter, strict, so invalid values return 400): `status` (choice), `min_rating` (1–5), `genre` (case-insensitive contains), `show_status` (exact, case-insensitive) and `network` (case-insensitive contains).
- **Ordering:** `?ordering=` (`OrderingFilter`) over `updated_at`, `created_at`, `show__name`, `rating`, `show__premiered` and `show__tvmaze_rating`, with `-` for descending. The default is `-updated_at`. Ordering by `rating` or `tvmaze_rating` puts nulls last in both directions, via a small custom ordering filter.
- **Pagination:** page-number, `page_size` 12 by default, adjustable with `?page_size=` up to a maximum of 50. The response includes `count`, `next`, `previous` and `results`.
- **Licensing note:** show data in API responses is TVmaze-derived (CC BY-SA 4.0). The README documents this.

### Client script

- **A standalone Python script named `httptv_client`** in the existing scripts folder, kept separate from the Django app. It uses `requests` and talks only to the HTTP.tv API, never the database.
- **Configuration:**
  - `HTTPTV_API_TOKEN` (required);
  - `HTTPTV_API_URL` (default `http://127.0.0.1:8000/api/`);
  - both can come from the same `.env` via `uv run --env-file .env`.
- **Commands:**
  - `list`: options `--status`, `--search`, `--ordering` and `--page`. Prints a numbered table of entry ID, show name, status, progress ("Season X, Episode Y" / "Not started") and rating, plus a "page N of M (count entries)" line.
  - `update <id>`: options `--status`, `--season`, `--episode`, `--rating` and `--notes`. Sends a PATCH with only the given fields and prints the updated entry. At least one option is required.
  - `next <id>`: reads the entry, adds 1 to the episode only (never changes the season or status), turns "Not started" into Season 1, Episode 1, sends a PATCH, and prints the before → after progress.
- **Errors** (friendly messages in the verification script's style): missing token (with how to get one), server not running or unreachable, timeout, 401/403 (bad token), 404 ("no such entry in your collection"), 400 (the API's validation messages, field by field) and unexpected responses. Exit code 0 on success, 1 on any error.
- **No `add` command.** Adding is demonstrated by the web app and `POST /api/collection/`.

### Existing assets that must be preserved

- **The TVmaze verification script and its 44 tests** remain unchanged and passing.
- **Both UI prototypes:** the approved Direction D cinematic prototype and the original variants A–C. They stay in the prototypes folder as design history and are never imported by the app.
- **The research document, PROMPTS.md and README** are kept. The README is extended, never rewritten.

### Required deliverable: REFLECTION.md

- Project #2 requires a `REFLECTION.md` at the repository root, covering these **five assigned topics**:
  1. **API research and provider decision:** how the free media APIs were researched and compared, and why TVmaze was chosen.
  2. **The prototype:** what design question it answered, the variants explored (A–C, then Direction D and its refinements), and what was decided.
  3. **Tracing the second script's update through the API:** follow one real `update` or `next` command from the command line through the HTTP request, authentication, the viewset and serializer validation, the database save, and the response printed by the script.
  4. **Local search, filtering, sorting and pagination:** how the API (and the shared logic with the web collection page) implements each, with real example requests and responses.
  5. **Bugs and corrections, with before-and-after evidence:** real problems hit during the project and how each was found and fixed, with evidence such as failing then passing test output, or error output before and after the fix.
- **The answers are written only after the related work is complete,** and must describe what actually happened. They are not drafted ahead of time, and no example output is invented.
- **Evidence is collected during implementation, not reconstructed later.**
  - Whenever a bug or correction occurs, record its before-and-after evidence (command, output and fix) at the time.
  - The PROMPTS.md "Sideways" summaries are one source.
  - Real requests and responses for topics 3 and 4 are captured from the running app.

### Testing

- **pytest with pytest-django** for everything; one command (`uv run pytest`) runs the whole suite offline.
- **Mocking:**
  - TVmaze is always mocked by patching the TVmaze client module (or `requests` inside it, for the client's own tests). No automated test makes a real network call.
  - Client-script tests mock HTTP responses from the HTTP.tv API.
- **Coverage:**
  - Model rules and constraints.
  - The TVmaze client: success mapping, backdrop rule, HTML stripping, and each error type.
  - Web views: login required, ownership 404s, save flow including duplicates and TVmaze failures, tracking validation errors, delete, collection query parameters and empty states, show page for saved, unsaved and unknown shows, tabs, and Extras failure.
  - The API: auth required, token endpoint, CRUD, create errors (400/503), validation parity with the web form, each filter, invalid filters → 400, search, every ordering field, **unrated-last in both rating directions, for both the API and the collection page**, and page size default/maximum.
  - The client script: each command, the `next` edge cases, configuration errors and every error path, with exit codes.
- **TDD** for the trickiest behaviors (validation rules, query/sort logic, `next`). Tests are added within each implementation phase, never deferred to the end.
- **The README manual verification checklist** covers real-network behavior the mocks can't prove:
  - a real TVmaze search, including no results and "café";
  - saving a real show and checking its backdrop;
  - Extras live;
  - token retrieval;
  - each client command against a running server;
  - a visual check of the home, details, collection and Discover pages at desktop and phone widths.

## Acceptance Criteria

Each criterion is verifiable by an automated test (T), a manual check (M), or both.

### Setup and configuration
- AC1 (M): On a fresh clone, `uv sync`, copying the example env file, migrating, and running the server with `--env-file .env` produce a working app using only commands documented in the README.
- AC2 (T): Starting Django without `DJANGO_SECRET_KEY` fails with a message naming the variable.
- AC3 (M): `git ls-files` shows no `.env`, database file, token or secret key value. `.env.example` lists `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `HTTPTV_API_TOKEN` and `HTTPTV_API_URL`, with placeholders only.
- AC4 (T): `uv run pytest` passes with **0 failures**, needs no network or `.env`, and includes all **44** original verification-script tests unchanged.

### Accounts and access
- AC5 (T): Anonymous GETs to Discover, My Collection, a show page and every collection-entry URL redirect to login (302), as does an anonymous POST to `/collection/add/`. Home, login and sign-up return 200.
- AC5a (T): For an anonymous visitor, every public page's navigation contains Log in and Sign up links and no username, Log out, My Collection, Watching, Completed or Discover links. For a logged-in user, it contains the username and all five navigation links and no Log in or Sign up.
- AC5b (T): A GET to `/collection/add/` returns 405.
- AC6 (T): Sign-up creates a user and logs them in. Logout via POST ends the session.
- AC7 (T): User B requesting user A's entry via the web tracking, delete or API URLs receives 404, and A's entry is unchanged.

### Search and save
- AC8 (T): A Discover search renders up to 10 results in the mocked TVmaze order. A blank query makes **zero** TVmaze calls.
- AC9 (T): Each TVmaze failure type (timeout, connection error, 429, 500, invalid JSON) shows its specific friendly message on Discover. No server error (500) is raised.
- AC10 (T): Saving sends only `tvmaze_id`. Show fields posted from the browser are ignored. The stored `Show` matches the mocked TVmaze response.
- AC11 (T): Saving a show whose `Show` row already exists updates that row's fields and creates no second `Show`.
- AC12 (T): A second save of the same show by the same user creates no entry and shows "already in your collection". The database constraint also rejects a direct duplicate insert.
- AC13 (T): When TVmaze fails during a save, **no** `Show` or entry is created, and a friendly message is shown.
- AC14 (T): A successful save creates an entry with Plan to Watch status, blank progress, rating and notes, and redirects to the show page's My Tracking tab with a success message.
- AC15 (T): The backdrop rule picks the widest background ≥1920 px; with only smaller or no backgrounds it stores none. HTML in the summary is stripped.
- AC15a (T): Channel mapping. A mocked show with `network` stores its name, type "network" and country. A show with only `webChannel` stores its name and type "web channel", with country blank when TVmaze gives none. A show with neither stores all three as blank. The show page and API output reflect these values.

### Show page
- AC16 (T): The show page for a saved show uses no TVmaze call (for the default and Suggested tabs) and shows the My Tracking tab by default.
- AC17 (T): The show page for an unsaved show makes one TVmaze call and creates **zero** database rows. An unknown ID returns 404. An outage shows a friendly message (status 200 or 503, not 500).
- AC18 (T): The tabs are exactly My Tracking (saved only), Suggested and Extras, and no "Franchise" text appears.
- AC19 (T): Suggested lists only shows sharing ≥1 genre, excludes the current show, and is ordered by shared-genre count then name.
- AC20 (T): Extras makes exactly one TVmaze call when opened and none on other tabs. On failure it shows a friendly message, and the rest of the page renders.
- AC21 (M): The details page matches the approved prototype layout: metadata left, summary right on desktop, stacked on narrow screens, and the poster fallback when there's no backdrop.
- AC22 (T/M): "Where to watch" shows only the verified channel. Its heading and subtitle match `channel_type`, the country appears only when stored, and the "no channel" message appears when all channel fields are blank. No provider placeholders, content ratings, HD/CC badges or invented availability appear anywhere.

### Tracking
- AC23 (T): Each invalid input is rejected with a field-specific message, the user's input kept, and no change saved: season without episode, episode without season, season or episode of 0, negative or non-integer, rating 0 or 6, notes of 2,001 characters. Notes of exactly 2,000 characters and an empty rating are accepted.
- AC24 (T): Saving valid tracking updates `updated_at` and redirects back with a success message. Status never changes unless the user changes it.
- AC25 (T): Delete GET shows a confirmation without deleting. POST deletes only the entry. The `Show` row and other users' entries remain.

### Home and collection
- AC26 (T): The home hero shows the most recently updated Watching entry, then falls back to the most recently updated entry. A logged-in user with no entries sees the welcome hero with a Discover link. An anonymous visitor sees the welcome hero with Sign up and Log in links, no Discover link and no rows.
- AC27 (T): Each home row contains only the current user's entries. Continue Tracking, My Watchlist and Completed Shows contain only their matching status. Recently Added holds at most 10 entries of any status, newest first. Empty rows are absent.
- AC28 (T): My Collection shows 12 entries per page. With 14 entries, page 2 shows 2. Out-of-range page numbers are handled without a 500 error.
- AC29 (T): Status chips show correct counts. `status`, `q` and `sort` combine correctly. The Watching and Completed nav links produce the filtered view.
- AC30 (T): Sorting by rating places all unrated entries after all rated ones.
- AC31 (T): The empty collection and no-match states each render their message and link.
- AC32 (M): Rows and grids use the same card spacing, hover effect and "Season X, Episode Y / Not started" captions shown in the approved prototype.

### REST API
- AC33 (T): Every collection endpoint and the API root return 401 or 403 without credentials, and succeed with a valid token or a logged-in session. The token endpoint is the only API endpoint that accepts anonymous requests, because it is how a client obtains a token.
- AC34 (T): `POST /api/auth/token/` returns a token for valid credentials, and 400 for invalid ones.
- AC35 (T): List returns only the caller's entries, with nested show data. Retrieve, PATCH, PUT and DELETE (204) work on the caller's entry. All return 404 for another user's entry.
- AC36 (T): `POST /api/collection/` with a valid `tvmaze_id` returns 201. A duplicate returns 400. An unknown ID (TVmaze 404) returns 400. A TVmaze outage returns 503. All errors carry a JSON message and create no rows.
- AC37 (T): Every invalid tracking case from AC23 is rejected by the API with 400 and a field error. This includes a PATCH that sends only `current_season` for an entry with no episode.
- AC38 (T): Read-only fields (`id`, `show`, `created_at`, `updated_at`) are ignored or rejected on write and never changed.
- AC39 (T): `search` matches show name and notes. `status`, `min_rating`, `genre`, `show_status` and `network` each filter correctly, alone and combined.
- AC40 (T): Invalid filter values (e.g. `status=banana`, `min_rating=9`) return 400.
- AC41 (T): Each allowed `ordering` field sorts correctly ascending and descending. `ordering=rating` and `ordering=-rating` both place unrated entries last. The default order is most recently updated first.
- AC42 (T): Pagination returns 12 results by default, honours `page_size` up to 50, caps larger requests at 50, and includes `count`, `next` and `previous`.
- AC43 (T): For the same user, the same status filter and the equivalent sort, with no text search, the web collection and the API return the same entries in the same order. The three equivalent sorts are recently updated (`-updated_at`), title (`show__name`) and rating high-to-low (`-rating`). Text search is compared separately in AC52.
- AC44 (M): The browsable API at `/api/` works in a logged-in browser and shows the filters form.

### Client script
- AC45 (T): `list` sends the token header and the requested query parameters, prints a numbered table and page summary, and exits 0.
- AC46 (T): `update` PATCHes only the provided fields. With no options it exits 1 with a usage message. API validation errors are printed per field, with exit 1.
- AC47 (T): `next` turns S2E9 into S2E10 (season unchanged), "Not started" into S1E1, and never sends a `status` change.
- AC48 (T): A missing token, a connection error, a timeout, 401, 404 and an unexpected response each print their specific friendly message and exit 1.
- AC49 (M): Against a running server with a real token, `list`, `update` and `next` produce the expected changes, visible in the web app.

### Attribution and documentation
- AC50 (T/M): Every page's footer links to TVmaze and CC BY-SA 4.0. Every show page links to the show's TVmaze page.
- AC51 (M): The README documents setup, environment variables, running the app, obtaining a token, every API endpoint and query parameter with examples, both scripts, running tests, the manual checklist, TVmaze licensing, where the prototypes are, and the difference between web title-only search and API title-and-notes search.

### Search scope
- AC52 (T): With an entry whose notes contain "goats" but whose title doesn't, the web collection's `q=goats` returns no results, and the API's `search=goats` returns that entry. Both find it by a word in the title.

### Show page link
- AC53 (T): The Where to Watch card's link is the show's TVmaze URL. The `Show` model has no official-site field.

### Reflection
- AC54 (M): `REFLECTION.md` exists at the repository root with one section for each of the five assigned topics.
  - Each section refers to real artifacts from this project: the research document, the prototype files, real commands and responses, real test output.
  - The bugs section includes at least one documented before-and-after example from the actual work.
  - It is written after the related work is complete.

## Out of Scope

1. **Deployment.** The app runs locally only. The assignment requires a public GitHub repository, not a deployed site. No hosting, production settings or HTTPS setup.
2. **Email features:** password reset, email verification and social login.
3. **Real streaming availability.** Only the verified original network or web channel is shown.
4. **Franchise and spin-off links,** and any recommendation engine beyond the local genre match.
5. **Episode-level tracking:** episode lists, episode titles, percent complete.
6. **Automatic status changes** of any kind.
7. **Caching TVmaze search results,** and storing seasons or cast.
8. **A separate Genre model** or many-to-many genre relationships.
9. **API extras:** a shows endpoint, JWT, token expiry, API rate limiting, and an `add` command in the client script.
10. **Social features:** sharing collections, following users, public profiles.
11. **Cleanup of unused `Show` rows.**
12. **Video playback** of any kind, including trailers and autoplay.

## Further Notes

### Design Defense considerations

- **Why TVmaze:** the research compared 20 free media APIs. TVmaze needs no key or sign-up, has an explicit open license (CC BY-SA 4.0, link-back attribution) that allows storing data, and a generous rate limit (at least 20 calls per 10 seconds per IP). These were verified on TVmaze's official API page during this session.
- **Why two models:** shared show facts are stored once, and personal tracking is per user. This avoids duplication and lets the API search, filter and sort locally without calling TVmaze per item.
- **Why re-fetch on save:** posting only `tvmaze_id` stops users from editing hidden form fields to tamper with the shared `Show` table. It's a deliberate security decision.
- **Why the same rules in model, serializer and database:** DRF serializers don't run model `clean()`. Enforcing the rules in all three keeps the web app and API consistent, and tests prove it.
- **How the design evolved:** the prototype began with three structurally different Bootstrap layouts (poster grid, dense dark table, library list + detail), preserved as v1. Direction D, a cinematic dark streaming-style interface, was then chosen and refined in four steps:
  - removed the illustrative provider placeholders;
  - widened the tracking form to three panels;
  - unified card spacing, hover and progress labels;
  - kept the left-metadata / right-summary details layout.

  Both versions are kept to show this progression.
- **Honest data:** HTTP.tv is styled like a streaming app but deliberately shows only verified data.
  - No content ratings (TVmaze has no such field).
  - No streaming availability (only the original network).
  - No Franchise tab (no data source).
  - "Suggested" is labelled as a local genre match.
  - Backdrops are real TVmaze 16:9 "background" images. The automatic widest-image rule sometimes picks artwork with the title baked in; this is an accepted, explainable limitation.
- **Rejected alternatives worth mentioning:**
  - live-fetching on every page (rate limits, outages);
  - JWT (unnecessary complexity);
  - storing seasons and cast (no requirement needs them);
  - PostgreSQL (setup burden);
  - hand-written filtering (more code, no browsable filter form).

### TVmaze data limitations (verified 2026-11-15)

- Background images come only at full resolution (about 0.5–1.7 MB each). Wide cards on the home page and in Suggested load these, so lazy loading is used. Posters (about 20 KB) are used for the long rows.
- No background image is flagged as "main", so selection is automatic and imperfect.
- "Typography" images are JPEGs with solid backgrounds, not transparent logos, so titles are always rendered as text.
- `runtime` is sometimes empty; `averageRuntime` is used as the fallback.

### Process notes

- Every AI-assisted session is logged in PROMPTS.md using its existing instructions (newest entry first, never rewriting old entries).
- The implementation plan will be produced next from this PRD as tracer-bullet vertical slices, each ending with its tests passing. The final slice includes writing REFLECTION.md from the evidence collected along the way.
- **Deliverables summary:**
  - the Django app (`accounts`, `shows`) with its REST API;
  - both scripts (`verify_tvmaze`, unchanged, and `httptv_client`) and the full pytest suite;
  - README (extended), `.env.example`, this PRD, the implementation plan, both prototypes, PROMPTS.md and REFLECTION.md;
  - all in the public GitHub repository.
