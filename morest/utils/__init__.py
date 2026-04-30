import secrets
from .paginator import PaginationSerializer
from .search import SearchSerializer
from .order import OrderSerializer


class PaginationSearchSerializer(PaginationSerializer, SearchSerializer):
    pass


def generate_api_token():
    return secrets.token_hex(20)