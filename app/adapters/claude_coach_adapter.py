from anthropic import Anthropic
from app.domain.entities import Explanation, GameEntity, Mistake
from app.domain.ports import ChessEnginePort


class ClaudeCoachAdapter:
    def __init__(self, api_key: str, engine: ChessEnginePort):
        self._client: Anthropic | None = Anthropic(api_key=api_key)
        self.api_key = api_key
        self._engine = engine


    def explain(self, game, mistakes) -> list[Explanation]:
        explanations = []
        tools = [{
            "name": "get_best_move",
            "description": "Get the best move for a given chess position in FEN format.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "fen": {"type": "string", "description": "FEN string representing the chess position"}
                },
                "required": ["fen"]
            },
        }]
        for mistake in mistakes:
            prompt = generate_prompt(self, game, mistake)
            history = [{"role": "user", "content": prompt}]
            response = self._client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=history,
                max_tokens=1024,
                tools=tools,
            )
            if response.stop_reason == "tool_use":
                tool_use = next(block for block in response.content if block.type == "tool_use")
                fen = tool_use.input["fen"]
                best_move = self._engine.get_best_move(fen)

                history = history + [
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": best_move}]}
                ]
                followup = self._client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                tools=tools,
                    messages=history
                )
                text = next(b.text for b in followup.content if b.type == "text")
            else:
                text = next(b.text for b in response.content if b.type == "text")
                best_move = None
            explanations.append(Explanation(mistake=mistake, text=text, best_move=best_move))
            print(f"Explanations: {explanations}")
        return explanations

def generate_prompt(game, mistake) -> str:
     # ← fill in: move_number, player, fen_before, fen_after, eval_before, eval_after, move_played
     prompt = f"""
        Explain the mistake made in this chess game.
        Move number: {mistake.move_number}
        Player: "This mistake was made by {mistake.player} ({game.white if mistake.player == 'white' else game.black})" 
        FEN before: {mistake.fen_before}
        FEN after: {mistake.fen_after}
        Evaluation before: {mistake.eval_before} ({mistake.eval_before_type})
        Evaluation after: {mistake.eval_after} ({mistake.eval_after_type})
        Move played: {mistake.move_played}
        """
     return prompt