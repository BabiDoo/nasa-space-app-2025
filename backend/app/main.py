from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import csv, io
from typing import List

from .schemas import UploadOut, PredictRequest, Prediction, PredictOut, Mission
from . import ml_client

from .db import init_db, get_session
from .models import Run as RunDB, Prediction as PredictionDB

app = FastAPI(title="ExoSeeker Backend")

@app.on_event("startup")
def _startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

DATASETS = {}
RUNS = {}
EXPLAINS = {}

@app.post("/api/upload", response_model=UploadOut)
async def upload(file: UploadFile = File(...), mission: Mission = Form(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Envie um CSV (.csv).")

    # --- Lê o CSV inteiro em memória
    content = await file.read()
    f = io.StringIO(content.decode("utf-8", errors="ignore"))
    reader = csv.DictReader(f)
    rows = list(reader)

    # --- Helpers de conversão
    def to_float(x):
        try:
            if x is None or str(x).strip() == "":
                return None
            return float(str(x).replace(",", "."))  # caso venha com vírgula decimal
        except Exception:
            return None

    def first_float(row, *cands):
        for c in cands:
            if c in row:
                v = to_float(row[c])
                if v is not None:
                    return v
        return None  # ausência: o serviço de ML já usa 0.0 nesses casos

    # --- Mapeamento NASA -> features esperadas pelo ML
    # Kepler/K2/TESS: cobrimos os nomes mais comuns
    def nasa_to_features(r: dict) -> dict:
        feats = {
            "longitude":           first_float(r, "ra", "ra_deg"),
            "latitude":            first_float(r, "dec", "dec_deg"),
            "stellar_temperature": first_float(r, "koi_steff", "st_teff"),
            "stellar_radius":      first_float(r, "koi_srad", "st_rad"),
            "planet_radius":       first_float(r, "koi_prad", "pl_rade"),
            "eq_temperature":      first_float(r, "koi_teq", "teq", "pl_eqt"),
            "stellar_sur_gravity": first_float(r, "koi_slogg", "st_logg"),
            # distância é a mais incerta nos CSVs KOI.
            # Preferimos st_dist; se não existir, usamos um proxy (koi_sma ou koi_dor).
            "distance":            first_float(r, "st_dist", "sy_dist", "koi_sma", "koi_dor"),
        }
        # Remove chaves None (o serviço usa .get(k, 0.0) de qualquer jeito)
        return {k: v for k, v in feats.items() if v is not None}

    # --- Monta dataset interno com target_id + features mapeadas
    dataset_id = str(uuid4())
    parsed_rows = []
    for i, r in enumerate(rows):
        # escolha de ID: kepid é bom para KOIs; cai para "row{i}" se não houver
        tid = r.get("kepid") or r.get("koi_name") or r.get("kepoi_name") or r.get("id") or f"row{i}"
        feats = nasa_to_features(r)
        parsed_rows.append({
            "target_id": tid,
            "mission": mission,
            "features": feats
        })

    DATASETS[dataset_id] = {"mission": mission, "rows": parsed_rows}

    # --- Preview e schema (só informativo)
    preview = {
        "rows": min(5, len(rows)),
        "columns": reader.fieldnames,
        "sample": rows[:5]
    }
    # as 'required' relevantes para seu fluxo
    schema = {"required": ["target_id"], "dtypes": "float"}

    return UploadOut(dataset_id=dataset_id, preview=preview, schema=schema)


@app.post("/api/predict", response_model=PredictOut)
def predict(req: PredictRequest):
    ds = DATASETS.get(req.dataset_id)
    if not ds:
        raise HTTPException(404, "dataset_id desconhecido")

    run_id = str(uuid4())

    preds: List[Prediction] = []
    for row in ds["rows"]:
        res = ml_client.predict_row(row)
        preds.append(Prediction(
            target_id=row["target_id"],
            mission=row["mission"],
            per_model=res["per_model"],
            ensemble=res["ensemble"]
        ))
        EXPLAINS.setdefault(row["target_id"], {
            "gradcam_1d":  {"time": [0,1,2,3,4], "flux": [1.0,0.99,0.97,1.01,1.0], "importance": [0,0.1,0.6,0.2,0.1]},
            "shap_tabular": {"top_features": [
                {"name": "pl_orbper", "value": 0.31},
                {"name": "st_teff",  "value": 0.27}
            ]}
        })

    # Persistência
    with get_session() as s:
        s.add(RunDB(run_id=run_id, dataset_id=req.dataset_id))
        for p in preds:
            s.add(PredictionDB(
                run_id=run_id,
                target_id=p.target_id,
                mission=p.mission,
                per_model=p.per_model,
                ensemble_label=p.ensemble["label"],
                ensemble_confidence=p.ensemble.get("confidence", 0.0),
            ))
        s.commit()

    RUNS[run_id] = {"status": "done", "preds": preds}
    metrics = {"macro_auc": None, "f1_per_class": None}
    return PredictOut(run_id=run_id, status="done", predictions=preds, metrics=metrics)

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
    return {"run_id": run_id, "predictions": [p.dict() for p in run["preds"]]}
