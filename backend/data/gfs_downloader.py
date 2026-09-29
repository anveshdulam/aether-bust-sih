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

def download_gfs_run(year: int, month: int, day: int):
    """
    Downloads historical GFS forecast sequence (Days 1-10) for a SINGLE initialization date.
    No API Key required.
    """
    logger.info(f"Connecting to AWS Open Data Registry for NOAA GFS...")
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    date = datetime(year, month, day)
    date_str = date.strftime("%Y%m%d")
    cycle = "12" # 12:00 UTC cycle
    
    # Download Day 1 (f024) to Day 10 (f240)
    for lead_days in range(1, 11):
        forecast_hour = lead_days * 24
        fhour_str = f"f{forecast_hour:03d}"
        
        s3_key = f"gfs.{date_str}/{cycle}/atmos/gfs.t{cycle}z.pgrb2.0p25.{fhour_str}"
        output_file = DATA_DIR / f"gfs_india_{date_str}_{cycle}z_{fhour_str}.grib2"
        
        if output_file.exists():
            logger.info(f"File {output_file.name} already exists. Skipping.")
            continue

        logger.info(f"Downloading GFS Forecast (Day {lead_days}): {s3_key} (~500MB)")
        try:
            # We add a progress callback so it doesn't look stuck
            import sys
            class ProgressPercentage(object):
                def __init__(self, filename):
                    self._filename = filename
                    self._size = float(s3.head_object(Bucket=GFS_BUCKET, Key=s3_key)['ContentLength'])
                    self._seen_so_far = 0
                def __call__(self, bytes_amount):
                    self._seen_so_far += bytes_amount
                    percentage = (self._seen_so_far / self._size) * 100
                    sys.stdout.write(
                        f"\r{self._filename}  {self._seen_so_far / (1024*1024):.1f} MB / {self._size / (1024*1024):.1f} MB  ({percentage:.1f}%)"
                    )
                    sys.stdout.flush()

            s3.download_file(GFS_BUCKET, s3_key, str(output_file), Callback=ProgressPercentage(output_file.name))
            print() # new line after progress bar finishes
            logger.info(f"Successfully downloaded: {output_file.name}")
        except Exception as e:
            logger.error(f"Failed to download {s3_key} from AWS: {e}")

if __name__ == "__main__":
    print("==================================================")
    print(" AETHER-BUST: SIH Dataset Builder (GFS)           ")
    print("==================================================")
    
    # Download sequence for Jan 1 2023, 12z cycle (T=10 lead times)
    download_gfs_run(2023, 1, 1)
    print("\nNext Step: Run the Master Tensor Builder cell!")
