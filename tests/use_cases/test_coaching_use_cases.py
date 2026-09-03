from tests.adapters.test_claude_coach_adapter import generate_mistakes
from app.use_cases.coaching_use_case import detect_mistakes
from app.domain.entities import EvaluationEntity

mistakes = generate_mistakes

class FakeCoachingPort:
    def explain(self, game, mistakes):
        explanations = []
        for mistake in mistakes:
            explanation = {
                'mistake': mistake,
                'text': f"Explanation for mistake",
                'best_move': "Best move suggestion"
            }
            explanations.append(explanation)
        return explanations
    

def test_fake_coaching_port(mistakes):
    coaching_port = FakeCoachingPort()
    explanations = coaching_port.explain(None, mistakes)

    assert isinstance(explanations, list)
    assert len(explanations) == len(mistakes)
    for explanation in explanations:
        assert 'mistake' in explanation
        assert 'text' in explanation
        assert 'best_move' in explanation

def test_detect_mistakes():
    evaluations = [
        EvaluationEntity(fen="fen1", type="cp", value=50, move_played="e4"),
        EvaluationEntity(fen="fen2", type="cp", value=-100, move_played="e5"),  # Mistake here
        EvaluationEntity(fen="fen3", type="cp", value=30, move_played="Nf3"),
        EvaluationEntity(fen="fen4", type="cp", value=-200, move_played="Bc4"),  # Mistake here
    ]

    mistakes = detect_mistakes(evaluations, threshold=100)

    assert len(mistakes) == 2
    assert mistakes[0].move_number == 1
    assert mistakes[1].move_number == 2
