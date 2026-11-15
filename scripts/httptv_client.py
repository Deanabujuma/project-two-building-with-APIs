"""Command-line client for the HTTP.tv REST API.

Reads and updates YOUR collection through the authenticated API (never the database directly).

Setup:
    1. Start the server:  uv run --env-file .env python manage.py runserver
    2. Get a token:       POST http://127.0.0.1:8000/api/auth/token/ with your username and password
    3. Put it in .env:    HTTPTV_API_TOKEN=<token>      (never commit it)

Usage (run with uv so .env is loaded):
    uv run --env-file .env python scripts/httptv_client.py list [--status watching] [--search sev]
                                                              [--ordering -rating] [--page 2] [--page-size 12]
    uv run --env-file .env python scripts/httptv_client.py update ID [--status S] [--season N|none]
                                                              [--episode N|none] [--rating 1-5|none] [--notes TEXT]
    uv run --env-file .env python scripts/httptv_client.py next ID

Optional: HTTPTV_API_URL (default http://127.0.0.1:8000/api/).
Exit codes: 0 success, 1 error (message on stderr), 2 invalid command line.
"""

import argparse
import math
import os
import sys

import requests

DEFAULT_API_URL = "http://127.0.0.1:8000/api/"
TIMEOUT = 10
STATUSES = ["plan_to_watch", "watching", "on_hold", "completed", "dropped"]
UPDATE_FIELDS = {"status": "status", "season": "current_season", "episode": "current_episode",
                 "rating": "rating", "notes": "notes"}


class ClientError(Exception):
    """A problem to report to the user as one line on stderr."""


# --- HTTP -------------------------------------------------------------------------------------------------------

def api_url():
    return os.environ.get("HTTPTV_API_URL", DEFAULT_API_URL).rstrip("/") + "/"


def call(method, path, entry_id=None, **kwargs):
    """Send one request and return the decoded JSON body, or raise ClientError."""
    token = os.environ.get("HTTPTV_API_TOKEN", "").strip()
    url = api_url() + path
    try:
        response = requests.request(method, url, headers={"Authorization": f"Token {token}"},
                                    timeout=TIMEOUT, **kwargs)
    except requests.Timeout:
        raise ClientError(f"HTTP.tv did not respond within {TIMEOUT} seconds.")
    except requests.ConnectionError:
        raise ClientError(f"Could not connect to HTTP.tv at {api_url()}. Is the server running?")
    except requests.RequestException as error:
        raise ClientError(f"Request to HTTP.tv failed: {error.__class__.__name__}.")

    if response.status_code in (401, 403):
        raise ClientError(f"HTTP.tv rejected your token (HTTP {response.status_code}). "
                          "Check HTTPTV_API_TOKEN in .env.")
    if response.status_code == 404 and entry_id is not None:
        raise ClientError(f"No entry with ID {entry_id} in your collection.")
    if response.status_code == 400:
        raise ClientError("HTTP.tv refused the change:\n" + field_errors(read_json(response)))
    if response.status_code not in (200, 201):
        raise ClientError(f"HTTP.tv sent an unexpected response (HTTP {response.status_code}).")
    return read_json(response)


def read_json(response):
    try:
        return response.json()
    except ValueError:
        raise ClientError("HTTP.tv's response could not be read (it was not JSON).")


def field_errors(body):
    if not isinstance(body, dict):
        return "  (no details)"
    lines = []
    for field, messages in body.items():
        for message in messages if isinstance(messages, list) else [messages]:
            lines.append(f"  {field}: {message}")
    return "\n".join(lines) or "  (no details)"


def check_entry(body):
    if not (isinstance(body, dict) and isinstance(body.get("show"), dict) and "id" in body):
        raise ClientError("HTTP.tv's response could not be read (not a collection entry).")
    return body


# --- Formatting -----------------------------------------------------------------------------------------------------

def progress_text(entry):
    season, episode = entry.get("current_season"), entry.get("current_episode")
    if season is None or episode is None:
        return "Not started"
    return f"Season {season}, Episode {episode}"


def rating_text(entry):
    return "Not rated" if entry.get("rating") is None else f"{entry['rating']}/5"


def entry_line(entry):
    return (f"{entry['id']:>5}  {entry['show'].get('name', '?')[:32]:<32}  {entry.get('status', ''):<13}  "
            f"{progress_text(entry):<22}  {rating_text(entry)}")


# --- Commands ---------------------------------------------------------------------------------------------------------

def cmd_list(args):
    params = {key: value for key, value in [("status", args.status), ("search", args.search),
                                            ("ordering", args.ordering)] if value is not None}
    params.update(page=args.page, page_size=args.page_size)
    body = call("GET", "collection/", params=params)
    if not (isinstance(body, dict) and isinstance(body.get("results"), list) and "count" in body):
        raise ClientError("HTTP.tv's response could not be read (not a page of entries).")
    if not body["results"]:
        print("No entries found.")
        return 0
    print(f"{'ID':>5}  {'Show':<32}  {'Status':<13}  {'Progress':<22}  Rating")
    for entry in body["results"]:
        print(entry_line(check_entry(entry)))
    pages = max(1, math.ceil(body["count"] / args.page_size))
    print(f"\nPage {args.page} of {pages} ({body['count']} entries)")
    return 0


def cmd_update(args):
    changes = {api_field: getattr(args, option) for option, api_field in UPDATE_FIELDS.items()
               if getattr(args, option) is not MISSING}
    if not changes:
        raise ClientError("Give at least one of --status, --season, --episode, --rating, --notes.")
    entry = check_entry(call("PATCH", f"collection/{args.id}/", entry_id=args.id, json=changes))
    print(f"Updated entry {entry['id']}: {entry['show'].get('name', '?')} | {entry.get('status')} | "
          f"{progress_text(entry)} | {rating_text(entry)}")
    return 0


def cmd_next(args):
    """Mark the next episode watched: episode + 1. Season and status are never changed.

    An entry with no progress goes to Season 1, Episode 1. Moving to a new season is a
    deliberate choice, so it is done with `update --season N --episode 1`.
    """
    entry = check_entry(call("GET", f"collection/{args.id}/", entry_id=args.id))
    if entry.get("current_season") is None or entry.get("current_episode") is None:
        changes = {"current_season": 1, "current_episode": 1}
    else:
        changes = {"current_episode": entry["current_episode"] + 1}
    updated = check_entry(call("PATCH", f"collection/{args.id}/", entry_id=args.id, json=changes))
    print(f"{updated['show'].get('name', '?')}: {progress_text(entry)} -> {progress_text(updated)}")
    return 0


# --- Command line -----------------------------------------------------------------------------------------------------

MISSING = object()  # "option not given" (different from "none", which clears a value)


def number_or_none(text):
    if text.lower() == "none":
        return None
    try:
        return int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a whole number or 'none', got {text!r}")


def build_parser():
    parser = argparse.ArgumentParser(prog="httptv_client", description="Read and update your HTTP.tv collection.")
    commands = parser.add_subparsers(dest="command", required=True)

    list_cmd = commands.add_parser("list", help="list your collection")
    list_cmd.add_argument("--status", choices=STATUSES)
    list_cmd.add_argument("--search", help="text in the show name or your notes")
    list_cmd.add_argument("--ordering", help="e.g. -rating, show__name, -updated_at")
    list_cmd.add_argument("--page", type=int, default=1)
    list_cmd.add_argument("--page-size", type=int, default=12)
    list_cmd.set_defaults(handler=cmd_list)

    update = commands.add_parser("update", help="change an entry's tracking fields")
    update.add_argument("id", type=int)
    update.add_argument("--status", choices=STATUSES, default=MISSING)
    update.add_argument("--season", type=number_or_none, default=MISSING, help="number, or 'none' to clear")
    update.add_argument("--episode", type=number_or_none, default=MISSING, help="number, or 'none' to clear")
    update.add_argument("--rating", type=number_or_none, default=MISSING, help="1-5, or 'none' to clear")
    update.add_argument("--notes", default=MISSING)
    update.set_defaults(handler=cmd_update)

    next_cmd = commands.add_parser("next", help="mark the next episode watched (episode + 1)")
    next_cmd.add_argument("id", type=int)
    next_cmd.set_defaults(handler=cmd_next)
    return parser


def join_ordering(argv):
    """Allow `--ordering -rating`: argparse would read "-rating" as an option, so join it as --ordering=-rating."""
    joined, i = [], 0
    while i < len(argv):
        if argv[i] == "--ordering" and i + 1 < len(argv):
            joined.append(f"--ordering={argv[i + 1]}")
            i += 2
        else:
            joined.append(argv[i])
            i += 1
    return joined


def main(argv=None):
    args = build_parser().parse_args(join_ordering(sys.argv[1:] if argv is None else argv))
    if not os.environ.get("HTTPTV_API_TOKEN", "").strip():
        print("Error: HTTPTV_API_TOKEN is not set. Get a token with POST /api/auth/token/ "
              "(see README), put it in .env, and run with: uv run --env-file .env python scripts/httptv_client.py",
              file=sys.stderr)
        return 1
    try:
        return args.handler(args)
    except ClientError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # show names like "Shōgun" on any console
        except AttributeError:
            pass
    sys.exit(main())
