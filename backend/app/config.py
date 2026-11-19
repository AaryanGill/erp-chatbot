import os
from dotenv import load_dotenv

load_dotenv()  # reads variables from the .env file into the environment


def _database_url():
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://erp_user:test123@localhost:5432/erp_chatbot_db"
    )
    # Some hosting services still use the old "postgres://" spelling
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Cloud databases close idle connections; test each one before use and refresh old ones
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-this")
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"