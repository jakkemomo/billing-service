from datetime import datetime
from typing import Optional, Set

import aiohttp
from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError, ExpiredTokenError, JoseError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.core.settings import logger, settings

http_bearer = HTTPBearer(auto_error=False)
auth_debug = settings.auth.debug
debug_user_id = settings.auth.debug_user_id
auth_service_url = settings.auth.get_pubkey_url()


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
        claims.validate_exp(now, leeway=0)
    except ExpiredTokenError:
        logger.debug("Token Expired!")
        return None

    return claims


async def get_public_key(url: str) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.error(f"Error while getting public key from auth service!")
                    return ""
                body = await resp.json()
                return body["public_key"]
    except Exception as e:
        logger.error(f"Error while getting public key from auth service: {e}")
        return ""


async def get_user(
        token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> Optional[AuthorizedUser]:
    if auth_debug:
        debug_claims = {
            "sub": debug_user_id,
            "rls": {},
        }
        return AuthorizedUser(debug_claims)

    if not token:
        return None

    public_key: str = await get_public_key(auth_service_url)

    claims = _decode_token(token.credentials, public_key)
    if not claims:
        return None

    return AuthorizedUser(claims)
