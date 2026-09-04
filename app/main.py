"""
FastAPI application main entry point.

Provides REST API for chess game storage and analysis.
Routes handle game CRUD operations and Stockfish-powered position analysis.
"""

import anthropic
from app.adapters.chess_engine_adapter import StockfishEngineAdapter
from app.adapters.claude_coach_adapter import ClaudeCoachAdapter
from app.adapters.persistence import SQLAlchemyGameRepository
from app.domain.entities import Explanation
from fastapi import Depends, FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.database import get_db
from app.use_cases import coaching_use_case, game_use_cases
from app.database import engine, Base
from app.schemas import EvaluationModelResponse, ExplanationModelResponse, GameCreated, GetGame, PostGame
from app.config import settings

stockfish_adapter = StockfishEngineAdapter(settings.stockfish_path)
claude_adapter = ClaudeCoachAdapter(settings.anthropic_api_key.get_secret_value(), stockfish_adapter)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: initialize DB and Stockfish on startup, cleanup on shutdown."""
    Base.metadata.create_all(engine)
    # start stockfish engine
    stockfish_adapter.start()
    # store the adapters in the app state for access in route handlers
    app.state.chess_engine = stockfish_adapter
    # store the Claude coach adapter in the app state for access in route handlers
    app.state.coach_adapter = claude_adapter
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

@app.get("/games/{game_id}/coaching", status_code=200)
def get_coaching(game_id: int, db = Depends(get_db)) -> list[ExplanationModelResponse]:
    # Fetch the game, analyze it, detect mistakes, and get explanations for those mistakes
    repo = SQLAlchemyGameRepository(db)
    # Get the Stockfish engine and Claude coach adapter from the app state
    stockfish_engine = app.state.chess_engine
    # Get the Claude coach adapter from the app state
    coach_adapter = app.state.coach_adapter
    try:
        # Fetch the game and analyze it
        game_by_id = game_use_cases.fetch_game(game_id, repo)
        # Analyze the game to get evaluations
        game_analysis = game_use_cases.analyze_game(game_id, repo, stockfish_engine)
        # Detect mistakes based on the evaluations
        mistakes = coaching_use_case.detect_mistakes(game_analysis)
        # Get explanations for the detected mistakes
        explanations = coaching_use_case.explain_mistakes(game_by_id, mistakes, coach_adapter)
        return [ExplanationModelResponse(mistake=explanation.mistake, text=explanation.text, best_move=explanation.best_move) for explanation in explanations]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Coaching service error: {e.message}")

@app.get("/health")
def health_check() -> dict:
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "ok"}
