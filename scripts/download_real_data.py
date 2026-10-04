import os
import requests
from pathlib import Path

# Need cdsapi installed for ERA5: pip install cdsapi
try:
    import cdsapi
except ImportError:
    print("Please install cdsapi: pip install cdsapi")
    print("You also need to configure your ~/.cdsapirc file with your API key.")

DATA_DIR = Path("backend/data_storage")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def download_gfs():
    """
    Downloads historical GFS data from NOAA AWS S3 or NOMADS.
    For this example, we mock the S3 URL since NOAA archives move to AWS S3 bucket: noaa-gfs-bdp-pds.
    """
    print("--- Downloading GFS Data ---")
    # Example URL for a specific cycle. Note: NOAA historical requires AWS CLI or direct S3 HTTP access.
    # To keep it simple, we demonstrate downloading from a public HTTP mirror if available.
    print("Note: NOAA historical GFS (2023) is stored in AWS S3 (s3://noaa-gfs-bdp-pds).")
    print("To download programmatically without AWS CLI, you can construct the HTTP URL:")
    date_str = "20230101"
    cycle = "12"
    
    for fhr in range(24, 241, 24):
        file_name = f"gfs.t{cycle}z.pgrb2.0p25.f{fhr:03d}"
        url = f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{date_str}/{cycle}/atmos/{file_name}"
        dest = DATA_DIR / f"gfs_india_{date_str}_{cycle}z_f{fhr:03d}.grib2"
        
        if dest.exists():
            print(f"Already exists: {dest.name}")
            continue
            
        print(f"Downloading {url} to {dest}...")
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Downloaded: {dest.name}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")

def download_era5():
    """
    Downloads ERA5 reanalysis data using the Copernicus CDS API.
    """
    print("--- Downloading ERA5 Data ---")
    try:
        c = cdsapi.Client()
    except Exception as e:
        print("Failed to initialize CDS API client. Is ~/.cdsapirc configured?")
        return

    # Download Surface Variables
    dest_sfc = DATA_DIR / "era5_india_2023_01.nc"
    if not dest_sfc.exists():
        print("Requesting ERA5 Surface Variables...")
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': ['2m_temperature', 'total_precipitation'],
                'year': '2023',
                'month': '01',
                'day': [f"{d:02d}" for d in range(1, 32)],
                'time': ['00:00', '06:00', '12:00', '18:00'],
                'area': [37.75, 68.0, 6.0, 99.75], # N, W, S, E (India bbox)
            },
            str(dest_sfc)
        )
        print("Downloaded ERA5 Surface.")
    else:
        print(f"Already exists: {dest_sfc.name}")

    # Download Pressure Levels
    dest_pl = DATA_DIR / "era5_india_pl_2023_01.nc"
    if not dest_pl.exists():
        print("Requesting ERA5 Pressure Levels...")
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': ['geopotential', 'u_component_of_wind', 'v_component_of_wind'],
                'pressure_level': ['250', '500', '850'],
                'year': '2023',
                'month': '01',
                'day': [f"{d:02d}" for d in range(1, 32)],
                'time': ['00:00', '06:00', '12:00', '18:00'],
                'area': [37.75, 68.0, 6.0, 99.75],
            },
            str(dest_pl)
        )
        print("Downloaded ERA5 Pressure Levels.")
    else:
        print(f"Already exists: {dest_pl.name}")

if __name__ == "__main__":
    print("Starting AETHER-BUST Real Data Downloader...")
    download_gfs()
    download_era5()
    print("Done.")
