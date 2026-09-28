import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool

from app.models.common import LayerCode, VarCode
from app.services import export_service
from app.services.run_service import RunService, get_run_service

router = APIRouter(tags=["export"])

SUPPORTED_FORMATS = ("geojson", "geotiff", "netcdf")


@router.get(
    "/export",
    summary="Export a layer as GeoJSON, GeoTIFF or NetCDF",
    response_class=Response,
    responses={
        200: {"content": {t: {} for t in export_service.MEDIA_TYPES.values()}},
        415: {"description": "Unsupported export format"},
    },
)
async def export(
    run_id: Annotated[str, Query(min_length=1)],
    variable: VarCode,
    layer: LayerCode,
    lead_time: Annotated[int, Query(ge=1, le=10)],
    format: str,
    svc: RunService = Depends(get_run_service),
) -> Response:
    fmt = format.strip().lower()
    if fmt not in SUPPORTED_FORMATS:
        # TRD 5.5: an unsupported format is 415, not 422.
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported export format '{format}'. Supported: {', '.join(SUPPORTED_FORMATS)}",
        )

    started = time.perf_counter()

    if fmt == "geojson":
        p_bust = await run_in_threadpool(svc.layer_grid, run_id, variable, "p_bust", lead_time)
        conf = await run_in_threadpool(svc.layer_grid, run_id, variable, "confidence", lead_time)
        body = await run_in_threadpool(
            export_service.export_geojson, run_id, variable, lead_time, p_bust, conf
        )
    elif fmt == "geotiff":
        grid = await run_in_threadpool(svc.layer_grid, run_id, variable, layer, lead_time)
        body = await run_in_threadpool(export_service.export_geotiff, grid)
    else:
        cube = await run_in_threadpool(svc.layer_cube, run_id, variable, layer)
        body = await run_in_threadpool(export_service.export_netcdf, cube, layer, variable, run_id)

    latency_ms = (time.perf_counter() - started) * 1000.0
    await svc.log_telemetry(
        kind="EXPORT",
        severity="INFO",
        message=f"Exported {layer}/{variable} Day {lead_time} as {fmt} ({len(body)} bytes).",
        run_id=run_id,
        latency_ms=latency_ms,
        meta={"variable": variable, "layer": layer, "lead_time": lead_time, "format": fmt},
    )

    filename = export_service.filename_for(run_id, variable, layer, lead_time, fmt)
    return Response(
        content=body,
        media_type=export_service.MEDIA_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
