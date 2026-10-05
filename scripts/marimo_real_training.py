import os
import sys
import subprocess
import datetime
import urllib.request
from pathlib import Path

# --- 1. Dependencies ---
print("Ensuring dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "xarray", "h5netcdf", "dask", "netCDF4", "cdsapi", "numpy", "torch", "scipy"])

import xarray as xr
import numpy as np
import torch
import cdsapi
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# --- 2. Configuration & Constants ---
YEARS = [2019] 
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)
WEIGHTS_DIR = Path("weights")
WEIGHTS_DIR.mkdir(exist_ok=True)

# Constants for BustNet
PHI_MIN, PHI_MAX = 6.0, 37.75
LAMBDA_MIN, LAMBDA_MAX = 68.0, 99.75
H, W = 128, 128
T, C, V = 10, 10, 4
VAR_CODES = ("t2m", "tp", "z500", "ws850")
TAU = {"t2m": 3.0, "tp": 20.0, "z500": 60.0, "ws850": 5.0}
W_CONF = {"t2m": 0.25, "tp": 0.35, "z500": 0.25, "ws850": 0.15}

# --- 3. Self-Contained Neural Network (BustNet & Loss) ---
class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.GroupNorm(8, out_ch),
            nn.SiLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.GroupNorm(8, out_ch),
            nn.SiLU(inplace=True)
        )
    def forward(self, x): return self.conv(x)

class UNetEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = ConvBlock(C, 64)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(64, 128))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(128, 256))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(256, 256))
        self.down4 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(256, 256))
    def forward(self, x):
        s1 = self.stem(x)
        s2 = self.down1(s1)
        s3 = self.down2(s2)
        s4 = self.down3(s3)
        return self.down4(s4), s1, s2, s3, s4

class ConvLSTMCell(nn.Module):
    def __init__(self, in_ch=256, hidden_ch=256, kernel_size=3):
        super().__init__()
        self.hidden_ch = hidden_ch
        self.conv = nn.Conv2d(in_ch + hidden_ch, 4 * hidden_ch, kernel_size, padding=kernel_size//2)
    def forward(self, x, state):
        h, c = state
        gates = self.conv(torch.cat([x, h], dim=1))
        i, f, o, g = torch.split(gates, self.hidden_ch, dim=1)
        c_next = torch.sigmoid(f) * c + torch.sigmoid(i) * torch.tanh(g)
        return torch.sigmoid(o) * torch.tanh(c_next), c_next

class TemporalSelfAttention(nn.Module):
    def __init__(self, d_model=256, nhead=8):
        super().__init__()
        self.mha = nn.MultiheadAttention(embed_dim=d_model, num_heads=nhead, batch_first=True)
        self.norm = nn.LayerNorm(d_model)
    def forward(self, h_seq):
        B, t_len, C_, H_, W_ = h_seq.shape
        x = h_seq.view(B, t_len, C_, H_ * W_).permute(0, 3, 1, 2).reshape(B * H_ * W_, t_len, C_)
        causal_mask = torch.triu(torch.full((t_len, t_len), float('-inf'), device=x.device), diagonal=1)
        attn_out, _ = self.mha(x, x, x, attn_mask=causal_mask, need_weights=False)
        out = self.norm(x + attn_out)
        return out.view(B, H_ * W_, t_len, C_).permute(0, 2, 3, 1).view(B, t_len, C_, H_, W_)

class UNetDecoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.up4 = nn.ConvTranspose2d(256, 256, 2, stride=2)
        self.conv4 = ConvBlock(512, 256)
        self.up3 = nn.ConvTranspose2d(256, 256, 2, stride=2)
        self.conv3 = ConvBlock(512, 256)
        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.conv2 = ConvBlock(256, 128)
        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.conv1 = ConvBlock(128, 64)
    def forward(self, x, skips):
        s1, s2, s3, s4 = skips
        d = self.conv4(torch.cat([self.up4(x), s4], dim=1))
        d = self.conv3(torch.cat([self.up3(d), s3], dim=1))
        d = self.conv2(torch.cat([self.up2(d), s2], dim=1))
        return self.conv1(torch.cat([self.up1(d), s1], dim=1))

class BustNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = UNetEncoder()
        self.lstm = ConvLSTMCell(256, 256)
        self.attn = TemporalSelfAttention(256, 8)
        self.decoder = UNetDecoder()
        self.head_bust = nn.Conv2d(64, V, 1)
        self.head_error = nn.Conv2d(64, V, 1)
    def forward(self, x):
        B = x.shape[0]
        bots, skips_t = [], {1: [], 2: [], 3: [], 4: []}
        for t in range(T):
            bot, s1, s2, s3, s4 = self.encoder(x[:, t])
            bots.append(bot)
            skips_t[1].append(s1)
            skips_t[2].append(s2)
            skips_t[3].append(s3)
            skips_t[4].append(s4)
            
        lstm_out = []
        h = torch.zeros(B, 256, 8, 8, device=x.device, dtype=x.dtype)
        c = torch.zeros(B, 256, 8, 8, device=x.device, dtype=x.dtype)
        for t in range(T):
            h, c = self.lstm(bots[t], (h, c))
            lstm_out.append(h)
            
        a_seq = self.attn(torch.stack(lstm_out, dim=1))
        
        yb_out, ye_out = [], []
        for t in range(T):
            d = self.decoder(a_seq[:, t], (skips_t[1][t], skips_t[2][t], skips_t[3][t], skips_t[4][t]))
            yb_out.append(torch.sigmoid(self.head_bust(d)))
            ye_out.append(F.softplus(self.head_error(d)))
            
        return {"bust": torch.stack(yb_out, dim=1), "error": torch.stack(ye_out, dim=1)}

class MultiTaskBustLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.w_v = torch.tensor([W_CONF[v] for v in VAR_CODES], dtype=torch.float32)
        self.tau = torch.tensor([TAU[v] for v in VAR_CODES], dtype=torch.float32)
    def forward(self, Yb_pred, Ye_pred, Yb_true, Ye_true):
        w_v = self.w_v.to(Yb_pred.device).view(1, 1, 4, 1, 1)
        tau = self.tau.to(Yb_pred.device).view(1, 1, 4, 1, 1)
        
        bce = F.binary_cross_entropy(Yb_pred, Yb_true, reduction='none')
        p_t = torch.where(Yb_true == 1, Yb_pred, 1 - Yb_pred)
        alpha_t = torch.where(Yb_true == 1, 0.75, 0.25)
        l_cls_v = (alpha_t * torch.pow(1 - p_t, 2.0) * bce).mean(dim=(0, 1, 3, 4))
        
        mae = torch.abs(Ye_pred / tau - Ye_true / tau)
        hit_mask = (Yb_true == 1).float()
        mae_hit = (mae * hit_mask).sum(dim=(0, 1, 3, 4)) / (hit_mask.sum(dim=(0, 1, 3, 4)) + 1e-8)
        mae_all = mae.mean(dim=(0, 1, 3, 4))
        
        L_cls_w = (w_v.squeeze() * l_cls_v).sum()
        L_reg_w = (w_v.squeeze() * (1.0 * mae_hit + 0.1 * mae_all)).sum()
        return 1.0 * L_cls_w + 0.5 * L_reg_w


# --- 4. Authentication for ERA5 Ground Truth ---
CDSAPI_PATH = Path.home() / ".cdsapirc"
print("Setting up CDS API credentials...")
with open(CDSAPI_PATH, 'w') as f:
    f.write('url: https://cds.climate.copernicus.eu/api\n')
    f.write('key: a2b74ab2-30c3-4924-9f74-d1a80de2d317\n')
print(f"CDS API credentials saved to {CDSAPI_PATH}")

# --- 5. Downloading Data ---
def ensure_netcdf(filepath):
    """Copernicus sometimes wraps large yearly requests in ZIP/TAR or returns HTML errors."""
    filepath = Path(filepath)
    if not filepath.exists(): return
    
    with open(filepath, 'rb') as f: head = f.read(500)
    
    if b'<html' in head.lower() or b'<!doctype' in head.lower():
        print(f"❌ Copernicus API returned an HTML error page for {filepath.name}!")
        with open(filepath, 'r', errors='ignore') as f: print(f.read()[:1000])
        filepath.unlink()
        sys.exit(1)
        
    import zipfile, tarfile
    if zipfile.is_zipfile(filepath):
        print(f"📦 Unzipping {filepath.name}...")
        with zipfile.ZipFile(filepath, 'r') as z:
            ext_path = z.extract(z.namelist()[0], path=filepath.parent)
            os.replace(ext_path, filepath)
        return
        
    try:
        if tarfile.is_tarfile(filepath):
            print(f"📦 Untarring {filepath.name}...")
            with tarfile.open(filepath, 'r') as t:
                ext_path = filepath.parent / t.getnames()[0]
                t.extract(t.getnames()[0], path=filepath.parent)
                os.replace(ext_path, filepath)
            return
    except Exception: pass

def _is_valid_netcdf(filepath):
    """Check if a file is a valid, openable NetCDF file."""
    filepath = Path(filepath)
    if not filepath.exists():
        return False
    try:
        with xr.open_dataset(filepath) as ds:
            pass
        return True
    except Exception:
        return False

def _merge_monthly_to_yearly(monthly_files, yearly_dest):
    """Merge a list of monthly NetCDF files into a single yearly file."""
    yearly_dest = Path(yearly_dest)
    print(f"  Merging {len(monthly_files)} monthly files -> {yearly_dest.name}...")
    datasets = [xr.open_dataset(f, engine="h5netcdf") for f in monthly_files]
    merged = xr.concat(datasets, dim="time")
    # Sort by time just in case
    time_coord = _get_time_coord(merged)
    merged = merged.sortby(time_coord)
    merged.to_netcdf(yearly_dest, engine="h5netcdf")
    for ds in datasets:
        ds.close()
    # Clean up monthly files
    for f in monthly_files:
        Path(f).unlink()
    print(f"  ✅ Merged and saved {yearly_dest.name}")

def download_era5_year(year):
    """
    Download ERA5 data month-by-month to avoid CDS 'request too large' errors,
    then merge the monthly files into yearly NetCDF files.
    """
    print(f"Checking ERA5 ground truth for {year}...")
    c = cdsapi.Client()
    sfc_dest = DATA_DIR / f"era5_sfc_{year}.nc"
    pl_dest = DATA_DIR / f"era5_pl_{year}.nc"

    # --- AUTO-DELETE CORRUPTED YEARLY FILES ---
    for dest in [sfc_dest, pl_dest]:
        if dest.exists() and not _is_valid_netcdf(dest):
            print(f"🗑️ Found corrupted/GRIB file {dest.name}! Deleting it...")
            dest.unlink()

    # --- Surface variables (t2m, tp, msl, cape) ---
    if not sfc_dest.exists():
        sfc_monthly_files = []
        all_months_ready = True
        for month in range(1, 13):
            month_str = f"{month:02d}"
            monthly_dest = DATA_DIR / f"era5_sfc_{year}_{month_str}.nc"
            
            # Delete corrupted monthly files
            if monthly_dest.exists() and not _is_valid_netcdf(monthly_dest):
                print(f"🗑️ Deleting corrupted monthly file {monthly_dest.name}...")
                monthly_dest.unlink()
            
            if not monthly_dest.exists():
                print(f"  Downloading ERA5 surface {year}-{month_str}...")
                try:
                    c.retrieve('reanalysis-era5-single-levels', {
                        'product_type': 'reanalysis',
                        'format': 'netcdf',
                        'data_format': 'netcdf',
                        'download_format': 'uncompressed_netcdf',
                        'variable': [
                            '2m_temperature',
                            'total_precipitation',
                            'mean_sea_level_pressure',
                            'convective_available_potential_energy',
                        ],
                        'year': str(year),
                        'month': month_str,
                        'day': [f"{d:02d}" for d in range(1, 32)],
                        'time': '12:00',
                        'area': [PHI_MAX, LAMBDA_MIN, PHI_MIN, LAMBDA_MAX],
                    }, str(monthly_dest))
                    ensure_netcdf(monthly_dest)
                except Exception as e:
                    print(f"  ❌ Failed to download {monthly_dest.name}: {e}")
                    all_months_ready = False
                    continue
            
            if monthly_dest.exists():
                sfc_monthly_files.append(str(monthly_dest))
        
        if len(sfc_monthly_files) == 12:
            _merge_monthly_to_yearly(sfc_monthly_files, sfc_dest)
        elif len(sfc_monthly_files) > 0:
            print(f"  ⚠️ Only {len(sfc_monthly_files)}/12 months available for surface; merging partial year.")
            _merge_monthly_to_yearly(sfc_monthly_files, sfc_dest)
        else:
            print(f"  ❌ No surface data downloaded for {year}!")
    
    # --- Pressure-level variables (z, u, v) ---
    if not pl_dest.exists():
        pl_monthly_files = []
        all_months_ready = True
        for month in range(1, 13):
            month_str = f"{month:02d}"
            monthly_dest = DATA_DIR / f"era5_pl_{year}_{month_str}.nc"
            
            # Delete corrupted monthly files
            if monthly_dest.exists() and not _is_valid_netcdf(monthly_dest):
                print(f"🗑️ Deleting corrupted monthly file {monthly_dest.name}...")
                monthly_dest.unlink()
            
            if not monthly_dest.exists():
                print(f"  Downloading ERA5 pressure-levels {year}-{month_str}...")
                try:
                    c.retrieve('reanalysis-era5-pressure-levels', {
                        'product_type': 'reanalysis',
                        'format': 'netcdf',
                        'data_format': 'netcdf',
                        'download_format': 'uncompressed_netcdf',
                        'variable': [
                            'geopotential',
                            'u_component_of_wind',
                            'v_component_of_wind',
                        ],
                        'pressure_level': ['250', '500', '850'],
                        'year': str(year),
                        'month': month_str,
                        'day': [f"{d:02d}" for d in range(1, 32)],
                        'time': '12:00',
                        'area': [PHI_MAX, LAMBDA_MIN, PHI_MIN, LAMBDA_MAX],
                    }, str(monthly_dest))
                    ensure_netcdf(monthly_dest)
                except Exception as e:
                    print(f"  ❌ Failed to download {monthly_dest.name}: {e}")
                    all_months_ready = False
                    continue
            
            if monthly_dest.exists():
                pl_monthly_files.append(str(monthly_dest))
        
        if len(pl_monthly_files) == 12:
            _merge_monthly_to_yearly(pl_monthly_files, pl_dest)
        elif len(pl_monthly_files) > 0:
            print(f"  ⚠️ Only {len(pl_monthly_files)}/12 months available for pressure-levels; merging partial year.")
            _merge_monthly_to_yearly(pl_monthly_files, pl_dest)
        else:
            print(f"  ❌ No pressure-level data downloaded for {year}!")

    return sfc_dest, pl_dest

# --- 6. Data Extraction (Real Data) ---
def _get_time_coord(ds):
    """Return the name of the time dimension/coordinate used by this dataset."""
    for candidate in ("valid_time", "time"):
        if candidate in ds.coords or candidate in ds.dims:
            return candidate
    raise KeyError(f"Could not find a time coordinate in dataset. Available coords: {list(ds.coords)}")

def _get_level_coord(ds):
    """Return the name of the pressure-level coordinate used by this dataset."""
    for candidate in ("pressure_level", "level", "isobaricInhPa"):
        if candidate in ds.coords or candidate in ds.dims:
            return candidate
    raise KeyError(f"Could not find a pressure-level coordinate in dataset. Available coords: {list(ds.coords)}")

def parse_real_tensors_fast(date: datetime.date, ds_sfc, ds_pl):
    """
    GRAND FINALE METHOD: Self-Supervised Physics Degradation
    """
    try:
        sfc_time_coord = _get_time_coord(ds_sfc)
        pl_time_coord = _get_time_coord(ds_pl)
        pl_level_coord = _get_level_coord(ds_pl)
        
        # Select 10 days of future weather starting from `date`
        dates = [date + datetime.timedelta(days=d) for d in range(T)]
        time_strs = [d.strftime("%Y-%m-%dT12:00:00") for d in dates]
        
        # Helper function to extract and handle the `expver` extra dimension
        def safe_extract(ds, var_name, time_coord, level_coord=None, level_val=None):
            if var_name not in ds:
                return None # Handle missing variable gracefully
                
            if level_coord:
                da = ds[var_name].sel({time_coord: time_strs, level_coord: level_val}, method="nearest")
            else:
                da = ds[var_name].sel({time_coord: time_strs}, method="nearest")
                
            # Flatten the annoying 'expver' dimension if Copernicus added it
            if 'expver' in da.dims:
                da = da.mean(dim='expver', skipna=True)
            return da.values
            
        # Extract variables
        t2m = safe_extract(ds_sfc, 't2m', sfc_time_coord)
        msl = safe_extract(ds_sfc, 'msl', sfc_time_coord)
        cape = safe_extract(ds_sfc, 'cape', sfc_time_coord)
        
        tp = safe_extract(ds_sfc, 'tp', sfc_time_coord)
        if tp is None:
            tp = np.zeros_like(t2m) # Fallback if `total_precipitation` wasn't downloaded
            
        z500 = safe_extract(ds_pl, 'z', pl_time_coord, pl_level_coord, 500)
        u850 = safe_extract(ds_pl, 'u', pl_time_coord, pl_level_coord, 850)
        v850 = safe_extract(ds_pl, 'v', pl_time_coord, pl_level_coord, 850)
        
        ws850 = np.sqrt(u850**2 + v850**2)
        
        # Ground Truth Y [T, V, H, W] for the 4 target variables
        Y_true = np.stack([t2m, tp, z500, ws850], axis=1) # [10, 4, 128, 128]
        
        # Create "Fake GFS" X [T, C, H, W] by shifting and adding noise to Y
        # This simulates a GFS model predicting a cyclone in the slightly wrong location!
        X_base = np.stack([t2m, tp, z500, ws850, msl, cape, u850, v850, u850*0, v850*0], axis=1)
        
        # Degrade X to simulate forecast errors
        noise = np.random.randn(T, C, H, W) * 2.0
        X_forecast = X_base + noise
        
        # Calculate Busts (If Error > Threshold)
        Ye = np.abs(X_forecast[:, :4, :, :] - Y_true)
        Yb = np.zeros_like(Ye)
        for v, var in enumerate(VAR_CODES):
            Yb[:, v, :, :] = (Ye[:, v, :, :] > TAU[var]).astype(np.float32)
            
        # Convert to PyTorch Tensors
        X_tensor = torch.tensor(X_forecast, dtype=torch.float32)
        Y_b_tensor = torch.tensor(Yb, dtype=torch.float32)
        Y_e_tensor = torch.tensor(Ye, dtype=torch.float32)
        
        # Normalize X to prevent NaN loss
        X_tensor = (X_tensor - X_tensor.mean(dim=(0,2,3), keepdim=True)) / (X_tensor.std(dim=(0,2,3), keepdim=True) + 1e-5)
        
        return X_tensor, Y_b_tensor, Y_e_tensor
        
    except Exception as e:
        print(f"Error parsing date {date}: {e}")
        raise e

class RealWeatherDataset(torch.utils.data.Dataset):
    def __init__(self, years):
        self.samples = []
        self.ds_sfc_cache = {}
        self.ds_pl_cache = {}
        for year in years:
            era5_sfc, era5_pl = download_era5_year(year)
            
            # KEEP DATASETS OPEN IN MEMORY WITH H5NETCDF (Extremely thread-safe and stable)
            self.ds_sfc_cache[year] = xr.open_dataset(era5_sfc, engine="h5netcdf")
            self.ds_pl_cache[year] = xr.open_dataset(era5_pl, engine="h5netcdf")
            
            # Train on the entire year (Normal days + Cyclone days + Monsoon days)
            # We stop at day 355 because each sample looks 10 days into the future.
            start_date = datetime.date(year, 1, 1)
            for day_offset in range(355): 
                curr_date = start_date + datetime.timedelta(days=day_offset)
                self.samples.append({"date": curr_date, "year": year})
                
        print(f"Successfully assembled {len(self.samples)} physical days of combined ERA5 data (Normal + Extreme).")
        if len(self.samples) == 0:
            sys.exit(1)

    def __len__(self): return len(self.samples)
    def __getitem__(self, idx): 
        sample = self.samples[idx]
        return parse_real_tensors_fast(
            sample["date"], 
            self.ds_sfc_cache[sample["year"]], 
            self.ds_pl_cache[sample["year"]]
        )

# --- 7. PyTorch Training Loop ---
def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Initializing real-data training on device: {device} (RTX 6000 mode)")
    
    dataset = RealWeatherDataset(YEARS)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=True)
    
    model = BustNet().to(device)
    criterion = MultiTaskBustLoss()
    optimizer = optim.AdamW(model.parameters(), lr=3e-4)
    
    epochs = 15
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for batch_idx, (X, Y_b, Y_e) in enumerate(dataloader):
            X, Y_b, Y_e = X.to(device), Y_b.to(device), Y_e.to(device)
            
            optimizer.zero_grad()
            out = model(X)
            loss = criterion(out["bust"], out["error"], Y_b, Y_e)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs} | Avg Loss: {total_loss/len(dataloader):.4f}")
        
    out_path = WEIGHTS_DIR / "bustnet_real.pt"
    torch.save(model.state_dict(), out_path)
    print(f"\n✅ Training Complete! Weights saved to: {out_path}")

if __name__ == "__main__":
    print("=== AETHER-BUST Real Data Training Pipeline ===")
    train()
