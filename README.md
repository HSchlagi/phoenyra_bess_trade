# Phoenyra BESS Trade System

## 🚀 Übersicht

Das Phoenyra BESS Trade System ist eine moderne Web-Anwendung für das Trading und die Optimierung von Battery Energy Storage Systems (BESS). Das System kombiniert eine FastAPI-basierte Backend-Architektur mit einer Flask-basierten Web-Oberfläche, die mit Tailwind CSS und Magic UI Komponenten gestaltet wurde.

## ✨ Features

### Core Trading System
- **🎨 Moderne Web-Oberfläche** mit Flask + Tailwind CSS
- **🔮 Magic UI Komponenten** (Aurora Text, Neon Cards, Shimmer Buttons)
- **📊 Professionelle Charts** mit ApexCharts
- **💾 Persistente Chart-Historie** mit localStorage + Server-Sync
- **⚙️ Chart-Einstellungen** (Historie-Dauer, Auto-Sync, Auto-Play)
- **📥 Export-Funktion** für Chart-Daten (JSON/CSV)
- **🔄 Chart-Reset** für Historie-Management
- **🔋 BESS-Status-Monitoring** (SoC, Leistung, Temperatur)
- **💹 Trading-Funktionen** (Orders, Trades, Marktpreise)
- **⚙️ Automatische Matching-Engine** für sofortige Order-Ausführung
- **🌐 ENTSO-E/EPEX Spot Integration** für Live-Marktpreise
- **📱 Responsive Design** für alle Bildschirmgrößen
- **🐳 Docker-Containerisierung** mit Live-Reload
- **⚡ Real-time Updates** mit WebSocket

### ETRM Services (Enterprise Trading & Risk Management)
- **🔮 Forecast API**: Day-Ahead & Intraday Preisprognosen
- **🛡️ Risk API**: VaR-Berechnung (Value at Risk) und Risk Limits
- **⚡ Grid API**: Netzfrequenz-Monitoring und Grid-Constraints
- **💳 Credit API**: Counterparty Exposure Management
- **💰 Billing API**: Automatische Rechnungserstellung mit PDF-Export
- **🌉 Trading Bridge Service**: Routing zu externen Trading-Plattformen (EPEX Spot, APG)

### Dashboards
- **📊 Haupt-Dashboard**: Trading, BESS Status, Marktdaten
- **🔮 Forecast Dashboard**: Interaktive Prognose-Charts
- **📈 Risk Dashboard**: VaR-Verlauf & Limit-Überwachung
- **🔌 Grid Dashboard**: Live-Netzfrequenz & Constraints
- **💳 Credit Dashboard**: Exposure-Tracking & Limits
- **💰 Billing Dashboard**: Invoice-Verwaltung
- **🔑 Trading-Config**: Credentials-Verwaltung für externe Trading-Plattformen

## 🏗️ Architektur

### Backend-Services
- **Exchange Service** (FastAPI): Kern-Trading-Engine (Port 9000)
- **Market Feed Service**: Live-Marktpreise von ENTSO-E/EPEX Spot
- **BESS Telemetry Service**: Automatische Telemetrie (Modbus TCP, MQTT, REST)
- **Forecast API** (FastAPI): Day-Ahead & Intraday Prognosen (Port 9500)
- **Risk API** (FastAPI): VaR-Berechnung und Risk Limits (Port 9502)
- **Grid API** (FastAPI): Netzfrequenz & Grid-Constraints (Port 9501)
- **Credit API** (FastAPI): Counterparty Exposure Management (Port 9503)
- **Billing API** (FastAPI): Rechnungserstellung & PDF-Export (Port 9504)
- **Trading Bridge Service** (FastAPI): Routing zu externen Trading-Plattformen (Port 9510)
- **Redis**: In-Memory-Datenbank für Caching
- **Prometheus**: Metriken-Sammlung und Monitoring (Port 9090)
- **Grafana**: Visualisierung und Alerting (Port 3000)
- **Webapp Service** (Flask): Web-Dashboard (Port 5000)

### Frontend-Technologien
- **Flask**: Python Web Framework
- **Tailwind CSS**: Utility-first CSS Framework
- **Magic UI**: Moderne UI-Komponenten
- **ApexCharts**: Professionelle Chart-Bibliothek
- **Socket.IO**: Real-time Kommunikation

## 🚀 Installation

### Voraussetzungen
- Docker und Docker Compose
- Python 3.11+
- Git

### Schnellstart
```bash
# Repository klonen
git clone https://github.com/HSchlagi/phoenyra_bess_trade.git
cd phoenyra_bess_trade

# Docker Container starten
docker compose up -d --build

# Services überprüfen
docker compose ps
```

### Zugriff auf Services

#### Web-Dashboards
- **🌐 Haupt-Dashboard**: http://localhost:5000
- **🔮 Forecast**: http://localhost:5000/forecast
- **📈 Risk**: http://localhost:5000/risk
- **🔌 Grid**: http://localhost:5000/grid
- **💳 Credit**: http://localhost:5000/credit
- **💰 Billing**: http://localhost:5000/billing
- **⚙️ Konfiguration**: http://localhost:5000/config
- **🔑 Trading-Config**: http://localhost:5000/trading-config

#### API-Dokumentation
- **🔌 Exchange API**: http://localhost:9000/docs
- **🔮 Forecast API**: http://localhost:9500/docs
- **⚡ Grid API**: http://localhost:9501/docs
- **🛡️ Risk API**: http://localhost:9502/docs
- **💳 Credit API**: http://localhost:9503/docs
- **💰 Billing API**: http://localhost:9504/docs
- **🌉 Trading Bridge API**: http://localhost:9510/docs

#### Monitoring
- **📈 Grafana**: http://localhost:3000 (admin/admin)
- **📊 Prometheus**: http://localhost:9090

## 📋 Verwendung

### Dashboards

#### Haupt-Dashboard
- **BESS-Status-Monitoring** in Echtzeit
- **Trading-Operations** mit Order-Management
- **Marktpreise-Visualisierung** mit Zeitreihen-Charts
- **Persistente Chart-Historie** - Daten bleiben beim Seitenwechsel erhalten
- **Chart-Einstellungen** - Historie-Dauer, Auto-Sync, Auto-Play konfigurierbar
- **Export-Funktion** - Chart-Daten als JSON oder CSV exportieren
- **Chart-Reset** - Historie zurücksetzen
- **Trading-Plattform-Auswahl** (Interner Exchange / EPEX Spot / APG)
- **Automatische Order-Ausführung** via Matching-Engine

#### ETRM-Dashboards
- **Forecast Dashboard**: Preis-, Last-, Solar- und Windprognosen mit SOC-Optimierung
- **Risk Dashboard**: VaR-Verlauf, Risk Limits, Expected Shortfall
- **Grid Dashboard**: Live-Netzfrequenz, Tie-Line Flows, Grid-Constraints
- **Credit Dashboard**: Counterparty Exposure Tracking und Limit-Management
- **Billing Dashboard**: Invoice-Generierung, PDF-Download, Statistiken

### API-Endpunkte

#### Trading & Exchange
- `GET /api/bess-status` - BESS-Status abrufen
- `GET /api/market-data` - Marktdaten abrufen
- `GET /api/orders` - Aktive Orders abrufen
- `POST /api/orders` - Neue Order erstellen
- `POST /api/telemetry` - BESS-Telemetrie senden

#### Forecast
- `POST /api/forecast/dayahead` - Day-Ahead Forecast anfordern
- `POST /api/forecast/intraday` - Intraday Forecast anfordern
- `GET /api/forecast/status/{job_id}` - Forecast Job-Status

#### Risk
- `POST /api/risk/var` - VaR berechnen
- `GET /api/risk/limits` - Risk Limits abrufen

#### Grid
- `GET /api/grid/state` - Grid-Zustand abrufen
- `GET /api/grid/constraints` - Grid-Constraints abrufen

#### Credit
- `GET /api/credit/exposure` - Counterparty Exposure abrufen
- `POST /api/credit/limit` - Credit Limit setzen

#### Billing
- `POST /api/billing/generate` - Rechnung generieren
- `GET /api/billing/invoice/{id}` - Invoice PDF herunterladen

#### Trading Bridge
- `POST /api/trading-bridge/credentials/epex` - EPEX Spot Credentials speichern
- `POST /api/trading-bridge/credentials/apg` - APG Credentials speichern
- `GET /api/trading-bridge/status` - Status aller Trading-Adapter abrufen

## 🔧 Entwicklung

### Live-Reload
Das System unterstützt Live-Reload für Entwicklung:
```bash
# Flask Debug Mode aktiviert
FLASK_DEBUG=1
FLASK_ENV=development
```

### Code-Struktur
```
phoenyra_BESS_Trade/
├── webapp/                    # Flask Web-Dashboard
│   ├── app.py                 # Hauptanwendung
│   ├── templates/
│   │   ├── base.html          # Basis-Template mit Navigation
│   │   ├── dashboard.html      # Haupt-Dashboard
│   │   ├── forecast.html       # Forecast Dashboard
│   │   ├── risk.html          # Risk Dashboard
│   │   ├── grid.html          # Grid Dashboard
│   │   ├── credit.html        # Credit Dashboard
│   │   ├── billing.html       # Billing Dashboard
│   │   ├── config.html        # BESS-Konfiguration
│   │   ├── trading-config.html # Trading-Plattform Konfiguration
│   │   └── trading-bridge-konzept.html # Trading-Bridge Dokumentation
│   └── static/
│       └── phoenyra_logo.png
├── exchange/                  # Trading-Engine
│   ├── server.py              # FastAPI Backend
│   ├── market_feed.py         # ENTSO-E Integration
│   └── bess_telemetry.py      # Telemetrie-Service
├── etrm/                      # ETRM Services (Enterprise Trading & Risk Management)
│   ├── forecast/              # Forecast API
│   ├── grid/                  # Grid API
│   ├── risk/                  # Risk API
│   ├── credit/                # Credit API
│   ├── billing/               # Billing API
│   ├── trading-bridge/        # Trading Bridge Service
│   ├── openapi/               # OpenAPI Spezifikationen
│   ├── grafana_dashboards/    # Grafana Dashboard JSONs
│   └── n8n_workflows/         # n8n Workflow-Definitionen
├── prometheus/
│   └── prometheus.yml         # Monitoring-Konfiguration
├── grafana/
│   └── provisioning/          # Grafana Dashboards
├── docker-compose.yml         # Alle Services
└── Dokumentation_BESS_Trade.md # Vollständige Dokumentation
```

## 📊 Monitoring

### Prometheus Metriken

#### Core Trading
- **BESS-Status**: SoC, Leistung, Temperatur
- **Trading-Metriken**: Orders, Trades, Volumen
- **System-Performance**: API-Response-Zeiten

#### ETRM Services
- **Forecast**: `pho_forecast_jobs_total`, `pho_forecast_price_eur_mwh`, `pho_forecast_load_mw`
- **Risk**: `pho_risk_var_99_eur`, `pho_risk_limit_utilization_pct`
- **Grid**: `pho_grid_freq_hz`, `pho_grid_load_mw`
- **Credit**: `pho_credit_exposure_eur` (pro Counterparty)
- **Billing**: `pho_bo_invoices_total`
- **Trading Bridge**: Status und Konfiguration der externen Trading-Plattformen

### Grafana Dashboards
- **BESS-Überwachung**: SoC, Leistung, Temperatur-Trends
- **Trading-Analytics**: Order-Volumen, PnL, Marktpreise
- **ETRM Services Monitoring**: Forecast, Risk, Grid Metriken
- **System-Health**: API-Status, Response-Zeiten aller Services

**📖 Detaillierte Prometheus-Anleitung**: Siehe [PROMETHEUS_GUIDE.md](PROMETHEUS_GUIDE.md)

## 🔒 Sicherheit

- **API-Key-basierte** Authentifizierung
- **HMAC-SHA256** Signaturen für WebSocket-Verbindungen
- **Key-Rotation** für erweiterte Sicherheit
- **Input-Validierung** für alle Benutzereingaben

## 📚 Dokumentation

Vollständige Dokumentation finden Sie in:
- **[Dokumentation_BESS_Trade.md](Dokumentation_BESS_Trade.md)** - Vollständige System-Dokumentation (v3.0)
- **[AUTOMATISIERTER_HANDEL.md](AUTOMATISIERTER_HANDEL.md)** - Automatisierter Handel im Detail
- **[automatisierter_handel.html](automatisierter_handel.html)** - Automatisierter Handel (HTML)
- **[Summary_BESS_Trade.md](Summary_BESS_Trade.md)** - Zusammenfassung der ETRM-Integration
- **[TRADING_BRIDGE_KONZEPT.md](TRADING_BRIDGE_KONZEPT.md)** - Trading-Bridge Konzept & Integration
- **[Matching-Engine-Dokumentation.md](Matching-Engine-Dokumentation.md)** - Matching-Engine Details
- **[PROMETHEUS_GUIDE.md](PROMETHEUS_GUIDE.md)** - Prometheus Queries & Metriken
- **[Phoenyra_BESS_Trading_Final_Documentation_v2.md](Phoenyra_BESS_Trading_Final_Documentation_v2.md)** - Legacy Dokumentation v2.0

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## 📄 Lizenz

© 2025 Phoenyra.com by Ing. Heinz Schlagintweit. Alle Rechte vorbehalten.

## 🆘 Support

Bei Fragen oder Problemen:
- Erstelle ein [Issue](https://github.com/HSchlagi/phoenyra_bess_trade/issues)
- Kontaktiere uns unter: office@instanet.at

## 🆕 Was ist neu? (v3.0 - 05.11.2025)

### Chart-Historie & Persistenz (05.11.2025)
- ✅ **Persistente Chart-Historie** mit localStorage - Daten bleiben beim Seitenwechsel erhalten
- ✅ **Hybrid-Sync** mit Server-Backup - Automatische Synchronisation zwischen Client und Server
- ✅ **Einstellungs-UI** für Historie-Dauer, Auto-Sync und Auto-Play
- ✅ **Export-Funktion** für Chart-Daten (JSON/CSV Format)
- ✅ **Chart-Reset-Button** zum Zurücksetzen der Historie
- ✅ **Verbesserte Legende** mit vollständigen Beschreibungen (Markt Preis, EMA, VWAP)
- ✅ **Server-seitige Historie** in SQLite für längere Zeiträume (24 Stunden)
- ✅ **Automatisierter Handel Dokumentation** (Markdown & HTML)

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

**Vollständige Changelog**: Siehe [Summary_BESS_Trade.md](Summary_BESS_Trade.md)

---

**Phoenyra BESS Trade System v3.0 (ULTRA OMEGA+)** - Enterprise Trading & Risk Management für Battery Energy Storage Systems
