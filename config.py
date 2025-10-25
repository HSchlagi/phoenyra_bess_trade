"""
Phoenyra BESS Trade - Konfigurationsdatei
Sichere Speicherung von API-Keys und Systemkonfiguration
"""

import os
from datetime import datetime

# =============================================================================
# API-KONFIGURATION
# =============================================================================

# ENTSO-E Transparency Platform API
ENTSO_E_API_TOKEN = "2793353d-b5dd-4d4f-9638-8e26c88027e5"
ENTSO_E_BASE_URL = "https://web-api.tp.entsoe.eu/api"

# aWattar API (Fallback)
AWATTAR_BASE_URL = "https://api.awattar.de/v1"

# =============================================================================
# BIDDING ZONES (ENTSO-E)
# =============================================================================

BIDDING_ZONES = {
    "AT": "10YAT-APG------L",      # Österreich
    "DE": "10Y1001A1001A83F",     # Deutschland  
    "CH": "10YCH-SWISSGRIDZ",     # Schweiz
    "IT": "10YIT-GRTN-----B",      # Italien
    "CZ": "10YCZ-CEPS-----N",      # Tschechien
    "SK": "10YSK-SEPS-----K",      # Slowakei
    "HU": "10YHU-MAVIR----U",      # Ungarn
    "SI": "10YSI-ELES-----O"       # Slowenien
}

# =============================================================================
# MARKT-KONFIGURATION
# =============================================================================

# Standard-Markt
DEFAULT_MARKET = "epex_at"
DEFAULT_BIDDING_ZONE = "AT"

# Update-Intervalle (in Sekunden)
MARKET_UPDATE_INTERVAL = 300      # 5 Minuten
ENTSO_E_UPDATE_INTERVAL = 3600   # 1 Stunde
AWATTAR_UPDATE_INTERVAL = 300    # 5 Minuten

# =============================================================================
# SYSTEM-KONFIGURATION
# =============================================================================

# Exchange Service
EXCHANGE_URL = os.getenv("EXCHANGE_URL", "http://exchange:9000")
EXCHANGE_BASE_URL = os.getenv("EXCHANGE_BASE_URL", "http://exchange:9000")

# Redis Konfiguration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# API Keys
API_KEY = os.getenv("API_KEY", "demo")
HMAC_SECRET = os.getenv("HMAC_SECRET", "phoenyra_demo_secret")

# =============================================================================
# ENTSO-E DOKUMENTTYPEN
# =============================================================================

DOCUMENT_TYPES = {
    "DAY_AHEAD": "A44",           # Day-ahead prices
    "INTRADAY": "A69",            # Intraday prices  
    "BALANCING": "A85",           # Balancing prices
    "GENERATION": "A75",          # Generation data
    "LOAD": "A65"                 # Load data
}

# =============================================================================
# RATE LIMITING
# =============================================================================

# ENTSO-E API Limits
ENTSO_E_RATE_LIMIT = 400          # Requests pro Minute
ENTSO_E_REQUEST_DELAY = 1.0       # Sekunden zwischen Requests

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =============================================================================
# SICHERHEIT
# =============================================================================

# API-Key Validierung
def validate_entso_e_token():
    """Validiert den ENTSO-E API Token"""
    if not ENTSO_E_API_TOKEN or len(ENTSO_E_API_TOKEN) != 36:
        raise ValueError("Ungültiger ENTSO-E API Token")
    return True

# =============================================================================
# KONFIGURATION VALIDIERUNG
# =============================================================================

def validate_config():
    """Validiert die gesamte Konfiguration"""
    try:
        validate_entso_e_token()
        print("✅ Konfiguration validiert")
        return True
    except Exception as e:
        print(f"❌ Konfigurationsfehler: {e}")
        return False

# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

# Überschreibe mit Umgebungsvariablen falls gesetzt
ENTSO_E_API_TOKEN = os.getenv("ENTSO_E_TOKEN", ENTSO_E_API_TOKEN)
ENTSO_E_API_TOKEN = os.getenv("ENTSOE_API_KEY", ENTSO_E_API_TOKEN)

if __name__ == "__main__":
    print("🔧 Phoenyra BESS Trade - Konfiguration")
    print("=" * 50)
    print(f"ENTSO-E Token: {ENTSO_E_API_TOKEN[:8]}...")
    print(f"Standard-Markt: {DEFAULT_MARKET}")
    print(f"Bidding Zone: {DEFAULT_BIDDING_ZONE}")
    print(f"Update-Interval: {MARKET_UPDATE_INTERVAL}s")
    print("=" * 50)
    
    if validate_config():
        print("✅ Konfiguration ist gültig")
    else:
        print("❌ Konfiguration hat Fehler")
