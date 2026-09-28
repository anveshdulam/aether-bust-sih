"""Export engine gates: AC-F4-1 (GeoJSON), AC-F4-2 (GeoTIFF), AC-F4-3 (NetCDF)."""

import io
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
import xarray as xr

from app.constants import DELTA, H, LAMBDA_MAX, LAMBDA_MIN, PHI_MAX, PHI_MIN, T, W
from app.services import export_service

API = "/api/v1"


@pytest.fixture(scope="module")
def p_bust_grid():
    """A south-up probability field with two well-separated supra-threshold blobs."""
    g = np.zeros((H, W), dtype=np.float32)
    g[30:42, 60:74] = 0.82
    g[80:90, 20:32] = 0.61
    return g


@pytest.fixture(scope="module")
def confidence_grid():
    return np.full((H, W), 42.5, dtype=np.float32)


# --------------------------------------------------------------- AC-F4-1 GeoJSON


def test_geojson_is_rfc7946_with_required_properties(p_bust_grid, confidence_grid):
    raw = export_service.export_geojson("run-1", "tp", 7, p_bust_grid, confidence_grid)
    fc = json.loads(raw)

    assert fc["type"] == "FeatureCollection"
    assert isinstance(fc["features"], list)
    assert len(fc["features"]) == 2
    assert len(fc["bbox"]) == 4

    for feature in fc["features"]:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Polygon"

        ring = feature["geometry"]["coordinates"][0]
        assert len(ring) >= 4
        # RFC 7946: linear rings are closed, and axis order is [lon, lat].
        assert ring[0] == ring[-1]
        # Coordinates stay inside the canonical domain (PRD 0.1).
        for lon, lat in ring:
            assert LAMBDA_MIN <= lon <= LAMBDA_MAX
            assert PHI_MIN <= lat <= PHI_MAX

        lon_min, lat_min, lon_max, lat_max = feature["bbox"]
        for lon, lat in ring:
            assert lon_min <= lon <= lon_max
            assert lat_min <= lat <= lat_max

        props = feature["properties"]
        for required in ("p_bust", "variable", "lead_time", "confidence"):
            assert required in props, required
        assert props["variable"] == "tp"
        assert props["lead_time"] == 7
        assert 0.0 <= props["p_bust"] <= 1.0
        assert 0.0 <= props["confidence"] <= 100.0


def test_geojson_discards_subminimum_blobs(confidence_grid):
    g = np.zeros((H, W), dtype=np.float32)
    g[10:12, 10:12] = 0.9  # 4 cells < MIN_BLOB_CELLS
    fc = json.loads(export_service.export_geojson("run-1", "t2m", 1, g, confidence_grid))
    assert fc["features"] == []


# --------------------------------------------------------------- AC-F4-2 GeoTIFF


def test_geotiff_crs_and_geotransform(p_bust_grid):
    raw = export_service.export_geotiff(p_bust_grid)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "t.tif"
        path.write_bytes(raw)
        with rasterio.open(path) as src:
            assert src.crs.to_string() == "EPSG:4326"
            assert (src.height, src.width) == (H, W)
            assert src.count == 1
            assert src.dtypes[0] == "float32"

            transform = src.transform
            # Origin is the north-west corner: 68.0E / 37.75N, pixel 0.25 deg.
            assert transform.c == pytest.approx(LAMBDA_MIN)
            assert transform.f == pytest.approx(PHI_MAX)
            assert transform.a == pytest.approx(DELTA)
            assert transform.e == pytest.approx(-DELTA)  # north-up

            band = src.read(1)
            # Row 0 of the raster is the northernmost row of the south-up tensor.
            assert band[0] == pytest.approx(p_bust_grid[H - 1])
            assert band[-1] == pytest.approx(p_bust_grid[0])


def test_geotiff_rejects_wrong_shape():
    with pytest.raises(ValueError):
        export_service.export_geotiff(np.zeros((64, 64), dtype=np.float32))


# --------------------------------------------------------------- AC-F4-3 NetCDF


def test_netcdf_dims_and_cf_attrs():
    cube = np.random.default_rng(26079).random((T, H, W)).astype(np.float32)
    raw = export_service.export_netcdf(cube, "p_bust", "tp", "run-1")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "e.nc"
        path.write_bytes(raw)
        with xr.open_dataset(path) as ds:
            assert ds.sizes["lead_time"] == T
            assert ds.sizes["lat"] == H
            assert ds.sizes["lon"] == W

            assert ds.attrs["Conventions"] == "CF-1.10"

            name = "tp_p_bust"
            assert name in ds.data_vars
            var = ds[name]
            assert var.dims == ("lead_time", "lat", "lon")
            assert "units" in var.attrs
            assert "standard_name" in var.attrs
            assert var.encoding["_FillValue"] == export_service.FILL_VALUE

            assert ds["lat"].attrs["units"] == "degrees_north"
            assert ds["lon"].attrs["units"] == "degrees_east"
            assert ds["lat"].values[0] == pytest.approx(6.0)
            assert ds["lat"].values[-1] == pytest.approx(37.75)
            assert ds["lon"].values[0] == pytest.approx(68.0)
            assert ds["lon"].values[-1] == pytest.approx(99.75)


def test_netcdf_confidence_layer_var_name():
    cube = np.full((T, H, W), 55.0, dtype=np.float32)
    raw = export_service.export_netcdf(cube, "confidence", "tp", "run-1")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.nc"
        path.write_bytes(raw)
        with xr.open_dataset(path) as ds:
            assert "confidence" in ds.data_vars
            assert ds["confidence"].attrs["units"] == "percent"


def test_netcdf_rejects_wrong_shape():
    with pytest.raises(ValueError):
        export_service.export_netcdf(np.zeros((5, H, W), dtype=np.float32), "p_bust", "tp", "r")


# ------------------------------------------------------- end-to-end via the API


async def test_export_geojson_endpoint(client, demo_run_id):
    r = await client.get(
        f"{API}/export",
        params={
            "run_id": demo_run_id, "variable": "tp", "layer": "p_bust",
            "lead_time": 3, "format": "geojson",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/geo+json")
    assert "attachment" in r.headers["content-disposition"]
    fc = r.json()
    assert fc["type"] == "FeatureCollection"
    for feature in fc["features"]:
        for required in ("p_bust", "variable", "lead_time", "confidence"):
            assert required in feature["properties"]


async def test_export_geotiff_endpoint(client, demo_run_id):
    r = await client.get(
        f"{API}/export",
        params={
            "run_id": demo_run_id, "variable": "tp", "layer": "p_bust",
            "lead_time": 3, "format": "geotiff",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/tiff")
    with rasterio.open(io.BytesIO(r.content)) as src:
        assert src.crs.to_string() == "EPSG:4326"
        assert (src.height, src.width) == (H, W)
        assert src.transform.c == pytest.approx(LAMBDA_MIN)
        assert src.transform.f == pytest.approx(PHI_MAX)


async def test_export_netcdf_endpoint(client, demo_run_id):
    r = await client.get(
        f"{API}/export",
        params={
            "run_id": demo_run_id, "variable": "tp", "layer": "confidence",
            "lead_time": 1, "format": "netcdf",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/x-netcdf")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "api.nc"
        path.write_bytes(r.content)
        with xr.open_dataset(path) as ds:
            assert (ds.sizes["lead_time"], ds.sizes["lat"], ds.sizes["lon"]) == (T, H, W)
            assert ds.attrs["Conventions"] == "CF-1.10"
            values = ds["confidence"].values
            assert np.isfinite(values).all()
            assert values.min() >= 0.0 and values.max() <= 100.0
