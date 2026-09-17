from datetime import date, timedelta
from app.adapters.persistence import GameORM, SQLAlchemyDrillRepository
from app.domain.entities import Drill, Mistake
from tests.conftest import (
    game_entity_list,
    game_orm,
    game_entity,
    FakeSQLAlchemyGameRepository,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import StaticPool, create_engine
from app.database import Base, Base

game_entity_list_mock = game_entity_list
game_orm_mock = game_orm
game_entity_mock = game_entity

# Test GameORM and GameEntity conversion methods
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


# Test DrillORM and repository methods,
def drill_due_yesterday():
    """Provide a sample Drill for testing."""
    mistake = Mistake(
        move_number=1,
        player="white",
        fen_before="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
        eval_before=20,
        eval_before_type="cp",
        eval_after=15,
        eval_after_type="cp",
        move_played="e5",
    )
    return Drill(
        mistake=mistake,
        fen_before="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        correct_move="e4",
        target_evaluation=30,
        repetition_count=0,
        ease_factor=2.5,
        interval=1,
        next_review_date=date.today() - timedelta(days=1),  # Due yesterday
        last_reviewed_at=None,
    )

def drill_due_tomorrow():
    """Provide a sample Drill for testing."""
    mistake = Mistake(
        move_number=2,
        player="black",
        fen_before="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
        fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 1 2",
        eval_before=10,
        eval_before_type="cp",
        eval_after=5,
        eval_after_type="cp",
        move_played="Nf6",
    )
    return Drill(
        mistake=mistake,
        fen_before="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
        correct_move="Nc6",
        target_evaluation=20,
        repetition_count=0,
        ease_factor=2.5,
        interval=1,
        next_review_date=date.today() + timedelta(days=1),  # Due tomorrow
        last_reviewed_at=None,
    )

def test_drill_repository_methods():
    # Create a fake repository
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    repo = SQLAlchemyDrillRepository(session)
    # real repo, real session
    repo.add_drill(drill_due_yesterday())  
    repo.add_drill(drill_due_tomorrow())    
    due = repo.get_due_drills(date.today())      
    assert len(due) == 1                 
    assert due[0].mistake.move_number == 1



def test_drill_repository_update_drill():
    # Create a fake repository
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    repo = SQLAlchemyDrillRepository(session)
    # Add a drill
    drill = drill_due_yesterday()
    saved = repo.add_drill(drill)          # saved.id is now set
    saved.repetition_count += 1
    saved.next_review_date = date.today() + timedelta(days=1)
    repo.update_drill(saved)               # now update has a real id to match on
    # Fetch the updated drill and verify changes
    updated_drill = repo.get_due_drills(date.today() + timedelta(days=1))[0]
    assert updated_drill.repetition_count == 1
    assert updated_drill.next_review_date == date.today() + timedelta(days=1)

    # assertion that update_drill didn't accidentally create a second row
    assert len(repo.get_due_drills(date.today() + timedelta(days=1))) == 1