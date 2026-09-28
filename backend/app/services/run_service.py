"""
Orchestrates forecast runs: synthetic input materialization, BustNet inference,
in-process LRU caching of the output grids (TRD 5.7), grid slicing/cropping for
the API boundary, and MongoDB persistence of runs/detections/attributions.
"""

import hashlib
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from threading import Lock

import numpy as np
from fastapi import Request

from app.constants import (
    BF_CRIT,
    DELTA,
    H,
    T,
    TAU,
    V,
    VAR_CODES,
    W,
    W_CONF,
    lat_vector,
    lon_vector,
)
from app.ml.inference import InferenceResult, InferenceRunner
from app.ml.xai import gradcam, integrated_gradients, narrative
from app.models.common import CHANNEL_NAMES, VAR_NAMES
from app.services.export_service import clamp_bbox, clamp_lat, clamp_lon, clamp_ring

CACHE_MAXSIZE = 8  # TRD 5.7

# Integrated Gradients is a serving-path cost: every extra step is another full
# forward+backward over a [1,10,10,128,128] tensor. Two steps keeps the
# attribution ordering stable while holding the endpoint inside a request budget;
# results are cached per (run, variable, lead, cell) so a repeat read is free.
API_IG_STEPS = 2

# Region half-width, in grid cells, used to pool Grad-CAM / IG around a queried point.
ATTRIBUTION_REGION_RADIUS = 8


def utcnow() -> datetime:
    # Mongo stores millisecond precision; truncate so round-trips compare equal.
    return datetime.now(timezone.utc).replace(microsecond=0)


class _LruCache:
    """Small thread-safe LRU. Inference runs in a worker thread, so this is shared."""

    def __init__(self, maxsize: int = CACHE_MAXSIZE):
        self.maxsize = maxsize
        self._data: OrderedDict = OrderedDict()
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            if key not in self._data:
                return None
            self._data.move_to_end(key)
            return self._data[key]

    def put(self, key, value) -> None:
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)


# ---------------------------------------------------------------- grid helpers


def lat_index(lat: float) -> int:
    """Nearest south-up row index for a latitude (TRD 5.5: points snap to the grid)."""
    return int(np.clip(round((float(lat) - float(lat_vector()[0])) / DELTA), 0, H - 1))


def lon_index(lon: float) -> int:
    return int(np.clip(round((float(lon) - float(lon_vector()[0])) / DELTA), 0, W - 1))


def bbox_to_slices(bbox) -> tuple[slice, slice]:
    """[lon_min, lat_min, lon_max, lat_max] -> (row slice, col slice), south-up."""
    lon_min, lat_min, lon_max, lat_max = (float(v) for v in bbox)
    i0, i1 = sorted((lat_index(lat_min), lat_index(lat_max)))
    j0, j1 = sorted((lon_index(lon_min), lon_index(lon_max)))
    return slice(i0, i1 + 1), slice(j0, j1 + 1)


def to_north_up(grid: np.ndarray) -> np.ndarray:
    return np.flip(np.asarray(grid), axis=-2)


def grid_stats(grid: np.ndarray) -> dict[str, float]:
    a = np.asarray(grid, dtype=np.float64).ravel()
    if a.size == 0:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "p10": 0.0, "p90": 0.0}
    return {
        "min": float(a.min()),
        "max": float(a.max()),
        "mean": float(a.mean()),
        "p10": float(np.percentile(a, 10)),
        "p90": float(np.percentile(a, 90)),
    }


def deterministic_init_time(run_id: str) -> datetime:
    """
    A run's 00Z init cycle, derived from its id so it is stable across restarts
    (PRD NFR: no wall-clock-dependent logic).
    """
    digest = hashlib.sha256(run_id.encode("utf-8")).digest()
    day_offset = digest[0] % 28  # within a 4-week window
    base = datetime(2026, 9, 1, tzinfo=timezone.utc)
    return base.replace(hour=0, minute=0, second=0, microsecond=0) + _days(day_offset)


def _days(n: int):
    from datetime import timedelta

    return timedelta(days=int(n))


# ------------------------------------------------------------------- service


class RunService:
    def __init__(self, settings, db=None, runner: InferenceRunner | None = None):
        self.settings = settings
        self.db = db
        self.runner = runner or InferenceRunner(artifacts_root=settings.artifacts_path)
        self._results = _LruCache(CACHE_MAXSIZE)
        self._detections = _LruCache(CACHE_MAXSIZE)
        self._attributions = _LruCache(CACHE_MAXSIZE * 4)
        self._infer_lock = Lock()

    # -- model lifecycle ---------------------------------------------------

    def load_model(self) -> None:
        self.runner.load(self.settings.MODEL_WEIGHTS_PATH or None)

    def warmup(self) -> None:
        self.runner.warmup()

    @property
    def model_loaded(self) -> bool:
        return self.runner.is_loaded

    # -- inference + cache -------------------------------------------------

    def get_result(self, run_id: str) -> InferenceResult:
        """Cached inference outputs for `run_id`. Computes on first request."""
        cached = self._results.get(run_id)
        if cached is not None:
            return cached

        # Serialize inference: BustNet is single-threaded by contract and two
        # concurrent runs would just contend for the same core.
        with self._infer_lock:
            cached = self._results.get(run_id)
            if cached is not None:
                return cached
            result = self.runner.run(run_id)
            self._results.put(run_id, result)
            return result

    def cache_size(self) -> int:
        return len(self._results)

    def known_run_ids(self) -> list[str]:
        root = self.settings.artifacts_path
        if not root.exists():
            return []
        return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "X.npy").exists())

    def default_run_id(self) -> str:
        """An existing run id, or a freshly materialized deterministic one."""
        existing = self.known_run_ids()
        if existing:
            return existing[0]
        run_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "aether-bust/synthetic/0"))
        self.runner.ensure_inputs(run_id)
        return run_id

    # -- derived API payloads ---------------------------------------------

    def confidence_map(self, run_id: str, lead_time: int) -> tuple[list[list[float]], dict[str, float]]:
        conf = self.get_result(run_id).confidence[lead_time - 1]
        values = np.clip(to_north_up(conf), 0.0, 100.0)
        return values.astype(float).tolist(), grid_stats(values)

    def bust_layers(self, run_id: str, variables, lead_times, bbox=None):
        """One BustProbabilityLayer payload dict per (variable, lead_time)."""
        result = self.get_result(run_id)
        rows, cols = bbox_to_slices(bbox) if bbox is not None else (slice(None), slice(None))

        layers = []
        for variable in variables:
            v = VAR_CODES.index(variable)
            for lead_time in lead_times:
                p = result.bust[lead_time - 1, v][rows, cols]
                layers.append(
                    {
                        "variable": variable,
                        "lead_time": int(lead_time),
                        "values": np.clip(to_north_up(p), 0.0, 1.0).astype(float).tolist(),
                        "threshold": float(TAU[variable]),
                        # BF over the region from the predicted bust indicator
                        # p_v >= 0.5 (PRD 2.3 applied to model output rather
                        # than to truth, which is unavailable at issuance time).
                        "bust_frequency": float((p >= 0.5).mean()) if p.size else 0.0,
                    }
                )
        return layers

    def layer_grid(self, run_id: str, variable: str, layer: str, lead_time: int) -> np.ndarray:
        """South-up [128,128] slice for an export/read of one layer."""
        result = self.get_result(run_id)
        if layer == "confidence":
            return result.confidence[lead_time - 1]
        v = VAR_CODES.index(variable)
        if layer == "p_bust":
            return result.bust[lead_time - 1, v]
        return result.error[lead_time - 1, v]

    def layer_cube(self, run_id: str, variable: str, layer: str) -> np.ndarray:
        """South-up [10,128,128] cube for a NetCDF export."""
        result = self.get_result(run_id)
        if layer == "confidence":
            return result.confidence
        v = VAR_CODES.index(variable)
        return (result.bust if layer == "p_bust" else result.error)[:, v]

    def detections(self, run_id: str) -> list[dict]:
        """
        Per-variable, per-lead detections for cells where p_v >= 0.5 (AC-F2-2).
        Sorted by peak probability desc.

        Connected-component extraction over all 40 (variable, lead) slices costs
        seconds, so the result is cached alongside the inference outputs.
        """
        cached = self._detections.get(run_id)
        if cached is not None:
            return cached

        result = self.get_result(run_id)
        from app.ml.masking import extract_blobs

        docs = []
        for v, variable in enumerate(VAR_CODES):
            for lead_time in range(1, T + 1):
                p = result.bust[lead_time - 1, v]
                conf = result.confidence[lead_time - 1]
                for idx, blob in enumerate(extract_blobs(p)):
                    docs.append(
                        self._detection_doc(run_id, variable, lead_time, idx, blob, p, conf)
                    )
        docs.sort(key=lambda d: d["peak_probability"], reverse=True)
        self._detections.put(run_id, docs)
        return docs

    def _detection_doc(self, run_id, variable, lead_time, idx, blob, p, conf) -> dict:
        rows, cols = bbox_to_slices(blob.bbox)
        window_p = p[rows, cols]
        window_conf = conf[rows, cols]
        # Mean confidence over the thresholded cells inside the blob's bounding
        # box. The box can clip a neighbouring component, so this is a
        # bbox-local approximation of the blob mean, not an exact blob mask.
        mask = window_p >= 0.5
        confidence = float(window_conf[mask].mean()) if mask.any() else float(window_conf.mean())

        # Cell-corner hulls can overshoot the cell-centre domain by DELTA/2; the
        # API contract is cell-centre bounds, so clamp before serializing.
        ring = clamp_ring(blob.polygon["coordinates"][0])
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]

        return {
            "detection_id": f"det-{run_id}-t{lead_time:02d}-{variable}-{idx:04d}",
            "run_id": run_id,
            "variable": variable,
            "lead_time": int(lead_time),
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "centroid": {
                "type": "Point",
                "coordinates": [
                    clamp_lon(sum(lons) / len(lons)),
                    clamp_lat(sum(lats) / len(lats)),
                ],
            },
            "bbox": clamp_bbox(blob.bbox),
            "peak_probability": float(np.clip(blob.peak_probability, 0.0, 1.0)),
            "mean_probability": float(np.clip(blob.mean_probability, 0.0, 1.0)),
            "area_km2": float(blob.area_km2),
            "n_cells": int(blob.n_cells),
            "dominant_driver": blob.dominant_driver,
            "confidence": float(np.clip(confidence, 0.0, 100.0)),
            "threshold": float(TAU[variable]),
            "is_regional_event": bool(float((window_p >= 0.5).mean()) > BF_CRIT),
            "created_at": utcnow(),
        }

    # -- XAI ---------------------------------------------------------------

    def attribution(self, run_id: str, variable: str, lead_time: int, lat: float, lon: float) -> dict:
        i, j = lat_index(lat), lon_index(lon)
        key = (run_id, variable, int(lead_time), i, j)
        cached = self._attributions.get(key)
        if cached is not None:
            return cached

        v = VAR_CODES.index(variable)
        t = int(lead_time) - 1

        import torch

        self.runner.ensure_inputs(run_id)
        X = np.load(self.runner.run_dir(run_id) / "X.npy").astype(np.float32)
        X = self.runner.normalize(X, norm_stats_path=self.runner.run_dir(run_id) / "norm_stats.json")
        X_t = torch.as_tensor(X)

        region = np.zeros((H, W), dtype=np.float32)
        r = ATTRIBUTION_REGION_RADIUS
        region[max(0, i - r) : min(H, i + r + 1), max(0, j - r) : min(W, j + r + 1)] = 1.0

        if self.runner.model is None:
            self.load_model()
        model = self.runner.model

        cam = gradcam(model, X_t, v=v, t=t, region_mask=region)
        drivers_raw = integrated_gradients(
            model, X_t, v=v, t=t, region_mask=region, n_steps=API_IG_STEPS
        )

        drivers = [
            {
                "channel_code": d["code"],
                "channel_name": CHANNEL_NAMES.get(d["code"], d["code"]),
                "score": float(np.clip(d["score"], 0.0, 1.0)),
                "sign": d["sign"],
            }
            for d in drivers_raw
        ]

        payload = {
            "run_id": run_id,
            "variable": variable,
            "lead_time": int(lead_time),
            "lat": float(lat_vector()[i]),
            "lon": float(lon_vector()[j]),
            "drivers": drivers,
            "spatial_gradcam": np.clip(to_north_up(cam), 0.0, 1.0).astype(float).tolist(),
            "narrative": narrative(
                int(lead_time),
                VAR_NAMES.get(variable, variable),
                f"{lat_vector()[i]:.2f}N/{lon_vector()[j]:.2f}E",
                drivers_raw,
            ),
        }
        self._attributions.put(key, payload)
        return payload

    # -- persistence --------------------------------------------------------

    def run_document(self, run_id: str) -> dict:
        result = self.get_result(run_id)
        now = utcnow()
        d = self.runner.run_dir(run_id)
        return {
            "run_id": run_id,
            "init_time": deterministic_init_time(run_id),
            "source_model": "SYNTHETIC",
            "n_lead_times": int(T),
            "grid": {
                "lat_min": float(lat_vector()[0]),
                "lat_max": float(lat_vector()[-1]),
                "lon_min": float(lon_vector()[0]),
                "lon_max": float(lon_vector()[-1]),
                "resolution": float(DELTA),
                "n_rows": int(H),
                "n_cols": int(W),
            },
            "variables": list(VAR_CODES),
            "norm_stats_ref": str((d / "norm_stats.json").as_posix()),
            "result_refs": {
                "confidence_uri": str((d / "confidence.npy").as_posix()),
                "bust_uri": str((d / "bust.npy").as_posix()),
                "error_uri": str((d / "error.npy").as_posix()),
            },
            "mean_confidence": float(np.clip(result.confidence.mean(), 0.0, 100.0)),
            "status": "COMPLETE",
            "created_at": now,
            "updated_at": now,
        }

    async def upsert_run(self, run_id: str) -> dict:
        doc = self.run_document(run_id)
        if self.db is not None:
            insert = dict(doc)
            created_at = insert.pop("created_at")
            await self.db["forecast_runs"].update_one(
                {"run_id": run_id},
                {"$set": insert, "$setOnInsert": {"created_at": created_at}},
                upsert=True,
            )
            stored = await self.db["forecast_runs"].find_one({"run_id": run_id})
            if stored is not None:
                return stored
        return doc

    async def persist_detections(self, run_id: str, limit: int = 200) -> int:
        """Upsert this run's detections (DB_SCHEMA 2). Returns the count written."""
        if self.db is None:
            return 0
        docs = self.detections(run_id)[:limit]
        written = 0
        for doc in docs:
            payload = dict(doc)
            created_at = payload.pop("created_at")
            await self.db["bust_detections"].update_one(
                {"detection_id": payload["detection_id"]},
                {"$set": payload, "$setOnInsert": {"created_at": created_at}},
                upsert=True,
            )
            written += 1
        return written

    async def log_telemetry(
        self,
        kind: str,
        severity: str,
        message: str,
        run_id: str | None = None,
        latency_ms: float | None = None,
        meta: dict | None = None,
    ) -> None:
        if self.db is None:
            return
        doc = {
            "event_id": f"evt-{uuid.uuid4()}",
            "kind": kind,
            "severity": severity,
            "run_id": run_id,
            "message": message,
            "latency_ms": float(latency_ms) if latency_ms is not None else None,
            "created_at": utcnow(),
        }
        if meta:
            doc["meta"] = meta
        try:
            await self.db["system_telemetry"].insert_one(doc)
        except Exception:
            # Telemetry is best-effort; never fail the request that produced it.
            return


def get_run_service(request: Request) -> RunService:
    """FastAPI dependency: the process-wide RunService built during lifespan."""
    return request.app.state.run_service
