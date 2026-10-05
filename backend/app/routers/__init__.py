from app.routers import (
    attribution,
    bust,
    confidence,
    export,
    forecast_runs,
    health,
    telemetry,
    live,
    chat,
)

# Routers mounted under /api/v1 by the app factory, in catalogue order (TRD 5.2).
API_ROUTERS = (
    forecast_runs.router,
    confidence.router,
    bust.router,
    attribution.router,
    export.router,
    telemetry.router,
    live.router,
    chat.router,
)

# Mounted at the app root.
ROOT_ROUTERS = (health.router,)

__all__ = [
    "API_ROUTERS",
    "ROOT_ROUTERS",
    "attribution",
    "bust",
    "confidence",
    "export",
    "forecast_runs",
    "health",
    "telemetry",
]
