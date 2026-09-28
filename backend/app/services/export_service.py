"""
Tri-format export engine (PRD 3.4 / AC-F4-1..3).

GeoJSON  -- RFC 7946 FeatureCollection of contoured p>=0.5 bust polygons.
GeoTIFF  -- single-band EPSG:4326 raster, 128x128, north-up, origin 68.0E/37.75N.
NetCDF   -- CF-1.10, dims (lead_time, lat, lon).
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import rasterio
import xarray as xr
from rasterio.transform import from_origin

from app.constants import (
    DELTA,
    H,
    LAMBDA_MIN,
    PHI_MAX,
    T,
    TAU,
    W,
    lat_vector,
    lon_vector,
)
from app.ml.masking import extract_blobs
from app.models.common import VAR_STANDARD_NAMES, VAR_UNITS

FILL_VALUE = -9999.0
CRS_EPSG = "EPSG:4326"

# Top-left corner of the north-up raster (AC-F4-2).
GEOTIFF_TRANSFORM = from_origin(LAMBDA_MIN, PHI_MAX, DELTA, DELTA)

MEDIA_TYPES = {
    "geojson": "application/geo+json",
    "geotiff": "image/tiff",
    "netcdf": "application/x-netcdf",
}
FILE_SUFFIXES = {"geojson": "geojson", "geotiff": "tif", "netcdf": "nc"}

LAYER_UNITS = {"confidence": "percent", "p_bust": "1", "error": None}
LAYER_STANDARD_NAMES = {
    "confidence": "forecast_confidence_index",
    "p_bust": "forecast_bust_probability",
    "error": "forecast_absolute_error",
}


def to_north_up(grid: np.ndarray) -> np.ndarray:
    """In-memory tensors are south-up (row 0 = 6.0N); serialization is north-up (PRD 0.1)."""
    return np.flip(np.asarray(grid), axis=-2)


# masking.py builds convex hulls from grid-cell *corners* (centre +/- DELTA/2), so a
# blob touching the domain edge extends half a cell beyond the cell-centre bounds of
# PRD 0.1. The API contract (TRD 5.3 Latitude/Longitude) is cell-centre bounds, so
# geometry is clamped at the serialization boundary.
LON_MIN = float(lon_vector()[0])
LON_MAX = float(lon_vector()[-1])
LAT_MIN = float(lat_vector()[0])
LAT_MAX = float(lat_vector()[-1])


def clamp_lon(lon: float) -> float:
    return float(min(max(float(lon), LON_MIN), LON_MAX))


def clamp_lat(lat: float) -> float:
    return float(min(max(float(lat), LAT_MIN), LAT_MAX))


def clamp_bbox(bbox) -> list[float]:
    lon_min, lat_min, lon_max, lat_max = (float(v) for v in bbox)
    return [clamp_lon(lon_min), clamp_lat(lat_min), clamp_lon(lon_max), clamp_lat(lat_max)]


def clamp_ring(ring) -> list[list[float]]:
    return [[clamp_lon(pt[0]), clamp_lat(pt[1])] for pt in ring]


def export_geojson(
    run_id: str,
    variable: str,
    lead_time: int,
    p_bust: np.ndarray,
    confidence: np.ndarray,
) -> bytes:
    """
    p_bust:     [128,128] probabilities for (variable, lead_time), south-up
    confidence: [128,128] confidence index for lead_time, south-up
    """
    features = []
    for idx, blob in enumerate(extract_blobs(np.asarray(p_bust, dtype=np.float32))):
        features.append(
            {
                "type": "Feature",
                "id": f"{run_id}-{variable}-t{lead_time:02d}-{idx:04d}",
                "bbox": clamp_bbox(blob.bbox),
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [clamp_ring(blob.polygon["coordinates"][0])],
                },
                "properties": {
                    # AC-F4-1 requires all four of these on every feature.
                    "p_bust": float(blob.peak_probability),
                    "variable": variable,
                    "lead_time": int(lead_time),
                    "confidence": _mean_confidence_in_bbox(confidence, blob.bbox),
                    "run_id": run_id,
                    "mean_p_bust": float(blob.mean_probability),
                    "area_km2": float(blob.area_km2),
                    "dominant_driver": blob.dominant_driver,
                    "threshold": float(TAU[variable]),
                },
            }
        )

    fc = {
        "type": "FeatureCollection",
        "features": features,
        "bbox": [
            float(lon_vector()[0]),
            float(lat_vector()[0]),
            float(lon_vector()[-1]),
            float(lat_vector()[-1]),
        ],
    }
    return json.dumps(fc).encode("utf-8")


def _mean_confidence_in_bbox(confidence: np.ndarray, bbox) -> float:
    lon_min, lat_min, lon_max, lat_max = (float(v) for v in bbox)
    i0 = max(0, int(np.floor((lat_min - lat_vector()[0]) / DELTA)))
    i1 = min(H - 1, int(np.ceil((lat_max - lat_vector()[0]) / DELTA)))
    j0 = max(0, int(np.floor((lon_min - lon_vector()[0]) / DELTA)))
    j1 = min(W - 1, int(np.ceil((lon_max - lon_vector()[0]) / DELTA)))
    window = np.asarray(confidence)[i0 : i1 + 1, j0 : j1 + 1]
    if window.size == 0:
        return 0.0
    return float(np.clip(window.mean(), 0.0, 100.0))


def export_geotiff(grid: np.ndarray) -> bytes:
    """Single-band GeoTIFF of a [128,128] south-up field, written north-up."""
    data = np.asarray(grid, dtype=np.float32)
    if data.shape != (H, W):
        raise ValueError(f"GeoTIFF export expects a ({H}, {W}) grid, got {data.shape}")
    data = np.ascontiguousarray(to_north_up(data))

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "layer.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=H,
            width=W,
            count=1,
            dtype="float32",
            crs=CRS_EPSG,
            transform=GEOTIFF_TRANSFORM,
            nodata=FILL_VALUE,
        ) as dst:
            dst.write(data, 1)
        return path.read_bytes()


def export_netcdf(
    cube: np.ndarray,
    layer: str,
    variable: str,
    run_id: str,
) -> bytes:
    """
    CF-1.10 NetCDF of a [10,128,128] south-up cube with dims (lead_time, lat, lon).
    """
    data = np.asarray(cube, dtype=np.float32)
    if data.shape != (T, H, W):
        raise ValueError(f"NetCDF export expects a ({T}, {H}, {W}) cube, got {data.shape}")

    var_name = "confidence" if layer == "confidence" else f"{variable}_{layer}"
    units = LAYER_UNITS.get(layer) or VAR_UNITS.get(variable, "1")
    standard_name = (
        LAYER_STANDARD_NAMES["error"] if layer == "error" else LAYER_STANDARD_NAMES[layer]
    )

    ds = xr.Dataset(
        data_vars={var_name: (("lead_time", "lat", "lon"), data)},
        coords={
            "lead_time": np.arange(1, T + 1, dtype=np.int32),
            "lat": lat_vector(),
            "lon": lon_vector(),
        },
    )
    ds.attrs["Conventions"] = "CF-1.10"
    ds.attrs["title"] = "AETHER-BUST forecast bust export"
    ds.attrs["source"] = "AETHER-BUST (SIH26079) BustNet inference"
    ds.attrs["run_id"] = run_id

    ds["lead_time"].attrs.update({"units": "days", "standard_name": "forecast_period", "long_name": "Forecast lead time"})
    ds["lat"].attrs.update({"units": "degrees_north", "standard_name": "latitude", "axis": "Y"})
    ds["lon"].attrs.update({"units": "degrees_east", "standard_name": "longitude", "axis": "X"})
    ds[var_name].attrs.update(
        {
            "units": units,
            "standard_name": standard_name,
            "long_name": f"{layer} for {variable}",
        }
    )
    if layer == "error":
        ds[var_name].attrs["ancillary_variables"] = VAR_STANDARD_NAMES.get(variable, variable)

    encoding = {var_name: {"_FillValue": FILL_VALUE, "dtype": "float32"}}

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "export.nc"
        ds.to_netcdf(path, format="NETCDF4", encoding=encoding)
        ds.close()
        return path.read_bytes()


def filename_for(run_id: str, variable: str, layer: str, lead_time: int, fmt: str) -> str:
    stem = f"aether-bust_{run_id}_{layer}_{variable}_t{lead_time:02d}"
    return f"{stem}.{FILE_SUFFIXES[fmt]}"
