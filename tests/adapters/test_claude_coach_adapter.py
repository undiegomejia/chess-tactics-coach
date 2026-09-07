
from app.adapters.claude_coach_adapter import generate_prompt
from app.adapters.claude_coach_adapter import ClaudeCoachAdapter
from app.domain.entities import GameEntity, Explanation, Mistake
from tests.conftest import game_entity, FakeAnthropicClient, FakeChessEnginePort

test_game_entity = game_entity
anthropic_client = FakeAnthropicClient(api_key="TEST_your_api_key_here")
fake_engine = FakeChessEnginePort()

def test_test_game_entity_aliases(test_game_entity):
    """Test that the aliased name is correct."""
    assert test_game_entity == GameEntity(
        id=1,
        white="?",
        black="Bruce, Rowena M",
        result="1/2-1/2",
        pgn='[Event "?"]\n[Site "?"]\n[Date "2023.10.01"]\n[Round "?"]\n[White "?"]\n[Black "Bruce, Rowena M"]\n[Result "1/2-1/2"]\n\n1. e4 e5 1/2-1/2',
    )

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
        assert isinstance(explanation.mistake, Mistake)
        assert explanation.mistake_category == "Positional Mistake"
        assert explanation.concise_explanation == "White's move e4 allowed Black to gain control of the center with e5."
        assert explanation.concrete_variation == "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"
        assert explanation.best_alternatives is not None
        assert isinstance(explanation.best_alternatives, list)
        for alt in explanation.best_alternatives:
            assert alt.move_san == "d4"
            assert alt.move_uci == "d2d4"
            assert alt.short_line == "1. d4 d5 2. c4"
            assert alt.eval_after_line == "30"
            assert alt.rationale == "Opens up lines for the queen and bishop."
        assert explanation.tactical_motifs == ["Pin", "Fork"]
        assert explanation.strategic_factors == ["Control of the center", "Piece development"]
        assert explanation.recommended_plan == "Develop pieces and control the center."
        assert explanation.confidence == 0.95
        assert isinstance(explanation.confidence, float)
        assert explanation.best_move == "e2e4"
