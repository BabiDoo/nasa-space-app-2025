from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Column, JSON

class Run(SQLModel, table=True):
    run_id: str = Field(primary_key=True)
    dataset_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="run.run_id")
    target_id: str
    mission: str
    per_model: Dict[str, Any] = Field(sa_column=Column(JSON))
    ensemble_label: str
    ensemble_confidence: float
