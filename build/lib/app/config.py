"""
Application configuration management.

Loads environment variables from .env file using Pydantic Settings.
Main settings: stockfish_path, database_url.
"""
from pydantic import SecretStr
from pydantic.fields import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    stockfish_path: str = "/usr/local/bin/stockfish"
    database_url: str = "sqlite:///./data/chess.db"
    anthropic_api_key: SecretStr = Field(alias="CLAUDE_API_KEY")

settings = Settings()
