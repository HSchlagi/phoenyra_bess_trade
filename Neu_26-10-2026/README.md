# Phoenyra FastAPI Stubs (Forecast, Grid, Risk, Credit, Billing)

## Quickstart
```bash
docker compose up -d --build
# Forecast: http://localhost:9500/docs  |  /metrics
# Grid:     http://localhost:9501/docs  |  /metrics
# Risk:     http://localhost:9502/docs  |  /metrics
# Credit:   http://localhost:9503/docs  |  /metrics
# Billing:  http://localhost:9504/docs  |  /metrics
```

### Notes
- Endpoints entsprechen den OpenAPI-Spezifikationen (Skeletons).
- Prometheus-Exporter sind in jedem Service aktiviert (`/metrics`).
- Speicher ist in-memory (PoC) — bitte später gegen Postgres/Redis austauschen.
