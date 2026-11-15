"""The tracking rules, written once and used everywhere.

`validate_tracking` is called by `CollectionEntry.clean()` (so the Django admin and the web
form use it) and by the API serializer. The database check constraints on
`CollectionEntry` enforce the same rules as a last line of defence.
"""

NOTES_MAX_LENGTH = 2000
RATING_MIN, RATING_MAX = 1, 5
STATUS_VALUES = ("plan_to_watch", "watching", "on_hold", "completed", "dropped")

BOTH_OR_NEITHER = "Enter both a season and an episode, or leave both blank."


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_tracking(status, current_season, current_episode, rating, notes):
    """Return {field_name: message} for every broken rule (empty dict when all valid)."""
    errors = {}

    if status not in STATUS_VALUES:
        errors["status"] = "Choose a valid status."

    for field, value, label in (("current_season", current_season, "Season"),
                                ("current_episode", current_episode, "Episode")):
        if value is not None and (not _is_int(value) or value < 1):
            errors[field] = f"{label} must be a whole number of 1 or more."

    if "current_season" not in errors and "current_episode" not in errors:
        if current_season is not None and current_episode is None:
            errors["current_episode"] = BOTH_OR_NEITHER
        elif current_episode is not None and current_season is None:
            errors["current_season"] = BOTH_OR_NEITHER

    if rating is not None and (not _is_int(rating) or not RATING_MIN <= rating <= RATING_MAX):
        errors["rating"] = f"Rating must be a whole number from {RATING_MIN} to {RATING_MAX}, or blank."

    if notes is not None and len(notes) > NOTES_MAX_LENGTH:
        errors["notes"] = f"Notes can be at most {NOTES_MAX_LENGTH:,} characters (you entered {len(notes):,})."

    return errors
