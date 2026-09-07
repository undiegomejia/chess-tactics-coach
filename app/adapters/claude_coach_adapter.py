from anthropic import Anthropic
from app.domain.ports import ChessEnginePort
from app.config import settings
from app.domain.entities import Explanation
from pydantic import BaseModel

class AlternativeMove(BaseModel):
    move_san: str
    move_uci: str | None
    short_line: str
    eval_after_line: str  # numeric or "mate+N" per your own prompt's rules
    rationale: str

class ClaudeExplanationPayload(BaseModel):
    mistake_category: str
    concise_explanation: str
    concrete_variation: str
    best_alternatives: list[AlternativeMove]
    tactical_motifs: list[str]
    strategic_factors: list[str]
    recommended_plan: str
    confidence: float


class ClaudeCoachAdapter:
    def __init__(self, api_key: str, engine: ChessEnginePort, client: Anthropic | None = None):
        self._client: Anthropic | None = client or Anthropic(api_key=api_key)
        self.api_key = api_key
        self._engine = engine

    def explain(self, game, mistakes) -> list[Explanation]:
        explanations = []
        tools = [
            {
                "name": "get_best_move",
                "description": "Get the best move for a given chess position in FEN format.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fen": {
                            "type": "string",
                            "description": "FEN string representing the chess position",
                        }
                    },
                    "required": ["fen"],
                },
            }
        ]
        for mistake in mistakes:
            prompt = generate_prompt(game, mistake)
            history = [{"role": "user", "content": prompt}]
            response = self._client.messages.parse(
                model=settings.claude_model,
                messages=history,
                max_tokens=1024,
                tools=tools,
                output_format=ClaudeExplanationPayload
            )
            if response.stop_reason == "tool_use":
                tool_use = next(
                    block for block in response.content if block.type == "tool_use"
                )
                fen = tool_use.input["fen"]
                best_move = self._engine.get_best_move(fen)

                history = history + [
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": best_move,
                            }
                        ],
                    },
                ]
                response = self._client.messages.parse(
                    model=settings.claude_model,
                    max_tokens=1024,
                    tools=tools,
                    messages=history,
                    output_format=ClaudeExplanationPayload
                )
            else:
                best_move = None
            payload = response.parsed_output
            explanations.append(
                Explanation(
                    mistake=mistake, 
                    mistake_category=payload.mistake_category, 
                    concise_explanation=payload.concise_explanation,
                    concrete_variation=payload.concrete_variation,
                    best_alternatives=payload.best_alternatives,
                    tactical_motifs=payload.tactical_motifs,
                    strategic_factors=payload.strategic_factors,
                    recommended_plan=payload.recommended_plan,
                    confidence=payload.confidence,
                    best_move=best_move
                )
            )
        return explanations


def generate_prompt(game, mistake) -> str:

    # ← fill in: move_number, player, fen_before, fen_after, eval_before, eval_after, move_played
    prompt = f"""
        Explain the mistake in this chess game and return a single JSON object only.

        Context
        Game metadata:
        - pgn: {game.pgn}
        - white: {game.white}
        - black: {game.black}
        - result: {game.result}

        Mistake record
        - move_number: {mistake.move_number}
        - player: "This mistake was made by {mistake.player} ({game.white if mistake.player == 'white' else game.black})"
        - move_played: {mistake.move_played}
        - fen_before: {mistake.fen_before}
        - fen_after: {mistake.fen_after}
        - eval_before: {mistake.eval_before}
        - eval_before_type: {mistake.eval_before_type}
        - eval_after: {mistake.eval_after}
        - eval_after_type: {mistake.eval_after_type}

        Instructions for the model
        1. **Output format**: Return **only** a single JSON object (no surrounding text). The JSON keys must be exactly:
        - move_number
        - player
        - move_played
        - fen_before
        - fen_after
        - eval_before
        - eval_after
        - eval_delta
        - eval_units
        - eval_type_before
        - eval_type_after
        - mistake_category
        - concise_explanation
        - concrete_variation
        - best_alternatives
        - tactical_motifs
        - strategic_factors
        - recommended_plan
        - confidence

        2. **Definitions and units**
        - **eval_before** and **eval_after** must be numeric. Use centipawns for numeric evaluations; if the engine reports mate, convert to a string like "mate+3" or "mate-2".
        - **eval_units** must be "centipawns" or "mate".
        - **eval_delta** = eval_after - eval_before (numeric when centipawns; if mate values are present, set eval_delta to null and explain in concise_explanation).
        - **mistake_category** must be one of: "blunder", "mistake", "inaccuracy", "book", "unknown". Choose the smallest category consistent with the evaluation change and tactical context.

        3. **Content requirements**
        - **concise_explanation**: 1-3 sentences that state why the move is a mistake, referencing concrete tactical or strategic reasons visible in the FENs.
        - **concrete_variation**: Provide a short principal variation (SAN moves) showing the best immediate line after a better move, with the engine evaluation after that line.
        - **best_alternatives**: An array of up to 3 alternatives. Each alternative must include: move_san, move_uci (if available), short_line (SAN), eval_after_line (numeric or mate string), and a one-sentence rationale.
        - **tactical_motifs**: List up to 3 tactical motifs present (e.g., fork, pin, discovered attack, back-rank).
        - **strategic_factors**: List up to 3 strategic factors (e.g., king safety, pawn structure, piece activity, weak squares).
        - **recommended_plan**: 2-4 short actionable sentences describing how the player should proceed to improve in similar positions.
        - **confidence**: A number between 0.0 and 1.0 representing how confident the model is in the analysis.
        - **get_best_move**: Use the get_best_move tool to verify the engine's actual best move before making claims about what should have been played

        4. **Safety and hallucination rules**
        - If any required field is missing or cannot be determined from the provided data, set that field to **null** and do not invent values.
        - Do not assert engine names, depths, or move times unless provided. If engine provenance is unknown, omit it.
        - Keep speculative language out of the JSON. Use the `concise_explanation` field for any brief interpretation.

        5. **Brevity and clarity**
        - Keep each string value concise. Avoid long essays inside JSON fields.
        - Do not include markdown, code fences, or extra commentary outside the JSON object.

        Example JSON structure expected
        
        {expected_json_example()}

        End of prompt.
        """
    return prompt

def expected_json_example() -> str:
    return """
        [
        {
    "mistake": {
      "move_number": 3,
      "player": "black",
      "fen_before": "r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3",
      "fen_after": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
      "eval_before": -25,
      "eval_before_type": "cp",
      "eval_after": 1,
      "eval_after_type": "mate",
      "move_played": "g8f6"
    },
    "full_explanation": {
        "mistake_category": "blunder",
        "concise_explanation": "Black's move g8f6 allows White to deliver a checkmate in one move with Qxf7#.",
        "concrete_variation": "3... g8f6 4. Qxf7# (mate)",
        "best_alternatives": [
            {
            "move_uci": "d7d6",
            "short_line": "3... d7d6 4. Qxf7# (mate)",
            "eval_after_line": -50,
            "rationale": "Develops the bishop and prevents immediate mate."
            },
            {
            "move_uci": "e5e4",
            "short_line": "3... e5e4 4. Qxf7# (mate)",
            "eval_after_line": -30,
            "rationale": "Gains space and opens lines for development."
            }
        ],
        "tactical_motifs": ["back-rank mate", "pin"],
        "strategic_factors": ["king safety", "piece activity"],
        "recommended_plan": "Focus on king safety, avoid weakening pawn moves, and prioritize piece development.",
        "confidence": 0.95
    },
    "best_move": null
  }
  ]
    """