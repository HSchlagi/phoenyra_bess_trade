from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime
import random

app = FastAPI(title="Phoenyra Grid API", version="0.1.0")

G_FREQ = Gauge("pho_grid_freq_hz", "Grid frequency (Hz)")
G_LOAD = Gauge("pho_grid_load_mw", "Grid load (MW)")

@app.get("/grid/state")
def grid_state(area: str = "AT"):
    freq = round(49.98 + random.uniform(-0.03, 0.03), 3)
    load = int(7000 + random.uniform(-500, 500))
    G_FREQ.set(freq); G_LOAD.set(load)
    return {"area": area, "freq_hz": freq, "load_mw": load, "tie_lines":[{"name":"AT-DE","flow_mw":1200},{"name":"AT-CZ","flow_mw":-300}], "congestion_index": 0.15}

@app.get("/grid/constraints")
def constraints(window: str = "PT1H"):
    now = datetime.utcnow().isoformat() + "Z"
    return {"items":[{"ts":now,"type":"redispatch","detail":"North-East corridor maintenance"}]}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
