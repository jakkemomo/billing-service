import logging

import aiohttp
from src.core.settings import settings

logger = logging.getLogger(__name__)


class RolesService:
    def __init__(self, url_pattern: str):
        self.url_pattern = url_pattern

    async def grant_role(self, user_id: str, role_id: str) -> bool:
        url = self.url_pattern % (user_id, role_id)
        logger.info(f"Sending request to update user roles to AUTH API. User {user_id} Role {role_id}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as resp:
                    if resp.status == 200:
                        return True
                    if resp.status == 409:
                        logger.info("User %s already has role %s" % (user_id, role_id))
                    elif resp.status == 404:
                        logger.error(
                            "User %s or role %s not found" % (user_id, role_id)
                        )
                    return False
        except Exception as e:
            logger.error(f"Error while granting role through Auth API by url {url}: {e}")
            return False

    async def revoke_role(self, user_id: str, role_id: str) -> bool:
        url = self.url_pattern % (user_id, role_id)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url) as resp:
                    if resp.status == 200:
                        logger.error(f"User {user_id} or role {role_id} not found")
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error while revoking role through Auth API by url {url}: {e}")
            return False


def get_roles_service() -> RolesService:
    roles_url_pattern = settings.auth.get_roles_url()
    return RolesService(roles_url_pattern)
