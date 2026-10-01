import os
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).parent.parent / "data_storage"
DATA_DIR.mkdir(parents=True, exist_ok=True)
GFS_BUCKET = "noaa-gfs-bdp-pds"

import concurrent.futures

def download_file(s3, s3_key, output_file):
    if output_file.exists():
        logger.info(f"File {output_file.name} already exists. Skipping.")
        return True

    logger.info(f"Downloading: {s3_key}")
    try:
        s3.download_file(GFS_BUCKET, s3_key, str(output_file))
        logger.info(f"Successfully downloaded: {output_file.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {s3_key}: {e}")
        return False

def download_gfs_run(year: int, month: int, day: int):
    """
    Downloads historical GFS forecast sequence (Days 1-10) for a SINGLE initialization date.
    Parallelized for high speed.
    """
    logger.info(f"Connecting to AWS Open Data Registry for NOAA GFS...")
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    date = datetime(year, month, day)
    date_str = date.strftime("%Y%m%d")
    cycle = "12" # 12:00 UTC cycle
    
    tasks = []
    # We will download in parallel to saturate bandwidth
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for lead_days in range(1, 11):
            forecast_hour = lead_days * 24
            fhour_str = f"f{forecast_hour:03d}"
            
            s3_key = f"gfs.{date_str}/{cycle}/atmos/gfs.t{cycle}z.pgrb2.0p25.{fhour_str}"
            output_file = DATA_DIR / f"gfs_india_{date_str}_{cycle}z_{fhour_str}.grib2"
            
            tasks.append(executor.submit(download_file, s3, s3_key, output_file))
        
        concurrent.futures.wait(tasks)

if __name__ == "__main__":
    print("==================================================")
    print(" AETHER-BUST: SIH Dataset Builder (GFS)           ")
    print("==================================================")
    
    # Download sequence for Jan 1 2023, 12z cycle (T=10 lead times)
    download_gfs_run(2023, 1, 1)
    print("\nNext Step: Run the Master Tensor Builder cell!")
