"""
Market Feed Service - Fetches live market prices from aWattar, EPEX Spot via ENTSO-E
Integrates with the Phoenyra BESS Trading System
"""
import requests
import asyncio
from datetime import datetime, timedelta
import os
import sys
from typing import Optional, List, Dict
from xml.etree import ElementTree as ET

# Configuration - use environment variables with fallbacks
ENTSO_E_API_TOKEN = os.getenv("ENTSO_E_TOKEN", "2793353d-b5dd-4d4f-9638-8e26c88027e5")
ENTSO_E_BASE_URL = "https://web-api.tp.entsoe.eu/api"
BIDDING_ZONES = {
    "AT": "10YAT-APG------L",      # Österreich
    "DE": "10Y1001A1001A83F",      # Deutschland  
    "CH": "10YCH-SWISSGRIDZ",      # Schweiz
    "IT": "10YIT-GRTN-----B",      # Italien
    "CZ": "10YCZ-CEPS-----N",      # Tschechien
    "SK": "10YSK-SEPS-----K",      # Slowakei
    "HU": "10YHU-MAVIR----U",      # Ungarn
    "SI": "10YSI-ELES-----O"       # Slowenien
}
DEFAULT_MARKET = "epex_at"
DEFAULT_BIDDING_ZONE = "AT"
MARKET_UPDATE_INTERVAL = 300
ENTSO_E_REQUEST_DELAY = 1.0

class MarketFeed:
    """Service to fetch and push market prices from various energy APIs"""
    
    def __init__(self, exchange_url: str = "http://exchange:9000"):
        self.exchange_url = exchange_url
        self.awattar_base = "https://api.awattar.de/v1"
        self.entso_e_base = ENTSO_E_BASE_URL
        # ENTSO-E API token from config
        self.entso_token = ENTSO_E_API_TOKEN
        
    def fetch_awattar(self, region: str = "AT") -> Optional[Dict]:
        """Fetch current electricity prices from aWattar
        
        Args:
            region: Market region ('AT' for Austria, 'DE' for Germany)
            
        Returns:
            Dict with current price information
        """
        try:
            url = f"{self.awattar_base}/marketdata"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                # Get current market price
                current_price = None
                now = datetime.now()
                
                for price_point in data["data"]:
                    start_time = datetime.fromtimestamp(price_point["start_timestamp"] / 1000)
                    end_time = datetime.fromtimestamp(price_point["end_timestamp"] / 1000)
                    
                    if start_time <= now <= end_time:
                        # aWattar API returns price in ct/kWh (Cent pro Kilowattstunde)
                        # Convert to EUR/MWh: ct/kWh * 10 = EUR/MWh
                        # Example: 7.1 ct/kWh * 10 = 71 EUR/MWh
                        raw_price = price_point["marketprice"]
                        # Check if price is in ct/kWh (typical range 1-50 ct/kWh) or EUR/MWh (typical range 50-500 EUR/MWh)
                        if raw_price < 50:  # Likely ct/kWh
                            current_price = round(raw_price * 10.0, 2)  # ct/kWh * 10 = EUR/MWh
                        else:  # Already in EUR/MWh
                            current_price = round(raw_price, 2)
                        break
                
                if current_price:
                    return {
                        "source": "aWattar",
                        "region": region,
                        "price_eur_mwh": current_price,
                        "timestamp": datetime.now().isoformat(),
                        "unit": "EUR/MWh"
                    }
            
            return None
        except Exception as e:
            print(f"Error fetching aWattar data: {e}")
            return None
    
    def fetch_epex_spot(self, bidding_zone: str = "AT") -> Optional[Dict]:
        """Fetch EPEX Spot prices via ENTSO-E Transparency Platform
        
        Args:
            bidding_zone: Bidding zone code ('10YAT-APG------L' for Austria, '10YDE-RWENET---I' for Germany)
            
        Returns:
            Dict with current EPEX Spot price information
        """
        try:
            if not self.entso_token:
                print("ENTSO-E API token not configured, using aWattar fallback")
                return None
            
            # Use bidding zones from config
            zone_code = BIDDING_ZONES.get(bidding_zone, BIDDING_ZONES["AT"])
            now = datetime.now()
            start_date = now.strftime("%Y%m%d0000")
            end_date = now.strftime("%Y%m%d2359")
            
            params = {
                "securityToken": self.entso_token,
                "documentType": "A44",
                "in_Domain": zone_code,
                "out_Domain": zone_code,
                "periodStart": start_date,
                "periodEnd": end_date
            }
            
            # Rate limiting
            import time
            time.sleep(ENTSO_E_REQUEST_DELAY)
            
            response = requests.get(self.entso_e_base, params=params, timeout=15)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0'}
            
            # Extract prices from TimeSeries
            prices = []
            for timeseries in root.findall('.//ns:TimeSeries', ns):
                for period in timeseries.findall('.//ns:Period', ns):
                    resolution_elem = period.find('.//ns:resolution', ns)
                    resolution = resolution_elem.text if resolution_elem is not None else "PT60M"
                    
                    # Get prices from all periods
                    for point in period.findall('.//ns:Point', ns):
                        position = int(point.find('ns:position', ns).text)
                        price = float(point.find('ns:price.amount', ns).text)
                        prices.append({"position": position, "price": price, "resolution": resolution})
            
            # Get current hour price
            if prices:
                print(f"Found {len(prices)} price points")
                print(f"Sample price: {prices[0] if prices else 'none'}")
                
                # Resolution could be PT60M (hourly) or PT15M (15min)
                # For PT15M: 96 periods (4 per hour), position 1-96
                # For PT60M: 24 periods, position 1-24
                
                # Check if we have PT15M resolution
                first_resolution = prices[0].get("resolution", "PT60M")
                print(f"Resolution: {first_resolution}")
                
                if "PT15M" in first_resolution:
                    # PT15M: calculate which quarter hour we are in
                    # Current time in minutes since start of day
                    minutes_since_start = now.hour * 60 + now.minute
                    # Which 15-minute period (1-96)
                    quarter_hour = (minutes_since_start // 15) + 1
                    print(f"Current quarter hour: {quarter_hour}")
                    current_price = next((p["price"] for p in prices if p["position"] == quarter_hour), None)
                else:
                    # PT60M: hourly resolution
                    # Current hour (1-24)
                    current_hour = now.hour + 1
                    print(f"Current hour: {current_hour}")
                    current_price = next((p["price"] for p in prices if p["position"] == current_hour), None)
                
                print(f"Current price (raw from ENTSO-E): {current_price}")
                
                if current_price:
                    # ENTSO-E A44 Document Type returns prices in EUR/MWh according to official documentation
                    # If price is suspiciously high (>200), it might be incorrectly interpreted
                    # Typical range: 30-150 EUR/MWh (3-15 ct/kWh)
                    # If price > 200, divide by 10 (might be in wrong unit format)
                    if current_price > 200:  # Suspiciously high, likely needs division by 10
                        print(f"Warning: Price {current_price} seems very high, dividing by 10")
                        converted_price = round(current_price / 10.0, 2)  # Divide by 10 to correct unit
                        print(f"Corrected: {current_price} -> {converted_price} EUR/MWh")
                    else:  # Likely already in correct EUR/MWh range (30-200)
                        converted_price = round(current_price, 2)
                    
                    return {
                        "source": "EPEX Spot (via ENTSO-E)",
                        "region": bidding_zone,
                        "price_eur_mwh": converted_price,
                        "timestamp": now.isoformat(),
                        "unit": "EUR/MWh",
                        "market": f"EPEX_{bidding_zone}_DAY_AHEAD"
                    }
            
            print("No prices found or no matching time period")
            return None
            
        except Exception as e:
            print(f"Error fetching EPEX Spot data: {e}")
            return None
    
    def push_price(self, market: str, price: float, volume: float = 1.0) -> bool:
        """Push price to the exchange server
        
        Args:
            market: Market identifier (e.g., 'awattar_at', 'etenso_at')
            price: Price in EUR/MWh
            volume: Trading volume
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.exchange_url}/admin/pricefeed/push"
            params = {
                "market": market,
                "price": price,
                "volume": volume
            }
            response = requests.post(url, params=params, timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error pushing price to exchange: {e}")
            return False
    
    async def run_feed(self, market: str = DEFAULT_MARKET, interval: int = MARKET_UPDATE_INTERVAL, bidding_zone: str = DEFAULT_BIDDING_ZONE):
        """Run continuous market feed
        
        Args:
            market: Market identifier (e.g., 'epex_at', 'awattar_at')
            interval: Update interval in seconds (default 5 minutes)
            bidding_zone: Bidding zone ('AT' or 'DE')
        """
        print(f"Starting market feed for {market} (update interval: {interval}s)")
        
        while True:
            try:
                # Try EPEX Spot first (official source)
                price_data = self.fetch_epex_spot(bidding_zone)
                source_name = "EPEX Spot"
                
                # Fallback to aWattar if EPEX not available
                if not price_data:
                    price_data = self.fetch_awattar(bidding_zone)
                    source_name = "aWattar"
                
                if price_data and price_data.get("price_eur_mwh"):
                    price = price_data["price_eur_mwh"]
                    
                    # Additional safety check: if price still seems too high, divide by 10
                    if price > 200:
                        print(f"[{datetime.now()}] WARNING: Price {price} EUR/MWh seems too high, dividing by 10")
                        price = round(price / 10.0, 2)
                        print(f"[{datetime.now()}] Corrected price: {price} EUR/MWh")
                    
                    # Use market from price data if available, otherwise use parameter
                    market_id = price_data.get("market", market)
                    success = self.push_price(market_id, price)
                    
                    if success:
                        print(f"[{datetime.now()}] {market_id}: {price:.2f} EUR/MWh (source: {source_name})")
                    else:
                        print(f"[{datetime.now()}] Failed to push price to exchange")
                else:
                    print(f"[{datetime.now()}] No price data available from {source_name}")
                
            except Exception as e:
                print(f"[{datetime.now()}] Error in market feed: {e}")
            
            await asyncio.sleep(interval)


def main():
    """Main entry point for the market feed service"""
    exchange_url = os.getenv("EXCHANGE_URL", "http://exchange:9000")
    market = os.getenv("MARKET", DEFAULT_MARKET)
    interval = int(os.getenv("UPDATE_INTERVAL", str(MARKET_UPDATE_INTERVAL)))
    bidding_zone = os.getenv("BIDDING_ZONE", DEFAULT_BIDDING_ZONE)
    
    print(f"🚀 Starting Market Feed Service")
    print(f"   Market: {market}")
    print(f"   Bidding Zone: {bidding_zone}")
    print(f"   Update Interval: {interval}s")
    print(f"   ENTSO-E Token: {ENTSO_E_API_TOKEN[:8]}...")
    
    feed = MarketFeed(exchange_url)
    asyncio.run(feed.run_feed(market, interval, bidding_zone))


if __name__ == "__main__":
    main()
