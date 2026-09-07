"""
pytest fixtures and configuration.

Provides test client with in-memory database and mock Stockfish engine.
Automatically discovered by pytest before running tests.
"""

import sys
from pathlib import Path
from app.adapters.persistence import GameORM
from app.domain.entities import EvaluationEntity, Explanation, GameEntity, Mistake
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.use_cases import game_use_cases

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fixtures:

@pytest.fixture
def sample_pgn():
    """Provide sample PGN for testing game creation and retrieval."""
    return {"pgn": """[Event "Sample"]
[White "Magnus Carlsen"]
[Black "Hikaru Nakamura"]
[Result "1/2-1/2"]

1. e4 e5 1/2-1/2"""}

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
def generate_mistakes():
    return [
        Mistake(
            move_number=1,
            player="white",
            fen_before="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            eval_before=20,
            eval_before_type="cp",
            eval_after=15,
            eval_after_type="cp",
            move_played="e5"
        ),
        Mistake(
            move_number=2,
            player="black",
            fen_before="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
            eval_before=15,
            eval_before_type="cp",
            eval_after=10,
            eval_after_type="cp",
            move_played="Nf6"
        )
    ]


@pytest.fixture
def mock_engine_adapter():
    """Provide mock Stockfish engine instance."""
    return FakeStockfishAdapter()


@pytest.fixture
def client(mock_engine_adapter):
    """
    Provide FastAPI test client with in-memory database.

    Uses SQLite in-memory database with StaticPool for test isolation.
    Overrides app dependencies to inject test database and mock engine.
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # KEY: ensures single shared connection
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as test_client:
        test_client.app.state.chess_engine = mock_engine_adapter
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
# 
def game_repo():
    return FakeGameRepository()

@pytest.fixture
def sample_pgn_string():
    """Provide sample PGN for testing game creation and retrieval."""
    return "[Event \"WECU Bristol\"]\n[Site \"Bristol\"]\n[Date \"1947.??.??\"]\n[Round \"3\"]\n[White \"?\"]\n[Black \"Bruce, Rowena M\"]\n[Result \"1/2-1/2\"]\n[WhiteElo \"\"]\n[BlackElo \"\"]\n[ECO \"E15\"]\n\n1.d4 Nf6 2.c4 e6 3.g3 c5 4.Nf3 b6 5.Bg2 Bb7 6.d5 exd5 7.Nh4 g6 8.O-O Bg7\n9.Nc3 O-O 10.Bf4 Qe7 11.Nb5 Ne8 12.Bxd5 Nc6 13.Qd2 Nd8 14.Rad1 a6 15.Nc3 d6\n16.b3 Rb8 17.Ng2 Ne6 18.Bh6 Nd4 19.Bxg7 Kxg7 20.Ne3 f5 21.Bxb7 Rxb7 22.Nc2 Nxc2\n23.Qxc2 Nf6 24.Nd5 Nxd5 25.Rxd5 Rf6 26.Rfd1 Rd7 27.e3 Re6 28.Qb2+ Qf6 29.Qa3 a5\n30.Qa4 Qe7 31.Qc6 Rxe3 32.fxe3 Qxe3+ 33.Kg2 Qe2+ 34.Kg1 Qe3+  1/2-1/2"

# Classes

# Mocking the coaching port 
class FakeCoachingPort:
    def explain(self, _, mistakes) -> list[Explanation]:
        explanations:list[Explanation] = []
        for mistake in mistakes:
            explanation = Explanation(
                mistake=mistake,
                text=f"Explanation for mistake at move {mistake.move_number} by {mistake.player}.",
                best_move="e2e4"  # Mock best move
            )
            explanations.append(explanation)
        return explanations

class FakeChessEnginePort:
    def get_best_move(self, fen: str) -> str:
        """Return a mock best move for the given FEN."""
        return "e2e4"  # Mock best move
    
class FakeAnthropicMessagesResponse:
    def __init__(self, stop_reason: str, content: list[dict]):
        self.stop_reason = stop_reason
        self.content = content

class FakeAnthropicContentBlock:
    def __init__(self, block_type: str, text: str = None, tool_use_id: str = None, input_data: dict = None):
        self.type = block_type
        self.text = text
        self.id = tool_use_id
        self.input = input_data
    
# Mocking the Anthropic API client.messages.create()
def messages_create_mock(**kwargs):
    messages = kwargs.get("messages", [])
    if any(m.get("role") == "assistant" for m in messages):
        return FakeAnthropicMessagesResponse(
            stop_reason="end_turn",
            content=[FakeAnthropicContentBlock(block_type="text", text="Mock explanation for the mistake.")]
        )
    return FakeAnthropicMessagesResponse(
        stop_reason="tool_use",
        content=[FakeAnthropicContentBlock(block_type="tool_use", tool_use_id="mock_tool_use_id", input_data={"fen": "..."})]
    )

# Mocking the Anthropic API client Messages class
class Messages:
    def __init__(self,):
        self.create = messages_create_mock
messages_mock = Messages()

# Mocking the Anthropic Client Wrapper class
class FakeAnthropicClient:
    """Mock wrapper for the Anthropic API client."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Create nested structure
        self.messages = messages_mock


class FakeStockfishAdapter:
    def analyze(self, _) -> list[EvaluationEntity]:
        """Return a fixed evaluation sequence for testing."""
        return [
            EvaluationEntity(
                fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                type="cp",
                value=20
            ),
            EvaluationEntity(
                fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                type="cp",
                value=15
            ),
            EvaluationEntity(
                fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
                type="cp",
                value=10
            ),
            EvaluationEntity(
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


class FakeSQLAlchemyGameRepository:
    def __init__(self, _):
        return

    def add_game(self, game_entity_mock: GameEntity) -> GameEntity:
        return game_entity_mock

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