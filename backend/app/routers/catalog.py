# backend/app/routers/catalog.py
from typing import Optional, Dict, Any, List, Tuple
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlmodel import select, func, col
from sqlmodel import Session

from app.db import get_session
from app.models import ExoplanetCatalog
from app.schemas import CatalogItem, CatalogPage

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def build_numeric_filters(
    model,
    ranges: Dict[str, Tuple[Optional[float], Optional[float]]]
):
    """
    Constrói clausulas .where() a partir de um dicionário de ranges numéricos.
    Ignora campos que não existem no modelo.
    """
    clauses = []
    for field, (min_v, max_v) in ranges.items():
        if not hasattr(model, field):
            continue
        column = getattr(model, field)
        if min_v is not None:
            clauses.append(column >= min_v)
        if max_v is not None:
            clauses.append(column <= max_v)
    return clauses


@router.get("", response_model=CatalogPage)
def list_catalog(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),

    # Filtros de igualdade
    mission: Optional[str] = Query(None, description="kepler | k2 | tess"),
    final_classification: Optional[str] = Query(None, description="planet | not_planet | candidate"),
    object_id: Optional[str] = Query(None),

    # Ranges numéricos (min_/max_)
    min_stellar_temperature: Optional[float] = None,
    max_stellar_temperature: Optional[float] = None,

    min_stellar_radius: Optional[float] = None,
    max_stellar_radius: Optional[float] = None,

    min_planet_radius: Optional[float] = None,
    max_planet_radius: Optional[float] = None,

    min_eq_temperature: Optional[float] = None,
    max_eq_temperature: Optional[float] = None,

    min_distance: Optional[float] = None,
    max_distance: Optional[float] = None,

    min_surface_gravity: Optional[float] = None,
    max_surface_gravity: Optional[float] = None,

    min_orbital_period: Optional[float] = None,
    max_orbital_period: Optional[float] = None,

    min_insol_flux: Optional[float] = None,
    max_insol_flux: Optional[float] = None,

    min_depth: Optional[float] = None,
    max_depth: Optional[float] = None,

    min_final_confidence: Optional[float] = None,
    max_final_confidence: Optional[float] = None,

    # Ordenação simples
    order_by: Optional[str] = Query(None, description="campo para ordenar, ex.: planet_radius"),
    order_dir: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="asc | desc"),

    sess: Session = Depends(get_session),
):
    """
    Lista do catálogo com filtros, paginação e ordenação.
    """
    stmt = select(ExoplanetCatalog)

    # Igualdade
    if mission:
        stmt = stmt.where(ExoplanetCatalog.mission == mission.lower().strip())
    if final_classification:
        fc = final_classification.lower().strip()
        if fc not in {"planet", "not_planet", "candidate"}:
            raise HTTPException(400, detail="final_classification inválido. Use planet|not_planet|candidate.")
        stmt = stmt.where(ExoplanetCatalog.final_classification == fc)
    if object_id:
        stmt = stmt.where(ExoplanetCatalog.object_id == object_id)

    # Ranges numéricos (só aplica os que existem no modelo)
    ranges = {
        "stellar_temperature": (min_stellar_temperature, max_stellar_temperature),
        "stellar_radius": (min_stellar_radius, max_stellar_radius),
        "planet_radius": (min_planet_radius, max_planet_radius),
        "eq_temperature": (min_eq_temperature, max_eq_temperature),
        "distance": (min_distance, max_distance),
        "surface_gravity": (min_surface_gravity, max_surface_gravity),
        "orbital_period": (min_orbital_period, max_orbital_period),
        "insol_flux": (min_insol_flux, max_insol_flux),
        "depth": (min_depth, max_depth),
        "final_confidence": (min_final_confidence, max_final_confidence),
    }
    for clause in build_numeric_filters(ExoplanetCatalog, ranges):
        stmt = stmt.where(clause)

    # Total (para paginação)
    total = sess.exec(
        select(func.count()).select_from(stmt.subquery())
    ).one()

    # Ordenação
    if order_by and hasattr(ExoplanetCatalog, order_by):
        order_col = getattr(ExoplanetCatalog, order_by)
        stmt = stmt.order_by(order_col.asc() if order_dir == "asc" else order_col.desc())
    else:
        # Default: mais confiantes primeiro, depois maior raio planetário
        stmt = stmt.order_by(
            ExoplanetCatalog.final_confidence.desc().nulls_last(),
            ExoplanetCatalog.planet_radius.desc().nulls_last(),
        )

    # Paginação
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    rows = sess.exec(stmt).all()

    items: List[CatalogItem] = [
        CatalogItem.model_validate(r) for r in rows  # Pydantic v2 + SQLModel -> OK
    ]

    return CatalogPage(
        page=page,
        page_size=page_size,
        total=total,
        items=items,
    )


@router.get("/{id}", response_model=CatalogItem)
def get_catalog_item(
    id: int,
    sess: Session = Depends(get_session),
):
    row = sess.get(ExoplanetCatalog, id)
    if not row:
        raise HTTPException(404, detail="Registro não encontrado.")
    return CatalogItem.model_validate(row)
