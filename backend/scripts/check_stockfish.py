"""
Utility script (infra, not domain logic -- fully implemented).

Verifies the Stockfish binary configured in .env is installed and
responds correctly, BEFORE you start writing app.chess_engine.py.
Debug your environment first, your code second.

Run with: python scripts/check_stockfish.py
"""

import sys
from pathlib import Path

# Running this as `python scripts/check_stockfish.py` puts scripts/ on
# sys.path, not the project root -- so `app` isn't importable without
# this. (Alternative fix: run as `python -m scripts.check_stockfish`
# with an __init__.py in scripts/. Either is fine; this is more
# forgiving for a one-off utility script.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chess.engine

from app.config import settings


def main() -> None:
    print(f"Looking for Stockfish at: {settings.stockfish_path}")
    try:
        with chess.engine.SimpleEngine.popen_uci(settings.stockfish_path) as engine:
            name = engine.id.get("name", "unknown")
            print(f"✅ Connected successfully. Engine reports: {name}")

            board = chess.Board()  # starting position
            info = engine.analyse(board, chess.engine.Limit(depth=10))
            print(f"✅ Sample analysis from starting position: {info['score']}")
    except FileNotFoundError:
        print(
            "❌ Stockfish binary not found at that path.\n"
            "   Install it (see README) and/or fix STOCKFISH_PATH in .env.\n"
            "   Find your install with: which stockfish"
        )
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 -- diagnostic script, broad catch is fine here
        print(f"❌ Unexpected error talking to Stockfish: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
