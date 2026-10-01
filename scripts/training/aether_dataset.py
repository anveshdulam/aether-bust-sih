import json
import datetime
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

import sys
backend_path = str(Path(__file__).resolve().parents[2] / "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.constants import (
    VAR_CODES, CHANNEL_CODES, TAU,
    PHI_MIN, PHI_MAX, LAMBDA_MIN, LAMBDA_MAX,
    H, W, T, C, V
)

class AetherDataset(Dataset):
    """
    Phase C Dataset:
    - Loads pre-processed real-data numpy samples (X, Yb_true, Ye_true).
    - Ensures samples are partitioned chronologically (no random mixing).
    - Preserves exact canonical tensor shapes and normalizations.
    """
    
    def __init__(self, data_dir: str, start_date: str = None, end_date: str = None):
        super().__init__()
        self.data_dir = Path(data_dir)
        
        # Load all run directories that match the prefix
        all_runs = sorted([d for d in self.data_dir.iterdir() if d.is_dir() and d.name.startswith("real_")])
        
        # Parse filter dates
        dt_start = datetime.datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.datetime.min
        dt_end = datetime.datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.datetime.max
        
        self.samples = []
        for run_dir in all_runs:
            # Extract date from "real_YYYYMMDD"
            date_str = run_dir.name.split("_")[1]
            run_dt = datetime.datetime.strptime(date_str, "%Y%m%d")
            
            if dt_start <= run_dt <= dt_end:
                self.samples.append(run_dir)
                
        print(f"AetherDataset initialized: {len(self.samples)} samples found between {start_date or 'BEGIN'} and {end_date or 'END'}.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        run_dir = self.samples[idx]
        
        X = np.load(run_dir / "X.npy")
        Yb_true = np.load(run_dir / "Yb_true.npy")
        Ye_true = np.load(run_dir / "Ye_true.npy")
        
        # Convert to float32 tensors
        X_tensor = torch.from_numpy(X).to(torch.float32)
        Yb_tensor = torch.from_numpy(Yb_true).to(torch.float32)
        Ye_tensor = torch.from_numpy(Ye_true).to(torch.float32)
        
        # Contract checks per TRD §2.2
        assert X_tensor.shape == (T, C, H, W), f"Invalid X shape: {X_tensor.shape}"
        assert Yb_tensor.shape == (T, V, H, W), f"Invalid Yb shape: {Yb_tensor.shape}"
        assert Ye_tensor.shape == (T, V, H, W), f"Invalid Ye shape: {Ye_tensor.shape}"
        
        return X_tensor, Yb_tensor, Ye_tensor

if __name__ == "__main__":
    # Test initialization
    dataset = AetherDataset(data_dir="data/processed2")
    if len(dataset) > 0:
        X, Yb, Ye = dataset[0]
        print(f"Sample 0 X shape: {X.shape}, Dtype: {X.dtype}")
