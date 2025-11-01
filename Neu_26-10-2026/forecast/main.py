from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title="Phoenyra Forecast API", version="0.1.0")

# In-memory storage
JOBS = {}
C_FORECAST_JOBS = Counter("pho_forecast_jobs_total", "Count of forecast jobs", ["type"])
G_PRICE = Gauge("pho_forecast_price_eur_mwh", "Forecast price", ["horizon"])
G_LOAD = Gauge("pho_forecast_load_mw", "Forecast load", ["horizon"])
G_SOLAR = Gauge("pho_forecast_solar_mw", "Forecast solar", ["horizon"])
G_WIND = Gauge("pho_forecast_wind_mw", "Forecast wind", ["horizon"])

class ForecastRequest(BaseModel):
    area: str = "AT"
    assets: List[str] = []
    horizon_h: int = 24
    granularity_min: int = 15
    features: Optional[dict] = None

class IntradayRequest(BaseModel):
    area: str = "AT"
    horizon_h: int = 12
    granularity_min: int = 15

@app.post("/forecast/dayahead", status_code=202)
def forecast_dayahead(req: ForecastRequest):
    C_FORECAST_JOBS.labels("dayahead").inc()
    job_id = uuid4().hex
    start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    series = []
    for i in range(0, req.horizon_h*60, req.granularity_min):
        ts = start + timedelta(minutes=i)
        price = 60 + (i % 120) * 0.1  # dummy pattern
        load = 5000 + (i % 180) * 5
        solar = max(0.0, 1000.0 - abs(360 - (i % 720)) * 3)
        wind = 800 + ((i * 7) % 300)
        series.append({
            "ts": ts.isoformat() + "Z",
            "price_eur_mwh": round(price, 2),
            "load_mw": round(load, 1),
            "gen_solar_mw": round(solar, 1),
            "gen_wind_mw": round(wind, 1),
            "soc_target_pct": 50 + (i % 50) * 0.5
        })
    JOBS[job_id] = {"status": "done", "series": series}
    # set last points to gauges
    if series:
        G_PRICE.labels(f"{req.horizon_h}h").set(series[-1]["price_eur_mwh"])
        G_LOAD.labels(f"{req.horizon_h}h").set(series[-1]["load_mw"])
        G_SOLAR.labels(f"{req.horizon_h}h").set(series[-1]["gen_solar_mw"])
        G_WIND.labels(f"{req.horizon_h}h").set(series[-1]["gen_wind_mw"])
    return {"job_id": job_id}

@app.post("/forecast/intraday", status_code=202)
def forecast_intraday(req: IntradayRequest):
    C_FORECAST_JOBS.labels("intraday").inc()
    job_id = uuid4().hex
    start = datetime.utcnow().replace(second=0, microsecond=0)
    series = []
    for i in range(0, req.horizon_h*60, req.granularity_min):
        ts = start + timedelta(minutes=i)
        series.append({
            "ts": ts.isoformat() + "Z",
            "price_eur_mwh": 50 + (i % 90) * 0.2,
            "load_mw": 5200 + (i % 120) * 4,
            "gen_solar_mw": 500.0,
            "gen_wind_mw": 900.0,
            "soc_target_pct": 55.0
        })
    JOBS[job_id] = {"status":"done","series":series}
    return {"job_id": job_id}

@app.get("/forecast/status/{job_id}")
def forecast_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
