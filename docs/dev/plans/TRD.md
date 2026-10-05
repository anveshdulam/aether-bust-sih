# TRD.md — Technical Requirements Document

**Project:** AETHER-BUST (SIH26079)
**Binds to:** `PRD.md` §0 (canonical constants). All tensor shapes, variable orders, thresholds, and grid definitions are inherited verbatim from `PRD.md` §0 and MUST NOT be redefined with different values.
**Document Version:** 1.0.0

---

## 1. TECH STACK & VERSION LOCKING

All versions are pinned. The autonomous agent MUST NOT introduce a dependency absent from these tables (`BUILD_PLAN.md` §1 FORBIDDEN ACTIONS).

### 1.1 Backend (Python)

| Package | Locked Version | Purpose |
|---------|----------------|---------|
| `python` | `3.11.9` | Runtime (interpreter) |
| `fastapi` | `0.111.0` | REST API framework |
| `uvicorn[standard]` | `0.30.1` | ASGI server |
| `pydantic` | `2.7.4` | Validation / schemas (v2) |
| `pydantic-settings` | `2.3.4` | Env config |
| `torch` | `2.3.1` | Deep learning |
| `numpy` | `1.26.4` | Arrays |
| `scipy` | `1.13.1` | `ndimage` labeling, interpolation |
| `xarray` | `2024.6.0` | NetCDF I/O, labeled arrays |
| `netCDF4` | `1.6.5` | NetCDF backend |
| `rasterio` | `1.3.10` | GeoTIFF export |
| `shapely` | `2.0.4` | Polygon geometry (masking) |
| `pyproj` | `3.6.1` | CRS handling |
| `Cartopy` | `0.23.0` | Map projection (server-side static renders only) |
| `shap` | `0.45.1` | SHAP attribution |
| `captum` | `0.7.0` | IntegratedGradients / Grad-CAM |
| `motor` | `3.4.0` | Async MongoDB driver |
| `pymongo` | `4.7.3` | (transitive, pinned) |
| `python-multipart` | `0.0.9` | Form/file endpoints |
| `orjson` | `3.10.5` | Fast JSON responses |
| `pytest` | `8.2.2` | Test runner |
| `pytest-asyncio` | `0.23.7` | Async tests |
| `httpx` | `0.27.0` | Test client / async HTTP |

### 1.2 Frontend (Node)

| Package | Locked Version | Purpose |
|---------|----------------|---------|
| `node` | `20.14.0 LTS` | Runtime |
| `react` | `18.3.1` | UI |
| `react-dom` | `18.3.1` | DOM renderer |
| `vite` | `5.3.1` | Build tool / dev server |
| `@vitejs/plugin-react` | `4.3.1` | React plugin |
| `tailwindcss` | `3.4.4` | Styling |
| `postcss` | `8.4.38` | CSS pipeline |
| `autoprefixer` | `10.4.19` | CSS prefixing |
| `leaflet` | `1.9.4` | Base map |
| `react-leaflet` | `4.2.1` | React bindings for Leaflet |
| `deck.gl` | `9.0.20` | GPU heatmap / grid overlays |
| `@deck.gl/leaflet` | `9.0.20` | deck.gl ↔ Leaflet bridge |
| `recharts` | `2.12.7` | Attribution bar / reliability charts |
| `zustand` | `4.5.2` | Client state store |
| `@tanstack/react-query` | `5.45.1` | Server-state / caching |
| `axios` | `1.7.2` | HTTP client |
| `d3-scale` | `4.0.2` | Color scale interpolation |
| `d3-scale-chromatic` | `3.1.0` | (optional ramps; WMO ramps hard-coded per UI_UX_DOC) |
| `@playwright/test` | `1.45.0` | E2E smoke tests |

### 1.3 Infrastructure

| Component | Locked Version |
|-----------|----------------|
| `mongodb` | `7.0.11` (official image `mongo:7.0.11`) |
| `docker` | `≥ 24.0` |
| `docker compose` | `v2` spec |
| `nginx` (frontend serve) | `1.27-alpine` |

### 1.4 Repository Layout (absolute paths relative to project root `./`)

```
./
├── PRD.md TRD.md UI_UX_DOC.md DB_SCHEMA.md BUILD_PLAN.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app factory
│   │   ├── config.py              # pydantic-settings
│   │   ├── constants.py           # PRD §0 constants (SSOT in code)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # motor async client
│   │   │   └── indexes.py         # index creation
│   │   ├── models/                # pydantic v2 schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── forecast.py
│   │   │   ├── bust.py
│   │   │   ├── attribution.py
│   │   │   └── telemetry.py
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── architecture.py    # ConvLSTM + U-Net + TemporalAttention
│   │   │   ├── loss.py            # MultiTaskBustLoss
│   │   │   ├── inference.py       # InferenceRunner
│   │   │   ├── xai.py             # GradCAM + SHAP wrappers
│   │   │   ├── masking.py         # connected-component bounding
│   │   │   └── confidence.py      # confidence index (PRD §2.6)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── export_service.py  # geojson/geotiff/netcdf
│   │   │   └── run_service.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── forecast_runs.py
│   │       ├── confidence.py
│   │       ├── bust.py
│   │       ├── attribution.py
│   │       ├── export.py
│   │       └── telemetry.py
│   ├── data/
│   │   └── generator.py           # synthetic NetCDF/NumPy generator (Phase 1)
│   └── tests/
│       ├── conftest.py
│       ├── test_shapes.py
│       ├── test_generator.py
│       ├── test_model.py
│       ├── test_loss.py
│       ├── test_confidence.py
│       ├── test_masking.py
│       ├── test_xai.py
│       ├── test_export.py
│       └── test_api.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── tsconfig.json
│   ├── src/ (see UI_UX_DOC.md §6 component tree)
│   └── e2e/
│       └── smoke.spec.ts
└── scripts/
    ├── seed_mongo.py
    ├── smoke_e2e.sh
    └── healthcheck.sh
```

---

## 2. AI/ML MODEL SPECIFICATION

### 2.1 Architecture Overview — `BustNet`

`BustNet` is a spatiotemporal encoder–decoder:

```
X [B,10,10,128,128]
   │
   ├─ (per-timestep) U-Net Spatial Encoder  →  multi-scale spatial features
   │        E_t ∈ R[B, 256, 8, 8]  (bottleneck) + skip connections s1,s2,s3,s4
   │
   ├─ ConvLSTM over T=10 bottleneck features  →  H_t ∈ R[B,256,8,8] per t
   │
   ├─ Temporal Self-Attention across {H_0..H_9}  →  A_t ∈ R[B,256,8,8]
   │
   └─ U-Net Spatial Decoder (per t, with skips) →  D_t ∈ R[B,64,128,128]
            │
            ├─ Bust Head   (1×1 conv, 4 ch, sigmoid)  → Yb [B,10,4,128,128]
            └─ Error Head  (1×1 conv, 4 ch, softplus) → Ye [B,10,4,128,128]
```

Confidence `Yc` is a **deterministic post-process** (PRD §2.6), NOT a learned head.

### 2.2 Strict Input Tensor Contract

```
INPUT   X  : torch.float32  [B, T, C, H, W] = [B, 10, 10, 128, 128]
OUTPUT  Yb : torch.float32  [B, 10, 4, 128, 128]   values ∈ (0,1) via sigmoid
OUTPUT  Ye : torch.float32  [B, 10, 4, 128, 128]   values ≥ 0   via softplus
```

`BustNet.forward(x)` returns `dict(bust=Yb, error=Ye)`. Any tensor whose shape violates this contract MUST raise `ShapeContractError` (custom exception) at the layer boundary — never silently reshape. `test_shapes.py` asserts these exact shapes and is a GATE (`BUILD_PLAN.md` §1).

#### 2.2.1 Normalization Contract

Each channel `c` is standardized with fixed per-channel statistics stored in `backend/app/ml/norm_stats.json` (produced by the Phase-1 generator over the synthetic corpus):

```
X_norm[...,c,...] = ( X[...,c,...] − MU[c] ) / SIGMA[c]
```

`MU`, `SIGMA` are length-10 float32 vectors. Precipitation channel `tp` (idx 1) is first log1p-transformed: `X_tp := log1p(max(X_tp,0))` BEFORE standardization. Error-head targets are in native (de-normalized) units.

### 2.3 Layer Specifications

#### 2.3.1 U-Net Spatial Encoder (shared weights across timesteps)

Applied independently to each `X[:,t]` (`[B,10,128,128]`):

| Block | Op | Out shape `[B,·,·,·]` |
|-------|----|------------------------|
| stem | Conv3×3(10→64), GN(8,64), SiLU ×2 | `[B,64,128,128]` = skip `s1` |
| down1 | MaxPool2 → Conv×2(64→128) | `[B,128,64,64]` = `s2` |
| down2 | MaxPool2 → Conv×2(128→256) | `[B,256,32,32]` = `s3` |
| down3 | MaxPool2 → Conv×2(256→256) | `[B,256,16,16]` = `s4` |
| down4 | MaxPool2 → Conv×2(256→256) | `[B,256,8,8]` = bottleneck `E_t` |

`Conv×2` = two (Conv3×3, GroupNorm(num_groups=8), SiLU) blocks, padding=1. Normalization is `GroupNorm` (batch-size independent → deterministic small-batch inference).

#### 2.3.2 ConvLSTM (temporal recurrence at bottleneck)

- Cell: standard ConvLSTM (Shi et al. 2015), kernel 3×3, `input_dim=256`, `hidden_dim=256`, `padding=1`.
- Processes `E_0..E_9` (each `[B,256,8,8]`) → hidden states `H_0..H_9` (each `[B,256,8,8]`).
- Single layer, single direction (causal — Day n cannot use Day n+1 features).
- Hidden/cell state initialized to zeros.

#### 2.3.3 Temporal Self-Attention

- Reshape `{H_t}` → sequence `[B, T=10, 256*8*8]` → linear project to `d_model=256` tokens per timestep via a `Conv1×1` pooling: actually spatial dims are kept; attention operates over the **temporal** axis for each spatial location independently.
- Implementation: flatten spatial → tokens `[B, 8*8=64, T=10, 256]`; apply `nn.MultiheadAttention(embed_dim=256, num_heads=8, batch_first=True)` along `T` for each of 64 spatial locations (vectorized as batch `B*64`).
- Query=Key=Value = `H` sequence. Additive **causal mask** so lead `t` attends only to `≤ t` (medium-range physical causality).
- Output `A_t` reshaped back to `[B,256,8,8]` per t. Residual: `A_t := A_t + H_t`; LayerNorm over channel dim.

#### 2.3.4 U-Net Spatial Decoder (shared weights across timesteps)

Applied per timestep to `A_t`, using the SAME-timestep encoder skips `s1..s4`:

| Block | Op | Out shape |
|-------|----|-----------|
| up4 | ConvTranspose2(256→256) ⊕ s4, Conv×2 | `[B,256,16,16]` |
| up3 | ConvTranspose2(256→256) ⊕ s3, Conv×2 | `[B,256,32,32]` |
| up2 | ConvTranspose2(256→128) ⊕ s2, Conv×2 | `[B,128,64,64]` |
| up1 | ConvTranspose2(128→64)  ⊕ s1, Conv×2 | `[B,64,128,128]` = `D_t` |

`⊕` = channel concatenation with the skip, followed by a 1×1 conv to restore channel count.

#### 2.3.5 Output Heads

```
Bust  head : Conv1×1(64 → 4);  activation = sigmoid   → Yb_t [B,4,128,128]
Error head : Conv1×1(64 → 4);  activation = softplus  → Ye_t [B,4,128,128]
```

Stack over `t` → `[B,10,4,128,128]`.

#### 2.3.6 Parameter Budget

Target ≈ 12–18 M parameters (fits CPU inference NFR, PRD §4). `test_model.py` asserts `1e6 < n_params < 3e7`.

### 2.4 Loss Function — `MultiTaskBustLoss`

Multi-task weighted loss balancing classification (bust occurrence) and regression (error magnitude):

```
Given predictions (Yb, Ye) and targets (Yb*, Ye*) with valid mask M (all ones on synthetic data):

# 1. Bust classification — Focal-weighted BCE (class imbalance: busts are rare)
L_cls = mean_over_valid( α_t * (1 − p_t)^γ * BCE(Yb, Yb*) )
        where p_t = Yb if Yb*=1 else (1−Yb);  γ = 2.0 (focal);  α = 0.75 (bust class weight)

# 2. Error regression — masked MAE, computed ONLY where Yb*=1 (busts) with a
#    down-weighted term elsewhere to stabilize:
L_reg = λ_hit * MAE(Ye, Ye* | Yb*=1) + λ_all * MAE(Ye, Ye* | all)

# 3. Per-variable reweighting using PRD §0.7 confidence weights w_v (broadcast over V axis)
L_cls_w = Σ_v w_v * L_cls_v ;   L_reg_w = Σ_v w_v * L_reg_v

# Total
L = β_cls * L_cls_w + β_reg * L_reg_w
```

**Fixed coefficients:** `γ=2.0`, `α=0.75`, `λ_hit=1.0`, `λ_all=0.1`, `β_cls=1.0`, `β_reg=0.5`. Error targets normalized by `τ_v` inside `L_reg` so scales are comparable: `Ye*/τ_v`, `Ye/τ_v`.

`test_loss.py` asserts: (a) loss is a scalar `>0`; (b) gradient flows to all parameters (no `None` grads); (c) `L=0` in the degenerate case `Yb=Yb*` and `Ye=Ye*`.

### 2.5 Explainability Subsystem

Two complementary methods, both operating on the strict tensor contract:

#### 2.5.1 Grad-CAM (spatial "where")

- Target layer: last decoder block `D_t` (before heads), i.e. `[B,64,128,128]`.
- For a chosen `(variable v, lead t)`, backprop the scalar `mean(Yb[:,t,v])` (or region-masked mean) to `D_t`; weight channels by global-average-pooled gradients; ReLU; upsample to 128×128; min-max normalize → `cam ∈ [0,1]^{128×128}`.
- Output consumed by dashboard XAI overlay and `attribution` API `spatial_gradcam`.

#### 2.5.2 SHAP / Integrated Gradients (channel "why")

- `captum.attr.IntegratedGradients` on a wrapper `f(X) = mean_region( Yb[:,t,v] )`.
- Baseline = per-channel climatological mean field (`MU` broadcast).
- Attribution tensor `[10 channels, 128, 128]`; reduce to per-channel scalar by summing absolute attribution over the target region → `attr[c]`.
- L1-normalize `attr` → `attr_norm` (Σ=1.0, PRD AC-F3-2). Sign from summed signed attribution.
- Maps channel index → meteorological driver name (PRD §0.4): `z500_anom`, `shear_850_250`, `cape`, etc.

`test_xai.py` asserts: cam shape `[128,128]`∈[0,1]; exactly 10 channel attributions; `abs(sum(attr_norm)-1.0) < 1e-6`.

### 2.6 Inference Runner

`backend/app/ml/inference.py :: InferenceRunner`

```
class InferenceRunner:
    load(weights_path | None)        # if None → deterministic randomly-seeded weights (demo mode)
    warmup()                         # run a [1,10,10,128,128] dummy pass; set eval(); no_grad
    run(run_id) -> InferenceResult   # loads X for run_id (from generator/store), returns:
        bust:  np.float32 [10,4,128,128]
        error: np.float32 [10,4,128,128]
        confidence: np.float32 [10,128,128]     # PRD §2.6
        blobs: list[BustBlob]                    # masking.py output (PRD §3.5)
```

Determinism block executed at import: `torch.manual_seed(SEED=26079)`, `torch.use_deterministic_algorithms(True)`, `os.environ["CUBLAS_WORKSPACE_CONFIG"]=":4096:8"`, single-thread option for reproducibility in CI.

---

## 3. DATA PIPELINE CONTRACT

### 3.1 Synthetic Generator (Phase 1) — `backend/data/generator.py`

Produces physically-plausible fields on the canonical grid (PRD §0.1) so downstream tensor bugs surface before real GRIB ingest.

- **Base fields:** smooth spatial structure via low-wavenumber 2-D sinusoids + Perlin-like fractal noise (numpy-only, seeded), added to per-variable climatological means.
- **Lead-time degradation:** forecast error variance grows with `t`: `σ_err(t) = σ0_v * (1 + κ * t)`, `κ = 0.18`. Truth `A` = base; forecast `F` = `A` + correlated error field scaled by `σ_err(t)`.
- **Bust injection:** randomly place `N_blobs = 3..6` Gaussian error "blobs" per run at higher lead times to guarantee positive bust labels; each blob amplitude ≥ `1.5 * τ_v`.
- **Physical coupling:** high `cape` + high `shear_850_250` regions are correlated with injected `tp` and `ws850` busts (so XAI attributions are physically sensible).
- **Outputs per run:**
  - `X.npy` — `[1,10,10,128,128]` float32 (forecast predictors)
  - `Yb_true.npy` — `[10,4,128,128]` (from PRD §2.2/§2.5)
  - `Ye_true.npy` — `[10,4,128,128]`
  - `run.nc` — xarray dataset, CF-1.10, dims `(lead_time,lat,lon)` for each variable (both F and A groups)
  - `norm_stats.json` — `{MU:[…10…], SIGMA:[…10…]}`

`test_generator.py` asserts exact shapes, dtype float32, no NaN/Inf, and `Yb_true` has ≥ 1 positive cell.

### 3.2 Real-Data Ingest Seam (documented, not implemented in v1.0)

An adapter interface `IngestAdapter.load(init_date) -> X, meta` is specified; a `SyntheticAdapter` implements it in v1.0. A future `GfsEra5Adapter` would regrid GRIB→0.25° via `xarray`+`scipy` and populate identical tensors. No live download code is written in v1.0.

---

## 4. XAI IMPLEMENTATION CONTRACT (summary; math in PRD §3.3)

| Artifact | Producer | Shape / form | API surface |
|----------|----------|--------------|-------------|
| `spatial_gradcam` | `xai.gradcam(v,t,region)` | `[128,128]` ∈ [0,1] | `attribution.spatial_gradcam` |
| `channel_attributions` | `xai.integrated_gradients(v,t,region)` | 10 × `{code,score,sign}` sorted | `attribution.drivers` |
| `narrative` | `xai.narrative(...)` | string (PRD §3.3.1 template) | `attribution.narrative` |

---

## 5. HIGH-PERFORMANCE API CONTRACT

### 5.1 Conventions

- Base path: `/api/v1`. JSON via `ORJSONResponse`. All datetimes ISO-8601 UTC (`Z`).
- Errors: RFC 9457 Problem Details (`application/problem+json`) with `type,title,status,detail,instance`.
- CORS: allow `http://localhost:5173` (dev) + configured origin.
- All responses validated by Pydantic v2 `response_model`. `ConfigDict(extra="forbid")` on request bodies.

### 5.2 Endpoint Catalogue

| Method | Path | Purpose | Response model |
|--------|------|---------|----------------|
| GET | `/health` | Liveness + dependency check | `HealthResponse` |
| GET | `/api/v1/forecast-runs` | List runs (paginated) | `Page[ForecastRunSummary]` |
| GET | `/api/v1/forecast-runs/{run_id}` | Run detail | `ForecastRunDetail` |
| GET | `/api/v1/confidence-map` | Confidence field for `run_id`,`lead_time` | `ConfidenceMapResponse` |
| POST | `/api/v1/bust-probability` | Bust prob for selected vars/leads/bbox | `BustProbabilityResponse` |
| GET | `/api/v1/bust-detections` | Masked blobs / detections | `Page[BustDetection]` |
| GET | `/api/v1/attribution` | XAI drivers at a point/region | `AttributionResponse` |
| GET | `/api/v1/baselines` | Historical baseline stats | `Page[HistoricalBaseline]` |
| GET | `/api/v1/export` | Export field as file | binary stream |
| GET | `/api/v1/telemetry` | System telemetry / alerts | `Page[TelemetryEvent]` |

### 5.3 Pydantic v2 Models (authoritative field contracts)

> These are model specifications, not implementation. Field types are Pydantic v2. `Latitude`, `Longitude`, `LeadTime`, `VarCode` are constrained types defined in `models/common.py`.

```
# common.py
VarCode          = Literal["t2m","tp","z500","ws850"]
LayerCode        = Literal["confidence","p_bust","error"]
ExportFormat     = Literal["geojson","geotiff","netcdf"]
Latitude         = Annotated[float, Field(ge=6.0,  le=37.75)]
Longitude        = Annotated[float, Field(ge=68.0, le=99.75)]
LeadTime         = Annotated[int,   Field(ge=1,    le=10)]     # Day 1..10
Probability      = Annotated[float, Field(ge=0.0,  le=1.0)]
Confidence       = Annotated[float, Field(ge=0.0,  le=100.0)]
BBox             = tuple[Longitude, Latitude, Longitude, Latitude]  # [lon_min,lat_min,lon_max,lat_max]

class GridMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat_min: float = 6.0; lat_max: float = 37.75
    lon_min: float = 68.0; lon_max: float = 99.75
    resolution: float = 0.25
    n_rows: int = 128; n_cols: int = 128

# forecast.py
class ForecastRunSummary(BaseModel):
    run_id: str
    init_time: datetime
    source_model: Literal["GFS","ECMWF","SYNTHETIC"]
    n_lead_times: int = 10
    created_at: datetime
    mean_confidence: Confidence

class ForecastRunDetail(ForecastRunSummary):
    grid: GridMeta
    variables: list[VarCode]
    norm_stats_ref: str

# confidence.py
class ConfidenceMapResponse(BaseModel):
    run_id: str
    lead_time: LeadTime
    grid: GridMeta
    # 128x128 row-major (north-up at API boundary), float in [0,100]
    values: list[list[Confidence]]
    stats: dict[str, float]   # {"min","max","mean","p10","p90"}

# bust.py
class BustProbabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    variables: list[VarCode] = ["t2m","tp","z500","ws850"]
    lead_times: list[LeadTime] = [1,2,3,4,5,6,7,8,9,10]
    bbox: BBox | None = None

class BustProbabilityLayer(BaseModel):
    variable: VarCode
    lead_time: LeadTime
    values: list[list[Probability]]     # 128x128 (or bbox-cropped)
    threshold: float                    # τ_v (PRD §0.6)
    bust_frequency: float               # BF_v(t,R), PRD §2.3

class BustProbabilityResponse(BaseModel):
    run_id: str
    grid: GridMeta
    layers: list[BustProbabilityLayer]

class BustDetection(BaseModel):
    detection_id: str
    run_id: str
    variable: VarCode
    lead_time: LeadTime
    bbox: BBox
    polygon: dict            # GeoJSON Polygon geometry
    peak_probability: Probability
    mean_probability: Probability
    area_km2: float
    dominant_driver: str     # input channel code (PRD §0.4)
    confidence: Confidence
    created_at: datetime

# attribution.py
class DriverAttribution(BaseModel):
    channel_code: str        # PRD §0.4 code
    channel_name: str
    score: float             # normalized magnitude in [0,1]
    sign: Literal["+","-"]

class AttributionResponse(BaseModel):
    run_id: str
    variable: VarCode
    lead_time: LeadTime
    lat: Latitude
    lon: Longitude
    drivers: list[DriverAttribution]   # length 10, sorted desc by score
    spatial_gradcam: list[list[float]] # 128x128 in [0,1]
    narrative: str

# telemetry.py
class TelemetryEvent(BaseModel):
    event_id: str
    kind: Literal["INFERENCE","ALERT","EXPORT","ERROR"]
    severity: Literal["INFO","WARN","CRITICAL"]
    run_id: str | None
    message: str
    latency_ms: float | None
    created_at: datetime

class HealthResponse(BaseModel):
    status: Literal["ok","degraded"]
    version: str
    mongo: Literal["up","down"]
    model_loaded: bool
    uptime_s: float
```

### 5.4 Pagination Envelope

```
class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int = 50   # ge=1, le=500
    offset: int = 0   # ge=0
```

### 5.5 Query Parameter Validation (examples)

- `GET /api/v1/confidence-map` requires `run_id: str`, `lead_time: LeadTime`. Missing/out-of-range → `422`.
- `GET /api/v1/export` requires `run_id`, `variable: VarCode`, `layer: LayerCode`, `lead_time: LeadTime`, `format: ExportFormat`. Unsupported format → `415`.
- `GET /api/v1/attribution` requires `run_id`, `variable`, `lead_time`, `lat`, `lon` (point snapped to nearest grid cell).

### 5.6 OpenAPI

FastAPI auto-serves OpenAPI 3.1 at `/openapi.json` and Swagger UI at `/docs`. `test_api.py` asserts `/openapi.json` returns 200 and contains all paths in §5.2. `info.title="AETHER-BUST API"`, `info.version="1.0.0"`.

### 5.7 Performance / Caching

- Inference outputs per `run_id` cached in-process (LRU, maxsize=8) and persisted to MongoDB (`bust_detections`, precomputed grids referenced from `forecast_runs.result_refs`).
- Large 128×128 grids returned as nested lists in v1.0 (≈ 200 KB JSON); documented seam for future binary (Apache Arrow / `.npy` stream). p95 ≤ 400 ms served from cache.

---

## 6. CONFIGURATION (`backend/app/config.py`, pydantic-settings)

| Env var | Default | Meaning |
|---------|---------|---------|
| `MONGO_URI` | `mongodb://mongo:27017` | Mongo connection |
| `MONGO_DB` | `aether_bust` | Database name |
| `MODEL_WEIGHTS_PATH` | `""` (empty → demo weights) | Path to `.pt` |
| `SEED` | `26079` | Global determinism seed |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed origins |
| `API_VERSION` | `1.0.0` | Reported version |
| `TORCH_NUM_THREADS` | `1` | Determinism in CI |

---

## 7. TESTING & DETERMINISM REQUIREMENTS

| Test file | Asserts | Gate? |
|-----------|---------|-------|
| `test_shapes.py` | Input/output tensor shapes exactly match §2.2 | YES |
| `test_generator.py` | Synthetic shapes/dtype/no-NaN/positive labels | YES |
| `test_model.py` | Param count bound; forward runs; deterministic (2 runs equal) | YES |
| `test_loss.py` | Scalar>0; grads present; zero-loss degenerate | YES |
| `test_confidence.py` | Conf ∈[0,100]; AC-F1-1..3 | YES |
| `test_masking.py` | Blob min-size, bbox⊇polygon (AC-F5-1) | YES |
| `test_xai.py` | cam shape/range; 10 drivers; Σ=1 (AC-F3-*) | YES |
| `test_export.py` | GeoJSON/GeoTIFF/NetCDF validity (AC-F4-*) | YES |
| `test_api.py` | All endpoints 200/validation 422; OpenAPI complete | YES |

Determinism is mandatory: any test that runs the model twice with identical input MUST get identical output (tolerance 0).

*End of TRD.md — inherits PRD.md §0 constants.*
