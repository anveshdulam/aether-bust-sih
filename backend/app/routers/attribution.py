from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool

from app.constants import LAMBDA_MAX, LAMBDA_MIN, PHI_MAX, PHI_MIN
from app.models import AttributionResponse
from app.models.common import VarCode
from app.services.run_service import RunService, get_run_service

router = APIRouter(tags=["attribution"])


@router.get(
    "/attribution",
    response_model=AttributionResponse,
    summary="XAI driver attribution at a point (snapped to the nearest grid cell)",
)
async def attribution(
    run_id: Annotated[str, Query(min_length=1)],
    variable: VarCode,
    lead_time: Annotated[int, Query(ge=1, le=10)],
    lat: Annotated[float, Query(ge=PHI_MIN, le=PHI_MAX)],
    lon: Annotated[float, Query(ge=LAMBDA_MIN, le=LAMBDA_MAX)],
    svc: RunService = Depends(get_run_service),
) -> AttributionResponse:
    payload = await run_in_threadpool(svc.attribution, run_id, variable, lead_time, lat, lon)
    return AttributionResponse(**payload)
