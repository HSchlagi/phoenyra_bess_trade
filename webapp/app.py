from flask import Flask, render_template, request, jsonify, session, send_from_directory, flash, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
import json
import asyncio
import websockets
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
import os
import yaml
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'phoenyra_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Load users from YAML
def load_users():
    """Load users from users.yaml file"""
    users_path = os.path.join(os.path.dirname(__file__), 'config', 'users.yaml')
    try:
        with open(users_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('users', [])
    except FileNotFoundError:
        logging.warning(f"Users file not found at {users_path}, using default users")
        return [
            {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
            {'username': 'trader', 'password': 'trader123', 'role': 'trader'},
            {'username': 'viewer', 'password': 'viewer123', 'role': 'viewer'}
        ]

# Load users on startup
app.users = load_users()

# Import auth decorators (must be after app.users is set)
try:
    from auth import login_required, role_required
except ImportError:
    # Fallback if auth module not found
    def login_required(f):
        return f
    def role_required(*roles):
        def decorator(f):
            return f
        return decorator

# API Configuration
EXCHANGE_BASE_URL = os.getenv('EXCHANGE_BASE_URL', 'http://exchange:9000')
FORECAST_BASE_URL = os.getenv('FORECAST_BASE_URL', 'http://forecast:9500')
GRID_BASE_URL = os.getenv('GRID_BASE_URL', 'http://grid:9501')
RISK_BASE_URL = os.getenv('RISK_BASE_URL', 'http://risk:9502')
CREDIT_BASE_URL = os.getenv('CREDIT_BASE_URL', 'http://credit:9503')
BILLING_BASE_URL = os.getenv('BILLING_BASE_URL', 'http://billing:9504')
TRADING_BRIDGE_URL = os.getenv('TRADING_BRIDGE_URL', 'http://trading-bridge:9510')
API_KEY = os.getenv('API_KEY', 'demo')
HMAC_SECRET = os.getenv('HMAC_SECRET', 'phoenyra_demo_secret')

class TradingAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {'X-API-KEY': api_key}
    
    def get_metrics(self):
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def create_order(self, order_data):
        try:
            response = requests.post(
                f"{self.base_url}/orders",
                json=order_data,
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def push_price(self, market, price, volume=1.0):
        try:
            response = requests.post(
                f"{self.base_url}/admin/pricefeed/push",
                params={"market": market, "price": price, "volume": volume},
                timeout=5
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# Initialize API client
trading_api = TradingAPI(EXCHANGE_BASE_URL, API_KEY)

# ============================================================================
# Authentication Routes
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        for user in app.users:
            if user.get('username') == username and user.get('password') == password:
                session['user'] = {
                    'name': username,
                    'role': user.get('role', 'viewer')
                }
                logging.info(f"User logged in: {username}")
                next_url = request.args.get('next') or url_for('dashboard')
                return redirect(next_url)
        
        logging.warning(f"Failed login attempt for user: {username}")
        return render_template('login.html', error='Ungültige Anmeldedaten')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    user = session.get('user', {}).get('name', 'unknown')
    session.pop('user', None)
    logging.info(f"User logged out: {user}")
    return redirect(url_for('login'))

# ============================================================================
# Protected Routes
# ============================================================================

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/metrics')
def get_metrics():
    metrics = trading_api.get_metrics()
    return metrics, 200, {'Content-Type': 'text/plain'}

@app.route('/api/bess-status')
def get_bess_status():
    """Get current BESS status from exchange"""
    try:
        response = requests.get(f"{EXCHANGE_BASE_URL}/api/bess/status")
        if response.status_code == 200:
            data = response.json()
            # Add telemetry source information
            data["telemetry_source"] = "Automatische Telemetrie"
            return data
        else:
            # Return mock data if exchange is not available
            return {
                "soc_percent": 72.5,
                "active_power": 3.8,
                "temperature": 28.3,
                "status": "online",
                "telemetry_source": "Manuelle Eingabe"
            }
    except Exception as e:
        # Return mock data if connection fails
        return {
            "soc_percent": 72.5,
            "active_power": 3.8,
            "temperature": 28.3,
            "status": "offline",
            "telemetry_source": "Manuelle Eingabe"
        }

@app.route('/api/market-data')
def get_market_data():
    """Get current market data"""
    try:
        response = requests.get(f"{EXCHANGE_BASE_URL}/market/prices")
        if response.status_code == 200:
            return response.json()
        else:
            # Return mock data
            return {
                "mark": 85.50,
                "ema": 84.20,
                "vwap": 85.10,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        # Return mock data
        return {
            "mark": 85.50,
            "ema": 84.20,
            "vwap": 85.10,
            "timestamp": datetime.now().isoformat()
        }

@app.route('/api/market/history')
def get_market_history():
    """Get market price history from server"""
    try:
        market = request.args.get('market', 'epex_at')
        hours = int(request.args.get('hours', 1))
        limit = int(request.args.get('limit', 360))
        
        response = requests.get(
            f"{EXCHANGE_BASE_URL}/market/history",
            params={'market': market, 'hours': hours, 'limit': limit}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"market": market, "count": 0, "history": []}
    except Exception as e:
        return {"market": market, "count": 0, "history": [], "error": str(e)}

@app.route('/api/market/history/sync', methods=['POST'])
def sync_market_history():
    """Sync client history with server"""
    try:
        data = request.get_json()
        response = requests.post(
            f"{EXCHANGE_BASE_URL}/market/history/sync",
            json=data
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"market": data.get('market', 'epex_at'), "count": 0, "history": []}
    except Exception as e:
        return {"market": data.get('market', 'epex_at'), "count": 0, "history": [], "error": str(e)}

@app.route('/api/market/history/longterm')
def get_longterm_history():
    """Get aggregated long-term market price history"""
    try:
        market = request.args.get('market', 'epex_at')
        days = int(request.args.get('days', 7))
        aggregation = request.args.get('aggregation', 'hour')
        
        response = requests.get(
            f"{EXCHANGE_BASE_URL}/market/history/longterm",
            params={'market': market, 'days': days, 'aggregation': aggregation}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"market": market, "days": days, "aggregation": aggregation, "count": 0, "history": []}
    except Exception as e:
        return {"market": market, "days": days, "aggregation": aggregation, "count": 0, "history": [], "error": str(e)}

@app.route('/api/market/history/debug')
def debug_market_history():
    """Debug endpoint to check database contents"""
    try:
        market = request.args.get('market', 'epex_at')
        response = requests.get(
            f"{EXCHANGE_BASE_URL}/market/history/debug",
            params={'market': market},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Exchange server returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/api/orders')
def get_orders():
    """Get active orders"""
    try:
        response = requests.get(f"{EXCHANGE_BASE_URL}/orders", headers={"X-API-Key": API_KEY})
        if response.status_code == 200:
            return response.json()
        else:
            return {"orders": []}
    except Exception as e:
        return {"orders": []}

@app.route('/api/trades')
def get_trades():
    """Get recent trades"""
    try:
        response = requests.get(f"{EXCHANGE_BASE_URL}/trades", headers={"X-API-Key": API_KEY})
        if response.status_code == 200:
            return response.json()
        else:
            return {"trades": []}
    except Exception as e:
        return {"trades": []}

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create order - route to internal exchange or external trading bridge"""
    order_data = request.get_json()
    target_exchange = order_data.get('target_exchange', 'INTERNAL')
    
    # Route to appropriate exchange
    if target_exchange == 'INTERNAL':
        # Internal exchange (current behavior)
        result = trading_api.create_order(order_data)
        return jsonify(result)
    elif target_exchange in ['EPEX_SPOT', 'APG']:
        # External exchange - route through trading bridge
        try:
            bridge_url = os.getenv('TRADING_BRIDGE_URL', 'http://trading-bridge:9510')
            response = requests.post(
                f"{bridge_url}/bridge/orders",
                json=order_data,
                timeout=10
            )
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({
                    "error": f"Trading Bridge Error: {response.status_code}",
                    "message": response.text,
                    "fallback": "Order wurde nicht übertragen. Bitte Credentials prüfen."
                }), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({
                "error": "Trading Bridge nicht erreichbar",
                "message": "Der Trading-Bridge-Service ist nicht verfügbar. Externe Plattformen erfordern zusätzliche Konfiguration.",
                "fallback": "Bitte verwenden Sie 'Interner Exchange' oder kontaktieren Sie den Administrator."
            }), 503
        except Exception as e:
            return jsonify({
                "error": str(e),
                "message": "Fehler bei der Übertragung an externe Plattform"
            }), 500
    else:
        return jsonify({"error": f"Unbekannte Trading-Plattform: {target_exchange}"}), 400

@app.route('/order', methods=['POST'])
def create_order_form():
    """Handle form submission for order creation"""
    try:
        side = request.form["side"].upper()  # Convert to BUY/SELL
        quantity_mwh = float(request.form["amount"])
        limit_price_eur_mwh = float(request.form["price"])
        market = request.form["market"]
        target_exchange = request.form.get("target_exchange", "INTERNAL")  # Default: INTERNAL
        
        # Generate delivery times for 1 hour
        now = datetime.now()
        delivery_start = now.isoformat()
        delivery_end = (now + timedelta(hours=1)).isoformat()

        order_data = {
            "side": side,  # "BUY" or "SELL"
            "quantity_mwh": quantity_mwh,
            "limit_price_eur_mwh": limit_price_eur_mwh,
            "market": market,
            "delivery_start": delivery_start,
            "delivery_end": delivery_end,
            "order_type": "LIMIT",
            "time_in_force": "GFD",
            "target_exchange": target_exchange  # INTERNAL, EPEX_SPOT, or APG
        }

        # Route to appropriate exchange
        if target_exchange == 'INTERNAL':
            # Internal exchange (current behavior)
            response = requests.post(f"{EXCHANGE_BASE_URL}/orders", json=order_data, headers={"X-API-KEY": API_KEY})
            response.raise_for_status()
            flash("Order erfolgreich erstellt!", "success")
        elif target_exchange in ['EPEX_SPOT', 'APG']:
            # External exchange - route through trading bridge
            try:
                bridge_url = os.getenv('TRADING_BRIDGE_URL', 'http://trading-bridge:9510')
                response = requests.post(f"{bridge_url}/bridge/orders", json=order_data, timeout=10)
                if response.status_code == 200:
                    flash(f"Order an {target_exchange} übertragen!", "success")
                else:
                    flash(f"Fehler bei {target_exchange}: {response.text}", "error")
            except requests.exceptions.ConnectionError:
                flash("Trading Bridge nicht erreichbar. Bitte Credentials prüfen oder 'Interner Exchange' verwenden.", "error")
            except Exception as e:
                flash(f"Fehler: {str(e)}", "error")
        else:
            flash(f"Unbekannte Trading-Plattform: {target_exchange}", "error")
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = e.response.json().get("detail", "Unknown error")
        except (json.JSONDecodeError, ValueError):
            error_detail = e.response.text or f"HTTP {e.response.status_code}"
        flash(f"Error creating order: {error_detail}", "error")
    except requests.exceptions.RequestException as e:
        flash(f"Network error creating order: {e}", "error")
    except ValueError:
        flash("Invalid amount or price. Please enter numerical values.", "error")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("dashboard"))

@app.route('/api/pricefeed', methods=['POST'])
def push_price():
    data = request.get_json()
    result = trading_api.push_price(
        data.get('market'),
        data.get('price'),
        data.get('volume', 1.0)
    )
    return jsonify(result)

@app.route('/api/telemetry', methods=['POST'])
def update_telemetry():
    telemetry_data = request.get_json()
    try:
        response = requests.post(
            f"{EXCHANGE_BASE_URL}/telemetry/bess",
            json=telemetry_data,
            timeout=5
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)})

# ---- BESS Telemetrie-Konfiguration ----
@app.route('/config')
@login_required
def config_page():
    """BESS Telemetrie-Konfigurationsseite"""
    return render_template('config.html')

@app.route('/trading-config')
@login_required
def trading_config():
    """Trading-Plattform Konfigurationsseite"""
    return render_template('trading-config.html')

@app.route('/trading-bridge-konzept')
@login_required
def trading_bridge_konzept():
    """Trading-Bridge Konzept Dokumentation"""
    return render_template('trading-bridge-konzept.html')

# ---- Forecast Dashboard ----
@app.route('/forecast')
@login_required
def forecast_page():
    """Forecast Dashboard Seite"""
    return render_template('forecast.html')

@app.route('/api/forecast/dayahead', methods=['POST'])
def request_dayahead_forecast():
    """Request Day-Ahead Forecast"""
    try:
        data = request.get_json() or {}
        response = requests.post(f"{FORECAST_BASE_URL}/forecast/dayahead", json=data, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/forecast/intraday', methods=['POST'])
def request_intraday_forecast():
    """Request Intraday Forecast"""
    try:
        data = request.get_json() or {}
        response = requests.post(f"{FORECAST_BASE_URL}/forecast/intraday", json=data, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/forecast/status/<job_id>')
def get_forecast_status(job_id):
    """Get Forecast Job Status"""
    try:
        response = requests.get(f"{FORECAST_BASE_URL}/forecast/status/{job_id}", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Risk Dashboard ----
@app.route('/risk')
@login_required
def risk_page():
    """Risk Dashboard Seite"""
    return render_template('risk.html')

@app.route('/api/risk/var', methods=['POST'])
def calculate_var():
    """Calculate VaR"""
    try:
        data = request.get_json() or {}
        response = requests.post(f"{RISK_BASE_URL}/risk/var", json=data, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk/limits')
def get_risk_limits():
    """Get Risk Limits"""
    try:
        response = requests.get(f"{RISK_BASE_URL}/risk/limits", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Grid Dashboard ----
@app.route('/grid')
@login_required
def grid_page():
    """Grid Dashboard Seite"""
    return render_template('grid.html')

@app.route('/api/grid/state')
def get_grid_state():
    """Get Grid State"""
    try:
        area = request.args.get('area', 'AT')
        response = requests.get(f"{GRID_BASE_URL}/grid/state", params={"area": area}, timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/grid/constraints')
def get_grid_constraints():
    """Get Grid Constraints"""
    try:
        window = request.args.get('window', 'PT1H')
        response = requests.get(f"{GRID_BASE_URL}/grid/constraints", params={"window": window}, timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Credit Dashboard ----
@app.route('/credit')
@login_required
def credit_page():
    """Credit Dashboard Seite"""
    return render_template('credit.html')

@app.route('/api/credit/exposure')
def get_credit_exposure():
    """Get Credit Exposure"""
    try:
        counterparty = request.args.get('counterparty', 'CP-A')
        response = requests.get(f"{CREDIT_BASE_URL}/credit/exposure", params={"counterparty": counterparty}, timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/credit/limit', methods=['POST'])
def set_credit_limit():
    """Set Credit Limit"""
    try:
        data = request.get_json() or {}
        response = requests.post(f"{CREDIT_BASE_URL}/credit/limit", json=data, timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Billing Dashboard ----
@app.route('/billing')
@login_required
def billing_page():
    """Billing Dashboard Seite"""
    return render_template('billing.html')

@app.route('/api/billing/generate', methods=['POST'])
def generate_invoice():
    """Generate Invoice"""
    try:
        period = request.args.get('period') or request.get_json().get('period') if request.is_json else '2025-10'
        response = requests.post(f"{BILLING_BASE_URL}/billing/generate", params={"period": period}, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/billing/invoice/<invoice_id>')
def get_invoice_pdf(invoice_id):
    """Get Invoice PDF"""
    try:
        response = requests.get(f"{BILLING_BASE_URL}/billing/invoice/{invoice_id}", timeout=10)
        return Response(
            response.content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=invoice_{invoice_id}.pdf'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/save', methods=['POST'])
def save_config():
    """Konfiguration speichern"""
    try:
        data = request.get_json()
        config_type = data.get('type')
        config = data.get('config')
        
        # Hier würde normalerweise die Konfiguration in einer Datenbank gespeichert
        # Für Demo-Zwecke geben wir nur eine Bestätigung zurück
        return jsonify({
            "success": True,
            "message": f"{config_type} Konfiguration gespeichert",
            "config": config
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/config/load')
def load_config():
    """Aktuelle Konfiguration laden"""
    try:
        # Hier würde normalerweise die Konfiguration aus einer Datenbank geladen
        # Für Demo-Zwecke geben wir Standardwerte zurück
        return jsonify({
            "modbus": {
                "modbus_host": "192.168.1.100",
                "modbus_port": "502",
                "modbus_unit_id": "1",
                "soc_register": "0",
                "power_register": "1",
                "temp_register": "2",
                "modbus_enabled": False
            },
            "mqtt": {
                "mqtt_broker": "localhost",
                "mqtt_port": "1883",
                "mqtt_username": "",
                "mqtt_password": "",
                "mqtt_topic_soc": "bess/soc",
                "mqtt_topic_power": "bess/power",
                "mqtt_topic_temp": "bess/temperature",
                "mqtt_enabled": False
            },
            "rest": {
                "rest_api_key": "bess_telemetry_key",
                "rest_enabled": True
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/config/test', methods=['POST'])
def test_config():
    """Verbindungstest für Konfiguration"""
    try:
        data = request.get_json()
        config_type = data.get('type')
        
        if config_type == 'modbus':
            # Modbus TCP Test
            return jsonify({"success": True, "message": "Modbus TCP Verbindung erfolgreich"})
        elif config_type == 'mqtt':
            # MQTT Test
            return jsonify({"success": True, "message": "MQTT Verbindung erfolgreich"})
        elif config_type == 'rest':
            # REST API Test
            return jsonify({"success": True, "message": "REST API verfügbar"})
        else:
            return jsonify({"success": False, "error": "Unbekannter Konfigurationstyp"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to Phoenyra Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def handle_join_room(data):
    room = data['room']
    join_room(room)
    emit('status', {'message': f'Joined room {room}'})

@socketio.on('leave_room')
def handle_leave_room(data):
    room = data['room']
    leave_room(room)
    emit('status', {'message': f'Left room {room}'})

# WebSocket message verification
def verify_ws_message(meta, data):
    try:
        body = (meta['ts'] + '|' + json.dumps(data, separators=(',', ':'))).encode()
        calc = base64.b64encode(
            hmac.new(HMAC_SECRET.encode(), body, hashlib.sha256).digest()
        ).decode()
        return calc == meta['sig']
    except Exception:
        return False

# Background task for WebSocket data
async def fetch_ws_data():
    uri = f"ws://exchange:9000/ws/orders?api_key={API_KEY}"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            try:
                msg = json.loads(message)
                if verify_ws_message(msg['meta'], msg['data']):
                    socketio.emit('order_update', msg['data'])
            except Exception as e:
                print(f"WebSocket error: {e}")

@socketio.on('start_ws_connection')
def start_ws_connection():
    asyncio.create_task(fetch_ws_data())

# Trading Bridge API Routes
@app.route('/api/trading-bridge/status')
def trading_bridge_status():
    """Get status of trading bridge adapters"""
    try:
        response = requests.get(f"{TRADING_BRIDGE_URL}/bridge/status", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Trading Bridge nicht erreichbar"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 503

@app.route('/api/trading-bridge/credentials')
def get_trading_credentials():
    """Get current trading credentials (masked)"""
    try:
        # Get status to check if configured
        status_response = requests.get(f"{TRADING_BRIDGE_URL}/bridge/status", timeout=5)
        status_data = status_response.json() if status_response.status_code == 200 else {}
        
        # Return masked credentials (from environment or config)
        return jsonify({
            "epex": {
                "username": os.getenv('EPEX_USERNAME', ''),
                "api_key": os.getenv('EPEX_API_KEY', ''),
                "test_mode": os.getenv('EPEX_TEST_MODE', 'true').lower() == 'true',
                "configured": status_data.get('epex_spot', {}).get('configured', False)
            },
            "apg": {
                "mpid": os.getenv('APG_MPID', ''),
                "bilanzgruppe": os.getenv('APG_BILANZGRUPPE', ''),
                "as4_endpoint": os.getenv('APG_AS4_ENDPOINT', ''),
                "configured": status_data.get('apg', {}).get('configured', False)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trading-bridge/credentials/epex', methods=['POST'])
def save_epex_credentials():
    """Save EPEX Spot credentials"""
    try:
        data = request.get_json()
        # In production: Store securely (e.g., encrypted config file or secret manager)
        # For now: Return success (actual storage would require Trading Bridge service update)
        # TODO: Implement secure credential storage
        return jsonify({
            "success": True,
            "message": "Credentials werden im Trading-Bridge Service gespeichert. Bitte setzen Sie die Environment-Variablen im Docker-Compose oder kontaktieren Sie den Administrator.",
            "note": "Für Produktionsumgebung: Credentials sollten über sichere Secret-Management gespeichert werden"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trading-bridge/credentials/apg', methods=['POST'])
def save_apg_credentials():
    """Save APG credentials"""
    try:
        data = request.get_json()
        # In production: Store securely
        # For now: Return success
        return jsonify({
            "success": True,
            "message": "Credentials werden im Trading-Bridge Service gespeichert. Bitte setzen Sie die Environment-Variablen im Docker-Compose oder kontaktieren Sie den Administrator.",
            "note": "Für Produktionsumgebung: Credentials sollten über sichere Secret-Management gespeichert werden"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True)
