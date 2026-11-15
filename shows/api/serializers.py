from rest_framework import serializers

from ..models import CollectionEntry, Show


class ShowSerializer(serializers.ModelSerializer):
    """TVmaze-derived show data (CC BY-SA 4.0), always read-only through the API."""

    class Meta:
        model = Show
        fields = [
            "tvmaze_id", "name", "tvmaze_url", "image_url", "background_url", "premiered", "ended",
            "show_status", "genres", "network", "channel_type", "channel_country", "runtime",
            "tvmaze_rating", "language", "show_type", "summary",
        ]
        read_only_fields = fields


class CollectionEntrySerializer(serializers.ModelSerializer):
    show = ShowSerializer(read_only=True)

    class Meta:
        model = CollectionEntry
        fields = ["id", "show", "status", "current_season", "current_episode", "rating", "notes",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "show", "created_at", "updated_at"]
