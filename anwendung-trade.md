# Anwendung-Trade: User-Trading-Workflow

## 🎯 Übersicht

Das Phoenyra BESS Trade Dashboard bietet eine intuitive Trading-Oberfläche für Kauf- und Verkaufentscheidungen von Strom. Der User kann basierend auf Live-Marktdaten fundierte Trading-Entscheidungen treffen.

## 📊 Dashboard-Layout

### **1. Status-Cards (Oben)**
- **BESS SoC** - Batterie-Ladestand in %
- **Aktive Leistung** - Aktuelle Power in MW
- **Temperatur** - System-Temperatur in °C
- **Exposure** - Finanzielle Belastung in €

### **2. Marktpreise-Charts (Mitte)**
- **Live-Marktpreise** - EPEX Spot Day-Ahead Preise (Österreich)
- **VWAP-Chart** - 15-Minuten Volume-Weighted Average Price
- **Real-time Updates** alle 10 Sekunden

### **3. Trading-Sektion (Unten)**
- **Neue Order** - Trading-Formular
- **Aktive Orders** - Offene Positionen
- **Letzte Trades** - Ausgeführte Trades

## 🚀 User-Trading-Workflow

### **Schritt 1: Marktanalyse** 📈

**1.1 Live-Marktpreise betrachten**
- Öffnen Sie das Dashboard unter `http://localhost:5000`
- Schauen Sie sich die **Marktpreise-Charts** an
- Aktuelle Preise werden in **EUR/MWh** angezeigt
- **Beispiel:** 141,10 EUR/MWh = 14,11 ct/kWh

**1.2 VWAP-Trend analysieren**
- Der **VWAP-Chart** zeigt 15-Minuten-Trends
- Grüne Linie zeigt den durchschnittlichen Preis
- Trend-Richtung erkennen (steigend/fallend)

**1.3 BESS-Status prüfen**
- **SoC** (State of Charge) - Wie voll ist die Batterie?
- **Aktive Leistung** - Lädt oder entlädt das System?
- **Temperatur** - Ist das System im optimalen Bereich?

### **Schritt 2: Trading-Entscheidung** 💡

**2.1 Kauf-Entscheidung (BUY)**
```
Wann KAUFEN?
✅ Strompreis ist niedrig (z.B. < 100 EUR/MWh)
✅ BESS SoC ist niedrig (< 30%)
✅ Prognose: Preise steigen später
✅ Arbitrage-Möglichkeit erkennbar
```

**2.2 Verkauf-Entscheidung (SELL)**
```
Wann VERKAUFEN?
✅ Strompreis ist hoch (z.B. > 150 EUR/MWh)
✅ BESS SoC ist hoch (> 70%)
✅ Prognose: Preise fallen später
✅ Profit-Möglichkeit erkennbar
```

### **Schritt 3: Order-Parameter festlegen** ⚙️

**3.1 Order-Formular ausfüllen**

```html
<!-- Neue Order Sektion -->
<div class="dark-card p-6">
    <h3>Neue Order</h3>
    <form action="/order" method="POST">
        
        <!-- 1. SEITE wählen -->
        <select name="side">
            <option value="buy">Kaufen</option>    <!-- Strom kaufen -->
            <option value="sell">Verkaufen</option> <!-- Strom verkaufen -->
        </select>
        
        <!-- 2. MENGE festlegen -->
        <input name="amount" placeholder="1.0"> <!-- MWh -->
        
        <!-- 3. PREIS setzen -->
        <input name="price" placeholder="141.10"> <!-- €/MWh -->
        
        <!-- 4. MARKT wählen -->
        <select name="market">
            <option value="epex_at">EPEX AT</option>
            <option value="EPEX_AT_INTRADAY_15MIN">EPEX AT Intraday</option>
        </select>
        
        <!-- 5. ORDER erstellen -->
        <button type="submit">Order erstellen</button>
    </form>
</div>
```

**3.2 Parameter-Erklärung**

| Parameter | Beschreibung | Beispiel | Tipp |
|-----------|--------------|----------|------|
| **Seite** | Kaufen oder Verkaufen | `buy` / `sell` | Basierend auf Marktanalyse |
| **Menge** | Strommenge in MWh | `1.0` MWh | Abhängig von BESS-Kapazität |
| **Preis** | Limit-Preis in €/MWh | `141.10` €/MWh | Aktueller Marktpreis ± Spread |
| **Markt** | Trading-Markt | `epex_at` | EPEX AT für Day-Ahead |

### **Schritt 4: Order-Ausführung** 🚀

**4.1 Order senden**
1. Klicken Sie auf **"Order erstellen"** (Shimmer-Button)
2. Das System sendet die Order an die Matching-Engine
3. **Flash Message** bestätigt die Order-Erstellung

**4.2 Order-Status verfolgen**
- **Aktive Orders** zeigt offene Positionen
- **Letzte Trades** zeigt ausgeführte Trades
- **Real-time Updates** alle 10 Sekunden

## 📈 Trading-Strategien

### **1. Arbitrage-Trading**
```
Ziel: Preisunterschiede zwischen Zeiten nutzen
Beispiel:
- 02:00 Uhr: 50 EUR/MWh (kaufen)
- 18:00 Uhr: 150 EUR/MWh (verkaufen)
Profit: 100 EUR/MWh
```

### **2. Peak-Shaving**
```
Ziel: Spitzenlasten reduzieren
Beispiel:
- Hohe Preise: BESS entladen (verkaufen)
- Niedrige Preise: BESS laden (kaufen)
```

### **3. Frequency Response**
```
Ziel: Netzfrequenz stabilisieren
Beispiel:
- Frequenz < 50 Hz: BESS entladen
- Frequenz > 50 Hz: BESS laden
```

## 🎨 Dashboard-Features

### **Magic UI Komponenten**
- **Aurora-Text** - Animierte Überschriften
- **Shimmer-Buttons** - Glänzende Buttons
- **Dark-Cards** - Moderne Karten-Design
- **Number-Ticker** - Animierte Zahlen

### **Real-time Updates**
- **WebSocket-Verbindung** für Live-Daten
- **Auto-Refresh** alle 10 Sekunden
- **Status-Indikatoren** (Online/Offline)

### **Theme-Support**
- **Dark Mode** (Standard)
- **Light Mode** (Toggle verfügbar)
- **Responsive Design** für alle Geräte

## 🔧 BESS-Steuerung

### **Telemetrie-Steuerung**
```html
<!-- BESS Parameter manuell setzen -->
<form id="telemetryForm">
    <input name="soc_percent" placeholder="72.5">    <!-- SoC in % -->
    <input name="active_power" placeholder="3.8">    <!-- Leistung in MW -->
    <input name="temperature" placeholder="28.3">    <!-- Temperatur in °C -->
    <button type="submit">Telemetrie senden</button>
</form>
```

## 📊 Marktdaten-Quellen

### **ENTSO-E Integration**
- **Datenquelle:** EPEX Spot Day-Ahead Preise
- **Aktualisierung:** Alle 5 Minuten
- **Coverage:** Österreich (AT)
- **Format:** EUR/MWh

### **Fallback-System**
- **Primary:** ENTSO-E Transparency Platform
- **Secondary:** aWattar API
- **Backup:** Mock-Daten (Development)

## 🚨 Wichtige Hinweise

### **Trading-Risiken**
- ⚠️ **Preisvolatilität** - Strompreise können stark schwanken
- ⚠️ **BESS-Kapazität** - Nicht mehr handeln als Speicherkapazität
- ⚠️ **Netzregeln** - Einhaltung der Netzanschlussbedingungen

### **Best Practices**
- ✅ **Kleine Mengen** beginnen (0.1-1.0 MWh)
- ✅ **Limit-Orders** verwenden (nicht Market-Orders)
- ✅ **Stop-Loss** bei hohen Risiken
- ✅ **Diversifikation** über verschiedene Märkte

## 🎯 Erfolgreiche Trading-Beispiele

### **Beispiel 1: Arbitrage-Gewinn**
```
Zeit: 02:00 Uhr
Aktion: KAUFEN 1.0 MWh @ 50 EUR/MWh
BESS: SoC steigt von 20% auf 30%

Zeit: 18:00 Uhr  
Aktion: VERKAUFEN 1.0 MWh @ 150 EUR/MWh
BESS: SoC fällt von 30% auf 20%

Gewinn: 100 EUR (150 - 50 = 100 EUR/MWh)
```

### **Beispiel 2: Peak-Shaving**
```
Zeit: 12:00 Uhr
Marktpreis: 200 EUR/MWh
BESS SoC: 80%
Aktion: VERKAUFEN 2.0 MWh @ 200 EUR/MWh
Ergebnis: 400 EUR Einnahmen, SoC auf 60%
```

## 📱 Mobile Trading

### **Responsive Design**
- **Smartphone** - Optimierte Touch-Oberfläche
- **Tablet** - Vollständige Desktop-Funktionen
- **Desktop** - Erweiterte Chart-Analyse

### **Touch-Optimierung**
- **Große Buttons** für Touch-Bedienung
- **Swipe-Gesten** für Chart-Navigation
- **Zoom-Funktionen** für Detail-Analyse

---

**Phoenyra BESS Trade System v2.0**  
*Professionelle Trading-Lösung für Battery Energy Storage Systems*

© 2025 Phoenyra.com by Ing. Heinz Schlagintweit. Alle Rechte vorbehalten.
