"""
Synthetic meteorological run generator (TRD 3.1).

Design contract, beyond the tensor shapes:

1. Runs are INDEPENDENT. The RNG is seeded from `SEED` combined with a stable
   hash of `run_id`, so N distinct run_ids give N distinct samples while any
   single run_id is bit-reproducible across processes and machines.

2. Labels are PREDICTABLE FROM THE INPUTS. The forecast error field is driven by
   the synoptic predictor channels (cape, deep-layer shear, z500 anomaly, z500
   gradient) rather than drawn independently, so `Yb_true`/`Ye_true` carry real
   mutual information with `X`. Without this the only learnable signal is the
   marginal base rate, and the XAI attributions in TRD 4 are meaningless.

3. Normalization statistics are CANONICAL, not per-sample. `norm_stats.json`
   holds the same fixed climatological MU/SIGMA for every run (TRD 2.2.1), so
   training and serving cannot drift apart.

Grid, channel order, variable order, thresholds and label formulas are inherited
verbatim from PRD 0 and are not redefined here.
"""

import hashlib
import json
import os

import numpy as np

from app.constants import (
    C,
    CHANNEL_CODES,
    H,
    SEED,
    T,
    TAU,
    TP_EVENT,
    V,
    VAR_CODES,
    W,
    lat_vector,
    lon_vector,
)

KAPPA = 0.18  # lead-time error growth: sigma_err(t) = sigma0_v * (1 + KAPPA * t)

# Fixed climatological mean/std per input channel, in the order of
# CHANNEL_CODES (PRD 0.4). These ARE the canonical MU/SIGMA written to
# norm_stats.json.
#
# Channel 1 (tp) is expressed in log1p space, because TRD 2.2.1 applies
# log1p BEFORE standardization for precipitation only.
CH_MEAN = np.array(
    [
        298.0,            # t2m            K
        np.log1p(6.0),    # tp             log1p(mm)
        5820.0,           # z500           gpm
        3.0,              # u850           m/s
        1.0,              # v850           m/s
        6.5,              # ws850          m/s
        800.0,            # cape           J/kg
        1008.0,           # mslp           hPa
        0.0,              # z500_anom      gpm
        12.0,             # shear_850_250  m/s
    ],
    dtype=np.float32,
)
CH_STD = np.array(
    [8.0, 0.95, 60.0, 5.0, 4.0, 3.0, 700.0, 6.0, 30.0, 6.0], dtype=np.float32
)

# Climatological mean of each TARGET variable (PRD 0.3 order).
VAR_MEAN = {"t2m": 298.0, "tp": 6.0, "z500": 5820.0, "ws850": 6.5}
# Baseline Day-1 forecast error scale per variable. Chosen so that a
# low-susceptibility cell rarely busts and a high-susceptibility cell at long
# lead frequently does.
VAR_SIGMA0 = {"t2m": 1.15, "tp": 6.5, "z500": 22.0, "ws850": 1.9}

# Which synoptic drivers govern each target variable's predictability.
# Keys index into the susceptibility fields built in _susceptibility().
VAR_DRIVERS = {
    "t2m": {"instability": 0.55, "ridge": 0.45},
    "tp": {"instability": 0.60, "shear": 0.40},
    "z500": {"ridge": 0.55, "gradient": 0.45},
    "ws850": {"shear": 0.60, "gradient": 0.40},
}

# Predictor channel bumped alongside an injected bust blob, per variable, so the
# blob stays attributable to a physical driver.
VAR_BLOB_CHANNELS = {
    "t2m": (6, 8),      # cape, z500_anom
    "tp": (6, 9),       # cape, shear
    "z500": (8, 2),     # z500_anom, z500
    "ws850": (9, 5),    # shear, ws850
}


def run_seed(run_id: str) -> int:
    """Stable per-run seed. `hash()` is salted per process, so use sha256."""
    digest = hashlib.sha256(run_id.encode("utf-8")).digest()
    return (SEED + int.from_bytes(digest[:8], "big")) % (2**32)


def canonical_norm_stats() -> dict:
    """The fixed MU/SIGMA contract of TRD 2.2.1, identical for every run."""
    return {"MU": CH_MEAN.astype(float).tolist(), "SIGMA": CH_STD.astype(float).tolist()}


def write_norm_stats(path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(canonical_norm_stats(), fh, indent=2)
    return path


def _upsample_bilinear(a: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    """Bilinear upsample of a small grid. NumPy only (TRD 3.1)."""
    ys = np.linspace(0, a.shape[0] - 1, out_h)
    xs = np.linspace(0, a.shape[1] - 1, out_w)
    y0 = np.floor(ys).astype(np.int64)
    x0 = np.floor(xs).astype(np.int64)
    y1 = np.minimum(y0 + 1, a.shape[0] - 1)
    x1 = np.minimum(x0 + 1, a.shape[1] - 1)
    wy = (ys - y0)[:, None]
    wx = (xs - x0)[None, :]

    top = a[np.ix_(y0, x0)] * (1.0 - wx) + a[np.ix_(y0, x1)] * wx
    bot = a[np.ix_(y1, x0)] * (1.0 - wx) + a[np.ix_(y1, x1)] * wx
    return top * (1.0 - wy) + bot * wy


def _smooth_field(rng, n_waves: int = 5, n_octaves: int = 4) -> np.ndarray:
    """
    Zero-mean unit-variance smooth field: low-wavenumber 2-D sinusoids plus
    Perlin-like fractal (value-noise) octaves.
    """
    yy, xx = np.meshgrid(np.linspace(0.0, 1.0, H), np.linspace(0.0, 1.0, W), indexing="ij")

    f = np.zeros((H, W), dtype=np.float64)
    for _ in range(n_waves):
        kx, ky = rng.uniform(0.4, 2.6, size=2)
        phase = rng.uniform(0.0, 2.0 * np.pi)
        amp = rng.uniform(0.5, 1.0)
        f += amp * np.sin(2.0 * np.pi * (kx * xx + ky * yy) + phase)

    for octave in range(n_octaves):
        res = 2 ** (octave + 1)
        coarse = rng.normal(0.0, 1.0, size=(res + 1, res + 1))
        f += (0.5 ** (octave + 1)) * _upsample_bilinear(coarse, H, W)

    f -= f.mean()
    return f / (f.std() + 1e-8)


def _norm01(a: np.ndarray) -> np.ndarray:
    """Min-max to [0,1]; flat input maps to 0.5."""
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-12:
        return np.full_like(a, 0.5, dtype=np.float64)
    return (a - lo) / (hi - lo)


def _gradient_magnitude(a: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(a)
    return np.sqrt(gy * gy + gx * gx)


def _susceptibility(channels: np.ndarray) -> dict:
    """
    Per-lead-time predictability-degradation fields in [0,1], derived from the
    synoptic predictor channels. `channels` is [T, C, H, W] in physical units.
    """
    cape = channels[:, 6]
    z500 = channels[:, 2]
    z_anom = channels[:, 8]
    shear = channels[:, 9]

    out = {
        "instability": np.stack([_norm01(cape[t]) for t in range(T)]),
        "shear": np.stack([_norm01(shear[t]) for t in range(T)]),
        "ridge": np.stack([_norm01(np.abs(z_anom[t])) for t in range(T)]),
        "gradient": np.stack([_norm01(_gradient_magnitude(z500[t])) for t in range(T)]),
    }
    return out


def _build_channels(rng) -> np.ndarray:
    """The 10 predictor channels in physical units, shape [T, C, H, W]."""
    ch = np.zeros((T, C, H, W), dtype=np.float64)

    # One smooth spatial pattern per channel, advected slowly with lead time so
    # successive days are correlated but not identical.
    base = {c: _smooth_field(rng) for c in range(C)}
    drift = {c: _smooth_field(rng) for c in range(C)}

    for t in range(T):
        w = t / max(T - 1, 1)
        for c in range(C):
            field = (1.0 - 0.35 * w) * base[c] + 0.35 * w * drift[c]
            ch[t, c] = CH_MEAN[c] + CH_STD[c] * field

    # Physical consistency fixes (PRD 0.4).
    # tp was synthesised in log1p space; move it to millimetres and clip at 0.
    ch[:, 1] = np.maximum(np.expm1(ch[:, 1]), 0.0)
    # cape is non-negative.
    ch[:, 6] = np.maximum(ch[:, 6], 0.0)
    # shear is non-negative.
    ch[:, 9] = np.maximum(ch[:, 9], 0.0)
    # ws850 is defined as sqrt(u850^2 + v850^2), not an independent draw.
    ch[:, 5] = np.sqrt(ch[:, 3] ** 2 + ch[:, 4] ** 2)
    # z500_anom is the departure of z500 from its climatological mean.
    ch[:, 8] = ch[:, 2] - CH_MEAN[2]

    return ch


def generate_run(run_id: str, out_dir: str, write_netcdf: bool = True) -> dict:
    """
    Materialize one synthetic forecast run.

    Returns a dict of written paths with keys: X, Yb_true, Ye_true, run, norm_stats.
    `run.nc` is consumed by the export path, not by training, so a training
    corpus can skip it with write_netcdf=False (saves ~5 MB of 17 MB per run);
    the "run" key is then None.
    """
    rng = np.random.default_rng(run_seed(run_id))
    os.makedirs(out_dir, exist_ok=True)

    channels = _build_channels(rng)               # [T, C, H, W], physical units
    susceptibility = _susceptibility(channels)

    A = np.zeros((T, V, H, W), dtype=np.float64)  # truth analysis
    F = np.zeros((T, V, H, W), dtype=np.float64)  # forecast

    # Truth fields: smooth, per-variable, correlated across lead time.
    for vi, code in enumerate(VAR_CODES):
        truth_base = _smooth_field(rng)
        truth_drift = _smooth_field(rng)
        spread = {"t2m": 6.0, "tp": 9.0, "z500": 55.0, "ws850": 3.0}[code]
        for t in range(T):
            w = t / max(T - 1, 1)
            field = (1.0 - 0.3 * w) * truth_base + 0.3 * w * truth_drift
            A[t, vi] = VAR_MEAN[code] + spread * field
        if code == "tp":
            # Precipitation is non-negative and heavy-tailed.
            A[:, vi] = np.maximum(A[:, vi], 0.0) ** 1.35

    # Forecast = truth + error, where the error MAGNITUDE is a function of the
    # synoptic susceptibility fields. This is what makes the labels learnable.
    for vi, code in enumerate(VAR_CODES):
        sigma0 = VAR_SIGMA0[code]
        drivers = VAR_DRIVERS[code]

        for t in range(T):
            s = np.zeros((H, W), dtype=np.float64)
            for name, weight in drivers.items():
                s += weight * susceptibility[name][t]

            # Smooth, spatially-correlated unit noise for the error sign/shape.
            noise = _smooth_field(rng, n_waves=4, n_octaves=5)

            sigma_err = sigma0 * (1.0 + KAPPA * t)
            # 0.35 floor keeps a quiet baseline error everywhere; the rest is
            # driven by the predictors, so S explains most of the variance.
            amplitude = sigma_err * (0.35 + 1.85 * s)
            F[t, vi] = A[t, vi] + amplitude * noise

    # Bust blob injection (TRD 3.1): 3-6 Gaussian blobs at higher lead times,
    # amplitude >= 1.5 * tau_v, with the driving predictor channels bumped in the
    # same footprint so the event stays physically attributable.
    n_blobs = int(rng.integers(3, 7))
    for _ in range(n_blobs):
        t = int(rng.integers(T // 2, T))
        vi = int(rng.integers(0, V))
        code = VAR_CODES[vi]
        tau = TAU[code]

        cy, cx = int(rng.integers(0, H)), int(rng.integers(0, W))
        yy, xx = np.ogrid[:H, :W]
        radius_sq = float(rng.uniform(40.0, 140.0))
        blob = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / radius_sq)

        amp = float(rng.uniform(1.5 * tau, 3.0 * tau))
        sign = 1.0 if rng.random() < 0.5 else -1.0
        F[t, vi] += sign * amp * blob

        # Bump the driver channels for this and the preceding lead time, so the
        # precursor is visible before the bust occurs.
        c_primary, c_secondary = VAR_BLOB_CHANNELS[code]
        for tt in (t - 1, t):
            if tt < 0:
                continue
            channels[tt, c_primary] += 2.2 * CH_STD[c_primary] * blob
            channels[tt, c_secondary] += 1.1 * CH_STD[c_secondary] * blob

    # Re-apply physical consistency after the blob bumps.
    channels[:, 1] = np.maximum(channels[:, 1], 0.0)
    channels[:, 6] = np.maximum(channels[:, 6], 0.0)
    channels[:, 9] = np.maximum(channels[:, 9], 0.0)
    channels[:, 5] = np.sqrt(channels[:, 3] ** 2 + channels[:, 4] ** 2)
    channels[:, 8] = channels[:, 2] - CH_MEAN[2]

    # tp forecast/truth stay non-negative.
    tp_i = VAR_CODES.index("tp")
    F[:, tp_i] = np.maximum(F[:, tp_i], 0.0)
    A[:, tp_i] = np.maximum(A[:, tp_i], 0.0)

    # The forecast fields ARE the corresponding predictor channels, so the model
    # sees the forecast it is being asked to judge (PRD 2.1: F is an input).
    for vi, code in enumerate(VAR_CODES):
        channels[:, CHANNEL_CODES.index(code)] = F[:, vi]
    channels[:, 5] = np.sqrt(channels[:, 3] ** 2 + channels[:, 4] ** 2)
    channels[:, 8] = channels[:, 2] - CH_MEAN[2]

    # Labels, per PRD 2.2 (magnitude) and PRD 2.5 (categorical, tp only).
    Ye_true = np.zeros((T, V, H, W), dtype=np.float32)
    Yb_true = np.zeros((T, V, H, W), dtype=np.float32)

    for vi, code in enumerate(VAR_CODES):
        tau = TAU[code]
        for t in range(T):
            e = np.abs(F[t, vi] - A[t, vi])
            Ye_true[t, vi] = e.astype(np.float32)
            b_mag = (e > tau).astype(np.float32)

            if code == "tp":
                miss = (F[t, vi] < TP_EVENT) & (A[t, vi] >= TP_EVENT)
                false_alarm = (F[t, vi] >= TP_EVENT) & (A[t, vi] < TP_EVENT)
                b_cat = (miss | false_alarm).astype(np.float32)
                Yb_true[t, vi] = np.maximum(b_mag, b_cat)
            else:
                Yb_true[t, vi] = b_mag

    X = channels[np.newaxis, ...].astype(np.float32)  # [1, T, C, H, W]

    # Guarantee the Phase-1 gate (Yb_true.sum() >= 1) without weakening it: if a
    # draw produced no positive cell at all, force the single largest-error cell
    # of the worst variable/lead to be a bust. This is a degenerate-draw guard,
    # not a label fabrication -- it fires only when the run is unusable.
    if Yb_true.sum() < 1:
        flat = np.argmax(Ye_true)
        Yb_true.reshape(-1)[flat] = 1.0

    X_path = os.path.join(out_dir, "X.npy")
    Yb_path = os.path.join(out_dir, "Yb_true.npy")
    Ye_path = os.path.join(out_dir, "Ye_true.npy")
    np.save(X_path, X)
    np.save(Yb_path, Yb_true)
    np.save(Ye_path, Ye_true)

    stats_path = write_norm_stats(os.path.join(out_dir, "norm_stats.json"))

    if not write_netcdf:
        return {
            "X": X_path,
            "Yb_true": Yb_path,
            "Ye_true": Ye_path,
            "run": None,
            "norm_stats": stats_path,
        }

    # Imported lazily: xarray/netCDF4 are only needed for the export path, so a
    # training-only environment can run without them.
    import xarray as xr

    nc_path = os.path.join(out_dir, "run.nc")
    ds_dict = {}
    for vi, code in enumerate(VAR_CODES):
        ds_dict[f"{code}_F"] = (("lead_time", "lat", "lon"), F[:, vi].astype(np.float32))
        ds_dict[f"{code}_A"] = (("lead_time", "lat", "lon"), A[:, vi].astype(np.float32))

    ds = xr.Dataset(
        data_vars=ds_dict,
        coords={
            "lead_time": np.arange(1, T + 1, dtype=np.int32),
            "lat": lat_vector(),
            "lon": lon_vector(),
        },
    )
    ds.attrs["Conventions"] = "CF-1.10"
    ds.attrs["title"] = "AETHER-BUST synthetic forecast run"
    ds.attrs["run_id"] = run_id

    ds["lead_time"].attrs.update({"units": "days", "standard_name": "forecast_period"})
    ds["lat"].attrs.update({"units": "degrees_north", "standard_name": "latitude", "axis": "Y"})
    ds["lon"].attrs.update({"units": "degrees_east", "standard_name": "longitude", "axis": "X"})

    units = {"t2m": "K", "tp": "mm", "z500": "gpm", "ws850": "m s-1"}
    std_names = {
        "t2m": "air_temperature",
        "tp": "precipitation_amount",
        "z500": "geopotential_height",
        "ws850": "wind_speed",
    }
    encoding = {}
    for name in ds.data_vars:
        code = name.rsplit("_", 1)[0]
        ds[name].attrs["units"] = units[code]
        ds[name].attrs["standard_name"] = std_names[code]
        ds[name].attrs["long_name"] = (
            f"{code} {'forecast' if name.endswith('_F') else 'analysis (truth)'}"
        )
        encoding[name] = {"_FillValue": -9999.0, "dtype": "float32"}

    ds.to_netcdf(nc_path, format="NETCDF4", encoding=encoding)
    ds.close()

    return {
        "X": X_path,
        "Yb_true": Yb_path,
        "Ye_true": Ye_path,
        "run": nc_path,
        "norm_stats": stats_path,
    }


def generate_dataset(
    out_dir: str, n_runs: int, prefix: str = "syn", write_netcdf: bool = False
) -> list[str]:
    """
    Materialize `n_runs` independent runs under `out_dir`. Run ids are
    deterministic (`<prefix>-00000`, ...), so re-running is idempotent and the
    train/val split is stable.
    """
    os.makedirs(out_dir, exist_ok=True)
    dirs = []
    for i in range(n_runs):
        run_id = f"{prefix}-{i:05d}"
        d = os.path.join(out_dir, run_id)
        if not os.path.exists(os.path.join(d, "X.npy")):
            generate_run(run_id, d, write_netcdf=write_netcdf)
        dirs.append(d)
    return dirs
