# AETHER-BUST (SIH26079) — working notes

## Specs are authoritative; read them before changing behaviour

`plans/` holds the frozen contract: `PRD.md` (constants + bust math), `TRD.md` (stack,
tensor contract, API), `DB_SCHEMA.md` (collections, validators, indexes),
`UI_UX_DOC.md` (components, colour scales), `BUILD_PLAN.md` (phase gates).

Precedence when two documents disagree: **the numeric constants in `PRD.md` §0 win**;
otherwise the more specific document wins for its own domain (TRD for code, DB_SCHEMA
for data, UI_UX_DOC for frontend). Never invent a third option.

`plans/PHASE_LOG.md` is the source of truth for what has actually passed. Only append
to it after a phase's exact verification command exits 0.

## Hard prohibitions (BUILD_PLAN §1.1)

- **Never change the frozen constants** to make something pass: `H=W=128`, `T=10`,
  `C=10`, `V=4`, the `τ_v` thresholds, the `w_v` confidence weights, grid bounds, port
  numbers, `SEED=26079`.
- **Never weaken, skip, or xfail `tests/test_shapes.py`** or any `ShapeContractError`
  guard. The tensor contract is the project's central gate.
- **Never relax a test's asserted contract to get green.** Fix the code instead. The one
  exception: if a test contradicts a spec constant, repair the test *toward* the spec and
  record the correction in `PHASE_LOG.md`.
- **No placeholder code.** A bare `pass` body, `# TODO`, `NotImplementedError`, or a stub
  return is a violation — two of these were found already, hiding real bugs.
- **Never add a dependency** that is not pinned in `TRD.md` §1.1/§1.2.
- Don't advance to phase N+1 while phase N's gate is red.

## This machine's environment (differs from the spec's assumptions)

- **No Docker.** The Phase 3 verification script's `docker compose up -d mongo` is not
  runnable here. Phase 6 genuinely needs Docker Desktop installed.
- **MongoDB runs from a portable extract**, not a container:
  `.tools/mongodb-win32-x86_64-windows-7.0.11/bin/mongod.exe --dbpath .tools/mongo-data
  --port 27017 --bind_ip 127.0.0.1`. Start it in the background before any DB work.
- **No virtualenv.** Use the system Python 3.11 with `PYTHONPATH` set to `backend/`;
  `. .venv/bin/activate` in the spec is POSIX and does not apply on Windows/PowerShell.
- **Installed dependency versions drift above the `requirements.txt` pins** (torch 2.12
  vs 2.3.1, numpy 2.2.6 vs 1.26.4, xarray 2026.7 vs 2024.6, and others). The pins are
  unchanged and remain the declared contract — don't "fix" them to match what's local.

Run the backend suite with:
`PYTHONPATH=backend python -m pytest backend/tests -q` (from the project root).

## Gotchas that cost real debugging time

- **`masking.py` builds convex hulls from grid-cell *corners*** (centre ± `DELTA/2`), so a
  blob touching the domain edge yields coordinates half a cell outside the PRD §0.1
  bounds (67.875E, 5.875N). The API's constrained `Latitude`/`Longitude` types reject
  these. Clamp geometry to cell-centre bounds at any new serialization boundary.
- **In-memory tensors are south-up** (row 0 = 6.0°N). GeoJSON/GeoTIFF/API responses are
  north-up. Flip at the serialization boundary only, never in the tensors.
- **Integrated Gradients is memory-bound, not compute-bound.** Captum expands the input
  by `n_steps` over a `[1,10,10,128,128]` tensor while retaining the full U-Net
  activation stack for all 10 leads; the default `n_steps=50` aborts the interpreter.
  Keep `internal_batch_size=1` and a small step count.
- **motor binds to the running event loop.** pytest-asyncio 0.23 gives each test a fresh
  loop, so a session-scoped Mongo client fails with "attached to a different loop" on the
  second test. Create the client per test; keep the expensive model load session-scoped.
- **Connected-component extraction over all 40 (variable, lead) slices takes ~16 s.**
  Anything that calls it per request must be cached.

## Known open risk

Inference is ~8.3 s per run on this CPU; the PRD NFR is ≤ 2.0 s, and Phase 6's
`scripts/stress_test.py` is specified to assert p95 ≤ 2.0 s. This is an architecture-
vs-NFR conflict that needs a decision, not a silently loosened assertion.
