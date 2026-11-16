from django.urls import path

from . import views

app_name = "shows"

urlpatterns = [
    path("discover/", views.discover, name="discover"),
    path("discover/browse/", views.discover_browse, name="discover_browse"),
    path("discover/genre/<str:genre>/", views.discover_genre, name="discover_genre"),
    path("shows/<int:tvmaze_id>/", views.show_detail, name="detail"),
    path("collection/", views.collection, name="collection"),
    path("collection/add/", views.add_to_collection, name="add"),
    path("collection/<int:entry_id>/", views.update_entry, name="update"),
    path("collection/<int:entry_id>/delete/", views.delete_entry, name="delete"),
]
