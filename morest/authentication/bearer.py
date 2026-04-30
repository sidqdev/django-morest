from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header


class BearerTokenAuthentication(BaseAuthentication):
    """
    Simple bearer token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Bearer ".  For example:

        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = 'Bearer'
    
    def get_model(self):
        from morest.bearertoken.models import BearerToken
        return BearerToken

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

    def find_token(self, key: str):
        return self.get_model().objects.select_related('user').filter(
            key=key, is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
        ).first()
    
    def authenticate_credentials(self, key):
        token = self.find_token(key=key)
        if token is None:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (token.user, token)

    def authenticate_header(self, request):
        return self.keyword


