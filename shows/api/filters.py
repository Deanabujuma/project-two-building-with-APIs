"""Search, filtering and ordering for GET /api/collection/."""

import django_filters
from django import forms
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter

from .. import queries
from ..models import CollectionEntry


class IntegerFilter(django_filters.NumberFilter):
    """Like NumberFilter, but only whole numbers are valid ("2.5" -> 400)."""

    field_class = forms.IntegerField


class CollectionEntryFilter(django_filters.FilterSet):
    """Strict filters: an invalid value (e.g. status=banana, min_rating=9) returns 400."""

    status = django_filters.ChoiceFilter(choices=CollectionEntry.Status.choices)
    min_rating = IntegerFilter(field_name="rating", lookup_expr="gte", min_value=1, max_value=5,
                               label="Minimum rating (1–5)")
    genre = django_filters.CharFilter(field_name="show__genres", lookup_expr="icontains", label="Genre contains")
    show_status = django_filters.CharFilter(field_name="show__show_status", lookup_expr="iexact",
                                            label="Show status (e.g. Running, Ended)")
    network = django_filters.CharFilter(field_name="show__network", lookup_expr="icontains",
                                        label="Network or web channel contains")

    class Meta:
        model = CollectionEntry
        fields = ["status", "min_rating", "genre", "show_status", "network"]


class SharedOrderingFilter(OrderingFilter):
    """?ordering= using shows.queries.order_entries, the same ordering as the web page.

    Unrated entries (and missing TVmaze ratings / premiere dates) sort last in both
    directions. An unknown field returns 400 instead of being silently ignored.
    """

    ordering_fields = sorted(queries.ORDERING_FIELDS)

    def filter_queryset(self, request, queryset, view):
        ordering = request.query_params.get(self.ordering_param)
        try:
            return queries.order_entries(queryset, ordering or None)
        except queries.InvalidOrdering as error:
            raise ValidationError({"ordering": [str(error)]})

    def get_valid_fields(self, queryset, view, context=None):
        # Used by the browsable API's ordering menu.
        return [(field, field) for field in self.ordering_fields]
