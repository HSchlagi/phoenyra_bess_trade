# Phoenyra BESS Trading & Optimization Stack — ULTRA OMEGA Documentation (v2)

## Overview
The **Phoenyra ULTRA OMEGA Stack** represents the final integrated version of the trading and BESS optimization framework.  
It unifies the ULTRA MAX++++ foundation with live telemetry feedback, policy webhooks, Grafana visualization, and signature verification endpoints.

---

## Newly Added in ULTRA OMEGA
| Feature | Description |
|----------|--------------|
| **JWKS Signature Verification** | Standardized WS-HMAC discovery and verification examples for Python & Node.js clients |
| **Grafana Dashboard Template** | Prebuilt JSON dashboard for Prometheus metrics: marks, VWAP, PnL, exposure, SoC |
| **Policy Reload Webhook** | `/admin/policy/reload` triggers hot reload remotely (instead of mtime polling) |
| **BESS Telemetry Binding** | `/telemetry/bess` accepts SoC, Power, and Temp metrics → adjusts throttle & exposure dynamically |
| **Grafana Integration & Alerts** | Prometheus metrics exported to Grafana for visual analytics and automated alerting |

---

## 1. JWKS Signature Verification Example

### Python Client
```python
import json, hmac, hashlib, base64, time, websockets, asyncio

async def verify_message(msg, key):
    meta = msg["meta"]
    data = json.dumps(msg["data"], separators=(',',':'))
    body = f"{meta['ts']}|{data}".encode()
    calc = base64.b64encode(hmac.new(key.encode(), body, hashlib.sha256).digest()).decode()
    assert calc == meta["sig"], "Invalid HMAC signature"
    print("Signature OK")

async def listen():
    async with websockets.connect("ws://localhost:9000/ws/orders?api_key=<KEY>") as ws:
        async for raw in ws:
            msg = json.loads(raw)
            await verify_message(msg, "phoenyra_demo_secret")

asyncio.run(listen())
```

### Node.js Client
```js
import crypto from "crypto";
function verify(meta, data, secret) {
  const body = meta.ts + "|" + JSON.stringify(data);
  const calc = crypto.createHmac("sha256", secret).update(body).digest("base64");
  if (calc !== meta.sig) throw new Error("Invalid HMAC");
  return true;
}
```

---

## 2. Grafana Dashboard (Prometheus Data Source)

**Metrics Exposed**
| Metric | Description |
|---------|--------------|
| `pho_mark{market}` | Current mark price |
| `pho_ema{market}` | Exponential moving average |
| `pho_vwap{market}` | Volume-weighted average price |
| `pho_price_events_total{market}` | Count of price updates |
| `pho_exposure_energy{market}` | Active BESS exposure (MWh) |
| `pho_exposure_notional{market}` | Active notional exposure (€) |
| `pho_soc_percent{market}` | BESS state of charge (live) |

**Grafana Panels (JSON Extract)**:
```json
{
  "panels": [
    {"type": "graph", "title": "Mark & EMA", "targets": [{"expr": "pho_mark"}]},
    {"type": "graph", "title": "VWAP (15min)", "targets": [{"expr": "pho_vwap"}]},
    {"type": "gauge", "title": "BESS SoC (%)", "targets": [{"expr": "pho_soc_percent"}]},
    {"type": "timeseries", "title": "Exposure (MWh)", "targets": [{"expr": "pho_exposure_energy"}]},
    {"type": "timeseries", "title": "PnL (€)", "targets": [{"expr": "pho_pnl_realized"}]}
  ]
}
```

**Alert Rule Example (Grafana Alerting)**
```yaml
name: "Low SoC Warning"
expr: pho_soc_percent < 15
for: 5m
labels:
  severity: warning
annotations:
  summary: "Battery SoC below 15%"
```

---

## 3. Policy Reload Webhook

**Endpoint**
```
POST /admin/policy/reload
```
Reloads `policy/policy.yaml` dynamically in memory, replacing file modification checks.  
Webhook can be triggered from CI/CD, Grafana alerts, or manual n8n flows.

**Example:**
```bash
curl -X POST http://localhost:9000/admin/policy/reload   -H "X-API-KEY: <ADMIN_KEY>"
```

---

## 4. BESS Telemetry Binding

**Endpoint**
```
POST /telemetry/bess
```
**Body Example:**
```json
{
  "soc_percent": 72.5,
  "active_power_mw": 3.8,
  "temperature_c": 28.3
}
```
System auto-adjusts exposure and throttling parameters:
- `soc_percent` < 15% → disable BUY orders (low reserve)
- `soc_percent` > 90% → disable SELL orders (capacity full)
- `temperature_c` > 40 °C → reduce per-market RPS by 50%

Stored in Redis keys:
```
telemetry:soc
telemetry:power
telemetry:temp
```

Metrics exported as:
```
pho_soc_percent
pho_temp_celsius
pho_bess_power_mw
```

---

## 5. Grafana Integration & Visualization

**Recommended Prometheus Scrape Config**
```yaml
scrape_configs:
  - job_name: phoenyra
    static_configs:
      - targets: ['exchange:9000']
```

**Grafana Import**
1. Open Grafana → Dashboards → Import
2. Paste JSON from above
3. Select Prometheus as data source
4. Save & Reload

**Alert Channels**
- Email (SMTP)
- Telegram Bot (via Grafana OnCall or n8n)
- Webhook → `/admin/policy/reload` (for automated rule tightening)

---

## Final Deployment Stack

**Compose Services**
- `exchange`: FastAPI trading engine
- `redis`: pricefeed & cache
- `prometheus`: metrics backend
- `grafana`: visualization
- `n8n`: orchestration (automation + alerting)

**Run**
```bash
docker compose up -d --build
```
Then open:
- Exchange API: [http://localhost:9000/docs](http://localhost:9000/docs)
- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:3000](http://localhost:3000)

---

**Author:** Phoenyra Engineering  
**Version:** 2025‑10‑24 (ULTRA OMEGA)  
**Format:** Markdown (`.md`) — ready for Cursor AI integration
