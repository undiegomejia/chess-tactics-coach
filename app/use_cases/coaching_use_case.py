from app.domain.entities import Explanation, GameEntity, Mistake, EvaluationEntity
from app.adapters.claude_coach_adapter import ClaudeCoachAdapter
from app.domain.ports import ChessEnginePort, CoachingPort


def detect_mistakes(evaluations: list[EvaluationEntity], threshold=100) -> list[Mistake]:
    mistakes: list[Mistake] = []
    for i in range(1, len(evaluations)):
        eval_before = evaluations[i - 1]
        eval_after = evaluations[i]
        # Assuming a mistake is defined as a drop in evaluation of more than `threshold` centipawns
        if abs(_to_centipawns(eval_after) - _to_centipawns(eval_before)) > threshold:
            mistakes.append(
                Mistake(
                    move_number=i,
                    player="white" if i % 2 == 1 else "black",
                    fen_before=eval_before.fen,
                    fen_after=eval_after.fen,
                    eval_before=eval_before.value,
                    eval_after=eval_after.value,
                    move_played=eval_after.move_played
                )
            )
    return mistakes

def explain_mistakes(game: GameEntity, mistakes: list[Mistake], coach: CoachingPort) -> list[Explanation]:
    return coach.explain(game, mistakes)

def _to_centipawns(eval: EvaluationEntity) -> int:
    if eval.type == "mate":
        return 10000 if eval.value > 0 else -10000
    return eval.value