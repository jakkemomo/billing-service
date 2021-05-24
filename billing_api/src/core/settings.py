import logging
import pathlib

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

from .logging import LOGGING_CFG

BASE_DIR = pathlib.Path(__file__).parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"

logging.config.dictConfig(LOGGING_CFG)

load_dotenv()


class DatabaseSettings(BaseSettings):
    host: str = Field("localhost", env="DB_HOST")
    port: int = Field(5432, env="DB_PORT")
    user: str = Field("postgres", env="DB_USER")
    password: str = Field("postgres", env="DB_PASSWORD")
    database: str = Field("postgres", env="DB_NAME")
    scheme: str = Field("public", env="DB_SCHEMA", alias="schema")


class StripeSettings(BaseSettings):
    url: str = Field("https://api.stripe.com/v1", env="STRIPE_URL")
    api_key: str = Field(None, env="STRIPE_API_KEY")


class BackoffSettings(BaseSettings):
    factor: float = Field(1, env="BACKOFF_FACTOR")
    base: float = Field(2, env="BACKOFF_BASE")
    max_value: float = Field(None, env="BACKOFF_MAX_VALUE")


class Settings(BaseSettings):
    stripe: StripeSettings = StripeSettings()
    db: DatabaseSettings = DatabaseSettings()
    backoff: BackoffSettings = BackoffSettings()


settings = Settings.parse_file(DEFAULT_CONFIG_PATH)
