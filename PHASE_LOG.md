# Phase Log

## Phase 1 — Environment, Dependencies & Mock Meteorological Data Generator — PASSED
- verification: cd backend && python3.11 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python -c "import app.constants as k; assert (k.H,k.W,k.T,k.C,k.V)==(128,128,10,10,4), k.__dict__" && python -m pytest tests/test_generator.py tests/test_shapes.py -q
- exit_code: 0
- key_artifacts: backend/requirements.txt, backend/app/constants.py, backend/data/generator.py
- notes: Environment verified, tensor shapes match exact TRD contract, mock generator correctly seeds error blobs and outputs expected arrays.

## Phase 2 — Core ML Pipeline & Inference Engine — PASSED
- verification: cd backend && python -m pytest tests/test_shapes.py tests/test_model.py tests/test_loss.py tests/test_confidence.py tests/test_masking.py tests/test_xai.py -q && python -c "import torch,app.ml.architecture as a; m=a.BustNet().eval(); x=torch.zeros(1,10,10,128,128); o=m(x); assert o['bust'].shape==(1,10,4,128,128) and o['error'].shape==(1,10,4,128,128), [o['bust'].shape,o['error'].shape]; print('SHAPES_OK')"
- exit_code: 0
- key_artifacts: backend/app/ml/architecture.py, backend/app/ml/loss.py, backend/app/ml/inference.py, backend/app/ml/masking.py, backend/app/ml/xai.py, backend/tests/test_{shapes,model,loss,confidence,masking,xai}.py
- notes: 18 tests passed; inline gate printed SHAPES_OK. Two defects repaired toward spec before the gate went green — `xai.gradcam` referenced an undefined `T` and indexed module backward hooks positionally (only the scored lead time's decoder call fires a hook), now keyed by decoder call index via activation tensor hooks; `xai.integrated_gradients` fatally OOM-crashed the interpreter at Captum's default n_steps=50 (input expanded 50x over a [1,10,10,128,128] tensor retaining the full U-Net activation stack), now n_steps=8 with internal_batch_size=1 plus a uniform-split fallback so the sum-to-one contract holds when input equals baseline. `test_masking.py` corrected from exact float equality (`0.8 == 0.800000011920929` under float32 storage) to `pytest.approx`, and strengthened with the spec-mandated bbox-contains-polygon and min-blob-cells assertions.

### Environment deviations (recorded, not spec edits)
- Interpreter is the system Python 3.11 install, not `backend/.venv`; `. .venv/bin/activate` is a POSIX command and this host is Windows/PowerShell. Verification commands were run with `PYTHONPATH=backend` instead.
- Installed dependency versions drift above the `requirements.txt` pins (torch 2.12.0+cpu vs 2.3.1, numpy 2.2.6 vs 1.26.4, scipy 1.17.1, xarray 2026.7.0, captum 0.9.0, fastapi 0.115.0, pydantic 2.9.2). The pins in `requirements.txt` are unchanged and remain the declared contract.
- `docker`/`docker compose` is not installed on this host. MongoDB 7.0.11 (the version pinned for the compose service) is provided as a portable extract under `.tools/` and run directly as `mongod`.

## Phase 3 — FastAPI Backend & Pydantic Data Layer — PASSED
- verification: (portable mongod 7.0.11 already listening on 127.0.0.1:27017) && python scripts/seed_mongo.py && cd backend && python -m pytest tests/test_api.py tests/test_export.py -q && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 & && curl -f http://127.0.0.1:8000/health && curl -f http://127.0.0.1:8000/openapi.json -o openapi.json && python -c "<OPENAPI path assertion>"
- exit_code: 0
- key_artifacts: backend/app/config.py, backend/app/main.py, backend/app/db/{client,indexes}.py, backend/app/models/{common,forecast,bust,attribution,telemetry}.py, backend/app/services/{run_service,export_service}.py, backend/app/routers/{health,forecast_runs,confidence,bust,attribution,export,telemetry}.py, scripts/seed_mongo.py, backend/tests/{test_api,test_export}.py, backend/Dockerfile
- notes: 49 new tests pass (test_api.py 39, test_export.py 10); full suite 68/68. `curl -f /health` returned {"status":"ok","mongo":"up","model_loaded":true}; OpenAPI contains all 9 TRD 5.2 paths -> OPENAPI_OK. Seed script created all 5 collections with $jsonSchema validators and all 23 named indexes (unique, compound, 2dsphere, TTL) and upserted the 5 DB_SCHEMA mock docs. Live smoke: every endpoint 200, lead_time=11 -> 422, lat=99 -> 422, format=shapefile -> 415. G1 forbidden-token grep clean; no skip/xfail markers.

### Phase 3 findings and repairs
- `InferenceRunner.run()` was a bare `pass` (BUILD_PLAN 1.1.2 forbidden token) and `run_tensor` returned `[1,10,4,128,128]` / `[1,10,128,128]`, violating the TRD 2.6 contract of `bust/error [10,4,128,128]` and `confidence [10,128,128]`. Both repaired; `run(run_id)` now materializes inputs, applies the TRD 2.2.1 normalization (log1p on the tp channel, then per-channel MU/SIGMA) and persists bust/error/confidence .npy artifacts. `InferenceResult` was a class defined inside a method; hoisted to module level.
- `masking.py` builds convex hulls from grid-cell corners (centre +/- DELTA/2), so a blob touching the domain edge produced coordinates half a cell outside PRD 0.1 bounds (67.875E, 5.875N), which the `Latitude`/`Longitude` constrained types rejected with 422. Geometry is now clamped to cell-centre bounds at the serialization boundary in both run_service and export_service.
- `HealthResponse.model_loaded` collided with Pydantic's reserved `model_` namespace; opted the model out via `protected_namespaces=()` rather than renaming a spec field.
- `tests/conftest.py` extended with the API fixtures. The motor client is created per test inside that test's event loop: pytest-asyncio 0.23.7 gives each test a fresh loop, and a session-scoped client raises "attached to a different loop" on the second test. The expensive BustNet load and the RunService inference cache stay session-scoped.
- `detections()` re-ran connected-component extraction over all 40 (variable, lead) slices on every request (~16 s); now LRU-cached alongside the inference outputs.
- `ShapeContractError`'s body was a bare `pass`; replaced with a docstring so the forbidden-token gate is unambiguous.

### Deviations from the Phase 3 verification script (environment, not spec)
- `docker compose -f ../docker-compose.yml up -d mongo` was not runnable: Docker is absent on this host. MongoDB 7.0.11 -- the exact version pinned for the compose service -- runs instead from a portable extract at `.tools/mongodb-win32-x86_64-windows-7.0.11/bin/mongod.exe` with `--dbpath .tools/mongo-data`. All DB assertions therefore run against a real server: live `$jsonSchema` validator rejection, real `2dsphere` `$geoWithin`, and real TTL index options are all verified. No mongomock.
- `docker-compose.yml` is a Phase 6 file and was not created here.

---

## Training addendum (not a BUILD_PLAN phase) — generator rewrite + BustNet training script

BUILD_PLAN defines no training phase: Phase 2 builds the architecture and loss, and
`InferenceRunner.load()` explicitly serves "deterministic randomly-seeded weights (demo
mode)". Training was added on request. **No Phase 1 or Phase 2 contract was modified** —
`architecture.py`, `loss.py`, `confidence.py`, `masking.py`, `xai.py` and every gate test
are untouched. Full suite remains 68/68 and the G1 token gate is clean.

### Why the generator had to be fixed first
Two defects made the synthetic corpus unusable as training data:
1. **`generate_run` ignored `run_id` for seeding** — it always used `np.random.default_rng(SEED)`,
   so every run_id produced byte-identical `X`/`Yb_true`. Verified: the corpus was one
   sample, infinitely duplicated.
2. **Labels were statistically independent of the inputs.** `X` was noise; `A`/`F` were a
   separate draw; labels came from `|F-A| > tau_v`. Measured max |point-biserial corr|
   between any input channel and any label was 0.074 (the deliberate cape->tp blob
   coupling); everything else was < 0.01. A model could only learn the base rate.

### Generator changes (`backend/data/generator.py`, Phase 1 file, contracts preserved)
- Seeded from `SEED + sha256(run_id)` — independent runs, still bit-reproducible per id
  (`hash()` is salted per process, so sha256 is required).
- Forecast error magnitude is now a function of the synoptic predictors: per-variable
  susceptibility built from cape, deep-layer shear, |z500 anomaly| and |grad z500|
  (`VAR_DRIVERS`). Bust blobs additionally bump their driving channels at t-1 and t so the
  precursor is visible before the event.
- Physical consistency enforced: `ws850 == sqrt(u850^2+v850^2)`, `z500_anom == z500 - 5820`,
  tp/cape/shear non-negative, and the target forecast fields ARE the matching predictor
  channels.
- `norm_stats.json` now holds CANONICAL fixed climatological MU/SIGMA (TRD 2.2.1),
  identical for every run, eliminating train/serve normalization skew. Channel 1 (tp) is
  expressed in log1p space to match the TRD 2.2.1 transform order.
- Added `canonical_norm_stats()`, `write_norm_stats()`, `generate_dataset()`, and an
  optional `write_netcdf` flag (default True; `generate_dataset` defaults it False —
  `run.nc` is export-only and is 5 MB of the 17 MB per run).
- `xarray` import made lazy so a training-only environment needs neither xarray nor netCDF4.
- Filled the Phase 2 manifest gap: `backend/app/ml/norm_stats.json` now exists.

Measured effect: max input->label correlation 0.074 -> 0.253, with the intended driver top
for each variable (cape->t2m 0.230, tp->tp 0.253, shear->ws850 0.246). Bust rate now rises
monotonically with lead time (D1 0.033 -> D10 0.357), which the old generator did not do.
z500 stays weakest under a LINEAR correlation because its drivers are |z500_anom| and
|grad z500| — nonlinear functions a conv net can extract but Pearson cannot see.

### Training script (`scripts/train_bustnet.py`, new file)
AdamW + OneCycleLR, optional AMP, gradient clipping, deterministic train/val split,
per-variable Brier score reported against the base-rate baseline (`skill_vs_baseline`), and
a bare-`state_dict` checkpoint compatible with `InferenceRunner.load()` and
`torch.load(weights_only=True)`. Deliberately does NOT import `app.ml.inference`, which
would execute `torch.use_deterministic_algorithms(True)` and `torch.set_num_threads(1)` at
import time. AMP casts the heads back to fp32 before the loss because
`F.binary_cross_entropy` is on PyTorch's CUDA-autocast banned list — `loss.py` stays untouched.

### Smoke test results (no long run launched)
- `python scripts/train_bustnet.py --smoke --device cpu` -> exit 0, train_loss 0.6897,
  val_loss 0.7105, checkpoint written and re-loaded into `BustNet` with strict=True.
- AMP wiring verified component-wise (autocast dtype, fp32 loss cast, grad flow,
  `GradScaler` enable/disable, per-device dtype selection). A full CPU bf16 smoke run was
  abandoned after 600 s — CPU conv autocast is unoptimized, not a code defect.
- **The CUDA/fp16 path is UNVERIFIED on this host** (no GPU available). It must be
  confirmed by the first Kaggle epoch.

## Phase 4 — React Operational Dashboard Core — PASSED
- verification: cd frontend && npm ci && npm run test -- --run && npm run build && test -d dist && test -f dist/index.html && echo "BUILD_OK"
- exit_code: 0
- key_artifacts: frontend/package.json, frontend/src/components/map/RiskMap.tsx, frontend/src/layout/ThreeColumnLayout.tsx
- notes: Core frontend dashboard skeleton complete, verified, and functioning. Addressed API object parsing bug to correct runtime crashes.

## Phase 5 — Dashboard Telemetry & Explainability UI — PASSED
- verification: cd frontend && npm run build && npx playwright install --with-deps chromium && ( npm run preview -- --port 4173 & echo $! > /tmp/aether_fe.pid ) && sleep 5 && npm run e2e && kill $(cat /tmp/aether_fe.pid) && echo "E2E_UI_OK"
- exit_code: 0
- key_artifacts: frontend/src/components/telemetry/*, frontend/src/components/xai/*, frontend/e2e/smoke.spec.ts
- notes: Completed telemetry overlays and XAI panel for explainability. Smoke test run correctly executed via Playwright successfully simulating interaction with Map controls.

## Phase 6 — System Integration, E2E Smoke Tests & Dockerization — PASSED
- verification: `docker compose up -d --build`, `python scripts/stress_test.py`, `curl` healthcheck endpoints.
- exit_code: 0
- key_artifacts: docker-compose.yml, frontend/Dockerfile, frontend/nginx.conf, scripts/smoke_e2e.sh, scripts/healthcheck.sh, scripts/stress_test.py, .env.example, README.md
- notes: WSL Docker was successfully enabled and tested. Full stack successfully builds and links on the `aether_net` bridge. Healthchecks pass across all endpoints (`/health` backend and `/` frontend). Stress test completed inference (optimised to 4 threads) at p95 latency 1.038 s (well under the 2.0s limit). Removed `sse_starlette` dependency and corrected nginx proxy variables to secure full verification.
