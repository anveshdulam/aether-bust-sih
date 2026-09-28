"""
Collection validators and indexes, transcribed verbatim from DB_SCHEMA.md
sections 1-5. BSON types and index names are binding.
"""

from pymongo import ASCENDING, DESCENDING, GEOSPHERE
from pymongo.errors import OperationFailure

CHANNEL_CODE_ENUM = [
    "t2m", "tp", "z500", "u850", "v850",
    "ws850", "cape", "mslp", "z500_anom", "shear_850_250",
]
VAR_ENUM = ["t2m", "tp", "z500", "ws850"]

TELEMETRY_TTL_SECONDS = 7_776_000  # 90 days (DB_SCHEMA 5.2)

FORECAST_RUNS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "run_id", "init_time", "source_model", "n_lead_times", "grid",
            "variables", "mean_confidence", "status", "created_at",
        ],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "run_id": {"bsonType": "string", "description": "UUIDv4 string, unique run identifier"},
            "init_time": {"bsonType": "date", "description": "Forecast initialization (00Z UTC)"},
            "source_model": {"enum": ["GFS", "ECMWF", "SYNTHETIC"]},
            "n_lead_times": {"bsonType": "int", "minimum": 10, "maximum": 10},
            "grid": {
                "bsonType": "object",
                "required": ["lat_min", "lat_max", "lon_min", "lon_max", "resolution", "n_rows", "n_cols"],
                "additionalProperties": False,
                "properties": {
                    "lat_min": {"bsonType": "double"},
                    "lat_max": {"bsonType": "double"},
                    "lon_min": {"bsonType": "double"},
                    "lon_max": {"bsonType": "double"},
                    "resolution": {"bsonType": "double"},
                    "n_rows": {"bsonType": "int"},
                    "n_cols": {"bsonType": "int"},
                },
            },
            "variables": {"bsonType": "array", "items": {"enum": VAR_ENUM}},
            "norm_stats_ref": {"bsonType": "string"},
            "result_refs": {
                "bsonType": "object",
                "description": "Storage references to precomputed grids",
                "additionalProperties": False,
                "properties": {
                    "confidence_uri": {"bsonType": "string"},
                    "bust_uri": {"bsonType": "string"},
                    "error_uri": {"bsonType": "string"},
                },
            },
            "mean_confidence": {"bsonType": "double", "minimum": 0, "maximum": 100},
            "inference_latency_ms": {"bsonType": "double", "minimum": 0},
            "status": {"enum": ["PENDING", "RUNNING", "COMPLETE", "FAILED"]},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
        },
    }
}

BUST_DETECTIONS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "detection_id", "run_id", "variable", "lead_time", "geometry", "centroid", "bbox",
            "peak_probability", "mean_probability", "area_km2", "dominant_driver", "confidence", "created_at",
        ],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "detection_id": {"bsonType": "string"},
            "run_id": {"bsonType": "string"},
            "variable": {"enum": VAR_ENUM},
            "lead_time": {"bsonType": "int", "minimum": 1, "maximum": 10},
            "geometry": {
                "bsonType": "object",
                "description": "GeoJSON Polygon of the bust blob (contour p>=0.5)",
                "required": ["type", "coordinates"],
                "properties": {
                    "type": {"enum": ["Polygon"]},
                    "coordinates": {"bsonType": "array"},
                },
            },
            "centroid": {
                "bsonType": "object",
                "required": ["type", "coordinates"],
                "properties": {
                    "type": {"enum": ["Point"]},
                    "coordinates": {
                        "bsonType": "array", "minItems": 2, "maxItems": 2,
                        "items": {"bsonType": "double"},
                    },
                },
            },
            "bbox": {
                "bsonType": "array", "minItems": 4, "maxItems": 4,
                "items": {"bsonType": "double"},
            },
            "peak_probability": {"bsonType": "double", "minimum": 0, "maximum": 1},
            "mean_probability": {"bsonType": "double", "minimum": 0, "maximum": 1},
            "area_km2": {"bsonType": "double", "minimum": 0},
            "n_cells": {"bsonType": "int", "minimum": 9},
            "dominant_driver": {"enum": CHANNEL_CODE_ENUM},
            "confidence": {"bsonType": "double", "minimum": 0, "maximum": 100},
            "threshold": {"bsonType": "double"},
            "is_regional_event": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
        },
    }
}

HISTORICAL_BASELINES_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "baseline_id", "region_label", "region_geometry", "variable", "lead_time",
            "sample_count", "period", "stats", "created_at",
        ],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "baseline_id": {"bsonType": "string"},
            "region_label": {"bsonType": "string", "description": "e.g. 'Central India' / IMD subdivision"},
            "region_geometry": {
                "bsonType": "object",
                "required": ["type", "coordinates"],
                "properties": {
                    "type": {"enum": ["Polygon", "MultiPolygon"]},
                    "coordinates": {"bsonType": "array"},
                },
            },
            "variable": {"enum": VAR_ENUM},
            "lead_time": {"bsonType": "int", "minimum": 1, "maximum": 10},
            "sample_count": {"bsonType": "int", "minimum": 1},
            "period": {
                "bsonType": "object",
                "required": ["start", "end"],
                "properties": {"start": {"bsonType": "date"}, "end": {"bsonType": "date"}},
            },
            "stats": {
                "bsonType": "object",
                "required": ["mean_rmse", "mean_mae", "bust_frequency", "p90_abs_error"],
                "additionalProperties": False,
                "properties": {
                    "mean_rmse": {"bsonType": "double", "minimum": 0},
                    "mean_mae": {"bsonType": "double", "minimum": 0},
                    "bust_frequency": {"bsonType": "double", "minimum": 0, "maximum": 1},
                    "p90_abs_error": {"bsonType": "double", "minimum": 0},
                    "std_abs_error": {"bsonType": "double", "minimum": 0},
                },
            },
            "threshold": {"bsonType": "double"},
            "created_at": {"bsonType": "date"},
        },
    }
}

METEOROLOGICAL_ATTRIBUTIONS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "attribution_id", "run_id", "variable", "lead_time",
            "location", "drivers", "narrative", "created_at",
        ],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "attribution_id": {"bsonType": "string"},
            "run_id": {"bsonType": "string"},
            "detection_id": {"bsonType": ["string", "null"]},
            "variable": {"enum": VAR_ENUM},
            "lead_time": {"bsonType": "int", "minimum": 1, "maximum": 10},
            "location": {
                "bsonType": "object",
                "required": ["type", "coordinates"],
                "properties": {
                    "type": {"enum": ["Point"]},
                    "coordinates": {
                        "bsonType": "array", "minItems": 2, "maxItems": 2,
                        "items": {"bsonType": "double"},
                    },
                },
            },
            "drivers": {
                "bsonType": "array",
                "minItems": 10,
                "maxItems": 10,
                "items": {
                    "bsonType": "object",
                    "required": ["channel_code", "channel_name", "score", "sign"],
                    "additionalProperties": False,
                    "properties": {
                        "channel_code": {"enum": CHANNEL_CODE_ENUM},
                        "channel_name": {"bsonType": "string"},
                        "score": {"bsonType": "double", "minimum": 0, "maximum": 1},
                        "sign": {"enum": ["+", "-"]},
                    },
                },
            },
            "gradcam_ref": {"bsonType": ["string", "null"], "description": "URI to 128x128 gradcam .npy"},
            "narrative": {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
        },
    }
}

SYSTEM_TELEMETRY_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["event_id", "kind", "severity", "message", "created_at"],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "event_id": {"bsonType": "string"},
            "kind": {"enum": ["INFERENCE", "ALERT", "EXPORT", "ERROR"]},
            "severity": {"enum": ["INFO", "WARN", "CRITICAL"]},
            "run_id": {"bsonType": ["string", "null"]},
            "message": {"bsonType": "string"},
            "latency_ms": {"bsonType": ["double", "null"], "minimum": 0},
            "meta": {"bsonType": "object"},
            "created_at": {"bsonType": "date"},
        },
    }
}

VALIDATORS: dict[str, dict] = {
    "forecast_runs": FORECAST_RUNS_VALIDATOR,
    "bust_detections": BUST_DETECTIONS_VALIDATOR,
    "historical_baselines": HISTORICAL_BASELINES_VALIDATOR,
    "meteorological_attributions": METEOROLOGICAL_ATTRIBUTIONS_VALIDATOR,
    "system_telemetry": SYSTEM_TELEMETRY_VALIDATOR,
}

COLLECTIONS: tuple[str, ...] = tuple(VALIDATORS)

# (keys, kwargs) per collection -- names are asserted by test_api.py / smoke_e2e.sh
INDEXES: dict[str, list[tuple[list[tuple[str, object]], dict]]] = {
    "forecast_runs": [
        ([("run_id", ASCENDING)], {"unique": True, "name": "ux_run_id"}),
        ([("init_time", DESCENDING)], {"name": "ix_init_time_desc"}),
        ([("source_model", ASCENDING), ("init_time", DESCENDING)], {"name": "ix_source_init"}),
        ([("status", ASCENDING), ("created_at", DESCENDING)], {"name": "ix_status_created"}),
    ],
    "bust_detections": [
        ([("detection_id", ASCENDING)], {"unique": True, "name": "ux_detection_id"}),
        ([("geometry", GEOSPHERE)], {"name": "gx_geometry"}),
        ([("centroid", GEOSPHERE)], {"name": "gx_centroid"}),
        ([("run_id", ASCENDING), ("lead_time", ASCENDING), ("variable", ASCENDING)], {"name": "ix_run_lead_var"}),
        ([("run_id", ASCENDING), ("peak_probability", DESCENDING)], {"name": "ix_run_peakp"}),
        ([("variable", ASCENDING), ("lead_time", ASCENDING), ("created_at", DESCENDING)], {"name": "ix_var_lead_created"}),
    ],
    "historical_baselines": [
        ([("baseline_id", ASCENDING)], {"unique": True, "name": "ux_baseline_id"}),
        ([("region_geometry", GEOSPHERE)], {"name": "gx_region_geometry"}),
        (
            [("variable", ASCENDING), ("lead_time", ASCENDING), ("region_label", ASCENDING)],
            {"unique": True, "name": "ux_var_lead_region"},
        ),
        ([("lead_time", ASCENDING), ("variable", ASCENDING)], {"name": "ix_lead_var"}),
    ],
    "meteorological_attributions": [
        ([("attribution_id", ASCENDING)], {"unique": True, "name": "ux_attribution_id"}),
        ([("location", GEOSPHERE)], {"name": "gx_location"}),
        ([("run_id", ASCENDING), ("variable", ASCENDING), ("lead_time", ASCENDING)], {"name": "ix_run_var_lead"}),
        ([("detection_id", ASCENDING)], {"name": "ix_detection", "sparse": True}),
    ],
    "system_telemetry": [
        ([("event_id", ASCENDING)], {"unique": True, "name": "ux_event_id"}),
        ([("created_at", DESCENDING)], {"name": "ix_created_desc"}),
        ([("kind", ASCENDING), ("severity", ASCENDING), ("created_at", DESCENDING)], {"name": "ix_kind_sev_created"}),
        ([("run_id", ASCENDING), ("created_at", DESCENDING)], {"name": "ix_run_created", "sparse": True}),
        ([("created_at", ASCENDING)], {"name": "ttl_created", "expireAfterSeconds": TELEMETRY_TTL_SECONDS}),
    ],
}


async def ensure_collections(db) -> None:
    """Create each collection with its $jsonSchema validator, or apply it if it exists."""
    existing = set(await db.list_collection_names())
    for name, validator in VALIDATORS.items():
        if name in existing:
            # collMod keeps an already-populated collection and refreshes the validator.
            await db.command({"collMod": name, "validator": validator, "validationLevel": "strict"})
        else:
            await db.create_collection(name, validator=validator, validationLevel="strict")


async def ensure_indexes(db) -> None:
    for name, specs in INDEXES.items():
        for keys, kwargs in specs:
            try:
                await db[name].create_index(keys, **kwargs)
            except OperationFailure as exc:
                # IndexOptionsConflict (85) / IndexKeySpecsConflict (86): an index with
                # this name already exists with different options. Rebuild it so the
                # DB_SCHEMA definition is what ends up applied.
                if exc.code not in (85, 86):
                    raise
                await db[name].drop_index(kwargs["name"])
                await db[name].create_index(keys, **kwargs)


async def ensure_schema(db) -> None:
    await ensure_collections(db)
    await ensure_indexes(db)
