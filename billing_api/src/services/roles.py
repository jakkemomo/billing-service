"""Module with role management service"""

import logging

import aiohttp
import backoff
from aiohttp import ClientConnectorError, ClientResponse, ServerConnectionError
from src.core.settings import settings

logger = logging.getLogger(__name__)

BACKOFF_FACTOR = settings.backoff.factor
BACKOFF_BASE = settings.backoff.base
BACKOFF_MAX_VALUE = settings.backoff.max_value


class RoleServiceException(Exception):
    """Roles service base exception"""

    def __init__(self, msg: str, *args):
        super().__init__(*args)
        self.msg = msg


class RoleServiceConflictError(RoleServiceException):
    """Exception for the case where an user already has a role"""

    pass


class RoleServiceNotFoundError(RoleServiceException):
    """Exception for the case where an user or a role not found"""

    pass


EXCEPTIONS_MAPPING = {
    404: RoleServiceNotFoundError,
    409: RoleServiceConflictError,
}


async def handle_response(resp: ClientResponse) -> ClientResponse:
    """
    Handle response from auth service

    @param resp: `aiohttp.ClientResponse` response object
    @return: `aiohttp.ClientResponse` object for the cases where response has status code 200.
    @raise: one of exceptions from `EXCEPTIONS_MAPPING` dictionary depending on response status code
    """
    exception_cls = EXCEPTIONS_MAPPING[resp.status]
    if not exception_cls:
        return resp
    body = await resp.json()
    description = body["description"]
    raise exception_cls(description)


class RolesService:
    """Class to perform granting and revoking roles to users"""

    def __init__(self, url_pattern: str):
        self.url_pattern = url_pattern

    @backoff.on_exception(
        backoff.expo,
        (ClientConnectorError, ServerConnectionError),
        base=BACKOFF_BASE,
        factor=BACKOFF_FACTOR,
        max_value=BACKOFF_MAX_VALUE,
    )
    async def _request(self, method: str, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url) as resp:
                return handle_response(resp)

    async def grant_role(self, user_id: str, role_id: str) -> None:
        """
        Perform role granting

        @param user_id: user identifier
        @param role_id: role identifier
        """
        method = "POST"
        url = self.url_pattern % (user_id, role_id)
        await self._request(method, url)

    async def revoke_role(self, user_id: str, role_id: str) -> None:
        """
        Perform role revoking

        @param user_id: user identifier
        @param role_id: role identifier
        """
        method = "DELETE"
        url = self.url_pattern % (user_id, role_id)
        await self._request(method, url)


def get_roles_service() -> RolesService:
    """
    Get configured class `RolesService` instance
    @return: class `RolesService` instance
    """
    roles_url_pattern = settings.auth.get_roles_url()
    return RolesService(roles_url_pattern)
