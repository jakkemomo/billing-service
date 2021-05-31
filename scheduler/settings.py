import logging

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Settings(BaseSettings):
    DB_NAME: str = Field("billing", env="DB_NAME")
    DB_USER: str = Field("scheduler", env="DB_USER")
    DB_PASSWORD: str = Field("scheduler", env="DB_PASSWORD")
    DB_HOST: str = Field("localhost", env="DB_HOST")
    DB_PORT: str = Field("5432", env="DB_PORT")
    DB_SCHEMA: str = Field("data", env="DB_SCHEMA")
    REQUEST_DELAY: int = 1
    BILLING_API_HOST: str = Field("localhost", env="BILLING_API_HOST")
    BILLING_API_PORT: str = Field("8787", env="BILLING_API_PORT")

    def get_service_url(self):
        return f"http://{self.BILLING_API_HOST}:{self.BILLING_API_PORT}/api/service"
