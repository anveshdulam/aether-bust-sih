import xarray as xr
import numpy as np
import sys

print("Loading ERA5...")
ds_era5 = xr.open_dataset('backend/data_storage/era5_india_2023_01.nc')
ds_era5_pl = xr.open_dataset('backend/data_storage/era5_india_pl_2023_01.nc')

print("ERA5 SPATIAL:")
print(f"  Lat bounds: {float(ds_era5.latitude.min())} to {float(ds_era5.latitude.max())}")
print(f"  Lon bounds: {float(ds_era5.longitude.min())} to {float(ds_era5.longitude.max())}")
print(f"  Lat shape: {ds_era5.latitude.shape}")
print(f"  Lon shape: {ds_era5.longitude.shape}")
print(f"  First/Last Lat: {float(ds_era5.latitude[0])}, {float(ds_era5.latitude[-1])}")
print(f"  First/Last Lon: {float(ds_era5.longitude[0])}, {float(ds_era5.longitude[-1])}")

print("Loading GFS...")
try:
    # try with xarray and cfgrib
    ds_gfs_surf = xr.open_dataset('backend/data_storage/gfs_india_20230101_12z_f024.grib2', engine='cfgrib', filter_by_keys={'typeOfLevel': 'surface'})
    ds_gfs_isobaric = xr.open_dataset('backend/data_storage/gfs_india_20230101_12z_f024.grib2', engine='cfgrib', filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
    ds_gfs_2m = xr.open_dataset('backend/data_storage/gfs_india_20230101_12z_f024.grib2', engine='cfgrib', filter_by_keys={'typeOfLevel': 'heightAboveGround', 'level': 2})
except Exception as e:
    print(f"Failed to load GFS using cfgrib: {e}")
    sys.exit(1)

print("GFS SPATIAL:")
print(f"  Lat bounds: {float(ds_gfs_surf.latitude.min())} to {float(ds_gfs_surf.latitude.max())}")
print(f"  Lon bounds: {float(ds_gfs_surf.longitude.min())} to {float(ds_gfs_surf.longitude.max())}")
print(f"  Lat shape: {ds_gfs_surf.latitude.shape}")
print(f"  Lon shape: {ds_gfs_surf.longitude.shape}")
print(f"  First/Last Lat: {float(ds_gfs_surf.latitude[0])}, {float(ds_gfs_surf.latitude[-1])}")
print(f"  First/Last Lon: {float(ds_gfs_surf.longitude[0])}, {float(ds_gfs_surf.longitude[-1])}")

print("\nGFS PRECIPITATION METADATA:")
if 'tp' in ds_gfs_surf:
    print(ds_gfs_surf['tp'].attrs)
    print("Precip data shape:", ds_gfs_surf['tp'].shape)
else:
    print("tp not found in surface. Keys:", list(ds_gfs_surf.keys()))

print("\nExtracting slice 37.75 to 6.0 and 68.0 to 99.75...")
# GFS lat is usually 90 to -90, lon is 0 to 360
# 128 points starting from 37.75 to 6.0 -> 37.75 - 6.0 = 31.75 / 127 = 0.25
lat_slice = slice(37.75, 6.0)
lon_slice = slice(68.0, 99.75)

gfs_t2m = ds_gfs_2m['t2m'].sel(latitude=lat_slice, longitude=lon_slice)
gfs_tp = ds_gfs_surf['tp'].sel(latitude=lat_slice, longitude=lon_slice) if 'tp' in ds_gfs_surf else None
gfs_z500 = ds_gfs_isobaric['gh'].sel(isobaricInhPa=500, latitude=lat_slice, longitude=lon_slice)
gfs_u850 = ds_gfs_isobaric['u'].sel(isobaricInhPa=850, latitude=lat_slice, longitude=lon_slice)
gfs_v850 = ds_gfs_isobaric['v'].sel(isobaricInhPa=850, latitude=lat_slice, longitude=lon_slice)
gfs_u250 = ds_gfs_isobaric['u'].sel(isobaricInhPa=250, latitude=lat_slice, longitude=lon_slice)
gfs_v250 = ds_gfs_isobaric['v'].sel(isobaricInhPa=250, latitude=lat_slice, longitude=lon_slice)
gfs_cape = ds_gfs_surf['cape'].sel(latitude=lat_slice, longitude=lon_slice) if 'cape' in ds_gfs_surf else None

# Mean sea level pressure might be in a different filter
try:
    ds_gfs_msl = xr.open_dataset('backend/data_storage/gfs_india_20230101_12z_f024.grib2', engine='cfgrib', filter_by_keys={'typeOfLevel': 'meanSea'})
    gfs_msl = ds_gfs_msl['prmsl'].sel(latitude=lat_slice, longitude=lon_slice)
except Exception as e:
    print(f"Failed to load PRMSL: {e}")
    gfs_msl = None

print("\nShapes after slicing:")
print(f"GFS t2m: {gfs_t2m.shape}")
if gfs_tp is not None: print(f"GFS tp: {gfs_tp.shape}")

era5_t2m = ds_era5['t2m'].sel(time='2023-01-02T12:00:00', latitude=lat_slice, longitude=lon_slice)
era5_tp = ds_era5['tp'].sel(time='2023-01-02T12:00:00', latitude=lat_slice, longitude=lon_slice)
era5_z500 = ds_era5_pl['z'].sel(time='2023-01-02T12:00:00', level=500, latitude=lat_slice, longitude=lon_slice)
era5_u850 = ds_era5_pl['u'].sel(time='2023-01-02T12:00:00', level=850, latitude=lat_slice, longitude=lon_slice)

print(f"ERA5 t2m: {era5_t2m.shape}")

print("\nRAW PHYSICAL RANGES GFS:")
def pr(name, da):
    if da is not None:
        v = da.values
        print(f"{name:<10}: Min {v.min():8.2f} | Max {v.max():8.2f} | Mean {v.mean():8.2f} | Std {v.std():8.2f}")
pr("t2m", gfs_t2m)
pr("tp", gfs_tp)
pr("z500", gfs_z500)
pr("u850", gfs_u850)
pr("v850", gfs_v850)
pr("cape", gfs_cape)
pr("mslp", gfs_msl)

print("\nRAW PHYSICAL RANGES ERA5:")
pr("t2m", era5_t2m)
pr("tp", era5_tp)
pr("z", era5_z500)
pr("u850", era5_u850)

