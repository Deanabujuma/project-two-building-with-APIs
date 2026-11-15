"""Shared test helpers for the shows app. No test ever reaches the real TVmaze API."""

import pytest
import requests
from django.contrib.auth import get_user_model


class FakeResponse:
    """Stands in for requests.Response."""

    def __init__(self, status_code=200, payload=None, invalid_json=False):
        self.status_code = status_code
        self._payload = payload
        self._invalid_json = invalid_json

    def json(self):
        if self._invalid_json:
            raise ValueError("not JSON")
        return self._payload


def raw_show(tvmaze_id=1, name="Sample Show", **overrides):
    """A TVmaze show object shaped like the real API's."""
    data = {
        "id": tvmaze_id,
        "url": f"https://www.tvmaze.com/shows/{tvmaze_id}/sample-show",
        "name": name,
        "type": "Scripted",
        "language": "English",
        "genres": ["Comedy", "Drama"],
        "status": "Running",
        "runtime": 30,
        "averageRuntime": 31,
        "premiered": "2021-12-07",
        "ended": None,
        "rating": {"average": 7.9},
        "network": {"id": 3, "name": "ABC", "country": {"name": "United States", "code": "US"}},
        "webChannel": None,
        "image": {"medium": f"https://static.tvmaze.com/medium/{tvmaze_id}.jpg",
                  "original": f"https://static.tvmaze.com/original/{tvmaze_id}.jpg"},
        "summary": "<p>A <b>sample</b> show &amp; its story.</p>",
    }
    data.update(overrides)
    return data


class TVmazeStub:
    """Records every TVmaze request and returns queued responses (or raises queued errors)."""

    def __init__(self):
        self.calls = []
        self.responses = []

    def queue(self, response):
        self.responses.append(response)
        return self

    def __call__(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        if not self.responses:
            raise AssertionError(f"Unexpected TVmaze call: {url} {params}")
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture
def tvmaze_stub(monkeypatch):
    stub = TVmazeStub()
    monkeypatch.setattr("shows.tvmaze.requests.get", stub)
    return stub


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="demo_user", password="a-strong-pass-123")


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user(username="other_user", password="a-strong-pass-456")


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


# Every way a TVmaze request can fail, with a phrase its user message must contain.
FAILURES = [
    (requests.Timeout(), "respond within 10 seconds"),
    (requests.ConnectionError(), "connect to TVmaze"),
    (FakeResponse(429), "too many requests"),
    (FakeResponse(503), "TVmaze is having problems (HTTP 503)"),
    (FakeResponse(400), "unexpected response (HTTP 400)"),
    (FakeResponse(200, invalid_json=True), "response HTTP.tv"),
    (FakeResponse(200, payload={"not": "a list"}), "response HTTP.tv"),
]
