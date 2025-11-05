@echo off
chcp 65001 >nul
title Phoenyra BESS Trade System - Starter
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     Phoenyra BESS Trade System - Starter                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Prüfen ob Docker läuft
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker läuft nicht! Bitte Docker Desktop starten.
    echo.
    pause
    exit /b 1
)

echo ✅ Docker läuft
echo.

REM Zum Projektverzeichnis wechseln
cd /d "%~dp0"

echo 📦 Starte alle Services...
echo.

REM Docker Compose starten
docker compose up -d --build

if %errorlevel% neq 0 (
    echo.
    echo ❌ Fehler beim Starten der Services!
    pause
    exit /b 1
)

echo.
echo ✅ Services gestartet!
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Services sind erreichbar:                 ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  🌐 Haupt-Dashboard:      http://localhost:5000             ║
echo ║  📊 Grafana:              http://localhost:3000             ║
echo ║  📈 Prometheus:           http://localhost:9090             ║
echo ║  🔌 Exchange API:         http://localhost:9000/docs        ║
echo ║  🔮 Forecast API:         http://localhost:9500/docs        ║
echo ║  ⚡ Grid API:             http://localhost:9501/docs        ║
echo ║  🛡️ Risk API:             http://localhost:9502/docs        ║
echo ║  💳 Credit API:           http://localhost:9503/docs       ║
echo ║  💰 Billing API:          http://localhost:9504/docs        ║
echo ║  🌉 Trading Bridge API:   http://localhost:9510/docs        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 💡 Tipp: Öffnen Sie http://localhost:5000 im Browser
echo.
echo 📋 Status der Container:
docker compose ps
echo.
pause

