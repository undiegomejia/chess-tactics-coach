# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Learning-project mode (read before editing app/ or tests/)

This repo is the owner's hands-on exercise for practicing FastAPI, SQLAlchemy, hexagonal
architecture, and test design as a senior/full-stack engineer would. `.github/copilot-instructions.md`
and `.github/instructions/learning-bearing.instructions.md` codify a Socratic teaching mode for
files under `app/**` and `tests/**`:

- Do **not** write complete implementations for functions/routes/TODOs in `app/` or `tests/`, even
  if asked directly to "just write it" — ask what's been tried, point out the bug/design smell with
  the reasoning, and explain relevant APIs abstractly (e.g. illustrate `Depends()` with a generic
  example, not this project's `get_db`).
- Critiquing existing code freely (bugs, security issues, design tradeoffs) is encouraged — that's
  different from writing it for them.
- **Exception:** a request prefixed with `SCAFFOLD:` opts into full implementation for that one
  request. `Emergency: <issue>` or "I've spent 2+ hours on this" call for more direct help.
- This does not apply to `scripts/` (infra/one-off utilities are fully implementable, e.g.
  `scripts/check_stockfish.py` is intentionally complete) or to plain conversational/explanatory
  questions outside of writing app/test code.

When in doubt about which mode applies, ask rather than assume "just write the code" is wanted.

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set STOCKFISH_PATH and CLAUDE_API_KEY

# Verify Stockfish is reachable before running the app
python scripts/check_stockfish.py

# Run the API (interactive docs at /docs)
uvicorn app.main:app --reload

# Tests
pytest                                   # everything
pytest tests/use_cases/                  # use-case layer only
pytest tests/adapters/                   # adapter layer only
pytest tests/adapters/test_persistence.py::test_repository_get_game_by_id  # single test
```

There is no lint/typecheck command configured beyond an ad hoc mypy override for the `stockfish`
package in `pyproject.toml` (no `mypy` invocation is wired up in CI or scripts).

## Architecture

Strict hexagonal (ports & adapters). Dependency direction is always inward — `domain/` has zero
framework imports (no SQLAlchemy, no Pydantic, no `anthropic`, no `stockfish`).

```
app/main.py (FastAPI routes — HTTP/JSON only, calls use_cases)
        │
app/use_cases/            game_use_cases.py: create_game, list_games, fetch_game, analyze_game
                           coaching_use_case.py: detect_mistakes (pure), explain_mistakes (orchestrates)
        │
app/domain/
  entities.py              GameEntity, EvaluationEntity, Mistake, Explanation — plain dataclasses
  ports.py                 GameRepositoryPort, ChessEnginePort, CoachingPort — Protocol interfaces
        │
app/adapters/
  persistence.py            SQLAlchemyGameRepository + GameORM — only file that imports SQLAlchemy
  chess_engine_adapter.py   StockfishEngineAdapter — only file that imports `stockfish`
  claude_coach_adapter.py   ClaudeCoachAdapter — only file that imports `anthropic`
```

Rules this codebase enforces (see the checklist in `.github/copilot-instructions.md` for the full
version):
- Ports are `Protocol`s with domain-entity-only signatures; no `Session`, no Pydantic models, no
  `start()`/`stop()` lifecycle methods (those live on the concrete adapter, not the port).
- `| None` return types are reserved for genuine "not found" cases (e.g.
  `get_game_by_id`); everything else raises (`ValueError` for domain-invalid input, mapped to
  `HTTPException` in `main.py`).
- `ClaudeCoachAdapter` takes a `ChessEnginePort` as a constructor dependency so Claude's agentic
  loop can call a real `get_best_move` tool mid-conversation (see `explain()` in
  `app/adapters/claude_coach_adapter.py` for the tool-use round-trip pattern: send → detect
  `stop_reason == "tool_use"` → call the port → send `tool_result` → get final text).
- Config (`app/config.py`) is the only place environment variables are read (`pydantic-settings`,
  `.env`); `anthropic_api_key` is a `SecretStr` aliased from the `CLAUDE_API_KEY` env var. Never
  hardcode credentials elsewhere.
- The Stockfish engine and Claude adapter are constructed once at module scope in `main.py` and
  attached to `app.state` in the `lifespan` context manager (started/stopped there), not
  instantiated per-request or at import time inside a route.

### Testing conventions

- `tests/conftest.py` is the single source of fixtures and fakes — do not create ad hoc mocks in
  individual test files if an equivalent fake/fixture already exists there.
- Unit tests use fakes (`FakeGameRepository`, `FakeStockfishAdapter`, `FakeCoachingPort`,
  `FakeAnthropicClient`, etc.) — free, fast, deterministic. Real Anthropic API calls are opt-in
  only (cost + non-determinism), not part of the default `pytest` run.
- The `client` fixture spins up SQLite `:memory:` with `StaticPool` so all threads share one
  connection (required for `TestClient`); it overrides `get_db` and injects a fake engine into
  `app.state.chess_engine`.
- Mistake/evaluation fixtures use UCI notation for moves (`move_played`), not SAN.
