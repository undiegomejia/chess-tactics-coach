"""
SQLAlchemy persistence adapter.

Implements GameRepositoryPort using SQLAlchemy ORM.
Converts between domain entities and database models.
"""

from app.database import Base
from sqlalchemy import Float, Integer, String, Text, DateTime, Date
from app.domain.entities import Drill, GameEntity, Mistake
from datetime import datetime, timezone, date
from sqlalchemy.orm import Mapped, mapped_column

def get_datetime():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)

class DrillORM(Base):
    __tablename__ = "drills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Evaluation details
    fen_before: Mapped[str] = mapped_column(String(90), nullable=False)
    correct_move: Mapped[str] = mapped_column(String(4), nullable=False)
    target_evaluation: Mapped[int] = mapped_column(Integer, nullable=False)
    # SM-2 state
    repetition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5, server_default="2.5")
    interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    next_review_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, server_default=None)
    # Mistake details
    mistake_move_number: Mapped[int] = mapped_column(Integer, nullable=False)
    mistake_player: Mapped[str] = mapped_column(String(100), nullable=False)
    mistake_fen_before: Mapped[str] = mapped_column(String(90), nullable=False)
    mistake_fen_after: Mapped[str] = mapped_column(String(90), nullable=False)
    mistake_eval_before: Mapped[int] = mapped_column(Integer, nullable=False)
    mistake_eval_before_type: Mapped[str] = mapped_column(String(10), nullable=False)
    mistake_eval_after: Mapped[int] = mapped_column(Integer, nullable=False)
    mistake_eval_after_type: Mapped[str] = mapped_column(String(10), nullable=False)
    mistake_move_played: Mapped[str] = mapped_column(String(10), nullable=False)


    def to_entity(self) -> Drill:
        mistake = Mistake(
            move_number=self.mistake_move_number,
            player=self.mistake_player,
            fen_before=self.mistake_fen_before,
            fen_after=self.mistake_fen_after,
            eval_before=self.mistake_eval_before,
            eval_before_type=self.mistake_eval_before_type,
            eval_after=self.mistake_eval_after,
            eval_after_type=self.mistake_eval_after_type,
            move_played=self.mistake_move_played
        )
        return Drill(
            mistake=mistake,
            fen_before=self.fen_before,
            correct_move=self.correct_move,
            target_evaluation=self.target_evaluation,
            repetition_count=self.repetition_count,
            ease_factor=self.ease_factor,
            interval=self.interval,
            next_review_date=self.next_review_date,
            last_reviewed_at=self.last_reviewed_at
        )

    @classmethod
    def from_entity(cls, drill: Drill) -> "DrillORM":
        return cls(
            fen_before=drill.fen_before,
            correct_move=drill.correct_move,
            target_evaluation=drill.target_evaluation,
            repetition_count=drill.repetition_count,
            ease_factor=drill.ease_factor,
            interval=drill.interval,
            next_review_date=drill.next_review_date,
            last_reviewed_at=drill.last_reviewed_at,
            mistake_move_number=drill.mistake.move_number,
            mistake_player=drill.mistake.player,
            mistake_fen_before=drill.mistake.fen_before,
            mistake_fen_after=drill.mistake.fen_after,
            mistake_eval_before=drill.mistake.eval_before,
            mistake_eval_before_type=drill.mistake.eval_before_type,
            mistake_eval_after=drill.mistake.eval_after,
            mistake_eval_after_type=drill.mistake.eval_after_type,
            mistake_move_played=drill.mistake.move_played
            )


class GameORM(Base):
    """ORM model for games table."""
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pgn: Mapped[str] = mapped_column(Text, nullable=False)
    white: Mapped[str] = mapped_column(String(100), nullable=False)
    black: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_datetime, nullable=False)

    def to_entity(self) -> GameEntity:
        """Convert ORM model to domain entity."""
        return GameEntity(
            id=self.id,
            pgn=self.pgn,
            white=self.white,
            black=self.black,
            result=self.result,
            created_at=self.created_at
        )
    
    @classmethod
    def from_entity(cls, game_entity: GameEntity) -> "GameORM":
        """Create ORM model from domain entity."""
        return cls(
            id=game_entity.id,
            pgn=game_entity.pgn,
            white=game_entity.white,
            black=game_entity.black,
            result=game_entity.result,
            created_at=game_entity.created_at
        )
    
class SQLAlchemyGameRepository:
    """Repository implementation using SQLAlchemy."""
    def __init__(self, session):
        self.session = session

    def add_game(self, game_entity: GameEntity) -> GameEntity:
        """Add a new game to the database."""
        game_orm = GameORM.from_entity(game_entity)
        self.session.add(game_orm)
        self.session.commit()
        self.session.refresh(game_orm)
        return game_orm.to_entity()

    def get_games(self) -> list[GameEntity]:
        """Retrieve all games from database."""
        games = self.session.query(GameORM).all()
        return [game.to_entity() for game in games]
    
    def get_game_by_id(self, game_id: int) -> GameEntity | None:
        """Retrieve a specific game by ID, or None if not found."""
        game = self.session.query(GameORM).filter(GameORM.id == game_id).first()
        if not game:
            return None
        return game.to_entity()