from tests.conftest import generate_mistakes
from app.use_cases.coaching_use_case import detect_mistakes
from app.domain.entities import EvaluationEntity, Explanation, Mistake
from tests.conftest import FakeCoachingPort

mistakes = generate_mistakes

def test_fake_coaching_port(mistakes):
    coaching_port = FakeCoachingPort()
    explanations = coaching_port.explain(None, mistakes)

    assert isinstance(explanations, list)
    assert len(explanations) == len(mistakes)
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

def test_detect_mistakes():
    evaluations = [
        EvaluationEntity(fen="fen1", type="cp", value=50, move_played="e4"),
        EvaluationEntity(fen="fen2", type="cp", value=-100, move_played="e5"),  # Mistake here
        EvaluationEntity(fen="fen3", type="cp", value=30, move_played="Nf3"),
        EvaluationEntity(fen="fen4", type="cp", value=-200, move_played="Bc4"),  # Mistake here
    ]

    mistakes = detect_mistakes(evaluations, threshold=100)

    assert len(mistakes) == 3
    assert mistakes[0].move_number == 1
    assert mistakes[1].move_number == 2
    assert mistakes[2].move_number == 2

def test_detect_mistakes_with_mate():
    evaluations = [
        EvaluationEntity(fen="fen1", type="cp", value=50, move_played="e4"),
        EvaluationEntity(fen="fen2", type="cp", value=-1, move_played="e5"), 
        EvaluationEntity(fen="fen3", type="cp", value=30, move_played="Nf3"),
        EvaluationEntity(fen="fen4", type="mate", value=1, move_played="Bc4"),  
    ]

    mistakes = detect_mistakes(evaluations, threshold=100)

    assert len(mistakes) == 1
    assert mistakes[0].move_number == 2
