# backend/app/schemas.py
from __future__ import annotations
from typing import Dict, List, Optional, Literal, Union, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID

# Missoes aceitas (ajuste se quiser permitir outras)
Mission = Literal["kepler", "k2", "tess"]

# Evita warning por campo "schema" em UploadOut
class UploadOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    dataset_id: str
    preview: Dict
    schema: Dict

# Score por modelo (aceita "non_planet" ou "not_planet")
class ModelScore(BaseModel):
    label: Literal["planet", "non_planet", "not_planet", "candidate"]
    proba: Dict[str, float]  # ex: {"planet": 0.91, "non_planet": 0.09}

# Pedido de predição
class PredictRequest(BaseModel):
    dataset_id: str

# Predição por alvo (o que o main.py monta)
class Prediction(BaseModel):
    target_id: str
    mission: Mission
    # por segurança, aceitamos tanto ModelScore quanto dict já normalizado
    per_model: Dict[str, Union[ModelScore, Dict[str, Any]]]
    ensemble: Dict[str, Any]

# Resposta final do endpoint /api/predict
class PredictOut(BaseModel):
    run_id: Union[UUID, str]
    status: Literal["done", "pending", "error"]
    predictions: List[Prediction]
    metrics: Optional[Dict[str, Any]] = None
