# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_NAME: str = "genealogy_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    PORT: int = 5050
    DEBUG: bool = True
    GOOGLE_MAPS_API_KEY: str = "AIza..."

    @property
    def DATABASE_URI(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
