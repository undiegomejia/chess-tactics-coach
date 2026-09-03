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
            response = self._client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=history,
                max_tokens=1024,
                tools=tools,
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
                followup = self._client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=1024,
                    tools=tools,
                    messages=history,
                )
                text = next(b.text for b in followup.content if b.type == "text")
            else:
                text = next(b.text for b in response.content if b.type == "text")
                best_move = None
            explanations.append(
                Explanation(mistake=mistake, text=text, best_move=best_move)
            )
            print(f"Explanations: {explanations}")
        return explanations


def generate_prompt(game, mistake) -> str:
    expected_json_example = {
        "move_number": "23",
        "player": "black",
        "move_played": "Qh4",
        "fen_before": "r1bq1rk1/ppp2ppp/2n2n2/3p4/3P4/2N1PN2/PPP2PPP/R1BQ1RK1 w - - 0 10",
        "fen_after": "r1bq1rk1/ppp2ppp/2n2n2/3p4/3P4/2N1PN2/PPP2PPP/R1BQ1RK1 b - - 0 10",
        "eval_before": "20",
        "eval_after": "-150",
        "eval_delta": "-170",
        "eval_units": "centipawns",
        "eval_type_before": "engine",
        "eval_type_after": "engine",
        "mistake_category": "blunder",
        "concise_explanation": "The move Qh4 allows a tactical sequence that wins material by exploiting an undefended back rank and a pinned piece.",
        "concrete_variation": "1. Qh4 2. Nxh4 g5 3. Nf3 ... eval +2.10",
        "best_alternatives": [
            {
                "move_san": "Re1",
                "move_uci": "e1e8",
                "short_line": "Re1 Re8 2. ...",
                "eval_after_line": "50",
                "rationale": "Improves rook activity and avoids the tactical motif.",
            }
        ],
        "tactical_motifs": ["pin", "back-rank"],
        "strategic_factors": ["king safety", "piece coordination"],
        "recommended_plan": "Prioritize king safety and avoid weakening pawn moves that create tactical targets. When in doubt, improve piece coordination before launching attacks.",
        "confidence": "0.92",
    }

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

        4. **Safety and hallucination rules**
        - If any required field is missing or cannot be determined from the provided data, set that field to **null** and do not invent values.
        - Do not assert engine names, depths, or move times unless provided. If engine provenance is unknown, omit it.
        - Keep speculative language out of the JSON. Use the `concise_explanation` field for any brief interpretation.

        5. **Brevity and clarity**
        - Keep each string value concise. Avoid long essays inside JSON fields.
        - Do not include markdown, code fences, or extra commentary outside the JSON object.

        Example JSON structure expected
        
        {expected_json_example}

        End of prompt.
        """
    return prompt
