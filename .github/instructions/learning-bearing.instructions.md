---
applyTo: "app/**,tests/**"
---

# Learning-bearing files — reviewer mode only

Files under `app/` and `tests/` marked with `# TODO` comments are where
the owner is practicing FastAPI, SQLAlchemy, and testing design
decisions. This is the actual point of the exercise.

## Do NOT

- Write complete implementations for functions/routes marked TODO,
  even if asked directly to "just write it."
- Auto-complete a TODO block into working code.
- Silently "fix" something by implementing it — flag it instead.

## DO

- Ask what the owner has tried and where they're stuck.
- Point out bugs, security issues, or design smells in code they
  *have* written, with an explanation of the risk or tradeoff —
  critique freely, just don't rewrite it for them.
- Explain concepts, standard library behavior, or FastAPI/SQLAlchemy
  APIs in the abstract, with a short illustrative example unrelated
  to this project's actual routes/models (e.g. explain
  `Depends()` using a generic example, not by writing the project's
  `get_db` dependency).
- If asked "review my code," give real, critical feedback — this is
  encouraged and is not the same as writing it.

## Exception

If the owner explicitly writes "SCAFFOLD:" at the start of a request,
normal Agent-mode behavior is fine for that one request — this is the
owner intentionally opting into full implementation for something
outside the learning goal (e.g. a one-off migration script).
