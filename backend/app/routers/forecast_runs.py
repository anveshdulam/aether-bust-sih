from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.db import client as db_client
from app.models import ForecastRunDetail, ForecastRunSummary, Page
from app.services.run_service import RunService, get_run_service

router = APIRouter(prefix="/forecast-runs", tags=["forecast-runs"])

SUMMARY_FIELDS = ("run_id", "init_time", "source_model", "n_lead_times", "created_at", "mean_confidence")


@router.get("", response_model=Page[ForecastRunSummary], summary="List forecast runs")
async def list_runs(
    svc: RunService = Depends(get_run_service),
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    source_model: str | None = None,
) -> Page[ForecastRunSummary]:
    db = db_client.get_db()
    items: list[ForecastRunSummary] = []
    total = 0

    if db is not None and await db_client.ping():
        query: dict = {}
        if source_model:
            query["source_model"] = source_model
        total = await db["forecast_runs"].count_documents(query)
        cursor = db["forecast_runs"].find(query).sort("init_time", -1).skip(offset).limit(limit)
        async for doc in cursor:
            items.append(ForecastRunSummary(**{k: doc[k] for k in SUMMARY_FIELDS if k in doc}))

    if not items:
        # Mongo unavailable or empty: fall back to the runs materialized on disk
        # so the dashboard still has something to select.
        run_ids = await run_in_threadpool(svc.known_run_ids)
        if not run_ids:
            run_ids = [await run_in_threadpool(svc.default_run_id)]
        total = len(run_ids)
        for run_id in run_ids[offset : offset + limit]:
            doc = await run_in_threadpool(svc.run_document, run_id)
            items.append(ForecastRunSummary(**{k: doc[k] for k in SUMMARY_FIELDS}))

    return Page[ForecastRunSummary](items=items, total=total, limit=limit, offset=offset)


@router.get("/{run_id}", response_model=ForecastRunDetail, summary="Forecast run detail")
async def get_run(
    run_id: str,
    svc: RunService = Depends(get_run_service),
) -> ForecastRunDetail:
    db = db_client.get_db()
    if db is not None and await db_client.ping():
        doc = await db["forecast_runs"].find_one({"run_id": run_id})
        if doc is not None:
            doc.pop("_id", None)
            return ForecastRunDetail(**_detail_fields(doc))

    known = await run_in_threadpool(svc.known_run_ids)
    if run_id not in known:
        raise HTTPException(status_code=404, detail=f"Forecast run '{run_id}' not found")

    doc = await run_in_threadpool(svc.run_document, run_id)
    return ForecastRunDetail(**_detail_fields(doc))


def _detail_fields(doc: dict) -> dict:
    keys = (*SUMMARY_FIELDS, "grid", "variables", "norm_stats_ref")
    out = {k: doc[k] for k in keys if k in doc}
    out.setdefault("norm_stats_ref", "")
    return out
