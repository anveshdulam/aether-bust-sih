from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TelemetryKind = Literal["INFERENCE", "ALERT", "EXPORT", "ERROR"]
TelemetrySeverity = Literal["INFO", "WARN", "CRITICAL"]


class TelemetryEvent(BaseModel):
    event_id: str
    kind: TelemetryKind
    severity: TelemetrySeverity
    run_id: str | None = None
    message: str
    latency_ms: float | None = None
    created_at: datetime


class HealthResponse(BaseModel):
    # `model_loaded` is a spec field name (TRD 5.3); opt out of Pydantic's
    # reserved `model_` namespace rather than renaming it.
    model_config = ConfigDict(protected_namespaces=())

    status: Literal["ok", "degraded"]
    version: str
    mongo: Literal["up", "down"]
    model_loaded: bool
    uptime_s: float
