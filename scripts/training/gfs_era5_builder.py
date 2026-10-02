import os
import json
import argparse
import datetime
from pathlib import Path

import numpy as np
import xarray as xr

import sys
backend_path = str(Path(__file__).resolve().parents[2] / "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.constants import (
    VAR_CODES, CHANNEL_CODES, TAU,
    PHI_MIN, PHI_MAX, LAMBDA_MIN, LAMBDA_MAX,
    H, W, T, C, V
)

def get_era5_24h_precip(era5_file: Path, valid_time: datetime.datetime):
    # ERA5 24h block spans two calendar days (13:00 to 12:00)
    start_time = valid_time - datetime.timedelta(hours=23)
    files_to_open = [era5_file]
    
    if start_time.month != valid_time.month:
        prev_file = era5_file.parent / f"era5_india_sl_{start_time.strftime('%Y_%m')}.nc"
        if prev_file.exists():
            files_to_open.insert(0, prev_file)
        
    ds1 = xr.open_dataset(files_to_open[0])
    if len(files_to_open) == 2:
        ds2 = xr.open_dataset(files_to_open[1])
        da = xr.concat([ds1['tp'], ds2['tp']], dim='time')
    else:
        da = ds1['tp']
    start_time = valid_time - datetime.timedelta(hours=23)
    
    da_24h = da.sel(time=slice(start_time, valid_time))
    if len(da_24h.time) != 24:
        raise ValueError(f"Could not extract exactly 24 hours ending at {valid_time} from {files_to_open}. Got {len(da_24h.time)} steps.")
        
    tp_24h = da_24h.sum(dim='time')
    
    # Convert to mm if necessary
    if tp_24h.max() < 2.0 and tp_24h.max() > 0:
        tp_24h = tp_24h * 1000.0
        
    interval_str = f"{start_time.strftime('%Y-%m-%dT%H')} to {valid_time.strftime('%Y-%m-%dT%H')}"
    return tp_24h, interval_str

def get_gfs_24h_precip(init_date: datetime.datetime, target_lead: int, gfs_dir: Path):
    """
    Dynamically determines GFS accumulation semantics by inspecting the GRIB2 metadata.
    If 'tp' is a 6-hour bucket (GRIB_stepRange='18-24'), it automatically loads
    and sums the 4 consecutive 6-hour forecast files.
    """
    # Load target forecast
    target_file = gfs_dir / f"gfs_india_{init_date.strftime('%Y%m%d')}_12z_f{target_lead:03d}.grib2"
    if not target_file.exists():
        raise FileNotFoundError(f"Missing GFS {target_file.name}")
        
    ds_target = xr.open_dataset(
        target_file, 
        engine="cfgrib", 
        backend_kwargs={
            "filter_by_keys": {"typeOfLevel": "surface", "stepType": "accum"}
        }
    )
    if 'tp' not in ds_target:
        return ds_target['t2m'] * 0.0, "Missing tp", 0.0  # Fallback zero if no precip in model
        
    tp_da = ds_target['tp']
    
    # Inspect stepRange
    step_range = tp_da.attrs.get('GRIB_stepRange', '')
    
    if step_range == f"{target_lead-24}-{target_lead}":
        # It's already a 24-hour accumulation
        interval_str = f"f{target_lead-24:03d} - f{target_lead:03d} (Native 24h)"
        tp_24h = tp_da
    elif step_range == f"{target_lead-6}-{target_lead}":
        # It's a 6-hour accumulation bucket. We must sum 4 files.
        tp_24h = tp_da
        interval_str = f"f{target_lead-24:03d} - f{target_lead:03d} (Sum of four 6h buckets: "
        bucket_strs = [f"{target_lead-6}-{target_lead}"]
        for offset in [6, 12, 18]:
            lead = target_lead - offset
            f_path = gfs_dir / f"gfs_india_{init_date.strftime('%Y%m%d')}_12z_f{lead:03d}.grib2"
            if not f_path.exists():
                raise FileNotFoundError(f"Missing intermediate GFS for 6h bucket sum: {f_path.name}")
            ds_int = xr.open_dataset(
                f_path, 
                engine="cfgrib",
                backend_kwargs={
                    "filter_by_keys": {"typeOfLevel": "surface", "stepType": "accum"}
                }
            )
            tp_24h = tp_24h + ds_int['tp']
            bucket_strs.append(ds_int['tp'].attrs.get('GRIB_stepRange', f"{lead-6}-{lead}"))
            ds_int.close()
        interval_str += ", ".join(reversed(bucket_strs)) + ")"
    elif step_range == f"{target_lead-12}-{target_lead}":
        # 12-hour accumulation bucket
        tp_24h = tp_da
        interval_str = f"f{target_lead-24:03d} - f{target_lead:03d} (Sum of two 12h buckets)"
        lead = target_lead - 12
        f_path = gfs_dir / f"gfs_india_{init_date.strftime('%Y%m%d')}_12z_f{lead:03d}.grib2"
        ds_int = xr.open_dataset(
            f_path, 
            engine="cfgrib",
            backend_kwargs={
                "filter_by_keys": {"typeOfLevel": "surface", "stepType": "accum"}
            }
        )
        tp_24h = tp_24h + ds_int['tp']
        ds_int.close()
    elif step_range == f"0-{target_lead}":
        # Cumulative from init. We subtract the 24h prior.
        if target_lead == 24:
            tp_24h = tp_da
            interval_str = f"f000 - f024 (Native 24h cumulative)"
        else:
            prev_lead = target_lead - 24
            f_path = gfs_dir / f"gfs_india_{init_date.strftime('%Y%m%d')}_12z_f{prev_lead:03d}.grib2"
            ds_prev = xr.open_dataset(
                f_path, 
                engine="cfgrib",
                backend_kwargs={
                    "filter_by_keys": {"typeOfLevel": "surface", "stepType": "accum"}
                }
            )
            tp_24h = tp_da - ds_prev['tp']
            ds_prev.close()
            interval_str = f"f000-f{target_lead:03d} MINUS f000-f{prev_lead:03d} (Subtraction)"
    else:
        # Fallback assuming it's a simulated or unified netcdf
        tp_24h = tp_da
        interval_str = f"f{target_lead-24:03d} - f{target_lead:03d} (Assumed single file 24h based on '{step_range}')"
        
    ds_target.close()
    
    if tp_24h.max() < 2.0 and tp_24h.max() > 0: 
        tp_24h = tp_24h * 1000.0
        
    return tp_24h, interval_str, tp_24h.mean().values

def extract_field(datasets, var_name, level=None):
    if not isinstance(datasets, list):
        datasets = [datasets]
        
    for ds in datasets:
        if var_name in ds:
            da = ds[var_name]
            if level:
                dim = [d for d in da.dims if 'isobaric' in d.lower() or 'level' in d.lower()]
                if not dim:
                    continue
                da = da.sel({dim[0]: level}, method='nearest')
            return da
            
    raise KeyError(f"Missing {var_name}")

def process_initialization(init_date: datetime.datetime, gfs_dir: Path, era5_dir: Path, out_dir: Path):
    x_sequence = np.zeros((T, C, H, W), dtype=np.float32)
    yb_sequence = np.zeros((T, V, H, W), dtype=np.float32)
    ye_sequence = np.zeros((T, V, H, W), dtype=np.float32)
    
    with open(Path(backend_path) / "app" / "ml" / "norm_stats.json", "r") as f:
        norm_stats = json.load(f)
    mu, sigma = np.array(norm_stats["MU"], dtype=np.float32), np.array(norm_stats["SIGMA"], dtype=np.float32)
    
    log_report = []
    
    for lead_idx in range(T):
        target_lead = (lead_idx + 1) * 24
        valid_date = init_date + datetime.timedelta(hours=target_lead)
        
        # 1. GFS Processing (including dynamic 24h precipitation)
        gfs_tp_24h, gfs_tp_interval, gfs_tp_mean = get_gfs_24h_precip(init_date, target_lead, gfs_dir)
        
        gfs_file = gfs_dir / f"gfs_india_{init_date.strftime('%Y%m%d')}_12z_f{target_lead:03d}.grib2"
        import cfgrib
        ds_gfs = cfgrib.open_datasets(str(gfs_file))
        
        t2m = extract_field(ds_gfs, "t2m")
        z500 = extract_field(ds_gfs, "gh", 500)
        u850 = extract_field(ds_gfs, "u", 850)
        v850 = extract_field(ds_gfs, "v", 850)
        u250 = extract_field(ds_gfs, "u", 250)
        v250 = extract_field(ds_gfs, "v", 250)
        cape = extract_field(ds_gfs, "cape")
        
        # Mean sea level pressure can be msl or prmsl
        try:
            mslp = extract_field(ds_gfs, "msl")
        except KeyError:
            mslp = extract_field(ds_gfs, "prmsl")
        
        ws850 = np.sqrt(u850**2 + v850**2)
        shear = np.sqrt((u250 - u850)**2 + (v250 - v850)**2)
        mslp_hpa = mslp / 100.0 if mslp.mean() > 2000 else mslp
        z500_anom = z500 - mu[2]
        
        channels = [t2m, gfs_tp_24h, z500, u850, v850, ws850, cape, mslp_hpa, z500_anom, shear]
        for ci in range(C):
            x_sequence[lead_idx, ci] = channels[ci].values
            
        # 2. ERA5 Processing (24h continuous precipitation)
        era5_file = era5_dir / f"era5_india_sl_{valid_date.strftime('%Y_%m')}.nc"
        era5_tp_24h, era5_tp_interval = get_era5_24h_precip(era5_file, valid_date)
        
        ds_era5 = xr.open_dataset(era5_file).sel(time=valid_date) # instantaneous fields at valid_time
        era_t2m = extract_field(ds_era5, "t2m")
        era_z500 = extract_field(ds_era5, "z", 500) / 9.80665
        era_u850 = extract_field(ds_era5, "u", 850)
        era_v850 = extract_field(ds_era5, "v", 850)
        era_ws850 = np.sqrt(era_u850**2 + era_v850**2)
        
        era_targets = [era_t2m, era5_tp_24h, era_z500, era_ws850]
        
        # 3. Target Generation
        for vi, code in enumerate(VAR_CODES):
            F = channels[vi].values
            A = era_targets[vi].values
            Ye = np.abs(F - A)
            ye_sequence[lead_idx, vi] = Ye
            
            if code == "tp":
                Yb = (Ye > 20.0) | ((F >= 20.0) & (A < 20.0)) | ((F < 20.0) & (A >= 20.0))
            else:
                Yb = Ye > TAU[code]
            yb_sequence[lead_idx, vi] = Yb.astype(np.float32)
            
        ds_gfs.close()
        
        log_report.append(f"  Lead: Day {lead_idx+1} | Valid: {valid_date.strftime('%Y-%m-%d %H:%M')}")
        log_report.append(f"    GFS  tp src: {gfs_tp_interval} -> Mean: {gfs_tp_mean:.2f} mm")
        log_report.append(f"    ERA5 tp src: {era5_tp_interval} -> Mean: {float(era5_tp_24h.mean()):.2f} mm")

    # 4. Final Application-side Normalization
    tp_idx = CHANNEL_CODES.index("tp")
    x_sequence[:, tp_idx] = np.log1p(np.maximum(x_sequence[:, tp_idx], 0.0))
    x_sequence = (x_sequence - mu.reshape(1, C, 1, 1)) / sigma.reshape(1, C, 1, 1)
    
    run_id = f"real_{init_date.strftime('%Y%m%d')}"
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    np.save(run_dir / "X.npy", x_sequence)
    np.save(run_dir / "Yb_true.npy", yb_sequence)
    np.save(run_dir / "Ye_true.npy", ye_sequence)
    
    return True, run_id, log_report
