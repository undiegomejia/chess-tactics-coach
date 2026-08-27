# Copilot Instructions — Chess Tactics Coach

Purpose: concise, project-specific guidance so an AI coding agent can be
productive immediately. This repository is a learning exercise — follow
the explicit constraints in `.github/instructions/learning-bearing.instructions.md`.

High level
- Phase 1 (current): a deliberately "rough" FastAPI app where routes
  call the DB and engine directly. Don't introduce large architectural
  refactors yet (no service/repository layering) — that's Phase 2+.

Key files and responsibilities
- `app/main.py` — FastAPI entrypoint and routes (one working `GET /health`).
- `app/config.py` — Pydantic Settings (use `.env`; fields: `stockfish_path`,
  `database_url`).
- `app/database.py` — TODO: SQLAlchemy engine, SessionLocal, Base,
  `get_db()` generator to use with `Depends()`.
- `app/models.py` — TODO: `Game` model (store `pgn`, `white`, `black`,
  `result`, `created_at`). Consider the tradeoff: store parsed moves vs
  raw PGN (re-parse cost vs query simplicity).
- `app/chess_engine.py` — TODO: Stockfish integration; comments already
  describe two viable approaches (use python-chess `chess.engine` vs
  the `stockfish` pip wrapper). Pick one and justify it in PR notes.
- `scripts/check_stockfish.py` — utility that verifies the configured
  Stockfish binary; run this first to debug environment issues.
- `tests/test_main.py` — example TestClient test for `/health` and a set
  of TODO tests that describe expected behavior for the exercise.

Data flow (what routes should implement)
- POST /games: accept a Pydantic model with `pgn: str`; parse PGN with
  python-chess to extract headers (`White`, `Black`, `Result`), validate
  and save a `Game` row using a DB session from `Depends(get_db)`.
- GET /games: list games with summary fields (id, white, black, result,
  created_at). Avoid returning full PGN in list view.
- GET /games/{id}/analysis: read game, parse PGN, call
  `app.chess_engine.analyze_game()` and return evaluation results. Handle
  missing game -> 404 explicitly.

Engine integration notes (from `app/chess_engine.py` comments)
- Two options: (a) `chess.engine.SimpleEngine.popen_uci(path)` — lower-level
  and aligns with python-chess objects, or (b) `stockfish.Stockfish(path=...)`
  — higher-level but may need conversions.
- Consider engine lifecycle: do NOT open a new process per request. Use a
  singleton started on FastAPI startup (lifespan events) or a small pool.

Database setup expectations (`app/database.py` TODO)
- Needs: an engine bound to `settings.database_url`, a session factory,
  a declarative base importable by `app/models.py`, and a FastAPI
  dependency-injection-compatible session provider.
- Do not write this for the owner. If asked to explain the pattern in
  the abstract (not this file), that's fine — see SQLAlchemy + FastAPI
  docs on `Depends()`.

Testing & CI
- Unit tests use FastAPI's `TestClient` (httpx). See `tests/test_main.py`
  for the health check example — mirror that pattern for other route tests.
- Avoid running slow, Stockfish-dependent analysis inside the regular
  unit test suite. Treat those as integration tests or mock the
  engine. The repo includes `scripts/check_stockfish.py` to validate
  the binary separately.

Developer workflows / commands (copied from README and verified)
- Create venv and install:
  python3 -m venv venv
  source venv/bin/activate   # (Windows PowerShell/CMD: venv\Scripts\activate)
  pip install -r requirements.txt
- Configure `.env` (copy `.env.example`), set `STOCKFISH_PATH` and
  `DATABASE_URL` (these map to `settings.stockfish_path` and
  `settings.database_url`).
- Verify Stockfish before writing engine code:
  python scripts/check_stockfish.py
- Run server locally:
  uvicorn app.main:app --reload
- Run tests:
  pytest

Project-specific conventions / do/don't
- DO read `app/*.py` comments — they intentionally document the
  expected design choices for the exercise (e.g. engine choices,
  DB tradeoffs). Use those comments as authoritative guidance.
- DO preserve the "learning-bearing" rule: files under `app/` and
  `tests/` with `# TODO` are exercises. See
  `.github/instructions/learning-bearing.instructions.md` for strict
  rules: don't silently implement TODOs or rewrite the owner's learning
  exercises. If the owner asks explicitly (prefix with `SCAFFOLD:`), it's
  allowed to implement.
- DO justify non-trivial choices (engine wrapper, where to parse PGN,
  whether to store parsed moves) in PR descriptions — the repository's
  point is to discuss tradeoffs.
- DON'T add heavy-weight infra (Celery, DB server changes), auth, or
  unrelated refactors in Phase 1. Those will be introduced later.

If you need clarification
- Ask what the owner has tried and which TODO they want implemented.
- If asked to implement a TODO, verify whether the owner permitted
  scaffolded implementation (look for `SCAFFOLD:` in their request).

References in repo: `app/main.py`, `app/config.py`, `app/database.py`,
`app/models.py`, `app/chess_engine.py`, `scripts/check_stockfish.py`,
`tests/test_main.py`, `README.md`.

---

Merge note: preserved the original learning-bearing intent; expanded with
explicit, actionable examples, commands, and file-level expectations.
