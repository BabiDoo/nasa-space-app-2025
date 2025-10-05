
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Literal, Optional, List
import uvicorn
import orjson

from .training import ModelRegistry, METRICS

Mission = Literal["kepler","k2","tess"]

app = FastAPI(title="ExoSeeker ML Service")

REGISTRY = ModelRegistry()
REGISTRY.fit_all()

class PredictIn(BaseModel):
    mission: Mission
    object_id: Optional[str] = None
    features: Dict[str, float]

@app.get("/health")
def health():
    return {"status": "ok", "models": len(REGISTRY.models)}

@app.get("/datasets")
def datasets():
    return REGISTRY.list_datasets()

@app.get("/metrics")
def metrics():
    return {"available": list(METRICS.keys())}

@app.get("/tests")
def tests(mission: Optional[Mission] = None, model: Optional[str] = None, balanced: Optional[bool] = None, metric: Optional[str] = None):
    results = REGISTRY.get_results(mission=mission, model=model, balanced=balanced)
    payload = []
    for mr in results:
        row = {
            "mission": mr.mission,
            "model": mr.model_name,
            "balanced": mr.balanced,
            "metrics": mr.metrics,
            "report": mr.report,
        }
        if metric:
            row["metric_selected"] = {metric: mr.metrics.get(metric)}
        payload.append(row)
    return {"count": len(payload), "results": payload}

@app.get("/final")
def final(metric: str = "f1_weighted", balanced: bool = True, mission: Optional[Mission] = None, model: Optional[str] = None):
    # final = best by metric per mission OR filter by model/mission
    if model or mission is not None:
        # return a filtered subset
        results = REGISTRY.get_results(mission=mission, model=model, balanced=balanced)
        return {"mode": "filtered", "metric": metric, "balanced": balanced,
                "results": [{
                    "mission": r.mission, "model": r.model_name, "balanced": r.balanced, "metrics": r.metrics
                } for r in results]}
    best = REGISTRY.best_by(metric=metric, balanced=balanced)
    return {"mode": "best_by_metric", "metric": metric, "balanced": balanced,
            "winners": [{
                "mission": r.mission, "model": r.model_name, "metrics": r.metrics
            } for r in best]}

@app.get("/compare")
def compare(metric: str = "f1_weighted", balanced: bool = True):
    # compare all models by metric across missions
    results = REGISTRY.get_results(balanced=balanced)
    table: Dict[str, Dict[str, float]] = {}
    for r in results:
        key = f"{r.mission}"
        table.setdefault(key, {})
        table[key][r.model_name] = r.metrics.get(metric, 0.0)
    return {"metric": metric, "balanced": balanced, "table": table}

@app.post("/predict")
def predict(body: PredictIn):
    try:
        res = REGISTRY.predict(body.mission, body.features)
    except Exception as e:
        raise HTTPException(400, f"prediction error: {e}")
    # Ensure labels precisely match backend expectation: planet or non_planet
    # (candidate may appear only in per_model labels/probas)
    return res

if __name__ == "__main__":
    uvicorn.run("ml_service.main:app", host="0.0.0.0", port=8001, reload=False)
