"""
Utility script to output sample PGN as JSON.

Prints a notable chess game (Gukesh vs Ding Liren, World Championship 2024)
in JSON format suitable for API testing.
"""

import json

pgn = """[Event "rated rapid game]
[Site "?"]
[Date "?"]
[Round "7.1"]
[White "?"]
[Black "?"]
[Result "?"]
[WhiteElo "?"]
[BlackElo "?"]
[ECO "?"]

e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# *"""

print(json.dumps({"pgn": pgn}, indent=2))

from app.domain.entities import Mistake

mistake = Mistake(
    move_number=1,
    player="white",
    fen_before="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    fen_after="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    eval_before=0,
    eval_before_type="mate",
    eval_after=0,
    eval_after_type="mate",
    move_played="e4"
)

#mistake to json request 
mistake_json = json.dumps({
    "move_number": mistake.move_number,
    "player": mistake.player,
    "fen_before": mistake.fen_before,
    "fen_after": mistake.fen_after,
    "eval_before": mistake.eval_before,
    "eval_before_type": mistake.eval_before_type,
    "eval_after": mistake.eval_after,
    "eval_after_type": mistake.eval_after_type,
    "move_played": mistake.move_played
})  

print(mistake_json)

import chess
board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKB1R w KQkq - 0 1")
print([m.uci() for m in board.legal_moves])