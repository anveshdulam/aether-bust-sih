import logging
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from asgi_correlation_id import CorrelationIdMiddleware
from app.config import Settings, get_settings
from app.db import client as db_client
from app.db.indexes import ensure_schema
from app.routers import API_ROUTERS, ROOT_ROUTERS
from app.services.run_service import RunService
from app.logging import setup_logging

setup_logging()

API_PREFIX = "/api/v1"
PROBLEM_JSON = "application/problem+json"

logger = logging.getLogger("aether_bust")


def problem_response(request: Request, status: int, title: str, detail: str | None) -> ORJSONResponse:
    """RFC 9457 Problem Details (TRD 5.1)."""
    return ORJSONResponse(
        status_code=status,
        media_type=PROBLEM_JSON,
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": str(request.url.path),
        },
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    torch.set_num_threads(settings.TORCH_NUM_THREADS)
    settings.artifacts_path.mkdir(parents=True, exist_ok=True)

    db = db_client.connect(settings)
    mongo_up = await db_client.ping()
    if mongo_up:
        await ensure_schema(db)
    else:
        logger.warning("MongoDB unreachable at %s; serving in degraded mode.", settings.MONGO_URI)

    svc = RunService(settings, db=db if mongo_up else None)
    app.state.run_service = svc

    await run_in_threadpool(svc.load_model)
    await run_in_threadpool(svc.warmup)

    try:
        yield
    finally:
        await db_client.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="AETHER-BUST API",
        version="1.0.0",
        description=(
            "AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts (SIH26079). "
            "Confidence scoring, bust-risk heatmaps, XAI attribution and tri-format export."
        ),
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    app.state.settings = settings

    import uuid
    from starlette.middleware.base import BaseHTTPMiddleware
    from app.logging import correlation_id

    class CustomCorrelationIdMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            req_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
            correlation_id.set(req_id)
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response

    app.add_middleware(CustomCorrelationIdMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROOT_ROUTERS:
        app.include_router(router)
    for router in API_ROUTERS:
        app.include_router(router, prefix=API_PREFIX)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else None
        return problem_response(request, exc.status_code, _title_for(exc.status_code), detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return ORJSONResponse(
            status_code=422,
            media_type=PROBLEM_JSON,
            content={
                "type": "about:blank",
                "title": "Unprocessable Entity",
                "status": 422,
                "detail": "Request validation failed.",
                "instance": str(request.url.path),
                "errors": _serializable_errors(exc.errors()),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return problem_response(request, 422, "Unprocessable Entity", str(exc))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return problem_response(request, 500, "Internal Server Error", str(exc))

    return app


def _serializable_errors(errors: list[dict]) -> list[dict]:
    """Pydantic v2 error payloads can carry non-JSON `ctx` values; keep only safe keys."""
    out = []
    for err in errors:
        out.append(
            {
                "loc": [str(p) for p in err.get("loc", ())],
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", "")),
            }
        )
    return out


_TITLES = {
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


def _title_for(status: int) -> str:
    return _TITLES.get(status, HTTPException(status_code=status).__class__.__name__)


app = create_app()
