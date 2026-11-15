"""Phase 7: My Collection page (AC28, AC29, AC30 web, AC31, AC52 web half)."""

import re

import pytest

from shows.models import CollectionEntry, Show


def add(user, tvmaze_id, name, **fields):
    show = Show.objects.create(tvmaze_id=tvmaze_id, name=name, tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}")
    return CollectionEntry.objects.create(user=user, show=show, **fields)


def card_names(html):
    return re.findall(r'<div class="cap-t clamp-1">([^<]+)</div>', html)


@pytest.fixture
def fourteen(user):
    return [add(user, i, f"Show {i:02d}") for i in range(1, 15)]


# --- AC28: pagination ------------------------------------------------------------------------------------

def test_twelve_per_page_and_two_on_page_two(logged_in, fourteen):
    assert len(card_names(logged_in.get("/collection/").content.decode())) == 12
    html = logged_in.get("/collection/?page=2").content.decode()
    assert len(card_names(html)) == 2
    assert 'aria-current="page">2</span>' in html


@pytest.mark.parametrize("page", ["99", "0", "-1", "abc", ""])
def test_out_of_range_or_invalid_page_is_handled(logged_in, fourteen, page):
    response = logged_in.get(f"/collection/?page={page}")
    assert response.status_code == 200
    assert card_names(response.content.decode())


def test_pager_links_keep_the_other_filters(logged_in, user):
    for i in range(1, 15):
        add(user, i, f"Watch {i:02d}", status="watching")
    html = logged_in.get("/collection/?status=watching&sort=title").content.decode()
    assert 'href="/collection/?status=watching&amp;sort=title&amp;page=2"' in html


# --- AC29: chips, combinations and nav links ---------------------------------------------------------------

def test_status_chips_show_counts(logged_in, user):
    add(user, 1, "A", status="watching")
    add(user, 2, "B", status="watching")
    add(user, 3, "C", status="completed")
    add(user, 4, "D")
    html = logged_in.get("/collection/").content.decode()
    for chip, count in [("all", 4), ("watching", 2), ("completed", 1), ("plan_to_watch", 1), ("on_hold", 0), ("dropped", 0)]:
        chip_html = html[html.index(f'data-chip="{chip}"'):]
        assert f'<span class="n">{count}</span>' in chip_html[:400], chip


def test_status_q_and_sort_combine(logged_in, user):
    add(user, 1, "Office Space", status="watching", rating=2)
    add(user, 2, "The Office", status="watching", rating=5)
    add(user, 3, "Office Hours", status="completed", rating=4)
    add(user, 4, "Severance", status="watching", rating=5)
    html = logged_in.get("/collection/?status=watching&q=office&sort=-rating").content.decode()
    assert card_names(html) == ["The Office", "Office Space"]


def test_title_sort_and_default_recently_updated(logged_in, user):
    first = add(user, 1, "Zulu")
    add(user, 2, "alpha")
    first.notes = "touched"
    first.save()
    assert card_names(logged_in.get("/collection/").content.decode()) == ["Zulu", "alpha"]
    assert card_names(logged_in.get("/collection/?sort=title").content.decode()) == ["alpha", "Zulu"]


def test_rating_sort_puts_unrated_last_on_the_page(logged_in, user):
    add(user, 1, "Unrated A")
    add(user, 2, "Three", rating=3)
    add(user, 3, "Unrated B")
    add(user, 4, "Five", rating=5)
    assert card_names(logged_in.get("/collection/?sort=-rating").content.decode()) == ["Five", "Three", "Unrated A", "Unrated B"]


@pytest.mark.parametrize("url, title", [("/collection/?status=watching", "Watching"),
                                        ("/collection/?status=completed", "Completed"),
                                        ("/collection/", "My Collection")])
def test_watching_and_completed_nav_links_filter_the_page(logged_in, user, url, title):
    add(user, 1, "W", status="watching")
    add(user, 2, "C", status="completed")
    html = logged_in.get(url).content.decode()
    assert f'<h1 class="page-title mb-1">{title}</h1>' in html


def test_invalid_status_and_sort_fall_back_safely(logged_in, user):
    add(user, 1, "Only Show")
    response = logged_in.get("/collection/?status=nonsense&sort=notes")
    assert response.status_code == 200 and card_names(response.content.decode()) == ["Only Show"]


def test_only_my_entries_are_listed(logged_in, other_user, user):
    add(user, 1, "Mine")
    show = Show.objects.create(tvmaze_id=2, name="Theirs", tvmaze_url="https://www.tvmaze.com/shows/2")
    CollectionEntry.objects.create(user=other_user, show=show)
    assert card_names(logged_in.get("/collection/").content.decode()) == ["Mine"]


def test_cards_link_to_tracking_and_show_stars(logged_in, user):
    entry = add(user, 44933, "Severance", status="watching", current_season=2, current_episode=3, rating=4)
    html = logged_in.get("/collection/").content.decode()
    assert 'href="/shows/44933/?tab=tracking"' in html
    assert "Season 2, Episode 3" in html and 'aria-label="4 of 5 stars"' in html


# --- AC31: empty states ---------------------------------------------------------------------------------------

def test_empty_collection_state(logged_in):
    html = logged_in.get("/collection/").content.decode()
    assert 'data-state="empty"' in html and 'href="/discover/"' in html


def test_no_match_state_with_clear_link(logged_in, user):
    add(user, 1, "Severance")
    html = logged_in.get("/collection/?q=zzz").content.decode()
    assert 'data-state="no-match"' in html and "Nothing titled “zzz”" in html
    assert 'href="/collection/">Clear filters' in html


# --- AC52 (web half): q searches titles only ------------------------------------------------------------------

def test_q_matches_titles_not_notes(logged_in, user):
    add(user, 1, "Severance", notes="The goats scene was wild.")
    assert 'data-state="no-match"' in logged_in.get("/collection/?q=goats").content.decode()
    assert card_names(logged_in.get("/collection/?q=sever").content.decode()) == ["Severance"]
