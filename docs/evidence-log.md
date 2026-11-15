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

---

## 2. Requests and responses

*(Captured from the running app in Phases 9, 11 and 12.)*

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
