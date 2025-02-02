from django.http import HttpRequest
from django.db.models.query import QuerySet
from rest_framework.views import APIView
from rest_framework.serializers import Serializer
from morest.utils import PaginationSerializer
from morest.api import Response
from morest.core import get_queryset


class ListFilterView(APIView):
    queryset: QuerySet
    serializer: Serializer
    filter_serializer: Serializer

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return get_queryset(self.queryset)
    
    def get_filter_serializer(self, request: HttpRequest) -> Serializer:
        return self.filter_serializer
    
    def get_filters(self, request: HttpRequest, filters: dict):
        if issubclass(self.get_filter_serializer(request), PaginationSerializer):
            filters.pop("page", None)
            filters.pop("limit", None)
        return filters
    
    def filter_queryset(self, request: HttpRequest, qs: QuerySet, filters: dict) -> QuerySet:
        return qs.filter(**filters).all()
    
    def get_serializer(self, request: HttpRequest) -> Serializer:
        return self.serializer
    
    def paginate(self, request: HttpRequest, filter_serializer: PaginationSerializer, qs: QuerySet):
        serializer = self.get_serializer(request)
        return filter_serializer.paginate(qs=qs, serializer=serializer)
    
    def serialize(self, request: HttpRequest, qs: QuerySet):
        serializer = self.get_serializer(request)
        return [serializer().to_representation(x) for x in qs]
    
    def get_response_data(self, request: HttpRequest, qs: QuerySet, data: dict):
        if isinstance(data, PaginationSerializer):
            return self.paginate(request=request, filter_serializer=data, qs=qs)
        else:
            return self.serialize(request=request, qs=qs)
        
    def get(self, request: HttpRequest):
        qs = self.get_queryset(request)
        filter_serializer = self.get_filter_serializer(request)
        data = filter_serializer(data=request.GET)
        if not data.is_valid():
            return Response.validation_error(data.errors)
        
        filters = self.get_filters(request, data.validated_data.copy())
        qs = self.filter_queryset(request, qs, filters)
        return Response(self.get_response_data(request, qs, data))