"""
FastAPI application main entry point.

Provides REST API for chess game storage and analysis.
Routes handle game CRUD operations and Stockfish-powered position analysis.
"""

from app.adapters.chess_engine_adapter import StockfishEngineAdapter
from app.adapters.persistence import SQLAlchemyGameRepository
from fastapi import Depends, FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.database import get_db
from app.use_cases import game_use_cases
from app.database import engine, Base
from app.schemas import EvaluationModelResponse, GameCreated, GetGame, PostGame
from app.config import settings

stockfish_adapter = StockfishEngineAdapter(settings.stockfish_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: initialize DB and Stockfish on startup, cleanup on shutdown."""
    Base.metadata.create_all(engine)
    stockfish_adapter.start()
    app.state.chess_engine = stockfish_adapter
    yield
    stockfish_adapter.stop()

app = FastAPI(lifespan=lifespan,title="Chess Tactics Coach", version="0.1.0")

@app.post("/games", status_code=201)
def post_game(payload: PostGame, db = Depends(get_db))  -> GameCreated:
    repo = SQLAlchemyGameRepository(db)
    try:
        new_game = game_use_cases.create_game(payload.pgn, repo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    valid_game = GameCreated.model_validate(new_game)
    return valid_game

@app.get("/games/{game_id}", status_code=200)
def get_game(game_id: int, db = Depends(get_db)) -> GetGame:
    """Retrieve a specific game by ID (summary only, no full PGN)."""
    repo = SQLAlchemyGameRepository(db)
    game_by_id = game_use_cases.fetch_game(game_id, repo)
    if not game_by_id:
        raise HTTPException(status_code=404, detail="Game not found")

    valid_game = GetGame.model_validate(game_by_id)
    return valid_game

@app.get("/games", status_code=200)
def get_games(db = Depends(get_db)) -> list[GetGame]:
    """List all games (summary only, excludes full PGN)."""
    repo = SQLAlchemyGameRepository(db)
    games = game_use_cases.list_games(repo)
    valid_game = [GetGame.model_validate(game) for game in games]
    return valid_game

@app.get("/games/{game_id}/analysis", status_code=200)
def get_analysis(game_id: int, db = Depends(get_db)) -> list[EvaluationModelResponse]:
    """
    Analyze a game using Stockfish.
    
    Returns evaluation for each position in the game.
    """
    repo = SQLAlchemyGameRepository(db)
    stockfish_engine = app.state.chess_engine
    try:
        evaluations = game_use_cases.analyze_game(game_id, repo, stockfish_engine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [EvaluationModelResponse(fen=position.fen, type=position.type, value=position.value) for position in evaluations]

@app.get("/health")
def health_check() -> dict:
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "ok"}
