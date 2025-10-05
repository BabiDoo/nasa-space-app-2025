# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import io
import csv
import time
from uuid import uuid4
from typing import List, Any, Dict
import dataclasses
from sqlalchemy.exc import OperationalError

from .schemas import UploadOut, PredictRequest, Prediction, PredictOut, Mission
from . import ml_client
from sqlmodel import select  # mantido caso use em outras rotas

from .db import init_db, get_session
from .models import Run as RunDB, Prediction as PredictionDB

app = FastAPI(title="ExoSeeker Backend")


# Retry no startup para aguardar o Postgres
@app.on_event("startup")
def _startup():
    for i in range(30):  # ~60s
        try:
            init_db()
            print("[startup] DB pronto.")
            break
        except OperationalError as e:
            print(f"[startup] DB indisponível, tentando novamente ({i+1}/30): {e}")
            time.sleep(2)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Memória em runtime (para preview/explicabilidade)
DATASETS: dict = {}   # dataset_id -> {"mission":..., "rows":[{target_id, mission, features}]}
RUNS: dict = {}       # run_id -> {"status":..., "preds":[Prediction]}
EXPLAINS: dict = {}   # target_id -> mocks de explicabilidade


def _to_plain(obj: Any) -> Any:
    """Converte recursivamente para tipos JSON-serializáveis."""
    if dataclasses.is_dataclass(obj):
        return {k: _to_plain(v) for k, v in dataclasses.asdict(obj).items()}

    # Pydantic v2
    if hasattr(obj, "model_dump"):
        return _to_plain(obj.model_dump())

    # Pydantic v1
    if hasattr(obj, "dict"):
        return _to_plain(obj.dict())

    if isinstance(obj, dict):
        return {str(k): _to_plain(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [_to_plain(x) for x in obj]

    # numpy types
    try:
        import numpy as np
        if isinstance(obj, np.generic):
            return obj.item()
    except Exception:
        pass

    return obj


@app.post("/api/upload", response_model=UploadOut)
async def upload(file: UploadFile = File(...), mission: Mission = Form(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Envie um CSV (.csv).")

    # Lê CSV completo
    content = await file.read()
    f = io.StringIO(content.decode("utf-8", errors="ignore"))
    reader = csv.DictReader(f)
    rows = list(reader)

    # Helpers de conversão
    def to_float(x):
        try:
            if x is None or str(x).strip() == "":
                return None
            return float(str(x).replace(",", "."))
        except Exception:
            return None

    def first_float(row, *cands):
        for c in cands:
            if c in row:
                v = to_float(row[c])
                if v is not None:
                    return v
        return None

    # Mapear CSV NASA -> features esperadas pelo ML
    def nasa_to_features(r: dict) -> dict:
        feats = {
            "longitude":           first_float(r, "ra", "ra_deg"),
            "latitude":            first_float(r, "dec", "dec_deg"),
            "stellar_temperature": first_float(r, "koi_steff", "st_teff"),
            "stellar_radius":      first_float(r, "koi_srad", "st_rad"),
            "planet_radius":       first_float(r, "koi_prad", "pl_rade"),
            "eq_temperature":      first_float(r, "koi_teq", "teq", "pl_eqt"),
            "stellar_sur_gravity": first_float(r, "koi_slogg", "st_logg"),
            # distância: tenta fontes mais confiáveis e cai para proxies
            "distance":            first_float(r, "st_dist", "sy_dist", "koi_sma", "koi_dor"),
        }
        return {k: v for k, v in feats.items() if v is not None}

    # Monta dataset interno
    dataset_id = str(uuid4())
    parsed_rows = []
    for i, r in enumerate(rows):
        tid = r.get("kepid") or r.get("koi_name") or r.get("kepoi_name") or r.get("id") or f"row{i}"
        feats = nasa_to_features(r)
        parsed_rows.append({"target_id": tid, "mission": mission, "features": feats})

    DATASETS[dataset_id] = {"mission": mission, "rows": parsed_rows}

    preview = {
        "rows": min(5, len(rows)),
        "columns": reader.fieldnames,
        "sample": rows[:5],
    }
    schema = {"required": ["target_id"], "dtypes": "float"}

    return UploadOut(dataset_id=dataset_id, preview=preview, schema=schema)


@app.post("/api/predict", response_model=PredictOut)
def predict(req: PredictRequest):
    ds = DATASETS.get(req.dataset_id)
    if not ds:
        raise HTTPException(404, "dataset_id desconhecido")

    run_id = str(uuid4())

    # chama o ML e monta preds_out em memória...
    preds_out: List[Prediction] = []
    results_for_rows = []
    for row in ds["rows"]:
        res = ml_client.predict_row(row)
        results_for_rows.append({"row": row, "res": res})

    with get_session() as s:
        # >>> CRIA O RUN COM run_id <<<
        s.add(RunDB(run_id=run_id, dataset_id=req.dataset_id))
        s.flush()  # garante que o INSERT do run é emitido antes das FKs

        for item in results_for_rows:
            row, res = item["row"], item["res"]

            pred = Prediction(
                target_id=row["target_id"],
                mission=row["mission"],
                per_model=res["per_model"],
                ensemble=res["ensemble"],
            )
            preds_out.append(pred)

            per_model_json = _to_plain(pred.per_model)
            ensemble = pred.ensemble if isinstance(pred.ensemble, dict) else {}
            s.add(PredictionDB(
                run_id=run_id,
                target_id=pred.target_id,
                mission=pred.mission,
                per_model=per_model_json,
                ensemble_label=str(ensemble.get("label", "") or ""),
                ensemble_confidence=float(ensemble.get("confidence", 0.0) or 0.0),
            ))

        s.commit()

    RUNS[run_id] = {"status": "done", "preds": preds_out}
    return PredictOut(run_id=run_id, status="done", predictions=preds_out, metrics={"macro_auc": None})



@app.get("/api/explain/{target_id}")
def explain(target_id: str):
    e = EXPLAINS.get(target_id)
    if not e:
        raise HTTPException(404, "target_id sem explicabilidade (ainda)")
    return {"target_id": target_id, "gradcam_1d": e["gradcam_1d"], "shap_tabular": e["shap_tabular"]}


@app.get("/api/jobs/{run_id}")
def get_job(run_id: str):
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(404, "run não encontrado")
    return {"run_id": run_id, "status": run["status"]}


@app.get("/api/jobs/{run_id}/results")
def get_results(run_id: str):
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(404, "run não encontrado")
    # pydantic v2
    return {"run_id": run_id, "predictions": [p.model_dump() for p in run["preds"]]}