# Free External Media APIs: Provider Comparison

*Research notes. All sources accessed 2026-11-14 unless noted.*

## Scope

This page compares free (or free-tier) external APIs that could back a Django app where users **search** an external catalog, **save** chosen items, and **add their own notes, ratings, or progress**. It covers six categories: books, movies, television, recipes, music, and games.

For each provider it records the data available, free limits, sign-up, authentication, and restrictions. The restrictions that matter most for a search-save-annotate app are attribution, commercial use, and caching or storage rules, since the app keeps items in its own database.

Only primary sources were used: official docs, terms, pricing, and signup pages. A few response field lists were also confirmed by sending one anonymous request to the live public API (marked **"live probe"**). When an official page could not be reached or did not cover a point, this page says so and does not guess.

**This page does not recommend a provider.**

## Summary comparison

| Provider | Category | Auth | Sign-up | Free limits | Key restrictions |
|---|---|---|---|---|---|
| Open Library | Books | None (User-Agent with contact asked for) | None required (optional app registration) | 1 req/s unidentified, 3 req/s identified. Covers by ISBN etc.: 100 per 5 min per IP | No bulk downloads. Not for high-traffic commercial backends. Cover attribution appreciated |
| Google Books | Books | API key (`key=` query param) or OAuth 2.0 | Google Cloud project for a key | Not stated on the docs page. Keyless calls hit a shared daily quota (live probe returned 429) | Can't charge users a fee without Google's permission. Must remove content on request |
| Gutendex | Books (public domain) | None | None | Not stated. Docs ask long-term users to self-host | Only Project Gutenberg titles. No terms page |
| TMDB | Movies + TV | API key (`api_key=`) or Bearer "Read Access Token" | TMDB account, then apply in settings | ~40 req/s ceiling | Non-commercial only. TMDB logo plus non-endorsement notice required. **Cache no longer than 6 months** |
| OMDb | Movies + TV | API key (`apikey=`) | Email address | 1,000 req/day (free) | Poster API is for patrons only. Site content is CC BY-NC 4.0 |
| TVmaze | TV | None (public API) | None | At least 20 calls per 10 s per IP | CC BY-SA: attribution (link back) and ShareAlike |
| Trakt | Movies + TV (tracking) | `trakt-api-key` header (client ID). OAuth for user data/writes | Trakt account plus app registration | 500 GET per 5 min (unauthed, per client ID + IP) | Images: docs page not reviewed. Terms not reviewed |
| TheMealDB | Recipes | Key in URL path (test key `1`) | None for test key. Paid supporter for app-store release | Not stated | Test key is for development/education. Must credit as data source. Free tier can't publish to an app store |
| Spoonacular | Recipes | API key | Account, no credit card (direct) | 50 points/day, 1 req/s, 2 concurrent | Backlink required. **Only ID, title, and image URL may be stored. Cache max 1 hour** (needs permission) |
| Edamam | Recipes | Not verified | Paid plan | **No free plan.** Lowest is $9/mo (10-day trial) | Attribution mandatory. Strict caching limits |
| MusicBrainz | Music | None for reads. User-Agent with contact **required** | None for reads | 1 req/s per IP (average) | Core data CC0. Supplementary data CC BY-NC-SA. Commercial use needs a paid plan |
| Cover Art Archive | Music (cover images) | None stated | None | "No rate limiting rules" (page is inconsistent) | Image licensing not stated on API page |
| Last.fm | Music | API key (`api_key` param) | Last.fm API account | No number published | Non-commercial only. **Must not use images/artwork.** 100 MB storage cap. Attribution button required |
| Spotify Web API | Music | OAuth 2.0 (client credentials / user auth) | Spotify account. **Dev Mode owner needs Premium** | Dev Mode: 5 users. Quota shared per developer account | No databases/compilations of Spotify Content. 2024–2026 endpoint removals. Extended quota only for organizations with 250k MAU or more |
| Deezer | Music | None needed for public search (live probe). Login required to accept terms | Account login to accept terms | Not stated on reviewed pages | Strictly non-commercial. No offline storage of audio |
| Discogs | Music | Not verified (docs blocked) | Not verified | Not verified (see Open questions) | Not verified |
| RAWG | Games | API key (`key=` query param) | RAWG account | 20,000 req/month | Attribution plus active hyperlink on every page. Wording on free commercial use is inconsistent |
| IGDB | Games | Twitch OAuth client credentials. `Client-ID` + `Authorization: Bearer` headers | Twitch account with **2FA**, register app | 4 req/s, 8 open requests | Non-commercial (Twitch Developer Service Agreement). No browser calls (CORS) |
| FreeToGame | Games (free-to-play only) | None | None | "Avoid more than 10 req/s" | Attribution with hyperlink. Personal and commercial use allowed. **No title-search endpoint** |
| Giant Bomb | Games | Not verified (docs blocked) | Not verified | Not verified | Not verified (see Open questions) |

---

## Books

### Open Library (Internet Archive)

- **Data.** Book Search (`https://openlibrary.org/search.json`), Works, Editions, Authors, Subjects, and Covers APIs. Most identifiers return JSON when you add `.json` ([Developers API](https://openlibrary.org/developers/api)). Search results include `key` (work ID, e.g. `OL27448W`), `title`, `first_publish_year`, and `cover_i`. A `fields` parameter picks which fields come back. The search schema "is not guaranteed to be stable," though common fields like title should be safe to rely on ([Search API](https://openlibrary.org/dev/docs/api/search)). A live probe also showed `author_name`, `author_key`, `cover_edition_key`, and `edition_count`.
- **Covers.** `https://covers.openlibrary.org/b/$key/$value-$size.jpg`, where key is ISBN, OCLC, LCCN, OLID, or ID and size is S, M, or L. Add `?default=false` to get a 404 when no cover exists ([Covers API](https://openlibrary.org/dev/docs/api/covers)).
- **Rate limits.** Default is 1 request per second. Identified requests (with a User-Agent) get 3 requests per second ([Developers API](https://openlibrary.org/developers/api)). Cover lookups by any ID other than CoverID or OLID are limited to 100 requests per IP every 5 minutes, and going over returns 403 ([Covers API](https://openlibrary.org/dev/docs/api/covers)).
- **Sign-up / auth.** No API key. Apps in regular use should send `User-Agent: AppName (contact email or phone)`. There is an optional registration form for tracking use cases ([Developers API](https://openlibrary.org/developers/api)).
- **Restrictions.**
  - Don't bulk-download through the API. Use the monthly data dumps instead.
  - Don't scrape HTML, spread requests across several IPs, or use Open Library as the backend for high-traffic commercial services.
  - Research and education tools are among the prioritized uses ([Developers API](https://openlibrary.org/developers/api)).
  - For covers, load images from covers.openlibrary.org instead of downloading them. Linking back is "appreciated but not strictly required" ([Covers API](https://openlibrary.org/dev/docs/api/covers)).
  - No explicit rule on storing metadata in your own database was found.
- **Fit notes.** The work `key` and `cover_i` are stable handles to save locally. Cover images can be hotlinked by ID without counting against the 100-per-5-minute limit. Rate limits are low, so per-keystroke search would need throttling.

### Google Books API

- **Data.** Search with `GET https://www.googleapis.com/books/v1/volumes?q=...`. Each result has an `id` and a `volumeInfo` object. The single-volume example shows `title`, `authors`, `publishedDate`, `description`, and `imageLinks` (`smallThumbnail`, `thumbnail`) ([Using the API](https://developers.google.com/books/docs/v1/using)).
- **Auth.** "A request that does not provide an OAuth 2.0 token must send an API key," passed as `key=yourAPIKey`. OAuth 2.0 is needed only for private user data (bookshelves) ([Using the API](https://developers.google.com/books/docs/v1/using)). The same page also says "Performing a search does not require authentication."
- **Free limits.** The docs page gives no number. It only says the key "provides API access, quota, and reports" ([Using the API](https://developers.google.com/books/docs/v1/using)). A live probe without a key (2026-11-14) returned HTTP 429: "Quota exceeded for quota metric 'Queries' and limit 'Queries per day'". So keyless calls share an exhausted quota, and in practice a key is needed. **The per-key daily quota was not verified from an official page.**
- **Sign-up.** Requires a Google Cloud project to create an API key. Whether a credit card is needed was not verified.
- **Restrictions.** "You may not charge users any fee for the use of your application" without a separate agreement or written permission. You must remove allegedly infringing content on request and provide a contact for rights holders. Users must be told that content they submit may become public ([Books API Terms](https://developers.google.com/books/terms)). The Books terms don't cover attribution or caching. The general Google APIs Terms of Service also apply but were not reviewed here.
- **Fit notes.** The volume `id` works for detail lookup. Coverage of in-print books is broad. Quota details still need confirming in the Cloud console.

### Gutendex (Project Gutenberg)

- **Data.** `GET /books?search=...` (matches titles and authors) and `GET /books/<id>`, with pages of up to 32 results. Fields: `id`, `title`, `authors` (name, birth_year, death_year), `subjects`, `summaries`, `bookshelves`, `languages`, `copyright`, `download_count`, and `formats` (MIME type to URL) ([gutendex.com](https://gutendex.com/)). The docs don't name a cover field. A live probe showed the `formats` map includes an `image/jpeg` key, which appears to be the cover.
- **Auth / limits / terms.** None are documented. The docs say: "For long-term use, please run your own server" (code at github.com/garethbjohnson/gutendex) ([gutendex.com](https://gutendex.com/)).
- **Upstream (Project Gutenberg) rules.** The Gutenberg website is "intended for human users only," and automated use can get an IP blocked. Gutenberg's catalog data "are granted to the public domain" ([Robot Access policy](https://www.gutenberg.org/policy/robot_access.html)). Gutendex is a separate, unofficial service built on that catalog.
- **Fit notes.** Covers public-domain titles only, so the catalog is limited. The hosted instance has no stated uptime or limits.

---

## Movies & Television

### TMDB (The Movie Database)

- **Data.** `GET https://api.themoviedb.org/3/search/movie?query=...` returns `id`, `title`, `overview`, `poster_path` (relative path, can be null), and `release_date` ([Search Movie reference](https://developer.themoviedb.org/reference/search-movie)). To build an image URL, combine the base URL, a size, and the file path, e.g. `https://image.tmdb.org/t/p/w500/<poster_path>`. The base URL and sizes come from `/configuration` ([Image basics](https://developer.themoviedb.org/docs/image-basics)). TV search endpoints exist but their reference pages were not opened.
- **Auth.** Pass a v3 key as the `api_key` query parameter, or send `Authorization: Bearer <Read Access Token>`. Both give the same access ([Application authentication](https://developer.themoviedb.org/docs/authentication-application)).
- **Rate limits.** The legacy limit was disabled on 2019-12-16. Upper limits now "sit somewhere in the 40 requests per second range" and "could change at any time." Respect 429 responses ([Rate limiting](https://developer.themoviedb.org/docs/rate-limiting)).
- **Sign-up.** Create a TMDB account, then apply under Settings > API ([FAQ](https://developer.themoviedb.org/docs/faq)).
- **Restrictions.**
  - Free for non-commercial use with attribution. Commercial use needs a license from sales@themoviedb.org ([FAQ](https://developer.themoviedb.org/docs/faq)).
  - You must use an approved TMDB logo and show the notice "This product uses the TMDB API but is not endorsed or certified by TMDB," e.g. in About/Credits ([FAQ](https://developer.themoviedb.org/docs/faq)).
  - Terms: you may not "Cache, for longer than 6 months, any information obtained through or from TMDB," and must purge cached content on termination ([API Terms of Use](https://www.themoviedb.org/api-terms-of-use), last updated 2023-10-20).
- **Fit notes.** One provider covers both movies and TV. The 6-month cache limit matters for saved items: the app would need to refresh stored TMDB fields or keep only the ID plus user-generated data. Whether storing just an ID counts as "information obtained from TMDB" was not confirmed (see Open questions).

### OMDb API

- **Data.** Parameters are `s` (search), `i` (IMDb ID, e.g. `tt1285016`), `t` (title), `type` (movie/series/episode), `y` (year), and `plot` (short/full). Responses are JSON or XML ([omdbapi.com](https://www.omdbapi.com/)). The page doesn't list response fields in full.
- **Auth.** `apikey` query parameter on every request ([omdbapi.com](https://www.omdbapi.com/)).
- **Free limits / sign-up.** "FREE! (1,000 daily limit)." Enter an email address and the key is emailed to you ([API key page](https://www.omdbapi.com/apikey.aspx)).
- **Restrictions.** "The Poster API is only available to patrons." Site content is "licensed under CC BY-NC 4.0." How that license applies to API data isn't stated ([omdbapi.com](https://www.omdbapi.com/)). No caching or storage rules were found.
- **Fit notes.** IMDb IDs are well-known keys to save. Whether search results include poster URLs for free keys was not verified, because only the separate Poster API is described as patron-only.

### TVmaze

- **Data.** `/search/shows?q=` does fuzzy search. `/singlesearch/shows?q=` returns exactly one result or none ([TVmaze API](https://www.tvmaze.com/api)). A live probe showed each show has `id`, `name`, `premiered`, `ended`, `image`, `summary`, `genres`, `rating`, and `externals`. `image` is null when none exists ([TVmaze API](https://www.tvmaze.com/api)).
- **Auth / sign-up.** The public API needs no key. A separate user-level API is for Premium members ([TVmaze API](https://www.tvmaze.com/api)).
- **Rate limits.** "At least 20 calls every 10 seconds per IP address." Excess calls get 429 ([TVmaze API](https://www.tvmaze.com/api)).
- **Restrictions.** Licensed CC BY-SA. The data "can freely be used for any purpose" if you credit TVmaze (a link back is enough) and follow ShareAlike. Responses are cached for 60 minutes on TVmaze's side. Image URLs never change, so images can be cached indefinitely ([TVmaze API](https://www.tvmaze.com/api)).
- **Fit notes.** No key and an explicit open license make storing saved show data straightforward. **ShareAlike** may affect how the app's own derived data is licensed (see Open questions). TV only.

### Trakt

- **Data.** A movie/TV tracking service. The search endpoint docs were not reviewed in detail. The Apiary docs page didn't render through the fetch tool.
- **Auth / headers.** Required on every request: `Content-Type: application/json`, `User-Agent` (e.g. `MyAppName/1.0.0`), `trakt-api-key` (your app's client ID), and `trakt-api-version: 2` ([Required headers](https://developer.trakt.tv/docs/required-headers)). OAuth is needed for user-specific data and writes.
- **Rate limits (Standard apps, api.trakt.tv).** Authenticated POST/PUT/DELETE: 1 call per second. Authenticated GET: 500 per 5 minutes. Unauthenticated GET: 500 per 5 minutes per client ID and IP ([Rate limiting](https://developer.trakt.tv/docs/rate-limiting)).
- **Not verified.** Whether Trakt returns images (a docs "Images" page exists but was not opened), Trakt's API terms (commercial use, caching), and app-registration requirements.
- **Fit notes.** Trakt overlaps with the app's own "progress" feature. It is often paired with TMDB for artwork, but that pairing was not verified from Trakt's docs.

---

## Recipes

### TheMealDB

- **Data.** `/api/json/v1/1/search.php?s=<name>` and `/api/json/v1/1/lookup.php?i=<id>` ([API page](https://www.themealdb.com/api.php)). A live probe showed `idMeal`, `strMeal`, `strCategory`, `strArea`, `strInstructions`, `strMealThumb`, `strSource`, and `strImageSource`, plus `strIngredientN` and `strMeasureN`.
- **Auth.** The key is part of the URL path. "You can use the test API key "1" during development of your app or for educational use." Paid supporters get an upgraded key ([API page](https://www.themealdb.com/api.php)).
- **Limits.** No rate limit is stated. Non-supporters can list at most 100 items when listing the full database ([API page](https://www.themealdb.com/api.php)).
- **Restrictions.**
  - "You must become a supporter if releasing publicly on an appstore" ([API page](https://www.themealdb.com/api.php)).
  - Terms: the free tier cannot publish to app stores. You "must mention us as the source of the data." Don't remove copyright or trademark notices. Check `strCreativeCommons` for artwork licensing. Content from the official endpoints may be copied and modified. Scraping is not allowed ([Terms of Use](https://www.themealdb.com/terms_of_use.php)).
  - No explicit caching or storage limit was found.
- **Fit notes.** The test key is aimed at development and educational use. Saving `idMeal` plus fields looks allowed under the "copy and modify" wording, but there is no explicit storage clause.

### Spoonacular

- **Free limits.** 50 points per day. Calls fail with 402 until the quota resets at midnight UTC. 1 request per second and 2 concurrent requests. No credit card when you sign up directly (RapidAPI's free plan does require one). "Backlink Required" ([Pricing](https://spoonacular.com/food-api/pricing)).
- **Storage / caching (important).** You may store the **recipe ID, title, and image URL indefinitely**, and link your own users' data to recipe IDs. Other data (ingredients, instructions, nutrition) may **not** be stored. Caching needs prior written permission and lasts at most **1 hour**. All data must be deleted if you stop using the API ([Terms](https://spoonacular.com/food-api/terms); also [Pricing](https://spoonacular.com/food-api/pricing)).
- **Other restrictions.** Credit the original recipe source with a hyperlink. Don't resell data. Don't build a product that provides "the same experience" as spoonacular ([Terms](https://spoonacular.com/food-api/terms)).
- **Auth.** API key. The exact way to pass it was not confirmed on the pages reviewed.
- **Fit notes.** The storage rules line up with a save-ID-plus-user-notes design, but any detail view must re-fetch from the API. 50 points a day is small, and the points cost per endpoint was not reviewed.

### Edamam Recipe Search API

- **Free limits.** **No free plan is listed.** The cheapest is Enterprise Basic at $9/month: 10,000 calls a month, 10 per minute, with a 10-day trial ([Recipe API plans](https://developer.edamam.com/edamam-recipe-api)).
- **Restrictions.** Attribution is required on all plans, and missing it means "immediate service suspension." Caching is not allowed except what a plan explicitly permits (Basic: recipe ID and name only), and only inside the end user's password-protected account. Only human, end-user-driven requests are allowed ([Recipe API plans](https://developer.edamam.com/edamam-recipe-api)).
- **Auth.** Not verified. The plans page doesn't describe `app_id`/`app_key`.
- **Fit notes.** Not free as of the access date.

---

## Music

### MusicBrainz (+ Cover Art Archive)

- **Data.** Search with `/ws/2/<entity>?query=...&limit=&offset=` and look up by MBID with `/ws/2/<entity>/<MBID>?inc=...`. The default format is XML. Use `fmt=json` or `Accept: application/json` for JSON ([MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API)). A live probe of a release-group search showed `id`, `title`, `first-release-date`, `primary-type`, and `artist-credit`.
- **Cover art.** MusicBrainz data has no cover art ([Data License](https://musicbrainz.org/doc/About/Data_License)). Cover images come from the Cover Art Archive: `/release-group/{mbid}/front[-250|-500|-1200]` and `/release/{mbid}/front`. The CAA page says there are "currently no rate limiting rules," but some endpoints list a 503 for exceeding a rate limit. Image licensing isn't stated ([Cover Art Archive API](https://musicbrainz.org/doc/Cover_Art_Archive/API)).
- **Auth.** None for lookup, browse, or search. User data needs OAuth (digest auth is deprecated and scheduled for removal in August 2027) ([MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API)).
- **Rate limits / User-Agent.** "(on average) 1 request per second" per IP. Excess requests get 503. A User-Agent header is **required**, in the form `AppName/<version> ( contact-email-or-url )` ([Rate Limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting)).
- **Licensing / commercial.** Core data is CC0. Supplementary data is CC BY-NC-SA 3.0 ([Data License](https://musicbrainz.org/doc/About/Data_License)). Non-commercial use of the web service is free. Commercial use needs a paid plan ([MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API)).
- **Fit notes.** MBIDs are stable keys to save. Core data is CC0, which makes storing it simple. The 1 req/s limit means server-side throttling would be needed.

### Last.fm

- **Data.** `album.search`, `artist.search`, `track.search`, and the `*.getInfo` methods ([API index](https://www.last.fm/api)). `album.search` needs `api_key` and `album`, returns `name`, `artist`, `image` (several sizes), and `url`, and "does not require authentication" ([album.search](https://www.last.fm/api/show/album.search)).
- **Sign-up.** You create an API account ([API index](https://www.last.fm/api)).
- **Restrictions (Terms).**
  - "solely for non-commercial purposes" (3.1).
  - A "powered by AudioScrobbler" button linking to Last.fm is required, and placement needs approval. Public pages need prior written approval (2.7).
  - **"You will not use any audio, audiovisual, images and/or artwork"** (5.1.8).
  - Storage cap of 100 MB. Cache according to HTTP headers (4.3.4).
  - Delete data on termination (9.3).
  - Rate limits are at Last.fm's discretion. No number is published (4.4).
  - Source: [API Terms of Service](https://www.last.fm/api/tos).
- **Fit notes.** The search response includes image URLs, but the terms forbid using images or artwork, so the app couldn't show cover art from Last.fm. The approval requirement for public pages may also matter.

### Spotify Web API

- **Recent changes (important).**
  - **2024-11-27:** New apps (registered on or after that date) and dev-mode apps without a pending extension lost access to Related Artists, Recommendations, Audio Features, Audio Analysis, Featured and Category playlists, 30-second preview URLs in multi-get responses, and algorithmic/editorial playlists ([Spotify blog, 2024-11-27](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api)).
  - **2025-05-15:** Extended access is limited to apps with "established, scalable, and impactful use cases" ([Spotify blog, 2025-04-15](https://developer.spotify.com/blog/2025-04-15-updating-the-criteria-for-web-api-extended-access)). The quota modes page says Spotify "only accepts applications from organizations (not individuals)" and requires a registered business and at least 250k MAUs ([Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)).
  - **2026-02-11 / 2026-03-09:** Development Mode requires a **Spotify Premium** account, at most 5 authorized users, and a smaller set of endpoints. The endpoint limits were postponed for existing integrations ([Spotify blog, 2026-02-06](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security)). The changelog cuts the `GET /search` `limit` maximum from 50 to 10 (default 5). It removes batch "Get Several" endpoints and drops fields such as `popularity` and `available_markets` ([Changelog, Feb 2026](https://developer.spotify.com/documentation/web-api/references/changes/february-2026)).
  - **2026-07-23:** Up to 25 Development Mode client IDs per developer account, with all of them sharing one quota. Quota-exceeded 429s now include `"reason": "QUOTA_EXCEEDED"`. No numeric quota is given ([Spotify blog, 2026-07-23](https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates)).
- **Development Mode now.** Up to 5 authenticated Spotify users, and the app owner must have Premium. Non-allowlisted users get 403 ([Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)).
- **Storage rules.** "you may not store, aggregate or create compilations or databases of Spotify Content." "Do not store Spotify Content indefinitely." Local caching only "as strictly necessary to enhance the performance" (metadata and cover art) ([Developer Terms](https://developer.spotify.com/terms), Version 10, effective 2025-05-15).
- **Fit notes.** A Premium account is needed to develop. A public deployment would be capped at 5 allowlisted users. The terms forbid building databases of Spotify Content, which conflicts with saving items, though saving only Spotify IDs plus user notes was not confirmed either way.

### Deezer

- **Data.** Developer docs pages sit behind a login gate ("You have to login to accept the terms and conditions of the simple API") ([developers.deezer.com/api](https://developers.deezer.com/api)). A live probe of `https://api.deezer.com/search/album?q=...` without a key returned `id`, `title`, `cover`, `cover_small` through `cover_xl`, `artist`, `nb_tracks`, `record_type`, and `link`.
- **Restrictions.** "strictly limited for a non-commercial purpose." No generating money tied to the Services. Follow the Trademark Guidelines. Deezer may restrict or remove access ([Terms of use](https://developers.deezer.com/termsofuse)). "Local Storage/Offline Storage of audio data is strictly forbidden" ([Guidelines](https://developers.deezer.com/guidelines)).
- **Not verified.** Rate limits (none appeared on the reviewed pages), whether new app registration is open, and metadata storage rules.
- **Fit notes.** Public search works without a key and returns several cover sizes, but the docs are gated and the limits are undocumented.

### Discogs

- **Could not verify.** discogs.com/developers and the API Terms of Use page on support.discogs.com both returned HTTP 403 (Cloudflare challenge) to WebFetch and curl on 2026-11-14. Search-engine snippets of the official developer page mention 60 requests per minute authenticated, 25 per minute unauthenticated, and a unique User-Agent. **These figures were not read from the page itself and should be confirmed in a browser** ([discogs.com/developers](https://www.discogs.com/developers), [API Terms of Use](https://support.discogs.com/hc/en-us/articles/360009334593-API-Terms-of-Use)).

---

## Games

### RAWG

- **Data / auth.** The key is passed as a query parameter, e.g. `GET https://api.rawg.io/api/platforms?key=YOUR_API_KEY`. Get it from "Get API Key" (account login). The page says User-Agent signing is being "slowly deprecated" in favor of key-based signing ([API docs](https://rawg.io/apidocs)). Search parameters and response fields were not reviewed in detail.
- **Free limits.** 20,000 requests a month on the free plan ([API docs](https://rawg.io/apidocs)).
- **Restrictions.**
  - "attribute RAWG as the source of the data and/or images," with an active hyperlink on every page that uses RAWG data.
  - No redistribution.
  - **Inconsistent wording:** the Free plan says non-commercial only, while the terms say free commercial use is allowed for projects under 100,000 MAU or 500,000 page views a month.
  - No caching rules were found.
  - Source: [API docs](https://rawg.io/apidocs).
- **Fit notes.** A simple query-string key and a monthly quota are easy to wire into Django. Attribution must appear on every page that shows RAWG data.

### IGDB (Twitch)

- **Sign-up / auth.** Register an app in the Twitch Developer Portal. The Twitch account must have Two-Factor Authentication enabled. Get an app access token with `POST https://id.twitch.tv/oauth2/token?client_id=...&client_secret=...&grant_type=client_credentials`. The token expires (`expires_in`, in seconds) and must be refreshed. Send `Client-ID` and `Authorization: Bearer <token>` headers ([IGDB API docs](https://api-docs.igdb.com/), via curl because WebFetch was blocked).
- **Data.** Requests are POSTs to `https://api.igdb.com/v4/<endpoint>` with an Apicalypse query body, e.g. `search "Halo"; fields name,release_dates.human;`. A dedicated search endpoint covers Characters, Collections, Games, Platforms, and Themes. Images are served from `images.igdb.com/igdb/image/upload/t_<size>/<image_id>.jpg` ([IGDB API docs](https://api-docs.igdb.com/)).
- **Rate limits.** 4 requests per second (429 if exceeded) and up to 8 open requests ([IGDB API docs](https://api-docs.igdb.com/)).
- **Restrictions.** "free for non-commercial usage under the terms of the Twitch Developer Service Agreement." Commercial partnerships go through partner@igdb.com. Browser calls fail on CORS, so requests must come from a backend or proxy ([IGDB API docs](https://api-docs.igdb.com/)). The Twitch Developer Service Agreement itself was not reviewed (caching and attribution not verified).
- **Fit notes.** A Django backend avoids the CORS problem. Token refresh logic is needed. 2FA is a sign-up hurdle.

### FreeToGame

- **Data.** `/api/games` (filter by `platform`, `category`, `sort-by`), `/api/game?id=`, and `/api/filter?tag=` ([API docs](https://www.freetogame.com/api-doc)). **No title-search endpoint is documented.** A live probe of `/api/games?platform=pc` returned 354 games with `id`, `title`, `thumbnail`, `short_description`, `genre`, `platform`, `publisher`, `developer`, `release_date`, and `game_url`.
- **Auth / limits.** No key. "Please avoid doing more than 10 requests per second" ([API docs](https://www.freetogame.com/api-doc)).
- **Restrictions.** "Free for personal and commercial use." Credit FreeToGame with an active hyperlink ([API docs](https://www.freetogame.com/api-doc)).
- **Fit notes.** Covers free-to-play games only. Without a search endpoint, search would mean filtering the full list locally.

### Giant Bomb

- **Could not verify.** www.giantbomb.com/api/ returned HTTP 403 (Cloudflare challenge) to WebFetch and curl on 2026-11-14 ([giantbomb.com/api](https://www.giantbomb.com/api/)). Search results surfaced only user-generated forum threads. These say the API is "strictly for non-commercial use" and give conflicting rate limits (200 per hour per resource, 400–450 per 15 minutes, and others). **Forum posts are not primary sources, and these points are unverified.**

---

## Open questions / unverified

1. **Discogs:** rate limits, User-Agent rule, auth options, image access, and API terms. The official pages were blocked (403). Check them in a browser.
2. **Giant Bomb:** whether the API is still active, plus its sign-up, rate limits, and terms. The official page was blocked (403).
3. **Google Books:** the per-key daily quota and whether a Google Cloud project needs billing or a credit card. The Google APIs Terms of Service (caching, attribution) were not reviewed.
4. **TMDB:** whether keeping only the TMDB `id` past 6 months counts as caching "information obtained from TMDB." The TV search reference pages were not opened.
5. **OMDb:** whether free-key search and detail responses include a `Poster` URL, and how CC BY-NC 4.0 applies to API data.
6. **TVmaze:** how CC BY-SA ShareAlike applies to an app that stores TVmaze data alongside user notes.
7. **Trakt:** API terms, image availability, and app-registration requirements were not reviewed.
8. **Spoonacular:** how the key is passed (header or query) and the points cost per endpoint.
9. **Edamam:** the auth method was not reviewed, since no free plan exists.
10. **Spotify:** whether storing only Spotify IDs plus user annotations is allowed under the "no databases of Spotify Content" rule, and which endpoints Development Mode apps can use after the postponed endpoint changes take effect.
11. **Deezer:** rate limits, metadata storage rules, and whether new apps can be registered. The docs are login-gated.
12. **Cover Art Archive:** image licensing, and the inconsistent rate-limit statement.
13. **IGDB:** caching and attribution terms in the Twitch Developer Service Agreement.
14. **RAWG:** which statement on free commercial use is current, and caching rules.
15. **Gutendex:** no terms, limits, or uptime commitment for the hosted instance.
16. **Additional providers:** none were added beyond the candidate list, apart from the Cover Art Archive as MusicBrainz's image companion.

## Sources

All accessed 2026-11-14.

**Books**
- Open Library Developers API: https://openlibrary.org/developers/api
- Open Library Search API: https://openlibrary.org/dev/docs/api/search
- Open Library Covers API: https://openlibrary.org/dev/docs/api/covers
- Google Books, Using the API: https://developers.google.com/books/docs/v1/using
- Google Books API Terms: https://developers.google.com/books/terms
- Gutendex: https://gutendex.com/
- Project Gutenberg Robot Access policy: https://www.gutenberg.org/policy/robot_access.html

**Movies & TV**
- TMDB Rate limiting: https://developer.themoviedb.org/docs/rate-limiting
- TMDB FAQ: https://developer.themoviedb.org/docs/faq
- TMDB API Terms of Use: https://www.themoviedb.org/api-terms-of-use
- TMDB Application authentication: https://developer.themoviedb.org/docs/authentication-application
- TMDB Search Movie: https://developer.themoviedb.org/reference/search-movie
- TMDB Image basics: https://developer.themoviedb.org/docs/image-basics
- OMDb: https://www.omdbapi.com/
- OMDb API key: https://www.omdbapi.com/apikey.aspx
- TVmaze API: https://www.tvmaze.com/api
- Trakt Required headers: https://developer.trakt.tv/docs/required-headers
- Trakt Rate limiting: https://developer.trakt.tv/docs/rate-limiting

**Recipes**
- TheMealDB API: https://www.themealdb.com/api.php
- TheMealDB Terms of Use: https://www.themealdb.com/terms_of_use.php
- Spoonacular Pricing: https://spoonacular.com/food-api/pricing
- Spoonacular Terms: https://spoonacular.com/food-api/terms
- Edamam Recipe Search API: https://developer.edamam.com/edamam-recipe-api

**Music**
- MusicBrainz API: https://musicbrainz.org/doc/MusicBrainz_API
- MusicBrainz Rate Limiting: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting
- MusicBrainz Data License: https://musicbrainz.org/doc/About/Data_License
- Cover Art Archive API: https://musicbrainz.org/doc/Cover_Art_Archive/API
- Last.fm API: https://www.last.fm/api
- Last.fm album.search: https://www.last.fm/api/show/album.search
- Last.fm API Terms of Service: https://www.last.fm/api/tos
- Spotify blog, 2024-11-27: https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
- Spotify blog, 2025-04-15: https://developer.spotify.com/blog/2025-04-15-updating-the-criteria-for-web-api-extended-access
- Spotify blog, 2026-02-06: https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security
- Spotify blog, 2026-07-23: https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates
- Spotify Quota modes: https://developer.spotify.com/documentation/web-api/concepts/quota-modes
- Spotify Web API Changelog, Feb 2026: https://developer.spotify.com/documentation/web-api/references/changes/february-2026
- Spotify Developer Terms: https://developer.spotify.com/terms
- Deezer API (login-gated): https://developers.deezer.com/api
- Deezer Guidelines: https://developers.deezer.com/guidelines
- Deezer Terms of use: https://developers.deezer.com/termsofuse
- Discogs developers (blocked, 403): https://www.discogs.com/developers
- Discogs API Terms of Use (blocked, 403): https://support.discogs.com/hc/en-us/articles/360009334593-API-Terms-of-Use

**Games**
- RAWG API docs: https://rawg.io/apidocs
- IGDB API docs: https://api-docs.igdb.com/
- FreeToGame API: https://www.freetogame.com/api-doc
- Giant Bomb API (blocked, 403): https://www.giantbomb.com/api/

**Live probes** (single anonymous requests, 2026-11-14, used only to confirm response field names): api.tvmaze.com, openlibrary.org/search.json, gutendex.com, themealdb.com (test key), freetogame.com, api.deezer.com, musicbrainz.org/ws/2, googleapis.com/books.

---

**Provider selection is deferred.** This page records findings only and makes no recommendation.
