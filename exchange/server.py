from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header, Body
from pydantic import BaseModel, validator
from typing import Optional, Literal, Dict, List, Tuple
from datetime import datetime
import os, json, sqlite3, redis, time, yaml, uuid, asyncio, hmac, hashlib, base64

from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Phoenyra Exchange v1.3 (ULTRA OMEGA+)")

DB_PATH = os.getenv("SQLITE_PATH","/app/exchange.db")
REDIS_HOST = os.getenv("REDIS_HOST","redis"); REDIS_PORT=int(os.getenv("REDIS_PORT","6379")); REDIS_DB=int(os.getenv("REDIS_DB","0"))
POLICY_PATH = os.getenv("POLICY_PATH","/app/policy/policy.yaml")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0); conn.row_factory = sqlite3.Row; return conn

def init_db():
    con=db(); c=con.cursor()
    c.executescript("""    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, api_key TEXT UNIQUE, role TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, user_key TEXT, market TEXT, side TEXT, type TEXT, tif TEXT, p_limit REAL, qty REAL, d_start TEXT, d_end TEXT, status TEXT, filled REAL, ts TEXT);
    CREATE TABLE IF NOT EXISTS trades(id TEXT PRIMARY KEY, order_id TEXT, user_key TEXT, executed REAL, price REAL, ts TEXT, market TEXT, side TEXT);
    CREATE TABLE IF NOT EXISTS orderbook_history(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, market TEXT, bids TEXT, asks TEXT);
    CREATE TABLE IF NOT EXISTS market_price_history(id INTEGER PRIMARY KEY AUTOINCREMENT, market TEXT, mark REAL, ema REAL, vwap REAL, timestamp INTEGER, ts TEXT);
    CREATE INDEX IF NOT EXISTS idx_market_price_history_market_ts ON market_price_history(market, timestamp);
    """    )
    con.commit(); con.close()
init_db()

# ---- Policy hot-reload + webhook ----
_POLICY = {"mtime":0, "data":{}}
def load_policy(force=False):
    try:
        st = os.stat(POLICY_PATH).st_mtime
        if force or st != _POLICY["mtime"]:
            with open(POLICY_PATH) as f:
                _POLICY["data"] = yaml.safe_load(f) or {}
            _POLICY["mtime"] = st
    except FileNotFoundError:
        _POLICY["data"] = {}
    return _POLICY["data"]

@app.post("/admin/policy/reload")
def policy_reload():
    pol = load_policy(force=True)
    return {"status":"OK","version":pol.get("version")}

# ---- HMAC keys (rotation + discovery) ----
def _decode_secret(s):
    try:
        return base64.b64decode(s)
    except Exception:
        try:
            return bytes.fromhex(s)
        except Exception:
            return s.encode("utf-8")

def parse_hmac_keys():
    raw = os.getenv("HMAC_KEYS_JSON")
    if raw:
        arr = json.loads(raw)
        out = {k["kid"]: _decode_secret(k["secret"]) for k in arr}
        return out, arr[0]["kid"]
    # fallback single key
    sec = os.getenv("HMAC_SECRET","phoenyra_demo_secret")
    return {"default": _decode_secret(sec)}, "default"

HMAC_KEYS, ACTIVE_KID = parse_hmac_keys()

@app.get("/.well-known/ws-keys")
def ws_keys():
    arr=[]
    for kid, key in HMAC_KEYS.items():
        fp = hashlib.sha256(key).hexdigest()[:16]
        arr.append({"kid":kid, "alg":"HMAC-SHA256", "fingerprint":fp})
    return {"keys": arr, "active": ACTIVE_KID}

@app.post("/admin/ws_hmac/rotate")
def ws_rotate(kid: str, secret: str):
    global ACTIVE_KID, HMAC_KEYS
    HMAC_KEYS[kid] = _decode_secret(secret)
    ACTIVE_KID = kid
    return {"status":"OK","active":kid}

# ---- Metrics ----
G_MARK = Gauge("pho_mark", "Mark price", ["market"])
G_EMA = Gauge("pho_ema", "EMA price", ["market"])
G_VWAP = Gauge("pho_vwap", "VWAP price", ["market"])
C_EVENTS = Counter("pho_price_events_total", "Price events", ["market"])

G_SOC = Gauge("pho_soc_percent", "BESS State of Charge %", [])
G_TEMP = Gauge("pho_temp_celsius", "BESS temperature (C)", [])
G_PWR = Gauge("pho_bess_power_mw", "BESS active power (MW)", [])

G_EXPO_E = Gauge("pho_exposure_energy", "Exposure energy (MWh)", ["market"])
G_EXPO_N = Gauge("pho_exposure_notional", "Exposure notional (EUR)", ["market"])
G_PNL_REAL = Gauge("pho_pnl_realized", "Realized PnL (EUR)", ["market"])

# ---- Auth (demo) ----
class User(BaseModel):
    name: str="heinz"; api_key: str="demo"; role: str="trader"; status: str="ACTIVE"
async def get_user(x_api_key: Optional[str] = Header(default=None)) -> User:
    return User()

# ---- Book & exposure ----
BOOK: Dict[str, Dict[str, List[Tuple[float,float]]]] = {}
def ensure_market(m): 
    if m not in BOOK: BOOK[m]={"bids":[], "asks":[]}
def persist_book(market:str):
    con=db(); c=con.cursor()
    c.execute("INSERT INTO orderbook_history(ts,market,bids,asks) VALUES(?,?,?,?)",
              (datetime.utcnow().isoformat(), market, json.dumps(BOOK[market]["bids"][:50]), json.dumps(BOOK[market]["asks"][:50])))
    con.commit(); con.close()

def exposure_of(api_key: str):
    con=db(); c=con.cursor()
    c.execute("SELECT market, side, qty, filled, p_limit FROM orders WHERE status!='CANCELLED'")
    netE={}; netN={}
    for row in c.fetchall():
        m=row["market"]; rem=row["qty"]-row["filled"]; s=1 if row["side"]=="BUY" else -1
        netE[m]=netE.get(m,0.0)+s*rem; netN[m]=netN.get(m,0.0)+abs(rem*(row["p_limit"] or 0.0))
    con.close()
    for m,v in netE.items(): G_EXPO_E.labels(m).set(float(v))
    for m,v in netN.items(): G_EXPO_N.labels(m).set(float(v))
    return {"energy":netE,"notional":netN}

# ---- Telemetry with SoC-driven scaling ----
class TelemetryIn(BaseModel):
    soc_percent: float
    active_power_mw: float
    temperature_c: float
@app.post("/telemetry/bess")
def telemetry(b: TelemetryIn):
    r.set("telemetry:soc", b.soc_percent)
    r.set("telemetry:power", b.active_power_mw)
    r.set("telemetry:temp", b.temperature_c)
    G_SOC.set(b.soc_percent); G_PWR.set(b.active_power_mw); G_TEMP.set(b.temperature_c)
    return {"status":"OK"}

# ---- REST API für externe BESS-Systeme ----
@app.post("/api/bess/telemetry")
def external_telemetry(api_key: str = Header(None)):
    """REST API für externe BESS-Systeme"""
    # API-Key Validierung
    expected_key = os.getenv("BESS_API_KEY", "bess_telemetry_key")
    if not api_key or api_key != expected_key:
        return {"error": "Unauthorized", "status": 401}
    
    try:
        data = request.get_json()
        if not data:
            return {"error": "No JSON data provided", "status": 400}
        
        # Telemetrie-Daten validieren und verarbeiten
        telemetry_data = TelemetryIn(
            soc_percent=float(data.get("soc_percent", 0)),
            active_power_mw=float(data.get("active_power_mw", 0)),
            temperature_c=float(data.get("temperature_c", 0))
        )
        
        # An interne Telemetrie-Funktion weiterleiten
        r.set("telemetry:soc", telemetry_data.soc_percent)
        r.set("telemetry:power", telemetry_data.active_power_mw)
        r.set("telemetry:temp", telemetry_data.temperature_c)
        G_SOC.set(telemetry_data.soc_percent)
        G_PWR.set(telemetry_data.active_power_mw)
        G_TEMP.set(telemetry_data.temperature_c)
        
        return {
            "status": "OK",
            "message": "Telemetrie erfolgreich aktualisiert",
            "data": {
                "soc_percent": telemetry_data.soc_percent,
                "active_power_mw": telemetry_data.active_power_mw,
                "temperature_c": telemetry_data.temperature_c,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        return {"error": f"Telemetrie-Fehler: {str(e)}", "status": 500}

@app.get("/api/bess/status")
def get_bess_status():
    """Aktuelle BESS-Status abrufen"""
    try:
        soc = float(r.get("telemetry:soc") or 0.0)
        power = float(r.get("telemetry:power") or 0.0)
        temp = float(r.get("telemetry:temp") or 0.0)
        
        return {
            "soc_percent": soc,
            "active_power_mw": power,
            "temperature_c": temp,
            "timestamp": datetime.now().isoformat(),
            "status": "online" if soc > 0 else "offline"
        }
    except Exception as e:
        return {"error": f"Status-Fehler: {str(e)}", "status": 500}

def soc_limits():
    soc = float(r.get("telemetry:soc") or 100.0)
    temp = float(r.get("telemetry:temp") or 25.0)
    allow_buy = soc >= 15.0
    allow_sell = soc <= 90.0
    rps_scale = 0.5 if temp>40.0 else 1.0
    return allow_buy, allow_sell, rps_scale, soc, temp

# ---- Throttle with SoC scaling ----
def throttle(api_key:str, market:str):
    pol = load_policy()
    base = pol.get("per_market_rps",{}).get(market, 120)
    allow_buy, allow_sell, scale, *_ = soc_limits()
    budget = max(1, int(base*scale))
    now_min=int(time.time())//60; k=f"rps:{api_key}:{market}:{now_min}"
    cnt=r.incr(k); r.expire(k,70)
    remaining = max(0, budget - cnt)
    if cnt>budget: raise HTTPException(429,f"per-market throttle exceeded for {market} (scaled by SoC/temp)")
    return remaining

# ---- WS with HMAC signatures ----
WS_BOOK=[]; WS_TRADES=[]; WS_ORDERS: Dict[str, List]= {}
from fastapi import WebSocket

def sign_payload(payload: dict) -> dict:
    kid = ACTIVE_KID
    body = json.dumps(payload, separators=(',',':'))
    ts = str(int(time.time()*1000))
    mac = hmac.new(HMAC_KEYS[kid], (ts + "|" + body).encode(), hashlib.sha256).digest()
    sig = base64.b64encode(mac).decode()
    return {"ts": ts, "sig": sig, "algo":"HMAC-SHA256", "key_id": kid}

async def ws_send(ws, payload: dict, meta_extra: dict = None):
    meta = sign_payload(payload)
    if meta_extra: meta.update(meta_extra)
    await ws.send_json({"meta": meta, "data": payload})

@app.websocket("/ws/book/{market}")
async def ws_book(ws: WebSocket, market: str):
    await ws.accept(); WS_BOOK.append(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        if ws in WS_BOOK: WS_BOOK.remove(ws)

@app.websocket("/ws/trades")
async def ws_trades(ws: WebSocket):
    await ws.accept(); WS_TRADES.append(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        if ws in WS_TRADES: WS_TRADES.remove(ws)

@app.websocket("/ws/orders")
async def ws_orders(ws: WebSocket):
    api_key = ws.query_params.get("api_key") or "demo"
    await ws.accept()
    WS_ORDERS.setdefault(api_key, []).append(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        if ws in WS_ORDERS.get(api_key, []): WS_ORDERS[api_key].remove(ws)

async def emit_book(market:str):
    payload={"type":"book","market":market,"bids":BOOK.get(market,{}).get("bids",[])[:10],"asks":BOOK.get(market,{}).get("asks",[])[:10]}
    for ws in list(WS_BOOK):
        try: await ws_send(ws, payload)
        except: 
            try: WS_BOOK.remove(ws)
            except: pass

async def emit_trade(trade:dict):
    payload={"type":"trade", **trade}
    for ws in list(WS_TRADES):
        try: await ws_send(ws, payload)
        except:
            try: WS_TRADES.remove(ws)
            except: pass

async def emit_order(api_key:str, event:dict):
    arr = WS_ORDERS.get(api_key, [])
    # include throttle remaining & short exposure snapshot
    remaining = throttle_remaining_cached(api_key, event.get("market",""))
    snapshot = exposure_of(api_key)
    for ws in list(arr):
        try: await ws_send(ws, {"type":"order", **event}, {"throttle_remaining": remaining, "exposure_snapshot": snapshot})
        except:
            try: arr.remove(ws)
            except: pass
    WS_ORDERS[api_key]=arr

def throttle_remaining_cached(api_key:str, market:str):
    pol = load_policy()
    base = pol.get("per_market_rps",{}).get(market, 120)
    _, _, scale, *_ = soc_limits()
    budget = max(1, int(base*scale))
    now_min=int(time.time())//60; k=f"rps:{api_key}:{market}:{now_min}"
    cnt = int(r.get(k) or 0)
    return max(0, budget - cnt)

# ---- Pricefeed + metrics ----
@app.post("/admin/pricefeed/push")
def pricefeed_push(market: str, price: float, volume: float = 1.0):
    key=f"price:stream:{market}"
    ts_ms = int(time.time()*1000)
    r.xadd(key, {"p": price, "v": volume, "ts": ts_ms}, maxlen=10000, approximate=True)
    r.set(f"price:mark:{market}", price)
    # EMA
    prev = r.get(f"price:ema:{market}"); prev = float(prev) if prev else price
    alpha = 0.2
    ema = alpha*price + (1-alpha)*prev
    r.set(f"price:ema:{market}", ema)
    # VWAP
    entries = r.xrevrange(key, count=96)
    num=0.0; den=0.0
    for _, fields in entries:
        p=float(fields[b"p"].decode()); v=float(fields.get(b"v",b"1").decode())
        num += p*v; den += v
    vwap = (num/den) if den>0 else price
    r.set(f"price:vwap:{market}", vwap)
    
    # Persist to SQLite for history - use single connection and transaction to avoid locks
    try:
        con=db(); c=con.cursor()
        # Insert new price data
        c.execute("INSERT INTO market_price_history(market, mark, ema, vwap, timestamp, ts) VALUES(?,?,?,?,?,?)",
                  (market, price, ema, vwap, ts_ms, datetime.utcnow().isoformat()))
        # Keep only last 90 days of data (cleanup old entries for long-term analysis)
        cutoff_ts = ts_ms - (90 * 24 * 60 * 60 * 1000)
        c.execute("DELETE FROM market_price_history WHERE timestamp < ?", (cutoff_ts,))
        # Commit both operations in one transaction
        con.commit(); con.close()
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            # Database is locked - skip this update, will retry on next price feed
            print(f"WARNING: Database locked, skipping price history update (will retry): {e}")
        else:
            import traceback
            print(f"ERROR persisting price history: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    except Exception as e:
        import traceback
        print(f"ERROR persisting price history: {e}")
        print(f"Traceback: {traceback.format_exc()}")
    
    G_MARK.labels(market).set(price); G_EMA.labels(market).set(ema); G_VWAP.labels(market).set(vwap); C_EVENTS.labels(market).inc()
    return {"status":"OK"}

@app.get("/market/prices")
def get_market_prices(market: str = "epex_at"):
    """Get current market prices from Redis and persist to database for long-term analysis"""
    try:
        mark = round(float(r.get(f"price:mark:{market}") or 0.0), 2)
        ema = round(float(r.get(f"price:ema:{market}") or mark), 2)
        vwap = round(float(r.get(f"price:vwap:{market}") or mark), 2)
        
        # CRITICAL: Persist to database for long-term analysis
        # This ensures data is available for /market/history/longterm endpoint
        # Debug: Log what we're trying to persist
        print(f"🔍 Persistence check: market={market}, mark={mark:.2f}, ema={ema:.2f}, vwap={vwap:.2f}, condition={mark > 0 and mark < 1000}")
        if mark > 0 and mark < 1000:  # Only persist valid prices
            try:
                ts_ms = int(time.time() * 1000)
                con = db()
                c = con.cursor()
                # Check if data for this timestamp already exists (avoid duplicates)
                # Round timestamp to nearest second to avoid duplicate inserts
                ts_second = (ts_ms // 1000) * 1000
                c.execute("""
                    SELECT COUNT(*) FROM market_price_history 
                    WHERE market = ? AND timestamp >= ? AND timestamp < ?
                """, (market, ts_second, ts_second + 1000))
                exists = c.fetchone()[0] > 0
                
                if not exists:
                    # Insert new price data only if it doesn't exist
                    c.execute("""
                        INSERT INTO market_price_history(market, mark, ema, vwap, timestamp, ts) 
                        VALUES(?,?,?,?,?,?)
                    """, (market, mark, ema, vwap, ts_ms, datetime.utcnow().isoformat()))
                    
                    # Debug: Log successful insert (every insert for now to debug)
                    c.execute("SELECT COUNT(*) FROM market_price_history WHERE market = ?", (market,))
                    total_count = c.fetchone()[0]
                    print(f"✅ Market price persisted: market={market}, mark={mark:.2f}, ema={ema:.2f}, vwap={vwap:.2f}, timestamp={ts_ms}, total_records={total_count}")
                else:
                    print(f"⚠️ Duplicate timestamp skipped: market={market}, timestamp={ts_ms}")
                
                # Keep only last 90 days of data (cleanup old entries)
                cutoff_ts = ts_ms - (90 * 24 * 60 * 60 * 1000)
                c.execute("DELETE FROM market_price_history WHERE timestamp < ?", (cutoff_ts,))
                deleted = c.rowcount
                if deleted > 0:
                    print(f"Cleaned up {deleted} old market_price_history records (older than 90 days)")
                con.commit()
                con.close()
            except Exception as db_error:
                # Log but don't fail the request if database write fails
                import traceback
                print(f"❌ Warning: Failed to persist market price to database: {db_error}")
                print(f"❌ Traceback: {traceback.format_exc()}")
        else:
            print(f"⚠️ Skipping persistence: mark={mark:.2f} is not in valid range (0 < mark < 1000)")
        
        # If no data, return default values
        if mark == 0.0:
            return {
                "mark": 85.50,
                "ema": 84.20,
                "vwap": 85.10,
                "timestamp": datetime.now().isoformat(),
                "market": market
            }
        
        return {
            "mark": mark,
            "ema": ema,
            "vwap": vwap,
            "timestamp": datetime.now().isoformat(),
            "market": market
        }
    except Exception as e:
        return {
            "mark": 85.50,
            "ema": 84.20,
            "vwap": 85.10,
            "timestamp": datetime.now().isoformat(),
            "market": market,
            "error": str(e)
        }

@app.get("/market/history")
def get_market_history(market: str = "epex_at", hours: int = 1, limit: int = 360, aggregated: bool = False):
    """Get market price history from database
    
    Args:
        market: Market identifier
        hours: Number of hours to retrieve (default: 1)
        limit: Maximum number of data points (default: 360)
        aggregated: If True, aggregate data for longer periods (default: False)
    
    Returns:
        List of price history entries
    """
    try:
        cutoff_ts = int(time.time() * 1000) - (hours * 60 * 60 * 1000)
        con = db()
        c = con.cursor()
        
        if aggregated and hours > 24:
            # For longer periods, aggregate by hour
            c.execute("""
                SELECT 
                    (timestamp / 3600000) * 3600000 as hour_timestamp,
                    AVG(mark) as mark,
                    AVG(ema) as ema,
                    AVG(vwap) as vwap,
                    MIN(mark) as mark_min,
                    MAX(mark) as mark_max,
                    COUNT(*) as data_points
                FROM market_price_history 
                WHERE market = ? AND timestamp >= ?
                GROUP BY hour_timestamp
                ORDER BY hour_timestamp ASC
                LIMIT ?
            """, (market, cutoff_ts, limit))
            rows = c.fetchall()
            history = []
            for row in rows:
                history.append({
                    "timestamp": int(row["hour_timestamp"]),
                    "mark": round(row["mark"], 2),
                    "ema": round(row["ema"], 2),
                    "vwap": round(row["vwap"], 2),
                    "mark_min": round(row["mark_min"], 2),
                    "mark_max": round(row["mark_max"], 2),
                    "data_points": row["data_points"],
                    "ts": datetime.fromtimestamp(row["hour_timestamp"] / 1000).isoformat()
                })
        else:
            # Original granular data
            c.execute("""
                SELECT timestamp, mark, ema, vwap, ts 
                FROM market_price_history 
                WHERE market = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (market, cutoff_ts, limit))
            rows = c.fetchall()
            history = []
            for row in rows:
                history.append({
                    "timestamp": row["timestamp"],
                    "mark": row["mark"],
                    "ema": row["ema"],
                    "vwap": row["vwap"],
                    "ts": row["ts"]
                })
        
        con.close()
        return {
            "market": market,
            "count": len(history),
            "history": history,
            "aggregated": aggregated
        }
    except Exception as e:
        return {
            "market": market,
            "count": 0,
            "history": [],
            "error": str(e)
        }

@app.get("/market/history/longterm")
def get_longterm_history(market: str = "epex_at", days: int = 7, aggregation: str = "hour"):
    """Get aggregated long-term market price history
    
    Args:
        market: Market identifier
        days: Number of days to retrieve (1, 7, 30, 90)
        aggregation: Aggregation level - 'hour' or 'day' (default: 'hour')
    
    Returns:
        Aggregated price history with statistics
    """
    try:
        cutoff_ts = int(time.time() * 1000) - (days * 24 * 60 * 60 * 1000)
        con = db()
        c = con.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_price_history'")
        if not c.fetchone():
            return {
                "market": market,
                "days": days,
                "aggregation": aggregation,
                "count": 0,
                "history": [],
                "error": "Table market_price_history does not exist yet. Data will be available after first price feed."
            }
        
        # DEBUG: Check total records in database
        c.execute("SELECT COUNT(*) as total FROM market_price_history WHERE market = ?", (market,))
        total_records = c.fetchone()["total"]
        c.execute("SELECT COUNT(*) as total FROM market_price_history WHERE market = ? AND timestamp >= ?", (market, cutoff_ts))
        records_in_range = c.fetchone()["total"]
        c.execute("SELECT MIN(timestamp) as min_ts, MAX(timestamp) as max_ts FROM market_price_history WHERE market = ?", (market,))
        ts_range = c.fetchone()
        
        print(f"DEBUG longterm: market={market}, days={days}, total_records={total_records}, records_in_range={records_in_range}, min_ts={ts_range['min_ts']}, max_ts={ts_range['max_ts']}, cutoff_ts={cutoff_ts}")
        
        if aggregation == "day":
            # Aggregate by day
            interval_ms = 24 * 60 * 60 * 1000
            c.execute("""
                SELECT 
                    (timestamp / ?) * ? as day_timestamp,
                    AVG(mark) as mark_avg,
                    AVG(ema) as ema_avg,
                    AVG(vwap) as vwap_avg,
                    MIN(mark) as mark_min,
                    MAX(mark) as mark_max,
                    MIN(ema) as ema_min,
                    MAX(ema) as ema_max,
                    COUNT(*) as data_points
                FROM market_price_history 
                WHERE market = ? AND timestamp >= ?
                GROUP BY day_timestamp
                ORDER BY day_timestamp ASC
            """, (interval_ms, interval_ms, market, cutoff_ts))
        else:
            # Aggregate by hour (default)
            interval_ms = 60 * 60 * 1000
            c.execute("""
                SELECT 
                    (timestamp / ?) * ? as hour_timestamp,
                    AVG(mark) as mark_avg,
                    AVG(ema) as ema_avg,
                    AVG(vwap) as vwap_avg,
                    MIN(mark) as mark_min,
                    MAX(mark) as mark_max,
                    MIN(ema) as ema_min,
                    MAX(ema) as ema_max,
                    COUNT(*) as data_points
                FROM market_price_history 
                WHERE market = ? AND timestamp >= ?
                GROUP BY hour_timestamp
                ORDER BY hour_timestamp ASC
            """, (interval_ms, interval_ms, market, cutoff_ts))
        
        rows = c.fetchall()
        con.close()
        
        history = []
        for row in rows:
            # SQLite Row objects - access by column name or index
            if aggregation == "day":
                entry = {
                    "timestamp": int(row["day_timestamp"]),
                    "mark": round(row["mark_avg"], 2),
                    "ema": round(row["ema_avg"], 2),
                    "vwap": round(row["vwap_avg"], 2),
                    "mark_min": round(row["mark_min"], 2),
                    "mark_max": round(row["mark_max"], 2),
                    "ema_min": round(row["ema_min"], 2) if row["ema_min"] is not None else None,
                    "ema_max": round(row["ema_max"], 2) if row["ema_max"] is not None else None,
                    "data_points": row["data_points"],
                    "ts": datetime.fromtimestamp(int(row["day_timestamp"]) / 1000).isoformat()
                }
            else:
                entry = {
                    "timestamp": int(row["hour_timestamp"]),
                    "mark": round(row["mark_avg"], 2),
                    "ema": round(row["ema_avg"], 2),
                    "vwap": round(row["vwap_avg"], 2),
                    "mark_min": round(row["mark_min"], 2),
                    "mark_max": round(row["mark_max"], 2),
                    "ema_min": round(row["ema_min"], 2) if row["ema_min"] is not None else None,
                    "ema_max": round(row["ema_max"], 2) if row["ema_max"] is not None else None,
                    "data_points": row["data_points"],
                    "ts": datetime.fromtimestamp(int(row["hour_timestamp"]) / 1000).isoformat()
                }
            history.append(entry)
        
        result = {
            "market": market,
            "days": days,
            "aggregation": aggregation,
            "count": len(history),
            "history": history,
            "debug": {
                "total_records": total_records,
                "records_in_range": records_in_range,
                "min_timestamp": ts_range["min_ts"],
                "max_timestamp": ts_range["max_ts"],
                "cutoff_timestamp": cutoff_ts
            }
        }
        print(f"DEBUG longterm result: count={len(history)}, first_entry={history[0] if history else None}")
        
        # Enhanced debug info
        result["debug"] = {
            "total_records": total_records,
            "records_in_range": records_in_range,
            "min_timestamp": ts_range["min_ts"],
            "max_timestamp": ts_range["max_ts"],
            "cutoff_timestamp": cutoff_ts,
            "cutoff_date": datetime.fromtimestamp(cutoff_ts / 1000).isoformat() if cutoff_ts else None,
            "min_date": datetime.fromtimestamp(ts_range["min_ts"] / 1000).isoformat() if ts_range["min_ts"] else None,
            "max_date": datetime.fromtimestamp(ts_range["max_ts"] / 1000).isoformat() if ts_range["max_ts"] else None,
            "current_time": datetime.now().isoformat(),
            "query_used": "day" if aggregation == "day" else "hour"
        }
        
        return result
    except Exception as e:
        import traceback
        return {
            "market": market,
            "days": days,
            "aggregation": aggregation,
            "count": 0,
            "history": [],
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/market/history/debug")
def debug_market_history(market: str = "epex_at"):
    """Debug endpoint to check database contents"""
    try:
        con = db()
        c = con.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_price_history'")
        table_exists = c.fetchone() is not None
        
        if not table_exists:
            return {
                "table_exists": False,
                "error": "Table market_price_history does not exist"
            }
        
        # Get total count
        c.execute("SELECT COUNT(*) as total FROM market_price_history WHERE market = ?", (market,))
        total = c.fetchone()["total"]
        
        # Get time range
        c.execute("SELECT MIN(timestamp) as min_ts, MAX(timestamp) as max_ts FROM market_price_history WHERE market = ?", (market,))
        ts_range = c.fetchone()
        
        # Get last 10 records
        c.execute("""
            SELECT timestamp, mark, ema, vwap, ts 
            FROM market_price_history 
            WHERE market = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (market,))
        recent = [dict(row) for row in c.fetchall()]
        
        # Get first 10 records
        c.execute("""
            SELECT timestamp, mark, ema, vwap, ts 
            FROM market_price_history 
            WHERE market = ? 
            ORDER BY timestamp ASC 
            LIMIT 10
        """, (market,))
        oldest = [dict(row) for row in c.fetchall()]
        
        con.close()
        
        return {
            "table_exists": True,
            "market": market,
            "total_records": total,
            "min_timestamp": ts_range["min_ts"],
            "max_timestamp": ts_range["max_ts"],
            "min_date": datetime.fromtimestamp(ts_range["min_ts"] / 1000).isoformat() if ts_range["min_ts"] else None,
            "max_date": datetime.fromtimestamp(ts_range["max_ts"] / 1000).isoformat() if ts_range["max_ts"] else None,
            "recent_records": recent,
            "oldest_records": oldest,
            "current_time": datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/market/history/sync")
def sync_market_history(data: dict = Body(...)):
    """Sync client-side history with server
    
    Args in body:
        market: Market identifier
        client_history: Array of {timestamp, mark, ema, vwap} entries
        last_sync: Last sync timestamp (optional)
    
    Returns:
        Server history that client doesn't have
    """
    try:
        market = data.get("market", "epex_at")
        client_history = data.get("client_history", [])
        last_sync = data.get("last_sync", 0)
        
        # Get client timestamps
        client_timestamps = {int(p.get("timestamp", 0)) for p in client_history}
        
        # Get server history newer than last_sync
        cutoff_ts = max(last_sync, int(time.time() * 1000) - (24 * 60 * 60 * 1000))
        con = db()
        c = con.cursor()
        
        if client_timestamps:
            # Exclude timestamps that client already has
            placeholders = ",".join("?" * len(client_timestamps))
            c.execute(f"""
                SELECT timestamp, mark, ema, vwap, ts 
                FROM market_price_history 
                WHERE market = ? AND timestamp >= ? AND timestamp NOT IN ({placeholders})
                ORDER BY timestamp ASC
                LIMIT 1000
            """, [market, cutoff_ts] + list(client_timestamps))
        else:
            # No client timestamps, return all since cutoff
            c.execute("""
                SELECT timestamp, mark, ema, vwap, ts 
                FROM market_price_history 
                WHERE market = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT 1000
            """, (market, cutoff_ts))
        
        rows = c.fetchall()
        con.close()
        
        server_history = []
        for row in rows:
            server_history.append({
                "timestamp": row["timestamp"],
                "mark": row["mark"],
                "ema": row["ema"],
                "vwap": row["vwap"],
                "ts": row["ts"]
            })
        
        return {
            "market": market,
            "count": len(server_history),
            "history": server_history,
            "synced_at": int(time.time() * 1000)
        }
    except Exception as e:
        return {
            "market": market,
            "count": 0,
            "history": [],
            "error": str(e)
        }

# ---- Book injection ----
@app.post("/admin/book_inject")
async def book_inject(market: str = Body(...), bids: List[List[float]] = Body(default=[]), asks: List[List[float]] = Body(default=[])):
    ensure_market(market)
    BOOK[market]["bids"] = sorted([(float(p), float(q)) for p,q in bids], key=lambda x: (-x[0],))
    BOOK[market]["asks"] = sorted([(float(p), float(q)) for p,q in asks], key=lambda x: (x[0],))
    persist_book(market)
    await emit_book(market)
    return {"status":"OK"}

# ---- Orders with SoC gates + throttle scaling ----
class OrderIn(BaseModel):
    market: str
    delivery_start: str
    delivery_end: str
    side: Literal["BUY","SELL"]
    quantity_mwh: float
    limit_price_eur_mwh: float = 0.0
    order_type: Literal["LIMIT","MARKET"] = "LIMIT"
    time_in_force: Literal["GFD","IOC","FOK"]="GFD"
    @validator("delivery_start","delivery_end")
    def v_iso(cls, v): datetime.fromisoformat(v.replace("Z","+00:00")); return v

@app.post("/orders")
async def create_order(o: OrderIn, user: User = Depends(get_user)):
    allow_buy, allow_sell, _, soc, temp = soc_limits()
    if o.side=="BUY" and not allow_buy:
        raise HTTPException(400, f"BUY disabled at SoC {soc:.1f}% (<15%)")
    if o.side=="SELL" and not allow_sell:
        raise HTTPException(400, f"SELL disabled at SoC {soc:.1f}% (>90%)")
    remaining = throttle(user.api_key, o.market)  # raises if over budget
    oid=uuid.uuid4().hex; now=datetime.utcnow().isoformat()
    con=db(); c=con.cursor()
    c.execute("""INSERT INTO orders(id,user_key,market,side,type,tif,p_limit,qty,d_start,d_end,status,filled,ts)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (oid,user.api_key,o.market,o.side,o.order_type,o.time_in_force,o.limit_price_eur_mwh,o.quantity_mwh,o.delivery_start,o.delivery_end,"ACCEPTED",0.0,now))
    con.commit(); con.close()
    asyncio.create_task(emit_order(user.api_key, {"event":"ACCEPTED","order_id":oid,"market":o.market}))
    exposure_of(user.api_key)
    
    # Try to match the new order
    asyncio.create_task(try_match_order(oid, o.market, o.side, o.quantity_mwh, o.limit_price_eur_mwh))
    
    return {"order_id":oid,"status":"ACCEPTED","timestamp":now,"throttle_remaining":remaining}

async def try_match_order(new_order_id: str, market: str, side: str, quantity: float, limit_price: float):
    """Simple matching engine - matches against opposite side orders"""
    con=db(); c=con.cursor()
    
    # Find matching orders (opposite side, acceptable price)
    opposite_side = "SELL" if side == "BUY" else "BUY"
    
    if side == "BUY":
        # For BUY: find SELL orders where ask_price <= limit_price
        c.execute("""SELECT id, user_key, qty, p_limit FROM orders 
                     WHERE market=? AND side=? AND status='ACCEPTED' AND filled < qty 
                     AND p_limit <= ? ORDER BY p_limit ASC, ts ASC""", 
                  (market, opposite_side, limit_price))
    else:
        # For SELL: find BUY orders where bid_price >= limit_price
        c.execute("""SELECT id, user_key, qty, p_limit FROM orders 
                     WHERE market=? AND side=? AND status='ACCEPTED' AND filled < qty 
                     AND p_limit >= ? ORDER BY p_limit DESC, ts ASC""", 
                  (market, opposite_side, limit_price))
    
    matches = c.fetchall()
    
    remaining_qty = quantity
    
    for match in matches:
        if remaining_qty <= 0:
            break
        
        match_order_id = match["id"]
        match_user_key = match["user_key"]
        match_qty = match["qty"]
        match_price = match["p_limit"]
        
        # How much can we trade?
        c.execute("SELECT filled FROM orders WHERE id=?", (match_order_id,))
        filled_row = c.fetchone()
        filled_qty = float(filled_row["filled"] or 0) if filled_row else 0.0
        match_available = match_qty - filled_qty
        trade_qty = min(remaining_qty, match_available)
        
        # Average price for the trade
        trade_price = (limit_price + match_price) / 2.0
        
        if trade_qty > 0:
            # Create trade record
            trade_id = uuid.uuid4().hex
            now = datetime.utcnow().isoformat()
            
            c.execute("""INSERT INTO trades(id, order_id, user_key, executed, price, ts, market, side)
                         VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                     (trade_id, new_order_id, match_user_key, trade_qty, trade_price, now, market, side))
            
            # Update new order filled qty
            c.execute("""UPDATE orders SET filled = filled + ? WHERE id = ?""", (trade_qty, new_order_id))
            
            # Update matched order filled qty
            c.execute("""UPDATE orders SET filled = filled + ? WHERE id = ?""", (trade_qty, match_order_id))
            
            # Update status if fully filled
            c.execute("""UPDATE orders SET status = 'FILLED' WHERE id = ? AND filled >= qty""", (new_order_id,))
            c.execute("""UPDATE orders SET status = 'FILLED' WHERE id = ? AND filled >= qty""", (match_order_id,))
            
            con.commit()
            
            # Emit trade event
            await emit_trade({
                "trade_id": trade_id,
                "market": market,
                "price": trade_price,
                "quantity": trade_qty,
                "side": side
            })
            
            remaining_qty -= trade_qty
    
    con.close()

@app.get("/orders")
def get_orders():
    """Get all orders"""
    con=db(); c=con.cursor()
    c.execute("SELECT * FROM orders ORDER BY ts DESC LIMIT 100")
    orders = []
    for row in c.fetchall():
        orders.append({
            "order_id": row["id"],
            "side": row["side"],
            "quantity_mwh": row["qty"],
            "price": row["p_limit"],
            "market": row["market"],
            "status": row["status"],
            "timestamp": row["ts"]
        })
    con.close()
    return {"orders": orders}

@app.get("/trades")
def get_trades():
    """Get all trades"""
    con=db(); c=con.cursor()
    c.execute("SELECT * FROM trades ORDER BY ts DESC LIMIT 100")
    trades = []
    for row in c.fetchall():
        trades.append({
            "trade_id": row["id"],
            "order_id": row["order_id"],
            "side": row["side"],
            "quantity_mwh": row["executed"],
            "price": row["price"],
            "market": row["market"],
            "timestamp": row["ts"]
        })
    con.close()
    return {"trades": trades}

# ---- Metrics endpoint ----
@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
