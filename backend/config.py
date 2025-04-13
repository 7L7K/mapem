# /Users/kingal/mapem/backend/config.py
from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    DB_NAME: str = "genealogy_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    PORT: int = 5050
    DEBUG: bool = False
    GOOGLE_MAPS_API_KEY: str = ""

    @property
    def database_uri(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # <-- this right here


# Global settings instance
settings = Settings()
