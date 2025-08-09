# backend/config.py

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import ClassVar

# ─────────────────────────────────────────────
# File System Constants
# ─────────────────────────────────────────────

# Always points to backend/
BASE_DIR = Path(__file__).resolve().parent

# Allow override with MAPEM_DATA_DIR and MAPEM_LOG_DIR, else default to subfolders in backend/
DATA_DIR = Path(os.getenv("MAPEM_DATA_DIR", BASE_DIR / "data"))
LOG_DIR = Path(os.getenv("MAPEM_LOG_DIR", BASE_DIR / "logs"))

# ─────────────────────────────────────────────
# Settings Class (Pydantic)
# ─────────────────────────────────────────────

class Settings(BaseSettings):
    DB_NAME: str = "genealogy_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    PORT: int = 5050
    DEBUG: bool = False
    GOOGLE_MAPS_API_KEY: str = ""
    GEOCODE_API_KEY: str = ""
    SQLALCHEMY_ECHO: ClassVar[bool] = True  # Can make dynamic if you want
    ALLOW_GEOCODE_EXTERNAL: bool = True

    @property
    def database_uri(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

# Global instance
settings = Settings()

# ─────────────────────────────────────────────
# Visible Path & Key Check (Debug)
# ─────────────────────────────────────────────

def _show_partial_key(key: str) -> str:
    if not key:
        return "❌ MISSING"
    if len(key) < 8:
        return "🔒 (short/hidden)"
    return key[:4] + "..." + key[-4:]

if __name__ == "__main__" or os.getenv("MAPEM_DEBUG_CONFIG", "") == "1":
    print("🗂️  BASE_DIR:", BASE_DIR)
    print("📁 DATA_DIR:", DATA_DIR)
    print("🗂️  LOG_DIR:", LOG_DIR)
    print("🔑 GOOGLE_MAPS_API_KEY:", _show_partial_key(settings.GOOGLE_MAPS_API_KEY))
    print("🔑 GEOCODE_API_KEY:", _show_partial_key(settings.GEOCODE_API_KEY))
    print("🐘 DB URI:", settings.database_uri)
    print("🛠️  SQLALCHEMY_ECHO:", settings.SQLALCHEMY_ECHO)

