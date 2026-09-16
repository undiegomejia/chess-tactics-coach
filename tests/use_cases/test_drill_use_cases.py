from datetime import date
from types import SimpleNamespace
from app.domain.entities import Drill, EvaluationEntity, Mistake
from app.use_cases.drill_use_cases import apply_sm2, eval_distance_to_quality, grade_attempt
import chess
import pytest
from tests.conftest import FakeDrillRepositoryPort, FakeGradingEngine


def test_eval_distance_to_quality():

    ev1 = eval_distance_to_quality(student_eval_cp=250, target_eval_cp=0, side_to_move="white")
    assert ev1 == 5

    ev2 = eval_distance_to_quality(student_eval_cp=-155, target_eval_cp=33, side_to_move="black")
    assert ev2 == 5

    ev3 = eval_distance_to_quality(student_eval_cp=-155, target_eval_cp=33, side_to_move="white")
    assert ev3 == 1

    ev4 = eval_distance_to_quality(student_eval_cp=-44, target_eval_cp=0, side_to_move="black")
    assert ev4 == 5

    ev5 = eval_distance_to_quality(student_eval_cp=-300, target_eval_cp=0, side_to_move="white")
    assert ev5 == 0

    ev6 = eval_distance_to_quality(student_eval_cp=40, target_eval_cp=0, side_to_move="white")
    assert ev6 == 5

    ev7 = eval_distance_to_quality(student_eval_cp=70, target_eval_cp=0, side_to_move="black")
    assert ev7 == 3

def test_apply_sm2():
    # Test case 1: quality < 3
    repetition_count, ease_factor, interval = apply_sm2(quality=2, repetition_count=0, ease_factor=2.5, interval=5)
    assert repetition_count == 0
    assert ease_factor == 2.18
    assert interval == 1

    # Test case 2: quality >= 3, repetition_count = 0
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=1, ease_factor=2.5, interval=5)
    assert repetition_count == 2
    assert ease_factor == 2.5
    assert interval == 6

    # Test case 3: quality >= 3, repetition_count = 1
    repetition_count, ease_factor, interval = apply_sm2(quality=5, repetition_count=1, ease_factor=2.5, interval=6)
    assert repetition_count == 2
    assert ease_factor == 2.6
    assert interval == 6

    # Test case 4: quality >= 3, repetition_count > 1
    repetition_count, ease_factor, interval = apply_sm2(quality=5, repetition_count=2, ease_factor=2.5, interval=6)
    assert repetition_count == 3
    assert ease_factor == 2.6
    assert interval == 16  # interval = round(6 * 2.5)

    # test case 5: quality = 3, repetition_count = 1 round down ease factor
    repetition_count, ease_factor, interval = apply_sm2(quality=3, repetition_count=1, ease_factor=2.5, interval=6)
    assert repetition_count == 2
    assert ease_factor == 2.36
    assert interval == 6

    # test exact 1.3 EF floor actually clamping
    repetition_count, ease_factor, interval = apply_sm2(quality=0, repetition_count=0, ease_factor=1.3, interval=5)
    assert repetition_count == 0
    assert ease_factor == 1.3
    assert interval == 1

    # Add this four-review chain as a test, asserting the final (4, 2.5, 39)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=0, ease_factor=2.5, interval=1)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=repetition_count, ease_factor=ease_factor, interval=interval)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=repetition_count, ease_factor=ease_factor, interval=interval)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=repetition_count, ease_factor=ease_factor, interval=interval)
    assert repetition_count == 4
    assert ease_factor == 2.5
    assert interval == 38  # interval = round(15 * 2.5) = 38

# Test the grade_attempt function with a good move and a bad move
def test_grade_attempt_good_vs_bad_move():
    fen_before = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # start position
    correct_move = "e2e4"
    bad_move = "a2a3"
    # Good move
    good_board = chess.Board(fen_before)
    good_board.push_uci(correct_move)  # play the correct move
    good_fen = good_board.fen()

    bad_board = chess.Board(fen_before)
    bad_board.push_uci(bad_move)  # play the bad move
    bad_fen = bad_board.fen()

    evals = {
        good_fen: EvaluationEntity(fen=good_fen, value=30, move_played=correct_move, type ="cp"),
        bad_fen: EvaluationEntity(fen=bad_fen, value=-300, move_played=bad_move, type ="cp"),
    }
    engine = FakeGradingEngine(evals_by_fen=evals, best_move=correct_move)
    repo = FakeDrillRepositoryPort()
    mistake = Mistake(move_number=1, player="white", fen_before=fen_before, fen_after=good_fen, eval_before=0, eval_before_type="cp", eval_after=30, eval_after_type="cp", move_played=correct_move)
    drill = Drill(mistake=mistake, fen_before=fen_before, correct_move=correct_move, target_evaluation=30)
    saved = repo.add_drill(drill)

    good = grade_attempt(saved.id, correct_move, engine, repo)
    assert good.repetition_count == 1  # advanceds

    bad = grade_attempt(saved.id, bad_move, engine, repo)
    assert bad.repetition_count == 0  # reset — the proof grading discriminated

# Test the grade_attempt function with an illegal move
def test_grade_attempt_with_illegal_move():
    fen_before = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # start position
    repo = FakeDrillRepositoryPort()
    correct_move = "e2e4"
    board = chess.Board(fen_before)
    board.push_uci(correct_move)

    fen = board.fen()
    mistake = Mistake(move_number=1, player="white", fen_before=fen_before, fen_after=fen, eval_before=0, eval_before_type="cp", eval_after=30, eval_after_type="cp", move_played=correct_move)
    drill = Drill(id=1, mistake=mistake, fen_before=fen_before, correct_move=correct_move, target_evaluation=30)

    repo.add_drill(drill)
    engine = FakeGradingEngine(evals_by_fen={}, best_move=correct_move)
    try:
        grade_attempt(drill_id=1, submitted_move="a2a5", engine=engine, repo=repo)  # illegal move
        assert pytest.raises(ValueError, match="Invalid move submitted")
    except ValueError as e:
        assert "Invalid move submitted" in str(e)
        
 # Test the grade_attempt function with a missing drill_id
def test_grade_attempt_with_invalid_id():
    # returns None for a missing drill_id
    repo = FakeDrillRepositoryPort()
    engine = FakeGradingEngine(evals_by_fen={}, best_move="e2e4")
    result = grade_attempt(999, "e2e4", engine, repo)  # drill_id 999 does not exist
    assert result is None

# Test the create_drill function to ensure it saves the drill correctly
def test_create_drill_happy_path():
    fen_before = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # start position
    correct_move = "e2e4"
    board = chess.Board(fen_before)
    board.push_uci(correct_move)
    repo = FakeDrillRepositoryPort()
    mistake = Mistake(move_number=1, player="white", fen_before=fen_before, fen_after=board.fen(), eval_before=0, eval_before_type="cp", eval_after=30, eval_after_type="cp", move_played=correct_move)
    drill = Drill(mistake=mistake, fen_before=fen_before, correct_move=correct_move, target_evaluation=30)
    saved = repo.add_drill(drill)
    assert saved.correct_move == correct_move
    assert saved.target_evaluation == 30 

# Test create_drill with invalid move from engine
def test_create_drill_with_invalid_move_from_engine():
    fen_before = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # start position
    invalid_move = "e9e5"  # Invalid move
    board = chess.Board(fen_before)
    repo = FakeDrillRepositoryPort()
    mistake = Mistake(move_number=1, player="white", fen_before=fen_before, fen_after=board.fen(), eval_before=0, eval_before_type="cp", eval_after=30, eval_after_type="cp", move_played=invalid_move)
    drill = Drill(mistake=mistake, fen_before=fen_before, correct_move=invalid_move, target_evaluation=30)
    try:
        repo.add_drill(drill)
        assert pytest.raises(ValueError, match="Invalid move from engine")
    except ValueError as e:
        assert "Invalid move from engine" in str(e)