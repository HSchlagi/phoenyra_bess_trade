"""
BESS Telemetry Service - Automatische Telemetrie-Erfassung
Unterstützt Modbus TCP, MQTT und REST API Schnittstellen
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any
import os
import logging

# Modbus TCP Support
try:
    from pymodbus.client.sync import ModbusTcpClient
    from pymodbus.exceptions import ModbusException
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    print("⚠️ pymodbus nicht installiert. Modbus TCP nicht verfügbar.")

# MQTT Support
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️ paho-mqtt nicht installiert. MQTT nicht verfügbar.")

class BESSTelemetryService:
    """Service für automatische BESS-Telemetrie-Erfassung"""
    
    def __init__(self, exchange_url: str = "http://exchange:9000"):
        self.exchange_url = exchange_url
        self.logger = logging.getLogger(__name__)
        
        # Modbus TCP Konfiguration
        self.modbus_config = {
            "host": os.getenv("BESS_MODBUS_HOST", "192.168.1.100"),
            "port": int(os.getenv("BESS_MODBUS_PORT", "502")),
            "unit_id": int(os.getenv("BESS_MODBUS_UNIT_ID", "1")),
            "soc_register": int(os.getenv("BESS_MODBUS_SOC_REGISTER", "0")),
            "power_register": int(os.getenv("BESS_MODBUS_POWER_REGISTER", "1")),
            "temp_register": int(os.getenv("BESS_MODBUS_TEMP_REGISTER", "2")),
            "enabled": os.getenv("BESS_MODBUS_ENABLED", "false").lower() == "true"
        }
        
        # MQTT Konfiguration
        self.mqtt_config = {
            "broker": os.getenv("BESS_MQTT_BROKER", "localhost"),
            "port": int(os.getenv("BESS_MQTT_PORT", "1883")),
            "username": os.getenv("BESS_MQTT_USERNAME", ""),
            "password": os.getenv("BESS_MQTT_PASSWORD", ""),
            "topics": {
                "soc": os.getenv("BESS_MQTT_TOPIC_SOC", "bess/soc"),
                "power": os.getenv("BESS_MQTT_TOPIC_POWER", "bess/power"),
                "temperature": os.getenv("BESS_MQTT_TOPIC_TEMP", "bess/temperature")
            },
            "enabled": os.getenv("BESS_MQTT_ENABLED", "false").lower() == "true"
        }
        
        # REST API Konfiguration
        self.rest_config = {
            "api_key": os.getenv("BESS_API_KEY", "bess_telemetry_key"),
            "enabled": os.getenv("BESS_REST_ENABLED", "true").lower() == "true"
        }
        
        # Update-Intervalle
        self.update_interval = int(os.getenv("BESS_UPDATE_INTERVAL", "30"))  # 30 Sekunden
        
        # MQTT Client
        self.mqtt_client = None
        if MQTT_AVAILABLE and self.mqtt_config["enabled"]:
            self.setup_mqtt_client()
    
    def setup_mqtt_client(self):
        """MQTT Client Setup"""
        if not MQTT_AVAILABLE:
            return
            
        self.mqtt_client = mqtt.Client()
        
        if self.mqtt_config["username"]:
            self.mqtt_client.username_pw_set(
                self.mqtt_config["username"], 
                self.mqtt_config["password"]
            )
        
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT Verbindung hergestellt"""
        if rc == 0:
            self.logger.info("✅ MQTT verbunden")
            # Subscribe zu allen BESS-Topics
            for topic in self.mqtt_config["topics"].values():
                client.subscribe(topic)
                self.logger.info(f"📡 Subscribed to: {topic}")
        else:
            self.logger.error(f"❌ MQTT Verbindung fehlgeschlagen: {rc}")
    
    def on_mqtt_message(self, client, userdata, message):
        """MQTT Nachricht empfangen"""
        try:
            topic = message.topic
            payload = json.loads(message.payload.decode())
            
            # Telemetrie-Daten basierend auf Topic
            telemetry_data = {}
            
            if topic == self.mqtt_config["topics"]["soc"]:
                telemetry_data["soc_percent"] = float(payload.get("value", payload.get("soc", 0)))
            elif topic == self.mqtt_config["topics"]["power"]:
                telemetry_data["active_power_mw"] = float(payload.get("value", payload.get("power", 0)))
            elif topic == self.mqtt_config["topics"]["temperature"]:
                telemetry_data["temperature_c"] = float(payload.get("value", payload.get("temp", 0)))
            
            if telemetry_data:
                self.send_telemetry_to_exchange(telemetry_data)
                self.logger.info(f"📊 MQTT Telemetrie: {telemetry_data}")
                
        except Exception as e:
            self.logger.error(f"❌ MQTT Nachricht Fehler: {e}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT Verbindung getrennt"""
        self.logger.warning("⚠️ MQTT Verbindung getrennt")
    
    def read_modbus_telemetry(self) -> Optional[Dict[str, float]]:
        """Modbus TCP Telemetrie lesen"""
        if not MODBUS_AVAILABLE or not self.modbus_config["enabled"]:
            return None
        
        try:
            client = ModbusTcpClient(
                self.modbus_config["host"], 
                port=self.modbus_config["port"]
            )
            
            if not client.connect():
                self.logger.error("❌ Modbus TCP Verbindung fehlgeschlagen")
                return None
            
            # Register-Adressen aus Konfiguration
            soc_register = self.modbus_config["soc_register"]
            power_register = self.modbus_config["power_register"]
            temp_register = self.modbus_config["temp_register"]
            
            # Register lesen
            soc_result = client.read_holding_registers(soc_register, 1, unit=self.modbus_config["unit_id"])
            power_result = client.read_holding_registers(power_register, 1, unit=self.modbus_config["unit_id"])
            temp_result = client.read_holding_registers(temp_register, 1, unit=self.modbus_config["unit_id"])
            
            if (soc_result.isError() or power_result.isError() or temp_result.isError()):
                self.logger.error("❌ Modbus Register-Lesefehler")
                return None
            
            # Werte konvertieren
            soc_percent = soc_result.registers[0] / 100.0  # Prozent
            power_kw = power_result.registers[0] / 1000.0   # kW zu MW
            temp_c = temp_result.registers[0] / 10.0        # °C (0.1°C Auflösung)
            
            client.close()
            
            return {
                "soc_percent": soc_percent,
                "active_power_mw": power_kw,
                "temperature_c": temp_c
            }
            
        except Exception as e:
            self.logger.error(f"❌ Modbus TCP Fehler: {e}")
            return None
    
    def send_telemetry_to_exchange(self, telemetry_data: Dict[str, float]):
        """Telemetrie an Exchange Service senden"""
        try:
            response = requests.post(
                f"{self.exchange_url}/telemetry/bess",
                json=telemetry_data,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.info(f"✅ Telemetrie gesendet: {telemetry_data}")
                return True
            else:
                self.logger.error(f"❌ Telemetrie-Fehler: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Telemetrie-Sendefehler: {e}")
            return False
    
    async def start_mqtt_client(self):
        """MQTT Client starten"""
        if not self.mqtt_client or not self.mqtt_config["enabled"]:
            return
        
        try:
            self.mqtt_client.connect(
                self.mqtt_config["broker"], 
                self.mqtt_config["port"], 
                60
            )
            self.mqtt_client.loop_start()
            self.logger.info("🚀 MQTT Client gestartet")
        except Exception as e:
            self.logger.error(f"❌ MQTT Start-Fehler: {e}")
    
    async def run_telemetry_service(self):
        """Haupt-Telemetrie-Service"""
        self.logger.info("🚀 BESS Telemetrie-Service gestartet")
        
        # MQTT Client starten
        if self.mqtt_config["enabled"]:
            await self.start_mqtt_client()
        
        # Hauptschleife
        while True:
            try:
                # Modbus TCP Telemetrie (falls aktiviert)
                if self.modbus_config["enabled"]:
                    modbus_data = self.read_modbus_telemetry()
                    if modbus_data:
                        self.send_telemetry_to_exchange(modbus_data)
                        self.logger.info(f"📊 Modbus Telemetrie: {modbus_data}")
                
                # Warten bis nächster Update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Telemetrie-Service Fehler: {e}")
                await asyncio.sleep(5)  # Kurze Pause bei Fehlern
    
    def stop(self):
        """Service stoppen"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        self.logger.info("🛑 BESS Telemetrie-Service gestoppt")


def main():
    """Hauptfunktion für BESS Telemetrie-Service"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    service = BESSTelemetryService()
    
    try:
        asyncio.run(service.run_telemetry_service())
    except KeyboardInterrupt:
        service.stop()
        print("🛑 Service gestoppt")


if __name__ == "__main__":
    main()
