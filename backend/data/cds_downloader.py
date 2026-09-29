import os
import cdsapi
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).parent.parent / "data_storage"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# SIH Exact Bounding Box: [North, West, South, East]
# Calculated to perfectly fit 128x128 at 0.25deg resolution
SIH_BBOX = [37.75, 68.0, 6.0, 99.75]

def download_era5_ground_truth(year: int, month: int):
    """
    Downloads ERA5 Reanalysis data for the specified year and month.
    Downloads BOTH Pressure Levels and Single Levels required by the SIH BustNet.
    """
    logger.info("Connecting to Copernicus Climate Data Store (CDS)...")
    
    try:
        c = cdsapi.Client()
    except Exception as e:
        logger.error("Failed to initialize CDS API. Did you create the ~/.cdsapirc file?")
        raise e

    pl_file = DATA_DIR / f"era5_india_pl_{year}_{month:02d}.nc"
    sl_file = DATA_DIR / f"era5_india_sl_{year}_{month:02d}.nc"
    
    # 1. Download Pressure Levels (z500, u850, v850, u250, v250)
    if not pl_file.exists():
        logger.info(f"Downloading ERA5 Pressure Levels for {year}-{month:02d}...")
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': [
                    'geopotential', 
                    'u_component_of_wind', 
                    'v_component_of_wind'
                ],
                'pressure_level': ['250', '500', '850'],
                'year': str(year),
                'month': f"{month:02d}",
                'day': [f"{d:02d}" for d in range(1, 32)],
                'time': ['12:00'],
                'area': SIH_BBOX,
            },
            str(pl_file)
        )
    else:
        logger.info(f"File {pl_file.name} already exists. Skipping PL download.")

    # 2. Download Single Levels (t2m, tp, cape, mslp)
    if not sl_file.exists():
        logger.info(f"Downloading ERA5 Single Levels for {year}-{month:02d}...")
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': [
                    '2m_temperature',
                    'total_precipitation',
                    'convective_available_potential_energy',
                    'mean_sea_level_pressure'
                ],
                'year': str(year),
                'month': f"{month:02d}",
                'day': [f"{d:02d}" for d in range(1, 32)],
                'time': ['12:00'],
                'area': SIH_BBOX,
            },
            str(sl_file)
        )
    else:
        logger.info(f"File {sl_file.name} already exists. Skipping SL download.")
        
    logger.info(f"✅ Successfully prepared ERA5 data for {year}-{month:02d}")

if __name__ == "__main__":
    print("==================================================")
    print(" AETHER-BUST: SIH Dataset Builder (ERA5)          ")
    print("==================================================")
    
    test_year = 2023
    test_month = 1
    
    download_era5_ground_truth(test_year, test_month)
