"""
FastAPI application main entry point.

Provides REST API for chess game storage and analysis.
Routes handle game CRUD operations and Stockfish-powered position analysis.
"""

from datetime import date
import anthropic
from app.adapters.chess_engine_adapter import StockfishEngineAdapter
from app.adapters.claude_coach_adapter import ClaudeCoachAdapter
from app.adapters.persistence import SQLAlchemyDrillRepository, SQLAlchemyGameRepository
from app.domain.entities import Mistake
from fastapi import Depends, FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.database import get_db
from app.use_cases import coaching_use_case, drill_use_cases, game_use_cases
from app.database import engine, Base
from app.schemas import AlternativeMoveResponse, CreatedDrill, DrillModelRequest, DrillModelRequest, EvaluationModelResponse, ExplanationModelResponse, GameCreated, GetGame, MistakeModelRequest, MistakeModelResponse, PostGame, SubmittedMove
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

@app.get("/health")
def health_check() -> dict:
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "ok"}

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
        if game_by_id is None:
            raise HTTPException(status_code=404, detail=f"Game with id {game_id} not found")
        game_analysis = game_use_cases.analyze_game(game_id, repo, stockfish_engine)
        # Detect mistakes based on the evaluations
        mistakes = coaching_use_case.detect_mistakes(game_analysis)
        # Get explanations for the detected mistakes
        explanations = coaching_use_case.explain_mistakes(game_by_id, mistakes, coach_adapter)
        return [ExplanationModelResponse(mistake=MistakeModelResponse(
                                            move_number=explanation.mistake.move_number,
                                            player=explanation.mistake.player,
                                            fen_before=explanation.mistake.fen_before,
                                            fen_after=explanation.mistake.fen_after,
                                            eval_before=explanation.mistake.eval_before,
                                            eval_before_type=explanation.mistake.eval_before_type,
                                            eval_after=explanation.mistake.eval_after,
                                            eval_after_type=explanation.mistake.eval_after_type,
                                            move_played=explanation.mistake.move_played
                                         ), 
                                         mistake_category=explanation.mistake_category,
                                         concise_explanation=explanation.concise_explanation,
                                         concrete_variation=explanation.concrete_variation,
                                         best_alternatives=map_alternative_list(explanation.best_alternatives),
                                         tactical_motifs=explanation.tactical_motifs,
                                         strategic_factors=explanation.strategic_factors,
                                         recommended_plan=explanation.recommended_plan,
                                         confidence=explanation.confidence,
                                         best_move=explanation.best_move) for explanation in explanations]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Coaching service error: {e.message}")
    
@app.post("/drills", status_code=201)
def post_drill(mistake_request: MistakeModelRequest, db = Depends(get_db)) -> CreatedDrill:
    repo = SQLAlchemyDrillRepository(db)
    engine = app.state.chess_engine
    try:
        new_drill = drill_use_cases.create_drill(map_mistake_request_to_entity(mistake_request), engine, repo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CreatedDrill.model_validate(new_drill)

@app.get("/drills/due", status_code=200)
def get_due_drills(db = Depends(get_db), as_of: date | None = None) -> list[CreatedDrill]:
    repo = SQLAlchemyDrillRepository(db)
    if as_of is not None:
        as_of_date = as_of
    else:
        as_of_date = date.today()
    due_drills = drill_use_cases.get_due_drills(as_of_date, repo)
    return [CreatedDrill.model_validate(drill) for drill in due_drills]

@app.post("/drills/{drill_id}/attempt", status_code=200)
def submit_attempt(drill_id: int, submitted_move: SubmittedMove, db = Depends(get_db)) -> CreatedDrill:
    repo = SQLAlchemyDrillRepository(db)
    engine = app.state.chess_engine
    try:
       graded = drill_use_cases.grade_attempt(drill_id, submitted_move.move, engine, repo)
    except ValueError as e:
       raise HTTPException(400, detail=str(e))
    if graded is None:
       raise HTTPException(404, detail=f"Drill {drill_id} not found")
    return CreatedDrill.model_validate(graded)

# Helpers
def map_mistake_request_to_entity(mistake_req: MistakeModelRequest) -> Mistake:
    """Convert MistakeModelRequest to Mistake entity."""
    return Mistake(
        move_number=mistake_req.move_number,
        player=mistake_req.player,
        fen_before=mistake_req.fen_before,
        fen_after=mistake_req.fen_after,
        eval_before=mistake_req.eval_before,
        eval_before_type=mistake_req.eval_before_type,
        eval_after=mistake_req.eval_after,
        eval_after_type=mistake_req.eval_after_type,
        move_played=mistake_req.move_played
    )

def map_alternative_list(alternatives: list) -> list[AlternativeMoveResponse]:
    """Map a list of alternative moves to the AlternativeMoveResponse schema."""
    return [AlternativeMoveResponse(move_san=alt.move_san, move_uci=alt.move_uci, short_line=alt.short_line, eval_after_line=alt.eval_after_line, rationale=alt.rationale) for alt in alternatives]

