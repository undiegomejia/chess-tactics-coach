"""
Domain entities representing core business objects.

Pure Python dataclasses without framework dependencies.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

@dataclass
class EvaluationEntity:
    """Position evaluation from chess engine."""
    fen: str
    type: str
    value: int
    move_played: str = ""

@dataclass
class GameEntity:
    """Chess game domain entity."""
    pgn: str
    white: str
    black: str
    result: str
    id: int | None = None
    created_at: datetime | None = None

@dataclass
class Mistake:
    """Represents a mistake in a chess game."""
    move_number: int
    player: str          # "white" | "black"
    fen_before: str
    fen_after: str
    eval_before: int     # centipawns
    eval_before_type: str  # "cp" | "mate"
    eval_after: int
    eval_after_type: str   # "cp" | "mate"
    move_played: str


@dataclass
class AlternativeMoveEntity:
    move_san: str
    move_uci: str | None
    short_line: str | None
    eval_after_line: int | None
    rationale: str

@dataclass
class Explanation:
    """Represents an explanation for a mistake."""
    mistake: Mistake
    mistake_category: str
    concise_explanation: str
    concrete_variation: str
    best_alternatives: list[AlternativeMoveEntity]
    tactical_motifs: list[str]
    strategic_factors: list[str]
    recommended_plan: str
    confidence: float
    best_move: str | None


@dataclass
class Drill:
    mistake: Mistake
    fen_before: str
    correct_move: str # UCI format
    target_evaluation: int #always store the pre-normalized centipawn-equivalent
    # SM-2 state
    repetition_count: int = 0
    ease_factor: float = 2.5
    interval: int = 1
    next_review_date: date = field(default_factory=date.today)
    last_reviewed_at: datetime | None = None
    id: int | None = None