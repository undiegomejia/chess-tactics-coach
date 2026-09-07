from app.use_cases import game_use_cases
from tests.conftest import FakeStockfishAdapter
    
def test_create_game(sample_pgn_string, game_repo):
    """Test game creation and retrieval flow."""
    new_game = game_use_cases.create_game(sample_pgn_string, game_repo)
    assert new_game.white == "?"
    assert new_game.black == "Bruce, Rowena M"
    assert new_game.result == "1/2-1/2"

def test_fetch_game(sample_pgn_string, game_repo):
    """Test fetching a game by ID."""
    new_game = game_use_cases.create_game(sample_pgn_string, game_repo)
    fetched_game = game_use_cases.fetch_game(new_game.id, game_repo)
    assert fetched_game is not None
    assert fetched_game.id == new_game.id
    assert fetched_game.white == new_game.white
    assert fetched_game.black == new_game.black
    assert fetched_game.result == new_game.result

def test_list_games(sample_pgn_string, game_repo):
    """Test listing all games."""
    game1 = game_use_cases.create_game(sample_pgn_string, game_repo)
    game2 = game_use_cases.create_game(sample_pgn_string, game_repo)
    games = game_use_cases.list_games(game_repo)
    assert len(games) == 2
    assert any(game.id == game1.id for game in games)
    assert any(game.id == game2.id for game in games)

def test_analyze_game(sample_pgn_string, game_repo):
    """Test game analysis with a fake chess engine."""
    new_game = game_use_cases.create_game(sample_pgn_string, game_repo)
    fake_engine = FakeStockfishAdapter()
    evaluations = game_use_cases.analyze_game(new_game.id, game_repo, fake_engine)
    assert len(evaluations) == 4
    assert evaluations[0].fen == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    assert evaluations[0].type == "cp"
    assert evaluations[0].value == 20