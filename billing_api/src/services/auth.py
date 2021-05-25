from datetime import datetime
from typing import Optional, Set

import aiohttp
from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError, ExpiredTokenError, JoseError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.core.settings import settings

http_bearer = HTTPBearer(auto_error=False)


class AuthorizedUser:
    def __init__(self, token_claims: dict):
        self._id = token_claims["sub"]
        self._roles = token_claims["rls"].keys()
        self._permissions = self._get_permissions(token_claims["rls"])

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
        return "superuser" in self._roles


def _decode_token(token: str, public_key: str):
    """Метод проверки подписи и актуальности токена"""
    try:
        claims = jwt.decode(token, public_key)
    except (BadSignatureError, JoseError):
        return None

    try:
        now = datetime.utcnow().timestamp()
        claims.validate_exp(now, leeway=10)
    except ExpiredTokenError:
        return None

    return claims


async def get_public_key(url: str) -> Optional[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                # TODO: create exception
                raise Exception()

            body = await resp.json()
            return body["public_key"]


async def get_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> Optional[AuthorizedUser]:
    auth_debug = settings.auth.debug
    debug_user_id = settings.auth.debug_user_id
    auth_service_url = settings.auth.get_pubkey_url()

    if auth_debug:
        debug_claims = {
            "sub": debug_user_id,
            "rls": {},
        }
        return AuthorizedUser(debug_claims)

    if not token:
        return None

    public_key = await get_public_key(auth_service_url)

    claims = _decode_token(token.credentials, public_key)
    if not claims:
        return None

    return AuthorizedUser(claims)
