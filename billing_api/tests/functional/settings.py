from os import environ as env

from dotenv import load_dotenv
from src.core.settings import settings

load_dotenv()

STRIPE_API_KEY = env.get("STRIPE_API_KEY")
STRIPE_URL = settings.stripe.url
DEBUG_USER_ID = "d306f620-2083-4c55-b66f-7171fffecc2b"
ACCESS_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkMzA2ZjYyMC0yMDgzLTRjNTUtYjY2Zi03MTcxZmZmZWNjMmIiLCJpYXQiOjE1MTYyMzkwMjJ9.sf4fYKlDrLwtt55dvC_FKy5_MRLnCeUTOCCG723pNIs"
