import logging
from datetime import datetime
from typing import Optional, Set

import backoff
from aiohttp import ClientConnectorError, ClientSession, ServerConnectionError
from async_lru import alru_cache
from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError, ExpiredTokenError, JoseError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.core.settings import settings

logger = logging.getLogger(__name__)

http_bearer = HTTPBearer(auto_error=False)

DEBUG = settings.auth.debug
DEBUG_USER_ID = settings.auth.debug_user_id
AUTH_URL = settings.auth.get_pubkey_url()

BACKOFF_FACTOR = settings.backoff.factor
BACKOFF_BASE = settings.backoff.base
BACKOFF_MAX_VALUE = settings.backoff.max_value


class GettingPubKeyError(Exception):
    pass


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
        for permissions in roles.values():
            user_permissions.update(permissions)
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


@alru_cache(cache_exceptions=False)
@backoff.on_exception(
    backoff.expo,
    (ClientConnectorError, ServerConnectionError, GettingPubKeyError),
    base=BACKOFF_BASE,
    factor=BACKOFF_FACTOR,
    max_value=BACKOFF_MAX_VALUE,
)
async def get_public_key(url: str) -> str:
    async with ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                logger.error("Error while getting public key from auth service")
                raise GettingPubKeyError()
            body = await resp.json()
            return body["public_key"]


async def get_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> Optional[AuthorizedUser]:
    if DEBUG:
        debug_claims = {
            "sub": DEBUG_USER_ID,
            "rls": {},
        }
        return AuthorizedUser(debug_claims)

    if not token:
        return None

    public_key = await get_public_key(AUTH_URL)

    claims = _decode_token(token.credentials, public_key)
    if not claims:
        return None

    return AuthorizedUser(claims)
