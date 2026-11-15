from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from .. import queries, services, tvmaze
from .filters import CollectionEntryFilter, SharedOrderingFilter
from .serializers import CollectionEntrySerializer, CreateEntrySerializer


class CollectionEntryViewSet(viewsets.ModelViewSet):
    """The logged-in user's collection. Other users' entries don't exist here (404).

    POST takes only {"tvmaze_id": N}. The show's details are fetched from TVmaze by the
    same save logic as the web app's Save button.
    """

    serializer_class = CollectionEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, SharedOrderingFilter]
    filterset_class = CollectionEntryFilter
    search_fields = ["show__name", "notes"]  # broader than the web page, which searches titles only

    def get_queryset(self):
        return queries.collection_entries(self.request.user)  # ordered by SharedOrderingFilter

    def create(self, request, *args, **kwargs):
        body = CreateEntrySerializer(data=request.data)
        body.is_valid(raise_exception=True)
        tvmaze_id = body.validated_data["tvmaze_id"]
        try:
            entry = services.save_show_to_collection(request.user, tvmaze_id)
        except services.AlreadySaved as already:
            return Response({"tvmaze_id": [str(already)]}, status=status.HTTP_400_BAD_REQUEST)
        except tvmaze.ShowNotFound as missing:
            return Response({"tvmaze_id": [str(missing)]}, status=status.HTTP_400_BAD_REQUEST)
        except tvmaze.TVmazeError as error:
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        data = self.get_serializer(entry).data
        location = request.build_absolute_uri(f"{entry.pk}/")
        return Response(data, status=status.HTTP_201_CREATED, headers={"Location": location})
