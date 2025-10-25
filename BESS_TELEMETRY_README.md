# BESS Telemetrie-System - Automatische Datenquellen

## 🎯 Übersicht

Das Phoenyra BESS Trade System unterstützt jetzt **automatische Telemetrie-Erfassung** über drei verschiedene Schnittstellen:

1. **Modbus TCP** - Für echte BESS-Hardware
2. **MQTT** - Für IoT-Sensoren und Smart-Grid-Systeme  
3. **REST API** - Für externe Systeme und Integrationen

## 🔧 Schnittstellen-Implementierung

### **1. Modbus TCP Schnittstelle**

**Für echte BESS-Hardware (Batterie-Speichersysteme)**

```python
# Konfiguration
BESS_MODBUS_HOST=192.168.1.100    # BESS-System IP
BESS_MODBUS_PORT=502              # Standard Modbus Port
BESS_MODBUS_UNIT_ID=1             # Modbus Unit ID
BESS_MODBUS_ENABLED=true          # Aktivieren
```

**Register-Mapping:**
- **Register 0:** SoC in Prozent (0-100)
- **Register 1:** Aktive Leistung in kW
- **Register 2:** Temperatur in °C (0.1°C Auflösung)

**Beispiel-Integration:**
```python
# BESS-System sendet automatisch:
# SoC: 75% → Register 0: 7500
# Power: 2.5 MW → Register 1: 2500  
# Temp: 28.3°C → Register 2: 283
```

### **2. MQTT Schnittstelle**

**Für IoT-Sensoren und Smart-Grid-Systeme**

```python
# Konfiguration
BESS_MQTT_BROKER=localhost         # MQTT Broker
BESS_MQTT_PORT=1883               # MQTT Port
BESS_MQTT_USERNAME=               # Optional
BESS_MQTT_PASSWORD=               # Optional
BESS_MQTT_ENABLED=true            # Aktivieren

# Topics
BESS_MQTT_TOPIC_SOC=bess/soc
BESS_MQTT_TOPIC_POWER=bess/power
BESS_MQTT_TOPIC_TEMP=bess/temperature
```

**MQTT Message Format:**
```json
// Topic: bess/soc
{
  "value": 75.5,
  "timestamp": "2025-01-25T20:30:00Z",
  "unit": "%"
}

// Topic: bess/power  
{
  "value": 2.5,
  "timestamp": "2025-01-25T20:30:00Z",
  "unit": "MW"
}

// Topic: bess/temperature
{
  "value": 28.3,
  "timestamp": "2025-01-25T20:30:00Z", 
  "unit": "°C"
}
```

### **3. REST API Schnittstelle**

**Für externe Systeme und Integrationen**

```bash
# API-Endpunkt
POST http://localhost:9000/api/bess/telemetry
Headers: X-API-KEY: bess_telemetry_key
Content-Type: application/json

# Request Body
{
  "soc_percent": 75.5,
  "active_power_mw": 2.5,
  "temperature_c": 28.3
}
```

**Response:**
```json
{
  "status": "OK",
  "message": "Telemetrie erfolgreich aktualisiert",
  "data": {
    "soc_percent": 75.5,
    "active_power_mw": 2.5,
    "temperature_c": 28.3,
    "timestamp": "2025-01-25T20:30:00.000Z"
  }
}
```

## 🚀 System-Start

### **Docker Compose Setup**

```yaml
# docker-compose.yml
bess-telemetry:
  build: ./exchange
  container_name: bess-telemetry
  command: python bess_telemetry.py
  environment:
    - BESS_MODBUS_ENABLED=false      # Modbus aktivieren
    - BESS_MQTT_ENABLED=false        # MQTT aktivieren  
    - BESS_REST_ENABLED=true         # REST API aktivieren
    - BESS_UPDATE_INTERVAL=30        # Update alle 30s
```

### **Manueller Start**

```bash
# BESS Telemetrie-Service starten
docker-compose up bess-telemetry

# Logs anzeigen
docker logs bess-telemetry -f

# Status prüfen
curl http://localhost:9000/api/bess/status
```

## 📊 Dashboard-Integration

### **Automatische Updates**

Das Dashboard zeigt jetzt die **Telemetrie-Quelle** an:

- **"Automatische Telemetrie"** - Daten von Modbus/MQTT/REST
- **"Manuelle Eingabe"** - User hat Werte manuell eingegeben

### **Real-time Anzeige**

```javascript
// Dashboard zeigt automatisch:
// SoC: 75.5% (Automatische Telemetrie)
// Power: 2.5 MW (Automatische Telemetrie)  
// Temp: 28.3°C (Automatische Telemetrie)
```

## 🔧 Konfiguration

### **Umgebungsvariablen**

```bash
# Modbus TCP
export BESS_MODBUS_ENABLED=true
export BESS_MODBUS_HOST=192.168.1.100
export BESS_MODBUS_PORT=502
export BESS_MODBUS_UNIT_ID=1

# MQTT
export BESS_MQTT_ENABLED=true
export BESS_MQTT_BROKER=localhost
export BESS_MQTT_PORT=1883
export BESS_MQTT_USERNAME=
export BESS_MQTT_PASSWORD=

# REST API
export BESS_REST_ENABLED=true
export BESS_API_KEY=bess_telemetry_key

# Update-Interval
export BESS_UPDATE_INTERVAL=30
```

### **Dependencies**

```txt
# exchange/requirements.txt
pymodbus==3.5.2      # Modbus TCP Support
paho-mqtt==1.6.1     # MQTT Support
requests==2.31.0      # HTTP Requests
```

## 🎯 Trading-Entscheidungen

### **User braucht aktuelle Speicherdaten für:**

1. **Kauf-Entscheidung:**
   - SoC < 30% → Batterie leer → Strom kaufen
   - Niedrige Preise → Arbitrage-Möglichkeit

2. **Verkauf-Entscheidung:**
   - SoC > 70% → Batterie voll → Strom verkaufen
   - Hohe Preise → Profit-Möglichkeit

3. **System-Status:**
   - Temperatur > 40°C → System-Überhitzung
   - Power > 5 MW → Maximale Leistung erreicht

## 📈 Beispiel-Szenarien

### **Szenario 1: Arbitrage-Trading**
```
02:00 Uhr: SoC 20%, Preis 50 EUR/MWh → KAUFEN
18:00 Uhr: SoC 80%, Preis 150 EUR/MWh → VERKAUFEN
Profit: 100 EUR/MWh
```

### **Szenario 2: Peak-Shaving**
```
12:00 Uhr: SoC 90%, Preis 200 EUR/MWh → VERKAUFEN
23:00 Uhr: SoC 10%, Preis 30 EUR/MWh → KAUFEN
Profit: 170 EUR/MWh
```

### **Szenario 3: System-Überwachung**
```
Temperatur: 45°C → System-Überhitzung → Trading stoppen
Power: 5.2 MW → Maximale Leistung → Order-Limit setzen
```

## 🔒 Sicherheit

### **API-Key Authentifizierung**
```bash
# REST API erfordert API-Key
curl -H "X-API-KEY: bess_telemetry_key" \
     -H "Content-Type: application/json" \
     -d '{"soc_percent": 75.5}' \
     http://localhost:9000/api/bess/telemetry
```

### **MQTT Authentifizierung**
```python
# MQTT mit Username/Password
client.username_pw_set("username", "password")
```

### **Modbus TCP Sicherheit**
```python
# Modbus TCP über lokales Netzwerk
# Nur vertrauenswürdige IP-Adressen
```

## 🚨 Troubleshooting

### **Häufige Probleme**

1. **Modbus TCP Verbindung fehlgeschlagen**
   ```bash
   # IP-Adresse prüfen
   ping 192.168.1.100
   
   # Port prüfen
   telnet 192.168.1.100 502
   ```

2. **MQTT Broker nicht erreichbar**
   ```bash
   # Broker-Status prüfen
   mosquitto_pub -h localhost -t test -m "hello"
   ```

3. **REST API Fehler**
   ```bash
   # API-Key prüfen
   curl -H "X-API-KEY: bess_telemetry_key" \
        http://localhost:9000/api/bess/status
   ```

### **Logs prüfen**
```bash
# BESS Telemetrie-Logs
docker logs bess-telemetry -f

# Exchange-Logs  
docker logs exchange -f

# Alle Services
docker-compose logs -f
```

---

**Phoenyra BESS Trade System v2.0**  
*Automatische Telemetrie-Erfassung für professionelle Trading-Entscheidungen*

© 2025 Phoenyra.com by Ing. Heinz Schlagintweit. Alle Rechte vorbehalten.
