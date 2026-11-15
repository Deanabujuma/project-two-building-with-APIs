from rest_framework import serializers

from ..models import CollectionEntry, Show
from ..validation import validate_tracking


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
    """One entry in the user's collection.

    Writable: status, current_season, current_episode, rating, notes. Range and cross-field
    rules are not declared here; `validate` runs the shared rules from shows.validation,
    the same function the web form uses, so both give the same answers and messages.
    """

    show = ShowSerializer(read_only=True)
    tvmaze_id = serializers.IntegerField(write_only=True, required=False, min_value=1,
                                         help_text="Create only: the TVmaze ID of the show to add.")
    # Declared without min/max so the shared rules produce the messages.
    current_season = serializers.IntegerField(allow_null=True, required=False, error_messages={
        "invalid": "Season must be a whole number of 1 or more."})
    current_episode = serializers.IntegerField(allow_null=True, required=False, error_messages={
        "invalid": "Episode must be a whole number of 1 or more."})
    rating = serializers.IntegerField(allow_null=True, required=False, error_messages={
        "invalid": "Rating must be a whole number from 1 to 5, or blank."})
    notes = serializers.CharField(allow_blank=True, required=False, trim_whitespace=False)

    class Meta:
        model = CollectionEntry
        fields = ["id", "show", "tvmaze_id", "status", "current_season", "current_episode", "rating", "notes",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "show", "created_at", "updated_at"]

    def validate(self, attrs):
        if self.instance is not None and "tvmaze_id" in attrs:
            raise serializers.ValidationError({"tvmaze_id": "An entry's show can't be changed. "
                                               "Delete the entry and add the other show instead."})
        if self.instance is None:
            return attrs  # create: only tvmaze_id is used (see CollectionEntryViewSet.create)

        # Check the values the entry WILL have after this update, so a PATCH that sends
        # only `current_season` is checked against the episode already saved.
        merged = {field: attrs.get(field, getattr(self.instance, field))
                  for field in ("status", "current_season", "current_episode", "rating", "notes")}
        errors = validate_tracking(**merged)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class CreateEntrySerializer(serializers.Serializer):
    """POST /api/collection/ body: just the TVmaze ID."""

    tvmaze_id = serializers.IntegerField(min_value=1)
