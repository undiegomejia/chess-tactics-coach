from datetime import datetime
from pydantic import BaseModel
from pydantic.config import ConfigDict


class PostGame(BaseModel):
    """Request model for creating a new game."""
    model_config = ConfigDict(from_attributes=True)
    pgn: str

class GetGame(BaseModel):
    """Response model for game summary (without full PGN)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    white: str
    black: str
    result: str
    created_at: datetime

class GameCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    white: str
    black: str
    result: str
    created_at: datetime
    pgn: str

class EvaluationModelResponse(BaseModel):
    """Response model for position analysis with FEN and evaluation."""
    model_config = ConfigDict(from_attributes=True)
    fen: str
    type: str
    value: int

