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
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; return conn

def init_db():
    con=db(); c=con.cursor()
    c.executescript("""    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, api_key TEXT UNIQUE, role TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, user_key TEXT, market TEXT, side TEXT, type TEXT, tif TEXT, p_limit REAL, qty REAL, d_start TEXT, d_end TEXT, status TEXT, filled REAL, ts TEXT);
    CREATE TABLE IF NOT EXISTS trades(id TEXT PRIMARY KEY, order_id TEXT, user_key TEXT, executed REAL, price REAL, ts TEXT, market TEXT, side TEXT);
    CREATE TABLE IF NOT EXISTS orderbook_history(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, market TEXT, bids TEXT, asks TEXT);
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
    r.xadd(key, {"p": price, "v": volume, "ts": int(time.time()*1000)}, maxlen=10000, approximate=True)
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
    G_MARK.labels(market).set(price); G_EMA.labels(market).set(ema); G_VWAP.labels(market).set(vwap); C_EVENTS.labels(market).inc()
    return {"status":"OK"}

@app.get("/market/prices")
def get_market_prices(market: str = "epex_at"):
    """Get current market prices from Redis"""
    try:
        mark = round(float(r.get(f"price:mark:{market}") or 0.0), 2)
        ema = round(float(r.get(f"price:ema:{market}") or mark), 2)
        vwap = round(float(r.get(f"price:vwap:{market}") or mark), 2)
        
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
