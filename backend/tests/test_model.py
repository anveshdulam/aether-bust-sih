import torch
import pytest
from app.ml.architecture import BustNet, ShapeContractError

def test_model_param_count():
    model = BustNet()
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert 1e6 < n_params < 3e7

def test_model_shapes():
    model = BustNet()
    x = torch.zeros(1, 10, 10, 128, 128)
    out = model(x)
    assert out["bust"].shape == (1, 10, 4, 128, 128)
    assert out["error"].shape == (1, 10, 4, 128, 128)

def test_model_determinism():
    torch.manual_seed(26079)
    model1 = BustNet()
    out1 = model1(torch.zeros(1, 10, 10, 128, 128))
    
    torch.manual_seed(26079)
    model2 = BustNet()
    out2 = model2(torch.zeros(1, 10, 10, 128, 128))
    
    assert torch.allclose(out1["bust"], out2["bust"])
    assert torch.allclose(out1["error"], out2["error"])

def test_model_shape_contract_error():
    model = BustNet()
    with pytest.raises(ShapeContractError):
        model(torch.zeros(1, 10, 10, 128, 64))
