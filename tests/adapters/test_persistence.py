from app.adapters.persistence import GameORM
from app.domain.entities import GameEntity
import pytest


@pytest.fixture
def game_entity():
    return GameEntity(
        id=1,
        white="?",
        black="Bruce, Rowena M",
        result="1/2-1/2",
        pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.01"]\n[Round "?"]\n[White "?"]\n[Black "Bruce, Rowena M"]\n[Result "1/2-1/2"]\n\n1. e4 e5 1/2-1/2',
    )


@pytest.fixture
def game_orm():
    return GameORM(
        id=1,
        white="?",
        black="Bruce, Rowena M",
        result="1/2-1/2",
        pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.01"]\n[Round "?"]\n[White "?"]\n[Black "Bruce, Rowena M"]\n[Result "1/2-1/2"]\n\n1. e4 e5 1/2-1/2',
    )


@pytest.fixture
def game_entity_list():
    game_entity_1 = GameEntity(
        id=1,
        white="?",
        black="Bruce, Rowena M",
        result="1/2-1/2",
        pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.01"]\n[Round "?"]\n[White "?"]\n[Black "Bruce, Rowena M"]\n[Result "1/2-1/2"]\n\n1. e4 e5 1/2-1/2',
    )
    game_entity_2 = GameEntity(
        id=2,
        white="Alice",
        black="Bob",
        result="1-0",
        pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.02"]\n[Round "?"]\n[White "Alice"]\n[Black "Bob"]\n[Result "1-0"]\n\n1. d4 d5 2. c4 1-0',
    )
    return [game_entity_1, game_entity_2]


class FakeSQLAlchemyGameRepository:
    def __init__(self, _):
        return

    def add_game(self, game_entity: GameEntity) -> GameEntity:
        return game_entity

    def get_games(self) -> list[GameEntity]:
        game_entity_1 = GameEntity(
            id=1,
            white="?",
            black="Bruce, Rowena M",
            result="1/2-1/2",
            pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.01"]\n[Round "?"]\n[White "?"]\n[Black "Bruce, Rowena M"]\n[Result "1/2-1/2"]\n\n1. e4 e5 1/2-1/2',
        )
        game_entity_2 = GameEntity(
            id=2,
            white="Alice",
            black="Bob",
            result="1-0",
            pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.02"]\n[Round "?"]\n[White "Alice"]\n[Black "Bob"]\n[Result "1-0"]\n\n1. d4 d5 2. c4 1-0',
        )
        return [game_entity_1, game_entity_2]

    def get_game_by_id(self, game_id: int) -> GameEntity | None:
        for game in self.get_games():
            if game.id == game_id:
                return game
        return None


def test_game_orm_to_entity_conversion(game_orm, game_entity):
    """Test conversion from GameORM to GameEntity."""
    entity = game_orm.to_entity()
    assert entity == game_entity


def test_game_entity_to_orm_conversion(game_orm, game_entity):
    """Test conversion from GameEntity to GameORM."""
    orm = GameORM.from_entity(game_entity)
    assert orm.id == game_orm.id
    assert orm.white == game_orm.white
    assert orm.black == game_orm.black
    assert orm.result == game_orm.result


def test_repository_add_game(game_entity):
    """Test adding a game to the repository."""
    repo = FakeSQLAlchemyGameRepository(None)
    added_game = repo.add_game(game_entity)
    assert added_game == game_entity


def test_repository_get_games(game_entity_list):
    """Test retrieving all games from the repository."""
    repo = FakeSQLAlchemyGameRepository(None)
    games = repo.get_games()
    assert games == game_entity_list


def test_repository_get_game_by_id():
    """Test retrieving a game by ID from the repository."""
    repo = FakeSQLAlchemyGameRepository(None)
    list_of_games = repo.get_games()
    for game in list_of_games:
        fetched_game = repo.get_game_by_id(game.id)
        assert fetched_game == game
    # Test for a non-existent game ID
    assert repo.get_game_by_id(999) is None
