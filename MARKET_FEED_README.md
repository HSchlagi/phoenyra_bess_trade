# Market Feed Service - Live Marktpreise

## Übersicht

Der Market Feed Service ermöglicht die Integration von Live-Marktpreisen verschiedener Energiebörsen in das Phoenyra BESS Trade System.

## Unterstützte Datenquellen

### ✅ aWattar (Implementiert)
- **API**: https://api.awattar.de/v1
- **Regionen**: AT (Österreich), DE (Deutschland)
- **Datenformat**: Day-ahead Marktpreise
- **Update-Intervall**: 5 Minuten (standard)

### 🔄 ETEnSo (Vorbereitet)
- **Platform**: ENTSO-E Transparency Platform
- **Status**: Implementierung vorbereitet
- **Benötigt**: API-Token von ENTSO-E
- **Dokumentation**: https://transparency.entsoe.eu/

## Installation

Der Market Feed Service läuft automatisch als Docker Container:

```bash
# System starten
docker compose up -d

# Logs anzeigen
docker compose logs -f market-feed

# Service status überprüfen
docker compose ps market-feed
```

## Konfiguration

### Umgebungsvariablen

```bash
# In docker-compose.yml konfigurierbar:
EXCHANGE_URL=http://exchange:9000   # Exchange Service URL
MARKET=awattar_at                   # Marktbezeichnung
UPDATE_INTERVAL=300                 # Update-Intervall in Sekunden
```

### Aktuelle Marktbezeichnungen

- `awattar_at` - Österreich (AT)
- `awattar_de` - Deutschland (DE)

## Funktionsweise

1. **Preisabfrage**: Der Service ruft alle 5 Minuten die aktuellen Marktpreise von aWattar ab
2. **Preisumwandlung**: Umrechnung von ct/kWh zu EUR/MWh
3. **Preisvalidierung**: Prüfung, ob Preis für aktuellen Zeitpunkt verfügbar
4. **Systemintegration**: Push an Exchange Service über `/admin/pricefeed/push`
5. **Metriken**: Automatische Berechnung von Mark, EMA und VWAP

## Preisdatenformat

```python
{
    "source": "aWattar",
    "region": "AT",
    "price_eur_mwh": 85.50,  # EUR/MWh
    "timestamp": "2025-01-XX...",
    "unit": "EUR/MWh"
}
```

## Monitoring

### Logs
```bash
# Live-Logs anzeigen
docker compose logs -f market-feed

# Beispiel-Output:
[2025-01-XX] awattar_at: 85.50 EUR/MWh (source: aWattar)
```

### Prometheus Metriken
- `pho_mark{market="awattar_at"}` - Aktueller Marktpreis
- `pho_ema{market="awattar_at"}` - Exponentiell gleitender Durchschnitt
- `pho_vwap{market="awattar_at"}` - Volume-weighted Average Price
- `pho_price_events_total{market="awattar_at"}` - Anzahl Preisupdates

### Grafana Dashboard
Die Preise werden automatisch im Grafana Dashboard visualisiert.

## Troubleshooting

### Problem: Keine Preise
```bash
# 1. Market Feed Container überprüfen
docker compose ps market-feed

# 2. Logs prüfen
docker compose logs market-feed

# 3. Network-Connectivity prüfen
docker exec -it market-feed ping exchange
```

### Problem: API-Fehler
- Überprüfe Internetverbindung
- Prüfe, ob aWattar API erreichbar ist
- Checke Firewall-Einstellungen

### Problem: Exchange-Verbindung
```bash
# Exchange Service Status prüfen
docker compose logs exchange | grep pricefeed

# Exchange-URL testen
curl http://localhost:9000/admin/pricefeed/push?market=test&price=100
```

## Erweiterung

### Weitere Marktdatenquellen hinzufügen

1. Neuen Fetch-Funktion in `market_feed.py` erstellen:
```python
def fetch_custom_api(self) -> Optional[Dict]:
    # API-Abfrage implementieren
    pass
```

2. In `run_feed()` integrieren

3. Docker-Compose aktualisieren

## API-Dokumentation

### aWattar API
- **Dokumentation**: https://www.a-wattar.de/
- **Rate Limits**: Keine dokumentiert
- **Datenverfügbarkeit**: 24/7

### ENTSO-E API
- **Anmeldung erforderlich**: https://transparency.entsoe.eu/
- **API-Token erforderlich**
- **Rate Limits**: Nach Vereinbarung

## Support

Bei Fragen oder Problemen:
1. Logs überprüfen
2. Docker-Container Status prüfen
3. Prometheus/Grafana Metrics analysieren

---

**Version**: 1.0  
**Letztes Update**: Januar 2025  
**Autor**: Phoenyra Team
