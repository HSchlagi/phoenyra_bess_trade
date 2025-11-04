"""
Trading Bridge Service - Routes orders to internal exchange or external trading platforms (EPEX Spot, APG)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
import requests
import os
from datetime import datetime

app = FastAPI(title="Phoenyra Trading Bridge", version="1.0.0")

# Configuration
EXCHANGE_BASE_URL = os.getenv("EXCHANGE_BASE_URL", "http://exchange:9000")
EPEX_USERNAME = os.getenv("EPEX_USERNAME", "")
EPEX_PASSWORD = os.getenv("EPEX_PASSWORD", "")
EPEX_API_KEY = os.getenv("EPEX_API_KEY", "")
EPEX_TEST_MODE = os.getenv("EPEX_TEST_MODE", "true").lower() == "true"

APG_MPID = os.getenv("APG_MPID", "")
APG_BILANZGRUPPE = os.getenv("APG_BILANZGRUPPE", "")
APG_AS4_ENDPOINT = os.getenv("APG_AS4_ENDPOINT", "")

class BridgeOrder(BaseModel):
    market: str
    side: Literal["BUY", "SELL"]
    quantity_mwh: float
    limit_price_eur_mwh: float
    delivery_start: str
    delivery_end: str
    target_exchange: Literal["INTERNAL", "EPEX_SPOT", "APG"]
    order_type: Literal["LIMIT", "MARKET"] = "LIMIT"
    time_in_force: Literal["GFD", "IOC", "FOK"] = "GFD"

class EPEXSpotAdapter:
    """EPEX Spot Trading Adapter"""
    
    def __init__(self):
        self.base_url = "https://api.epexspot.com" if not EPEX_TEST_MODE else "https://test-api.epexspot.com"
        self.username = EPEX_USERNAME
        self.password = EPEX_PASSWORD
        self.api_key = EPEX_API_KEY
    
    def is_configured(self) -> bool:
        """Check if EPEX credentials are configured"""
        return bool(self.username and self.password and self.api_key)
    
    def place_order(self, order: dict) -> dict:
        """Place order on EPEX Spot"""
        if not self.is_configured():
            raise HTTPException(
                status_code=503,
                detail="EPEX Spot Credentials nicht konfiguriert. Bitte EPEX_USERNAME, EPEX_PASSWORD und EPEX_API_KEY setzen."
            )
        
        # TODO: Implement actual EPEX Spot API call
        # This is a placeholder that shows the structure
        return {
            "status": "ERROR",
            "message": "EPEX Spot Integration erfordert Marktteilnehmer-Registrierung und API-Zugang",
            "order_id": None,
            "external_id": None,
            "note": "Bitte EPEX Spot Mitgliedschaft und Credentials konfigurieren"
        }

class APGAdapter:
    """APG (Austrian Power Grid) Adapter"""
    
    def __init__(self):
        self.mpid = APG_MPID
        self.bilanzgruppe = APG_BILANZGRUPPE
        self.as4_endpoint = APG_AS4_ENDPOINT
    
    def is_configured(self) -> bool:
        """Check if APG credentials are configured"""
        return bool(self.mpid and self.bilanzgruppe)
    
    def submit_schedule(self, schedule_data: dict) -> dict:
        """Submit schedule to APG"""
        if not self.is_configured():
            raise HTTPException(
                status_code=503,
                detail="APG Credentials nicht konfiguriert. Bitte APG_MPID, APG_BILANZGRUPPE und APG_AS4_ENDPOINT setzen."
            )
        
        # TODO: Implement actual APG EDIFACT/XML submission
        # This is a placeholder that shows the structure
        return {
            "status": "ERROR",
            "message": "APG Integration erfordert Bilanzgruppenvertrag, MPID und AS4-Anbindung",
            "submission_id": None,
            "note": "Bitte APG Marktteilnehmer-Registrierung und technische Anbindung konfigurieren"
        }

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "service": "Phoenyra Trading Bridge",
        "status": "running",
        "version": "1.0.0",
        "configured_adapters": {
            "EPEX_SPOT": EPEXSpotAdapter().is_configured(),
            "APG": APGAdapter().is_configured()
        }
    }

@app.post("/bridge/orders")
async def route_order(order: BridgeOrder):
    """
    Route order to internal exchange or external trading platform
    
    Args:
        order: Order data with target_exchange field
    
    Returns:
        Order response from target platform
    """
    if order.target_exchange == "INTERNAL":
        # Route to internal exchange
        try:
            response = requests.post(
                f"{EXCHANGE_BASE_URL}/orders",
                json=order.dict(),
                headers={"X-API-KEY": "demo"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Interner Exchange nicht erreichbar: {str(e)}")
    
    elif order.target_exchange == "EPEX_SPOT":
        # Route to EPEX Spot adapter
        adapter = EPEXSpotAdapter()
        result = adapter.place_order(order.dict())
        return result
    
    elif order.target_exchange == "APG":
        # Route to APG adapter
        adapter = APGAdapter()
        # Convert order to schedule format for APG
        schedule_data = {
            "delivery_date": order.delivery_start[:10],  # Extract date
            "hourly_schedule": [
                {
                    "hour": int(order.delivery_start[11:13]),  # Extract hour
                    "mwh": order.quantity_mwh if order.side == "SELL" else -order.quantity_mwh
                }
            ]
        }
        result = adapter.submit_schedule(schedule_data)
        return result
    
    else:
        raise HTTPException(status_code=400, detail=f"Unbekannte Trading-Plattform: {order.target_exchange}")

@app.get("/bridge/status")
def get_status():
    """Get status of all adapters"""
    epex_adapter = EPEXSpotAdapter()
    apg_adapter = APGAdapter()
    
    return {
        "internal_exchange": {
            "url": EXCHANGE_BASE_URL,
            "status": "available"
        },
        "epex_spot": {
            "configured": epex_adapter.is_configured(),
            "test_mode": EPEX_TEST_MODE,
            "status": "configured" if epex_adapter.is_configured() else "not_configured"
        },
        "apg": {
            "configured": apg_adapter.is_configured(),
            "status": "configured" if apg_adapter.is_configured() else "not_configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9510)

