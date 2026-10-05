# DB_SCHEMA.md — Database & In-Memory Data Models

**Project:** AETHER-BUST (SIH26079)
**Datastore:** MongoDB 7.0.11 (async access via `motor` 3.4.0)
**Database name:** `aether_bust`
**Binds to:** `PRD.md` §0 constants, `TRD.md` §5.3 Pydantic models.
**Document Version:** 1.0.0

All coordinates are `[longitude, latitude]` GeoJSON order (WGS84 / EPSG:4326), longitude first, per RFC 7946 — this is mandatory for `2dsphere` indexes. Domain bounds: lon ∈ [68.0, 99.75], lat ∈ [6.0, 37.75].

---

## 0. COLLECTION OVERVIEW

| Collection | Purpose | Primary key | Geo index |
|------------|---------|-------------|-----------|
| `forecast_runs` | One doc per NWP init cycle ingested/inferred | `run_id` (unique) | — |
| `bust_detections` | Detected bust blobs/regions (Pillar 2/5) | `detection_id` (unique) | `2dsphere` on `geometry` + `centroid` |
| `historical_baselines` | Per-region/lead climatological error baselines | `baseline_id` (unique) | `2dsphere` on `region_geometry` |
| `meteorological_attributions` | XAI driver attributions per detection/point | `attribution_id` (unique) | `2dsphere` on `location` |
| `system_telemetry` | Inference/alert/export/error events | `event_id` (unique) | — |

`_id` remains the default `ObjectId`; a human/domain key (`run_id`, etc.) is added with a unique index for referential joins.

---

## 1. COLLECTION: `forecast_runs`

### 1.1 JSON Schema (`$jsonSchema` validator, BSON types)

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["run_id","init_time","source_model","n_lead_times","grid","variables","mean_confidence","status","created_at"],
    "additionalProperties": false,
    "properties": {
      "_id":            { "bsonType": "objectId" },
      "run_id":         { "bsonType": "string", "description": "UUIDv4 string, unique run identifier" },
      "init_time":      { "bsonType": "date", "description": "Forecast initialization (00Z UTC)" },
      "source_model":   { "enum": ["GFS","ECMWF","SYNTHETIC"] },
      "n_lead_times":   { "bsonType": "int", "minimum": 10, "maximum": 10 },
      "grid": {
        "bsonType": "object",
        "required": ["lat_min","lat_max","lon_min","lon_max","resolution","n_rows","n_cols"],
        "additionalProperties": false,
        "properties": {
          "lat_min":    { "bsonType": "double" },
          "lat_max":    { "bsonType": "double" },
          "lon_min":    { "bsonType": "double" },
          "lon_max":    { "bsonType": "double" },
          "resolution": { "bsonType": "double" },
          "n_rows":     { "bsonType": "int" },
          "n_cols":     { "bsonType": "int" }
        }
      },
      "variables":      { "bsonType": "array", "items": { "enum": ["t2m","tp","z500","ws850"] } },
      "norm_stats_ref": { "bsonType": "string" },
      "result_refs": {
        "bsonType": "object",
        "description": "Storage references to precomputed grids",
        "additionalProperties": false,
        "properties": {
          "confidence_uri": { "bsonType": "string" },
          "bust_uri":       { "bsonType": "string" },
          "error_uri":      { "bsonType": "string" }
        }
      },
      "mean_confidence": { "bsonType": "double", "minimum": 0, "maximum": 100 },
      "inference_latency_ms": { "bsonType": "double", "minimum": 0 },
      "status":         { "enum": ["PENDING","RUNNING","COMPLETE","FAILED"] },
      "created_at":     { "bsonType": "date" },
      "updated_at":     { "bsonType": "date" }
    }
  }
}
```

### 1.2 Indexes

```js
db.forecast_runs.createIndex({ "run_id": 1 }, { unique: true, name: "ux_run_id" })
db.forecast_runs.createIndex({ "init_time": -1 }, { name: "ix_init_time_desc" })
db.forecast_runs.createIndex({ "source_model": 1, "init_time": -1 }, { name: "ix_source_init" })
db.forecast_runs.createIndex({ "status": 1, "created_at": -1 }, { name: "ix_status_created" })
```

### 1.3 Mock Document (valid)

```json
{
  "_id": { "$oid": "6605f1a2c3d4e5f601111101" },
  "run_id": "3f2c8b7a-1d4e-4a9c-9f21-0a1b2c3d4e5f",
  "init_time": { "$date": "2026-09-15T00:00:00.000Z" },
  "source_model": "SYNTHETIC",
  "n_lead_times": 10,
  "grid": {
    "lat_min": 6.0, "lat_max": 37.75, "lon_min": 68.0, "lon_max": 99.75,
    "resolution": 0.25, "n_rows": 128, "n_cols": 128
  },
  "variables": ["t2m", "tp", "z500", "ws850"],
  "norm_stats_ref": "artifacts/3f2c8b7a/norm_stats.json",
  "result_refs": {
    "confidence_uri": "artifacts/3f2c8b7a/confidence.npy",
    "bust_uri": "artifacts/3f2c8b7a/bust.npy",
    "error_uri": "artifacts/3f2c8b7a/error.npy"
  },
  "mean_confidence": 71.42,
  "inference_latency_ms": 1583.7,
  "status": "COMPLETE",
  "created_at": { "$date": "2026-09-15T00:04:11.221Z" },
  "updated_at": { "$date": "2026-09-15T00:04:13.884Z" }
}
```

---

## 2. COLLECTION: `bust_detections`

### 2.1 JSON Schema

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["detection_id","run_id","variable","lead_time","geometry","centroid","bbox",
                 "peak_probability","mean_probability","area_km2","dominant_driver","confidence","created_at"],
    "additionalProperties": false,
    "properties": {
      "_id":              { "bsonType": "objectId" },
      "detection_id":     { "bsonType": "string" },
      "run_id":           { "bsonType": "string" },
      "variable":         { "enum": ["t2m","tp","z500","ws850"] },
      "lead_time":        { "bsonType": "int", "minimum": 1, "maximum": 10 },
      "geometry": {
        "bsonType": "object",
        "description": "GeoJSON Polygon of the bust blob (contour p>=0.5)",
        "required": ["type","coordinates"],
        "properties": {
          "type":        { "enum": ["Polygon"] },
          "coordinates": { "bsonType": "array" }
        }
      },
      "centroid": {
        "bsonType": "object",
        "required": ["type","coordinates"],
        "properties": {
          "type":        { "enum": ["Point"] },
          "coordinates": { "bsonType": "array", "minItems": 2, "maxItems": 2, "items": { "bsonType": "double" } }
        }
      },
      "bbox":             { "bsonType": "array", "minItems": 4, "maxItems": 4, "items": { "bsonType": "double" } },
      "peak_probability": { "bsonType": "double", "minimum": 0, "maximum": 1 },
      "mean_probability": { "bsonType": "double", "minimum": 0, "maximum": 1 },
      "area_km2":         { "bsonType": "double", "minimum": 0 },
      "n_cells":          { "bsonType": "int", "minimum": 9 },
      "dominant_driver":  { "enum": ["t2m","tp","z500","u850","v850","ws850","cape","mslp","z500_anom","shear_850_250"] },
      "confidence":       { "bsonType": "double", "minimum": 0, "maximum": 100 },
      "threshold":        { "bsonType": "double" },
      "is_regional_event":{ "bsonType": "bool" },
      "created_at":       { "bsonType": "date" }
    }
  }
}
```

### 2.2 Indexes

```js
db.bust_detections.createIndex({ "detection_id": 1 }, { unique: true, name: "ux_detection_id" })
db.bust_detections.createIndex({ "geometry": "2dsphere" }, { name: "gx_geometry" })
db.bust_detections.createIndex({ "centroid": "2dsphere" }, { name: "gx_centroid" })
db.bust_detections.createIndex({ "run_id": 1, "lead_time": 1, "variable": 1 }, { name: "ix_run_lead_var" })
db.bust_detections.createIndex({ "run_id": 1, "peak_probability": -1 }, { name: "ix_run_peakp" })
db.bust_detections.createIndex({ "variable": 1, "lead_time": 1, "created_at": -1 }, { name: "ix_var_lead_created" })
```

> The compound `ix_run_lead_var` serves the primary dashboard query (`run + lead time + variable`); `gx_geometry`/`gx_centroid` serve `$geoWithin`/`$near` bbox queries from `GET /api/v1/bust-detections?bbox=`.

### 2.3 Mock Document

```json
{
  "_id": { "$oid": "6605f1a2c3d4e5f602222201" },
  "detection_id": "det-3f2c8b7a-t07-tp-0003",
  "run_id": "3f2c8b7a-1d4e-4a9c-9f21-0a1b2c3d4e5f",
  "variable": "tp",
  "lead_time": 7,
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [78.25, 21.00], [79.50, 21.00], [79.75, 22.25],
      [78.75, 22.75], [78.00, 21.75], [78.25, 21.00]
    ]]
  },
  "centroid": { "type": "Point", "coordinates": [78.85, 21.80] },
  "bbox": [78.00, 21.00, 79.75, 22.75],
  "peak_probability": 0.87,
  "mean_probability": 0.63,
  "area_km2": 41230.5,
  "n_cells": 47,
  "dominant_driver": "cape",
  "confidence": 41.8,
  "threshold": 20.0,
  "is_regional_event": true,
  "created_at": { "$date": "2026-09-15T00:04:12.500Z" }
}
```

---

## 3. COLLECTION: `historical_baselines`

Per-region, per-variable, per-lead climatological error statistics derived from historical NWP-vs-ERA5 pairs. Used to contextualize live bust risk (is today worse than usual?).

### 3.1 JSON Schema

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["baseline_id","region_label","region_geometry","variable","lead_time",
                 "sample_count","period","stats","created_at"],
    "additionalProperties": false,
    "properties": {
      "_id":            { "bsonType": "objectId" },
      "baseline_id":    { "bsonType": "string" },
      "region_label":   { "bsonType": "string", "description": "e.g. 'Central India' / IMD subdivision" },
      "region_geometry":{
        "bsonType": "object",
        "required": ["type","coordinates"],
        "properties": {
          "type":        { "enum": ["Polygon","MultiPolygon"] },
          "coordinates": { "bsonType": "array" }
        }
      },
      "variable":       { "enum": ["t2m","tp","z500","ws850"] },
      "lead_time":      { "bsonType": "int", "minimum": 1, "maximum": 10 },
      "sample_count":   { "bsonType": "int", "minimum": 1 },
      "period": {
        "bsonType": "object",
        "required": ["start","end"],
        "properties": { "start": { "bsonType": "date" }, "end": { "bsonType": "date" } }
      },
      "stats": {
        "bsonType": "object",
        "required": ["mean_rmse","mean_mae","bust_frequency","p90_abs_error"],
        "additionalProperties": false,
        "properties": {
          "mean_rmse":       { "bsonType": "double", "minimum": 0 },
          "mean_mae":        { "bsonType": "double", "minimum": 0 },
          "bust_frequency":  { "bsonType": "double", "minimum": 0, "maximum": 1 },
          "p90_abs_error":   { "bsonType": "double", "minimum": 0 },
          "std_abs_error":   { "bsonType": "double", "minimum": 0 }
        }
      },
      "threshold":      { "bsonType": "double" },
      "created_at":     { "bsonType": "date" }
    }
  }
}
```

### 3.2 Indexes

```js
db.historical_baselines.createIndex({ "baseline_id": 1 }, { unique: true, name: "ux_baseline_id" })
db.historical_baselines.createIndex({ "region_geometry": "2dsphere" }, { name: "gx_region_geometry" })
db.historical_baselines.createIndex({ "variable": 1, "lead_time": 1, "region_label": 1 }, { unique: true, name: "ux_var_lead_region" })
db.historical_baselines.createIndex({ "lead_time": 1, "variable": 1 }, { name: "ix_lead_var" })
```

### 3.3 Mock Document

```json
{
  "_id": { "$oid": "6605f1a2c3d4e5f603333301" },
  "baseline_id": "base-centralindia-tp-t07",
  "region_label": "Central India",
  "region_geometry": {
    "type": "Polygon",
    "coordinates": [[
      [74.0, 18.0], [84.0, 18.0], [84.0, 25.0], [74.0, 25.0], [74.0, 18.0]
    ]]
  },
  "variable": "tp",
  "lead_time": 7,
  "sample_count": 3650,
  "period": { "start": { "$date": "2015-01-01T00:00:00.000Z" }, "end": { "$date": "2024-12-31T00:00:00.000Z" } },
  "stats": {
    "mean_rmse": 14.83,
    "mean_mae": 9.21,
    "bust_frequency": 0.27,
    "p90_abs_error": 26.40,
    "std_abs_error": 11.05
  },
  "threshold": 20.0,
  "created_at": { "$date": "2026-09-14T18:00:00.000Z" }
}
```

---

## 4. COLLECTION: `meteorological_attributions`

Persisted XAI outputs (Grad-CAM summary + channel attributions) per detection or per queried point.

### 4.1 JSON Schema

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["attribution_id","run_id","variable","lead_time","location","drivers","narrative","created_at"],
    "additionalProperties": false,
    "properties": {
      "_id":            { "bsonType": "objectId" },
      "attribution_id": { "bsonType": "string" },
      "run_id":         { "bsonType": "string" },
      "detection_id":   { "bsonType": ["string","null"] },
      "variable":       { "enum": ["t2m","tp","z500","ws850"] },
      "lead_time":      { "bsonType": "int", "minimum": 1, "maximum": 10 },
      "location": {
        "bsonType": "object",
        "required": ["type","coordinates"],
        "properties": {
          "type":        { "enum": ["Point"] },
          "coordinates": { "bsonType": "array", "minItems": 2, "maxItems": 2, "items": { "bsonType": "double" } }
        }
      },
      "drivers": {
        "bsonType": "array",
        "minItems": 10, "maxItems": 10,
        "items": {
          "bsonType": "object",
          "required": ["channel_code","channel_name","score","sign"],
          "additionalProperties": false,
          "properties": {
            "channel_code": { "enum": ["t2m","tp","z500","u850","v850","ws850","cape","mslp","z500_anom","shear_850_250"] },
            "channel_name": { "bsonType": "string" },
            "score":        { "bsonType": "double", "minimum": 0, "maximum": 1 },
            "sign":         { "enum": ["+","-"] }
          }
        }
      },
      "gradcam_ref":    { "bsonType": ["string","null"], "description": "URI to 128x128 gradcam .npy" },
      "narrative":      { "bsonType": "string" },
      "created_at":     { "bsonType": "date" }
    }
  }
}
```

### 4.2 Indexes

```js
db.meteorological_attributions.createIndex({ "attribution_id": 1 }, { unique: true, name: "ux_attribution_id" })
db.meteorological_attributions.createIndex({ "location": "2dsphere" }, { name: "gx_location" })
db.meteorological_attributions.createIndex({ "run_id": 1, "variable": 1, "lead_time": 1 }, { name: "ix_run_var_lead" })
db.meteorological_attributions.createIndex({ "detection_id": 1 }, { name: "ix_detection", sparse: true })
```

### 4.3 Mock Document

```json
{
  "_id": { "$oid": "6605f1a2c3d4e5f604444401" },
  "attribution_id": "attr-3f2c8b7a-t07-tp-78.85-21.80",
  "run_id": "3f2c8b7a-1d4e-4a9c-9f21-0a1b2c3d4e5f",
  "detection_id": "det-3f2c8b7a-t07-tp-0003",
  "variable": "tp",
  "lead_time": 7,
  "location": { "type": "Point", "coordinates": [78.85, 21.80] },
  "drivers": [
    { "channel_code": "cape",          "channel_name": "Convective Available Potential Energy", "score": 0.34, "sign": "+" },
    { "channel_code": "shear_850_250", "channel_name": "Deep-layer bulk wind shear (250-850hPa)", "score": 0.21, "sign": "+" },
    { "channel_code": "z500_anom",     "channel_name": "500 hPa Geopotential Height Anomaly",     "score": 0.15, "sign": "+" },
    { "channel_code": "tp",            "channel_name": "Total Precipitation (24h)",               "score": 0.10, "sign": "+" },
    { "channel_code": "mslp",          "channel_name": "Mean Sea Level Pressure",                 "score": 0.06, "sign": "-" },
    { "channel_code": "ws850",         "channel_name": "850 hPa Wind Speed",                      "score": 0.05, "sign": "+" },
    { "channel_code": "v850",          "channel_name": "850 hPa Meridional Wind",                 "score": 0.04, "sign": "+" },
    { "channel_code": "u850",          "channel_name": "850 hPa Zonal Wind",                      "score": 0.03, "sign": "-" },
    { "channel_code": "z500",          "channel_name": "500 hPa Geopotential Height",             "score": 0.01, "sign": "+" },
    { "channel_code": "t2m",           "channel_name": "2 m Temperature",                         "score": 0.01, "sign": "+" }
  ],
  "gradcam_ref": "artifacts/3f2c8b7a/gradcam_t07_tp.npy",
  "narrative": "Day 7 bust risk for Total Precipitation over Central India is driven primarily by Convective Available Potential Energy (34%, +) and Deep-layer bulk wind shear (21%, +). Elevated convective instability raises precipitation-timing uncertainty.",
  "created_at": { "$date": "2026-09-15T00:04:13.010Z" }
}
```

> Note: driver `score` values are L1-normalized and sum to 1.00 (0.34+0.21+0.15+0.10+0.06+0.05+0.04+0.03+0.01+0.01 = 1.00), satisfying PRD AC-F3-2.

---

## 5. COLLECTION: `system_telemetry`

### 5.1 JSON Schema

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["event_id","kind","severity","message","created_at"],
    "additionalProperties": false,
    "properties": {
      "_id":         { "bsonType": "objectId" },
      "event_id":    { "bsonType": "string" },
      "kind":        { "enum": ["INFERENCE","ALERT","EXPORT","ERROR"] },
      "severity":    { "enum": ["INFO","WARN","CRITICAL"] },
      "run_id":      { "bsonType": ["string","null"] },
      "message":     { "bsonType": "string" },
      "latency_ms":  { "bsonType": ["double","null"], "minimum": 0 },
      "meta":        { "bsonType": "object" },
      "created_at":  { "bsonType": "date" }
    }
  }
}
```

### 5.2 Indexes

```js
db.system_telemetry.createIndex({ "event_id": 1 }, { unique: true, name: "ux_event_id" })
db.system_telemetry.createIndex({ "created_at": -1 }, { name: "ix_created_desc" })
db.system_telemetry.createIndex({ "kind": 1, "severity": 1, "created_at": -1 }, { name: "ix_kind_sev_created" })
db.system_telemetry.createIndex({ "run_id": 1, "created_at": -1 }, { name: "ix_run_created", sparse: true })
db.system_telemetry.createIndex({ "created_at": 1 }, { name: "ttl_created", expireAfterSeconds: 7776000 })
```

> TTL index expires telemetry after 90 days (7,776,000 s). Do NOT put a TTL on the other collections.

### 5.3 Mock Document

```json
{
  "_id": { "$oid": "6605f1a2c3d4e5f605555501" },
  "event_id": "evt-3f2c8b7a-inf-0001",
  "kind": "ALERT",
  "severity": "CRITICAL",
  "run_id": "3f2c8b7a-1d4e-4a9c-9f21-0a1b2c3d4e5f",
  "message": "Regional bust event: tp Day 7 over Central India (RMSE=24.3mm > 20.0mm; BF=0.31).",
  "latency_ms": null,
  "meta": {
    "variable": "tp",
    "lead_time": 7,
    "region_label": "Central India",
    "rmse": 24.3,
    "bust_frequency": 0.31,
    "threshold": 20.0
  },
  "created_at": { "$date": "2026-09-15T00:04:12.900Z" }
}
```

---

## 6. IN-MEMORY DATA MODELS (non-persisted, runtime)

These NumPy/torch structures are ephemeral (referenced by URI in `forecast_runs.result_refs`), NOT stored inline in MongoDB (BSON 16 MB doc limit; a 10×4×128×128 float32 grid ≈ 2.6 MB but nested-list JSON would exceed limits when combined).

| In-memory object | dtype/shape | Persistence |
|------------------|-------------|-------------|
| `X` input tensor | float32 `[1,10,10,128,128]` | file `artifacts/{run}/X.npy` |
| `Yb` bust prob | float32 `[10,4,128,128]` | `artifacts/{run}/bust.npy` (URI in `result_refs.bust_uri`) |
| `Ye` error | float32 `[10,4,128,128]` | `artifacts/{run}/error.npy` |
| `Yc` confidence | float32 `[10,128,128]` | `artifacts/{run}/confidence.npy` |
| `gradcam` | float32 `[128,128]` | `artifacts/{run}/gradcam_t{tt}_{var}.npy` |

The API reads these `.npy` artifacts (LRU-cached, TRD §5.7), crops/slices per request, and serializes to nested lists at the response boundary.

---

## 7. REFERENTIAL INTEGRITY (application-enforced; Mongo has no FKs)

| Child field | References | Enforced by |
|-------------|-----------|-------------|
| `bust_detections.run_id` | `forecast_runs.run_id` | `run_service` on insert |
| `meteorological_attributions.run_id` | `forecast_runs.run_id` | insert-time check |
| `meteorological_attributions.detection_id` | `bust_detections.detection_id` | nullable; check when present |
| `system_telemetry.run_id` | `forecast_runs.run_id` | nullable |

---

## 8. SEED / BOOTSTRAP (`scripts/seed_mongo.py`)

On startup (`BUILD_PLAN.md` Phase 3 verification), the seed script:
1. Creates the database `aether_bust` and all 5 collections with the `$jsonSchema` validators from §1–§5.
2. Creates every index from §1.2/§2.2/§3.2/§4.2/§5.2.
3. Inserts the 5 mock documents above (idempotent upsert by domain key).

`test_api.py` and `smoke_e2e.sh` assert each collection exists, the unique + `2dsphere` indexes are present (`db.<col>.getIndexes()` contains the named indexes), and a `$geoWithin` query on `bust_detections` returns the seeded Central-India detection.

*End of DB_SCHEMA.md — BSON types and indexes are binding.*
