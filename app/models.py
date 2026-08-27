"""
SQLAlchemy ORM models.

Defines the Game table structure for storing chess games.
"""

from datetime import datetime, timezone
from app.database import Base
from sqlalchemy import Integer, String, Text, DateTime, Column

def get_datetime():
    """Return current UTC datetime for created_at default."""
    return datetime.now(timezone.utc)

class Game(Base):
    """Game model representing a stored chess game."""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    pgn = Column(Text, nullable=False)
    white = Column(String(100), nullable=False)
    black = Column(String(100), nullable=False)
    result = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_datetime, nullable=False)

    