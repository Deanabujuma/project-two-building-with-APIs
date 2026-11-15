from django.urls import path

from . import views

app_name = "shows"

urlpatterns = [
    path("discover/", views.discover, name="discover"),
    path("shows/<int:tvmaze_id>/", views.show_detail, name="detail"),
    path("collection/", views.collection, name="collection"),
    path("collection/add/", views.add_to_collection, name="add"),
]
