from dotenv import load_dotenv
from pydantic import BaseSettings, Field

load_dotenv()


class TestSettings(BaseSettings):
    STRIPE_API_KEY: str = Field('check', env="STRIPE_API_KEY")
    ACCESS_TOKEN: str = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkMzA2ZjYyMC0yMDgzLTRjNTUtYjY2Zi03MTcxZmZmZWNjMmIiLCJpYXQiOjE1MTYyMzkwMjJ9.sf4fYKlDrLwtt55dvC_FKy5_MRLnCeUTOCCG723pNIs"
    DEBUG_USER_ID: str = "d306f620-2083-4c55-b66f-7171fffecc2b"


test_settings = TestSettings()
