"""Project-wide test setup."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def empty_cache():
    """Start every test with an empty cache, so cached TVmaze data never leaks between tests."""
    cache.clear()
    yield
    cache.clear()
