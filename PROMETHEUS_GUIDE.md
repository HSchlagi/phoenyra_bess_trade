# Prometheus Guide - Phoenyra BESS Trade

## 🎯 Was kann Prometheus?

Prometheus sammelt **Zeitreihen-Metriken** von allen Services und macht sie abfragbar.

**Zugriff:**
- **Web-UI**: http://localhost:9090
- **API**: http://localhost:9090/api/v1/
- **Grafana**: http://localhost:3000 (nutzt Prometheus als Datenquelle)

---

## 📊 Verfügbare Metriken im System

### 1. **Forecast API** (Port 9500)

```
pho_forecast_jobs_total{type="dayahead"}      # Anzahl Day-Ahead Forecasts
pho_forecast_jobs_total{type="intraday"}      # Anzahl Intraday Forecasts
pho_forecast_price_eur_mwh{horizon="24h"}     # Preisprognose (EUR/MWh)
pho_forecast_load_mw{horizon="24h"}          # Lastprognose (MW)
pho_forecast_solar_mw{horizon="24h"}         # Solarprognose (MW)
pho_forecast_wind_mw{horizon="24h"}          # Windprognose (MW)
```

### 2. **Grid API** (Port 9501)

```
pho_grid_freq_hz                             # Netzfrequenz (Hz) - aktuell: ~50.00
pho_grid_load_mw                             # Netzlast (MW)
```

### 3. **Risk API** (Port 9502)

```
pho_risk_var_99_eur                          # VaR 99% in EUR
pho_risk_var_95_eur                          # VaR 95% in EUR
pho_risk_limit_utilization_pct               # Limit-Auslastung (%)
```

### 4. **Exchange** (Port 9000)

```
# Alle Trading-Metriken des Haupt-Exchange-Servers
```

---

## 🔍 PromQL-Queries - Was du abfragen kannst

### **Einfache Metriken abrufen:**

```
# Aktuelle Netzfrequenz
pho_grid_freq_hz

# Aktueller VaR
pho_risk_var_99_eur

# Limit-Auslastung
pho_risk_limit_utilization_pct
```

### **Zeitraum-basierte Queries:**

```
# Durchschnittliche Frequenz der letzten 5 Minuten
avg_over_time(pho_grid_freq_hz[5m])

# Maximaler VaR der letzten Stunde
max_over_time(pho_risk_var_99_eur[1h])

# Summe aller Forecast-Jobs der letzten Stunde
sum(increase(pho_forecast_jobs_total[1h]))
```

### **Rate-basierte Queries:**

```
# Forecast-Jobs pro Minute
rate(pho_forecast_jobs_total[5m]) * 60

# Änderungsrate der Netzlast
rate(pho_grid_load_mw[5m])
```

### **Bedingungen & Alerts:**

```
# Frequenz außerhalb des Normbereichs (< 49.8 oder > 50.2 Hz)
pho_grid_freq_hz < 49.8 or pho_grid_freq_hz > 50.2

# VaR über 90% des Limits
pho_risk_limit_utilization_pct > 90

# Netzlast über 8000 MW
pho_grid_load_mw > 8000
```

### **Aggregationen:**

```
# Durchschnittliche Frequenz aller Grid-Instanzen
avg(pho_grid_freq_hz)

# Maximum aller VaR-Werte
max(pho_risk_var_99_eur)

# Anzahl aktiver Services
count(up{job=~"forecast|grid|risk"})
```

---

## 🖥️ Prometheus Web-UI nutzen

### **Schritt-für-Schritt:**

1. **Gehe zu**: http://localhost:9090
2. **Klicke auf "Graph"** (oben)
3. **Gib eine Query ein**, z.B.:
   ```
   pho_grid_freq_hz
   ```
4. **Klicke "Execute"** oder drücke Enter
5. **Zeige Graph/Table** - sieh dir die Daten an

### **Nützliche Views:**

- **Graph**: Zeitreihen-Visualisierung
- **Table**: Tabellarische Daten
- **Status → Targets**: Alle konfigurierten Services
- **Alerts**: Aktive Warnungen

---

## 📈 Praktische Beispiel-Queries

### **1. Frequenz-Monitoring:**
```
# Frequenz-Trend der letzten Stunde
pho_grid_freq_hz

# Abweichung von 50 Hz
abs(pho_grid_freq_hz - 50)
```

### **2. Risk-Monitoring:**
```
# Aktueller VaR vs. Limit (in %)
(pho_risk_var_99_eur / 250000) * 100

# Risk-Status: OK wenn < 75%
pho_risk_limit_utilization_pct < 75
```

### **3. Forecast-Statistiken:**
```
# Forecast-Jobs pro Tag (extrapoliert)
sum(rate(pho_forecast_jobs_total[1h])) * 24

# Durchschnittlicher Preis der letzten 24h
avg_over_time(pho_forecast_price_eur_mwh[24h])
```

---

## 🚨 Alerting-Regeln erstellen

In Grafana kannst du Alerts basierend auf Prometheus-Queries erstellen:

```
# Alert: Niedrige Frequenz
pho_grid_freq_hz < 49.8

# Alert: Hohes Risiko
pho_risk_limit_utilization_pct > 90

# Alert: Service down
up{job="forecast"} == 0
```

---

## 🔗 API-Nutzung

### **Direkte API-Abfragen:**

```bash
# Liste aller verfügbaren Metriken
curl http://localhost:9090/api/v1/label/__name__/values

# Query ausführen
curl 'http://localhost:9090/api/v1/query?query=pho_grid_freq_hz'

# Zeitreihen abfragen
curl 'http://localhost:9090/api/v1/query_range?query=pho_grid_freq_hz&start=2025-11-01T20:00:00Z&end=2025-11-01T21:00:00Z&step=1m'
```

---

## 💡 Tipps

1. **Grafana**: Bessere Visualisierung als Prometheus-UI
   - Bereits konfiguriert unter http://localhost:3000
   - Login: admin/admin

2. **Auto-Refresh**: In Prometheus-UI kannst du Auto-Refresh aktivieren

3. **Zeitbereich**: Nutze `[5m]`, `[1h]`, `[1d]` für verschiedene Zeiträume

4. **Labels filtern**: 
   ```
   pho_forecast_price_eur_mwh{horizon="24h"}
   ```

---

**© 2025 Phoenyra.com by Ing. Heinz Schlagintweit**

