from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import math

app = FastAPI(title="Phoenyra Risk API", version="0.1.0")

G_VAR99 = Gauge("pho_risk_var_99_eur", "Portfolio VaR 99% (EUR)")
G_VAR95 = Gauge("pho_risk_var_95_eur", "Portfolio VaR 95% (EUR)")
G_UTIL = Gauge("pho_risk_limit_utilization_pct", "Risk limit utilization (%)")

class VarReq(BaseModel):
    horizon_d: int = 1
    confidence: float = 0.99
    paths: int = 10000

@app.post("/risk/var")
def risk_var(r: VarReq):
    # simplified dummy VaR using sqrt-time scaling
    base_var = 100000.0  # EUR
    var = base_var * math.sqrt(r.horizon_d)
    es = var * 1.2
    if r.confidence >= 0.99:
        G_VAR99.set(var)
    else:
        G_VAR95.set(var)
    G_UTIL.set(min(100.0, var / 250000.0 * 100.0))
    return {"var_eur": round(var, 2), "es_eur": round(es, 2)}

@app.get("/risk/limits")
def risk_limits():
    return {"portfolio":{"PnL_Day_Limit_EUR":500000,"VaR_99_Limit_EUR":250000}}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
