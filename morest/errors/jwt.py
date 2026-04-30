from .base import BaseError
from rest_framework import status


class AccessTokenIsInvalidError(BaseError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = 'Access token is invalid'
    status = 'access_token_is_invalid'


class RefreshTokenIsInvalidError(BaseError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = 'Refresh token is invalid'
    status = 'refresh_token_is_invalid'
