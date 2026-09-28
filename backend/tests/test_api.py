import uuid

import pytest

from app.constants import C, H, T, W
from app.db.indexes import COLLECTIONS, INDEXES

API = "/api/v1"

REQUIRED_PATHS = [
    "/health",
    "/api/v1/forecast-runs",
    "/api/v1/confidence-map",
    "/api/v1/bust-probability",
    "/api/v1/bust-detections",
    "/api/v1/attribution",
    "/api/v1/baselines",
    "/api/v1/export",
    "/api/v1/telemetry",
]

MOCK_RUN_ID = "3f2c8b7a-1d4e-4a9c-9f21-0a1b2c3d4e5f"


# --------------------------------------------------------------- health / spec


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert body["mongo"] in ("up", "down")
    assert body["model_loaded"] is True
    assert body["version"] == "1.0.0"
    assert body["uptime_s"] >= 0.0


async def test_openapi_contains_every_catalogued_path(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "AETHER-BUST API"
    assert spec["info"]["version"] == "1.0.0"

    missing = [p for p in REQUIRED_PATHS if not any(p in k for k in spec["paths"])]
    assert not missing, missing


# ------------------------------------------------------------- forecast runs


async def test_list_forecast_runs(client):
    r = await client.get(f"{API}/forecast-runs")
    assert r.status_code == 200
    page = r.json()
    assert page["total"] >= 1
    assert len(page["items"]) >= 1
    item = page["items"][0]
    assert item["n_lead_times"] == T
    assert 0.0 <= item["mean_confidence"] <= 100.0


async def test_list_forecast_runs_rejects_bad_pagination(client):
    assert (await client.get(f"{API}/forecast-runs", params={"limit": 0})).status_code == 422
    assert (await client.get(f"{API}/forecast-runs", params={"limit": 501})).status_code == 422
    assert (await client.get(f"{API}/forecast-runs", params={"offset": -1})).status_code == 422


async def test_forecast_run_detail(client, demo_run_id):
    r = await client.get(f"{API}/forecast-runs/{demo_run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == demo_run_id
    assert body["variables"] == ["t2m", "tp", "z500", "ws850"]
    grid = body["grid"]
    assert (grid["n_rows"], grid["n_cols"]) == (H, W)
    assert (grid["lat_min"], grid["lat_max"]) == (6.0, 37.75)
    assert (grid["lon_min"], grid["lon_max"]) == (68.0, 99.75)
    assert grid["resolution"] == 0.25


async def test_forecast_run_detail_unknown_is_404(client):
    r = await client.get(f"{API}/forecast-runs/{uuid.uuid4()}")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
    problem = r.json()
    assert problem["status"] == 404
    assert problem["title"] == "Not Found"
    assert problem["instance"].startswith(f"{API}/forecast-runs/")


# ------------------------------------------------------------ confidence map


async def test_confidence_map(client, demo_run_id):
    r = await client.get(f"{API}/confidence-map", params={"run_id": demo_run_id, "lead_time": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["lead_time"] == 1
    assert len(body["values"]) == H
    assert all(len(row) == W for row in body["values"])
    flat = [v for row in body["values"] for v in row]
    assert all(0.0 <= v <= 100.0 for v in flat)  # AC-F1-1
    assert set(body["stats"]) == {"min", "max", "mean", "p10", "p90"}
    assert body["stats"]["min"] <= body["stats"]["mean"] <= body["stats"]["max"]


@pytest.mark.parametrize("lead_time", [0, 11, -1])
async def test_confidence_map_rejects_out_of_range_lead_time(client, demo_run_id, lead_time):
    r = await client.get(
        f"{API}/confidence-map", params={"run_id": demo_run_id, "lead_time": lead_time}
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")


async def test_confidence_map_requires_run_id(client):
    assert (await client.get(f"{API}/confidence-map", params={"lead_time": 1})).status_code == 422


async def test_confidence_map_is_north_up(client, demo_run_id, run_service):
    """Row 0 of the response must be the northernmost row of the south-up tensor."""
    body = (
        await client.get(f"{API}/confidence-map", params={"run_id": demo_run_id, "lead_time": 3})
    ).json()
    raw = run_service.get_result(demo_run_id).confidence[2]
    assert body["values"][0] == pytest.approx(raw[H - 1].tolist(), abs=1e-4)
    assert body["values"][-1] == pytest.approx(raw[0].tolist(), abs=1e-4)


# ---------------------------------------------------------- bust probability


async def test_bust_probability(client, demo_run_id):
    r = await client.post(
        f"{API}/bust-probability",
        json={"run_id": demo_run_id, "variables": ["tp"], "lead_times": [1, 10]},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["layers"]) == 2
    for layer in body["layers"]:
        assert layer["variable"] == "tp"
        assert layer["threshold"] == 20.0
        assert 0.0 <= layer["bust_frequency"] <= 1.0
        assert len(layer["values"]) == H
        flat = [v for row in layer["values"] for v in row]
        assert all(0.0 <= v <= 1.0 for v in flat)  # AC-F2-1


async def test_bust_probability_defaults_to_all_variables_and_leads(client, demo_run_id):
    r = await client.post(f"{API}/bust-probability", json={"run_id": demo_run_id})
    assert r.status_code == 200
    assert len(r.json()["layers"]) == 4 * T


async def test_bust_probability_bbox_crops(client, demo_run_id):
    r = await client.post(
        f"{API}/bust-probability",
        json={
            "run_id": demo_run_id,
            "variables": ["t2m"],
            "lead_times": [5],
            "bbox": [74.0, 18.0, 84.0, 25.0],
        },
    )
    assert r.status_code == 200
    values = r.json()["layers"][0]["values"]
    assert 0 < len(values) < H
    assert 0 < len(values[0]) < W


async def test_bust_probability_forbids_extra_fields(client, demo_run_id):
    r = await client.post(
        f"{API}/bust-probability", json={"run_id": demo_run_id, "not_a_field": 1}
    )
    assert r.status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"run_id": "x", "lead_times": [11]},
        {"run_id": "x", "lead_times": [0]},
        {"run_id": "x", "variables": ["not_a_var"]},
        {"run_id": "x", "bbox": [68.0, 99.0, 99.75, 37.75]},  # lat 99 out of range
    ],
)
async def test_bust_probability_validation(client, body):
    assert (await client.post(f"{API}/bust-probability", json=body)).status_code == 422


# ------------------------------------------------------------- detections


async def test_bust_detections(client, demo_run_id):
    r = await client.get(
        f"{API}/bust-detections", params={"run_id": demo_run_id, "variable": "tp", "limit": 5}
    )
    assert r.status_code == 200
    page = r.json()
    assert page["limit"] == 5
    assert len(page["items"]) <= 5
    for det in page["items"]:
        assert det["variable"] == "tp"
        assert 1 <= det["lead_time"] <= T
        assert 0.0 <= det["peak_probability"] <= 1.0
        assert 0.0 <= det["mean_probability"] <= 1.0
        assert 0.0 <= det["confidence"] <= 100.0
        assert det["area_km2"] >= 0.0
        assert det["polygon"]["type"] == "Polygon"
        assert len(det["bbox"]) == 4
        # AC-F5-1: the bbox fully contains the polygon.
        lon_min, lat_min, lon_max, lat_max = det["bbox"]
        for lon, lat in det["polygon"]["coordinates"][0]:
            assert lon_min <= lon <= lon_max
            assert lat_min <= lat <= lat_max


async def test_bust_detections_rejects_bad_bbox(client, demo_run_id):
    for bad in ["1,2,3", "a,b,c,d", "68,99,99.75,37.75"]:
        r = await client.get(
            f"{API}/bust-detections", params={"run_id": demo_run_id, "bbox": bad}
        )
        assert r.status_code == 422, bad


# ------------------------------------------------------------- attribution


async def test_attribution(client, demo_run_id):
    r = await client.get(
        f"{API}/attribution",
        params={"run_id": demo_run_id, "variable": "tp", "lead_time": 7, "lat": 21.8, "lon": 78.85},
    )
    assert r.status_code == 200
    body = r.json()

    assert len(body["drivers"]) == C                                  # AC-F3-1
    scores = [d["score"] for d in body["drivers"]]
    assert scores == sorted(scores, reverse=True)
    assert abs(sum(scores) - 1.0) < 1e-6                              # AC-F3-2
    assert all(d["sign"] in ("+", "-") for d in body["drivers"])
    assert all(d["channel_name"] for d in body["drivers"])

    cam = body["spatial_gradcam"]                                     # AC-F3-3
    assert len(cam) == H and all(len(row) == W for row in cam)
    assert all(0.0 <= v <= 1.0 for row in cam for v in row)

    assert body["narrative"].startswith("Day 7 ")
    # The point is snapped to the nearest grid cell.
    assert body["lat"] == pytest.approx(21.75, abs=0.25)
    assert body["lon"] == pytest.approx(78.75, abs=0.25)


@pytest.mark.parametrize(
    "params",
    [
        {"lat": 99.0, "lon": 78.0},    # latitude out of domain
        {"lat": 21.0, "lon": 180.0},   # longitude out of domain
        {"lat": 5.0, "lon": 78.0},     # south of PHI_MIN
    ],
)
async def test_attribution_rejects_out_of_domain_points(client, demo_run_id, params):
    r = await client.get(
        f"{API}/attribution",
        params={"run_id": demo_run_id, "variable": "tp", "lead_time": 1, **params},
    )
    assert r.status_code == 422


async def test_attribution_rejects_bad_variable(client, demo_run_id):
    r = await client.get(
        f"{API}/attribution",
        params={"run_id": demo_run_id, "variable": "nope", "lead_time": 1, "lat": 21.0, "lon": 78.0},
    )
    assert r.status_code == 422


# --------------------------------------------------------- baselines / telemetry


async def test_baselines_returns_seeded_document(client, mongo_db):
    r = await client.get(f"{API}/baselines", params={"variable": "tp", "lead_time": 7})
    assert r.status_code == 200
    page = r.json()
    assert page["total"] >= 1
    base = next(b for b in page["items"] if b["baseline_id"] == "base-centralindia-tp-t07")
    assert base["region_label"] == "Central India"
    assert base["sample_count"] == 3650
    assert base["stats"]["mean_rmse"] == pytest.approx(14.83)
    assert 0.0 <= base["stats"]["bust_frequency"] <= 1.0


async def test_telemetry_returns_seeded_alert(client, mongo_db):
    r = await client.get(f"{API}/telemetry", params={"kind": "ALERT"})
    assert r.status_code == 200
    page = r.json()
    assert page["total"] >= 1
    evt = next(e for e in page["items"] if e["event_id"] == "evt-3f2c8b7a-inf-0001")
    assert evt["severity"] == "CRITICAL"
    assert evt["kind"] == "ALERT"


async def test_telemetry_rejects_bad_kind(client):
    assert (await client.get(f"{API}/telemetry", params={"kind": "NOPE"})).status_code == 422


# ------------------------------------------------------------------ export


async def test_export_rejects_unsupported_format_with_415(client, demo_run_id):
    r = await client.get(
        f"{API}/export",
        params={
            "run_id": demo_run_id, "variable": "tp", "layer": "p_bust",
            "lead_time": 1, "format": "shapefile",
        },
    )
    assert r.status_code == 415
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["title"] == "Unsupported Media Type"


async def test_export_rejects_bad_layer(client, demo_run_id):
    r = await client.get(
        f"{API}/export",
        params={
            "run_id": demo_run_id, "variable": "tp", "layer": "nope",
            "lead_time": 1, "format": "geojson",
        },
    )
    assert r.status_code == 422


# ----------------------------------------------------- database structure


async def test_all_collections_exist(mongo_db):
    names = set(await mongo_db.list_collection_names())
    for collection in COLLECTIONS:
        assert collection in names, collection


async def test_every_named_index_exists(mongo_db):
    """DB_SCHEMA sections 1.2/2.2/3.2/4.2/5.2 index names are binding."""
    for collection, specs in INDEXES.items():
        info = await mongo_db[collection].index_information()
        for _keys, kwargs in specs:
            assert kwargs["name"] in info, f"{collection}.{kwargs['name']}"


async def test_unique_and_2dsphere_indexes(mongo_db):
    runs = await mongo_db["forecast_runs"].index_information()
    assert runs["ux_run_id"].get("unique") is True

    detections = await mongo_db["bust_detections"].index_information()
    assert detections["ux_detection_id"].get("unique") is True
    assert detections["gx_geometry"]["key"] == [("geometry", "2dsphere")]
    assert detections["gx_centroid"]["key"] == [("centroid", "2dsphere")]

    baselines = await mongo_db["historical_baselines"].index_information()
    assert baselines["ux_baseline_id"].get("unique") is True
    assert baselines["ux_var_lead_region"].get("unique") is True
    assert baselines["gx_region_geometry"]["key"] == [("region_geometry", "2dsphere")]

    attributions = await mongo_db["meteorological_attributions"].index_information()
    assert attributions["ux_attribution_id"].get("unique") is True
    assert attributions["gx_location"]["key"] == [("location", "2dsphere")]

    telemetry = await mongo_db["system_telemetry"].index_information()
    assert telemetry["ux_event_id"].get("unique") is True
    assert telemetry["ttl_created"].get("expireAfterSeconds") == 7_776_000


async def test_seed_documents_present(mongo_db):
    assert await mongo_db["forecast_runs"].find_one({"run_id": MOCK_RUN_ID}) is not None
    assert await mongo_db["bust_detections"].find_one({"detection_id": "det-3f2c8b7a-t07-tp-0003"}) is not None
    assert await mongo_db["historical_baselines"].find_one({"baseline_id": "base-centralindia-tp-t07"}) is not None
    assert await mongo_db["meteorological_attributions"].find_one({"attribution_id": "attr-3f2c8b7a-t07-tp-78.85-21.80"}) is not None
    assert await mongo_db["system_telemetry"].find_one({"event_id": "evt-3f2c8b7a-inf-0001"}) is not None


async def test_geowithin_finds_seeded_central_india_detection(mongo_db):
    """DB_SCHEMA section 8: the 2dsphere index must serve a $geoWithin bbox query."""
    box = {
        "type": "Polygon",
        "coordinates": [[
            [74.0, 18.0], [84.0, 18.0], [84.0, 25.0], [74.0, 25.0], [74.0, 18.0],
        ]],
    }
    doc = await mongo_db["bust_detections"].find_one(
        {"centroid": {"$geoWithin": {"$geometry": box}}, "detection_id": "det-3f2c8b7a-t07-tp-0003"}
    )
    assert doc is not None
    assert doc["dominant_driver"] == "cape"
    assert doc["variable"] == "tp"


async def test_jsonschema_validator_rejects_invalid_document(mongo_db):
    """The $jsonSchema validator must be active, not merely declared."""
    from pymongo.errors import WriteError

    with pytest.raises(WriteError):
        await mongo_db["bust_detections"].insert_one(
            {
                "detection_id": "det-invalid-test",
                "run_id": "x",
                "variable": "NOT_A_VARIABLE",  # violates the enum
                "lead_time": 7,
            }
        )


async def test_run_and_detections_persisted(client, demo_run_id, mongo_db, run_service):
    await client.get(f"{API}/bust-detections", params={"run_id": demo_run_id, "limit": 1})
    await run_service.upsert_run(demo_run_id)

    assert await mongo_db["forecast_runs"].find_one({"run_id": demo_run_id}) is not None
    assert await mongo_db["bust_detections"].count_documents({"run_id": demo_run_id}) > 0
