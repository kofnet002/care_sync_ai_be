from rest_framework import pagination
from django.core.cache import cache
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    """Custom pagination."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 50


# POLL

class PollsPagination(CustomPagination):
    def get_paginated_response(self, data):
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages

        return Response(
            {
                'current_page': current_page,
                'total_pages': total_pages,
                'total_records': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'polls': data,
            }
        )