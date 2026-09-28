import numpy as np
import torch
from app.ml.architecture import BustNet

def test_phase1_shapes(synthetic_run):
    X = np.load(synthetic_run["X"])
    Yb = np.load(synthetic_run["Yb_true"])
    
    assert X.shape == (1, 10, 10, 128, 128)
    assert Yb.shape == (10, 4, 128, 128)

def test_bustnet_shapes():
    model = BustNet()
    model.eval()
    x = torch.zeros(2, 10, 10, 128, 128)
    out = model(x)
    assert out["bust"].shape == (2, 10, 4, 128, 128)
    assert out["error"].shape == (2, 10, 4, 128, 128)
