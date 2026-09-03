from app.adapters.claude_coach_adapter import generate_prompt
import pytest
from tests.conftest import FakeClaudeCoachAdapter
from app.domain.entities import Explanation, Mistake
from tests.adapters.test_chess_engine_adapter import game_entity

test_game_entity = game_entity

@pytest.fixture
def generate_mistakes():
    return [
        Mistake(
            move_number=1,
            player="white",
            fen_before="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            eval_before=20,
            eval_before_type="cp",
            eval_after=15,
            eval_after_type="cp",
            move_played="e5"
        ),
        Mistake(
            move_number=2,
            player="black",
            fen_before="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            fen_after="rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
            eval_before=15,
            eval_before_type="cp",
            eval_after=10,
            eval_after_type="cp",
            move_played="Nf6"
        )
    ]

def test_generate_prompt(test_game_entity, generate_mistakes):
    """Test the _generate_prompt function."""
    for mistake in generate_mistakes:
        prompt = generate_prompt(test_game_entity, mistake)
        assert "Move number" in prompt
        assert "Player" in prompt
        assert "FEN before" in prompt
        assert "FEN after" in prompt
        assert "Evaluation before" in prompt
        assert "Evaluation after" in prompt
        assert "Move played" in prompt

def test_claude_coach_adapter(test_game_entity, generate_mistakes):
    adapter = FakeClaudeCoachAdapter()
    explanations = adapter.explain(test_game_entity, generate_mistakes)

    assert isinstance(explanations, list)
    assert len(explanations) == len(generate_mistakes)
    for explanation in explanations:
        assert explanation['mistake'] is not None or ""
        assert explanation['text'] is not None or ""
        assert explanation['best_move'] is not None or ""