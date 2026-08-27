"""
Application configuration management.

Loads environment variables from .env file using Pydantic Settings.
Main settings: stockfish_path, database_url.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    stockfish_path: str = "/usr/local/bin/stockfish"
    database_url: str = "sqlite:///./data/chess.db"


settings = Settings()
