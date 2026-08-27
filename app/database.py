"""
TODO: SQLAlchemy engine + session setup.

This is deliberately empty. Your job:

1. Create a SQLAlchemy `engine` using `settings.database_url` (imported
   from app.config).
2. Create a `SessionLocal` sessionmaker bound to that engine.
3. Create a `Base` (declarative base) that app/models.py will import
   and inherit from.
4. Write a `get_db()` generator function that yields a session and
   closes it afterward -- this is the FastAPI dependency-injection
   pattern you'll wire into routes with `Depends(get_db)`.

Why this matters for the later refactor: right now `get_db()` will be
called directly inside route handlers in main.py. That's the "rough"
part -- routes coupled directly to the database. In the hexagonal
refactor, routes won't know SQLAlchemy exists at all; they'll depend on
a repository interface instead. Keep that tension in mind as you build
this -- you're about to feel exactly why the pattern exists.

Docs if you get stuck: https://fastapi.tiangolo.com/tutorial/sql-databases/
(don't copy-paste it blindly -- read it, then write your own from
understanding, or the exercise doesn't do its job)
"""

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from app.config import settings

# TODO: engine = ...
# TODO: SessionLocal = ...
# TODO: Base = ...


# TODO: def get_db():
#     ...

from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
   db = SessionLocal()
   try:
      yield db
   except Exception as e:
      db.rollback()
      raise e
   finally:
      db.close()