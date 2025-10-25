# Phoenyra BESS Trade System - Dokumentation

## Übersicht

Das Phoenyra BESS Trade System ist eine moderne Web-Anwendung für das Trading und die Optimierung von Battery Energy Storage Systems (BESS). Das System kombiniert eine FastAPI-basierte Backend-Architektur mit einer Flask-basierten Web-Oberfläche, die mit Tailwind CSS und Magic UI Komponenten gestaltet wurde.

## Architektur

### Backend-Services
- **Exchange Service** (FastAPI): Kern-Trading-Engine mit REST API
- **Market Feed Service**: Live-Marktpreise von aWattar und ETEnSo
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
- **Theme-Toggle** zwischen Dark und Light Mode
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
- **Aktive Orders** Übersicht
- **Recent Trades** Anzeige
- **Live-Marktpreise** von aWattar (Österreich/Deutschland)
- **Marktpreise** Visualisierung (Mark, EMA, VWAP)
- **VWAP-Chart** mit 15-Minuten-Intervallen

### 4. Chart-Visualisierung
- **ApexCharts Integration** für professionelle Charts
- **Marktpreise-Chart** mit Mark, EMA und VWAP
- **VWAP-Zeitreihen-Chart** mit 15-Minuten-Intervallen
- **Sattes Grün** für optimale Sichtbarkeit
- **Responsive Design** für verschiedene Bildschirmgrößen

### 5. Magic UI Komponenten
- **Aurora Text** für Überschriften
- **Neon Gradient Cards** für Status-Karten
- **Shimmer Buttons** für interaktive Elemente
- **Gold Standard Background** mit subtilen Gold-Akzenten
- **Hover-Effekte** und Animationen
- **Number Ticker** für animierte Zahlen

### 6. BESS Telemetrie-Steuerung
- **SoC-Management** mit Prozent-Eingabe
- **Leistungssteuerung** in MW
- **Temperatur-Überwachung** in °C
- **Telemetrie-Daten** an Backend senden

## Technische Details

### Docker-Container
```yaml
services:
  exchange:      # FastAPI Backend (Port 9000)
  market-feed:   # Live market price feed (aWattar/ETEnSo)
  redis:         # In-Memory Database
  prometheus:    # Metrics Collection (Port 9090)
  grafana:       # Visualization (Port 3000)
  webapp:        # Flask Frontend (Port 5000)
```

### API-Endpunkte
- `GET /api/bess-status` - BESS-Status abrufen
- `GET /api/market-data` - Marktdaten abrufen
- `GET /api/orders` - Aktive Orders abrufen
- `GET /api/trades` - Recent Trades abrufen
- `POST /api/orders` - Neue Order erstellen
- `POST /api/telemetry` - BESS-Telemetrie senden

### Umgebungsvariablen
```bash
EXCHANGE_BASE_URL=http://exchange:9000
API_KEY=demo
HMAC_SECRET=phoenyra_demo_secret
FLASK_ENV=development
FLASK_DEBUG=1
```

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
- **Exchange API**: http://localhost:9000
- **Grafana**: http://localhost:3000
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
├── app.py              # Flask Hauptanwendung
├── templates/
│   ├── base.html       # Basis-Template
│   └── dashboard.html  # Dashboard-Template
├── static/
│   └── phoenyra_logo.png  # Logo
└── Dockerfile          # Container-Definition
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
- **BESS-Status**: SoC, Leistung, Temperatur
- **Trading-Metriken**: Orders, Trades, Volumen
- **System-Performance**: API-Response-Zeiten, Fehlerraten

### Grafana Dashboards
- **BESS-Überwachung**: SoC, Leistung, Temperatur-Trends
- **Trading-Analytics**: Order-Volumen, PnL, Marktpreise
- **System-Health**: API-Status, Response-Zeiten, Fehlerraten

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

#### aWattar Integration
- **API**: `https://api.awattar.de/v1/marketdata`
- **Regionen**: Österreich (AT), Deutschland (DE)
- **Update-Intervall**: Alle 5 Minuten (konfigurierbar)
- **Preiseinheit**: EUR/MWh
- **Datenformat**: Day-ahead und Spot-Marktpreise

#### ETEnSo Integration (ENTSO-E)
- **Status**: Vorbereitet für ENTSO-E Transparency Platform
- **Benötigt**: API-Token von ENTSO-E
- **Dokumentation**: https://transparency.entsoe.eu/

### Marktpreis-Register
Die Marktpreise werden im System in folgenden Formaten gespeichert:
- **Mark Price**: Aktueller Marktpreis
- **EMA**: Exponentiell gleitender Durchschnitt (α=0.2)
- **VWAP**: Volume-Weighted Average Price (über 96 Zeitpunkte)

### Konfiguration
```bash
# Market Feed Service Umgebungsvariablen
EXCHANGE_URL=http://exchange:9000
MARKET=awattar_at
UPDATE_INTERVAL=300  # Sekunden
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

## Neu hinzugefügte Features (heute)

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

## Roadmap

### Geplante Features
- **WebSocket-Integration** für Real-time-Updates ✅ (bereits implementiert)
- **Erweiterte Chart-Analyse** mit technischen Indikatoren
- **Mobile App** für BESS-Monitoring
- **Machine Learning** für Preisvorhersagen
- **Multi-Market-Support** für verschiedene Energiebörsen

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

---

**© 2025 Phoenyra.com by Ing. Heinz Schlagintweit. Alle Rechte vorbehalten.**

*Diese Dokumentation beschreibt das Phoenyra BESS Trade System v2.0 mit allen implementierten Features und Funktionen.*
