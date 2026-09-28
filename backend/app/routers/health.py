import time

from fastapi import APIRouter, Depends, Request

from app.db import client as db_client
from app.models import HealthResponse
from app.services.run_service import RunService, get_run_service

router = APIRouter(tags=["health"])

_STARTED_AT = time.monotonic()


@router.get("/health", response_model=HealthResponse, summary="Liveness + dependency check")
async def health(
    request: Request,
    svc: RunService = Depends(get_run_service),
) -> HealthResponse:
    mongo_up = await db_client.ping()
    model_loaded = svc.model_loaded
    return HealthResponse(
        status="ok" if (mongo_up and model_loaded) else "degraded",
        version=request.app.state.settings.API_VERSION,
        mongo="up" if mongo_up else "down",
        model_loaded=model_loaded,
        uptime_s=round(time.monotonic() - _STARTED_AT, 3),
    )
