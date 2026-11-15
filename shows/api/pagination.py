from rest_framework.pagination import PageNumberPagination


class CollectionPagination(PageNumberPagination):
    """12 entries per page by default; clients may ask for up to 50 with ?page_size=."""

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50
