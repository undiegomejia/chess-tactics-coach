"""
TODO: The `Game` SQLAlchemy model.

Fields to include, at minimum:
- id            (primary key)
- pgn           (text -- the full PGN move text)
- white         (string -- white player name, parse from PGN headers)
- black         (string -- black player name, parse from PGN headers)
- result        (string -- "1-0", "0-1", "1/2-1/2", or "*")
- created_at    (datetime, default to now)

Import `Base` from app.database once you've built that file.

A question to sit with while you write this (we'll discuss it when I
review): should `Game` store the parsed moves, or just the raw PGN
string and re-parse with python-chess on read? There's a real tradeoff
here -- storage/query simplicity vs. re-parse cost -- and there's no
single correct answer. I want your reasoning, not just your code.
"""

# from sqlalchemy import Column, Integer, String, Text, DateTime
# from datetime import datetime
# from app.database import Base

# TODO: class Game(Base):
#     __tablename__ = "games"
#     ...


from datetime import datetime, timezone
from app.database import Base
from sqlalchemy import Integer, String, Text, DateTime, Column

def get_datetime():
    return datetime.now(timezone.utc)

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    pgn = Column(Text, nullable=False)
    white = Column(String(100), nullable=False)
    black = Column(String(100), nullable=False)
    result = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_datetime, nullable=False)

    