from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.constants import LAMBDA_MAX, LAMBDA_MIN, PHI_MAX, PHI_MIN
from app.db import client as db_client
from app.models import (
    BustDetection,
    BustProbabilityRequest,
    BustProbabilityResponse,
    GridMeta,
    HistoricalBaseline,
    Page,
)
from app.models.common import VarCode
from app.services.run_service import RunService, get_run_service

router = APIRouter(tags=["bust"])


def parse_bbox(raw: str | None):
    """`lon_min,lat_min,lon_max,lat_max` -> tuple, or None. Invalid input -> 422."""
    if raw is None or not raw.strip():
        return None
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 4:
        raise HTTPException(status_code=422, detail="bbox must be 'lon_min,lat_min,lon_max,lat_max'")
    try:
        lon_min, lat_min, lon_max, lat_max = (float(p) for p in parts)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"bbox values must be numeric: {exc}") from exc

    for lon in (lon_min, lon_max):
        if not LAMBDA_MIN <= lon <= LAMBDA_MAX:
            raise HTTPException(
                status_code=422, detail=f"longitude {lon} outside [{LAMBDA_MIN}, {LAMBDA_MAX}]"
            )
    for lat in (lat_min, lat_max):
        if not PHI_MIN <= lat <= PHI_MAX:
            raise HTTPException(
                status_code=422, detail=f"latitude {lat} outside [{PHI_MIN}, {PHI_MAX}]"
            )
    return (lon_min, lat_min, lon_max, lat_max)


@router.post(
    "/bust-probability",
    response_model=BustProbabilityResponse,
    summary="Bust probability layers for selected variables, leads and bbox",
)
async def bust_probability(
    payload: BustProbabilityRequest,
    svc: RunService = Depends(get_run_service),
) -> BustProbabilityResponse:
    layers = await run_in_threadpool(
        svc.bust_layers, payload.run_id, payload.variables, payload.lead_times, payload.bbox
    )
    return BustProbabilityResponse(run_id=payload.run_id, grid=GridMeta(), layers=layers)


@router.get(
    "/bust-detections",
    response_model=Page[BustDetection],
    summary="Masked bust blobs for a run (PRD 3.5)",
)
async def bust_detections(
    run_id: Annotated[str, Query(min_length=1)],
    svc: RunService = Depends(get_run_service),
    variable: VarCode | None = None,
    lead_time: Annotated[int | None, Query(ge=1, le=10)] = None,
    bbox: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[BustDetection]:
    box = parse_bbox(bbox)
    docs = await run_in_threadpool(svc.detections, run_id)

    if variable is not None:
        docs = [d for d in docs if d["variable"] == variable]
    if lead_time is not None:
        docs = [d for d in docs if d["lead_time"] == lead_time]
    if box is not None:
        docs = [d for d in docs if _bbox_overlaps(d["bbox"], box)]

    total = len(docs)
    window = docs[offset : offset + limit]

    # Keep the persisted view in sync with what the dashboard is showing.
    await svc.persist_detections(run_id)

    return Page[BustDetection](
        items=[BustDetection(**_detection_fields(d)) for d in window],
        total=total,
        limit=limit,
        offset=offset,
    )


def _bbox_overlaps(a, b) -> bool:
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def _detection_fields(doc: dict) -> dict:
    out = {
        k: doc[k]
        for k in (
            "detection_id", "run_id", "variable", "lead_time", "bbox",
            "peak_probability", "mean_probability", "area_km2",
            "dominant_driver", "confidence", "created_at",
        )
    }
    out["polygon"] = doc["geometry"]
    return out


@router.get(
    "/baselines",
    response_model=Page[HistoricalBaseline],
    summary="Historical per-region error baselines",
)
async def baselines(
    variable: VarCode | None = None,
    lead_time: Annotated[int | None, Query(ge=1, le=10)] = None,
    region_label: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[HistoricalBaseline]:
    db = db_client.get_db()
    if db is None or not await db_client.ping():
        return Page[HistoricalBaseline](items=[], total=0, limit=limit, offset=offset)

    query: dict = {}
    if variable is not None:
        query["variable"] = variable
    if lead_time is not None:
        query["lead_time"] = lead_time
    if region_label:
        query["region_label"] = region_label

    total = await db["historical_baselines"].count_documents(query)
    cursor = (
        db["historical_baselines"]
        .find(query)
        .sort([("lead_time", 1), ("variable", 1)])
        .skip(offset)
        .limit(limit)
    )
    items = []
    async for doc in cursor:
        doc.pop("_id", None)
        items.append(HistoricalBaseline(**doc))
    return Page[HistoricalBaseline](items=items, total=total, limit=limit, offset=offset)
