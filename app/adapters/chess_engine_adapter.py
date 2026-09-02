"""
Chess engine adapter.

Adapt Stockfish to ChessEnginePort interface.
"""
import io
import threading
from app.domain.entities import EvaluationEntity, GameEntity
import stockfish
from chess import pgn


class StockfishEngineAdapter:
    def __init__(self, path: str):
        self._path = path
        self._engine: stockfish.Stockfish | None = None
        self._lock = threading.Lock()

    def start(self):
        try:
            self._engine = stockfish.Stockfish(path=self._path)
            self._engine.update_engine_parameters({"Threads": 2, "Minimum Thinking Time": 30})
        except Exception as e:
            raise RuntimeError(f"Failed to start Stockfish engine: {e}")
    
    def stop(self):
        """
        Clean up Stockfish engine subprocess.
        
        __del__'s poll()-loop blocks until the process actually exits,
        so stop() returns only once termination is confirmed
        
        """
        if self._engine:
            self._engine = None

    def analyze(self, game: GameEntity) -> list[EvaluationEntity]:
        if self._engine is None:
            raise RuntimeError("Stockfish engine is not started")
        chess_game = pgn.read_game(io.StringIO(game.pgn))
        if chess_game is None:
            raise ValueError("Invalid PGN")

        board = chess_game.board()
        evaluations: list[EvaluationEntity] = []
        for i, move in enumerate(chess_game.mainline_moves()):
            board.push(move)
            send_new_game = i == 0
            with self._lock:
                self._engine.set_fen_position(board.fen(), send_ucinewgame_token=send_new_game)
                evaluation = self._engine.get_evaluation()
            
            # Create entity directly
            evaluations.append(
                EvaluationEntity(
                    fen=board.fen(),
                    type=evaluation["type"],
                    value=evaluation["value"],
                    move_played=move.uci(),  # Store the move played in UCI format
                )
            )
        return evaluations
    
    def get_best_move(self, fen: str) -> str:
        if self._engine is None:
            raise RuntimeError("Stockfish engine is not started")
        with self._lock:
            self._engine.set_fen_position(fen)
            best_move = self._engine.get_best_move()
        return best_move
