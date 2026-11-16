from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """HTTP.tv's user model: Django's standard user plus two display preferences."""

    class ScheduleCountry(models.TextChoices):
        """Countries for Discover's "Airing This Week" (TVmaze schedule country codes)."""

        US = "US", "United States"
        GB = "GB", "United Kingdom"
        CA = "CA", "Canada"
        AU = "AU", "Australia"
        IE = "IE", "Ireland"
        NZ = "NZ", "New Zealand"

    class CollectionSort(models.TextChoices):
        """My Collection's default order (the same three sorts the page offers)."""

        UPDATED = "-updated", "Recently updated"
        TITLE = "title", "Title (A–Z)"
        RATING = "-rating", "My rating (high–low)"

    schedule_country = models.CharField(
        "Schedule country", max_length=2, choices=ScheduleCountry.choices, default=ScheduleCountry.US,
        help_text="Whose TV schedule Discover's Airing This Week shows.")
    default_collection_sort = models.CharField(
        "Default collection order", max_length=10, choices=CollectionSort.choices, default=CollectionSort.UPDATED,
        help_text="How My Collection is ordered when you open it.")
