"""
pytest configuration file.

This file is automatically discovered by pytest and runs before any tests.
It configures the Python path so tests can import from the 'app' package.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.api.main import app
from app.database import Base, get_db

class FakeStockfishEngine:
    def __init__(self):
        self._current_fen = None
        self._evaluation_sequence = [
            {"type": "cp", "value": 30},
            {"type": "cp", "value": 32},
            {"type": "cp", "value": 21},
            {"type": "cp", "value": 15},
        ]
        self._call_count = 0

    def set_fen_position(self, fen: str, send_ucinewgame_token: bool = True):
        self._current_fen = fen

    def get_evaluation(self) -> dict:
        eval_resul = self._evaluation_sequence[self._call_count % len(self._evaluation_sequence)]
        self._call_count += 1
        return eval_resul
    

@pytest.fixture
def mock_engine():
    return FakeStockfishEngine()


@pytest.fixture
def client(mock_engine):
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # KEY: ensures single shared connection
    )
    
    Base.metadata.create_all(bind=test_engine)
    
    TestingSessionLocal = sessionmaker(
        bind=test_engine
    )
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as test_client:
        test_client.app.state.stockfish_engine = mock_engine
        yield test_client
    
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_pgn():
    return {
        "pgn": """[Event "Sample"]
[White "Magnus Carlsen"]
[Black "Hikaru Nakamura"]
[Result "1/2-1/2"]

1. e4 e5 1/2-1/2"""
    }
