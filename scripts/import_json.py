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