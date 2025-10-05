import os
from sqlmodel import SQLModel, create_engine, Session

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/exoseeker")
engine = create_engine(DB_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
