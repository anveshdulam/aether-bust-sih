from typing import Annotated

from fastapi import APIRouter, Query

from app.db import client as db_client
from app.models import Page, TelemetryEvent
from app.models.telemetry import TelemetryKind, TelemetrySeverity

router = APIRouter(tags=["telemetry"])

EVENT_FIELDS = ("event_id", "kind", "severity", "run_id", "message", "latency_ms", "created_at")


@router.get("/telemetry", response_model=Page[TelemetryEvent], summary="System telemetry and alerts")
async def telemetry(
    kind: TelemetryKind | None = None,
    severity: TelemetrySeverity | None = None,
    run_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[TelemetryEvent]:
    db = db_client.get_db()
    if db is None or not await db_client.ping():
        return Page[TelemetryEvent](items=[], total=0, limit=limit, offset=offset)

    query: dict = {}
    if kind is not None:
        query["kind"] = kind
    if severity is not None:
        query["severity"] = severity
    if run_id:
        query["run_id"] = run_id

    total = await db["system_telemetry"].count_documents(query)
    cursor = db["system_telemetry"].find(query).sort("created_at", -1).skip(offset).limit(limit)
    items = []
    async for doc in cursor:
        items.append(TelemetryEvent(**{k: doc.get(k) for k in EVENT_FIELDS}))
    return Page[TelemetryEvent](items=items, total=total, limit=limit, offset=offset)
