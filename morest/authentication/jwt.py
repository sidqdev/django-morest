from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from morest.core import JWTManager, JWTPair


def get_jwt_manager() -> JWTManager:
    access_token_secret = getattr(settings, "JWT_ACCESS_TOKEN_SECRET", None)
    refresh_token_secret = getattr(settings, "JWT_REFRESH_TOKEN_SECRET", None)
    if access_token_secret is None or refresh_token_secret is None:
        raise Exception("JWT_ACCESS_TOKEN_SECRET and JWT_REFRESH_TOKEN_SECRET are required to use JWT auth")
    
    return JWTManager(
        access_token_secret=access_token_secret,
        refresh_token_secret=refresh_token_secret,
        access_token_ttl=getattr(settings, "JWT_ACCESS_TOKEN_TTL", None),
        refresh_token_ttl=getattr(settings, "JWT_REFRESH_TOKEN_TTL", None),
    )


class JWTAuthentication(BaseAuthentication):
    """
    Simple jwt access/refresh token authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "JWT ".  For example:

        Authorization: JWT ...
    """

    keyword = 'JWT'
    primary_key_field = 'pk'
    model = User

    def __init__(self):
        self.jwt_manager = get_jwt_manager()
        super().__init__()

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        pk = self.jwt_manager.authorize_access_token(key)
        user = self.model.objects.filter(**{self.primary_key_field: pk}).first()
        if user is None:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))
        if not user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (user, key)

    def authenticate_header(self, request):
        return self.keyword
    
    def authorize(self, user) -> JWTPair:
        return self.jwt_manager.create_jwt_pair(pk=getattr(user, self.primary_key_field))


