from tests.conftest import generate_mistakes
from app.use_cases.coaching_use_case import detect_mistakes
from app.domain.entities import EvaluationEntity, Explanation

mistakes = generate_mistakes

class FakeCoachingPort:
    def explain(self, _, mistakes) -> list[Explanation]:
        explanations:list[Explanation] = []
        for mistake in mistakes:
            explanation = Explanation(
                mistake=mistake,
                text=f"Explanation for mistake at move {mistake.move_number} by {mistake.player}.",
                best_move="e2e4"  # Mock best move
            )
            explanations.append(explanation)
        return explanations
    

def test_fake_coaching_port(mistakes):
    coaching_port = FakeCoachingPort()
    explanations = coaching_port.explain(None, mistakes)

    assert isinstance(explanations, list)
    assert len(explanations) == len(mistakes)
    print(f"Explanations: {explanations}")
    for explanation in explanations:
        assert isinstance(explanation, Explanation)
        assert explanation.mistake is not None
        assert explanation.text is not None
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
