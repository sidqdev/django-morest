import jwt
import time
from dataclasses import dataclass
from morest.errors import AccessTokenIsInvalidError, RefreshTokenIsInvalidError


@dataclass
class JWTPair:
    access_token: str
    refresh_token: str


class JWTManager:
    ALGORITHM = "HS256"

    def __init__(self, 
                 access_token_secret: str, refresh_token_secret: str,
                 access_token_ttl: int = None, refresh_token_ttl: int = None, 
                ):
        assert access_token_secret is not None
        assert refresh_token_secret is not None
        
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl
        self.access_token_secret = access_token_secret
        self.refresh_token_secret = refresh_token_secret

    def create_jwt_pair(self, pk) -> JWTPair:
        return JWTPair(
            access_token=jwt.encode(
                payload={
                    "type": "access",
                    "pk": pk,
                    "exp": None if self.access_token_ttl is None else int(time.time() + self.access_token_ttl)
                },
                key=self.access_token_secret,
                algorithm=self.ALGORITHM
            ),
            refresh_token=jwt.encode(
                payload={
                    "type": "refresh",
                    "pk": pk,
                    "exp": None if self.refresh_token_ttl is None else int(time.time() + self.refresh_token_ttl)
                },
                key=self.refresh_token_secret,
                algorithm=self.ALGORITHM
            ),
        )

    def refresh(self, refresh_token: str) -> JWTPair:
        return self.create_jwt_pair(pk=self.authorize_refresh_token(refresh_token=refresh_token))

    def authorize_access_token(self, access_token: str):
        '''Returns pk'''
        try:
            payload = jwt.decode(
                jwt=access_token,
                key=self.access_token_secret,
                algorithms=self.ALGORITHM,
                options={
                    "verify_exp": False
                }
            )
        except jwt.DecodeError:
            raise AccessTokenIsInvalidError

        if payload['type'] != 'access':
            raise AccessTokenIsInvalidError
        
        if payload['exp'] is not None and time.time() > payload['exp']:
            raise AccessTokenIsInvalidError

        return payload['pk']

    def authorize_refresh_token(self, refresh_token: str):
        '''Returns pk'''
        try:
            payload = jwt.decode(
                jwt=refresh_token,
                key=self.refresh_token_secret,
                algorithms=self.ALGORITHM,
                options={
                    "verify_exp": False
                }
            )
        except jwt.DecodeError:
            raise RefreshTokenIsInvalidError

        if payload['type'] != 'refresh':
            raise RefreshTokenIsInvalidError
        
        if payload['exp'] is not None and time.time() > payload['exp']:
            raise RefreshTokenIsInvalidError

        return payload['pk']


from rest_framework.authentication import TokenAuthentication
