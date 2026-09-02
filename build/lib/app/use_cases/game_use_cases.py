"""
Game use cases.

Business logic orchestration for game operations.
"""

import io
from app.domain.entities import EvaluationEntity, GameEntity
from app.domain.ports import ChessEnginePort, GameRepositoryPort
import chess.pgn


def create_game(pgn_str: str, repo: GameRepositoryPort) -> GameEntity:
    parsed_game = chess.pgn.read_game(io.StringIO(pgn_str))
    if parsed_game is None:
        raise ValueError("Invalid PGN - unable to parse")
    if list(parsed_game.mainline_moves()) == []:
        raise ValueError("Invalid PGN - no moves found.")
    white = parsed_game.headers["White"]
    black = parsed_game.headers["Black"]
    result = parsed_game.headers["Result"]
    new_game = GameEntity(
        pgn=pgn_str,
        white=white,
        black=black,
        result=result,   
    )

    return repo.add_game(new_game)

def fetch_game(game_id: int, repo: GameRepositoryPort) -> GameEntity | None:
    return repo.get_game_by_id(game_id)

def list_games(repo: GameRepositoryPort) -> list[GameEntity]:
    return repo.get_games()

def analyze_game(game_id: int, repo: GameRepositoryPort, 
                 engine: ChessEnginePort) -> list[EvaluationEntity]:
    game = repo.get_game_by_id(game_id)
    if game is None:
        raise ValueError(f"Game with ID {game_id} not found.")
    evaluations = engine.analyze(game)
    return evaluations