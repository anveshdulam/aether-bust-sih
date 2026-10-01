import time
import logging
from typing import Dict, Any, List
from pymongo import MongoClient, GEOSPHERE
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AlertDispatcher:
    """
    Handles dispatching and persisting High/Critical bust alerts.
    Includes deduplication and cooldown per region.
    """
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/", cooldown_seconds: int = 3600):
        self.cooldown_seconds = cooldown_seconds
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.db = self.client["aether_bust"]
            self.alerts_col = self.db["alerts"]
            # Ensure 2dsphere index exists
            self.alerts_col.create_index([("geometry", GEOSPHERE)])
            self.mongo_available = True
        except Exception as e:
            logger.warning(f"MongoDB not available, running in fallback mode: {e}")
            self.mongo_available = False
            self._in_memory_alerts = []

        self._last_alert_time = {} # Key: (lat, lon), Value: timestamp

    def dispatch(self, lat: float, lon: float, severity: str, reason: str, run_id: str) -> bool:
        """
        Attempt to dispatch an alert. Returns True if dispatched, False if deduplicated/cooldown.
        """
        # 1. Deduplication / Cooldown
        # Round lat/lon slightly for deduplication footprint (e.g. within same ~10km grid cell)
        loc_key = (round(lat, 2), round(lon, 2))
        now = time.time()
        
        if loc_key in self._last_alert_time:
            if now - self._last_alert_time[loc_key] < self.cooldown_seconds:
                logger.debug(f"Alert for {loc_key} suppressed (cooldown).")
                return False
                
        self._last_alert_time[loc_key] = now
        
        # 2. Persist to MongoDB as GeoJSON
        alert_doc = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat] # GeoJSON is [lon, lat]
            },
            "properties": {
                "severity": severity,
                "reason": reason,
                "run_id": run_id,
                "timestamp": now
            }
        }
        
        if self.mongo_available:
            self.alerts_col.insert_one(alert_doc)
        else:
            self._in_memory_alerts.append(alert_doc)

        # 3. Pluggable Interface (Mock SMS/Email/Webhook)
        self._mock_send_sms(lat, lon, severity)
        
        return True

    def _mock_send_sms(self, lat, lon, severity):
        logger.info(f"[SIMULATED SMS] CRITICAL ALERT DISPATCHED for {lat}, {lon} - Severity: {severity}")

    def query_alerts(self, bbox: list) -> list:
        """
        Query alerts using MongoDB $geoWithin.
        bbox: [min_lon, min_lat, max_lon, max_lat]
        """
        if not self.mongo_available:
            # Fallback for demo
            return self._in_memory_alerts

        min_lon, min_lat, max_lon, max_lat = bbox
        
        query = {
            "geometry": {
                "$geoWithin": {
                    "$box": [
                        [min_lon, min_lat],
                        [max_lon, max_lat]
                    ]
                }
            }
        }
        
        results = []
        for doc in self.alerts_col.find(query):
            doc["_id"] = str(doc["_id"])
            results.append(doc)
            
        return results
