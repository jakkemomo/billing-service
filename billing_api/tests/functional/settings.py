from os import environ as env

from dotenv import load_dotenv

load_dotenv()

SERVICE_URL: str = env.get("SERVICE_URL", "http://0.0.0.0:8092")
# DB_HOST: str = env.get("DB_HOST", "127.0.0.1")
# DB_PORT: str = env.get("DB_PORT", "27017")
# DB_NAME: str = env.get("DB_NAME", "user_data_test")
