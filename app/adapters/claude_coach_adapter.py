import os
from anthropic import Anthropic
from app.domain.entities import Explanation
from app.domain.ports import ChessEnginePort

class ClaudeCoachAdapter:
    def __init__(self, path: str, engine: ChessEnginePort):
        self._client: Anthropic | None = Anthropic(api_key=path)
        self.path = path
        self._engine = engine

    def _generate_prompt(self, game, mistake) -> str:
        # Generate a prompt for Claude based on the game and the mistake
        prompt = f"""
        Analyze the following chess game and explain the mistake made at move {mistake.move_number} by {mistake.player}.
        Game PGN: {game.pgn}
        Mistake FEN before: {mistake.fen_before}
        Mistake FEN after: {mistake.fen_after}
        Evaluation before: {mistake.eval_before}
        Evaluation after: {mistake.eval_after}
        Move played: {mistake.move_played}

        Please provide a detailed explanation of why this move was a mistake, what the best move would have been, and any strategic insights.
        """
        return prompt

    def explain(self, game, mistakes) -> list[Explanation]:
        explanations = []
        for mistake in mistakes:
            prompt = self._generate_prompt(game, mistake)
            response = self._client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
            )
            text = response.content[0].text if response.content else ""
            print(f"Claude response for move {mistake.move_number}: {text}")
            best_move = self._engine.get_best_move(mistake.fen_before) if self._engine else "unknown"
            print(f"Best move according to engine for move {mistake.move_number}: {best_move}")
            explanations.append(Explanation(
                mistake=mistake,
                text=text,
                best_move=best_move
            ))
        return explanations
