"""
SQLAlchemy database setup.

Provides:
- SQLAlchemy engine connected to configured database
- SessionLocal factory for creating database sessions
- Base class for ORM models
- get_db() dependency for FastAPI route injection
"""

from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
   """Yield database session for FastAPI dependency injection."""
   db = SessionLocal()
   try:
      yield db
   except Exception as e:
      db.rollback()
      raise e
   finally:
      db.close()