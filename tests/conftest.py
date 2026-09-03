"""
pytest fixtures and configuration.

Provides test client with in-memory database and mock Stockfish engine.
Automatically discovered by pytest before running tests.
"""

import sys
from pathlib import Path
from app.domain.entities import EvaluationEntity
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.database import Base, get_db


@pytest.fixture
def sample_pgn():
    """Provide sample PGN for testing game creation and retrieval."""
    return {"pgn": """[Event "Sample"]
[White "Magnus Carlsen"]
[Black "Hikaru Nakamura"]
[Result "1/2-1/2"]

1. e4 e5 1/2-1/2"""}


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

class FakeClaudeCoachAdapter:
    def explain(self, _, mistakes):
        """Return a fixed explanation for testing."""
        explanations = []
        for mistake in mistakes:
            explanations.append(
                {
                    "mistake": mistake,
                    "text": f"Mock explanation for move {mistake.move_number} by {mistake.player}.",
                    "best_move": "e2e4"  # Mock best move
                }
            )
        return explanations


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
