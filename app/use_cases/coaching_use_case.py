from app.domain.entities import Explanation, GameEntity, Mistake, EvaluationEntity
from app.adapters.claude_coach_adapter import ClaudeCoachAdapter
from app.domain.ports import ChessEnginePort, CoachingPort


def detect_mistakes(evaluations: list[EvaluationEntity], threshold=100) -> list[Mistake]:
    mistakes: list[Mistake] = []
    for i in range(1, len(evaluations)):
        eval_before = evaluations[i - 1]
        eval_after = evaluations[i]
        # normalize evaluation values to centipawns for comparison
        # Assuming a mistake is defined as a drop in evaluation of more than `threshold` centipawns
        if abs(_to_centipawns(eval_after) - _to_centipawns(eval_before)) > threshold:
            mistakes.append(
                Mistake(
                    move_number=(i // 2) + 1,
                    player="white" if i % 2 != 1 else "black",
                    fen_before=eval_before.fen,
                    fen_after=eval_after.fen,
                    eval_before=eval_before.value,
                    eval_before_type=eval_before.type,
                    eval_after=eval_after.value,
                    eval_after_type=eval_after.type,
                    move_played=eval_after.move_played
                )
            )
    return mistakes

def explain_mistakes(game: GameEntity, mistakes: list[Mistake], coach: CoachingPort) -> list[Explanation]:
    return coach.explain(game, mistakes)

def _to_centipawns(evaluation: EvaluationEntity) -> int:
    if evaluation.type == "mate":
        return 10000 if evaluation.value > 0 else -10000
    return evaluation.value