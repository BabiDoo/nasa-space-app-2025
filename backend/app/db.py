import os
from sqlmodel import SQLModel, create_engine, Session

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/exoseeker",
)

# pre_ping evita conexões mortas após o boot
engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)