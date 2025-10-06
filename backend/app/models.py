from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON

class ExoplanetCatalog(SQLModel, table=True):
    __tablename__ = "exoplanet_catalog"

    id: Optional[int] = Field(default=None, primary_key=True)

    mission: str = Field(index=True)                  # kepler|k2|tess
    object_id: str = Field(index=True)
    alt_designations: Optional[str] = Field(default=None)

    final_classification: Optional[str] = Field(default=None, index=True)  # planet|non_planet|candidate
    final_confidence: Optional[float] = 0.0

    longitude: Optional[float] = Field(default=None, index=True)  # ex.: RA/ecl. lon
    latitude: Optional[float] = Field(default=None, index=True)   # ex.: DEC/ecl. lat

    stellar_temperature: Optional[float] = Field(default=None, index=True)
    stellar_radius: Optional[float] = Field(default=None, index=True)
    planet_radius: Optional[float] = Field(default=None, index=True)
    eq_temperature: Optional[float] = Field(default=None, index=True)
    distance: Optional[float] = Field(default=None, index=True)
    surface_gravity: Optional[float] = Field(default=None, index=True)  # logg
    orbital_period: Optional[float] = Field(default=None, index=True)
    insol_flux: Optional[float] = Field(default=None, index=True)
    depth: Optional[float] = Field(default=None, index=True)

    extra: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
