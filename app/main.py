"""
FastAPI application main entry point.

Provides REST API for chess game storage and analysis.
Routes handle game CRUD operations and Stockfish-powered position analysis.
"""

from fastapi import Depends, FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from app.chess_engine import EvaluationModelResponse, start_stockfish_engine, stop_stockfish_engine, analyze_game
from app.database import get_db
from app.models import Game
import chess.pgn
import io
from pydantic import BaseModel
from app.database import engine, Base
from pydantic.config import ConfigDict
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: initialize DB and Stockfish on startup, cleanup on shutdown."""
    Base.metadata.create_all(engine)
    app.state.stockfish_engine = start_stockfish_engine()
    yield
    app.state.stockfish_engine = stop_stockfish_engine()


class PostGame(BaseModel):
    """Request model for creating a new game."""
    model_config = ConfigDict(from_attributes=True)
    pgn: str

class GetGame(BaseModel):
    """Response model for game summary (without full PGN)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    white: str
    black: str
    result: str
    created_at: datetime

class GameCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    white: str
    black: str
    result: str
    created_at: datetime
    pgn: str

app = FastAPI(lifespan=lifespan,title="Chess Tactics Coach", version="0.1.0")

@app.post("/games", status_code=201)
def create_game(payload: PostGame, db = Depends(get_db))  -> GameCreated:
    """
    Create a new game from PGN.
    
    Validates PGN format, extracts headers (White, Black, Result),
    stores game in database.
    """
    try:
        parsed_game = chess.pgn.read_game(io.StringIO(payload.pgn))
        if parsed_game is None:
            raise ValueError("Invalid PGN - unable to parse")
        if list(parsed_game.mainline_moves()) == []:
            raise ValueError("Invalid PGN - no moves found.")
        else:  
            pgn = payload.pgn
            white = parsed_game.headers["White"]
            black = parsed_game.headers["Black"]
            result = parsed_game.headers["Result"]
            new_game = Game(pgn=pgn, white=white, black=black, result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    response = GameCreated.model_validate(new_game)
    if not response:
        raise HTTPException(status_code=500, detail="Failed to create game")
    return response

@app.get("/games/{game_id}", status_code=200)
def get_game(game_id: int, db = Depends(get_db)) -> GetGame:
    """Retrieve a specific game by ID (summary only, no full PGN)."""
    game_by_id = db.query(Game).filter(Game.id == game_id).first()
    if not game_by_id:
        raise HTTPException(status_code=404, detail="Game not found")

    response = GetGame.model_validate(game_by_id)
    return response

@app.get("/games", status_code=200)
def list_games(db = Depends(get_db)) -> list[GetGame]:
    """List all games (summary only, excludes full PGN)."""
    games = db.query(Game).all()
    response = [GetGame.model_validate(game) for game in games]
    return response

@app.get("/games/{game_id}/analysis", status_code=200)
def get_analysis(request: Request, game_id: int, db = Depends(get_db)) -> list[EvaluationModelResponse]:
    """
    Analyze a game using Stockfish.
    
    Returns evaluation for each position in the game.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    stockfish_engine = request.app.state.stockfish_engine
    analysis = analyze_game(game.pgn, stockfish_engine)
    return analysis

@app.get("/health")
def health_check() -> dict:
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "ok"}
