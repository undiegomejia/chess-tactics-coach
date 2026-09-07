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

class MistakeModelResponse(BaseModel):
    """Response model for detected mistakes."""
    model_config = ConfigDict(from_attributes=True)
    move_number: int
    player: str
    fen_before: str
    fen_after: str
    eval_before: int
    eval_before_type: str
    eval_after: int
    eval_after_type: str
    move_played: str

class AlternativeMoveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    move_san: str
    move_uci: str | None
    short_line: str
    eval_after_line: str
    rationale: str

class ExplanationModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    mistake: MistakeModelResponse
    mistake_category: str
    concise_explanation: str
    concrete_variation: str
    best_alternatives: list[AlternativeMoveResponse]
    tactical_motifs: list[str]
    strategic_factors: list[str]
    recommended_plan: str
    confidence: float
    best_move: str | None