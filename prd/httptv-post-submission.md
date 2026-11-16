# HTTP.tv — Post-submission improvements (addendum)

This addendum covers changes made **after** the Project #2 submission. The approved PRD
(`prd/httptv.md`) and the submitted code are unchanged. They are tagged `project2-submission`
(commit `44b9337`). This work lives on the `post-submission-improvements` branch.

## Feature 1: Discover browsing rows

**Problem:** Discover showed only an empty search bar until the user searched.

**Solution:** before any search, Discover shows rows of wide landscape cards. Search works exactly as before.

| Row | Source (all real data) | Label |
|---|---|---|
| Featured Shows | the 10 highest TVmaze-rated shows with new episodes this week | "Highest TVmaze ratings among shows with new episodes this week" |
| Browse by Genre | genres occurring in this week's shows and in shows stored on HTTP.tv, with counts; each opens `/discover/genre/<genre>/` | "Genres of shows airing this week and shows saved on HTTP.tv" |
| Airing This Week | TVmaze `/schedule` (TV networks in the chosen country) plus `/schedule/web` (streaming; channels in that country or with no country), today and the next 6 days, one card per show | "each day's highest TVmaze-rated first" |
| Recommended From My Collection | the existing local genre match, generalised to the whole collection; candidates are stored shows plus this week's shows, excluding saved ones | "Shares genres with shows you've saved · not a TVmaze recommendation" |

**Decisions (approved 2026-11-15):**
- **Images:** real backdrops where available cheaply (stored shows, and lookups for the 10 Featured shows). Otherwise the card falls back to the real poster on a blurred copy of itself, with the title. If there's no image at all, the card shows the show's initial.
- **Caching** (this reverses design decision 7, "no caching"): Django's in-memory cache.
  - Schedules are cached for 1 hour, and backdrop lookups for 7 days (TVmaze image URLs never change).
  - Failures are never cached.
  - A cold cache costs at most 14 schedule requests plus up to 10 image requests.
  - The first failed image lookup stops further lookups for that visit.
- **No new database fields** for this feature. Browsing never saves a show.
- **Loading:** `/discover/` makes no TVmaze calls itself (the original tests, including AC8, are unchanged). Its script loads the rows from `/discover/browse/?partial=1`. `/discover/browse/` without `partial` is a full page for browsers without JavaScript.
- **No "Trending" or "Popular" labels.** TVmaze has no such data.

**Acceptance criteria** (`shows/tests/test_discover_browse.py`):
- 14 schedule requests on a cold cache, and none on a warm one;
- one card per show, at its first airing this week;
- the country filter for streaming;
- Featured = top 10 by rating;
- backdrop, poster-fallback and initial cards;
- a failed backdrop lookup stops further lookups;
- a schedule outage shows a note while the local rows still render;
- failures are not cached;
- genre counts and the genre page;
- recommendations ranked by shared genres, excluding saved shows;
- every card links to `/shows/<id>/`;
- saved shows are flagged;
- no "trending" or "popular" text;
- login required;
- no database writes.

## Feature 2: Profile & Settings and Delete Account

**Problem:** the nav avatar only led to My Collection. Users had no way to change their username or password, set preferences, or delete their account.

**Solution:** the nav username and avatar open `/accounts/profile/`. The page has these panels, top to bottom:
- **Account:** username, member since, last login, number of shows saved, API token status, and counts by status.
- **Shortcuts:** My Collection, Watching, Discover, and the browsable API.
- **Edit username:** uniqueness ignores capital letters.
- **Change password:** uses Django's `PasswordChangeForm`, which checks the old password and Django's password validators.
- **Preferences.**
- **Log out:** a POST form.
- **Danger Zone:** links to Delete Account.

**Database change** (migration `accounts/0002_profile_preferences`), two fields on `accounts.User`:
- `schedule_country`: US, GB, CA, AU, IE or NZ; default US. Discover's Airing This Week uses it.
- `default_collection_sort`: `-updated`, `title` or `-rating`; default `-updated`. My Collection uses it when the URL has no `sort`.

Existing users get the defaults, so nothing changes for them until they choose.

**Password change:**
- `update_session_auth_hash` keeps the current browser logged in.
- Other sessions are logged out (Django invalidates their session hash).
- The user's API token is deleted, as approved, so a leaked token stops working. The message tells the user to get a new one.

**Delete Account** (`/accounts/delete/`):
- GET shows a separate confirmation page with the exact warning: "Are you sure you want to permanently delete your account? This action cannot be undone." It explains that the collection, ratings, notes, progress and API token are removed, and gives the number of shows.
- The user must enter their current password and type `DELETE`. A small script enables the final button only when the password is filled in and the text is exactly `DELETE` (surrounding spaces ignored).
- POST is CSRF-protected. The server checks the password and the word again; GET never deletes.
- On success the server deletes `request.user` inside a transaction. The existing foreign keys do the rest: `CollectionEntry.user` and `Token.user` cascade, while `CollectionEntry.show` is `PROTECT` and `Show` has no user link, so shared Show rows and other users' accounts, entries and tokens are never touched.
- The user is then logged out and redirected to the public home page with "Your account has been permanently deleted."
- There is no undo or soft delete.

**Acceptance criteria** (`accounts/tests/test_profile.py`):
- the nav avatar links to the profile page;
- anonymous GET and POST are sent to login;
- all panels appear, with the Danger Zone last;
- no autofocus jump;
- username change, case-insensitive uniqueness, and invalid names;
- an unknown form name cannot set other fields;
- password change keeps the session, logs out other sessions and makes the old token return 401;
- wrong old password, mismatched or too-short new passwords;
- preferences are saved and validated;
- the default sort is applied, and an explicit sort still wins;
- the schedule country reaches Discover;
- the confirmation page deletes nothing and its button starts disabled;
- wrong or missing password, missing or lowercase `delete`;
- GET with query parameters doesn't delete;
- a missing CSRF token returns 403;
- deletion removes only this user's entries and token, keeping all Show rows and the other user's data;
- the user is logged out with the message;
- the deleted user can't log in or use the API;
- another user's password doesn't work.
