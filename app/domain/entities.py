from dataclasses import dataclass
from datetime import datetime

@dataclass
class EvaluationEntity:
    fen: str
    type: str
    value: int

@dataclass
class GameEntity:
    pgn: str
    white: str
    black: str
    result: str
    id: int | None = None
    created_at: datetime | None = None