# BUILD_PLAN.md — Agentic Execution Blueprint for Antigravity (Gemini 3.1 Pro)

**Project:** AETHER-BUST (SIH26079)
**Consumer:** Autonomous coding agent (Antigravity / Gemini 3.1 Pro).
**Binds to:** `PRD.md` §0 (constants), `TRD.md` (stack/tensor/API), `DB_SCHEMA.md` (collections/indexes), `UI_UX_DOC.md` (components/scales).
**Document Version:** 1.0.0
**Execution model:** 6 isolated sequential phases. Each phase is gated by a verification command that MUST exit `0`.

> INTERPRETATION RULE: If any instruction here conflicts with a sibling document, the numeric CONSTANTS in `PRD.md §0` win; otherwise the more specific document wins for its own domain (TRD for code, DB_SCHEMA for data, UI_UX_DOC for frontend). Never silently invent a third option — auto-repair toward these documents.

---

## SECTION 1: AUTONOMOUS AGENT GUARDRAILS

### 1.1 FORBIDDEN ACTIONS (HARD CONSTRAINTS)

The agent MUST NOT, under any circumstance:

1. **Invent dependencies.** Only packages listed in `TRD.md §1.1`/`§1.2`/`§1.3` may be imported or added to `requirements.txt`/`package.json`. Adding any other package is a violation → self-revert.
2. **Write partial or placeholder code.** The tokens `pass` (as a sole function body), `# TODO`, `// TODO`, `...` (Ellipsis as a body), `raise NotImplementedError`, `throw new Error("not implemented")`, `FIXME`, and stub returns like `return null // stub` are FORBIDDEN in committed files. Every function MUST be fully implemented per its spec.
3. **Advance on failure.** Never proceed to Phase N+1 while the Phase N verification command exits non-zero. A non-zero exit halts the phase; the agent enters AUTO-REPAIR (§1.3).
4. **Bypass tensor shape validation.** `tests/test_shapes.py` and any `ShapeContractError` guard MUST NOT be deleted, skipped (`@pytest.mark.skip`), `xfail`-ed, or weakened to make a phase pass. The tensor contract (`TRD §2.2`) is inviolable.
5. **Touch out-of-scope files.** Within a phase, only files listed in that phase's File Manifest may be created or modified. Do not edit sibling `.md` spec files. Do not modify files owned by a later phase.
6. **Change canonical constants.** `H=W=128`, `T=10`, `C=10`, `V=4`, thresholds `τ_v`, weights `w_v`, grid bounds, port numbers, and version pins are frozen. Never edit them to make a test pass.
7. **Introduce nondeterminism.** No unseeded randomness, no wall-clock-dependent inference output, no network calls during tests. Seeds fixed to `26079`.
8. **Weaken validators/tests to pass.** Fixing the code to satisfy the test is allowed; editing the test's asserted contract to be laxer is forbidden (unless the test itself contradicts a spec constant, in which case repair the test toward the spec and LOG the correction).

### 1.2 MANDATORY WORKFLOW (THE AGENTIC LOOP)

For EVERY unit of work inside a phase, the agent executes this loop exactly:

```
[1 INSPECT DIRECTORY]  -> list phase-scoped files, read current state, confirm prerequisites from prior phase's Exit Condition are still satisfied
        │
[2 WRITE/MODIFY CODE]  -> implement per the phase Implementation Blueprint; full implementations only (§1.1.2)
        │
[3 RUN VERIFICATION]   -> execute the EXACT phase Verification Script
        │
[4 ANALYZE LOGS/STDERR]-> capture exit code + stdout + stderr; classify failure (import? shape? assertion? lint? build?)
        │
   exit==0 ? ──── yes ──► [6 LOG SUCCESS & ADVANCE] -> append PHASE_LOG entry, satisfy Exit Condition, go to next phase
        │ no
        ▼
[5 AUTO-REPAIR]        -> apply the smallest correct fix consistent with the specs; return to [2]
                          (bounded: MAX_REPAIR_ATTEMPTS = 5 per verification script)
```

### 1.3 AUTO-REPAIR PROTOCOL

- On non-zero exit, parse stderr; map the top error to a cause; apply the minimal spec-consistent fix; re-run the SAME verification command.
- `MAX_REPAIR_ATTEMPTS = 5` per verification script. If still failing after 5 attempts, the agent MUST: (a) STOP, (b) write a `PHASE_<n>_BLOCKED.md` file describing the exact failing command, full stderr, attempted fixes, and hypothesized root cause, (c) NOT advance. It must not fabricate success.
- Repairs MUST move toward the spec, never away (do not relax a shape assertion, threshold, or version pin to pass).

### 1.4 PHASE LOG (append-only)

After each successful phase, append to `./PHASE_LOG.md` one entry:

```
## Phase <n> — <title> — PASSED
- verification: <exact command>
- exit_code: 0
- key_artifacts: <files>
- notes: <one line>
```

The agent MUST NOT create `PHASE_LOG.md` entries for phases that have not passed their verification with exit 0.

### 1.5 GLOBAL PRECONDITIONS (verified before Phase 1)

- Working directory = project root containing the 5 spec `.md` files.
- Available tools: `python3.11`, `pip`, `node 20`, `npm`, `docker`, `docker compose`, `curl`, `git`.
- Network is available ONLY during dependency installation steps (Phase 1 pip/npm, Phase 6 docker pull). Tests run offline.

---

## SECTION 2 & 3: PHASE-BY-PHASE EXECUTION MATRIX (with mandatory template)

Every phase below uses the mandatory template: **1. Phase Goal · 2. File Manifest · 3. Implementation Blueprint · 4. Verification Script · 5. Exit Condition.**

---

### PHASE 1 — Environment, Dependencies & Mock Meteorological Data Generator

**1. Phase Goal**
Establish the reproducible Python environment, pin every backend dependency (TRD §1.1), encode PRD §0 constants in code, and implement a deterministic synthetic meteorological data generator that emits tensors with the exact contract `[B,T,C,H,W]=[1,10,10,128,128]` plus ground-truth bust/error labels and CF-compliant NetCDF — eliminating downstream tensor bugs before any real dataset.

**2. File Manifest** (create)
```
backend/pyproject.toml
backend/requirements.txt
backend/app/__init__.py
backend/app/constants.py            # PRD §0 constants (SSOT in code)
backend/data/__init__.py
backend/data/generator.py           # synthetic generator (TRD §3.1)
backend/app/ml/__init__.py
backend/app/ml/confidence.py        # PRD §2.6 (pure function, used already for label sanity)
backend/tests/__init__.py
backend/tests/conftest.py
backend/tests/test_generator.py
backend/tests/test_shapes.py        # scaffolds the shape gate (extended in Phase 2)
.env.example
```

**3. Implementation Blueprint** (deterministic)
1. `requirements.txt`: list EXACT pins from TRD §1.1 (fastapi==0.111.0, torch==2.3.1, numpy==1.26.4, scipy==1.13.1, xarray==2024.6.0, netCDF4==1.6.5, rasterio==1.3.10, shapely==2.0.4, pyproj==3.6.1, Cartopy==0.23.0, shap==0.45.1, captum==0.7.0, motor==3.4.0, pymongo==4.7.3, pydantic==2.7.4, pydantic-settings==2.3.4, orjson==3.10.5, uvicorn[standard]==0.30.1, python-multipart==0.0.9, httpx==0.27.0, pytest==8.2.2, pytest-asyncio==0.23.7).
2. `constants.py`: define module-level constants — `PHI_MIN=6.0, PHI_MAX=37.75, LAMBDA_MIN=68.0, LAMBDA_MAX=99.75, DELTA=0.25, H=128, W=128, T=10, C=10, V=4, SEED=26079`; `VAR_CODES=("t2m","tp","z500","ws850")`; `CHANNEL_CODES=(...10 codes from PRD §0.4...)`; `TAU={"t2m":3.0,"tp":20.0,"z500":60.0,"ws850":5.0}`; `W_CONF={"t2m":0.25,"tp":0.35,"z500":0.25,"ws850":0.15}`; `TP_EVENT=20.0`, `BF_CRIT=0.30`, `MIN_BLOB_CELLS=9`. Provide helper `lat_vector()`/`lon_vector()` returning the exact 128-length coordinate arrays.
3. `confidence.py`: `confidence_index(bust_prob: np.ndarray[10,4,128,128]) -> np.ndarray[10,128,128]` = `100*(1 - Σ_v w_v * p_v)` clamped [0,100]. Pure NumPy, deterministic.
4. `generator.py` (TRD §3.1): seeded (`np.random.default_rng(SEED)`); build smooth base fields (low-wavenumber sinusoids + fractal noise) per channel added to per-variable climatological means; lead-degradation `σ_err(t)=σ0_v*(1+0.18*t)`; inject 3–6 Gaussian bust blobs at higher leads with amplitude ≥ `1.5*τ_v`; couple high cape+shear with tp/ws850 busts. Emit `X.npy [1,10,10,128,128]`, `Yb_true.npy [10,4,128,128]`, `Ye_true.npy [10,4,128,128]`, `run.nc` (xarray, CF-1.10, dims `(lead_time,lat,lon)`), `norm_stats.json {MU[10],SIGMA[10]}`. Labels computed via PRD §2.2/§2.5 formulas. Provide `generate_run(run_id, out_dir) -> dict(paths)`.
5. `test_generator.py`: assert shapes/dtype float32; no NaN/Inf; `Yb_true.sum() >= 1`; `run.nc` opens in xarray with dims `(lead_time=10, lat=128, lon=128)`; `norm_stats.json` has 10-length MU/SIGMA.
6. `test_shapes.py` (Phase-1 portion): assert generated `X.npy` shape is exactly `(1,10,10,128,128)` and `Yb_true.npy` is `(10,4,128,128)`.
7. `conftest.py`: session fixture generating one run into a temp dir; `.env.example` documents TRD §6 env vars.

**4. Verification Script** (exact)
```bash
cd backend && \
python3.11 -m venv .venv && . .venv/bin/activate && \
pip install --upgrade pip && pip install -r requirements.txt && \
python -c "import app.constants as k; assert (k.H,k.W,k.T,k.C,k.V)==(128,128,10,10,4), k.__dict__" && \
python -m pytest tests/test_generator.py tests/test_shapes.py -q
```

**5. Exit Condition**
`pytest` exits `0`; `constants.py` assertion passes; a synthetic run directory exists with `X.npy (1,10,10,128,128)`, `Yb_true.npy (10,4,128,128)`, `Ye_true.npy (10,4,128,128)`, `run.nc`, `norm_stats.json`. `PHASE_LOG.md` updated. No forbidden tokens present (grep clean).

---

### PHASE 2 — Core ML Pipeline & Inference Engine

**1. Phase Goal**
Implement `BustNet` (ConvLSTM + U-Net + Temporal Self-Attention) exactly per TRD §2.3, the `MultiTaskBustLoss` (TRD §2.4), the deterministic `InferenceRunner` (TRD §2.6), connected-component masking (PRD §3.5), and the XAI module (Grad-CAM + Integrated Gradients, TRD §2.5) — all covered by gating unit tests including the inviolable shape test.

**2. File Manifest** (create/modify)
```
backend/app/ml/architecture.py      # BustNet, ConvLSTMCell, TemporalSelfAttention, ShapeContractError
backend/app/ml/loss.py              # MultiTaskBustLoss
backend/app/ml/inference.py         # InferenceRunner + InferenceResult + BustBlob
backend/app/ml/masking.py           # connected-component bounding (PRD §3.5)
backend/app/ml/xai.py               # gradcam(), integrated_gradients(), narrative()
backend/app/ml/norm_stats.json      # written by generator; consumed here
backend/tests/test_model.py
backend/tests/test_loss.py
backend/tests/test_confidence.py
backend/tests/test_masking.py
backend/tests/test_xai.py
backend/tests/test_shapes.py        # extended: assert BustNet I/O shapes (TRD §2.2)
```

**3. Implementation Blueprint** (deterministic)
1. `architecture.py`:
   - `ShapeContractError(ValueError)`; `BustNet.forward` validates input is exactly `[B,10,10,128,128]` else raises it.
   - `UNetEncoder`/`UNetDecoder` per TRD §2.3.1/§2.3.4 (GroupNorm(8), SiLU, skips s1..s4, bottleneck `[B,256,8,8]`).
   - `ConvLSTMCell` (3×3, 256→256) per §2.3.2; loop over T causally.
   - `TemporalSelfAttention` (nn.MultiheadAttention, 8 heads, causal mask, residual+LayerNorm) per §2.3.3.
   - Heads: bust (Conv1×1→4, sigmoid), error (Conv1×1→4, softplus). Return `{"bust":Yb,"error":Ye}` with shapes `[B,10,4,128,128]`.
   - Assert param count `1e6 < n < 3e7`.
2. `loss.py`: `MultiTaskBustLoss` per TRD §2.4 (focal BCE α=0.75,γ=2.0; masked MAE λ_hit=1.0,λ_all=0.1; per-var w_v; β_cls=1.0,β_reg=0.5; error normalized by τ_v). Returns scalar; components exposed for logging.
3. `inference.py`: determinism block on import (seed 26079, `torch.use_deterministic_algorithms(True)`, threads=1). `InferenceRunner.load()/warmup()/run(run_id)` returns `InferenceResult(bust,error,confidence,blobs)` (confidence via `confidence.py`).
4. `masking.py`: threshold `P_agg≥0.5` → `scipy.ndimage.label` (8-conn) → discard `<MIN_BLOB_CELLS` → per blob compute bbox (lon/lat), convex-hull polygon (shapely), peak/mean prob, area_km2 (spherical), dominant driver (argmax mean attribution). Return `list[BustBlob]`; guarantee bbox ⊇ polygon.
5. `xai.py`: `gradcam(model,X,v,t,region)->[128,128] in [0,1]`; `integrated_gradients(model,X,v,t,region)->10 (code,score,sign)` L1-normalized to Σ=1; `narrative(...)` per PRD §3.3.1 rule table.
6. Tests: `test_model.py` (param bound, forward shapes, determinism: two runs equal, ShapeContractError on wrong input); `test_loss.py` (scalar>0, grads non-None, zero-loss degenerate); `test_confidence.py` (∈[0,100], AC-F1-1..3); `test_masking.py` (min-size, bbox⊇polygon); `test_xai.py` (cam shape/range, 10 drivers, Σ=1±1e-6). Extend `test_shapes.py` to run `BustNet` on `[2,10,10,128,128]` and assert both outputs `[2,10,4,128,128]`.

**4. Verification Script** (exact)
```bash
cd backend && . .venv/bin/activate && \
python -m pytest tests/test_shapes.py tests/test_model.py tests/test_loss.py \
  tests/test_confidence.py tests/test_masking.py tests/test_xai.py -q && \
python -c "import torch,app.ml.architecture as a; m=a.BustNet().eval(); x=torch.zeros(1,10,10,128,128); o=m(x); assert o['bust'].shape==(1,10,4,128,128) and o['error'].shape==(1,10,4,128,128), [o['bust'].shape,o['error'].shape]; print('SHAPES_OK')"
```

**5. Exit Condition**
All six test files pass (exit 0); inline shape check prints `SHAPES_OK`; `test_shapes.py` NOT skipped/xfailed; determinism test confirms bit-identical repeated inference; no forbidden tokens. `PHASE_LOG.md` updated.

---

### PHASE 3 — FastAPI Backend & Pydantic Data Layer

**1. Phase Goal**
Expose the ML pipeline through the FastAPI service defined in TRD §5: all routers, Pydantic v2 models (strict, `extra="forbid"`), async MongoDB (motor) client with the DB_SCHEMA validators + indexes (including `2dsphere`), seed script, and export service (GeoJSON/GeoTIFF/NetCDF) — integrated with a mock inference runner.

**2. File Manifest** (create/modify)
```
backend/app/config.py
backend/app/main.py
backend/app/db/__init__.py
backend/app/db/client.py
backend/app/db/indexes.py
backend/app/models/{__init__,common,forecast,bust,attribution,telemetry}.py
backend/app/services/{__init__,run_service,export_service}.py
backend/app/routers/{__init__,health,forecast_runs,confidence,bust,attribution,export,telemetry}.py
scripts/seed_mongo.py
backend/tests/test_api.py
backend/tests/test_export.py
backend/Dockerfile
```

**3. Implementation Blueprint** (deterministic)
1. `config.py`: pydantic-settings per TRD §6 (MONGO_URI, MONGO_DB=aether_bust, MODEL_WEIGHTS_PATH, SEED=26079, CORS_ORIGINS, API_VERSION=1.0.0, TORCH_NUM_THREADS=1).
2. `db/client.py`: motor `AsyncIOMotorClient`; lifespan-managed. `db/indexes.py`: create all 5 collections with `$jsonSchema` validators (DB_SCHEMA §1–§5) and every named index (unique, compound, `2dsphere`, TTL).
3. `models/*`: exact Pydantic v2 models from TRD §5.3 with constrained types (Latitude/Longitude/LeadTime/Probability/Confidence/VarCode/BBox), `ConfigDict(extra="forbid")` on request bodies, `Page[T]` generic.
4. `routers/*`: implement all endpoints in TRD §5.2 with `response_model`, `ORJSONResponse`, RFC 9457 error handler. `health` checks mongo + model_loaded. `confidence`/`bust`/`attribution` read cached inference artifacts (LRU maxsize=8) via `run_service` (uses InferenceRunner from Phase 2). `export` streams files via `export_service`.
5. `export_service.py`: GeoJSON (RFC 7946, contoured p≥0.5, required properties), GeoTIFF (rasterio, EPSG:4326, 128×128, north-up geotransform origin 37.75N/68.0E, pixel 0.25), NetCDF (xarray CF-1.10, dims (lead_time,lat,lon), units/standard_name/_FillValue).
6. `main.py`: app factory `title="AETHER-BUST API" version="1.0.0"`, CORS, lifespan (connect mongo, ensure indexes, warmup model), mount routers under `/api/v1` (+ `/health` root).
7. `seed_mongo.py`: create collections/indexes + upsert the 5 DB_SCHEMA mock docs idempotently.
8. Tests: `test_api.py` uses `httpx.ASGITransport` + `mongomock`-free real/ephemeral mongo (via `MONGO_URI` from CI service or `mongodb-memory` fallback documented) — assert every endpoint returns 200 for valid input and 422 for out-of-range (`lead_time=11`, `lat=99`), `/openapi.json` contains all §5.2 paths, `/health` returns `status`. `test_export.py` asserts AC-F4-1..3 (GeoJSON RFC7946 + properties; GeoTIFF opens in rasterio EPSG:4326 correct transform; NetCDF opens in xarray with dims (10,128,128) + CF attrs).
9. `Dockerfile`: python:3.11-slim, install requirements, copy app, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`.

**4. Verification Script** (exact)
```bash
cd backend && . .venv/bin/activate && \
docker compose -f ../docker-compose.yml up -d mongo && sleep 5 && \
python ../scripts/seed_mongo.py && \
python -m pytest tests/test_api.py tests/test_export.py -q && \
( uvicorn app.main:app --host 127.0.0.1 --port 8000 & echo $! > /tmp/aether_api.pid ) && sleep 6 && \
curl -f http://127.0.0.1:8000/health && \
curl -f "http://127.0.0.1:8000/openapi.json" -o /tmp/openapi.json && \
python -c "import json;d=json.load(open('/tmp/openapi.json'));req=['/health','/api/v1/forecast-runs','/api/v1/confidence-map','/api/v1/bust-probability','/api/v1/bust-detections','/api/v1/attribution','/api/v1/baselines','/api/v1/export','/api/v1/telemetry'];miss=[p for p in req if not any(p in k for k in d['paths'])];assert not miss, miss;print('OPENAPI_OK')" ; \
kill $(cat /tmp/aether_api.pid)
```

**5. Exit Condition**
`test_api.py` + `test_export.py` pass; `curl -f /health` exits 0 (HTTP 200); OpenAPI contains all §5.2 paths (`OPENAPI_OK`); all 5 collections exist with named unique + `2dsphere` indexes (verified in `test_api.py` via `getIndexes`); seed docs present. No forbidden tokens. `PHASE_LOG.md` updated.

---

### PHASE 4 — React Operational Dashboard Core

**1. Phase Goal**
Scaffold the Vite + React 18 + Tailwind + Leaflet/deck.gl frontend per UI_UX_DOC, implementing the 3-column layout, top bar, control rail, base map with the 128×128 grid overlay, and the Day 1–10 lead-time scrubber wired to `zustand` + `react-query` against the Phase-3 API.

**2. File Manifest** (create)
```
frontend/package.json
frontend/vite.config.ts
frontend/tsconfig.json
frontend/tailwind.config.js
frontend/postcss.config.js
frontend/index.html
frontend/src/main.tsx
frontend/src/App.tsx
frontend/src/theme/{tokens.ts,colormaps.ts}
frontend/src/store/useConsoleStore.ts
frontend/src/api/{client.ts,queries.ts,types.ts}
frontend/src/utils/{colorScale.ts,grid.ts,format.ts}
frontend/src/layout/{TopBar.tsx,ThreeColumnLayout.tsx,BottomStrip.tsx}
frontend/src/components/controls/{RunSelector,VariableSelector,LayerToggleGroup,OpacitySlider,ConfidenceBandFilter,BaselineCompare}.tsx
frontend/src/components/map/{RiskMap,LeafletBaseMap,DeckGridLayer,MapLegend,ScrubberBar,GridReadout}.tsx
frontend/src/components/common/{Pill,StatusDot,Card,SegmentedControl}.tsx
frontend/tests/colormaps.test.ts
```

**3. Implementation Blueprint** (deterministic)
1. `package.json`: EXACT pins from TRD §1.2; scripts `dev`,`build`,`preview`,`test` (vitest for colormaps unit test), `lint`. Vite proxy `/api → http://localhost:8000`.
2. `tailwind.config.js`: `theme.extend` with all UI_UX_DOC §0 tokens (colors, fonts, radius, shadow).
3. `theme/colormaps.ts`: encode EXACT control points from UI_UX_DOC §3 (SCALE_CONFIDENCE, SCALE_BUST_RISK, SCALE_ERROR_DIVERGING, predictor ramps).
4. `store/useConsoleStore.ts`: zustand store per UI_UX_DOC §2.3 (runId, variable, layer, leadTime, opacity, activeBands, selection, baselineCompare, playing).
5. `api/*`: axios client (baseURL `/api/v1`), react-query hooks (useRuns, useConfidenceMap, useBustProbability, useHealth...), TS types mirroring TRD §5.3.
6. Layout: `ThreeColumnLayout` (320/fluid/380 at xl), `TopBar` (RunSelector, UTC clock, ConfidencePill, HealthDot), `BottomStrip` (GridReadout).
7. Map: `LeafletBaseMap` (dark tiles, bounds locked to PRD §0.1), `DeckGridLayer` renders confidence-map values via `colorScale`, `MapLegend`, `ScrubberBar` (10 stops, keyboard + play).
8. `colormaps.test.ts`: assert scale arrays equal UI_UX_DOC §3 control points (UX-4).

**4. Verification Script** (exact)
```bash
cd frontend && \
npm ci && \
npm run test -- --run && \
npm run build && \
test -d dist && test -f dist/index.html && echo "BUILD_OK"
```

**5. Exit Condition**
`npm run build` exits 0 and produces `dist/index.html` (`BUILD_OK`); `colormaps.test.ts` passes (UX-4); no TypeScript errors; component tree matches UI_UX_DOC §6 for the Phase-4 subset. No forbidden tokens. `PHASE_LOG.md` updated.

---

### PHASE 5 — Dashboard Telemetry & Explainability UI

**1. Phase Goal**
Complete the operational UI: bust-probability heatmap layer, GeoJSON anomaly overlays, region telemetry (RMSE/MAE/BF vs baseline), and the XAI panel (driver bar chart, Grad-CAM thumbnail, narrative), fully integrated with the Phase-3 attribution/bust/export APIs.

**2. File Manifest** (create/modify)
```
frontend/src/components/map/BustPolygonLayer.tsx
frontend/src/components/telemetry/{RegionTelemetry,MetricTile,ConfidenceByLeadChart}.tsx
frontend/src/components/xai/{XaiPanel,DriverBarChart,GradcamThumb,NarrativeCard}.tsx
frontend/src/components/alerts/AlertsTicker.tsx
frontend/src/layout/ThreeColumnLayout.tsx        # modify: mount COL C + bottom alerts
frontend/src/api/queries.ts                      # modify: add useAttribution,useBaselines,useTelemetry,useBustProbability
frontend/src/components/controls/LayerToggleGroup.tsx   # modify: enable bust/error/predictor layers
frontend/e2e/smoke.spec.ts
frontend/playwright.config.ts
frontend/package.json                            # modify: add @playwright/test, e2e script
```

**3. Implementation Blueprint** (deterministic)
1. `BustPolygonLayer`: render GeoJSON detections (deck.gl GeoJsonLayer), fill by peak prob via SCALE_BUST_RISK, click → detection popover → sets selection + opens XAI.
2. `RegionTelemetry` + `MetricTile`: metric tiles (RMSE/MAE/BF/Confidence) with baseline delta chips; `ConfidenceByLeadChart` (Recharts line, Day 1–10).
3. `XaiPanel`: `DriverBarChart` (10 drivers, sorted desc, colored by sign), `GradcamThumb` (canvas render of 128×128 gradcam via SCALE_BUST_RISK), `NarrativeCard` (attribution.narrative, top-2 bold).
4. `AlertsTicker`: poll `useTelemetry` (ALERT kind) every 15 s; CRITICAL in `status.crit`.
5. Wire `LayerToggleGroup` to switch active layer (confidence/p_bust/error) and predictor overlays; opacity slider drives deck.gl `opacity`.
6. `e2e/smoke.spec.ts` (Playwright): load app (frontend preview + running backend), assert `#risk-map`,`#control-rail`,`#xai-panel` exist (UX-2); move scrubber → intercept confidence-map refetch (UX-3); click a mock bust polygon → XAI panel shows 10 driver bars (UX-5).

**4. Verification Script** (exact)
```bash
cd frontend && \
npm run build && \
npx playwright install --with-deps chromium && \
( npm run preview -- --port 4173 & echo $! > /tmp/aether_fe.pid ) && sleep 5 && \
npm run e2e && \
kill $(cat /tmp/aether_fe.pid) && echo "E2E_UI_OK"
```
> Precondition: the Phase-3 backend must be running (started by the same orchestration or mocked via Playwright route fulfillment against fixtures in `e2e/fixtures/`).

**5. Exit Condition**
`npm run build` exits 0; Playwright `smoke.spec.ts` passes (UX-2/UX-3/UX-5) → prints `E2E_UI_OK`; XAI panel renders exactly 10 driver bars from a mock attribution; no forbidden tokens. `PHASE_LOG.md` updated.

---

### PHASE 6 — System Integration, E2E Smoke Tests & Dockerization

**1. Phase Goal**
Assemble the full stack (MongoDB + FastAPI + React/nginx) via Docker Compose, run an end-to-end health + data-flow smoke test on synthetic data, execute a stress pass, and confirm production-parity startup.

**2. File Manifest** (create/modify)
```
docker-compose.yml
frontend/Dockerfile
frontend/nginx.conf
scripts/smoke_e2e.sh
scripts/healthcheck.sh
scripts/stress_test.py
.env.example                         # modify: full compose env
README.md                            # run instructions (no code)
```

**3. Implementation Blueprint** (deterministic)
1. `docker-compose.yml` (compose v2): services `mongo` (mongo:7.0.11, named volume, healthcheck `mongosh --eval "db.adminCommand('ping')"`), `backend` (build backend/Dockerfile, depends_on mongo healthy, env from `.env`, port 8000, healthcheck `curl -f localhost:8000/health`), `frontend` (build frontend/Dockerfile → nginx:1.27-alpine serving `dist`, port 5173→80, `nginx.conf` proxies `/api` → `backend:8000`). Named network `aether_net`.
2. `frontend/Dockerfile`: multi-stage (node:20.14 build → nginx:1.27-alpine). `nginx.conf`: SPA fallback + `/api` proxy.
3. `scripts/smoke_e2e.sh`: `docker compose up -d --build`; wait for all healthchecks green; `python scripts/seed_mongo.py` (or entrypoint); run `generator` to create a run; POST/GET the full flow: list runs → confidence-map (Day 1 & Day 10) → bust-probability → attribution → export (all 3 formats, verify file magic bytes/opens) → telemetry; assert every step HTTP 200 and shapes correct; `set -e` so any failure exits non-zero.
4. `scripts/healthcheck.sh`: curl `/health`, assert `status` in {ok,degraded} and `mongo:"up"`, `model_loaded:true`.
5. `scripts/stress_test.py`: run 25 sequential inferences on synthetic runs; assert each ≤ 2.0 s CPU (PRD NFR) and outputs shape-valid; report p50/p95 latency.
6. `README.md`: exact `docker compose up` instructions, ports, health URLs (documentation only — NO application code).

**4. Verification Script** (exact)
```bash
docker compose up -d --build && \
bash scripts/healthcheck.sh && \
bash scripts/smoke_e2e.sh && \
python scripts/stress_test.py && \
curl -f http://localhost:8000/health && \
curl -f http://localhost:5173/ -o /dev/null && \
echo "FULL_STACK_OK" && \
docker compose down
```

**5. Exit Condition**
`docker compose up --build` brings all 3 services to healthy; `smoke_e2e.sh` completes the full data flow with every step HTTP 200 and correct shapes; `stress_test.py` reports p95 ≤ 2.0 s CPU per inference; both `curl -f` (backend `/health`, frontend `/`) exit 0; script prints `FULL_STACK_OK`. No forbidden tokens anywhere in the repo (final global grep gate below). `PHASE_LOG.md` updated with Phase 6 PASSED.

---

## SECTION 4: GLOBAL FINAL GATES (run after Phase 6)

The agent MUST run these repo-wide gates; each MUST exit 0.

```bash
# G1 — no forbidden placeholder tokens in source (excludes .md specs, node_modules, .venv, dist)
! grep -rEn "TODO|FIXME|NotImplementedError|not implemented|^\s*\.\.\.\s*$|# stub|// stub" \
  --include=*.py --include=*.ts --include=*.tsx --include=*.js \
  backend/app backend/data frontend/src scripts

# G2 — all phase gates recorded as PASSED
python3 -c "import re,sys;t=open('PHASE_LOG.md').read();n=len(re.findall(r'PASSED',t));assert n>=6,f'only {n} phases passed';print('ALL_PHASES_PASSED')"

# G3 — dependency purity: no import outside TRD-pinned packages (static check)
cd backend && . .venv/bin/activate && \
python3 -c "import tomllib,pathlib;print('DEP_MANIFEST_OK')" && pip check
```

**FINAL EXIT CONDITION (project complete):** Phases 1–6 all PASSED in `PHASE_LOG.md`; G1, G2, G3 exit 0; `docker compose up` yields a healthy full stack serving the operational dashboard at `http://localhost:5173` backed by the API at `http://localhost:8000`, all consistent with `PRD.md §0` constants.

---

## APPENDIX A — PORT & PATH REGISTRY (frozen)

| Service | Port | URL |
|---------|------|-----|
| MongoDB | 27017 | `mongodb://mongo:27017` |
| FastAPI | 8000 | `http://localhost:8000` (`/health`, `/docs`, `/api/v1/*`) |
| Frontend (nginx) | 5173→80 | `http://localhost:5173` |
| Vite dev | 5173 | `http://localhost:5173` (dev only) |

## APPENDIX B — PHASE DEPENDENCY GRAPH

```
Phase1 (env+data) ──► Phase2 (ML) ──► Phase3 (API) ──► Phase6 (integration)
                                          │                    ▲
                                          └► Phase4 (UI core) ─► Phase5 (UI xai) ┘
```
Phase 4 may begin only after Phase 3 `/openapi.json` gate passes (frontend types mirror the live contract). Phase 6 requires Phases 3 and 5 both PASSED.

*End of BUILD_PLAN.md — every phase is gated by an exit-code-0 verification. The agent advances only on green.*
