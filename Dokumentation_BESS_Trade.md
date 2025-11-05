# Phoenyra BESS Trade System - Dokumentation

**Version:** 3.0 (ULTRA OMEGA+)  
**Stand:** 05.11.2025

## Übersicht

Das Phoenyra BESS Trade System ist eine moderne Web-Anwendung für das Trading und die Optimierung von Battery Energy Storage Systems (BESS). Das System kombiniert eine FastAPI-basierte Backend-Architektur mit einer Flask-basierten Web-Oberfläche, die mit Tailwind CSS und Magic UI Komponenten gestaltet wurde.

## Architektur

### Backend-Services
- **Exchange Service** (FastAPI): Kern-Trading-Engine mit REST API
- **Market Feed Service**: Live-Marktpreise von ENTSO-E (EPEX Spot)
- **BESS Telemetry Service**: Automatische Telemetrie-Erfassung (Modbus TCP, MQTT, REST API)
- **Forecast API** (FastAPI): Day-Ahead und Intraday Preisprognosen
- **Risk API** (FastAPI): Value at Risk (VaR) Berechnung und Risk Limits
- **Grid API** (FastAPI): Netzfrequenz-Monitoring und Grid Constraints
- **Credit API** (FastAPI): Counterparty Exposure Management
- **Billing API** (FastAPI): Rechnungserstellung und PDF-Generierung
- **Trading Bridge Service** (FastAPI): Routing zu externen Trading-Plattformen (EPEX Spot, APG)
- **Redis**: In-Memory-Datenbank für Caching und Session-Management
- **Prometheus**: Metriken-Sammlung und Monitoring
- **Grafana**: Visualisierung und Alerting
- **Webapp Service** (Flask): Web-Dashboard und Benutzeroberfläche

### Frontend-Technologien
- **Flask**: Python Web Framework
- **Tailwind CSS**: Utility-first CSS Framework
- **Magic UI**: Moderne UI-Komponenten und Effekte
- **ApexCharts**: Professionelle Chart-Bibliothek
- **Font Awesome**: Icon-Sammlung
- **Socket.IO**: Real-time Kommunikation

## Features

### 1. Dashboard-Interface
- **Moderne Dark-Mode-Oberfläche** mit Gold-Standard-Design
- **Responsive Design** für Desktop und Mobile
- **Live-Status-Anzeige** der Systemverbindung
- **Echtzeit-Uhr** in der Navigation

### 2. BESS-Status-Monitoring
- **State of Charge (SoC)** Anzeige in Prozent
- **Aktive Leistung** in MW
- **Temperatur-Monitoring** in °C
- **System-Status** (Online/Offline)
- **Echtzeit-Updates** alle 10 Sekunden

### 3. Trading-Funktionen
- **Order-Erstellung** mit Side (Buy/Sell), Menge, Preis und Markt
- **Trading-Plattform-Auswahl** (Interner Exchange / EPEX Spot / APG)
- **Aktive Orders** Übersicht
- **Recent Trades** Anzeige
- **Live-Marktpreise** von ENTSO-E/EPEX Spot (Österreich)
- **Marktpreise** Visualisierung (Mark, EMA, VWAP)
- **VWAP-Chart** mit 15-Minuten-Intervallen
- **Automatische Preisumrechnung** (ct/kWh → EUR/MWh)

### 4. Chart-Visualisierung
- **ApexCharts Integration** für professionelle Charts
- **Marktpreise-Zeitreihen-Chart** mit historischen Daten (Mark, EMA, VWAP)
- **VWAP-Zeitreihen-Chart** mit 15-Minuten-Intervallen
- **Interaktive Charts** mit Zoom, Pan und Tooltips
- **Automatische Preisvalidierung** (nur Preise 0-1000 EUR/MWh)
- **Sattes Grün** für optimale Sichtbarkeit
- **Responsive Design** für verschiedene Bildschirmgrößen
- **Persistente Chart-Historie** mit localStorage - Daten bleiben beim Seitenwechsel erhalten
- **Hybrid-Sync** mit Server-Backup - Automatische Synchronisation zwischen Client und Server (alle 60 Sekunden)
- **Server-seitige Historie** in SQLite für längere Zeiträume (24 Stunden)
- **Chart-Einstellungen** - Historie-Dauer (0.5-24h), maximale Datenpunkte (60-7200), Auto-Sync, Auto-Play
- **Export-Funktion** - Chart-Daten als JSON oder CSV exportieren
- **Chart-Reset-Button** - Historie zurücksetzen mit Bestätigung
- **Verbesserte Legende** - Vollständige Beschreibungen (Markt Preis, EMA (Exponential Moving Average), VWAP (Volume-Weighted Average Price))
- **Vertikale Legende-Anordnung** für bessere Lesbarkeit

### 5. Magic UI Komponenten
- **Aurora Text** für Überschriften
- **Neon Gradient Cards** für Status-Karten
- **Shimmer Buttons** für interaktive Elemente
- **Gold Standard Background** mit subtilen Gold-Akzenten
- **Hover-Effekte** und Animationen
- **Number Ticker** für animierte Zahlen

### 6. BESS Telemetrie-Steuerung
- **Automatische Telemetrie-Erfassung** via Modbus TCP, MQTT, REST API
- **Konfigurierbare Register-Adressen** für individuelle BESS-Anlagen
- **MQTT-Topic-Mapping** für IoT-Sensoren und Smart-Grid
- **REST API Integration** für externe Systeme
- **Live-Verbindungstests** für alle Schnittstellen
- **Benutzerfreundliche Konfiguration** mit Tab-Navigation

### 7. Trading Bridge & Externe Plattformen
- **Trading Bridge Service** für Routing zu externen Trading-Plattformen
- **EPEX Spot Integration** für Day-Ahead und Intraday Trading
- **APG Integration** für Fahrplanübermittlung (EDIFACT/XML)
- **Credentials-Verwaltung** über Trading-Config Dashboard
- **Status-Monitoring** aller Trading-Adapter
- **Test-Modus** für sichere Integrationstests
- **Automatische Order-Routing** basierend auf Plattform-Auswahl

## Technische Details

### Docker-Container
```yaml
services:
  exchange:        # FastAPI Backend (Port 9000)
  market-feed:     # Live market price feed (ENTSO-E/EPEX Spot)
  bess-telemetry:  # BESS Telemetry Service (Modbus TCP, MQTT, REST API)
  forecast:        # Forecast API (Port 9500)
  grid:            # Grid API (Port 9501)
  risk:            # Risk API (Port 9502)
  credit:          # Credit API (Port 9503)
  billing:         # Billing API (Port 9504)
  trading-bridge:  # Trading Bridge Service (Port 9510)
  redis:           # In-Memory Database
  prometheus:      # Metrics Collection (Port 9090)
  grafana:         # Visualization (Port 3000)
  webapp:          # Flask Frontend (Port 5000)
```

### API-Endpunkte

#### Exchange & Trading
- `GET /api/bess-status` - BESS-Status abrufen
- `GET /api/market-data` - Marktdaten abrufen
- `GET /api/orders` - Aktive Orders abrufen
- `GET /api/trades` - Recent Trades abrufen
- `POST /api/orders` - Neue Order erstellen
- `POST /api/telemetry` - BESS-Telemetrie senden
- `POST /api/bess/telemetry` - Externe Telemetrie-Daten empfangen
- `GET /api/bess/status` - Aktuelle BESS-Status abrufen

#### Marktdaten-Historie (Neu - 05.11.2025)
- `GET /api/market/history` - Marktpreis-Historie abrufen
  - Parameter: `market` (default: epex_at), `hours` (default: 1), `limit` (default: 360)
  - Gibt historische Preisdaten aus SQLite zurück (bis zu 24 Stunden)
- `POST /api/market/history/sync` - Client-Server-Synchronisation
  - Body: `{market, client_history, last_sync}`
  - Synchronisiert Client-Historie (localStorage) mit Server-Historie (SQLite)
  - Gibt fehlende Datenpunkte zurück für nahtlose Fortsetzung

#### Forecast API
- `POST /api/forecast/dayahead` - Day-Ahead Forecast anfordern
- `POST /api/forecast/intraday` - Intraday Forecast anfordern
- `GET /api/forecast/status/{job_id}` - Forecast Job-Status abrufen

#### Risk API
- `POST /api/risk/var` - VaR (Value at Risk) berechnen
- `GET /api/risk/limits` - Risk Limits abrufen

#### Grid API
- `GET /api/grid/state` - Grid-Zustand abrufen (Frequenz, Last, Tie-Lines)
- `GET /api/grid/constraints` - Aktive Grid-Constraints abrufen

#### Credit API
- `GET /api/credit/exposure` - Counterparty Exposure abrufen
- `POST /api/credit/limit` - Credit Limit setzen

#### Billing API
- `POST /api/billing/generate` - Rechnung generieren
- `GET /api/billing/invoice/{id}` - Invoice PDF herunterladen

#### Trading Bridge API
- `POST /api/trading-bridge/credentials/epex` - EPEX Spot Credentials speichern
- `POST /api/trading-bridge/credentials/apg` - APG Credentials speichern
- `GET /api/trading-bridge/status` - Status aller Trading-Adapter abrufen
- `GET /api/trading-bridge/credentials` - Aktuelle Credentials abrufen (maskiert)

#### Konfiguration
- `POST /api/config/save` - Konfiguration speichern
- `GET /api/config/load` - Konfiguration laden
- `POST /api/config/test` - Verbindungstests durchführen

### Umgebungsvariablen

#### WebApp Service
```bash
EXCHANGE_BASE_URL=http://exchange:9000
FORECAST_BASE_URL=http://forecast:9500
GRID_BASE_URL=http://grid:9501
RISK_BASE_URL=http://risk:9502
CREDIT_BASE_URL=http://credit:9503
BILLING_BASE_URL=http://billing:9504
API_KEY=demo
HMAC_SECRET=phoenyra_demo_secret
FLASK_ENV=development
FLASK_DEBUG=1
```

#### Exchange Service
```bash
SQLITE_PATH=/app/exchange.db
REDIS_HOST=redis
REDIS_DB=0
POLICY_PATH=/app/policy/policy.yaml
HMAC_SECRET=phoenyra_demo_secret
```

#### ETRM Services (Forecast, Grid, Risk, Credit, Billing)
Alle Services laufen mit Standard-Umgebungsvariablen und benötigen keine zusätzliche Konfiguration für den Basiseinsatz. Prometheus-Metriken werden automatisch unter `/metrics` bereitgestellt.

#### Trading Bridge Service
```bash
EXCHANGE_BASE_URL=http://exchange:9000
EPEX_USERNAME=${EPEX_USERNAME:-}
EPEX_PASSWORD=${EPEX_PASSWORD:-}
EPEX_API_KEY=${EPEX_API_KEY:-}
EPEX_TEST_MODE=${EPEX_TEST_MODE:-true}
APG_MPID=${APG_MPID:-}
APG_BILANZGRUPPE=${APG_BILANZGRUPPE:-}
APG_AS4_ENDPOINT=${APG_AS4_ENDPOINT:-}
```

## 🆕 Was ist neu? (v3.0 - 05.11.2025)

### Chart-Historie & Persistenz (05.11.2025)
- ✅ **Persistente Chart-Historie** mit localStorage - Daten bleiben beim Seitenwechsel erhalten
- ✅ **Hybrid-Sync** mit Server-Backup - Automatische Synchronisation zwischen Client und Server (alle 60 Sekunden)
- ✅ **Einstellungs-UI** für Historie-Dauer (0.5-24h), maximale Datenpunkte (60-7200), Auto-Sync und Auto-Play
- ✅ **Export-Funktion** für Chart-Daten (JSON/CSV Format) - Direkter Download im Browser
- ✅ **Chart-Reset-Button** zum Zurücksetzen der Historie mit Sicherheitsabfrage
- ✅ **Verbesserte Legende** mit vollständigen Beschreibungen (Markt Preis, EMA (Exponential Moving Average), VWAP (Volume-Weighted Average Price))
- ✅ **Vertikale Legende-Anordnung** für bessere Lesbarkeit
- ✅ **Server-seitige Historie** in SQLite für längere Zeiträume (24 Stunden)
- ✅ **Neue API-Endpunkte**: `/api/market/history` und `/api/market/history/sync`
- ✅ **Automatisierter Handel Dokumentation** (Markdown & HTML) - Vollständige Erklärung des automatisierten Handels

### Trading-Bridge Integration (04.11.2025)
- ✅ **Trading Bridge Service** für Routing zu externen Plattformen (EPEX Spot, APG)
- ✅ **Trading-Config Dashboard** für Credentials-Verwaltung
- ✅ **Order-Formular erweitert** mit Plattform-Auswahl (Intern / EPEX Spot / APG)
- ✅ **Trading-Bridge-Konzept-Dokumentation** mit vollständiger Integration-Anleitung
- ✅ **Marktpreis-Chart verbessert** auf Zeitreihen-Chart umgestellt
- ✅ **Umrechnungsfehler behoben** (ct/kWh → EUR/MWh)

### ETRM Services Integration (01.11.2025)
- ✅ **5 neue Enterprise Services** integriert (Forecast, Risk, Grid, Credit, Billing)
- ✅ **5 neue Dashboards** mit interaktiven Charts
- ✅ **Prometheus-Monitoring** für alle Services
- ✅ **Active Menu Highlighting** für bessere UX
- ✅ **Navigation optimiert** und bereinigt

### Highlights
- 🔮 **Forecast**: Automatische Preis- und Lastprognosen für optimales Trading
- 🛡️ **Risk**: VaR-Berechnung und Risk-Limit-Überwachung
- ⚡ **Grid**: Echtzeit-Netzfrequenz-Monitoring mit Constraint-Alerts
- 💳 **Credit**: Counterparty Exposure Management
- 💰 **Billing**: Automatische Invoice-Generierung
- 📊 **Chart-Persistenz**: Historie bleibt beim Seitenwechsel erhalten
- 🔄 **Hybrid-Sync**: Nahtlose Synchronisation zwischen Client und Server

---

## Installation und Start

### Voraussetzungen
- Docker und Docker Compose
- Python 3.11+
- Node.js (für WebSocket-Verbindungen)

### Installation
```bash
# Repository klonen
git clone <repository-url>
cd phoenyra_BESS_Trade

# Docker Container starten
docker compose up -d --build

# Services überprüfen
docker compose ps
```

### Zugriff auf Services
- **Web-Dashboard**: http://localhost:5000
  - **Dashboard**: http://localhost:5000/
  - **Forecast**: http://localhost:5000/forecast
  - **Risk**: http://localhost:5000/risk
  - **Grid**: http://localhost:5000/grid
  - **Credit**: http://localhost:5000/credit
  - **Billing**: http://localhost:5000/billing
  - **Konfiguration**: http://localhost:5000/config
  - **Trading-Config**: http://localhost:5000/trading-config
- **Exchange API**: http://localhost:9000/docs
- **Forecast API**: http://localhost:9500/docs
- **Grid API**: http://localhost:9501/docs
- **Risk API**: http://localhost:9502/docs
- **Credit API**: http://localhost:9503/docs
- **Billing API**: http://localhost:9504/docs
- **Trading Bridge API**: http://localhost:9510/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## Entwicklung

### Live-Reload
Das System unterstützt Live-Reload für Entwicklung:
- **Flask Debug Mode** aktiviert
- **Docker Volume Mounting** für sofortige Änderungen
- **Automatische Neuladung** bei Code-Änderungen

### Code-Struktur
```
webapp/
├── app.py                 # Flask Hauptanwendung
├── templates/
│   ├── base.html          # Basis-Template mit Navigation
│   ├── dashboard.html     # Dashboard-Template
│   ├── config.html        # BESS-Konfigurationsseite
│   ├── forecast.html      # Forecast Dashboard
│   ├── risk.html          # Risk Management Dashboard
│   ├── grid.html          # Grid Status Dashboard
│   ├── credit.html        # Credit Management Dashboard
│   ├── billing.html       # Billing Dashboard
│   ├── trading-config.html # Trading-Plattform Konfiguration
│   └── trading-bridge-konzept.html # Trading-Bridge Dokumentation
├── static/
│   └── phoenyra_logo.png  # Logo
└── Dockerfile             # Container-Definition

exchange/
├── server.py              # FastAPI Backend
├── market_feed.py         # ENTSO-E Marktdaten
├── bess_telemetry.py      # BESS Telemetrie-Service
├── config.py              # Zentrale Konfiguration
└── requirements.txt       # Python Dependencies

etrm/
├── forecast/
│   ├── main.py            # Forecast API
│   ├── requirements.txt   # Dependencies
│   └── Dockerfile         # Container-Definition
├── grid/
│   ├── main.py            # Grid API
│   ├── requirements.txt
│   └── Dockerfile
├── risk/
│   ├── main.py            # Risk API
│   ├── requirements.txt
│   └── Dockerfile
├── credit/
│   ├── main.py            # Credit API
│   ├── requirements.txt
│   └── Dockerfile
├── billing/
│   ├── main.py            # Billing API
│   ├── requirements.txt
│   └── Dockerfile
├── trading-bridge/
│   ├── main.py            # Trading Bridge Service
│   ├── requirements.txt
│   └── Dockerfile
├── openapi/               # OpenAPI Spezifikationen
│   ├── forecast.yaml
│   ├── grid.yaml
│   ├── risk.yaml
│   ├── credit.yaml
│   └── billing.yaml
├── grafana_dashboards/     # Grafana Dashboard Templates
│   ├── forecast_vs_actual.json
│   ├── risk_var_limits.json
│   └── backoffice_kpis.json
└── n8n_workflows/         # n8n Automation Workflows
    ├── wf_entsoe_forecast_strategy_order.json
    └── wf_grid_constraints_policy_reload.json

prometheus/
└── prometheus.yml         # Prometheus-Konfiguration für alle Services

grafana/
└── provisioning/
    ├── dashboards/
    │   └── etrm_services.json  # ETRM Services Dashboard
    └── datasources/
        └── prom.yaml      # Prometheus Datasource
```

## Design-System

### Farbpalette
- **Primär**: Dunkle Grautöne (#1a1a1a, #2d2d2d)
- **Akzent**: Gold (#FFD700) für Highlights
- **Charts**: Sattes Grün (#00FF00) für optimale Sichtbarkeit
- **Text**: Weiß (#FFFFFF) für Kontrast

### Magic UI Effekte
- **Gradient Backgrounds** mit subtilen Gold-Akzenten
- **Backdrop Blur** für moderne Glasmorphismus-Effekte
- **Hover-Animationen** für interaktive Elemente
- **Aurora Text** für dynamische Überschriften
- **Shimmer Buttons** für Call-to-Action-Elemente

## Monitoring und Metriken

### Prometheus Metriken

#### Exchange & Trading
- **BESS-Status**: SoC, Leistung, Temperatur
- **Trading-Metriken**: Orders, Trades, Volumen
- **System-Performance**: API-Response-Zeiten, Fehlerraten

#### Forecast Service
- `pho_forecast_jobs_total{type="dayahead|intraday"}` - Anzahl Forecast-Jobs
- `pho_forecast_price_eur_mwh{horizon="24h|12h"}` - Preisprognose
- `pho_forecast_load_mw{horizon="24h|12h"}` - Lastprognose
- `pho_forecast_solar_mw{horizon="24h|12h"}` - Solarprognose
- `pho_forecast_wind_mw{horizon="24h|12h"}` - Windprognose

#### Risk Service
- `pho_risk_var_99_eur` - VaR 99% in EUR
- `pho_risk_var_95_eur` - VaR 95% in EUR
- `pho_risk_limit_utilization_pct` - Limit-Auslastung in %

#### Grid Service
- `pho_grid_freq_hz` - Netzfrequenz in Hz
- `pho_grid_load_mw` - Netzlast in MW

#### Credit Service
- `pho_credit_exposure_eur{counterparty="CP-A"}` - Exposure pro Counterparty

#### Billing Service
- `pho_bo_invoices_total` - Gesamtanzahl generierter Rechnungen

### Grafana Dashboards
- **BESS-Überwachung**: SoC, Leistung, Temperatur-Trends
- **Trading-Analytics**: Order-Volumen, PnL, Marktpreise
- **ETRM Services Monitoring**: Forecast, Risk, Grid Metriken
- **System-Health**: API-Status, Response-Zeiten, Fehlerraten

### Prometheus Queries (PromQL)

#### Beispiel-Queries
```promql
# Durchschnittliche Netzfrequenz der letzten 5 Minuten
avg_over_time(pho_grid_freq_hz[5m])

# VaR über 90% des Limits?
pho_risk_limit_utilization_pct > 90

# Forecast-Jobs pro Stunde
sum(rate(pho_forecast_jobs_total[1h])) * 3600

# Alle Services UP?
count(up{job=~"forecast|grid|risk|credit|billing"})
```

**Detaillierte Prometheus-Anleitung**: Siehe `PROMETHEUS_GUIDE.md`

## Sicherheit

### Authentifizierung
- **API-Key-basierte** Authentifizierung
- **HMAC-SHA256** Signaturen für WebSocket-Verbindungen
- **Key-Rotation** für erweiterte Sicherheit

### Datenübertragung
- **HTTPS** für sichere Kommunikation
- **WebSocket-Verschlüsselung** für Real-time-Daten
- **Input-Validierung** für alle Benutzereingaben

## Marktpreis-Integration

### Live-Marktdaten
Das System integriert Live-Marktpreise von verschiedenen Energiebörsen:

#### ENTSO-E Integration (EPEX Spot)
- **API**: `https://web-api.tp.entsoe.eu/api`
- **Regionen**: Österreich (AT), Deutschland (DE), Schweiz (CH), Italien (IT)
- **Update-Intervall**: Alle 5 Minuten (konfigurierbar)
- **Preiseinheit**: EUR/MWh
- **Datenformat**: Day-ahead Preise (PT15M, PT60M)
- **API-Token**: Konfigurierbar in config.py
- **Rate Limiting**: 1 Sekunde zwischen Requests

### Marktpreis-Register
Die Marktpreise werden im System in folgenden Formaten gespeichert:
- **Mark Price**: Aktueller Marktpreis
- **EMA**: Exponentiell gleitender Durchschnitt (α=0.2)
- **VWAP**: Volume-Weighted Average Price (über 96 Zeitpunkte)

### Konfiguration
```bash
# Market Feed Service Umgebungsvariablen
EXCHANGE_URL=http://exchange:9000
MARKET=epex_at
UPDATE_INTERVAL=300  # Sekunden
ENTSO_E_TOKEN=2793353d-b5dd-4d4f-9638-8e26c88027e5

# BESS Telemetry Service Umgebungsvariablen
BESS_MODBUS_ENABLED=false
BESS_MODBUS_HOST=192.168.1.100
BESS_MODBUS_PORT=502
BESS_MODBUS_UNIT_ID=1
BESS_MODBUS_SOC_REGISTER=0
BESS_MODBUS_POWER_REGISTER=1
BESS_MODBUS_TEMP_REGISTER=2
BESS_MQTT_ENABLED=false
BESS_MQTT_BROKER=localhost
BESS_MQTT_PORT=1883
BESS_MQTT_TOPIC_SOC=bess/soc
BESS_MQTT_TOPIC_POWER=bess/power
BESS_MQTT_TOPIC_TEMP=bess/temperature
BESS_REST_ENABLED=true
BESS_API_KEY=bess_telemetry_key
BESS_UPDATE_INTERVAL=30
```

## Erweiterte Funktionen

### Real-time Updates
- **WebSocket-Verbindungen** für Live-Daten
- **Automatische Aktualisierung** alle 10 Sekunden
- **Echtzeit-Chart-Updates** ohne Seitenneuladung
- **Live-Marktpreise** von aWattar (alle 5 Minuten)

### Responsive Design
- **Mobile-First** Ansatz
- **Flexible Grid-Layouts** für verschiedene Bildschirmgrößen
- **Touch-optimierte** Bedienelemente

### Performance-Optimierung
- **Lazy Loading** für Chart-Komponenten
- **Efficient Data Fetching** mit Caching
- **Minimierte Bundle-Größe** für schnelle Ladezeiten

## Troubleshooting

### Häufige Probleme
1. **Container startet nicht**: Docker-Logs überprüfen
2. **Charts werden nicht angezeigt**: Browser-Konsole auf Fehler prüfen
3. **API-Verbindung fehlschlägt**: Exchange-Service-Status überprüfen

### Debug-Modi
```bash
# Flask Debug-Modus
FLASK_DEBUG=1

# Docker-Logs anzeigen
docker compose logs -f webapp

# Container-Shell öffnen
docker exec -it webapp bash
```

## Automatische Order-Ausführung (Matching-Engine)

### Übersicht
Das System verfügt über eine vollautomatische **Matching-Engine**, die eingehende Orders sofort mit kompatiblen Gegenorders matcht und Trades ausführt. Die Implementierung folgt bewährten Praktiken aus dem Electronic Trading.

### Funktionsweise

#### 1. Order-Erstellung
Jede neue Order wird in der SQLite-Datenbank gespeichert mit Status `ACCEPTED` und `filled = 0.0` (noch keine Ausführung).

#### 2. Automatisches Matching
Sofort nach dem Speichern startet die Matching-Engine (`try_match_order`):

**Für BUY-Orders:**
- Sucht SELL-Orders im selben Markt
- Bedingung: `ask_price ≤ limit_price`
- Sortierung: Preis aufsteigend, dann Zeitstempel

**Für SELL-Orders:**
- Sucht BUY-Orders im selben Markt
- Bedingung: `bid_price ≥ limit_price`
- Sortierung: Preis absteigend, dann Zeitstempel

#### 3. Trade-Ausführung
Wenn eine passende Order gefunden wird:
1. **Volumen-Berechnung:** `min(remaining_qty, match_available)`
2. **Preis-Berechnung:** Durchschnitt aus beiden Limit-Preisen
3. **Trade-Write:** In Datenbank schreiben
4. **Order-Update:** `filled` erhöhen, Status auf `FILLED` wenn vollständig
5. **WebSocket-Event:** An alle Clients senden

### Besonderheiten
- **Teilausführungen möglich:** Orders können mehrfach matchen
- **Fairer Preis:** Durchschnitt aus Buy- und Sell-Limit
- **Sofortige Ausführung:** Matching erfolgt unmittelbar nach Order-Erstellung
- **Faire Reihenfolge:** Preis → Zeitstempel (First-Come-First-Served)
- **Robustheit:** Atomare Transaktionen, keine Inkonsistenzen

### Integration
Die Matching-Engine ist integriert mit:
- **SoC-Limits:** BUY nur bei SoC ≥ 15%, SELL nur bei SoC ≤ 90%
- **Throttling:** Rate-Limiting pro Markt
- **Exposure-Tracking:** Automatische Berechnung
- **Prometheus-Metriken:** G_EXPO_E, G_EXPO_N, G_PNL_REAL

**Detaillierte Dokumentation:** Siehe `Matching-Engine-Dokumentation.md`

## Features-Historie

### Legacy Features (v2.0)

### 1. Live-Marktpreise von EPEX Spot
- **Datenquelle:** EPEX Spot Day-Ahead Preise (Österreich)
- **Provider:** ENTSO-E Transparency Platform
- **API-Integration:** XML-Parsing mit automatischer Umwandlung
- **Zeitauflösung:** PT15M und PT60M
- **Update-Intervall:** Alle 5 Minuten (konfigurierbar)

### 2. Automatische Matching-Engine
- **Vollautomatische Order-Ausführung**
- **Orderbuch-Matching** mit fairem Preis
- **Teilausführungen** unterstützt
- **Echtzeit-Trade-Generierung**

### 3. Enhanced Dashboard Features
- **Flash Messages** für Benutzer-Feedback
- **Order-Management** mit Status-Anzeige
- **Trade-Historie** mit Zeitstempeln
- **Einheiten-Anzeige** (EUR/MWh) in Charts
- **VWAP-Beschreibung** ("Volume-Weighted Average Price")
- **Marktdaten-Quelle** Anzeige (EPEX Spot)

### 4. API-Endpunkte
- **GET /orders:** Alle Orders abrufen
- **GET /trades:** Alle Trades abrufen
- **POST /order:** Order über Form erstellen
- **GET /market/prices:** Marktpreise abrufen

### 5. Datenbank-Erweiterungen
- **Orders-Tabelle:** Order-Status-Tracking
- **Trades-Tabelle:** Trade-Historie
- **Filled-Feld:** Teilausführungen verfolgen

## BESS Telemetrie-Integration (Goldstandard)

### 6. Vollständige BESS Telemetrie-System
- **Modbus TCP Integration:** Direkte Anbindung an BESS-Anlagen und Wechselrichter
- **MQTT Support:** IoT-Sensoren und Smart-Grid-Systeme
- **REST API:** Externe Systeme und Integrationen
- **Konfigurierbare Register:** User-definierte Modbus-Register-Adressen
- **Topic-Mapping:** Flexible MQTT-Topic-Konfiguration
- **API-Key-Authentifizierung:** Sichere externe Integration

### 7. Benutzerfreundliche Konfiguration
- **Tab-basierte Navigation:** Modbus TCP, MQTT, REST API
- **Vordefinierte Presets:** SMA, Fronius, Tesla Powerwall
- **Live-Verbindungstests:** Visuelle Rückmeldung für alle Schnittstellen
- **Register-Mapping:** SoC, Power, Temperature Register konfigurierbar
- **MQTT-Topics:** Flexible Topic-Definition für Sensoren
- **Flash Messages:** Erfolg/Fehler-Feedback für Konfiguration

### 8. Enterprise-Grade Telemetrie-Features
- **Real-time Data Collection:** Automatische Telemetrie-Erfassung
- **Multi-Source Support:** Modbus, MQTT, REST API parallel
- **Configurable Intervals:** Anpassbare Update-Intervalle
- **Error Handling:** Robuste Fehlerbehandlung und Fallbacks
- **Logging:** Detaillierte Logs für Debugging und Monitoring
- **Docker Integration:** Containerisierte Services für Skalierbarkeit

### 9. Erweiterte API-Endpunkte
- **POST /api/bess/telemetry:** Externe Telemetrie-Daten empfangen
- **GET /api/bess/status:** Aktuelle BESS-Status abrufen
- **POST /api/config/save:** Konfiguration speichern
- **GET /api/config/load:** Konfiguration laden
- **POST /api/config/test:** Verbindungstests durchführen

### 10. Konfigurationsseite (/config)
- **Modbus TCP Tab:** Register-Adressen für BESS-Anlage/Wechselrichter
- **MQTT Tab:** Topics für IoT-Sensoren und Smart-Grid
- **REST API Tab:** API-Key und Endpoints für externe Systeme
- **Verbindungstests:** Live-Tests für alle Schnittstellen
- **Preset-Konfigurationen:** Vordefinierte Einstellungen für gängige Systeme

## ETRM Services Integration (2025-11-01)

### Phase 1: Forecast, Risk & Grid Integration ✅

#### Forecast API (Port 9500)
- **Day-Ahead Prognosen**: 24h Preis-, Last-, Solar- und Windprognosen
- **Intraday Prognosen**: 12h Kurzfristprognosen für intraday Trading
- **SOC-Optimierung**: Automatische Berechnung optimaler Ladezustände für BESS
- **Features**:
  - Job-basierte Forecast-Generierung
  - Verschiedene Prognosehorizonte (konfigurierbar)
  - Multi-Resolution Support (15min, 60min Granularität)
  - Prometheus-Metriken für alle Prognose-Typen

#### Risk API (Port 9502)
- **VaR-Berechnung**: Value at Risk mit 95%, 99%, 99.5% Konfidenzniveau
- **Expected Shortfall (CVaR)**: Conditional Value at Risk
- **Risk Limits**: Portfolio-weite Risikolimits (PnL, VaR)
- **Features**:
  - Monte-Carlo Simulation (konfigurierbare Pfadanzahl)
  - Risk Limit Utilization Tracking
  - Automatische Alert-Generierung bei Limit-Überschreitungen
  - Echtzeit-Risiko-Monitoring

#### Grid API (Port 9501)
- **Netzfrequenz-Monitoring**: Echtzeit-Überwachung (49.7-50.3 Hz)
- **Grid Constraints**: Redispatch, Wartungen, Kapazitätsengpässe
- **Tie-Line Flows**: Grenzkapazitäten und Flussrichtung (Export/Import)
- **Features**:
  - Echtzeit-Frequenz-Tracking mit historischen Charts
  - Grid Constraint Alerts
  - Congestion Index Berechnung
  - Multi-Area Support (AT, DE, CZ, etc.)

### Phase 2: Credit & Billing Integration ✅

#### Credit API (Port 9503)
- **Counterparty Exposure Tracking**: Echtzeit-Überwachung des Exposure pro Counterparty
- **Credit Limit Management**: Setzen und Verwalten von Credit Limits
- **Utilization Monitoring**: Automatische Berechnung der Limit-Auslastung
- **Features**:
  - Multi-Counterparty Support
  - Exposure-Verlauf-Charts
  - Automatische Alerts bei hoher Auslastung (>75%, >90%)
  - Prometheus-Metriken pro Counterparty

#### Billing API (Port 9504)
- **Invoice-Generierung**: Automatische Rechnungserstellung pro Zeitraum
- **PDF-Export**: Download-Funktion für generierte Rechnungen
- **Statistiken**: Gesamtbetrag, Anzahl Rechnungen, letzte Rechnung
- **Features**:
  - Perioden-basierte Generierung (YYYY-MM Format)
  - Multi-Counterparty Billing
  - Invoice-Historie
  - Counter-basierte Metriken

### Dashboard-Integrationen

#### Forecast Dashboard (`/forecast`)
- Interaktive Charts für Preis-, Last-, Solar- und Windprognosen
- SOC-Zielwerte Visualisierung
- Day-Ahead vs. Intraday Vergleich
- Real-time Updates beim Forecast-Job

#### Risk Dashboard (`/risk`)
- VaR-Verlauf-Chart mit kontinuierlichem Zeitreihen-Diagramm
- Risk Limits Anzeige mit Utilization
- Expected Shortfall Tracking
- Automatische Alarmierung bei kritischen Werten

#### Grid Dashboard (`/grid`)
- Live-Netzfrequenz-Chart mit Normalbereich-Markierungen
- Tie-Line Flows Visualisierung (AT-DE, AT-CZ)
- Grid Constraints Anzeige mit Timestamps
- Auto-Refresh konfigurierbar (2-10 Sekunden)

#### Credit Dashboard (`/credit`)
- Counterparty Exposure-Übersicht
- Credit Limit Management Interface
- Exposure-Verlauf-Charts
- Multi-Counterparty Liste mit Quick-Access

#### Billing Dashboard (`/billing`)
- Invoice-Übersicht mit Filterung
- PDF-Download-Funktion
- Statistiken (Gesamtbetrag, Anzahl, letzte Rechnung)
- Perioden-basierte Invoice-Generierung

### UI/UX Verbesserungen

#### Navigation
- **Aktive Menü-Hervorhebung**: Dezenter weißer Hintergrund mit goldener Unterlinie
- **Bereinigte Navigation**: Trading und BESS Status entfernt (auf Dashboard verfügbar)
- **Vertikales Datum/Zeit-Layout**: Platzsparendes Design
- **7 Haupt-Menüpunkte**: Dashboard, Konfiguration, Forecast, Risk, Grid, Credit, Billing

#### Visual Improvements
- **VaR-Grafik**: Von isolierten Punkten zu kontinuierlichem Area-Chart mit Gradient
- **Historische Daten**: Automatische Generierung für Charts
- **Responsive Layouts**: Optimiert für alle Bildschirmgrößen
- **Gold-Standard Design**: Konsistentes Design-System durchgehend

### Prometheus Monitoring

#### Neue Metriken
- **Forecast**: `pho_forecast_jobs_total`, `pho_forecast_price_eur_mwh`, `pho_forecast_load_mw`, `pho_forecast_solar_mw`, `pho_forecast_wind_mw`
- **Risk**: `pho_risk_var_99_eur`, `pho_risk_var_95_eur`, `pho_risk_limit_utilization_pct`
- **Grid**: `pho_grid_freq_hz`, `pho_grid_load_mw`
- **Credit**: `pho_credit_exposure_eur` (pro Counterparty)
- **Billing**: `pho_bo_invoices_total`

#### Grafana Dashboard
- **ETRM Services Monitoring**: Umfassendes Dashboard für alle neuen Services
- **Service Health**: UP/DOWN Status aller Services
- **Auto-Refresh**: 5 Sekunden Intervall für Echtzeit-Daten

## Roadmap

### Implementiert ✅
- **WebSocket-Integration** für Real-time-Updates
- **ETRM Services**: Forecast, Risk, Grid, Credit, Billing
- **Erweiterte Dashboards** mit interaktiven Charts
- **Prometheus Monitoring** für alle Services
- **Active Menu Highlighting** für bessere UX

### Geplante Features
- **Erweiterte Chart-Analyse** mit technischen Indikatoren
- **Mobile App** für BESS-Monitoring
- **Machine Learning** für Preisvorhersagen
- **Multi-Market-Support** für verschiedene Energiebörsen
- **Automated Trading Strategies** basierend auf Forecast-Daten
- **Risk-basierte Order-Throttling** Integration

### Performance-Verbesserungen
- **Caching-Strategien** für bessere Performance
- **Database-Optimierung** für große Datenmengen
- **CDN-Integration** für statische Assets

## Support und Wartung

### Logs und Monitoring
- **Strukturierte Logs** für einfache Fehlerdiagnose
- **Health-Checks** für alle Services
- **Automatische Alerts** bei kritischen Problemen

### Updates und Wartung
- **Regelmäßige Security-Updates**
- **Performance-Monitoring** und Optimierung
- **Feature-Updates** basierend auf Benutzerfeedback

## Zusammenfassung der Features

### Core Trading System
- ✅ Vollautomatische Matching-Engine
- ✅ ENTSO-E/EPEX Spot Integration
- ✅ BESS Telemetrie (Modbus, MQTT, REST)
- ✅ Real-time WebSocket-Updates
- ✅ Order Management & Trade History
- ✅ Persistente Chart-Historie (localStorage + Server-Sync)
- ✅ Chart-Einstellungen (Historie-Dauer, Auto-Sync, Auto-Play)
- ✅ Export-Funktion (JSON/CSV)
- ✅ Chart-Reset-Button

### ETRM Services (2025-11-01)
- ✅ **Forecast API**: Day-Ahead & Intraday Prognosen
- ✅ **Risk API**: VaR, Expected Shortfall, Risk Limits
- ✅ **Grid API**: Netzfrequenz, Constraints, Tie-Lines
- ✅ **Credit API**: Counterparty Exposure Management
- ✅ **Billing API**: Invoice-Generierung & PDF-Export

### Dashboards
- ✅ **Haupt-Dashboard**: Trading, BESS Status, Marktdaten
- ✅ **Forecast Dashboard**: Interaktive Prognose-Charts
- ✅ **Risk Dashboard**: VaR-Verlauf & Limit-Überwachung
- ✅ **Grid Dashboard**: Live-Netzfrequenz & Constraints
- ✅ **Credit Dashboard**: Exposure-Tracking & Limits
- ✅ **Billing Dashboard**: Invoice-Verwaltung

### Monitoring & Analytics
- ✅ Prometheus Metriken für alle Services
- ✅ Grafana Dashboards
- ✅ Real-time Alerting
- ✅ Service Health Monitoring

### UI/UX
- ✅ Modern Dark-Mode Design
- ✅ Gold-Standard Design-System
- ✅ Active Menu Highlighting
- ✅ Verbesserte Chart-Legende mit vollständigen Beschreibungen
- ✅ Vertikale Legende-Anordnung
- ✅ Responsive Layout
- ✅ Interaktive Charts (ApexCharts)

---

**© 2025 Phoenyra.com by Ing. Heinz Schlagintweit. Alle Rechte vorbehalten.**

*Diese Dokumentation beschreibt das Phoenyra BESS Trade System v3.0 (ULTRA OMEGA+) mit allen implementierten Features inkl. vollständiger ETRM Services Integration, Chart-Historie-Persistenz und automatisiertem Handel (Stand: 05.11.2025).*
