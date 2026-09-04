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

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def sample_pgn():
    """Provide sample PGN for testing game creation and retrieval."""
    return {"pgn": """[Event "Sample"]
[White "Magnus Carlsen"]
[Black "Hikaru Nakamura"]
[Result "1/2-1/2"]

1. e4 e5 1/2-1/2"""}

def create_mock(*args, **kwargs):
        """Mock the create method to return a fixed response."""
        if "get_best_move" in kwargs.get("tools", [{}])[0].get("name", ""):
            return {
                "stop_reason": "tool_use",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "mock_tool_use_id",
                        "input": {"fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"},
                    }
                ],
            }
        elif "assistant" in kwargs.get("messages", [{}])[1].get("role", ""):
            return {
                "stop_reason": "end_turn",
                "content": [
                    {
                        "type": "text",
                        "text": "Mock explanation for the mistake.",
                    }
                ],
            }

class Messages:
    def __init__(self,):
        self.create = create_mock

messages_mock = Messages()

class AnthropicMockWrapper:
    """Mock wrapper for the Anthropic API client."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Create nested structure
        self.messages = messages_mock

anthropic_mock_wrapper = AnthropicMockWrapper(api_key="TEST_your_api_key_here")

class FakeClaudeCoachAdapter:
    def __init__(self):
        """Initialize the fake adapter."""
        self._client = anthropic_mock_wrapper

    def explain(self, _, mistakes) -> list[Explanation]:
        tools_mock = [
            {
                "name": "get_best_move",
                "description": "Get the best move for a given chess position in FEN format.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "FEN string representing the chess position",
                        }
                    },
                    "required": ["fen"],
                },
            }
        ]
        """Return a fixed explanation for testing."""
        for mistake in mistakes:
            get_fen_call = self._client.messages.create(
                model="claude-2",
                messages=[
                    {"role": "user", "content": f"Get FEN for the mistake: {mistake}"}
                ],
                tools=tools_mock
            )
            assert get_fen_call["stop_reason"] == "tool_use"
            assert get_fen_call["content"][0]["input"]["fen"] == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
            follow_up_call = self._client.messages.create(
                model="claude-2",
                messages=[
                    {"role": "user", "content": f"Follow up on the mistake: {mistake}"},
                    {"role": "assistant", "content": get_fen_call["content"]}    
                ]
            )
            assert follow_up_call["stop_reason"] == "end_turn"
            assert follow_up_call["content"][0]["text"] == "Mock explanation for the mistake."
        return [
            Explanation(
                mistake=Mistake(move_number=1, 
                                player="white",
                                fen_before="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                                fen_after="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                                eval_before=0, 
                                eval_before_type="cp",
                                eval_after=20, 
                                eval_after_type="cp", 
                                move_played="e2e4"), 
                text="Mock explanation for move 1.",
                best_move="e2e4"
            ),
            Explanation(
                mistake=Mistake(move_number=2, 
                                player="black",
                                fen_before="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                                fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                                eval_before=20, 
                                eval_before_type="cp",
                                eval_after=15, 
                                eval_after_type="cp", 
                                move_played="e7e5"), 
                text="Mock explanation for move 2.",
                best_move="e7e5"
            ),
        ]
    
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
