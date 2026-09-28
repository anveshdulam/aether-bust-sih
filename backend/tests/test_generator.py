import json
import numpy as np
import xarray as xr

def test_generator_outputs(synthetic_run):
    X = np.load(synthetic_run["X"])
    Yb = np.load(synthetic_run["Yb_true"])
    Ye = np.load(synthetic_run["Ye_true"])
    
    assert X.shape == (1, 10, 10, 128, 128)
    assert Yb.shape == (10, 4, 128, 128)
    assert Ye.shape == (10, 4, 128, 128)
    
    assert X.dtype == np.float32
    assert Yb.dtype == np.float32
    assert Ye.dtype == np.float32
    
    assert not np.isnan(X).any() and not np.isinf(X).any()
    
    assert Yb.sum() >= 1
    
    with open(synthetic_run["norm_stats"]) as f:
        stats = json.load(f)
        assert len(stats["MU"]) == 10
        assert len(stats["SIGMA"]) == 10
        
    ds = xr.open_dataset(synthetic_run["run"])
    assert ds.dims["lead_time"] == 10
    assert ds.dims["lat"] == 128
    assert ds.dims["lon"] == 128
