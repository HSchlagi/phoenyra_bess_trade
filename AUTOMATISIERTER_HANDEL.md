# Automatisierter Handel im Phoenyra BESS Trade System

## 📊 Übersicht

Das Phoenyra BESS Trade System implementiert einen vollautomatisierten Handel für Battery Energy Storage Systems (BESS). Das System ermöglicht es, automatisch Strom zu kaufen und zu verkaufen, basierend auf Marktpreisen, BESS-Status und konfigurierten Strategien.

---

## 🔄 Ablauf des automatisierten Handels

### 1. **Marktdaten-Abruf** (Kontinuierlich)

**Was passiert:**
- Alle 5 Minuten werden aktuelle Marktpreise von EPEX Spot (via ENTSO-E Transparency Platform) abgerufen
- Die Preise werden in EUR/MWh konvertiert und gespeichert
- Berechnung von:
  - **Mark Preis**: Aktueller Marktpreis
  - **EMA** (Exponential Moving Average): Exponentieller gleitender Durchschnitt
  - **VWAP** (Volume-Weighted Average Price): Volumengewichteter Durchschnittspreis

**Technische Details:**
- **Service:** `market-feed` Container
- **Update-Intervall:** 300 Sekunden (5 Minuten)
- **Datenquelle:** ENTSO-E API (A44 Document Type)
- **Markt:** EPEX AT Day-Ahead (Österreich)

**Speicherung:**
- Redis: Aktuelle Preise für schnellen Zugriff
- SQLite: Historische Preisdaten für Analyse und Chart-Darstellung

---

### 2. **Order-Erstellung** (Manuell oder Automatisch)

**Manuelle Order-Erstellung:**
- Benutzer erstellt Order über Web-Dashboard
- Eingabe: Menge (MWh), Preis (EUR/MWh), Seite (BUY/SELL), Markt

**Automatische Order-Erstellung:**
- Zukünftig: Automatische Strategien basierend auf:
  - Preisprognosen (Forecast API)
  - BESS-SoC (State of Charge)
  - Netzfrequenz (Grid API)
  - Risk-Limits (Risk API)

**Order-Validierung:**
```python
# SoC-basierte Schutzfunktionen
if side == "BUY" and SoC < 15%:
    → Order wird abgelehnt (Batterie zu leer)
    
if side == "SELL" and SoC > 90%:
    → Order wird abgelehnt (Batterie zu voll)
```

**Throttling:**
- Rate-Limiting pro Markt (z.B. 120 Orders/Minute)
- Skalierung basierend auf BESS-Temperatur (ab 40°C: 50% Reduktion)

---

### 3. **Matching-Engine** (Automatisch, sofort)

**Was passiert:**
Sobald eine Order erstellt wird, startet automatisch die Matching-Engine:

```python
# Pseudocode
Order wird gespeichert → Status: "ACCEPTED"
→ Matching-Engine wird getriggert
→ Suche nach kompatiblen Gegenorders
→ Wenn gefunden: Trade wird sofort ausgeführt
```

**Matching-Logik:**

#### Für **BUY-Orders** (Kauf):
1. **Suche nach:** SELL-Orders im selben Markt
2. **Bedingung:** `SELL-Preis ≤ BUY-Limit-Preis`
3. **Sortierung:** 
   - Günstigste SELL-Orders zuerst
   - Bei gleichem Preis: Älteste zuerst (First-Come-First-Served)

#### Für **SELL-Orders** (Verkauf):
1. **Suche nach:** BUY-Orders im selben Markt
2. **Bedingung:** `BUY-Preis ≥ SELL-Limit-Preis`
3. **Sortierung:**
   - Teuerste BUY-Orders zuerst
   - Bei gleichem Preis: Älteste zuerst

**Beispiel:**
```
Order 1: BUY 1.0 MWh @ 40 EUR/MWh
Order 2: SELL 0.5 MWh @ 39 EUR/MWh

→ Matching: ✅ Kompatibel (40 ≥ 39)
→ Trade: 0.5 MWh @ 39.5 EUR/MWh (Durchschnitt)
→ Order 1: 50% gefüllt, Order 2: 100% gefüllt
```

---

### 4. **Trade-Ausführung** (Automatisch, atomar)

**Schritte bei einem Match:**

1. **Volumen-Berechnung:**
   ```python
   trade_qty = min(neue_order_verfügbar, match_order_verfügbar)
   ```
   - Nimmt das Minimum beider verfügbaren Mengen
   - Teilausführungen sind möglich

2. **Preis-Berechnung:**
   ```python
   trade_price = (limit_price_neue_order + limit_price_match_order) / 2.0
   ```
   - Durchschnitt beider Limit-Preise
   - Fair für beide Seiten

3. **Datenbank-Update:**
   - Trade wird in `trades`-Tabelle gespeichert
   - Beide Orders: `filled`-Wert wird erhöht
   - Wenn `filled >= qty`: Status → "FILLED"

4. **Echtzeit-Benachrichtigung:**
   - WebSocket-Event an alle verbundenen Clients
   - Dashboard wird sofort aktualisiert
   - Trade erscheint in "Letzte Trades"

**Transaktionssicherheit:**
- Alle Schritte werden atomar ausgeführt
- Entweder vollständig oder gar nicht
- Keine verlorenen Orders oder Inkonsistenzen

---

### 5. **Externe Börsen-Integration** (Optional)

**Trading Bridge Service:**

Das System kann Orders auch an externe Börsen weiterleiten:

#### **EPEX Spot:**
- Direkte Integration mit EPEX Spot API
- Erfordert: Marktteilnehmer-Registrierung, ECC Clearing
- Order-Übermittlung in Echtzeit

#### **APG (Austrian Power Grid):**
- Fahrplanübermittlung an APG
- Format: EDIFACT/XML
- Erfordert: Bilanzgruppenvertrag, MPID, AS4-Anbindung

**Routing:**
```
Dashboard → Order-Formular
    ↓
    └─→ Trading Bridge Service
            ↓
    ┌───────┴────────┐
    │                │
INTERNAL         EPEX_SPOT / APG
Exchange        (Externe Börsen)
```

---

## 🎯 Strategien und Automatisierung

### Aktuelle Automatisierung:

1. **Automatische Matching-Engine:**
   - Jede Order wird sofort gematcht
   - Keine manuelle Intervention nötig

2. **SoC-basierte Schutzfunktionen:**
   - BUY nur bei SoC ≥ 15%
   - SELL nur bei SoC ≤ 90%
   - Verhindert Über-/Unterladung

3. **Temperatur-basiertes Throttling:**
   - Bei Temperaturen > 40°C: Reduktion der Order-Rate
   - Schutz der Batterie vor Überhitzung

### Zukünftige Automatisierungs-Möglichkeiten:

1. **Preis-basierte Strategien:**
   - Automatisches Kaufen bei niedrigen Preisen
   - Automatisches Verkaufen bei hohen Preisen
   - Baseline: VWAP oder EMA als Referenz

2. **Forecast-basierte Strategien:**
   - Nutzung von Day-Ahead Prognosen
   - Optimierung basierend auf erwarteten Preisen
   - Integration mit Forecast API

3. **Grid-basierte Strategien:**
   - Reaktion auf Netzfrequenz
   - Frequenz-Regelung (Primary/Secondary Reserve)
   - Integration mit Grid API

4. **Risk-basierte Strategien:**
   - Begrenzung der Exposure basierend auf VaR
   - Automatische Position-Limits
   - Integration mit Risk API

---

## 📈 Datenfluss-Diagramm

```
┌─────────────────┐
│  ENTSO-E API    │ (Marktdaten-Quelle)
└────────┬────────┘
         │ (alle 5 Min)
         ▼
┌─────────────────┐
│  Market Feed    │ → Preise abrufen & speichern
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Exchange API   │ → Preise in Redis/SQLite
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│ Dashboard│ │  Order │
│ (Chart)  │ │ (Manuell│
└─────────┘ └────┬────┘
                 │
                 ▼
         ┌───────────────┐
         │  Order API    │ → Validierung (SoC, Throttle)
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │ Matching Engine│ → Suche nach Gegenorders
         └───────┬───────┘
                 │
         ┌───────┴───────┐
         │                │
         ▼                ▼
    ┌─────────┐      ┌─────────┐
    │  Match  │      │  Match  │
    │ gefunden│      │  nicht  │
    └────┬────┘      │ gefunden│
         │           └────┬────┘
         │                │
         ▼                ▼
    ┌─────────┐      ┌─────────┐
    │  Trade  │      │  Order  │
    │ausgeführt│      │ wartet  │
    └─────────┘      └─────────┘
         │
         ▼
    ┌─────────┐
    │WebSocket│ → Echtzeit-Update an Dashboard
    └─────────┘
```

---

## 🔧 Technische Komponenten

### Backend-Services:

1. **Exchange Service** (`exchange/server.py`):
   - FastAPI-basierter Trading-Engine
   - Matching-Engine-Implementierung
   - Order- und Trade-Verwaltung
   - WebSocket-Server für Echtzeit-Updates

2. **Market Feed Service** (`exchange/market_feed.py`):
   - Kontinuierlicher Abruf von Marktdaten
   - ENTSO-E Integration
   - Preis-Updates alle 5 Minuten

3. **Trading Bridge Service** (`etrm/trading-bridge/`):
   - Routing zu externen Börsen
   - EPEX Spot Adapter
   - APG Adapter

### Datenbanken:

1. **SQLite** (`exchange.db`):
   - Orders: Alle Order-Einträge
   - Trades: Alle ausgeführten Trades
   - Market Price History: Historische Preisdaten

2. **Redis**:
   - Aktuelle Marktpreise (schneller Zugriff)
   - Throttling-Zähler
   - BESS-Telemetrie (SoC, Power, Temp)

### Frontend:

- **Web Dashboard** (`webapp/`):
  - Order-Formular
  - Chart-Darstellung (Marktpreise)
  - Aktive Orders & Trades
  - Echtzeit-Updates via WebSocket

---

## 📊 Metriken und Monitoring

### Prometheus-Metriken:

- **G_MARK**: Aktueller Marktpreis (pro Markt)
- **G_EMA**: Exponentieller gleitender Durchschnitt
- **G_VWAP**: Volumengewichteter Durchschnittspreis
- **G_EXPO_E**: Exposure (Einkauf)
- **G_EXPO_N**: Exposure (Verkauf)
- **G_PNL_REAL**: Realisierter Gewinn/Verlust
- **C_EVENTS**: Anzahl Preis-Updates

### Grafana-Dashboards:

- BESS-Überwachung
- Trading-Analytics
- Marktpreise-Visualisierung
- System-Health

---

## ⚙️ Konfiguration

### Policy-Datei (`policy/policy.yaml`):

```yaml
version: 6
per_market_rps:
  EPEX_AT_INTRADAY_15MIN: 120
  EPEX_DE_INTRADAY_15MIN: 120
```

- **per_market_rps**: Rate-Limiting pro Markt (Orders pro Minute)

### Environment-Variablen:

```bash
# Marktdaten
ENTSO_E_TOKEN=your_token
MARKET=epex_at
BIDDING_ZONE=AT
UPDATE_INTERVAL=300

# Exchange
SQLITE_PATH=/app/exchange.db
REDIS_HOST=redis
POLICY_PATH=/app/policy/policy.yaml
```

---

## 🚀 Zusammenfassung

Das Phoenyra BESS Trade System implementiert einen **vollautomatisierten Handel** mit:

✅ **Automatischer Marktdaten-Abruf** (alle 5 Minuten)  
✅ **Sofortige Matching-Engine** (Orders werden sofort gematcht)  
✅ **Automatische Trade-Ausführung** (atomar, sicher)  
✅ **SoC-basierte Schutzfunktionen** (verhindert Über-/Unterladung)  
✅ **Echtzeit-Updates** (WebSocket für Dashboard)  
✅ **Externe Börsen-Integration** (EPEX Spot, APG)  

Das System ist darauf ausgelegt, **automatisch** Strom zu kaufen und zu verkaufen, basierend auf Marktpreisen, BESS-Status und konfigurierten Strategien. Die Matching-Engine sorgt dafür, dass Orders **sofort** mit kompatiblen Gegenorders gematcht und Trades ausgeführt werden - ohne manuelle Intervention.

---

## 📚 Weitere Dokumentation

- **Matching-Engine Details:** Siehe `Matching-Engine-Dokumentation.md`
- **Trading Bridge:** Siehe `TRADING_BRIDGE_KONZEPT.md`
- **Vollständige Dokumentation:** Siehe `Dokumentation_BESS_Trade.md`

---

**Erstellt:** 2025-11-05  
**Version:** 1.0  
**Autor:** Phoenyra BESS Trade System

