# Credit Management Dashboard - Funktionsweise

## Übersicht

Das **Credit Management Dashboard** ist eine zentrale Komponente des BESS Trading Dashboards zur Überwachung und Verwaltung von Kreditrisiken bei Trading-Gegenparteien (Counterparties). Es ermöglicht die Echtzeitüberwachung von Exposure (Kreditrisiko), die Verwaltung von Credit Limits und die Visualisierung des Exposure-Verlaufs.

**URL:** `http://localhost:5000/credit`

---

## Hauptfunktionen

### 1. Counterparty Exposure Tracking
- **Aktuelles Exposure**: Zeigt das aktuelle Kreditrisiko einer Gegenpartei in EUR
- **Credit Limit**: Zeigt das gesetzte Kreditlimit für die Gegenpartei
- **Auslastung**: Berechnet den Prozentsatz des genutzten Limits (Exposure / Limit × 100%)

### 2. Credit Limit Management
- Setzen und Ändern von Credit Limits für einzelne Counterparties
- Validierung und Speicherung der Limits

### 3. Exposure-Verlauf Visualisierung
- Chart.js-basiertes Liniendiagramm zur Darstellung des Exposure-Verlaufs über die Zeit
- Automatische Aktualisierung alle 30 Sekunden
- Historische Daten der letzten 20 Datenpunkte

### 4. Counterparty-Verwaltung
- Liste aller verfügbaren Counterparties
- Schnelle Auswahl und Anzeige von Exposure-Daten

---

## Dashboard-Komponenten im Detail

### 1. Counterparty-Auswahl

**Position:** Oben links im Dashboard

**Funktionalität:**
- **Eingabefeld**: Manuelle Eingabe einer Counterparty-ID (z.B. "CP-A", "CP-B")
- **"Laden"-Button**: Lädt die Exposure-Daten für die eingegebene Counterparty
- **"Neu"-Button**: Erstellt eine neue Counterparty (aktuell nur Frontend, Backend-Integration optional)

**Code-Funktion:**
```javascript
loadExposure()  // Lädt Exposure-Daten via API
addNewCounterparty()  // Fügt neue Counterparty hinzu
```

---

### 2. Key Metrics (Wichtige Kennzahlen)

**Position:** Drei Karten nebeneinander unter der Counterparty-Auswahl

#### A) Aktuelles Exposure
- **Anzeige**: Große rote Zahl in EUR
- **Icon**: Rotes Ausrufezeichen (Warnung)
- **Datenquelle**: `/api/credit/exposure?counterparty=CP-A`
- **Feld**: `exposure_eur` aus der API-Antwort

#### B) Credit Limit
- **Anzeige**: Große gelbe Zahl in EUR
- **Icon**: Gelbes Liniendiagramm
- **Berechnung**: `exposure_eur / (utilization_pct / 100)`
- **Hinweis**: Wird aus Exposure und Auslastung rückgerechnet, wenn Limit nicht direkt verfügbar

#### C) Auslastung (Utilization)
- **Anzeige**: Große Zahl in Prozent
- **Icon**: Grünes Prozentzeichen (färbt sich je nach Wert)
- **Farbcodierung**:
  - **Grün** (`#10b981`): ≤ 75% - Normal
  - **Gelb** (`#f59e0b`): 75-90% - Warnung
  - **Rot** (`#ef4444`): > 90% - Kritisch
- **Datenquelle**: `utilization_pct` aus der API-Antwort

---

### 3. Credit Limit setzen

**Position:** Links unten, neben dem Exposure-Chart

**Funktionalität:**
- **Counterparty-Feld**: Zeigt die aktuell ausgewählte Counterparty (schreibgeschützt)
- **Credit Limit (EUR)**: Eingabefeld für das neue Limit (Schrittweite: 1000 EUR)
- **"Limit speichern"-Button**: Sendet POST-Request an `/api/credit/limit`

**API-Request:**
```javascript
POST /api/credit/limit
Content-Type: application/json

{
  "counterparty": "CP-A",
  "limit_eur": 100000
}
```

**Nach dem Speichern:**
- Statusmeldung wird angezeigt
- Exposure-Daten werden automatisch neu geladen (`loadExposure()`)

---

### 4. Exposure-Verlauf Chart

**Position:** Rechts unten, neben "Credit Limit setzen"

**Technologie:** Chart.js (Line Chart)

**Konfiguration:**
- **Typ**: Liniendiagramm mit Füllung
- **Farbe**: Rot (`#ef4444`) mit 10% Transparenz
- **Datenformat**: `{x: timestamp, y: exposure_eur}`
- **Höhe**: 256px (h-64)

**X-Achse (Zeit):**
- Format: `DD.MM. HH:mm` (z.B. "15.04. 07:20")
- Validierung: Nur gültige Daten zwischen 2000-2100 werden angezeigt
- Max. Ticks: 10

**Y-Achse (EUR):**
- Formatierung: 
  - Werte ≥ 1000: `Xk` (z.B. "25k" für 25.000)
  - Werte < 1000: Ganzzahl
- Titel: "EUR"

**Tooltip:**
- **Titel**: Formatiertes Datum/Zeit (`DD.MM. HH:mm`)
- **Label**: Währung formatiert (z.B. "25.000,00 €")

**Datenverwaltung:**
- **Historie**: Letzte 20 Datenpunkte werden gespeichert
- **Aktualisierung**: Bei jedem `loadExposure()`-Aufruf wird ein neuer Datenpunkt hinzugefügt
- **Auto-Refresh**: Alle 30 Sekunden wird `loadExposure()` aufgerufen

**Code-Funktion:**
```javascript
initExposureChart()  // Initialisiert Chart.js
// Bei loadExposure():
exposureHistory.push({ x: now, y: data.exposure_eur });
if (exposureHistory.length > 20) exposureHistory.shift();
exposureChart.data.datasets[0].data = exposureHistory.map(...);
exposureChart.update('none');
```

---

### 5. Alle Counterparties

**Position:** Ganz unten im Dashboard

**Funktionalität:**
- Zeigt eine Liste aller verfügbaren Counterparties
- **Standard-Counterparties**: CP-A, CP-B, CP-C, CP-D (hardcoded im Frontend)
- **"Anzeigen"-Button**: Lädt die Exposure-Daten für die ausgewählte Counterparty

**Code-Funktion:**
```javascript
loadCounterpartyList()  // Rendert die Liste
selectCounterparty(cp)  // Wählt Counterparty aus und lädt Daten
```

---

## API-Endpunkte

### 1. GET `/api/credit/exposure`

**Zweck:** Abrufen der aktuellen Exposure-Daten für eine Counterparty

**Parameter:**
- `counterparty` (Query-Parameter): Counterparty-ID (z.B. "CP-A")

**Beispiel-Request:**
```
GET /api/credit/exposure?counterparty=CP-A
```

**Beispiel-Response:**
```json
{
  "exposure_eur": 25000,
  "utilization_pct": 25.0
}
```

**Backend-Routing:**
- Frontend (`webapp/app.py`) → `CREDIT_BASE_URL/credit/exposure`
- Standard: `http://credit:9503/credit/exposure`

**Verwendung im Frontend:**
```javascript
const response = await fetch(`/api/credit/exposure?counterparty=${cp}`);
const data = await response.json();
// data.exposure_eur → Aktuelles Exposure
// data.utilization_pct → Auslastung in Prozent
```

---

### 2. POST `/api/credit/limit`

**Zweck:** Setzen eines neuen Credit Limits für eine Counterparty

**Request Body:**
```json
{
  "counterparty": "CP-A",
  "limit_eur": 100000
}
```

**Beispiel-Request:**
```javascript
fetch('/api/credit/limit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    counterparty: 'CP-A', 
    limit_eur: 100000 
  })
});
```

**Beispiel-Response:**
```json
{
  "status": "OK",
  "message": "Credit limit updated"
}
```

**Backend-Routing:**
- Frontend (`webapp/app.py`) → `CREDIT_BASE_URL/credit/limit`
- Standard: `http://credit:9503/credit/limit`

**Nach erfolgreichem Setzen:**
- Statusmeldung wird angezeigt
- `loadExposure()` wird automatisch aufgerufen, um aktualisierte Daten zu laden

---

## Automatische Aktualisierung

**Intervall:** Alle 30 Sekunden

**Funktion:**
```javascript
setInterval(() => loadExposure(), 30000);
```

**Was passiert bei jeder Aktualisierung:**
1. API-Request an `/api/credit/exposure`
2. Aktualisierung der drei Key Metrics (Exposure, Limit, Auslastung)
3. Neuer Datenpunkt wird zum Exposure-Chart hinzugefügt
4. Chart wird aktualisiert (ohne Animation: `update('none')`)

---

## Statusmeldungen

**Position:** Unterhalb des Hauptinhalts (standardmäßig versteckt)

**Anzeige:**
- Erfolgreiche Aktionen: Blaue Statusmeldung
- Fehler: Rote Statusmeldung (via `showStatus()`)

**Beispiele:**
- `"Exposure für CP-A geladen"`
- `"Credit Limit für CP-A auf 100.000 EUR gesetzt"`
- `"Fehler: [Fehlermeldung]"`

---

## Technische Details

### Frontend-Technologien
- **Chart.js**: Für das Exposure-Verlauf-Diagramm
- **Tailwind CSS**: Für das Styling
- **Font Awesome**: Für Icons
- **Vanilla JavaScript**: Keine zusätzlichen Frameworks

### Datenformat
- **Timestamps**: JavaScript `Date.getTime()` (Millisekunden seit Epoch)
- **Währungen**: EUR, formatiert mit `toLocaleString('de-DE')`
- **Prozentsätze**: Mit 1 Dezimalstelle (`toFixed(1)`)

### Chart.js Konfiguration
- **Responsive**: `true`
- **Aspect Ratio**: `maintainAspectRatio: false` (feste Höhe)
- **Tooltip**: Custom Callbacks für Datum/Zeit und Währungsformatierung
- **Scales**: Custom Callbacks für X-Achse (Datum) und Y-Achse (k/M Formatierung)

---

## Workflow-Beispiel

### Szenario: Credit Limit für CP-A erhöhen

1. **Counterparty auswählen:**
   - Eingabe "CP-A" im Counterparty-Feld
   - Klick auf "Laden" oder Auswahl aus der Liste

2. **Aktuelle Situation prüfen:**
   - Aktuelles Exposure: 25.000 EUR
   - Credit Limit: 100.000 EUR (rückgerechnet)
   - Auslastung: 25.0% (grün)

3. **Limit ändern:**
   - Im Feld "Credit Limit (EUR)" neuen Wert eingeben (z.B. 150.000)
   - Klick auf "Limit speichern"

4. **Bestätigung:**
   - Statusmeldung: "Credit Limit für CP-A auf 150.000 EUR gesetzt"
   - Exposure-Daten werden automatisch neu geladen
   - Auslastung wird neu berechnet (25.000 / 150.000 = 16.7%)

5. **Monitoring:**
   - Chart zeigt kontinuierlich den Exposure-Verlauf
   - Alle 30 Sekunden werden Daten aktualisiert

---

## Erweiterungsmöglichkeiten

### Geplante Features (optional):
- **Counterparty-Verwaltung**: Backend-Integration für neue Counterparties
- **Alarme**: E-Mail/Benachrichtigungen bei hoher Auslastung (>90%)
- **Historische Daten**: Langzeit-Exposure-Verlauf aus Datenbank
- **Multi-Market Exposure**: Exposure nach Märkten aufgeteilt
- **Export-Funktion**: CSV/PDF-Export der Exposure-Daten

---

## Troubleshooting

### Problem: Keine Daten werden angezeigt
- **Prüfen**: Ist der Credit-Service erreichbar? (`http://credit:9503`)
- **Prüfen**: Browser-Konsole auf Fehler (F12)
- **Prüfen**: Network-Tab im Browser (sind API-Requests erfolgreich?)

### Problem: Chart zeigt keine Daten
- **Prüfen**: Werden Exposure-Daten erfolgreich geladen?
- **Prüfen**: Sind Timestamps gültig? (Browser-Konsole: `exposureHistory`)
- **Prüfen**: Chart.js ist geladen? (Browser-Konsole: `typeof Chart`)

### Problem: Credit Limit wird nicht gespeichert
- **Prüfen**: Backend-Service erreichbar?
- **Prüfen**: Request-Body korrekt formatiert?
- **Prüfen**: Browser-Konsole auf Fehler

---

## Zusammenfassung

Das Credit Management Dashboard bietet eine vollständige Lösung zur Überwachung und Verwaltung von Kreditrisiken:

✅ **Echtzeit-Monitoring** von Exposure und Auslastung  
✅ **Visuelle Darstellung** des Exposure-Verlaufs  
✅ **Einfache Verwaltung** von Credit Limits  
✅ **Automatische Aktualisierung** alle 30 Sekunden  
✅ **Farbcodierte Warnungen** bei hoher Auslastung  

Die Integration mit dem Backend erfolgt über zwei Haupt-API-Endpunkte, die eine flexible und erweiterbare Architektur ermöglichen.

