"""Phase 8: personalized home page (AC26 logged-in parts, AC27)."""

import re

import pytest

from shows.models import CollectionEntry, Show
from shows.views import home_context


def add(user, tvmaze_id, name, status="plan_to_watch", **fields):
    show = Show.objects.create(tvmaze_id=tvmaze_id, name=name, tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}",
                               background_url=fields.pop("background_url", ""))
    return CollectionEntry.objects.create(user=user, show=show, status=status, **fields)


def touch(entry):
    entry.notes += "."
    entry.save()


def row_names(context, key):
    row = next((r for r in context["rows"] if r["key"] == key), None)
    return None if row is None else [e.show.name for e in row["entries"]]


# --- AC26: hero selection ---------------------------------------------------------------------------------

@pytest.mark.django_db
def test_hero_features_most_recently_updated_watching_entry(user):
    a = add(user, 1, "Watching Old", "watching")
    add(user, 2, "Watching New", "watching")
    add(user, 3, "Completed Newest", "completed")
    touch(a)
    touch(CollectionEntry.objects.get(show__tvmaze_id=3))
    assert home_context(user)["featured"].show.name == "Watching Old"


@pytest.mark.django_db
def test_hero_falls_back_to_latest_entry_when_nothing_is_watching(user):
    add(user, 1, "Plan", "plan_to_watch")
    add(user, 2, "Done", "completed")
    assert home_context(user)["featured"].show.name == "Done"


@pytest.mark.django_db
def test_no_entries_means_no_featured_show(user):
    assert home_context(user) == {"featured": None, "rows": []}


def test_home_renders_featured_hero_with_buttons(logged_in, user):
    add(user, 44933, "Severance", "watching", current_season=2, current_episode=3, background_url="https://img/bg.jpg")
    html = logged_in.get("/").content.decode()
    assert 'data-hero="featured"' in html and 'data-featured="44933"' in html
    assert "Continue tracking · Season 2, Episode 3" in html
    assert "More info" in html and "In your collection" in html
    assert "background-image:url('https://img/bg.jpg')" in html


def test_home_with_empty_collection_shows_discover_welcome(logged_in):
    html = logged_in.get("/").content.decode()
    assert 'data-hero="welcome-empty"' in html and 'href="/discover/"' in html


# --- AC27: rows --------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_rows_contain_the_right_entries(user):
    w1 = add(user, 1, "W1", "watching")
    add(user, 2, "W2", "watching")
    add(user, 3, "P1", "plan_to_watch")
    add(user, 4, "C1", "completed")
    add(user, 5, "H1", "on_hold")
    touch(w1)
    context = home_context(user)
    assert context["featured"].show.name == "W1"
    assert row_names(context, "continue") == ["W2"]            # the featured show isn't repeated
    assert row_names(context, "watchlist") == ["P1"]
    assert row_names(context, "completed") == ["C1"]
    assert row_names(context, "recent") == ["H1", "C1", "P1", "W2", "W1"]   # any status, newest save first


@pytest.mark.django_db
def test_recently_added_is_limited_to_ten(user):
    for i in range(1, 13):
        add(user, i, f"Show {i:02d}")
    recent = row_names(home_context(user), "recent")
    assert len(recent) == 10 and recent[0] == "Show 12"


@pytest.mark.django_db
def test_empty_rows_are_hidden(user):
    add(user, 1, "Only Plan", "plan_to_watch")
    keys = [row["key"] for row in home_context(user)["rows"]]
    assert keys == ["watchlist", "recent"]


@pytest.mark.django_db
def test_rows_only_include_my_entries(user, other_user):
    add(user, 1, "Mine", "watching")
    show = Show.objects.create(tvmaze_id=2, name="Theirs", tvmaze_url="https://www.tvmaze.com/shows/2")
    CollectionEntry.objects.create(user=other_user, show=show, status="watching")
    context = home_context(user)
    all_names = {e.show.name for row in context["rows"] for e in row["entries"]}
    assert all_names == {"Mine"} and context["featured"].show.name == "Mine"


def test_rows_render_with_shared_cards_and_tracking_links(logged_in, user):
    feature = add(user, 1, "Feature", "watching")
    add(user, 2, "Second Watch", "watching", current_season=1, current_episode=2)
    add(user, 3, "Plan Show", "plan_to_watch")
    touch(feature)  # most recently updated Watching entry -> hero; Second Watch goes in the row
    html = logged_in.get("/").content.decode()
    for key in ["continue", "watchlist", "recent"]:
        assert f'data-row="{key}"' in html
    assert 'data-row="completed"' not in html
    continue_row = html[html.index('data-row="continue"'):html.index('data-row="watchlist"')]
    assert "tile-wide" in continue_row and 'href="/shows/2/?tab=tracking"' in continue_row
    assert "Season 1, Episode 2" in continue_row
    assert "tile-flag" not in html   # rows contain only my shows, so no check marks
