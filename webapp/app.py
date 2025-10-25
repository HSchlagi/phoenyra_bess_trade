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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'phoenyra_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Exchange API Configuration
EXCHANGE_BASE_URL = os.getenv('EXCHANGE_BASE_URL', 'http://exchange:9000')
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

@app.route('/')
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
        response = requests.get(f"{EXCHANGE_BASE_URL}/telemetry/bess/status")
        if response.status_code == 200:
            return response.json()
        else:
            # Return mock data if exchange is not available
            return {
                "soc_percent": 72.5,
                "active_power": 3.8,
                "temperature": 28.3,
                "status": "online"
            }
    except Exception as e:
        # Return mock data if connection fails
        return {
            "soc_percent": 72.5,
            "active_power": 3.8,
            "temperature": 28.3,
            "status": "offline"
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
    order_data = request.get_json()
    result = trading_api.create_order(order_data)
    return jsonify(result)

@app.route('/order', methods=['POST'])
def create_order_form():
    """Handle form submission for order creation"""
    try:
        side = request.form["side"].upper()  # Convert to BUY/SELL
        quantity_mwh = float(request.form["amount"])
        limit_price_eur_mwh = float(request.form["price"])
        market = request.form["market"]
        
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
            "time_in_force": "GFD"
        }

        response = requests.post(f"{EXCHANGE_BASE_URL}/orders", json=order_data)
        response.raise_for_status()
        
        flash("Order successfully created!", "success")
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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True)
