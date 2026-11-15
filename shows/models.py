from django.conf import settings
from django.db import models

NOTES_MAX_LENGTH = 2000


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
        ]

    def __str__(self):
        return f"{self.user} · {self.show}"

    @property
    def has_progress(self):
        return self.current_season is not None and self.current_episode is not None

    @property
    def progress_text(self):
        """"Season 2, Episode 9", or "Not started"."""
        if self.has_progress:
            return f"Season {self.current_season}, Episode {self.current_episode}"
        return "Not started"
