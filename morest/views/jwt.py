import json
from django.http import HttpRequest
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from morest.authentication import get_jwt_manager
from morest.serializers import RefreshTokenResponse, RefreshTokenRequest
from morest.api import Response
from morest.core import docs


class RefreshTokenView(APIView):
    permission_classes = (AllowAny,)
    
    def _get_jwt_manager(self, request: HttpRequest):
        return get_jwt_manager()
    
    @docs.schema(request_body=RefreshTokenRequest, response=RefreshTokenResponse)
    def post(self, request: HttpRequest):
        data = RefreshTokenRequest(data=json.loads(request.body or '{}'))
        if not data.is_valid():
            return Response.validation_error(data.errors)
        return Response(RefreshTokenResponse().to_representation(self._get_jwt_manager(request=request).refresh(**data.validated_data)))
