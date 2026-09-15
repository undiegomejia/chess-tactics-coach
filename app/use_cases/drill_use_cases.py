from datetime import date, datetime, timedelta
from app.domain.entities import Drill, Mistake
from app.domain.ports import ChessEnginePort, DrillRepositoryPort
import chess


def eval_distance_to_quality(student_eval_cp: int, target_eval_cp: int, side_to_move: str) -> int:
    """
    Calculate the distance between the student's evaluation and the target evaluation.
    
    Args:
        student_eval_cp (int): The student's evaluation in centipawns.
        target_eval_cp (int): The target evaluation in centipawns.
        side_to_move (str): The side to move, either "white" or "black".
    
    Returns:
        int: The distance to quality_of_response. Positive if the student's evaluation is better than the target,
             negative if worse, and zero if equal.
    """
    # Adjust the sign of the evaluations based on the side to move
    quality_of_response = 0

    if side_to_move == "black":
        student_eval_cp = -student_eval_cp
        target_eval_cp = -target_eval_cp
    # Calculate the distance to quality
    min_distance = max(0, target_eval_cp - student_eval_cp) # Distance is positive if the student's evaluation is better than the target, negative if worse, and zero if equal.
    # shortfall_map with 0–5 quality with boundaries in centipawns ~10/50/100cp
    shortfall_map = {
        5: 10,
        4: 50,
        3: 100,
        2: 150,
        1: 200,
        0: 250,
    }
    for quality, boundary in shortfall_map.items():
       if min_distance <= boundary:
            quality_of_response = quality
            break
        
    return quality_of_response

def apply_sm2(quality: int, repetition_count: int, ease_factor: float, interval: int) -> tuple[int, float, int]:
    # returns the NEW (repetition_count, ease_factor, interval)
    ease_factor = round(max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)), 2)
    if quality < 3:
        repetition_count = 0
        interval = 1
    else:
        if repetition_count == 0:
            interval = 1
        elif repetition_count == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetition_count += 1
    # Apply the SM-2 algorithm to update the repetition count, ease factor, and interval based on the quality of the response.
    return repetition_count, ease_factor, interval

def create_drill(mistake: Mistake, engine: ChessEnginePort, repo: DrillRepositoryPort) -> Drill:
    correct_move = engine.get_best_move(mistake.fen_before)
    board = chess.Board(mistake.fen_before)
    try: 
        board.push_uci(correct_move)  # play the correct move
    except ValueError as e:
        raise ValueError(f"Invalid move from engine: {correct_move}. Error: {e}")
    target_evaluation = engine.evaluate_fen(board.fen()).to_centipawns()  # evaluate where it led
    drill = Drill(mistake=mistake, fen_before=mistake.fen_before, correct_move=correct_move, target_evaluation=target_evaluation)
    return repo.add_drill(drill)

def grade_attempt(drill_id: int, submitted_move: str, engine: ChessEnginePort, repo: DrillRepositoryPort) -> Drill | None:
    drill = repo.get_drill_by_id(drill_id)
    if drill is None:
        return None  # Drill not found
    # Evaluate the student's submitted move using the chess engine
    board = chess.Board(drill.fen_before)
    try:
        board.push_uci(submitted_move)  
       # play the student's actual move
    except ValueError as e:
        raise ValueError(f"Invalid move submitted: {submitted_move}. Error: {e}")
    
    submitted_eval = engine.evaluate_fen(board.fen()).to_centipawns()   # evaluate where it led

    # Get the target evaluation (the evaluation after the correct move)
    target_eval = drill.target_evaluation
    # Calculate the quality of the response based on the student's evaluation and the target evaluation
    quality = eval_distance_to_quality(submitted_eval, target_eval, drill.mistake.player)
    repetition_count, ease_factor, interval = apply_sm2(quality, drill.repetition_count, drill.ease_factor, drill.interval)
    # Update the drill with the new SM-2 state and next review date
    drill.repetition_count = repetition_count
    drill.ease_factor = ease_factor
    drill.interval = interval
    drill.next_review_date = date.today() + timedelta(days=interval)
    drill.last_reviewed_at = datetime.today()
    # Persist the updated drill
    updated_drill = repo.update_drill(drill)
    return updated_drill

def get_due_drills(as_of: date, repo: DrillRepositoryPort) -> list[Drill]:
    # Fetch drills that are due for review as of the given date
    return repo.get_due_drills(as_of)