from rest_framework import viewsets

from .. import queries
from .serializers import CollectionEntrySerializer


class CollectionEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """The logged-in user's collection. Other users' entries don't exist here (404)."""

    serializer_class = CollectionEntrySerializer

    def get_queryset(self):
        return queries.order_entries(queries.collection_entries(self.request.user))
