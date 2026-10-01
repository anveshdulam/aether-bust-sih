import datetime
import numpy as np
import xarray as xr
from pathlib import Path
import os
import sys

backend_path = str(Path(__file__).resolve().parents[2] / "backend")
import sys
sys.path.append(str(Path(__file__).resolve().parent))
from gfs_era5_builder import process_initialization

def generate_mock_precipitation_metadata_data(start_date, end_date, gfs_dir, era5_dir):
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").replace(hour=12)
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=12)
    
    Path(gfs_dir).mkdir(parents=True, exist_ok=True)
    Path(era5_dir).mkdir(parents=True, exist_ok=True)
    
    lat = np.linspace(37.75, 6.0, 128, dtype=np.float32)
    lon = np.linspace(68.0, 99.75, 128, dtype=np.float32)
    base_shape = (128, 128)
    
    # 1. Generate GFS with 6-hour stepRange metadata to test bucket summation
    curr = start_dt
    while curr <= end_dt:
        # We generate every 6 hours out to 240 to allow summation!
        for lead in range(6, 246, 6):
            gfs_file = Path(gfs_dir) / f"gfs_{curr.strftime('%Y%m%d')}_12z_f{lead:03d}.nc"
            ds = xr.Dataset(coords={"latitude": lat, "longitude": lon, "level_850": [850], "level_500": [500], "level_250": [250]})
            ds["t2m"] = (("latitude", "longitude"), np.ones(base_shape, dtype=np.float32) * 290.0)
            
            # 6-hour precip bucket of ~1.5mm
            precip = np.random.rand(*base_shape).astype(np.float32) * 3.0
            da_precip = xr.DataArray(precip, dims=["latitude", "longitude"])
            da_precip.attrs["GRIB_stepType"] = "accum"
            da_precip.attrs["GRIB_stepRange"] = f"{lead-6}-{lead}"
            ds["tp"] = da_precip
            
            ds["gh"] = (("level_500", "latitude", "longitude"), np.ones((1,128,128), dtype=np.float32) * 5800.0)
            ds["u"] = xr.DataArray(np.random.rand(3, 128, 128).astype(np.float32), coords={"level": [850, 500, 250], "latitude": lat, "longitude": lon}, dims=("level", "latitude", "longitude"))
            ds["v"] = xr.DataArray(np.random.rand(3, 128, 128).astype(np.float32), coords={"level": [850, 500, 250], "latitude": lat, "longitude": lon}, dims=("level", "latitude", "longitude"))
            ds["cape"] = (("latitude", "longitude"), np.random.rand(*base_shape).astype(np.float32) * 1000.0)
            ds["msl"] = (("latitude", "longitude"), np.ones(base_shape, dtype=np.float32) * 101325.0)
            ds.to_netcdf(gfs_file)
        curr += datetime.timedelta(days=1)
        
    # 2. Generate ERA5 with full 24-hour time dimensions per day
    curr = start_dt - datetime.timedelta(days=1) # Need previous day for overlapping 24h windows
    max_valid = end_dt + datetime.timedelta(days=11)
    
    while curr <= max_valid:
        era5_file = Path(era5_dir) / f"era5_{curr.strftime('%Y%m%d')}.nc"
        # Create 24 hours from 00:00 to 23:00 for this day
        times = [curr.replace(hour=0) + datetime.timedelta(hours=i) for i in range(24)]
        ds = xr.Dataset(coords={"time": times, "latitude": lat, "longitude": lon, "level_850": [850], "level_500": [500]})
        
        # Hourly precip of ~0.25mm
        ds["tp"] = (("time", "latitude", "longitude"), np.random.rand(24, 128, 128).astype(np.float32) * 0.5)
        ds["t2m"] = (("time", "latitude", "longitude"), np.ones((24, 128, 128), dtype=np.float32) * 290.5)
        ds["z"] = (("time", "level_500", "latitude", "longitude"), np.ones((24, 1, 128, 128), dtype=np.float32) * (5805.0 * 9.80665))
        ds["u"] = (("time", "level_850", "latitude", "longitude"), np.random.rand(24, 1, 128, 128).astype(np.float32))
        ds["v"] = (("time", "level_850", "latitude", "longitude"), np.random.rand(24, 1, 128, 128).astype(np.float32))
        ds.to_netcdf(era5_file)
        curr += datetime.timedelta(days=1)
        
    print("Generated mock data WITH 6-HOUR GFS BUCKETS and 24-HOUR ERA5 SERIES.")

def run_revalidation():
    print("="*60)
    print("CRITICAL SANITY CHECK: PRECIPITATION SEMANTICS")
    print("="*60)
    
    init_date = datetime.datetime(2023, 1, 1, 12, 0)
    success, run_id, log_report = process_initialization(
        init_date, Path("data/mock_gfs2"), Path("data/mock_era52"), Path("data/processed2")
    )
    
    print(f"Initialization: {init_date.strftime('%Y-%m-%d %H:%M')}")
    for line in log_report:
        print(line)
        
    print("\n="*60)
    print("TENSOR SHAPE & LABEL VALIDATION")
    print("="*60)
    
    X = np.load(Path(f"data/processed2/{run_id}/X.npy"))
    Yb = np.load(Path(f"data/processed2/{run_id}/Yb_true.npy"))
    Ye = np.load(Path(f"data/processed2/{run_id}/Ye_true.npy"))
    
    print(f"X shape      : {X.shape} (Expected: 10, 10, 128, 128)")
    print(f"Yb_true shape: {Yb.shape} (Expected: 10, 4, 128, 128)")
    print(f"Ye_true shape: {Ye.shape} (Expected: 10, 4, 128, 128)")
    
    print(f"\nNaN count: {np.isnan(X).sum()}")
    print(f"Inf count: {np.isinf(X).sum()}")
    
    print("\n[LABEL STATISTICS]")
    codes = ["t2m", "tp", "z500", "ws850"]
    ye_mean = Ye.mean(axis=(0,2,3))
    yb_rate = Yb.mean(axis=(0,2,3)) * 100
    
    print(f"{'Var':<6} | {'Mean Ye':<8} | {'Bust Rate (Yb)':<15}")
    for i in range(4):
        print(f"{codes[i]:<6} | {ye_mean[i]:8.2f} | {yb_rate[i]:6.2f}%")

if __name__ == "__main__":
    generate_mock_precipitation_metadata_data("2023-01-01", "2023-01-01", "data/mock_gfs2", "data/mock_era52")
    run_revalidation()
