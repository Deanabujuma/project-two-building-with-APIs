from django.urls import path

from . import views

app_name = "shows"

urlpatterns = [
    path("discover/", views.discover, name="discover"),
    path("collection/", views.collection, name="collection"),
]
