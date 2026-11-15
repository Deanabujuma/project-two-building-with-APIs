from django.contrib import admin

from .models import CollectionEntry, Show


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("name", "tvmaze_id", "network", "channel_type", "show_status", "premiered")
    list_filter = ("show_status", "channel_type")
    search_fields = ("name", "network", "genres")


@admin.register(CollectionEntry)
class CollectionEntryAdmin(admin.ModelAdmin):
    list_display = ("show", "user", "status", "current_season", "current_episode", "rating", "updated_at")
    list_filter = ("status",)
    search_fields = ("show__name", "user__username", "notes")
    list_select_related = ("show", "user")
    readonly_fields = ("created_at", "updated_at")
