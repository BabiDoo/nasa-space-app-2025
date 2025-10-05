from typing import Dict, Literal, Optional, Any, List
from pydantic import BaseModel

Mission = Literal["kepler","k2","tess"]
Label   = Literal["planet","non_planet"]

class UploadOut(BaseModel):
    dataset_id: str
    preview: Dict[str, Any]
    schema: Dict[str, Any]

class PredictRequest(BaseModel):
    dataset_id: str
    model_name: Literal["baseline","multimodal"]

class ModelScore(BaseModel):
    label: str
    proba: Dict[Label, float] = {}

class Prediction(BaseModel):
    target_id: str
    mission: Mission
    per_model: Dict[str, ModelScore]
    ensemble: Dict[str, Any]

class PredictOut(BaseModel):
    run_id: str
    status: Literal["done","queued","running","error"]
    predictions: List[Prediction]
    metrics: Optional[Dict[str, Any]] = None
