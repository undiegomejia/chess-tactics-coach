"""
Settings loading. This one's fully implemented for you -- it's infra
plumbing, not a design decision you need to practice yet. Pydantic's
BaseSettings reads from environment variables (and a .env file via
python-dotenv), which is the standard pattern for 12-factor config.

Worth understanding *why* this exists even though you didn't write it:
hardcoding STOCKFISH_PATH or DATABASE_URL directly in code is a code
smell we'll talk about in Phase 2 (secrets management) -- config that
differs between your machine, a teammate's machine, and CI should never
be a literal in a .py file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    stockfish_path: str = "/usr/local/bin/stockfish"
    database_url: str = "sqlite:///./data/chess.db"


settings = Settings()
