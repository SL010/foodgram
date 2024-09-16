from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Пагинатор."""

    page_size_query_param = 'limit'
    page_size = 6
