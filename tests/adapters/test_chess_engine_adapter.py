from app.adapters.chess_engine_adapter import StockfishEngineAdapter
from app.config import settings
from tests.conftest import game_entity

game_entity_mock = game_entity
stockfish_path = settings.stockfish_path

def test_stockfish_adapter(game_entity_mock):
    """Test the StockfishEngineAdapter's analyze method."""
    adapter = StockfishEngineAdapter(path=stockfish_path)
    adapter.start()
    evaluations = adapter.analyze(game_entity_mock)
    
    assert isinstance(evaluations, list)
    assert len(evaluations) == 2
    
    for position in evaluations:
        assert isinstance(position.fen, str)
        assert isinstance(position.type, str)
        assert isinstance(position.value, int)
    adapter.stop()

def test_stockfish_adapter_values(game_entity_mock):
    adapter = StockfishEngineAdapter(path=stockfish_path)
    adapter.start()
    evaluations = adapter.analyze(game_entity_mock)
    for position in evaluations:
        assert position.type in ("cp", "mate")
        if position.type == "cp":
            assert -200 < position.value < 200  # sane range for a quiet opening position
    adapter.stop()

def test_stockfish_adapter_fen(game_entity_mock):
    """Test that the StockfishEngineAdapter returns expected FEN strings."""
    adapter = StockfishEngineAdapter(path=stockfish_path)
    adapter.start()
    evaluations = adapter.analyze(game_entity_mock)

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