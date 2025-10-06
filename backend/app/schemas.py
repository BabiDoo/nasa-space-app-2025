from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class CatalogItem(BaseModel):
    id: int
    mission: str
    object_id: str
    alt_designations: Optional[str] = None
    final_classification: Optional[str] = None
    final_confidence: Optional[float] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    stellar_temperature: Optional[float] = None
    stellar_radius: Optional[float] = None
    planet_radius: Optional[float] = None
    eq_temperature: Optional[float] = None
    distance: Optional[float] = None
    surface_gravity: Optional[float] = None
    orbital_period: Optional[float] = None
    insol_flux: Optional[float] = None
    depth: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True  # pydantic v2

class CatalogPage(BaseModel):
    items: List[CatalogItem]
    page: int
    page_size: int
    total: int
