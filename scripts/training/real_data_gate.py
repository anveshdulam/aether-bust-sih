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
sys.path.append(str(Path(__file__).resolve().parent))

from app.constants import (
    VAR_CODES, CHANNEL_CODES, TAU,
    PHI_MIN, PHI_MAX, LAMBDA_MIN, LAMBDA_MAX,
    H, W, T, C, V
)
from gfs_era5_builder import get_gfs_24h_precip, get_era5_24h_precip, extract_field

def run_real_data_gate(init_date: datetime.datetime, gfs_dir: Path, era5_dir: Path):
    print("============================================================")
    print("REAL-DATA GATE: METADATA & SEMANTICS INSPECTION")
    print("============================================================")
    
    with open(Path(backend_path) / "app" / "ml" / "norm_stats.json", "r") as f:
        norm_stats = json.load(f)
    mu, sigma = np.array(norm_stats["MU"], dtype=np.float32), np.array(norm_stats["SIGMA"], dtype=np.float32)

    x_sequence = np.zeros((T, C, H, W), dtype=np.float32)
    yb_sequence = np.zeros((T, V, H, W), dtype=np.float32)
    ye_sequence = np.zeros((T, V, H, W), dtype=np.float32)
    
    total_nans = 0
    total_infs = 0
    
    for lead_idx in range(T):
        target_lead = (lead_idx + 1) * 24
        valid_date = init_date + datetime.timedelta(hours=target_lead)
        
        print(f"\n[LEAD DAY {lead_idx+1}]")
        print(f"  Init Time : {init_date.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  Valid Time: {valid_date.strftime('%Y-%m-%d %H:%M UTC')}")
        
        # --- GFS Precipitation ---
        gfs_tp_24h, gfs_tp_interval, gfs_tp_mean = get_gfs_24h_precip(init_date, target_lead, gfs_dir)
        print(f"  GFS Precipitation Source : {gfs_tp_interval}")
        print(f"  GFS 24h Total            : Mean {gfs_tp_mean:.2f} mm | Min {gfs_tp_24h.min().values:.2f} | Max {gfs_tp_24h.max().values:.2f}")
        
        # --- ERA5 Precipitation ---
        era5_file = era5_dir / f"era5_india_sl_{valid_date.strftime('%Y_%m')}.nc"
        # Adjusted for the specific filename structure available in the gate if it's monthly
        # If it's a monthly file, get_era5_24h_precip needs adjusting to slice correctly.
        try:
            era5_tp_24h, era5_tp_interval = get_era5_24h_precip(era5_file, valid_date)
            print(f"  ERA5 Precipitation Source: {era5_tp_interval}")
            print(f"  ERA5 24h Total           : Mean {era5_tp_24h.mean().values:.2f} mm | Min {era5_tp_24h.min().values:.2f} | Max {era5_tp_24h.max().values:.2f}")
        except Exception as e:
            print(f"  ERA5 Precipitation Source: FAILED ({e})")
            era5_tp_24h = None

        # Process instantaneous to verify bounds
        gfs_file = gfs_dir / f"gfs_india_{init_date.strftime('%Y%m%d')}_12z_f{target_lead:03d}.grib2"
        ds_gfs = xr.open_dataset(
            gfs_file, 
            engine="cfgrib",
            backend_kwargs={
                "filter_by_keys": {"typeOfLevel": "heightAboveGround", "stepType": "instant"},
                "indexpath": ""
            }
        )
        t2m = extract_field(ds_gfs, "t2m")
        
        print(f"  GFS Spatial Bounds       : Lat {float(t2m.latitude.min())} to {float(t2m.latitude.max())} | Lon {float(t2m.longitude.min())} to {float(t2m.longitude.max())}")
        print(f"  GFS Extracted Shape      : {t2m.shape}")
        ds_gfs.close()
        
    print("\n============================================================")
    print("GATE INSPECTION COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gfs-dir", required=True)
    parser.add_argument("--era5-dir", required=True)
    args = parser.parse_args()
    
    init_date = datetime.datetime(2023, 1, 1, 12, 0)
    run_real_data_gate(init_date, Path(args.gfs_dir), Path(args.era5_dir))
