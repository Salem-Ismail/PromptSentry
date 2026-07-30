"""
db connection stuff

hostname "postgres" is the docker compose service name
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://promptsentry:promptsentry@postgres:5432/promptsentry",
)

engine = create_engine(DATABASE_URL)

# one session per write
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """create tables that dont exist yet. fine for now, migrations later maybe."""
    from models import request_log  # noqa: F401

    Base.metadata.create_all(bind=engine)
