from app.use_cases import game_use_cases
import pytest

class FakeChessEngineAdapter:
    """A fake chess engine adapter for testing purposes."""
    def analyze(self, _):
        """Return a fixed evaluation sequence for testing."""
        return [
            game_use_cases.EvaluationEntity(
                fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                type="cp",
                value=20
            ),
            game_use_cases.EvaluationEntity(
                fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                type="cp",
                value=15
            ),
            game_use_cases.EvaluationEntity(
                fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
                type="cp",
                value=10
            ),
            game_use_cases.EvaluationEntity(
                fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 1 2",
                type="cp",
                value=5
            ),
        ]

class FakeGameRepository:
    """A fake in-memory game repository for testing purposes."""
    def __init__(self):
        self.games = {}
        self.next_id = 1

    def add_game(self, game):
        game.id = self.next_id
        self.games[self.next_id] = game
        self.next_id += 1
        return game

    def get_games(self):
        return list(self.games.values())

    def get_game_by_id(self, game_id):
        return self.games.get(game_id)
    

@pytest.fixture
def repo():
    """Provide mock game repository instance."""
    return FakeGameRepository()

@pytest.fixture
def sample_pgn_string():
    """Provide sample PGN for testing game creation and retrieval."""
    return "[Event \"WECU Bristol\"]\n[Site \"Bristol\"]\n[Date \"1947.??.??\"]\n[Round \"3\"]\n[White \"?\"]\n[Black \"Bruce, Rowena M\"]\n[Result \"1/2-1/2\"]\n[WhiteElo \"\"]\n[BlackElo \"\"]\n[ECO \"E15\"]\n\n1.d4 Nf6 2.c4 e6 3.g3 c5 4.Nf3 b6 5.Bg2 Bb7 6.d5 exd5 7.Nh4 g6 8.O-O Bg7\n9.Nc3 O-O 10.Bf4 Qe7 11.Nb5 Ne8 12.Bxd5 Nc6 13.Qd2 Nd8 14.Rad1 a6 15.Nc3 d6\n16.b3 Rb8 17.Ng2 Ne6 18.Bh6 Nd4 19.Bxg7 Kxg7 20.Ne3 f5 21.Bxb7 Rxb7 22.Nc2 Nxc2\n23.Qxc2 Nf6 24.Nd5 Nxd5 25.Rxd5 Rf6 26.Rfd1 Rd7 27.e3 Re6 28.Qb2+ Qf6 29.Qa3 a5\n30.Qa4 Qe7 31.Qc6 Rxe3 32.fxe3 Qxe3+ 33.Kg2 Qe2+ 34.Kg1 Qe3+  1/2-1/2"

def test_create_game(sample_pgn_string, repo):
    """Test game creation and retrieval flow."""
    new_game = game_use_cases.create_game(sample_pgn_string, repo)
    assert new_game.white == "?"
    assert new_game.black == "Bruce, Rowena M"
    assert new_game.result == "1/2-1/2"

def test_fetch_game(sample_pgn_string, repo):
    """Test fetching a game by ID."""
    new_game = game_use_cases.create_game(sample_pgn_string, repo)
    fetched_game = game_use_cases.fetch_game(new_game.id, repo)
    assert fetched_game is not None
    assert fetched_game.id == new_game.id
    assert fetched_game.white == new_game.white
    assert fetched_game.black == new_game.black
    assert fetched_game.result == new_game.result

def test_list_games(sample_pgn_string, repo):
    """Test listing all games."""
    game1 = game_use_cases.create_game(sample_pgn_string, repo)
    game2 = game_use_cases.create_game(sample_pgn_string, repo)
    games = game_use_cases.list_games(repo)
    assert len(games) == 2
    assert any(game.id == game1.id for game in games)
    assert any(game.id == game2.id for game in games)

def test_analyze_game(sample_pgn_string, repo):
    """Test game analysis with a fake chess engine."""
    new_game = game_use_cases.create_game(sample_pgn_string, repo)
    fake_engine = FakeChessEngineAdapter()
    evaluations = game_use_cases.analyze_game(new_game.id, repo, fake_engine)
    assert len(evaluations) == 4
    assert evaluations[0].fen == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    assert evaluations[0].type == "cp"
    assert evaluations[0].value == 20