import xarray as xr
import torch
import numpy as np
import logging
from pathlib import Path

# Safely get paths (Assuming DATA_DIR is already in cell-0, but we redefine it safely here for a standalone script)
DATA_DIR = Path.cwd() / "data_storage"
_PROCESSED_DIR = DATA_DIR.parent / "processed_tensors"
_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 1. Create a unique logger for this cell
_prep_logger = logging.getLogger("tensor_preprocessor")
if not _prep_logger.handlers:
    logging.basicConfig(level=logging.INFO)

def preprocess_and_align(year: int, month: int):
    _prep_logger.info(f"Processing Tensors for {year}-{month:02d}...")
    
    # 2. Locate the files you just downloaded (Notice the year 2023!)
    era5_file = DATA_DIR / f"era5_india_{year}_{month:02d}.nc"
    gfs_file = DATA_DIR / f"gfs_india_{year}{month:02d}01_12z_f024.grib2"
    
    if not era5_file.exists():
        _prep_logger.warning(f"Missing ERA5 file: {era5_file.name}")
        return
    if not gfs_file.exists():
        _prep_logger.warning(f"Missing GFS file: {gfs_file.name}")
        return

    # 3. Crack open the data
    era5_data = xr.open_dataset(era5_file, engine='netcdf4')
    gfs_data = xr.open_dataset(gfs_file, engine='cfgrib')
    
    try:
        # 4. Extract the physics variable (Geopotential Height at 500hPa)
        era5_z500 = era5_data['z'].sel(pressure_level=500).values 
        gfs_z500 = gfs_data['gh'].sel(isobaricInhPa=500).values 
        
        # 5. Calculate the Target! (Bust = | GFS Forecast - ERA5 Truth |)
        bust_error = np.abs(gfs_z500 - era5_z500)
        
        # 6. Convert to GPU-ready PyTorch Tensors
        X_tensor = torch.tensor(gfs_z500, dtype=torch.float32)
        Y_tensor = torch.tensor(bust_error, dtype=torch.float32)
        
        # 7. Save the .pt files for the RTX 6000
        torch.save(X_tensor, _PROCESSED_DIR / f"X_{year}_{month:02d}.pt")
        torch.save(Y_tensor, _PROCESSED_DIR / f"Y_{year}_{month:02d}.pt")
        
        _prep_logger.info(f"✅ Successfully generated: X_{year}_{month:02d}.pt and Y_{year}_{month:02d}.pt")
            
    except Exception as e:
        _prep_logger.error(f"Error extracting variables: {e}")

# Process the January 2023 data!
preprocess_and_align(2023, 1)
