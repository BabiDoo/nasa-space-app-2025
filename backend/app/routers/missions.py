from fastapi import APIRouter

router = APIRouter(prefix="/api/missions", tags=["missions"])

DATA = {
  "kepler": {
    "title": "Kepler",
    "subtitle": "First Mission",
    "summary": "Space telescope launched in 2009 focused on the transit method; discovered thousands of exoplanets; later adapted to K2 and retired in 2018.",
    "links": []
  },
  "k2": {
    "title": "K2",
    "subtitle": "Kepler K2 Mission",
    "summary": "Continuation of Kepler using innovative pointing to observe many fields and identify hundreds of new candidates.",
    "links": []
  },
  "tess": {
    "title": "TESS",
    "subtitle": "Transiting Exoplanet Survey Satellite",
    "summary": "All-sky bright-star transit survey (since 2018); thousands of candidates for follow-up and validation.",
    "links": []
  }
}

@router.get("")
def get_missions():
    return DATA
