import math
from typing import List, Tuple

from fastapi import Request

from database import Base


class DefaultPaginationClass:
    def __init__(self, request: Request, page_number_param: str = 'page', page_size_param: str = 'page_size_param'):
        self.request = request
        self.page_number_param = page_number_param
        self.page_size_param = page_size_param

    def paginate(self, queryset: List[Base]) -> dict:
        query_params = self.request.query_params
        page_size: int = int(query_params.get('page_size', 20))
        current_page: int = int(query_params.get('page', 1))
        queryset_offset = page_size * (current_page - 1)
        queryset_limit = page_size * current_page
        total_db_objects_count = len(queryset)
        total_pages = math.ceil(total_db_objects_count / page_size)
        queryset = queryset[queryset_offset:queryset_limit]
        previous_page, next_page = self.get_previous_and_next_pages(
            current_page, queryset_limit, total_db_objects_count
        )
        return {
            'data': queryset,
            'count': total_db_objects_count,
            'total_pages': total_pages,
            'current_page': current_page,
            'page_size': page_size,
            'next': next_page,
            'previous': previous_page,
        }

    def get_previous_and_next_pages(
            self,
            current_page: int,
            queryset_limit: int,
            total_db_objects_count: int
    ) -> Tuple[str, str]:
        url = self.request.url
        url_query_params: str = url.query
        url_contains_page_param = url_query_params and 'page=' in url_query_params
        url = str(url)
        page_number_param = self.page_number_param
        previous_page = None if current_page == 1 else url.replace(
            f'{page_number_param}={current_page}', f'{page_number_param}={current_page - 1}'
        ) if url_contains_page_param else f'{url}&{page_number_param}={current_page - 1}' if url_query_params else (
            f'{url}?{page_number_param}={current_page - 1}'
        )
        next_page = None if queryset_limit >= total_db_objects_count else url.replace(
            f'{page_number_param}={current_page}', f'{page_number_param}={current_page + 1}'
        ) if url_contains_page_param else f'{url}&{page_number_param}={current_page + 1}' if url_query_params else (
            f'{url}?{page_number_param}={current_page + 1}'
        )
        return previous_page, next_page