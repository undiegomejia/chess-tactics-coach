"""
FastAPI entrypoint.

`/health` is fully implemented below as a reference for the pattern:
route decorator -> function -> return value FastAPI serializes to JSON.
Use it as your template for the three TODO routes.

Deliberately rough for now: routes will call the database and the
chess engine directly, with no service/repository layer in between.
That's the point of this phase -- don't add abstractions preemptively.
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
    Base.metadata.create_all(engine)
    app.state.stockfish_engine = start_stockfish_engine()
    yield
    app.state.stockfish_engine = stop_stockfish_engine()


class PostGame(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pgn: str

class GetGame(BaseModel):
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
    game_by_id = db.query(Game).filter(Game.id == game_id).first()
    if not game_by_id:
        raise HTTPException(status_code=404, detail="Game not found")

    response = GetGame.model_validate(game_by_id)
    return response

@app.get("/games", status_code=200)
def list_games(db = Depends(get_db)) -> list[GetGame]:
    games = db.query(Game).all()
    response = [GetGame.model_validate(game) for game in games]
    return response

@app.get("/games/{game_id}/analysis", status_code=200)
def get_analysis(request: Request, game_id: int, db = Depends(get_db)) -> list[EvaluationModelResponse]:
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    stockfish_engine = request.app.state.stockfish_engine
    analysis = analyze_game(game.pgn, stockfish_engine)
    return analysis

@app.get("/health")
def health_check() -> dict:
    """Reference implementation. A real interviewer will ask 'why does
    a health check endpoint exist at all?' -- know the answer
    (load balancers / orchestrators poll this to know if your instance
    is alive) before you move on."""
    return {"status": "ok"}
                                


# ---------------------------------------------------------------------
# TODO 3: GET /games/{game_id}/analysis
#
# Look up the game, parse its PGN, run it through
# app.chess_engine.analyze_game(), return the evaluation.
#
# Handle the missing-game case explicitly (404, not a 500) -- this is
# the kind of thing that gets flagged in a code review and gets asked
# about in interviews ("what happens if the ID doesn't exist?").
#
# @app.get("/games/{game_id}/analysis")
# def get_analysis(...):
#     ...
