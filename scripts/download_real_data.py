import os
import requests
import datetime
from pathlib import Path

try:
    import cdsapi
except ImportError:
    print("Please install cdsapi: pip install cdsapi")

DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def download_gfs_for_year(year: int):
    """
    Downloads historical GFS data from NOAA AWS S3 for an entire year.
    WARNING: This will download thousands of files and take hundreds of GBs.
    """
    print(f"--- Downloading GFS Data for {year} ---")
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    
    # We'll stick to the 12Z cycle for now to align with daily predictions
    cycles = ["12"] 
    # Forecast hours (lead times) every 24 hours up to 240 (10 days)
    fhrs = list(range(24, 241, 24))

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y%m%d")
        
        for cycle in cycles:
            for fhr in fhrs:
                file_name = f"gfs.t{cycle}z.pgrb2.0p25.f{fhr:03d}"
                url = f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{date_str}/{cycle}/atmos/{file_name}"
                dest = DATA_DIR / f"gfs_india_{date_str}_{cycle}z_f{fhr:03d}.grib2"
                
                if dest.exists():
                    print(f"Already exists: {dest.name}")
                    continue
                    
                print(f"Downloading {dest.name}...")
                try:
                    with requests.get(url, stream=True) as r:
                        r.raise_for_status()
                        with open(dest, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                except Exception as e:
                    print(f"Failed {url}: {e}")
        
        current_date += datetime.timedelta(days=1)

def download_era5_for_year(year: int):
    """
    Downloads ERA5 reanalysis data using Copernicus CDS API for the whole year.
    """
    print(f"--- Downloading ERA5 Data for {year} ---")
    try:
        c = cdsapi.Client()
    except Exception as e:
        print("Failed to initialize CDS API client. Is ~/.cdsapirc configured?")
        return

    months = [f"{m:02d}" for m in range(1, 13)]
    days = [f"{d:02d}" for d in range(1, 32)]
    
    # Download Surface Variables for the whole year
    dest_sfc = DATA_DIR / f"era5_india_sfc_{year}.nc"
    if not dest_sfc.exists():
        print(f"Requesting ERA5 Surface Variables for {year}...")
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': ['2m_temperature', 'total_precipitation'],
                'year': str(year),
                'month': months,
                'day': days,
                'time': ['00:00', '06:00', '12:00', '18:00'],
                'area': [37.75, 68.0, 6.0, 99.75], 
            },
            str(dest_sfc)
        )
    else:
        print(f"Already exists: {dest_sfc.name}")

    # Download Pressure Levels for the whole year
    dest_pl = DATA_DIR / f"era5_india_pl_{year}.nc"
    if not dest_pl.exists():
        print(f"Requesting ERA5 Pressure Levels for {year}...")
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': ['geopotential', 'u_component_of_wind', 'v_component_of_wind'],
                'pressure_level': ['250', '500', '850'],
                'year': str(year),
                'month': months,
                'day': days,
                'time': ['00:00', '06:00', '12:00', '18:00'],
                'area': [37.75, 68.0, 6.0, 99.75],
            },
            str(dest_pl)
        )
    else:
        print(f"Already exists: {dest_pl.name}")

if __name__ == "__main__":
    print("Starting AETHER-BUST Full Year Data Downloader...")
    
    TARGET_YEAR = 2023
    
    download_gfs_for_year(TARGET_YEAR)
    download_era5_for_year(TARGET_YEAR)
    
    print("Done downloading full dataset.")
