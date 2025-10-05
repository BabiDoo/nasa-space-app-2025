# ML Microservice (FastAPI)

Endpoints:
- `GET /health`
- `GET /datasets`
- `GET /metrics`
- `GET /tests?mission=&model=&balanced=&metric=`
- `GET /final?metric=f1_weighted&balanced=true`
- `GET /compare?metric=f1_weighted&balanced=true`
- `POST /predict`

`POST /predict` body:

```json
{
  "mission": "kepler|k2|tess",
  "object_id": "optional",
  "features": {
    "longitude": 0, "latitude": 0, "stellar_temperature": 0, "stellar_radius": 0,
    "planet_radius": 0, "eq_temperature": 0, "distance": 0, "stellar_sur_gravity": 0
  }
}
```
