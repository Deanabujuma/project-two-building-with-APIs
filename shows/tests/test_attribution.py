"""AC50: every page credits TVmaze and CC BY-SA 4.0; show pages link to the show on TVmaze."""

import pytest

from shows.models import CollectionEntry, Show
from shows.tests.conftest import FAILURES, FakeResponse

TVMAZE_LINK = 'href="https://www.tvmaze.com"'
LICENSE_LINK = 'href="https://creativecommons.org/licenses/by-sa/4.0/"'


def assert_attributed(response, status=200):
    assert response.status_code == status
    html = response.content.decode()
    footer = html[html.index("<footer"):]
    assert TVMAZE_LINK in footer and LICENSE_LINK in footer


@pytest.mark.parametrize("url", ["/", "/accounts/login/", "/accounts/signup/", "/no-such-page/"])
def test_public_pages(client, db, url):
    assert_attributed(client.get(url), 404 if url == "/no-such-page/" else 200)


@pytest.fixture
def entry(user):
    show = Show.objects.create(tvmaze_id=44933, name="Severance", tvmaze_url="https://www.tvmaze.com/shows/44933/severance")
    return CollectionEntry.objects.create(user=user, show=show)


@pytest.mark.parametrize("url", ["/", "/discover/", "/collection/", "/shows/44933/?tab=tracking",
                                 "/shows/44933/?tab=suggested", "DELETE"])
def test_logged_in_pages(logged_in, entry, url):
    if url == "DELETE":
        url = f"/collection/{entry.pk}/delete/"
    assert_attributed(logged_in.get(url))


def test_discover_results(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(200, []))
    assert_attributed(logged_in.get("/discover/?q=zzqxjvk"))


def test_unknown_show_404_and_outage_503(logged_in, tvmaze_stub):
    tvmaze_stub.queue(FakeResponse(404, {}))
    assert_attributed(logged_in.get("/shows/999999999/"), 404)
    tvmaze_stub.queue(FAILURES[0][0])
    assert_attributed(logged_in.get("/shows/5/"), 503)


def test_show_page_links_to_the_show_on_tvmaze(logged_in, entry):
    html = logged_in.get("/shows/44933/").content.decode()
    assert 'href="https://www.tvmaze.com/shows/44933/severance"' in html
