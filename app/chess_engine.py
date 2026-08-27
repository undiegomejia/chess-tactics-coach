"""
TODO: Stockfish integration via python-chess.

Two libraries are available and doing different jobs -- don't conflate
them:
  - `chess` (python-chess): parses PGN, represents boards/moves, has
     its own `chess.engine` module for talking to UCI engines.
  - `stockfish` (the pip package): a friendlier high-level wrapper
     around the same binary.

Pick ONE approach and justify it in your PR notes / to me when I review:
  (a) `chess.engine.SimpleEngine.popen_uci(settings.stockfish_path)`
      -- lower-level, more control, matches python-chess's PGN objects
      directly.
  (b) `stockfish.Stockfish(path=settings.stockfish_path)`
      -- higher-level, simpler API, but you'll be converting between
      its representation and python-chess's Board when you parse PGNs.

Functions to build:

1. `analyze_position(board: chess.Board, depth: int = 15) -> dict`
   Returns something like {"score_cp": int, "best_move": str}.
   Handle the case where Stockfish reports mate-in-N instead of a
   centipawn score -- don't let that crash the endpoint.

2. `analyze_game(pgn_text: str, depth: int = 15) -> list[dict]`
   Parses the PGN into a game, walks through the moves, and returns
   an evaluation for each position (or just the final position for
   the first pass -- full per-move analysis can come later, it's
   slower).

Think about engine lifecycle: opening a new Stockfish process per
request is wasteful. Should the engine process be a singleton reused
across requests? A pool? Started at app startup and closed at
shutdown? This connects to a FastAPI concept called lifespan events
-- worth reading about before you commit to an approach.
"""

# import chess
# import chess.engine
# from app.config import settings

# TODO: analyze_position(...)
# TODO: analyze_game(...)


import io
import threading
from pydantic import BaseModel, ConfigDict
import stockfish
from app.config import settings
from chess import pgn

lock = threading.Lock()


class EvaluationModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    value: int


class EvaluationModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fen: str
    evaluation: EvaluationModel


def start_stockfish_engine():
    """Start the Stockfish engine as a singleton."""
    global stockfish_engine
    if "stockfish_engine" not in globals():
        stockfish_engine = stockfish.Stockfish(path=settings.stockfish_path)
        stockfish_engine.update_engine_parameters(
            {"Threads": 2, "Minimum Thinking Time": 30}
        )
        return stockfish_engine
    return None


def stop_stockfish_engine():
    """Stop the Stockfish engine."""
    global stockfish_engine
    if "stockfish_engine" in globals():
        del stockfish_engine


def analyze_game(pgn_text: str, stockfish_engine) -> list[EvaluationModelResponse]:
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
