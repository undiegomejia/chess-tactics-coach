from app.adapters.persistence import GameORM
from app.domain.entities import GameEntity
from tests.conftest import game_entity_list, game_orm, game_entity

game_entity_list_mock = game_entity_list
game_orm_mock = game_orm
game_entity_mock = game_entity

class FakeSQLAlchemyGameRepository:
    def __init__(self, _):
        return

    def add_game(self, game_entity_list_mock: GameEntity) -> GameEntity:
        return  game_entity_list_mock

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


def test_game_orm_to_entity_conversion(game_orm_mock, game_entity_mock):
    """Test conversion from GameORM to GameEntity."""
    entity = game_orm_mock.to_entity()
    assert entity == game_entity_mock


def test_game_entity_to_orm_conversion(game_orm_mock, game_entity_mock):
    """Test conversion from GameEntity to GameORM."""
    orm = GameORM.from_entity(game_entity_mock)
    assert orm.id == game_orm_mock.id
    assert orm.white == game_orm_mock.white
    assert orm.black == game_orm_mock.black
    assert orm.result == game_orm_mock.result


def test_repository_add_game(game_entity_mock):
    """Test adding a game to the repository."""
    repo = FakeSQLAlchemyGameRepository(None)
    added_game = repo.add_game(game_entity_mock)
    assert added_game == game_entity_mock


def test_repository_get_games(game_entity_list_mock):
    """Test retrieving all games from the repository."""
    repo = FakeSQLAlchemyGameRepository(None)
    games = repo.get_games()
    assert games == game_entity_list_mock


def test_repository_get_game_by_id():
    """Test retrieving a game by ID from the repository."""
    repo = FakeSQLAlchemyGameRepository(None)
    list_of_games = repo.get_games()
    for game in list_of_games:
        fetched_game = repo.get_game_by_id(game.id)
        assert fetched_game == game
    # Test for a non-existent game ID
    assert repo.get_game_by_id(999) is None
