"""
Stockfish chess engine integration.

Manages Stockfish lifecycle and game analysis.
Uses thread locking for safe concurrent access to engine.
"""

import io
import threading
from pydantic import BaseModel, ConfigDict
import stockfish
from app.config import settings
from chess import pgn

lock = threading.Lock()


class EvaluationModel(BaseModel):
    """Represents a single position evaluation."""
    model_config = ConfigDict(from_attributes=True)
    type: str
    value: int


class EvaluationModelResponse(BaseModel):
    """Response model for position analysis with FEN and evaluation."""
    model_config = ConfigDict(from_attributes=True)
    fen: str
    evaluation: EvaluationModel


def start_stockfish_engine():
    """Initialize and return Stockfish engine as singleton."""
    global stockfish_engine
    if "stockfish_engine" not in globals():
        stockfish_engine = stockfish.Stockfish(path=settings.stockfish_path)
        stockfish_engine.update_engine_parameters(
            {"Threads": 2, "Minimum Thinking Time": 30}
        )
        return stockfish_engine
    return None


def stop_stockfish_engine():
    """Clean up and stop the Stockfish engine."""
    global stockfish_engine
    if "stockfish_engine" in globals():
        del stockfish_engine


def analyze_game(pgn_text: str, stockfish_engine) -> list[EvaluationModelResponse]:
    """
    Analyze all positions in a chess game.
    
    Args:
        pgn_text: PGN string of the game
        stockfish_engine: Active Stockfish engine instance
    
    Returns:
        List of evaluations for each position in the game
    """
    game = pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise ValueError("Invalid PGN")

    board = game.board()
    evaluations = []

    for i, move in enumerate(game.mainline_moves()):
        board.push(move)
        send_new_game = i == 0
        with lock:
            stockfish_engine.set_fen_position(
                board.fen(), send_ucinewgame_token=send_new_game
            )
            evaluation = stockfish_engine.get_evaluation()
        evaluations.append({"fen": board.fen(), "evaluation": evaluation})

    response = [
        EvaluationModelResponse.model_validate(evaluation) for evaluation in evaluations
    ]

    return response
