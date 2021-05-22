import logging

import aiohttp
from aiohttp import ClientConnectionError

logger = logging.getLogger(__name__)

AUTH_ROLE_URL_PATTERN = "http://127.0.0.1:8000/api/v1/admin/user/%s/role/%s"


class RolesService:
    def __init__(self, url_pattern: str):
        self.url_pattern = url_pattern

    async def grant_role(self, user_id: str, role_id: str) -> None:
        url = self.url_pattern % (user_id, role_id)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as resp:
                    if resp.status == 409:
                        logger.info("User %s already has role %s" % (user_id, role_id))
                    elif resp.status == 404:
                        logger.error("User %s or role %s not found" % (user_id, role_id))
                        # TODO: Create exception
                        raise Exception()
        except ClientConnectionError as e:
            logger.error(f"Auth service is not available. Couldn't update role!")

    async def revoke_role(self, user_id: str, role_id: str):
        url = self.url_pattern % (user_id, role_id)
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as resp:
                if resp.status == 404:
                    logger.error("User %s or role %s not found" % (user_id, role_id))
                    # TODO: Create exception
                    raise Exception()


def get_roles_service() -> RolesService:
    return RolesService(AUTH_ROLE_URL_PATTERN)
