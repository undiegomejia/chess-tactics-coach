# Chess Tactics Coach

An agentic chess tactics coach: upload PGN games, get engine analysis, and
(eventually) an agent that explains *why* a move was a mistake in plain
language and schedules spaced-repetition drills.

## ⚠️ Current phase: "rough" (Phase 1 — pre-refactor)

This codebase is **deliberately unstructured** right now. Routes talk directly
to the database and the engine, with no separation of concerns. Once it works end-to-end,
we refactor it into a hexagonal architecture (ports/adapters).

## Setup

### 1. Python environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Stockfish (the chess engine binary — separate from the Python package)

- **macOS**: `brew install stockfish`
- **Ubuntu/Debian**: `sudo apt-get install stockfish`
- **Windows**: download from https://stockfishchess.org/download/ and note the `.exe` path

### 3. Configure environment

```bash
cp .env.example .env
# edit .env and set STOCKFISH_PATH to the binary location
# find it with: which stockfish   (macOS/Linux)
```

### 4. Verify Stockfish is reachable

```bash
python scripts/check_stockfish.py
```

This should print the engine's reported name/version. If it fails, fix
`STOCKFISH_PATH` in `.env` before writing any engine code — don't debug two
problems (your code + your environment) at once.

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/docs for the interactive OpenAPI UI.

### 6. Run tests

```bash
pytest
```

## What's scaffolded vs. what you build

| File | Status |
|---|---|
| `app/config.py` | ✅ done (settings loading) |
| `app/database.py` | ✅ done — SQLAlchemy engine/session setup |
| `app/models.py` | ✅ done — `Game` model |
| `app/chess_engine.py` | ✅ done — Stockfish wrapper with lifecycle management |
| `app/main.py` | ✅ done — All routes implemented with lifespan events |
| `scripts/check_stockfish.py` | ✅ done (infra utility) |
| `tests/test_main.py` | ✅ done — Comprehensive test suite with database isolation |
| `tests/conftest.py` | ✅ done — pytest fixtures (client, mock_engine, sample_pgn) |

## Planned MVP endpoints ✅ COMPLETED

1. ✅ `POST /games` — accept a PGN string, store it (with validation)
2. ✅ `GET /games` — list stored games (id, white, black, result)
3. ✅ `GET /games/{id}` — retrieve a single game
4. ✅ `GET /games/{id}/analysis` — run Stockfish on all positions, return evaluations
5. ✅ `GET /health` — health check endpoint

**Phase 1 Complete:** Core CRUD operations and engine integration working with comprehensive test coverage.

## Current Features

- **PGN Parsing:** Validates and extracts game metadata (players, result, moves)
- **Stockfish Integration:** Lifecycle-managed engine with factory pattern
- **Database:** SQLAlchemy with SQLite (easily swappable to PostgreSQL)
- **Testing:** Isolated in-memory databases with mock engine for fast tests
- **Error Handling:** Proper 400/404 responses with detailed error messages

## Next Steps (Phase 2+)

Resist the urge to add auth, async task queues, or the agent layer yet —
those come in later phases once this rough version proves the core loop
works and we've refactored it.
