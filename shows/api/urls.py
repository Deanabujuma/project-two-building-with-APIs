from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import CollectionEntryViewSet

router = DefaultRouter()
router.register("collection", CollectionEntryViewSet, basename="collection")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api-token"),
    path("", include(router.urls)),
]
