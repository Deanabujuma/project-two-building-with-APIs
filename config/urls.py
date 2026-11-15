"""HTTP.tv URL configuration."""

from django.contrib import admin
from django.urls import include, path

from shows import views as show_views

urlpatterns = [
    path("", show_views.home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("", include("shows.urls")),
    path("api/", include("shows.api.urls")),
    path("admin/", admin.site.urls),
]
