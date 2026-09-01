from app.adapters.chess_engine_adapter import StockfishEngineAdapter
from app.config import settings
from app.domain.entities import GameEntity
import pytest

stockfish_path = settings.stockfish_path

@pytest.fixture
def game_entity():
    return GameEntity(
        id=1,
        white="?",
        black="Bruce, Rowena M",
        result="1/2-1/2",
        pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.01"]\n[Round "?"]\n[White "?"]\n[Black "Bruce, Rowena M"]\n[Result "1/2-1/2"]\n\n1. e4 e5 1/2-1/2',
    )

def test_stockfish_adapter(game_entity):
    """Test the StockfishEngineAdapter's analyze method."""
    adapter = StockfishEngineAdapter(path=stockfish_path)
    adapter.start()
    evaluations = adapter.analyze(game_entity)
    
    assert isinstance(evaluations, list)
    assert len(evaluations) == 2
    
    for position in evaluations:
        assert isinstance(position.fen, str)
        assert isinstance(position.type, str)
        assert isinstance(position.value, int)
    adapter.stop()

def test_stockfish_adapter_values(game_entity):
    adapter = StockfishEngineAdapter(path=stockfish_path)
    adapter.start()
    evaluations = adapter.analyze(game_entity)
    for position in evaluations:
        assert position.type in ("cp", "mate")
        if position.type == "cp":
            assert -200 < position.value < 200  # sane range for a quiet opening position
    adapter.stop()

def test_stockfish_adapter_fen(game_entity):
    """Test that the StockfishEngineAdapter returns expected FEN strings."""
    adapter = StockfishEngineAdapter(path=stockfish_path)
    adapter.start()
    evaluations = adapter.analyze(game_entity)

    expected_fens = [
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    ]
    
    assert len(evaluations) == len(expected_fens)
    for position, expected in zip(evaluations, expected_fens):
        assert position.fen == expected
    adapter.stop()

def test_stop_stockfish_engine():
    """Test that the Stockfish engine stops without errors."""
    adapter = StockfishEngineAdapter(path=stockfish_path)
    adapter.start()
    adapter.stop()
    assert adapter._engine is None