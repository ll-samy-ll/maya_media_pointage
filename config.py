import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# --- DEBUG TEMPORAIRE ---
raw_db_url_debug = os.environ.get("DATABASE_URL", "")
print("=" * 60)
print("DEBUG DATABASE_URL")
print("Longueur:", len(raw_db_url_debug))
print("Repr:", repr(raw_db_url_debug))
print("=" * 60)
# --- FIN DEBUG ---


class Config:
    """Configuration centrale de l'application."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-a-changer")

    raw_db_url = os.environ.get("DATABASE_URL", "")

    if not raw_db_url:
        raise RuntimeError(
            "La variable d'environnement DATABASE_URL est manquante ou vide."
        )

    if raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    DEBUG = os.environ.get("FLASK_ENV", "development") == "development"