from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from db import engine
from routers import catalog, missions
from models import SQLModel

app = FastAPI(title="ExoSeeker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)  # cria tabela do catálogo

app.include_router(catalog.router)
app.include_router(missions.router)

@app.get("/")
def root():
    return {"ok": True, "service": "ExoSeeker API"}
