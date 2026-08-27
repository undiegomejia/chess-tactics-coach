from app.database import Base
from sqlalchemy import Integer, String, Text, DateTime
from app.domain.entities import GameEntity
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column

def get_datetime():
    return datetime.now(timezone.utc)

class GameORM(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pgn: Mapped[str] = mapped_column(Text, nullable=False)
    white: Mapped[str] = mapped_column(String(100), nullable=False)
    black: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_datetime, nullable=False)

    def to_entity(self) -> GameEntity:
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
        return cls(
            id=game_entity.id,
            pgn=game_entity.pgn,
            white=game_entity.white,
            black=game_entity.black,
            result=game_entity.result,
            created_at=game_entity.created_at
        )
    
class SQLAlchemyGameRepository:
    def __init__(self, session):
        self.session = session

    def add_game(self, game_entity: GameEntity) -> GameEntity:
        game_orm = GameORM.from_entity(game_entity)
        self.session.add(game_orm)
        self.session.commit()
        self.session.refresh(game_orm)
        return game_orm.to_entity()

    def get_games(self) -> list[GameEntity]:
        games = self.session.query(GameORM).all()
        return [game.to_entity() for game in games]
    
    def get_game_by_id(self, game_id: int) -> GameEntity | None:
        game = self.session.query(GameORM).filter(GameORM.id == game_id).first()
        if not game:
            return None
        return game.to_entity()