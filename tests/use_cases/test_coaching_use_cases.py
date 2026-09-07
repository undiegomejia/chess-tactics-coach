from tests.conftest import generate_mistakes
from app.use_cases.coaching_use_case import detect_mistakes
from app.domain.entities import EvaluationEntity, Explanation
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
        assert explanation.mistake_category is not None
        assert explanation.concise_explanation is not None
        assert explanation.concrete_variation is not None
        assert explanation.best_alternatives is not None
        for alt in explanation.best_alternatives:
            assert alt.move_san is not None
            assert alt.move_uci is not None
            assert alt.short_line is not None
            assert alt.eval_after_line is not None
            assert alt.rationale is not None
        assert explanation.tactical_motifs is not None
        assert explanation.strategic_factors is not None
        assert explanation.recommended_plan is not None
        assert explanation.confidence is not None
        assert explanation.best_move is not None

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
