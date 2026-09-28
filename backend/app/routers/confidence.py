from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool

from app.models import ConfidenceMapResponse, GridMeta
from app.services.run_service import RunService, get_run_service

router = APIRouter(tags=["confidence"])


@router.get(
    "/confidence-map",
    response_model=ConfidenceMapResponse,
    summary="Confidence index field for a run and lead time",
)
async def confidence_map(
    run_id: Annotated[str, Query(min_length=1)],
    lead_time: Annotated[int, Query(ge=1, le=10)],
    svc: RunService = Depends(get_run_service),
) -> ConfidenceMapResponse:
    values, stats = await run_in_threadpool(svc.confidence_map, run_id, lead_time)
    return ConfidenceMapResponse(
        run_id=run_id,
        lead_time=lead_time,
        grid=GridMeta(),
        values=values,
        stats=stats,
    )
