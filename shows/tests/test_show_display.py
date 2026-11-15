"""Display filters shared by every show card (years, identity line)."""

import pytest

from shows.templatetags.show_display import identity_line, initial, years


@pytest.mark.parametrize("show, expected", [
    ({"premiered": "2005-03-24", "ended": "2013-05-16", "show_status": "Ended"}, "2005–2013"),
    ({"premiered": "2021-12-07", "ended": None, "show_status": "Running"}, "2021–present"),
    ({"premiered": "2024-01-01", "ended": "2024-06-01", "show_status": "Ended"}, "2024"),
    ({"premiered": "2019-01-01", "ended": None, "show_status": "To Be Determined"}, "2019"),
    ({"premiered": None, "ended": None, "show_status": "In Development"}, ""),
])
def test_years(show, expected):
    assert years(show) == expected


def test_identity_line_tells_same_named_shows_apart():
    us = {"name": "The Office", "premiered": "2005-03-24", "ended": "2013-05-16", "show_status": "Ended", "network": "NBC", "genres": "Comedy"}
    uk = {"name": "The Office", "premiered": "2001-07-09", "ended": "2003-12-27", "show_status": "Ended", "network": "BBC Two", "genres": "Comedy"}
    assert identity_line(us) == "2005–2013 · NBC"
    assert identity_line(uk) == "2001–2003 · BBC Two"


def test_identity_line_falls_back_to_genres():
    assert identity_line({"premiered": None, "network": "", "genres": "Drama"}) == "Drama"


def test_initial():
    assert initial("severance") == "S" and initial("") == "?"
