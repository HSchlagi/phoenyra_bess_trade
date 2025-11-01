from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Phoenyra Credit API", version="0.1.0")

CREDIT = {}
G_EXPO = Gauge("pho_credit_exposure_eur", "Exposure by counterparty (EUR)", ["cp"])

class CreditLimitReq(BaseModel):
    counterparty: str
    limit_eur: float

@app.post("/credit/limit")
def credit_limit(req: CreditLimitReq):
    rec = CREDIT.get(req.counterparty) or {"limit_eur": req.limit_eur, "exposure_eur": 0.0}
    rec["limit_eur"] = req.limit_eur
    CREDIT[req.counterparty] = rec
    return {"status":"OK","counterparty": req.counterparty, "limit_eur": req.limit_eur}

@app.get("/credit/exposure")
def credit_exposure(counterparty: str):
    rec = CREDIT.get(counterparty) or {"limit_eur": 100000.0, "exposure_eur": 25000.0}
    util = (rec["exposure_eur"] / rec["limit_eur"])*100.0 if rec["limit_eur"]>0 else 0.0
    G_EXPO.labels(counterparty).set(rec["exposure_eur"])
    return {"counterparty": counterparty, "exposure_eur": rec["exposure_eur"], "utilization_pct": round(util,2)}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
