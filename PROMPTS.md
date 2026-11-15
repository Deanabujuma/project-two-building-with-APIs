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