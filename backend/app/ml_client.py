# app/ml_client.py
from __future__ import annotations

import os
import json
from typing import Any, Dict
from dataclasses import asdict, is_dataclass

import requests


class MLClient:
    """
    Cliente do microserviço de ML com dois modos:
      - http: chama o serviço real via REST (POST /predict)
      - mock: gera predições sintéticas para testes locais

    Variáveis de ambiente:
      ML_MODE=http|mock         (default: mock)
      ML_SERVICE_URL=http://ml:8001
    """

    def __init__(self) -> None:
        self.mode = (os.getenv("ML_MODE") or "mock").strip().lower()
        self.base = (os.getenv("ML_SERVICE_URL") or "http://ml:8001").rstrip("/")
        self.timeout = 30  # segundos

    # --------- API pública utilizada pelo main.py ---------

    def predict_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe um 'row' no formato do backend:
          { "target_id": "...", "mission": "kepler|k2|tess", "features": {...} }

        Retorna sempre:
          {
            "per_model": { "<model>": {"label": "...", "proba": {...}} },
            "ensemble":  { "rule": "...", "label": "...", "confidence": 0.0 }
          }
        """
        if self.mode == "http":
            return self._predict_http(row)
        return self._predict_mock(row)

    def health(self) -> Dict[str, Any]:
        if self.mode != "http":
            return {"status": "ok", "mode": "mock"}
        try:
            r = requests.get(f"{self.base}/health", timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    # --------- Implementações internas ---------

    def _predict_http(self, row: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "mission": row.get("mission"),
            "object_id": str(row.get("target_id")),
            "features": self._to_plain(row.get("features", {})),
        }
        url = f"{self.base}/predict"
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return self._normalize_response(data)

    def _predict_mock(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heurística simples para testes: usa planet_radius (quando houver)
        para inventar predições coerentes e estáveis.
        """
        feats = row.get("features", {}) or {}
        pr = feats.get("planet_radius")
        try:
            pr = float(pr) if pr is not None else None
        except Exception:
            pr = None

        # pontuação ingênua
        planet_score = 0.85 if (pr is not None and pr < 1.5) else 0.1

        per_model = {
            "gaussian_nb": {
                "label": "planet" if planet_score > 0.7 else "non_planet",
                "proba": {
                    "planet": round(min(1.0, planet_score), 3),
                    "non_planet": round(1 - min(1.0, planet_score), 3),
                    "candidate": 0.0,
                },
            },
            "knn": {
                "label": "planet" if planet_score > 0.6 else "non_planet",
                "proba": {
                    "planet": round(min(1.0, planet_score + 0.1), 3),
                    "non_planet": round(max(0.0, 1 - (planet_score + 0.1)), 3),
                    "candidate": 0.0,
                },
            },
            "log_reg": {
                "label": "planet" if planet_score > 0.5 else "non_planet",
                "proba": {
                    "planet": round(min(1.0, planet_score + 0.2), 3),
                    "non_planet": round(max(0.0, 1 - (planet_score + 0.2)), 3),
                    "candidate": 0.0,
                },
            },
        }

        # ensemble: majority vote
        votes = [m["label"] for m in per_model.values()]
        label = "planet" if votes.count("planet") >= 2 else "non_planet"
        conf = sum(m["proba"].get(label, 0.0) for m in per_model.values()) / len(per_model)

        return {
            "per_model": per_model,
            "ensemble": {"rule": "majority_vote", "label": label, "confidence": round(conf, 3)},
        }

    # --------- Normalização / utilidades ---------

    def _normalize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza a resposta do ML para o formato esperado pelo backend.
        - aceita variações de rótulos (non_planet / not_planet / etc.)
        - força probabilidades numéricas
        - garante JSON puro
        """
        per_model_out: Dict[str, Dict[str, Any]] = {}
        for name, res in (data.get("per_model") or {}).items():
            label = self._normalize_label((res or {}).get("label"))
            proba = (res or {}).get("proba") or {}
            # filtra / converte valores numéricos
            proba_num = {}
            for k, v in proba.items():
                try:
                    proba_num[str(k)] = float(v)
                except Exception:
                    # ignora valores não numéricos
                    continue
            per_model_out[str(name)] = {"label": label, "proba": proba_num}

        ens = data.get("ensemble") or {}
        ensemble = {
            "rule": ens.get("rule"),
            "label": self._normalize_label(ens.get("label")),
            "confidence": self._to_float(ens.get("confidence", 0.0)),
        }
        return {"per_model": per_model_out, "ensemble": ensemble}

    @staticmethod
    def _normalize_label(label: Any) -> str:
        if label is None:
            return ""
        l = str(label).lower().strip().replace("-", "_")
        if l in {"non_planet", "not_planet", "nonplanet", "notplanet"}:
            return "non_planet"
        if l in {"planet"}:
            return "planet"
        if l in {"candidate"}:
            return "candidate"
        return l  # mantém outros rótulos se existirem

    @staticmethod
    def _to_float(x: Any) -> float:
        try:
            return float(x)
        except Exception:
            return 0.0

    @staticmethod
    def _to_plain(obj: Any) -> Any:
        """Converte recursivamente para tipos JSON-serializáveis."""
        if is_dataclass(obj):
            return MLClient._to_plain(asdict(obj))
        if hasattr(obj, "model_dump"):
            return MLClient._to_plain(obj.model_dump())
        if hasattr(obj, "dict"):
            return MLClient._to_plain(obj.dict())
        if isinstance(obj, dict):
            return {str(k): MLClient._to_plain(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [MLClient._to_plain(v) for v in obj]
        # numpy types
        try:
            import numpy as np
            if isinstance(obj, np.generic):
                return obj.item()
        except Exception:
            pass
        return obj


# Instância única usada pelo app
_client = MLClient()

# Funções livres para importar no main.py
def predict_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return _client.predict_row(row)

def health() -> Dict[str, Any]:
    return _client.health()
