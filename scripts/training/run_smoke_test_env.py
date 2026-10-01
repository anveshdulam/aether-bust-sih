import os
import datetime
import xarray as xr
import numpy as np
from pathlib import Path

def generate_mock_data(start_date, end_date, gfs_dir, era5_dir):
    """
    Generates synthetic GFS and ERA5 NetCDF files for the smoke test.
    """
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").replace(hour=12)
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=12)
    
    gfs_dir = Path(gfs_dir)
    era5_dir = Path(era5_dir)
    gfs_dir.mkdir(parents=True, exist_ok=True)
    era5_dir.mkdir(parents=True, exist_ok=True)
    
    lat = np.linspace(37.75, 6.0, 128, dtype=np.float32)
    lon = np.linspace(68.0, 99.75, 128, dtype=np.float32)
    
    # We need to generate up to 10 days out from the end_date for GFS + ERA5
    max_valid_dt = end_dt + datetime.timedelta(days=10)
    
    # Helper to build a generic dataset
    def build_ds(is_gfs=True):
        ds = xr.Dataset(coords={"latitude": lat, "longitude": lon, "level_850": [850], "level_500": [500], "level_250": [250]})
        base_shape = (128, 128)
        base_shape_lvl = (1, 128, 128)
        
        if is_gfs:
            ds["t2m"] = (("latitude", "longitude"), np.ones(base_shape, dtype=np.float32) * 290.0)
            ds["tp"] = (("latitude", "longitude"), np.random.rand(*base_shape).astype(np.float32) * 5.0)
            ds["gh"] = (("level_500", "latitude", "longitude"), np.ones(base_shape_lvl, dtype=np.float32) * 5800.0)
            ds["u"] = xr.DataArray(np.random.rand(3, 128, 128).astype(np.float32), coords={"level": [850, 500, 250], "latitude": lat, "longitude": lon}, dims=("level", "latitude", "longitude"))
            ds["v"] = xr.DataArray(np.random.rand(3, 128, 128).astype(np.float32), coords={"level": [850, 500, 250], "latitude": lat, "longitude": lon}, dims=("level", "latitude", "longitude"))
            ds["cape"] = (("latitude", "longitude"), np.random.rand(*base_shape).astype(np.float32) * 1000.0)
            ds["msl"] = (("latitude", "longitude"), np.ones(base_shape, dtype=np.float32) * 101325.0)
        else:
            ds["t2m"] = (("latitude", "longitude"), np.ones(base_shape, dtype=np.float32) * 290.5)
            ds["tp"] = (("latitude", "longitude"), np.random.rand(*base_shape).astype(np.float32) * 6.0)
            ds["z"] = (("level_500", "latitude", "longitude"), np.ones(base_shape_lvl, dtype=np.float32) * (5805.0 * 9.80665))
            ds["u"] = xr.DataArray(np.random.rand(1, 128, 128).astype(np.float32), coords={"level": [850], "latitude": lat, "longitude": lon}, dims=("level", "latitude", "longitude"))
            ds["v"] = xr.DataArray(np.random.rand(1, 128, 128).astype(np.float32), coords={"level": [850], "latitude": lat, "longitude": lon}, dims=("level", "latitude", "longitude"))
        return ds

    # Generate GFS runs
    curr = start_dt
    while curr <= end_dt:
        for lead in range(1, 11):
            gfs_file = gfs_dir / f"gfs_{curr.strftime('%Y%m%d')}_12z_f{lead*24:03d}.nc"
            if not gfs_file.exists():
                ds = build_ds(is_gfs=True)
                ds.to_netcdf(gfs_file)
        curr += datetime.timedelta(days=1)
        
    # Generate ERA5 runs
    curr = start_dt + datetime.timedelta(days=1)
    while curr <= max_valid_dt:
        era5_file = era5_dir / f"era5_{curr.strftime('%Y%m%d')}_12z.nc"
        if not era5_file.exists():
            ds = build_ds(is_gfs=False)
            ds.to_netcdf(era5_file)
        curr += datetime.timedelta(days=1)
        
    print(f"Generated mock NetCDF data for smoke test.")

if __name__ == "__main__":
    generate_mock_data("2023-01-01", "2023-01-03", "data/mock_gfs", "data/mock_era5")
