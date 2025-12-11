from rest_framework.pagination import PageNumberPagination


class PostPagination(PageNumberPagination):
    page_size = 10


class PostPagination50(PageNumberPagination):
    page_size = 50


class Pagination25(PageNumberPagination):
    page_size = 20


class PostPagination100(PageNumberPagination):
    page_size = 100


class PostPagination200(PageNumberPagination):
    page_size = 200


class PostPagination300(PageNumberPagination):
    page_size = 300


class PostPagination6(PageNumberPagination):
    page_size = 6


class AllDataPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = None
