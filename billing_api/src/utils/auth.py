from datetime import datetime
from functools import lru_cache
from typing import Optional, Set

import aiohttp
from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError, ExpiredTokenError, JoseError
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

http_bearer = HTTPBearer(auto_error=False)

AUTH_DEBUG = 1
DEBUG_USER_ID = '60cac095-f081-4d01-bbc1-0f7197c1f99e'
AUTH_SERVICE_URI = 'http://127.0.0.1:8000/api/v1/pubkey'


class AuthorizedUser:

    def __init__(self, token_claims: dict):
        self._id = token_claims['sub']
        self._roles = token_claims['rls'].keys()
        self._permissions = self._get_permissions(token_claims['rls'])

    @property
    def id(self):
        return self._id

    @staticmethod
    def _get_permissions(roles: dict) -> Set[str]:
        user_permissions = set()
        for role_name in roles:
            user_permissions.update(roles[role_name])
        return user_permissions

    def has_permissions(self, *permissions) -> bool:
        return self._permissions.issuperset(permissions)

    def is_superuser(self) -> bool:
        return 'superuser' in self._roles


def _decode_token(token: str, public_key: str):
    """Метод проверки подписи и актуальности токена"""
    try:
        claims = jwt.decode(token, public_key)
    except (BadSignatureError, JoseError):
        return None

    try:
        now = datetime.utcnow().timestamp()
        claims.validate_exp(now)
    except ExpiredTokenError:
        return None

    return claims


@lru_cache()
async def get_public_key() -> Optional[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(AUTH_SERVICE_URI) as resp:
            if resp.status != 200:
                # TODO: create exception
                raise Exception()

            body = await resp.json()
            return body['public_key']


async def get_user(
        token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> Optional[AuthorizedUser]:
    if AUTH_DEBUG:
        debug_claims = {
            "sub": DEBUG_USER_ID,
            "rls": {},
        }
        return AuthorizedUser(debug_claims)

    if not token:
        return None

    public_key = await get_public_key()

    claims = _decode_token(token.credentials, public_key)
    if not claims:
        return None

    return AuthorizedUser(claims)
