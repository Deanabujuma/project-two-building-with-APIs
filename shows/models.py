from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual

from .validation import NOTES_MAX_LENGTH, RATING_MAX, RATING_MIN, STATUS_VALUES, validate_tracking


class Show(models.Model):
    """A TV show copied from TVmaze. Shared by all users: one row per TVmaze show."""

    class ChannelType(models.TextChoices):
        NETWORK = "network", "Network"
        WEB_CHANNEL = "web channel", "Web channel"

    tvmaze_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=255)
    tvmaze_url = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500, blank=True)
    background_url = models.URLField(max_length=500, blank=True)
    premiered = models.DateField(null=True, blank=True)
    ended = models.DateField(null=True, blank=True)
    show_status = models.CharField(max_length=50, blank=True)
    genres = models.CharField(max_length=255, blank=True, help_text="Comma-separated, e.g. 'Comedy, Drama'.")
    summary = models.TextField(blank=True, help_text="Plain text; TVmaze's HTML is stripped.")
    network = models.CharField(max_length=100, blank=True, help_text="Original TV network or web channel name.")
    channel_type = models.CharField(max_length=20, choices=ChannelType.choices, blank=True)
    channel_country = models.CharField(max_length=100, blank=True)
    runtime = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes.")
    tvmaze_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    language = models.CharField(max_length=50, blank=True)
    show_type = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def genre_list(self):
        return [genre.strip() for genre in self.genres.split(",") if genre.strip()]


class CollectionEntry(models.Model):
    """One user's tracking of one show."""

    class Status(models.TextChoices):
        PLAN_TO_WATCH = "plan_to_watch", "Plan to Watch"
        WATCHING = "watching", "Watching"
        ON_HOLD = "on_hold", "On Hold"
        COMPLETED = "completed", "Completed"
        DROPPED = "dropped", "Dropped"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collection_entries")
    show = models.ForeignKey(Show, on_delete=models.PROTECT, related_name="collection_entries")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLAN_TO_WATCH)
    # Range rules (season/episode >= 1, rating 1-5) live in shows.validation and the check
    # constraints below, so they are defined once instead of also as field validators.
    current_season = models.PositiveIntegerField(null=True, blank=True)
    current_episode = models.PositiveIntegerField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(max_length=NOTES_MAX_LENGTH, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "collection entries"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "show"], name="unique_show_per_user"),
            # The same rules as shows.validation.validate_tracking, enforced by the database.
            # The explicit isnull=False matters: SQL treats "NULL >= 1" as unknown, and a CHECK
            # whose result is unknown passes, which would let "season only" rows in.
            models.CheckConstraint(
                condition=Q(current_season__isnull=True, current_episode__isnull=True)
                | Q(current_season__isnull=False, current_episode__isnull=False,
                    current_season__gte=1, current_episode__gte=1),
                name="progress_both_or_neither",
            ),
            models.CheckConstraint(
                condition=Q(rating__isnull=True) | Q(rating__gte=RATING_MIN, rating__lte=RATING_MAX),
                name="rating_1_to_5",
            ),
            models.CheckConstraint(condition=Q(status__in=STATUS_VALUES), name="status_valid"),
            models.CheckConstraint(condition=LessThanOrEqual(Length("notes"), NOTES_MAX_LENGTH), name="notes_max_2000"),
        ]

    def __str__(self):
        return f"{self.user} · {self.show}"

    def clean(self):
        """Apply the shared tracking rules (used by the web form and the admin)."""
        errors = validate_tracking(self.status, self.current_season, self.current_episode, self.rating, self.notes)
        if errors:
            raise ValidationError(errors)

    @property
    def has_progress(self):
        return self.current_season is not None and self.current_episode is not None

    @property
    def progress_text(self):
        """"Season 2, Episode 9", or "Not started"."""
        if self.has_progress:
            return f"Season {self.current_season}, Episode {self.current_episode}"
        return "Not started"
