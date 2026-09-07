
from app.adapters.claude_coach_adapter import generate_prompt
from app.adapters.claude_coach_adapter import ClaudeCoachAdapter
from app.domain.entities import Explanation
from tests.conftest import game_entity, FakeAnthropicClient, FakeChessEnginePort

test_game_entity = game_entity
anthropic_client = FakeAnthropicClient(api_key="TEST_your_api_key_here")
fake_engine = FakeChessEnginePort()

def test_generate_prompt(test_game_entity, generate_mistakes):
    """Test the _generate_prompt function."""
    for mistake in generate_mistakes:
        prompt = generate_prompt(test_game_entity, mistake)
        assert "Explain the mistake" in prompt
        assert "Context" in prompt
        assert "Game metadata" in prompt
        assert "Mistake record" in prompt
        assert "Instructions for the model" in prompt
        assert "fen_before" in prompt
        assert "fen_after" in prompt

def test_claude_coach_adapter(test_game_entity, generate_mistakes):
    adapter = ClaudeCoachAdapter(api_key="fake", engine=fake_engine, client=anthropic_client)
    explanations = adapter.explain(test_game_entity, generate_mistakes)

    assert isinstance(explanations, list)
    assert len(explanations) == len(generate_mistakes)
    for explanation in explanations:
        assert isinstance(explanation, Explanation)
        assert explanation.mistake is not None
        assert explanation.text is not None
        assert explanation.best_move is not None
