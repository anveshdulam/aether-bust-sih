import xarray as xr
import torch
import numpy as np
import logging
from pathlib import Path
import json

# Setup directories
DATA_DIR = Path.cwd() / "data_storage"
_PROCESSED_DIR = DATA_DIR.parent / "artifacts" / "real_run_20230101"
_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 1. Create a unique logger for this script
_prep_logger = logging.getLogger("tensor_builder")
if not _prep_logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def build_master_tensor():
    _prep_logger.info("Initializing Master Tensor Builder for 2023-01-01 12z...")
    
    # 2. Locate ERA5 (Truth) Files
    era5_pl_file = DATA_DIR / "era5_india_pl_2023_01.nc"
    era5_sl_file = DATA_DIR / "era5_india_sl_2023_01.nc"
    
    if not era5_pl_file.exists() or not era5_sl_file.exists():
        _prep_logger.error("Missing ERA5 files! Did you run cds_downloader.py?")
        return

    _prep_logger.info("Loading ERA5 Data (Truth)...")
    try:
        era5_pl = xr.open_dataset(era5_pl_file, engine='netcdf4')
        era5_sl = xr.open_dataset(era5_sl_file, engine='netcdf4')
    except Exception as e:
        _prep_logger.error(f"Failed to open ERA5 NetCDF files. Is 'netCDF4' python package installed? Error: {e}")
        return

    # In a full implementation, you would:
    # 1. Loop through Days 1-10 (f024 to f240) of GFS (Forecast).
    # 2. Regrid GFS to match ERA5 exact 128x128 grid (`37.75 to 6.0` Lat, `68.0 to 99.75` Lon).
    # 3. Extract all 10 predictor channels (`t2m, tp, z500, u850, v850, ws850, cape, mslp, z500_anom, shear_850_250`).
    # 4. Extract the target analyses from ERA5 at the exact corresponding valid times.
    # 5. Calculate Bust Labels (Yb) based on thresholds and Expected Error (Ye).
    # 6. Save as X.npy (1, 10, 10, 128, 128), Yb_true.npy (10, 4, 128, 128), Ye_true.npy (10, 4, 128, 128)
    
    _prep_logger.info("This is the Master Tensor Builder template.")
    _prep_logger.info("Since we just fixed `gfs_downloader.py`, make sure to run it next!")
    _prep_logger.info("To finish this builder, we will need `cfgrib` installed to parse the GFS files.")

if __name__ == "__main__":
    print("==================================================")
    print(" AETHER-BUST: Master Tensor Builder               ")
    print("==================================================")
    build_master_tensor()
