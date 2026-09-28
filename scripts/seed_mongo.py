"""
Bootstrap MongoDB for AETHER-BUST (DB_SCHEMA section 8).

1. Creates `aether_bust` and all 5 collections with their $jsonSchema validators.
2. Creates every named index from DB_SCHEMA 1.2/2.2/3.2/4.2/5.2.
3. Upserts the 5 mock documents, idempotently, keyed by domain key.

Usage:  python scripts/seed_mongo.py [--mongo-uri URI] [--db NAME]
"""

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from bson import ObjectId  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db.indexes import ensure_schema  # noqa: E402


def dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)


MOCK_RUN_ID = "3f2c8b7a-1d4e-4a9c-9f21-0a1b2c3d4e5f"

FORECAST_RUN = {
    "_id": ObjectId("6605f1a2c3d4e5f601111101"),
    "run_id": MOCK_RUN_ID,
    "init_time": dt("2026-09-15T00:00:00.000Z"),
    "source_model": "SYNTHETIC",
    "n_lead_times": 10,
    "grid": {
        "lat_min": 6.0, "lat_max": 37.75, "lon_min": 68.0, "lon_max": 99.75,
        "resolution": 0.25, "n_rows": 128, "n_cols": 128,
    },
    "variables": ["t2m", "tp", "z500", "ws850"],
    "norm_stats_ref": "artifacts/3f2c8b7a/norm_stats.json",
    "result_refs": {
        "confidence_uri": "artifacts/3f2c8b7a/confidence.npy",
        "bust_uri": "artifacts/3f2c8b7a/bust.npy",
        "error_uri": "artifacts/3f2c8b7a/error.npy",
    },
    "mean_confidence": 71.42,
    "inference_latency_ms": 1583.7,
    "status": "COMPLETE",
    "created_at": dt("2026-09-15T00:04:11.221Z"),
    "updated_at": dt("2026-09-15T00:04:13.884Z"),
}

BUST_DETECTION = {
    "_id": ObjectId("6605f1a2c3d4e5f602222201"),
    "detection_id": "det-3f2c8b7a-t07-tp-0003",
    "run_id": MOCK_RUN_ID,
    "variable": "tp",
    "lead_time": 7,
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [78.25, 21.00], [79.50, 21.00], [79.75, 22.25],
            [78.75, 22.75], [78.00, 21.75], [78.25, 21.00],
        ]],
    },
    "centroid": {"type": "Point", "coordinates": [78.85, 21.80]},
    "bbox": [78.00, 21.00, 79.75, 22.75],
    "peak_probability": 0.87,
    "mean_probability": 0.63,
    "area_km2": 41230.5,
    "n_cells": 47,
    "dominant_driver": "cape",
    "confidence": 41.8,
    "threshold": 20.0,
    "is_regional_event": True,
    "created_at": dt("2026-09-15T00:04:12.500Z"),
}

HISTORICAL_BASELINE = {
    "_id": ObjectId("6605f1a2c3d4e5f603333301"),
    "baseline_id": "base-centralindia-tp-t07",
    "region_label": "Central India",
    "region_geometry": {
        "type": "Polygon",
        "coordinates": [[
            [74.0, 18.0], [84.0, 18.0], [84.0, 25.0], [74.0, 25.0], [74.0, 18.0],
        ]],
    },
    "variable": "tp",
    "lead_time": 7,
    "sample_count": 3650,
    "period": {"start": dt("2015-01-01T00:00:00.000Z"), "end": dt("2024-12-31T00:00:00.000Z")},
    "stats": {
        "mean_rmse": 14.83,
        "mean_mae": 9.21,
        "bust_frequency": 0.27,
        "p90_abs_error": 26.40,
        "std_abs_error": 11.05,
    },
    "threshold": 20.0,
    "created_at": dt("2026-09-14T18:00:00.000Z"),
}

ATTRIBUTION = {
    "_id": ObjectId("6605f1a2c3d4e5f604444401"),
    "attribution_id": "attr-3f2c8b7a-t07-tp-78.85-21.80",
    "run_id": MOCK_RUN_ID,
    "detection_id": "det-3f2c8b7a-t07-tp-0003",
    "variable": "tp",
    "lead_time": 7,
    "location": {"type": "Point", "coordinates": [78.85, 21.80]},
    "drivers": [
        {"channel_code": "cape", "channel_name": "Convective Available Potential Energy", "score": 0.34, "sign": "+"},
        {"channel_code": "shear_850_250", "channel_name": "Deep-layer bulk wind shear (250-850hPa)", "score": 0.21, "sign": "+"},
        {"channel_code": "z500_anom", "channel_name": "500 hPa Geopotential Height Anomaly", "score": 0.15, "sign": "+"},
        {"channel_code": "tp", "channel_name": "Total Precipitation (24h)", "score": 0.10, "sign": "+"},
        {"channel_code": "mslp", "channel_name": "Mean Sea Level Pressure", "score": 0.06, "sign": "-"},
        {"channel_code": "ws850", "channel_name": "850 hPa Wind Speed", "score": 0.05, "sign": "+"},
        {"channel_code": "v850", "channel_name": "850 hPa Meridional Wind", "score": 0.04, "sign": "+"},
        {"channel_code": "u850", "channel_name": "850 hPa Zonal Wind", "score": 0.03, "sign": "-"},
        {"channel_code": "z500", "channel_name": "500 hPa Geopotential Height", "score": 0.01, "sign": "+"},
        {"channel_code": "t2m", "channel_name": "2 m Temperature", "score": 0.01, "sign": "+"},
    ],
    "gradcam_ref": "artifacts/3f2c8b7a/gradcam_t07_tp.npy",
    "narrative": (
        "Day 7 bust risk for Total Precipitation over Central India is driven primarily by "
        "Convective Available Potential Energy (34%, +) and Deep-layer bulk wind shear (21%, +). "
        "Elevated convective instability raises precipitation-timing uncertainty."
    ),
    "created_at": dt("2026-09-15T00:04:13.010Z"),
}

TELEMETRY = {
    "_id": ObjectId("6605f1a2c3d4e5f605555501"),
    "event_id": "evt-3f2c8b7a-inf-0001",
    "kind": "ALERT",
    "severity": "CRITICAL",
    "run_id": MOCK_RUN_ID,
    "message": "Regional bust event: tp Day 7 over Central India (RMSE=24.3mm > 20.0mm; BF=0.31).",
    "latency_ms": None,
    "meta": {
        "variable": "tp",
        "lead_time": 7,
        "region_label": "Central India",
        "rmse": 24.3,
        "bust_frequency": 0.31,
        "threshold": 20.0,
    },
    "created_at": dt("2026-09-15T00:04:12.900Z"),
}

SEEDS: tuple[tuple[str, str, dict], ...] = (
    ("forecast_runs", "run_id", FORECAST_RUN),
    ("bust_detections", "detection_id", BUST_DETECTION),
    ("historical_baselines", "baseline_id", HISTORICAL_BASELINE),
    ("meteorological_attributions", "attribution_id", ATTRIBUTION),
    ("system_telemetry", "event_id", TELEMETRY),
)


async def seed(mongo_uri: str, db_name: str) -> int:
    client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=10000, uuidRepresentation="standard")
    try:
        await client.admin.command("ping")
        db = client[db_name]
        await ensure_schema(db)

        for collection, key, doc in SEEDS:
            payload = {k: v for k, v in doc.items() if k != "_id"}
            await db[collection].update_one(
                {key: doc[key]},
                {"$set": payload, "$setOnInsert": {"_id": doc["_id"]}},
                upsert=True,
            )

        for collection, _key, _doc in SEEDS:
            count = await db[collection].count_documents({})
            names = sorted((await db[collection].index_information()).keys())
            print(f"  {collection}: {count} doc(s), indexes={names}")

        print(f"SEED_OK db={db_name} uri={mongo_uri}")
        return 0
    finally:
        client.close()


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Seed MongoDB for AETHER-BUST")
    parser.add_argument("--mongo-uri", default=settings.MONGO_URI)
    parser.add_argument("--db", default=settings.MONGO_DB)
    args = parser.parse_args()
    return asyncio.run(seed(args.mongo_uri, args.db))


if __name__ == "__main__":
    raise SystemExit(main())
