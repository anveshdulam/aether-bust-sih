from typing import List, Optional, Dict
from pydantic import BaseModel, Field

# We use simple docstrings and typing so that the Gemini API can auto-generate the schemas.
# Data Tools

def get_run_summary(run_id: str) -> dict:
    """Returns basic metadata about a forecast run: grid size, lead days, channels, and provenance."""
    # This will be injected with actual logic in chat_service.py by closing over the RunService
    pass

def get_hotspots(run_id: str, day: int, top_k: int, threshold: float) -> list:
    """Finds the highest risk areas (bust probability hotspots) for a given lead time day."""
    pass

def get_region_stats(run_id: str, day: int, bbox: list[float]) -> dict:
    """Calculates statistics (mean, max, percentiles) of bust probability and error magnitude in a bounding box [lon_min, lat_min, lon_max, lat_max]."""
    pass

def get_attribution(run_id: str, lat: float, lon: float, day: int) -> dict:
    """Uses Integrated Gradients XAI to find the driving atmospheric variables for a forecast bust at a specific coordinate."""
    pass

def compare_days(run_id: str, day_a: int, day_b: int, bbox: Optional[List[float]] = None) -> dict:
    """Compares the bust risk between two different lead time days to see how risk changes over time."""
    pass

# UI-Action Tools
# These return a specific signature that the agent loop intercepts to emit an SSE event.

def set_day(day: int) -> dict:
    """Changes the UI map to show predictions for a specific lead time day (1 to 10)."""
    return {"_ui_action": "set_day", "params": {"day": day}}

def select_point(lat: float, lon: float) -> dict:
    """Selects a specific latitude and longitude point on the map, opening the XAI panel."""
    return {"_ui_action": "select_point", "params": {"lat": lat, "lon": lon}}

def set_layer(layer: str) -> dict:
    """Changes the map layer. Valid values are 'p_bust', 'error', 'confidence'."""
    return {"_ui_action": "set_layer", "params": {"layer": layer}}

def highlight_bbox(bbox: list[float]) -> dict:
    """Draws a highlighted bounding box on the map. Format: [lon_min, lat_min, lon_max, lat_max]."""
    return {"_ui_action": "highlight_bbox", "params": {"bbox": bbox}}

def fly_to(lat: float, lon: float, zoom: float = 6.0) -> dict:
    """Pans and zooms the map camera to a specific latitude and longitude coordinate."""
    return {"_ui_action": "fly_to", "params": {"lat": lat, "lon": lon, "zoom": zoom}}
