# Trading-Bridge Konzept: APG & EPEX Spot Integration

## 📊 Aktueller Stand

### ✅ Was bereits funktioniert:
- **Marktdaten-Abruf**: EPEX Spot Preise über ENTSO-E Transparency Platform
- **Internes Trading**: Vollständige Order-Verwaltung und Matching-Engine
- **Forecast & Risk**: ETRM Services für Trading-Entscheidungen

### ❌ Was noch fehlt:
- **Direkte Trading-Anbindung** zu APG oder EPEX Spot
- **Order-Übermittlung** an externe Börsen
- **Fahrplanübermittlung** an APG (EDIFACT/XML)
- **Clearing-Integration** (z.B. ECC für EPEX)

---

## 🎯 Lösungskonzept: Trading-Bridge-Service

### Architektur

```
┌─────────────────┐
│  WebApp/UI      │
│  (Order Entry)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Exchange API   │ ← Internes Trading (aktuell)
│  (Port 9000)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Trading Bridge Service (NEU)       │
│  - Order Routing                    │
│  - Market Adapter (APG/EPEX)        │
│  - Format Conversion (EDIFACT/XML) │
│  - Status Synchronisation           │
└────────┬────────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│   APG   │ │ EPEX Spot│
│   API   │ │   API    │
└─────────┘ └──────────┘
```

---

## 🔧 Implementierungsplan

### Phase 1: EPEX Spot Integration (Empfohlen zuerst)

#### 1.1 EPEX Spot API-Anbindung
```python
# etrm/trading-bridge/epex_adapter.py
class EPEXSpotAdapter:
    """
    EPEX Spot Trading Adapter
    
    Voraussetzungen:
    - EPEX Spot Mitgliedschaft
    - Clearing-Teilnahme über ECC (European Commodity Clearing)
    - API Credentials (Username, Password, API Key)
    """
    
    def __init__(self, credentials: dict):
        self.base_url = "https://api.epexspot.com"  # Beispiel
        self.username = credentials['username']
        self.password = credentials['password']
        self.api_key = credentials['api_key']
        self.session = requests.Session()
    
    def place_order(self, order: dict) -> dict:
        """
        Order an EPEX Spot platzieren
        
        Args:
            order: {
                'market': 'EPEX_AT_DAY_AHEAD',
                'product': 'Hourly',
                'delivery_date': '2025-11-05',
                'delivery_hour': 14,
                'side': 'BUY' | 'SELL',
                'quantity_mwh': 1.0,
                'limit_price_eur_mwh': 85.50,
                'order_type': 'LIMIT' | 'MARKET'
            }
        
        Returns:
            {
                'order_id': 'EPEX-12345',
                'status': 'SUBMITTED' | 'REJECTED',
                'external_id': '...'
            }
        """
        # API Call zu EPEX Spot
        pass
    
    def get_order_status(self, external_order_id: str) -> dict:
        """Order-Status von EPEX Spot abrufen"""
        pass
    
    def cancel_order(self, external_order_id: str) -> dict:
        """Order bei EPEX Spot stornieren"""
        pass
```

#### 1.2 Trading Bridge Service
```python
# etrm/trading-bridge/bridge_service.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal

app = FastAPI(title="Phoenyra Trading Bridge")

class BridgeOrder(BaseModel):
    market: str
    side: Literal["BUY", "SELL"]
    quantity_mwh: float
    limit_price_eur_mwh: float
    delivery_start: str
    delivery_end: str
    target_exchange: Literal["INTERNAL", "EPEX_SPOT", "APG"]

@app.post("/bridge/orders")
async def route_order(order: BridgeOrder):
    """
    Route Order zu internem Exchange oder externer Börse
    """
    if order.target_exchange == "INTERNAL":
        # An internen Exchange weiterleiten (aktuelles Verhalten)
        response = requests.post(
            "http://exchange:9000/orders",
            json=order.dict(),
            headers={"X-API-KEY": "demo"}
        )
        return response.json()
    
    elif order.target_exchange == "EPEX_SPOT":
        # An EPEX Spot Adapter weiterleiten
        adapter = EPEXSpotAdapter(credentials)
        result = adapter.place_order(order.dict())
        return result
    
    elif order.target_exchange == "APG":
        # An APG Adapter weiterleiten
        adapter = APGAdapter(credentials)
        result = adapter.submit_schedule(order.dict())
        return result
```

---

### Phase 2: APG Integration

#### 2.1 APG Fahrplanübermittlung
```python
# etrm/trading-bridge/apg_adapter.py
class APGAdapter:
    """
    APG (Austrian Power Grid) Adapter
    
    Voraussetzungen:
    - Bilanzgruppenvertrag mit APG
    - Marktpartner-ID (MPID)
    - AS4/ENTSO-E ECP Anbindung oder VPN
    - EDIFACT/XML Format-Konverter
    """
    
    def __init__(self, credentials: dict):
        self.mpid = credentials['mpid']  # Marktpartner-ID
        self.as4_endpoint = credentials['as4_endpoint']
        self.vpn_endpoint = credentials.get('vpn_endpoint')
        self.bilanzgruppe = credentials['bilanzgruppe']
    
    def submit_schedule(self, schedule_data: dict) -> dict:
        """
        Fahrplan an APG übermitteln (EDIFACT/XML Format)
        
        Args:
            schedule_data: {
                'delivery_date': '2025-11-05',
                'hourly_schedule': [
                    {'hour': 0, 'mwh': 0.0},
                    {'hour': 1, 'mwh': 1.5},
                    ...
                ]
            }
        
        Returns:
            {
                'submission_id': 'APG-12345',
                'status': 'ACCEPTED' | 'REJECTED',
                'message': '...'
            }
        """
        # EDIFACT/XML Format generieren
        edifact_message = self._generate_edifact(schedule_data)
        
        # Über AS4 oder VPN senden
        response = self._send_via_as4(edifact_message)
        
        return response
    
    def _generate_edifact(self, schedule_data: dict) -> str:
        """EDIFACT Format generieren (APG Standard)"""
        # EDIFACT Implementation
        pass
```

---

## 📋 Voraussetzungen Checkliste

### EPEX Spot Trading:
- [ ] EPEX Spot Mitgliedschaft (Vertrag)
- [ ] ECC Clearing-Teilnahme (European Commodity Clearing)
- [ ] API Credentials (Username, Password, API Key)
- [ ] Test-Umgebung Zugang
- [ ] Bankverbindung für Margins

### APG Trading:
- [ ] Marktteilnehmer-Registrierung bei E-Control
- [ ] Bilanzgruppenvertrag mit APG
- [ ] Marktpartner-ID (MPID)
- [ ] AS4/ENTSO-E ECP Anbindung oder VPN
- [ ] IT-System Zertifizierung
- [ ] Testphase mit APG

---

## 🔐 Konfiguration

### Environment Variables
```bash
# EPEX Spot Credentials
EPEX_USERNAME=your_username
EPEX_PASSWORD=your_password
EPEX_API_KEY=your_api_key
EPEX_TEST_MODE=true  # für Test-Umgebung

# APG Credentials
APG_MPID=your_mpid
APG_BILANZGRUPPE=your_bilanzgruppe
APG_AS4_ENDPOINT=https://...
APG_VPN_ENABLED=false

# Trading Bridge Config
BRIDGE_ENABLED=true
DEFAULT_TARGET_EXCHANGE=INTERNAL  # oder EPEX_SPOT, APG
```

---

## 🚀 Integration in Docker Compose

```yaml
# docker-compose.yml
services:
  trading-bridge:
    build: ./etrm/trading-bridge
    container_name: trading-bridge
    ports:
      - "9510:9510"
    environment:
      - EXCHANGE_BASE_URL=http://exchange:9000
      - EPEX_USERNAME=${EPEX_USERNAME}
      - EPEX_PASSWORD=${EPEX_PASSWORD}
      - APG_MPID=${APG_MPID}
    restart: unless-stopped
    depends_on:
      - exchange
```

---

## 📝 WebApp Integration

### Order-Formular erweitern
```html
<!-- webapp/templates/dashboard.html -->
<select name="target_exchange" id="target-exchange">
    <option value="INTERNAL">Interner Exchange</option>
    <option value="EPEX_SPOT">EPEX Spot</option>
    <option value="APG">APG (Fahrplan)</option>
</select>
```

### API-Route anpassen
```python
# webapp/app.py
@app.route('/api/orders', methods=['POST'])
def create_order():
    order_data = request.get_json()
    target_exchange = order_data.get('target_exchange', 'INTERNAL')
    
    if target_exchange == 'INTERNAL':
        # Aktuelles Verhalten
        response = requests.post(
            f"{EXCHANGE_BASE_URL}/orders",
            json=order_data,
            headers={"X-API-KEY": API_KEY}
        )
    else:
        # Trading Bridge verwenden
        response = requests.post(
            "http://trading-bridge:9510/bridge/orders",
            json=order_data
        )
    
    return jsonify(response.json())
```

---

## ⚠️ Wichtige Hinweise

1. **Test-Umgebung**: Zuerst in Test-Umgebungen testen
2. **Zertifizierung**: APG/EPEX erfordern oft technische Zertifizierung
3. **Compliance**: Regulatorische Anforderungen beachten
4. **Fehlerbehandlung**: Robuste Error-Handling für API-Ausfälle
5. **Monitoring**: Umfassendes Logging und Monitoring

---

## 📚 Weitere Ressourcen

- **APG Marktzugang**: Siehe `Marktzugang/APG_Marktzugang_Österreich.md`
- **EPEX Spot API**: https://www.epexspot.com/en/platforms/api
- **ENTSO-E ECP**: https://www.entsoe.eu/network_codes/ecp/
- **EDIFACT Standards**: APG Dokumentation

---

**Status**: 🟡 Konzept-Phase  
**Nächste Schritte**: Implementierung nach Verfügbarkeit der Credentials

