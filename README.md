# Phoenyra BESS Trade System

![Phoenyra Logo](logo/Phoenyra_Logos/Phoenyra_Abstract.png)

## 🚀 Übersicht

Das Phoenyra BESS Trade System ist eine moderne Web-Anwendung für das Trading und die Optimierung von Battery Energy Storage Systems (BESS). Das System kombiniert eine FastAPI-basierte Backend-Architektur mit einer Flask-basierten Web-Oberfläche, die mit Tailwind CSS und Magic UI Komponenten gestaltet wurde.

## ✨ Features

- **🎨 Moderne Web-Oberfläche** mit Flask + Tailwind CSS
- **🔮 Magic UI Komponenten** (Aurora Text, Neon Cards, Shimmer Buttons)
- **📊 Professionelle Charts** mit ApexCharts
- **🔋 BESS-Status-Monitoring** (SoC, Leistung, Temperatur)
- **💹 Trading-Funktionen** (Orders, Trades, Marktpreise)
- **🌙 Theme-Toggle** (Dark/Light Mode)
- **📱 Responsive Design** für alle Bildschirmgrößen
- **🐳 Docker-Containerisierung** mit Live-Reload
- **⚡ Real-time Updates** mit WebSocket

## 🏗️ Architektur

### Backend-Services
- **Exchange Service** (FastAPI): Kern-Trading-Engine
- **Redis**: In-Memory-Datenbank für Caching
- **Prometheus**: Metriken-Sammlung und Monitoring
- **Grafana**: Visualisierung und Alerting
- **Webapp Service** (Flask): Web-Dashboard

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
- **🌐 Web-Dashboard**: http://localhost:5000
- **🔌 Exchange API**: http://localhost:9000
- **📈 Grafana**: http://localhost:3000
- **📊 Prometheus**: http://localhost:9090

## 📋 Verwendung

### Dashboard
Das Web-Dashboard bietet eine intuitive Benutzeroberfläche für:
- **BESS-Status-Monitoring** in Echtzeit
- **Trading-Operations** mit Order-Management
- **Marktpreise-Visualisierung** mit professionellen Charts
- **Theme-Switching** zwischen Dark und Light Mode

### API-Endpunkte
- `GET /api/bess-status` - BESS-Status abrufen
- `GET /api/market-data` - Marktdaten abrufen
- `GET /api/orders` - Aktive Orders abrufen
- `POST /api/orders` - Neue Order erstellen
- `POST /api/telemetry` - BESS-Telemetrie senden

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
webapp/
├── app.py              # Flask Hauptanwendung
├── templates/
│   ├── base.html       # Basis-Template
│   └── dashboard.html  # Dashboard-Template
├── static/
│   └── phoenyra_logo.png
└── Dockerfile
```

## 📊 Monitoring

### Prometheus Metriken
- **BESS-Status**: SoC, Leistung, Temperatur
- **Trading-Metriken**: Orders, Trades, Volumen
- **System-Performance**: API-Response-Zeiten

### Grafana Dashboards
- **BESS-Überwachung**: SoC, Leistung, Temperatur-Trends
- **Trading-Analytics**: Order-Volumen, PnL, Marktpreise
- **System-Health**: API-Status, Response-Zeiten

## 🔒 Sicherheit

- **API-Key-basierte** Authentifizierung
- **HMAC-SHA256** Signaturen für WebSocket-Verbindungen
- **Key-Rotation** für erweiterte Sicherheit
- **Input-Validierung** für alle Benutzereingaben

## 📚 Dokumentation

Vollständige Dokumentation finden Sie in:
- [Dokumentation_BESS_Trade.md](Dokumentation_BESS_Trade.md)
- [Phoenyra_BESS_Trading_Final_Documentation_v2.md](Phoenyra_BESS_Trading_Final_Documentation_v2.md)

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

---

**Phoenyra BESS Trade System v2.0** - Moderne Trading-Lösung für Battery Energy Storage Systems