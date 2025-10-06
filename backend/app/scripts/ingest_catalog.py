import os
import sys
import csv
from typing import Any, Dict, Optional
from contextlib import contextmanager

from sqlmodel import Session, select
from pydantic import BaseModel


try:
    from db import engine  # type: ignore
    from models import ExoplanetCatalog  # type: ignore
except Exception as e:
    print(f"[ingest] ERRO ao importar app: {e}", file=sys.stderr)
    raise

CATALOG_CSV = os.getenv("CATALOG_CSV", "/data/catalog_preclassified.csv")


class RowMap(BaseModel):
    """
    Estrutura intermediária com campos conhecidos do modelo.
    O que não for mapeado fica em 'extra'.
    """
    mission: str
    object_id: str
    ra: Optional[float] = None
    dec: Optional[float] = None

    stellar_temperature: Optional[float] = None
    stellar_radius: Optional[float] = None
    planet_radius: Optional[float] = None
    eq_temperature: Optional[float] = None
    distance: Optional[float] = None
    surface_gravity: Optional[float] = None
    orbital_period: Optional[float] = None
    insol_flux: Optional[float] = None
    depth: Optional[float] = None

    final_classification: Optional[str] = None  # "planet" | "not_planet" | "candidate"
    final_confidence: Optional[float] = None

    extra: Dict[str, Any] = {}


@contextmanager
def session_scope():
    with Session(engine) as sess:
        yield sess


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in {"nan", "none", "null"}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def guess_mission(row: Dict[str, Any]) -> str:
    """
    Tenta inferir a missão a partir de campos comuns; se não houver, usa 'kepler' como default.
    """
    mission = (row.get("mission") or row.get("Mission") or "").strip().lower()
    if mission in {"kepler", "k2", "tess"}:
        return mission
    # Heurísticas simples (pelo nome de colunas):
    headers = {h.lower() for h in row.keys()}
    if any(h.startswith("koi_") or h == "kepid" for h in headers):
        return "kepler"
    if "epic" in headers:
        return "k2"
    if "tic" in headers:
        return "tess"
    return "kepler"


def guess_object_id(row: Dict[str, Any]) -> str:
    """
    Captura um identificador único da linha.
    """
    candidates = [
        "object_id", "id", "kepid", "kic", "epic", "tic", "loc_rowid", "rowid", "pl_name"
    ]
    for key in candidates:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
        # também tenta variações de caixa
        for k in row.keys():
            if k.lower() == key and str(row[k]).strip():
                return str(row[k]).strip()
    # fallback: hash do conteúdo (evita duplicidade inconsistente)
    return str(abs(hash(tuple(sorted(row.items())))))


def map_classification(row: Dict[str, Any]) -> Optional[str]:
    """
    Normaliza rótulos para 'planet' | 'not_planet' | 'candidate'
    a partir de colunas típicas (koi_disposition, disposition, final_classification, etc.)
    """
    raw = (
        row.get("final_classification")
        or row.get("classification")
        or row.get("koi_disposition")
        or row.get("disposition")
        or row.get("label")
        or ""
    )
    s = str(raw).strip().lower()

    # Mapeamentos comuns em Kepler (CONFIRMED / FALSE POSITIVE / CANDIDATE)
    mapping = {
        "confirmed": "planet",
        "planet": "planet",
        "false positive": "not_planet",
        "not_planet": "not_planet",
        "non_planet": "not_planet",
        "candidate": "candidate",
        "cand": "candidate",
        "candidato": "candidate",
    }
    return mapping.get(s) or (s if s in {"planet", "not_planet", "candidate"} else None)


def row_to_model(row: Dict[str, Any]) -> RowMap:
    # Campos “astronômicos” (tenta ambas as convenções)
    rm = RowMap(
        mission=guess_mission(row),
        object_id=guess_object_id(row),
        ra=_to_float(row.get("ra") or row.get("RA")),
        dec=_to_float(row.get("dec") or row.get("DEC")),

        stellar_temperature=_to_float(row.get("stellar_temperature") or row.get("koi_steff")),
        stellar_radius=_to_float(row.get("stellar_radius") or row.get("koi_srad")),
        planet_radius=_to_float(row.get("planet_radius") or row.get("koi_prad")),
        eq_temperature=_to_float(row.get("eq_temperature") or row.get("koi_teq")),
        distance=_to_float(row.get("distance") or row.get("koi_dist") or row.get("dist")),
        surface_gravity=_to_float(row.get("surface_gravity") or row.get("koi_slogg")),
        orbital_period=_to_float(row.get("orbital_period") or row.get("koi_period")),
        insol_flux=_to_float(row.get("insol_flux") or row.get("koi_insol")),
        depth=_to_float(row.get("depth") or row.get("koi_depth")),

        final_classification=map_classification(row),
        final_confidence=_to_float(row.get("final_confidence") or row.get("koi_score")),
        extra=row,  # guarda linha original para auditoria
    )
    return rm


def upsert_row(sess: Session, rm: RowMap) -> None:
    # Verifica se já existe (mission + object_id)
    existing = sess.exec(
        select(ExoplanetCatalog).where(
            ExoplanetCatalog.mission == rm.mission,
            ExoplanetCatalog.object_id == rm.object_id,
        )
    ).first()

    if existing:
        # Atualiza campos principais
        existing.ra = rm.ra
        existing.dec = rm.dec
        existing.stellar_temperature = rm.stellar_temperature
        existing.stellar_radius = rm.stellar_radius
        existing.planet_radius = rm.planet_radius
        existing.eq_temperature = rm.eq_temperature
        existing.distance = rm.distance
        existing.surface_gravity = rm.surface_gravity
        existing.orbital_period = rm.orbital_period
        existing.insol_flux = rm.insol_flux
        existing.depth = rm.depth
        existing.final_classification = rm.final_classification
        existing.final_confidence = rm.final_confidence
        existing.extra = rm.extra
    else:
        rec = ExoplanetCatalog(
            mission=rm.mission,
            object_id=rm.object_id,
            ra=rm.ra,
            dec=rm.dec,
            stellar_temperature=rm.stellar_temperature,
            stellar_radius=rm.stellar_radius,
            planet_radius=rm.planet_radius,
            eq_temperature=rm.eq_temperature,
            distance=rm.distance,
            surface_gravity=rm.surface_gravity,
            orbital_period=rm.orbital_period,
            insol_flux=rm.insol_flux,
            depth=rm.depth,
            final_classification=rm.final_classification,
            final_confidence=rm.final_confidence,
            extra=rm.extra,
        )
        sess.add(rec)


def main() -> int:
    if not os.path.exists(CATALOG_CSV):
        print(f"[ingest] CSV não encontrado em {CATALOG_CSV}", file=sys.stderr)
        return 1

    total = 0
    inserted_or_updated = 0

    with open(CATALOG_CSV, "r", encoding="utf-8") as f, session_scope() as sess:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            rm = row_to_model(row)
            upsert_row(sess, rm)
            if total % 1000 == 0:
                sess.commit()
        sess.commit()

    print(f"[ingest] Processadas {total} linhas de {CATALOG_CSV}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
