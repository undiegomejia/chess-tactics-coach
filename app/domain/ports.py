"""
Port interfaces for hexagonal architecture.

Defines contracts for adapters (repository and chess engine).
"""

from typing import Protocol

from app.domain.entities import EvaluationEntity, GameEntity

class GameRepositoryPort(Protocol):
    """Port for game persistence operations."""
    def add_game(self, game: GameEntity) -> GameEntity: ...
    def get_games(self) -> list[GameEntity]: ...
    def get_game_by_id(self, game_id: int) -> GameEntity | None: ...

class ChessEnginePort(Protocol):
    """Port for chess engine analysis operations."""
    def analyze(self, game: GameEntity) -> list[EvaluationEntity]: ...
