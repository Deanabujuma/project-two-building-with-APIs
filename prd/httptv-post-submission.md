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

## Feature 2: Profile & Settings

Added in Phase B (see below).
