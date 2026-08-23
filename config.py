import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration centrale de l'application."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-a-changer")

    # Récupère l'URL Neon, en s'assurant qu'elle utilise le driver psycopg (v3)
    raw_db_url = os.environ.get("DATABASE_URL", "")
    if raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Mode debug : actif seulement en local, jamais en production
    DEBUG = os.environ.get("FLASK_ENV", "development") == "development"