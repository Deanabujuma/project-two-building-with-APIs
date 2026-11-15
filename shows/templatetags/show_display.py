"""Display helpers shared by every page that shows a TV show.

They accept either a `Show` model instance or the plain dict returned by the TVmaze
client, because both use the same field names.
"""

from django import template

register = template.Library()


def _field(show, name):
    if isinstance(show, dict):
        return show.get(name)
    return getattr(show, name, None)


def _year(value):
    if not value:
        return ""
    return str(value)[:4]


@register.filter
def years(show):
    """"2021–present", "2008–2013", "2024" (same start and end year), or "" if unknown."""
    start = _year(_field(show, "premiered"))
    end = _year(_field(show, "ended"))
    if not start:
        return ""
    if end:
        return start if end == start else f"{start}–{end}"
    if _field(show, "show_status") == "Running":
        return f"{start}–present"
    return start


@register.filter
def initial(value):
    """First character of a name, for image fallbacks."""
    return (value or "?")[:1].upper()


@register.filter
def identity_line(show):
    """Years and channel, e.g. "2005–2013 · NBC", so same-named shows can be told apart.

    Falls back to genres when TVmaze gives neither a premiere date nor a channel.
    """
    parts = [part for part in (years(show), _field(show, "network")) if part]
    return " · ".join(parts) or (_field(show, "genres") or "")
