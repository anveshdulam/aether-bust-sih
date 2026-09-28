# PRD.md — Product Requirements Document

**Project Codename:** `AETHER-BUST` (AI-Enhanced Temporal Heuristic Error Recognition — Forecast Bust Engine)
**SIH Problem Statement ID:** SIH26079
**Title:** AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts
**Owning Ministry:** Ministry of Earth Sciences (MoES), Government of India
**Document Version:** 1.0.0 (frozen contract — all sibling documents `TRD.md`, `UI_UX_DOC.md`, `DB_SCHEMA.md`, `BUILD_PLAN.md` MUST NOT deviate from constants defined here)
**Status:** AUTHORITATIVE SPECIFICATION — machine-executable, no placeholders permitted.

---

## 0. CANONICAL CONSTANTS (SINGLE SOURCE OF TRUTH)

Every downstream document references these identifiers verbatim. Any coding agent that emits a value contradicting this section MUST auto-repair to match this section.

### 0.1 Spatial Domain

| Symbol | Meaning | Value |
|--------|---------|-------|
| `PHI_MIN` | Minimum latitude (°N) | `6.0` |
| `PHI_MAX` | Maximum latitude (°N) | `37.75` |
| `LAMBDA_MIN` | Minimum longitude (°E) | `68.0` |
| `LAMBDA_MAX` | Maximum longitude (°E) | `99.75` |
| `DELTA` | Grid resolution (°) | `0.25` |
| `H` | Grid rows (latitude count) | `128` |
| `W` | Grid columns (longitude count) | `128` |

Grid cell indexing is deterministic:

```
lat(i)  = PHI_MIN    + DELTA * i      for i in [0, 127]   -> lat in [6.0, 37.75]
lon(j)  = LAMBDA_MIN + DELTA * j      for j in [0, 127]   -> lon in [68.0, 99.75]
```

Row `i = 0` is the SOUTHERNMOST latitude. Array storage is `[..., i (lat, south->north), j (lon, west->east)]`. All GeoJSON/GeoTIFF exports MUST flip row order to north-up (row 0 = 37.75°N) at the serialization boundary only; in-memory tensors remain south-up.

### 0.2 Temporal Domain (Lead Times)

| Symbol | Meaning | Value |
|--------|---------|-------|
| `T` | Number of lead times | `10` |
| Lead index `t` | Discrete lead index | `t in [0, 9]` → Day `t+1` |
| Cycle | Forecast initialization cycle | `00Z` (00:00 UTC) |
| Step | Temporal step | `+24h` |

Day `d` (1..10) maps to tensor lead index `t = d - 1`. Valid time of Day `d` = `init_time + d * 24h`.

### 0.3 Target Variables (V = 4)

The system detects busts for exactly four target variables. Ordering is FIXED and used as the channel axis in output tensors.

| Var idx | Code | Name | Unit | Source (Forecast) | Source (Truth) |
|---------|------|------|------|-------------------|----------------|
| `0` | `t2m` | 2 m Temperature | K | GFS/ECMWF | ERA5 |
| `1` | `tp` | Total Precipitation (24 h accumulated) | mm | GFS/ECMWF | ERA5 |
| `2` | `z500` | 500 hPa Geopotential Height | gpm | GFS/ECMWF | ERA5 |
| `3` | `ws850` | 850 hPa Wind Speed | m s⁻¹ | GFS/ECMWF | ERA5 |

### 0.4 Input Feature Channels (C = 10)

The model consumes 10 predictor channels per grid cell per lead time. Ordering is FIXED.

| Ch idx | Code | Name | Unit |
|--------|------|------|------|
| `0` | `t2m` | 2 m Temperature | K |
| `1` | `tp` | Total Precipitation (24 h) | mm |
| `2` | `z500` | 500 hPa Geopotential Height | gpm |
| `3` | `u850` | 850 hPa Zonal Wind | m s⁻¹ |
| `4` | `v850` | 850 hPa Meridional Wind | m s⁻¹ |
| `5` | `ws850` | 850 hPa Wind Speed = √(u850²+v850²) | m s⁻¹ |
| `6` | `cape` | Convective Available Potential Energy | J kg⁻¹ |
| `7` | `mslp` | Mean Sea Level Pressure | hPa |
| `8` | `z500_anom` | 500 hPa Geopotential Height Anomaly vs climatology | gpm |
| `9` | `shear_850_250` | Deep-layer bulk wind shear (250 hPa − 850 hPa) | m s⁻¹ |

### 0.5 Tensor Contract (referenced by TRD.md §2)

```
INPUT  X : float32  shape = [B, T=10, C=10, H=128, W=128]
BUST   Yb: float32  shape = [B, T=10, V=4,  H=128, W=128]   # probabilities in [0,1]
ERROR  Ye: float32  shape = [B, T=10, V=4,  H=128, W=128]   # expected |error| in native units
CONF   Yc: float32  shape = [B, T=10,        H=128, W=128]   # confidence index in [0,100]
```

### 0.6 Bust Thresholds `τ_v` (absolute error thresholds)

| Var | Symbol | Threshold `τ_v` | Rationale |
|-----|--------|-----------------|-----------|
| `t2m` | `TAU_T2M` | `3.0` K | Operational surface-temp forecast tolerance for MR range |
| `tp` | `TAU_TP` | `20.0` mm/24h | Heavy-rain categorical boundary (IMD ">64.5mm=heavy" softened for grid-mean error) |
| `z500` | `TAU_Z500` | `60.0` gpm | ≈ synoptic-scale ridge/trough displacement error |
| `ws850` | `TAU_WS850` | `5.0` m s⁻¹ | ≈ one Beaufort category at LLJ level |

### 0.7 Confidence Weights `w_v` (Σ = 1.0)

| Var | Weight |
|-----|--------|
| `t2m` | `0.25` |
| `tp` | `0.35` |
| `z500` | `0.25` |
| `ws850` | `0.15` |

---

## 1. PRODUCT OVERVIEW

### 1.1 Problem Framing

Medium-range NWP models (GFS, ECMWF IFS) degrade non-uniformly across space and lead time. A "forecast bust" is a **localized, lead-time-dependent event where the deterministic NWP forecast error for a variable exceeds an operationally significant threshold.** Operational forecasters at MoES/IMD currently detect busts *post-hoc*. AETHER-BUST predicts, *at forecast issuance time*, **where** and **when** (Day 1–10) a bust is likely, quantifies **how confident** the forecast is per grid cell, and **explains which meteorological drivers** are responsible.

### 1.2 Product Pillars

1. **Confidence Scoring Engine** — 0–100% standardized confidence per grid cell per lead time.
2. **Spatiotemporal Bust Risk Heatmap** — `P(bust)` field, per variable, Day 1–10.
3. **Meteorological Anomaly Attribution (XAI)** — driver ranking per flagged region.
4. **Operational Alerts & Export Engine** — GeoJSON, GeoTIFF, NetCDF export + threshold alerts.
5. **Interactive Operational Dashboard + REST API** — 3-column ops console (see `UI_UX_DOC.md`).

### 1.3 Non-Goals (v1.0)

- The system does NOT re-train NWP models nor produce its own weather forecast.
- The system does NOT ingest live GFS/ECMWF GRIB in v1.0; it operates on the synthetic data generator (`BUILD_PLAN.md` Phase 1) and an ERA5-schema-compatible ingest adapter stub. Real ingest is a documented seam, not implemented.
- No user authentication/RBAC in v1.0 (single-tenant ops console).

---

## 2. MATHEMATICAL FORMULATION OF A "FORECAST BUST"

### 2.1 Pointwise Error

For target variable `v ∈ {t2m, tp, z500, ws850}`, grid cell `(i,j)`, lead time `t`, forecast field `F` and ERA5 ground-truth analysis `A` (both interpolated to the canonical 0.25° grid of §0.1):

```
Pointwise absolute error:   e_v(t,i,j) = | F_v(t,i,j) − A_v(t,i,j) |
Pointwise signed error:     δ_v(t,i,j) =   F_v(t,i,j) − A_v(t,i,j)
```

For `tp`, `F` and `A` are the 24-hour accumulations valid over `(init + t·24h, init + (t+1)·24h]`.

### 2.2 Binary Bust Indicator

```
B_v(t,i,j) = 1   if  e_v(t,i,j) > τ_v
           = 0   otherwise
```

with `τ_v` from §0.6.

### 2.3 Aggregate Skill Metrics (per variable, per lead time, over a region R)

Let `R` be a set of `N_R` grid cells (whole domain, admin region, or a bbox).

```
RMSE_v(t, R) = sqrt( (1/N_R) * Σ_{(i,j)∈R} δ_v(t,i,j)^2 )

MAE_v(t, R)  = (1/N_R) * Σ_{(i,j)∈R} e_v(t,i,j)

Bust Frequency:
BF_v(t, R)   = (1/N_R) * Σ_{(i,j)∈R} B_v(t,i,j)          # in [0,1]
```

### 2.4 Region-Level Bust Event (for alerting)

A **regional bust event** is declared for `(v, t, R)` when EITHER aggregate condition holds:

```
BUST_EVENT(v,t,R) = 1  iff  ( RMSE_v(t,R) > τ_v )  OR  ( BF_v(t,R) > BF_CRIT )
BF_CRIT = 0.30       # >30% of cells in region individually bust
```

### 2.5 Categorical (Event-Based) Bust for Precipitation

Because precipitation error is heavy-tailed, `tp` additionally uses a 2×2 contingency-derived bust. Define event threshold `TP_EVENT = 20.0 mm/24h` (heavy-rain proxy). Per cell:

```
hit   : F_tp ≥ TP_EVENT  and  A_tp ≥ TP_EVENT
miss  : F_tp <  TP_EVENT  and  A_tp ≥ TP_EVENT
false : F_tp ≥ TP_EVENT  and  A_tp <  TP_EVENT
corr  : F_tp <  TP_EVENT  and  A_tp <  TP_EVENT

Categorical bust indicator:  B_tp_cat(t,i,j) = 1 if (miss OR false), else 0
```

The model's `tp` bust probability head is trained on `B_tp = max(B_tp_magnitude, B_tp_cat)`. The other three variables use magnitude-only `B_v` from §2.2.

### 2.6 Standardized Confidence Index (Pillar 1)

The confidence index `C(t,i,j) ∈ [0,100]` fuses per-variable predicted bust probabilities `p_v = Yb_v(t,i,j)` from the ML model (§0.5):

```
C(t,i,j) = 100 * ( 1 − Σ_{v} w_v * p_v(t,i,j) )     # w_v from §0.7, Σ w_v = 1
```

`C` is clamped to `[0,100]`. Confidence bands (used by `UI_UX_DOC.md` color scale):

| Band | Range | Semantics |
|------|-------|-----------|
| `VERY_HIGH` | `[85,100]` | Trust forecast |
| `HIGH` | `[70,85)` | Minor caveat |
| `MODERATE` | `[50,70)` | Use with caution |
| `LOW` | `[30,50)` | Elevated bust risk |
| `VERY_LOW` | `[0,30)` | High bust risk — manual review |

### 2.7 Ground-Truth Label Generation (offline, for training)

For every historical `(init_date, v, t, i, j)` triplet the training pipeline computes `B_v` (§2.2/§2.5) and `e_v`, producing supervised targets `(Yb*, Ye*)`. The synthetic generator (`BUILD_PLAN.md` Phase 1) MUST emit these labels with the identical formulas.

---

## 3. CORE FEATURE SPECIFICATIONS

### 3.1 Feature F1 — Day 1–10 Confidence Scoring Engine

- **Input:** one `forecast_run` (init cycle) → tensor `X : [1,10,10,128,128]`.
- **Output:** `Yc : [10,128,128]` confidence index (§2.6) + per-variable `Yb`.
- **Standardization:** confidence is unit-free 0–100; identical scale across variables and lead times, enabling cross-lead comparison.
- **API:** `GET /api/v1/confidence-map?run_id=&lead_time=` (see `TRD.md` §5).
- **Acceptance:**
  - AC-F1-1: Output shape exactly `[10,128,128]`; dtype float32; all values ∈ [0,100].
  - AC-F1-2: `C` is monotonically non-increasing on average with lead time over the whole domain: `mean(C[t]) ≥ mean(C[t+1]) − 5` (soft, tolerance 5 pts; enforced as a data-sanity test on synthetic data).
  - AC-F1-3: Deterministic — identical input yields bit-identical output (model in `eval()`, seeds fixed).

### 3.2 Feature F2 — Spatiotemporal Bust Risk Heatmap

- **Output:** `Yb : [10,4,128,128]` per-variable bust probabilities.
- **Derived layer:** aggregate bust risk `P_agg(t,i,j) = Σ_v w_v * p_v(t,i,j)` (= `1 − C/100`).
- **API:** `POST /api/v1/bust-probability` (body selects variable(s), lead range, bbox).
- **Acceptance:**
  - AC-F2-1: Probabilities ∈ [0,1]; shape `[10,4,128,128]`.
  - AC-F2-2: `bust_detections` documents persisted for cells where `p_v > 0.5` (see `DB_SCHEMA.md`).

### 3.3 Feature F3 — Meteorological Anomaly Attribution Module (XAI)

- **Method:** Grad-CAM over the ConvLSTM/U-Net feature maps + SHAP (GradientExplainer/Captum IntegratedGradients) attributing output `p_v(t, region)` to the 10 input channels (§0.4). See `TRD.md` §4.
- **Output:** per flagged region, a ranked list of `(channel_code, attribution_score, sign)` where drivers include `z500_anom`, `shear_850_250`, `cape`, etc.
- **Human-readable narrative:** deterministic template rendering (see §3.3.1).
- **API:** `GET /api/v1/attribution?run_id=&lead_time=&lat=&lon=`.
- **Acceptance:**
  - AC-F3-1: Returns exactly 10 attribution entries (one per input channel), sorted by `|attribution_score|` desc.
  - AC-F3-2: Σ of normalized attribution magnitudes = 1.0 ± 1e-6 (attributions L1-normalized for display).
  - AC-F3-3: Grad-CAM spatial map shape `[128,128]`, values ∈ [0,1].

#### 3.3.1 Deterministic XAI Narrative Template

```
"Day {d} bust risk for {var_name} over {region_label} is driven primarily by
{driver_1_name} ({driver_1_pct}%, {driver_1_sign}) and {driver_2_name}
({driver_2_pct}%, {driver_2_sign}). {synoptic_clause}."
```

`synoptic_clause` is selected by rule table (deterministic): if top driver is `z500_anom` and sign positive → "A reinforced mid-tropospheric ridge is increasing model spread."; if `cape` → "Elevated convective instability raises precipitation-timing uncertainty."; if `shear_850_250` → "Strong deep-layer shear is associated with rapid synoptic evolution."; default → "Anomalous large-scale flow is elevating model uncertainty."

### 3.4 Feature F4 — Operational Alerts & Export Engine

- **Alerts:** when `BUST_EVENT(v,t,R)=1` (§2.4) for any admin region, emit alert record → `bust_detections` + `system_telemetry` alert log.
- **Exports (Pillar 4):**
  | Format | Payload | Endpoint param |
  |--------|---------|----------------|
  | GeoJSON | Bust polygons (contoured `p_v ≥ 0.5`) with properties | `format=geojson` |
  | GeoTIFF | Single-band raster of `p_v` or `C`, EPSG:4326, 128×128, north-up | `format=geotiff` |
  | NetCDF | CF-1.10 compliant, dims `(lead_time, lat, lon)`, var-per-target | `format=netcdf` |
- **API:** `GET /api/v1/export?run_id=&lead_time=&variable=&layer=&format=`.
- **Acceptance:**
  - AC-F4-1: GeoJSON validates against RFC 7946; every feature has `properties.p_bust`, `properties.variable`, `properties.lead_time`, `properties.confidence`.
  - AC-F4-2: GeoTIFF opens in `rasterio` with CRS EPSG:4326 and correct geotransform (origin top-left = 37.75°N/68.0°E, pixel 0.25°).
  - AC-F4-3: NetCDF opens in `xarray`, dims `(lead_time=10, lat=128, lon=128)`, passes CF attribute check for `units`, `standard_name`, `_FillValue`.

### 3.5 Feature F5 — Bounding / Masking of Error-Prone Areas

- **Method:** threshold `P_agg ≥ 0.5` → binary mask → connected-component labeling (`scipy.ndimage.label`, 8-connectivity) → minimum bounding boxes + convex-hull polygons per component ≥ `MIN_BLOB_CELLS = 9` cells.
- **Output:** list of `{bbox:[lon_min,lat_min,lon_max,lat_max], polygon, peak_p, mean_p, area_km2, dominant_driver}`.
- **API:** surfaced via `GET /api/v1/bust-detections`.
- **Acceptance:** AC-F5-1: components smaller than `MIN_BLOB_CELLS` are discarded; each returned bbox fully contains its polygon.

---

## 4. USER STORIES & OPERATIONAL REQUIREMENTS

| ID | As a… | I want… | So that… | Priority |
|----|-------|---------|----------|----------|
| US-1 | MoES duty forecaster | a Day 1–10 confidence map | I know which lead times to trust | P0 |
| US-2 | duty forecaster | bust probability per variable overlaid on the map | I can warn downstream users | P0 |
| US-3 | senior meteorologist | XAI driver breakdown for a flagged region | I can justify a manual override | P0 |
| US-4 | GIS analyst | GeoTIFF/NetCDF export | I can ingest into my own tooling | P1 |
| US-5 | ops manager | threshold-based alerts | I get paged on high-risk busts | P1 |
| US-6 | evaluator | reproducible, deterministic outputs | I can score the system fairly | P0 |

**Operational NFRs**

| NFR | Requirement |
|-----|-------------|
| Inference latency | ≤ 2.0 s per forecast run (10×10×128×128) on CPU; ≤ 300 ms on GPU |
| API p95 latency | ≤ 400 ms for map/attribution reads (cached tensors) |
| Determinism | Fixed seeds; `torch.use_deterministic_algorithms(True)` |
| Reproducibility | All constants in §0; no wall-clock-dependent logic in inference |
| Data volume | One run ≈ 10×4×128×128 float32 ≈ 2.6 MB per output field |

---

## 5. SIH EVALUATOR CRITERIA (MoES) — SCORING STRATEGY

The submission is optimized against the following evaluation axes. Each maps to concrete, demonstrable evidence.

| Axis | Weight (indicative) | Evidence produced by AETHER-BUST |
|------|---------------------|----------------------------------|
| **Meteorological correctness** | 25% | Formal bust math (§2), ERA5-truth alignment, CF-compliant exports, physically-named drivers (z500 anomaly, 850 hPa shear, CAPE). |
| **AI/ML rigor** | 20% | ConvLSTM+U-Net+Temporal-Attention (`TRD.md` §2), multi-task loss, strict tensor contract, verified shape tests. |
| **Explainability (XAI)** | 15% | Grad-CAM + SHAP per-driver attribution with deterministic narrative (§3.3). |
| **Skill quantification** | 15% | RMSE/MAE/Bust-Frequency + reliability diagram + Brier score (§5.1). |
| **Operational usability** | 15% | 3-column ops dashboard, Day 1–10 scrubber, alerts, exports (`UI_UX_DOC.md`). |
| **Engineering quality** | 10% | Deterministic build plan, automated verification per phase, Dockerized full stack (`BUILD_PLAN.md`). |

### 5.1 Quantitative Metrics Reported on the Dashboard "Model Skill" tab

For each variable and lead time, over the demo period, compute and display:

```
Brier Score (bust classifier):
BS_v(t) = (1/N) Σ ( p_v(t,i,j) − B*_v(t,i,j) )^2                # lower better

Reliability (calibration): binned mean predicted p vs observed bust frequency (10 bins).

ROC-AUC_v(t): area under ROC of p_v vs B*_v.

Continuous error skill (regression head):
MAE_reg_v(t) = mean | Ye_v(t,i,j) − e*_v(t,i,j) |

RMSE_v(t), MAE_v(t), BF_v(t): as §2.3, forecast vs truth.
```

### 5.2 Winning Differentiators (explicit talking points)

1. **Standardized cross-variable confidence index** (single 0–100 scale) — unusual and evaluator-legible.
2. **Physically-grounded XAI** naming exact meteorological drivers, not opaque saliency.
3. **CF-compliant tri-format export** (GeoJSON/GeoTIFF/NetCDF) — production integration ready.
4. **Deterministic, verifiable build** — every phase gated by an exit-code-0 check.

---

## 6. ACCEPTANCE MATRIX (TRACEABILITY)

| Feature | Acceptance IDs | Verified in `BUILD_PLAN.md` Phase |
|---------|----------------|-----------------------------------|
| F1 Confidence | AC-F1-1..3 | Phase 2 (`test_confidence.py`) |
| F2 Heatmap | AC-F2-1..2 | Phase 2 + Phase 3 |
| F3 XAI | AC-F3-1..3 | Phase 2 (`test_xai.py`) |
| F4 Export | AC-F4-1..3 | Phase 3 (`test_export.py`) |
| F5 Masking | AC-F5-1 | Phase 2 (`test_masking.py`) |
| API | endpoints §5 of TRD | Phase 3 (`test_api.py`) |
| Dashboard | US-1..3 | Phase 4/5 (`npm run build`, Playwright smoke) |
| E2E | all | Phase 6 (`smoke_e2e.sh`) |

---

## 7. GLOSSARY

- **Bust:** forecast error exceeding `τ_v` (§0.6) for a variable at a location/lead.
- **Lead time:** forecast horizon in days (Day 1..10).
- **ERA5:** ECMWF Reanalysis v5 — treated as ground truth `A`.
- **Confidence index:** standardized 0–100 trust score (§2.6).
- **Attribution:** XAI-derived contribution of an input channel to a bust prediction.
- **Regional bust event:** aggregate-level bust trigger for alerting (§2.4).

*End of PRD.md — constants in §0 are binding on all sibling documents.*
