# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry —
  the log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-15 — Designed, prototyped, planned, built, tested and documented the HTTP.tv Django app and API

### Prompts
1. `/grill-me` We are continuing CIDM 3312 Project #2, building with APIs. Our project is Http.Tv, a dingo application using the TV maze external API. We have already completed and committed the API research, UV setup, verification script, automated tests, and README documentation. Review the existing repository, especially docs research free media Apis MD, and help me design the Dangjango application. Users should be able to search TV Maze save television shows to their personal collection, and track  Viewing status, progress, ratings, and notes. We must also build our own authenticated Django REST framework API with local search filtering sorting Pagination and a second Python script that reads and And updates data through our API. Ask me design questions one at a time and explain trade offs and recommended options we must complete at least one meaningful slash prototype during design process then create a PRD and implementation plan before building the application do not implement Django code yetWe are continuing CIDM 3312 Project #2, building with APIs. Our project is Http.Tv, a dingo application using the TV maze external API. We have already completed and committed the API research, UV setup, verification script, automated tests, and README documentation. Review the existing repository, especially docs research free media Apis MD, and help me design the Dangjango application. Users should be able to search TV Maze save television shows to their personal collection, and track  Viewing status, progress, ratings, and notes. We must also build our own authenticated Django REST framework API with local search filtering sorting Pagination and a second Python script that reads and And updates data through our API. Ask me design questions one at a time and explain trade offs and recommended options we must complete at least one meaningful slash prototype during design process then create a PRD and implementation plan before building the application do not implement Django code yet
2. I choose Option A: two models, Show and CollectionEntry. Store shared TVmaze show information once, using a unique tvmaze_id, and keep each user's personal tracking information in their CollectionEntry. Add a database constraint preventing duplicate entries for the same user and show. I want to use this design because it avoids duplicate show data and supports local searching, filtering, and sorting. Please continue to Question 2 without implementing anything yet.
3. I choose Option B, the practical set of Show fields. I agree with storing image URLs rather than downloading images, storing summaries as safely converted plain text, and storing genres in one text field for simplicity. I understand that a separate Genre model would provide more precise relational filtering but would add complexity. Please verify TVmaze's attribution and licensing requirements before implementation. Continue to the next design question without writing code yet.
4. B. Default to Plan to Watch. Keep status changes manual.
5. B. Use current season and episode, both optional and positive integers. Leave both blank until the user starts watching.
6. Rating A, Notes 1. Use optional 1–5 whole-star ratings and one optional notes field limited to 2,000 characters. Add created_at and updated_at timestamps. I also approve the rule that season and episode must both be filled in or both blank.
7. A. Use server-side TVmaze searches with a separate TVmaze client module. No caching for now.
8. B. Send only the tvmaze_id and fetch show details directly from TVmaze before saving. I agree with refresh-on-save, the "In your collection" indicator, and redirecting to the saved entry. Handle API failures gracefully.
9. A. Use Django's built-in authentication with a sign-up page and a minimal custom User model based on AbstractUser. Require login except for home, login, and sign-up. Restrict collection entries to their owners and return 404 for unauthorized access.
10. B. Use two Django apps: accounts and shows. Name the configuration package config.
11. A. Use Bootstrap 5 via CDN with regular Django forms. We can decide the colors and visual style during the UI prototype.
12. A. Use one combined detail and edit page, plus a separate delete-confirmation page. I approve the status tabs, title search, sorting, 12 entries per page, empty-state message, and deleting only the user's CollectionEntry.
13. A. Create a UI prototype with three structurally different My Collection layouts using Bootstrap 5. Let me compare them and choose or combine elements before we finalize the design. Do not build the Django application yet.
14. (Multi-line prompt, recorded exactly as sent.)

    ```text
    I choose **Option D: a custom Disney+-inspired interface for HTTP.tv.**

    I want you to revise `prototypes/ui-convention.html` to create a new visual direction that closely follows the formatting, positioning, proportions, and overall appearance of the two Disney+ screenshots I'm providing.

    **My priority is visual fidelity to the reference layouts, not simply making something that looks like a generic streaming website.** I want a premium, cinematic, dark interface that feels like a real consumer application.

    HTTP.tv is a television discovery and tracking application. Users will not watch videos on the website. They will discover shows, view information, save titles, and track their viewing progress, ratings, and notes.

    ## 1. Overall visual style

    Use the following styling throughout the application:

    - Near-black background (`#0B0B0F`), with dark charcoal sections.
    - Large, cinematic imagery that fills the width of the screen.
    - White typography, with muted gray secondary information.
    - Smooth dark gradients over background imagery so text remains readable.
    - Minimal borders, understated shadows, and subtle hover effects.
    - Rounded poster cards and buttons.
    - A modern streaming-platform aesthetic with generous horizontal spacing.
    - Desktop-first layout matching the 16:9 screenshots, while remaining responsive on mobile.
    - Bootstrap 5 for the layout and components, supplemented with custom CSS to achieve the reference appearance.

    Avoid colorful dashboards, white cards, traditional admin panels, or excessive boxed sections.

    ## 2. Navigation bar

    Match the positioning and appearance of the top navigation in my screenshots.

    - A thin black or nearly black navigation bar stretching across the entire screen.
    - User profile avatar and username on the far left.
    - Main navigation arranged horizontally across the upper center.
    - A search icon on the far right.
    - Small, clean icons beside navigation labels.
    - Subtle hover effects and an obvious active-page indicator.

    Use these navigation options:

    - Home
    - Discover
    - My Collection
    - Watching
    - Completed

    Display HTTP.tv branding in a way that fits the design without dominating the navigation.

    Do not include Live TV or video playback controls because HTTP.tv is not a streaming service.

    ## 3. Home page: Cinematic hero banner

    The home page should closely resemble the first Disney+ screenshot.

    The most important visual element is a **large, full-width cinematic hero banner** that fills most of the upper screen beneath the navigation.

    ### Background image

    - Use one television show as the featured title.
    - Display a large, high-quality, static background image.
    - The image should fill the hero area using `background-size: cover`.
    - Position the focal subject toward the center or right side.
    - Apply a strong left-to-right dark gradient so the left side supports readable text while the artwork remains prominent.
    - Add a subtle bottom gradient that transitions into the page background.
    - Do not autoplay videos, create a trailer player, or add sound.

    TVmaze primarily provides show posters rather than guaranteed cinematic backdrops. Verify what images are available. If a wide image is unavailable, use the poster as part of a deliberately designed fallback instead of stretching a narrow poster across the screen.

    ### Hero information

    Position all primary text in the left third of the hero, approximately where Disney+ displays its featured title information.

    Include:

    - Large show title or available logo artwork.
    - Premiere year.
    - TV content rating, if verified data is available.
    - Genres.
    - Television network or web channel.
    - Short description, approximately two lines.

    Below the description, place two buttons:

    **MORE INFO** — White pill-shaped primary button with dark text.

    **+ ADD TO COLLECTION** — Dark, circular or outlined secondary button.

    If a show is already saved, change the second button to indicate that it is in the user's collection.

    Do not include Play, Watch Now, or video controls.

    ### Content rows below the banner

    Immediately below the hero, display horizontal rows of show artwork, similar to the first reference screenshot.

    Possible rows:

    - Continue Tracking
    - My Watchlist
    - Recently Added
    - Completed Shows

    Use large, visually appealing show cards with minimal text. Show additional information on hover or beneath the artwork.

    Use real TVmaze data where available. Avoid presenting fabricated recommendations as if they came from a recommendation engine.

    ## 4. Show details page: Match the second Disney+ screenshot

    This is especially important.

    When the user clicks **MORE INFO**, I want a show details page structured like the second screenshot.

    It should feel like an extension of the cinematic hero page, not a standard Django detail form.

    ### Background

    - Use a large, static hero image spanning the full content width.
    - Maintain the dark gradient treatment from the home page.
    - The artwork should remain visible behind the information.
    - Keep the page immersive and cinematic.

    ### Left-side information

    On the left side of the hero, include:

    - Large show title.
    - Content-rating badge, if available.
    - Premiere year.
    - Show status, such as Running or Ended.
    - Genres.
    - Runtime, where available.
    - Network or web channel.
    - TVmaze rating.

    In my screenshot, Disney+ has small badges for PG-13, HD, CC, and audio descriptions.

    I want a similar **horizontal row of small metadata badges**, but only display information HTTP.tv can actually verify. Do not fabricate HD, CC, accessibility, or content-rating information.

    Below the metadata, include the relevant buttons:

    - **ADD TO MY COLLECTION**
    - **VIEW ON TVMAZE**

    For a show already saved, replace Add to My Collection with **VIEW MY TRACKING** or **EDIT MY PROGRESS**.

    ### Right-side description

    Unlike a typical streaming page, I want the show description positioned in a dedicated area toward the **right side of the hero**, balanced against the title and metadata on the left.

    The summary should be readable and have enough space without obscuring the background artwork.

    Use a subtle translucent dark overlay if necessary.

    ### Streaming services / Where to watch

    Below the primary metadata, include a visually attractive horizontal section labeled **WHERE TO WATCH**.

    I want this section to resemble the row of streaming-service logos or buttons commonly found on streaming and entertainment websites.

    However, TVmaze does not necessarily supply accurate availability across Netflix, Hulu, Disney+, Max, and other platforms.

    Therefore:

    - Show the verified original network or web channel when available.
    - Do not invent streaming availability.
    - If a real provider-availability source is not integrated, label the section appropriately and display only verified network/channel information.
    - The prototype may visually demonstrate additional provider badges, but clearly label them as illustrative and do not build false availability into the production application.

    ## 5. Suggested, Extras, and Franchise section

    Below the cinematic hero area, create a horizontal navigation row similar to the second screenshot:

    **SUGGESTED | EXTRAS | FRANCHISE**

    Directly underneath, show a horizontal collection of related television title cards.

    I specifically want the card images arranged in a row, with proportions and spacing close to the Disney+ screenshot.

    - Use wide thumbnails where suitable images are available.
    - Otherwise use poster cards with consistent aspect ratios.
    - Provide subtle rounded corners.
    - Add a gentle scale or border highlight on hover.
    - Allow horizontal scrolling when more titles are available.

    For the initial version, these sections can be prototypes rather than working recommendation features. Do not invent actual franchise relationships or claim that TVmaze provides recommendations unless verified.

    ## 6. My Collection page

    I still want users to track their shows.

    Keep the same premium dark visual style, but adapt it to the existing features we designed.

    The collection should have:

    - Poster cards.
    - Status filters: All, Plan to Watch, Watching, On Hold, Completed, Dropped.
    - Search by show name.
    - Sorting by recently updated, title, or personal rating.
    - Pagination.
    - Viewing progress displayed as Season X, Episode Y.
    - Personal star ratings.
    - A clearly visible option to open and update each collection entry.

    Keep the already-approved combined tracking/detail form and delete-confirmation flow.

    Do not sacrifice usability to imitate Disney+.

    ## 7. Responsive behavior

    At desktop width, the interface should closely follow the screenshots.

    At tablet and mobile widths:

    - Reduce hero height appropriately.
    - Keep text readable.
    - Collapse navigation where necessary.
    - Stack the show description beneath the title when a two-column layout becomes too narrow.
    - Let horizontal card rows scroll naturally.

    Avoid horizontal overflow or overlapping text.

    ## 8. Prototype deliverable

    Before implementing Django, please update the existing UI prototype to demonstrate this new visual direction.

    Show at least:

    1. The home page with the cinematic hero and horizontal show rows.
    2. The show details page with left-side title/metadata, right-side description, Where to Watch, and related-show sections.
    3. The My Collection page using the same dark visual system.

    Use the two attached screenshots as the primary design references.

    Preserve the existing prototype variants if feasible, so I can explain how the design evolved during my Design Defense.

    Use HTML, Bootstrap 5, CSS, and minimal JavaScript. Keep this a standalone prototype, separate from Django production code.

    **Do not begin implementing the Django application yet.**

    Once the prototype is updated, tell me exactly how to open it in my browser, explain any limitations imposed by TVmaze's available data and images, and stop so I can review and approve the design before continuing to the PRD.
    ```

15. I approve Direction D as the overall visual design for HTTP.tv. Before finalizing the prototype, please make four refinements: (1) remove the illustrative streaming-provider placeholders and show only verified network or web-channel information, (2) improve the My Tracking form layout so it uses the available desktop width more effectively, (3) make the horizontal show rows more visually consistent in spacing, hover effects, and progress labels, and (4) preserve the cinematic Abbott Elementary details-page layout with metadata on the left and the description on the right. Keep the original A/B/C prototype for my Design Defense. Do not implement Django yet. Show me the revised result and stop for approval.
16. I approve the revised Direction D cinematic prototype as the visual design for HTTP.tv. Preserve both prototype versions for my Design Defense. Continue with the next /grill-me design question, one question at a time. Do not implement Django yet.
17. A. Add all five fields to Show. Use the widest TVmaze background image at least 1920px wide, with a poster fallback when unavailable. Keep the save-time fetch and refresh-on-save behavior.
18. A. Use one show details page at /shows/<tvmaze_id>/ with My Tracking as a tab for saved shows. I approve the proposed error handling, default tabs, and local genre-based suggestions. Viewing a show must not automatically save it.
19. Extras A, Franchise 1. Fetch seasons and cast from TVmaze only when Extras is opened, with graceful error handling. Remove the Franchise tab because we don't have verified franchise data.
20. A. Use DRF TokenAuthentication and SessionAuthentication. Require authentication for all collection API endpoints, enforce owner-only access with 404 for other users' entries, and read the token from an environment variable in the second script. Keep tokens out of Git.
21. A. Use DRF TokenAuthentication and SessionAuthentication. Require authentication for all collection API endpoints, enforce owner-only access with 404 for other users' entries, and read the token from an environment variable in the second script. Keep tokens out of Git.
22. A. Use full CRUD at /api/collection/, nested read-only show data, and POST by tvmaze_id. I approve shared model validation, read-only fields, the proposed error codes, and the browsable API. Ensure the serializer also enforces the relevant validation.
23. A. Use DRF SearchFilter, OrderingFilter, django-filter, and page-number pagination (12 per page, maximum 50). I approve 400 errors for invalid filters, unrated entries sorting last, and shared filtering logic between the web app and API. Please test the unrated sorting behavior.
24. A. Use scripts/httptv_client.py with list, update, and next commands. I approve the environment-variable configuration, friendly error handling, exit codes, and leaving out add. The next command should increment the episode number without automatically changing seasons.
25. A. Use SQLite with a Git-ignored .env file and a committed .env.example. Require DJANGO_SECRET_KEY, enable Django Admin, and manage Django, DRF, and django-filter through uv. Keep all secrets and API tokens out of Git. Continue to the next question without implementing yet.
26. A. Use pytest with pytest-django for everything. Mock TVmaze and external HTTP calls in automated tests, use DRF APIClient for API tests, and add tests during each implementation phase using TDD where appropriate. Include a test-only secret key and a README manual verification checklist.
27. A. Accept all 12 out-of-scope items as written. Keep the project focused on the assignment requirements. Before finalizing the PRD, verify whether the Project #2 instructions require deployment. Then summarize all 23 design decisions for my final review. Do not implement Django yet.
28. I approve all 23 design decisions for HTTP.tv. Based on the Project #2 assignment instructions I have reviewed, submission requires a public GitHub repository and does not explicitly require deployment, so proceed with local-only development unless new assignment evidence says otherwise. Preserve both UI prototype versions, the existing TVmaze verification script, and its 44 tests. Please use the /to-prd skill to create a complete PRD based on our approved decisions, the existing research, and the prototype. Include measurable acceptance criteria, all required API features, both scripts, testing, and Design Defense considerations. Stop after creating the PRD so I can review it before the implementation plan. Do not write Django code yet.
29. I approve the PRD's overall direction and all three additional edge-case rules. Please make channel_type and channel_country explicit optional fields on Show, while retaining network for the channel name. Update the relevant PRD requirements and acceptance criteria accordingly. Then perform a final consistency check against our 23 approved decisions and the Project #2 requirements, and show me any conflicts or missing requirements. Do not create the implementation plan or write Django code yet.
30. For items 1–6: (1) Use Option A and link the Where to Watch card to the TVmaze page without adding another model field. (2) Keep the approved behavior: web collection search matches show titles, while API search matches titles and notes; document the distinction while sharing applicable filtering logic. (3) Approve POST /collection/add/. (4) Approve public navigation showing Log in and Sign up for logged-out users. (5) Add HTTPTV_API_TOKEN and HTTPTV_API_URL as safe placeholders in .env.example. (6) Project #2 DOES require REFLECTION.md. Add it as an explicit deliverable with the five assigned topics: API research/provider decision, prototype, tracing the second script's update through the API, explaining local search/filter/sort/pagination, and bugs/corrections with before-and-after evidence. Do not write the reflection answers prematurely; they must reflect our actual completed work. Update the PRD, perform a final consistency check, and stop for my approval before creating the implementation plan. Do not implement Django yet.
31. I approve the finalized PRD at prd/httptv.md. Please use the /prd-to-plan skill to create an implementation plan based on the approved PRD, research, and Direction D prototype. Organize the work into small, sequential tracer-bullet phases, each with specific tasks, acceptance criteria, tests, and a Git commit checkpoint. Include the Django foundation, data models, TVmaze integration, web pages, authentication, REST API, filtering and pagination, second client script, documentation, and REFLECTION.md. Preserve our existing verification script and its 44 tests. Schedule compatibility checks and custom User setup before migrations. Include checkpoints for manual verification and evidence collection for the Design Defense. Create the plan only, show me the phase breakdown, and stop for approval before implementing Django or committing anything.
32. I approve the implementation plan with two refinements: (1) split Phase 4 into models/migrations and the save flow/basic show page; (2) keep the evidence log at docs/evidence-log.md and screenshots at docs/evidence/, excluding secrets and personal information. Update README and evidence incrementally rather than leaving all documentation until the end. My deadline is tonight at 11:59 PM Central, but I want thorough, tested work—not rushed shortcuts. Start Phase 0, then proceed through the planned phases in dependency order. Auto Mode may handle routine decisions, but run tests and show me a concise completion summary at each phase boundary. Keep the original 44 tests intact. Make local commits at verified checkpoints; ask before pushing to GitHub. Prioritize having a working, tested, documented submission ready before the deadline.
33. (Multi-line prompt, recorded exactly as sent.)

    ```text
    I approve committing Phase 13.

    Before moving forward, verify that the implementation meets the approved PRD and that the full test suite passes.

    Then push all completed commits to GitHub and verify that origin/main is up to date.

    After that, begin Phase 14 and draft REFLECTION.md using only real evidence from the project. I want to review and edit the reflection before its final commit.

    Do not redo completed phases or restart implementation.
    ```

34. (Multi-line prompt, recorded exactly as sent.)

    ```text
    The GitHub push is confirmed. Let's finish Phase 14.

    Please show me the seven sections marked ✏️ in REFLECTION.md, including the questions and enough surrounding context to understand each one.

    Do not commit the reflection yet. I want to answer these in my own words with help organizing my thoughts.

    After I review and approve the completed reflection, we'll commit it, update PROMPTS.md, push everything, and verify the final GitHub submission.
    ```

35. (Multi-line prompt, recorded exactly as sent.)

    ```text
    Please format REFLECTION.md the same way we formatted
    my previous CIDM 3312 Project #1 reflection
    (Applicant Tracking System).

    Use the previous REFLECTION.md as the formatting reference.

    Keep the original assignment questions as numbered
    Markdown headings, using this structure:

    # Project #2: HTTP.tv

    ## Question 1 — API Research and Provider Decision

    ## Question 2 — Prototype and Design Decisions

    ## Question 3 — Tracing an API Update

    ## Question 4 — Search, Filtering, Sorting, and Pagination

    ## Question 5 — Bugs, Corrections, and Lessons Learned

    Put my reflection paragraphs directly under each
    question, just like my previous projects.

    Keep the existing technical evidence, examples,
    and explanations accurate.

    Do not add pencil emojis, decorative symbols,
    or "DRAFT" labels.

    Make the language natural and straightforward,
    like a college programming student explaining
    what they learned.

    Show me the finalized REFLECTION.md for review
    before committing or pushing.
    ```

36. (Multi-line prompt, recorded exactly as sent.)

    ```text
    I changed my mind about REFLECTION.md.

    I only wanted you to create the REFLECTION.md file,
    not answer the reflection questions for me.

    Please keep REFLECTION.md in the root of my project,
    using the same Markdown format as my previous
    CIDM 3312 reflections.

    Include the five assigned reflection questions as
    numbered headings, using their original wording.

    Leave the space underneath each question blank
    so I can write my own answers.

    Do not generate answers, personal experiences,
    or explanations on my behalf.

    Do not change any other project files.

    Show me REFLECTION.md before committing anything.
    ```

37. (Multi-line prompt, recorded exactly as sent.)

    ```text
    I've finished writing my REFLECTION.md.

    Please keep R18 in docs/evidence-log.md.

    Review REFLECTION.md for Markdown formatting and
    spelling only. Do not rewrite my personal answers.

    Update PROMPTS.md to document this session accurately.

    Run the final tests, commit all remaining project
    changes, and push to origin/main.

    Verify that the local and remote main branches match,
    that REFLECTION.md is included on GitHub, and that
    the working tree is clean.

    Give me the final GitHub repository URL.
    ```


### Summary
- **Outcome:**
  - **Design:** 23 design decisions made through `/grill-me`, one question at a time.
  - **Prototype:** three v1 layouts (A poster grid, B dense table, C list + detail), then Direction D, a cinematic dark design, refined in four steps. Both versions are kept in `prototypes/`.
  - **PRD and plan:** `prd/httptv.md` with 57 acceptance criteria, and `plans/httptv.md` with phases 0–14 (Phase 4 split into 4a/4b).
  - **Build:** phases 0–13 committed locally at verified checkpoints. This produced:
    - a custom User model, sign up and log in;
    - TVmaze search, save by `tvmaze_id` only, show pages with Suggested and Extras tabs;
    - tracking with shared validation (model, DRF serializer and database constraints);
    - My Collection and a personalized home page;
    - a DRF API with token/session auth, CRUD, search, strict filters, nulls-last ordering and pagination;
    - `scripts/httptv_client.py` (`list`, `update`, `next`).
  - **Tests:** 485 passing, including the original 44 verification-script tests, unchanged.
  - **Evidence:** `docs/evidence-log.md` records 13 bugs/corrections (B1–B13), 18 real request/response captures (R1–R18) and 16 verification notes (V0–V16). Screenshots are in `docs/evidence/`.
  - **Final checks:** a fresh-clone check, a full manual checklist, and a PRD acceptance-criteria audit.
  - **Push:** pushed to GitHub after the user approved.
  - **REFLECTION.md:** created as a template; the user wrote all of the answers.
- **Deviations:**
  - **Prompt 14:** chose a fourth visual direction (D, a custom Disney+-inspired dark design) instead of any of the three prototype layouts A–C. Prompt 15 then asked for four specific refinements before approving.
  - **Prompt 19:** removed the Franchise section requested in prompt 14, because TVmaze has no verified franchise data.
  - **Prompts 27–28:** asked for a check on whether deployment is required, then decided on local-only development from the assignment instructions.
  - **Prompt 29:** added explicit `channel_type` and `channel_country` fields.
  - **Prompt 30:** settled six PRD consistency items and added REFLECTION.md as a required deliverable with five topics.
  - **Prompt 32:** refined the plan (split Phase 4; evidence log at `docs/evidence-log.md`; documentation updated incrementally), required commits only at verified checkpoints, and required asking before any push.
  - **Prompt 33:** asked for a PRD verification before pushing. This found that AC49 (client changes visible in the web app) had not been checked in the browser; it was checked and recorded (V16) before the push.
  - **Prompts 34–36 and REFLECTION.md:**
    - The AI drafted reflection answers from the evidence log with marked places for the user's own words (prompt 33).
    - The user asked to see the marked places (prompt 34), then asked for the draft in their Project #1 format (prompt 35).
    - Then the user changed their mind (prompt 36): REFLECTION.md should contain only the question headings, and the user writes every answer.
    - The AI-drafted text was discarded. In prompt 37, the AI only checked formatting and spelling: it added a blank line after the title and a final newline, and changed no wording.
  - **Prompt 37:** kept the R18 server-log entry in the evidence log.
  - Prompts 20 and 21 are the same message, sent twice; it was answered once.
- **Sideways:**
  - **Context compaction:** the conversation ran out of context during Phase 9 and continued from a written summary. Work resumed without redoing completed phases.
  - **Shell quoting:**
    - heredocs and quoted edits failed several times;
    - twice a regex `\b` became a literal backspace byte, caught by existing tests (B8);
    - later edits used files or Python scripts instead.
  - **Bugs found by tests or real data** (all in the evidence log with before/after output):
    - B6: identical "The Office" search cards;
    - B7: hidden fallback poster;
    - B8: space before punctuation;
    - B9: Extras accepting a non-show response;
    - B10: SQL NULL logic let "season only" rows pass a CHECK constraint;
    - B11: a duplicated error message, where the AI's first guess at the cause was wrong;
    - B12: web/API message mismatch;
    - B13: the client rejected `--ordering -rating`.
  - **The AI's own test and command mistakes** (each time the code was right):
    - a pagination assertion that mixed `and`/`or`;
    - expecting "Dark" to match `search=e`;
    - expecting a trailing slash on the TVmaze footer link;
    - a fresh-clone curl to `/api//collection/` that returned 404.
  - **Gap found during Phase 13:** no automated test covered the attribution footer (AC50). `test_attribution.py` was added.
  - **Debug 404:** with `DJANGO_DEBUG=true`, unknown URLs show Django's debug 404 page rather than the custom one. This is expected Django behaviour; the custom page is tested with debug off.
  - **Miscounts and misreadings:** the AI told the user there were seven marked reflection sections when there were five (the count included the draft note's own lines). It also briefly misread REFLECTION.md's line endings as CRLF; they were LF.
  - **Privacy:** the demo account's password and the API token stayed outside the repository (token only in the Git-ignored `.env`). A search of every commit found no token or secret key.

## 2026-11-14 — Researched free media APIs, chose TVmaze, built and tested the TVmaze verification script

### Prompts
1. `/research` Find free external APIs  For Django  Application where users can search for items, save selected items, and add their own notes, ratings, or progresses. Explore books, movies, television, recipes, music, and games. Compare promising providers using official documentation, Including available data, free limits, sign up requirements, API keys and restrictions. Save cited findings in a markdown file in this repository. Do not select a provider or implement anything yet.
2. `/grill-me` I have chosen TVmmaze as the external API provider for mmy Project #2 Django application, HTTP.tv. The application will help users discover TV shows, and track their viewing progress, ratings, and notes. Use the findings in docs/research/free-media-apis.md. For now, help me design only the required external API verification script. It must accept user input, make a real request to TVmaze, display useful results, and handle empty results and failed requests. This is for a future Django project that must use uv. Ask me questions and explain significant decisions before implementing anything. Do not begin building the Django application yet.
3. A
4. A
5. A
6. C, I agree with trimming whitespace and rejecting blank input before making an API request.
7. B option. Display the standard fields with appropriate fall backs for missing values. Number the results and preserve TVmazes relevance order. I would prefer displaying up to 10 results, while reporting the total number returned. Please verify the endpoints results behavior for before implementing
8. Option BI Approve separate user friendly messages for timeouts connection errors HTTP errors and invalid JSON Or Unexpected response data. I also approved the 10 second time out exit codes of zero for successful or empty results and one for errors and the UTF-8 Output fix. Continue to the next question without implementing yet.
9. Option B create the script at scripts/verify_tvmaze.py. I want the scripts kept separateFrom the Django application and organized in one folder. Continue to the next question without implementing yet.
10. I choose option C both manual and automated pytest Testing. I agree with organizing the script into four functions: get_search_term(), search_shows(term), format_show(show), and main(). I want to verify real API request manually and use mocked responses to test failure handling. Continue to the next question without implementing yet.
11. Option B use HTTP.tv-verify/0.1As the custom user dash agent. Define it as a constant alongside the TV maze search URL and 10 second timeout I want to include personal contact information in the public repository. Continue to the final set up question without implementing yet
12. (Correction) To clarify, I do NOT want to include personal contact information. Keep the User-Agent as HTTP.tv-verify/0.1. For Question 10, I choose B: uv init --bare, project name httptv, and Python 3.14 for my local environment. Before setting requires-python, verify compatibility with the required Django stack and recommend a reasonable supported version range. Please summarize all approved design decisions for my review before implementing anything.
13. I approve requires-python = ">=3.12" and tests/test_verify_tvmaze.py.I also approved the complete verification script design as summarized. Please begin implementation one step at a time. Start with setting up the UV project and its dependencies only. Explain what you're creating, run the necessary verification, and stop for my approval before writing the Python script or its test do not commit or push anything yet.
14. Yes proceed with writing scripts/verify_tvmaze.py According to our approved design. Do not write the pytest tests yet. After creating the script, explain each function and show me how it works. Run a syntax check and stop for my approval before running the real API tests, creating additional files, committing, or pushing.
15. Yes, I approve all five implementation choices. Please proceed with the real TVmaze manual tests for "the office", "xqzzvvnotashow", and "café", as well as the blank-input test. Verify the actual output and exit codes for each case. Do not turn off my Wi-Fi or change any network settings. After testing, summarize the results and stop for my approval before writing pytest tests, committing, or pushing.
16. Yes, please fix both cosmetic issues: display a single year when a show begins and ends in the same year, and align the details consistently for all numbered results, including result 10. Then create tests/test_verify_tvmaze.py using mocked responses for all the scenarios we approved. Run the automated tests and explain the results, including any failures and corrections. Do not commit, push, or modify unrelated files. Stop for my approval after testing.
17. (Same text as prompt 16, sent a second time.)
18. Please rerun the real TVmaze search for "the office" and confirm the updated year formatting and alignment for results 1–10. Then add a concise README section explaining the TVmaze verification script, how to run it with uv, how to provide search input, and how to run the pytest tests. Preserve the existing README content. Stop after these steps and show me the results. Do not commit, push, or modify PROMPTS.md yet.
19. Append a session log to PROMPTS.md at the repo root, under today's date, newest entry at the top. Record every prompt I gave you this session, in order, including any corrections. End the entry with a short summary: the outcome, any places where I deviated from a recommended answer or asked follow-up questions, and anything that went sideways. Follow the existing PROMPTS.md instructions exactly. Do not rewrite or remove earlier entries. After updating it, show me the session summary and git status. Do not commit or push yet.

### Summary
- **Outcome:** Created `docs/research/free-media-apis.md`, a cited comparison of 20 free media APIs with no recommendation. After TVmaze was chosen, designed the verification script through 10 grill-me questions. Set up a standalone uv project (`httptv`, `requires-python = ">=3.12"`, Python 3.14 pinned, `requests` plus dev-only `pytest`, `uv.lock`). Built `scripts/verify_tvmaze.py`, which uses fuzzy search, a 10 s timeout, the User-Agent `HTTP.tv-verify/0.1`, up to 10 numbered results with fallbacks, friendly error messages, and exit codes 0/1. Added `tests/test_verify_tvmaze.py` with 44 mocked tests, all passing, and a README section on running and testing the script. Manual real-API checks passed: "the office", "xqzzvvnotashow", "café", and blank input. Nothing committed or pushed.
- **Deviations:**
  - Results: chose "display up to 10 results while reporting the total" instead of the recommended "show all results". TVmaze caps fuzzy search at 10, so the limit is a safeguard.
  - Follow-ups asked: verify the endpoint's real behavior before implementing (done with live requests), and verify Django and DRF Python compatibility before setting `requires-python`.
  - Correction: prompt 11 said "I want to include personal contact information", which contradicted choosing option B. This was flagged and clarified in prompt 12 as do NOT include.
  - Approved five implementation choices not in the original design (the "Not yet aired, In Development" wording, "Not yet aired" only for In Development, `2017–N/A`, a catch-all request error plus required `id`/`name`/`url`, and joining argument words). Then requested both cosmetic fixes the AI raised (single year for same-year shows, two-character number alignment).
  - All other questions accepted the recommended option.
- **Sideways:**
  - The background research agent finished without delivering its report. The saved Markdown file was read in full and summarized instead.
  - During endpoint verification, one probe crashed decoding TVmaze JSON with the Windows default encoding, and a `café` request returned HTTP 400 because the shell garbled the text. Both were probe bugs; re-verified with proper UTF-8, and the encoding lesson led to the UTF-8 output fix.
  - `uv init` silently added this repo as a member of an unrelated uv workspace in the home folder (`~/pyproject.toml`), which would have put the lockfile and venv outside the repo. Caught from uv's output; only the added line was removed and the repo confirmed standalone with `uv lock -v`.
  - The first blank-prompt check reported exit code 0 because of a bug in the test command. Rerun correctly, it showed 1.
  - The first "not yet aired" label had nested parentheses and was reworded.
  - Prompt 16 was sent twice. The work was not redone; the tests were rerun to confirm the state.
  - All 44 tests passed on the first run, so no test was shown to fail against a broken script.