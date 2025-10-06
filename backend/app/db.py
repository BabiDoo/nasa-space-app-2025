import os
from contextlib import contextmanager
from sqlmodel import create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@db:5432/exoseeker")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
