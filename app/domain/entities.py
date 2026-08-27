"""
Domain entities representing core business objects.

Pure Python dataclasses without framework dependencies.
"""

from dataclasses import dataclass
from datetime import datetime

@dataclass
class EvaluationEntity:
    """Position evaluation from chess engine."""
    fen: str
    type: str
    value: int

@dataclass
class GameEntity:
    """Chess game domain entity."""
    pgn: str
    white: str
    black: str
    result: str
    id: int | None = None
    created_at: datetime | None = None