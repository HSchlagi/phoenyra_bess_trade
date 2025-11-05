@echo off
chcp 65001 >nul
title Phoenyra BESS Trade System - Stoppen
color 0C

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     Phoenyra BESS Trade System - Stoppen                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Zum Projektverzeichnis wechseln
cd /d "%~dp0"

echo 🛑 Stoppe alle Services...
echo.

docker compose down

if %errorlevel% neq 0 (
    echo.
    echo ❌ Fehler beim Stoppen der Services!
    pause
    exit /b 1
)

echo.
echo ✅ Alle Services gestoppt!
echo.
pause

