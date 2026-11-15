"""Phase 4a: Show and CollectionEntry models."""

import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from shows.models import CollectionEntry, Show


def make_show(tvmaze_id=1, name="Sample Show", **fields):
    return Show.objects.create(tvmaze_id=tvmaze_id, name=name, tvmaze_url=f"https://www.tvmaze.com/shows/{tvmaze_id}", **fields)


@pytest.mark.django_db
def test_new_entry_defaults(user):
    entry = CollectionEntry.objects.create(user=user, show=make_show())
    assert entry.status == CollectionEntry.Status.PLAN_TO_WATCH
    assert entry.current_season is None and entry.current_episode is None
    assert entry.rating is None and entry.notes == ""
    assert entry.created_at and entry.updated_at
    assert entry.progress_text == "Not started"


@pytest.mark.django_db
def test_progress_text(user):
    entry = CollectionEntry(user=user, show=make_show(), current_season=2, current_episode=9)
    assert entry.progress_text == "Season 2, Episode 9"


@pytest.mark.django_db
def test_same_show_cannot_be_saved_twice_by_one_user(user):
    show = make_show()
    CollectionEntry.objects.create(user=user, show=show)
    with pytest.raises(IntegrityError):
        CollectionEntry.objects.create(user=user, show=show)


@pytest.mark.django_db
def test_two_users_can_save_the_same_show(user, other_user):
    show = make_show()
    CollectionEntry.objects.create(user=user, show=show)
    CollectionEntry.objects.create(user=other_user, show=show)
    assert show.collection_entries.count() == 2


@pytest.mark.django_db
def test_tvmaze_id_is_unique():
    make_show(5)
    with pytest.raises(IntegrityError):
        make_show(5, "Duplicate")


@pytest.mark.django_db
def test_deleting_a_user_deletes_their_entries_but_not_shows(user):
    show = make_show()
    CollectionEntry.objects.create(user=user, show=show)
    user.delete()
    assert CollectionEntry.objects.count() == 0
    assert Show.objects.filter(pk=show.pk).exists()


@pytest.mark.django_db
def test_show_with_entries_cannot_be_deleted(user):
    show = make_show()
    CollectionEntry.objects.create(user=user, show=show)
    with pytest.raises(ProtectedError):
        show.delete()


@pytest.mark.django_db
def test_genre_list_splits_the_text_field():
    assert make_show(genres="Comedy, Drama ,Family").genre_list == ["Comedy", "Drama", "Family"]
    assert make_show(2, genres="").genre_list == []


@pytest.mark.django_db
@pytest.mark.parametrize("url", ["/admin/shows/show/", "/admin/shows/collectionentry/",
                                 "/admin/shows/show/add/", "/admin/shows/collectionentry/add/"])
def test_admin_pages_load_for_superuser(client, django_user_model, url):
    admin_user = django_user_model.objects.create_superuser("admin_test", password="a-strong-pass-789")
    client.force_login(admin_user)
    show = make_show()
    CollectionEntry.objects.create(user=admin_user, show=show)
    assert client.get(url).status_code == 200
    assert client.get(url, {"q": "Sample"}).status_code == 200
