import os, hashlib, random, requests
from typing import Dict, Any

MODE = os.getenv("ML_MODE", "mock")  # mock | http
ML_URL = os.getenv("ML_SERVICE_URL", "http://ml:8001")

def _deterministic_float(seed: str, a=0.4, b=0.98) -> float:
    rnd = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 10_000
    random.seed(rnd)
    return round(random.uniform(a,b), 3)

def _mock_predict_row(row: Dict[str, Any]) -> Dict[str, Any]:
    tid = row.get("target_id","?")
    def pack(p: float):
        return {"label": "planet" if p>=0.5 else "non_planet",
                "proba": {"planet": p, "non_planet": round(1-p,3)}}
    per_model = {
        "gaussian_nb":   pack(_deterministic_float(tid+"nb")),
        "knn":           pack(_deterministic_float(tid+"knn")),
        "decision_tree": pack(_deterministic_float(tid+"dt")),
        "random_forest": pack(_deterministic_float(tid+"rf")),
        "log_reg":       pack(_deterministic_float(tid+"lr")),
    }
    votes = sum(1 for v in per_model.values() if v["label"]=="planet")
    label = "planet" if votes >= 3 else "non_planet"
    conf  = round(sum(v["proba"]["planet"] for v in per_model.values())/5, 3)
    return {"per_model": per_model, "ensemble": {"rule":"majority_vote","label":label,"confidence":conf}}

def predict_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if MODE == "http":
        url = f"{ML_URL}/predict"
        payload = {"mission": row.get("mission"), "features": row.get("features", {})}
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    return _mock_predict_row(row)
