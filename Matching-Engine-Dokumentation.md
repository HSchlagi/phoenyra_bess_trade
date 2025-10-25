# Matching-Engine: Automatische Order-Ausführung

## Übersicht

Das Phoenyra BESS Trade System verfügt über eine vollautomatische Matching-Engine, die eingehende Orders sofort mit kompatiblen Gegenorders matcht und Trades ausführt.

## Ablauf im Detail

### 1. Order-Erstellung

Wenn eine neue Order erstellt wird (z.B. BUY 1.0 MWh @ 40 EUR/MWh):

```
Status: ACCEPTED
filled: 0.0 MWh (noch nichts ausgefüllt)
```

Die Order wird in der SQLite-Datenbank gespeichert mit:
- Eindeutiger Order-ID
- Markt (z.B. "epex_at")
- Seite (BUY/SELL)
- Preis (limit_price_eur_mwh)
- Menge (quantity_mwh)
- Status: "ACCEPTED"

### 2. Automatisches Matching

**Sofort nach dem Speichern** startet die Matching-Engine:

```python
asyncio.create_task(try_match_order(oid, o.market, o.side, o.quantity_mwh, o.limit_price_eur_mwh))
```

Die `try_match_order()` Funktion sucht nach kompatiblen Gegenorders:

#### Für BUY-Orders:
- **Sucht:** SELL-Orders im selben Markt
- **Bedingung:** `ask_price ≤ limit_price` (kann zu gleichem oder günstigeren Preis kaufen)
- **Sortierung:** Preis aufsteigend, dann Zeitstempel (billigste zuerst)

#### Für SELL-Orders:
- **Sucht:** BUY-Orders im selben Markt
- **Bedingung:** `bid_price ≥ limit_price` (kann zu gleichem oder höheren Preis verkaufen)
- **Sortierung:** Preis absteigend, dann Zeitstempel (teuerste zuerst)

### 3. Trade-Ausführung

Wenn eine passende Order gefunden wird:

#### a) Volumen-Berechnung
```python
trade_qty = min(remaining_qty, match_available)
```
- Nimmt das **Minimum** aus: verbleibender Menge der neuen Order und verfügbarer Menge der gefundenen Order
- Beide Orders können teilweise ausgeführt werden

#### b) Preis-Berechnung
```python
trade_price = (limit_price + match_price) / 2.0
```
- **Durchschnitt** aus beiden Limit-Preisen
- Fair für beide Seiten

#### c) Trade wird in Datenbank geschrieben
```sql
INSERT INTO trades(id, order_id, user_key, executed, price, ts, market, side)
VALUES(trade_id, new_order_id, match_user_key, trade_qty, trade_price, now, market, side)
```

#### d) Orders werden aktualisiert
- `filled`-Wert beider Orders wird um `trade_qty` erhöht
- Wenn `filled >= qty` → Status wird auf "FILLED" gesetzt

#### e) Trade wird per WebSocket verschickt
- Alle verbundenen Clients erhalten ein Trade-Event
- Dashboard wird in Echtzeit aktualisiert

## Praktisches Beispiel

### Ausgangssituation:
```
Order 1: BUY 1.0 MWh @ 40 EUR/MWh  (Status: ACCEPTED)
Order 2: SELL 0.5 MWh @ 39 EUR/MWh (Status: ACCEPTED)
```

### Matching-Logik:

1. **Prüfung:** BUY-Limit (40) ≥ SELL-Limit (39) → ✅ passt

2. **Volumen:**
   - Order 1 verfügbar: 1.0 MWh
   - Order 2 verfügbar: 0.5 MWh
   - **trade_qty = min(1.0, 0.5) = 0.5 MWh**

3. **Preis:**
   - **trade_price = (40 + 39) / 2 = 39.5 EUR/MWh**

### Ergebnis:

```
Order 1: BUY 1.0 MWh @ 40 EUR/MWh
- filled: 0.5 MWh
- Status: ACCEPTED (50% übrig)

Order 2: SELL 0.5 MWh @ 39 EUR/MWh
- filled: 0.5 MWh
- Status: FILLED (vollständig)

Trade:
- Menge: 0.5 MWh
- Preis: 39.5 EUR/MWh
- Zeitstempel: 12:47:51
```

**Anzeige im Dashboard:**
- **Aktive Orders:** Order 1 noch sichtbar (teilweise), Order 2 nicht mehr
- **Letzte Trades:** "SELL 0.5 MWh @ 39.5 €/MWh" wird angezeigt

## Besonderheiten

### 1. **Teilausführungen möglich**
- Orders können mehrfach matchen
- Teilausführung bleibt sichtbar im Dashboard

### 2. **Fairer Preis**
- Durchschnitt beider Limit-Preise
- Keine Seite wird benachteiligt

### 3. **Sofortige Ausführung**
- Matching erfolgt **unmittelbar** nach Order-Erstellung
- Keine Wartezeiten

### 4. **Faire Reihenfolge**
- Sortierung: **Preis → Zeitstempel**
- Beste Preise werden zuerst gematcht (First-Come-First-Served bei gleichem Preis)

### 5. **Robustheit**
- Einzelne Matches werden atomar ausgeführt
- Transaktionen werden entweder vollständig oder gar nicht durchgeführt
- Keine verlorenen Orders oder Inkonsistenzen

## Technische Implementierung

### Code-Location:
- **Datei:** `exchange/server.py`
- **Funktion:** `try_match_order()`
- **Database:** SQLite (`exchange.db`)
- **WebSockets:** Echtzeit-Updates via `/ws/trades`

### Datenbank-Struktur:

**Orders-Tabelle:**
```sql
CREATE TABLE orders(
    id TEXT PRIMARY KEY,
    user_key TEXT,
    market TEXT,
    side TEXT,
    type TEXT,
    tif TEXT,
    p_limit REAL,
    qty REAL,
    d_start TEXT,
    d_end TEXT,
    status TEXT,
    filled REAL,
    ts TEXT
)
```

**Trades-Tabelle:**
```sql
CREATE TABLE trades(
    id TEXT PRIMARY KEY,
    order_id TEXT,
    user_key TEXT,
    executed REAL,
    price REAL,
    ts TEXT,
    market TEXT,
    side TEXT
)
```

## Performance & Skalierung

- **Latenz:** Matching erfolgt in Millisekunden
- **Skalierung:** Durchschnittliche Laufzeit O(n) für n passende Orders
- **Parallelisierung:** Jede Order wird in separatem Task verarbeitet

## Integration mit BESS Trading

Die Matching-Engine ist vollständig integriert mit:
- **SoC-Limits:** BUY nur bei SoC ≥ 15%, SELL nur bei SoC ≤ 90%
- **Throttling:** Rate-Limiting pro Markt
- **Exposure-Tracking:** Automatische Berechnung der Markt-Exposure
- **Prometheus-Metriken:** G_EXPO_E, G_EXPO_N, G_PNL_REAL

## Zusammenfassung

Das System implementiert eine vollständige **Orderbuch-Matching-Engine** mit automatischer Trade-Ausführung. Jede neue Order wird sofort mit kompatiblen Gegenorders gematcht, Trades werden atomar ausgeführt und in Echtzeit an alle verbundenen Clients gesendet. Die Implementierung folgt bewährten Praktiken aus dem Electronic Trading und stellt Fairness, Effizienz und Datenintegrität sicher.
