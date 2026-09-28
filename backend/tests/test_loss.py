import torch
from app.ml.loss import MultiTaskBustLoss
from app.ml.architecture import BustNet

def test_loss_scalar_and_degenerate():
    loss_fn = MultiTaskBustLoss()
    Yb_pred = torch.full((1, 10, 4, 128, 128), 0.5)
    Ye_pred = torch.full((1, 10, 4, 128, 128), 10.0)
    
    Yb_true = torch.full((1, 10, 4, 128, 128), 1.0)
    Ye_true = torch.full((1, 10, 4, 128, 128), 20.0)
    
    loss = loss_fn(Yb_pred, Ye_pred, Yb_true, Ye_true)
    assert loss.item() > 0
    assert loss.dim() == 0
    
    # Degenerate
    loss_zero = loss_fn(Yb_true, Ye_true, Yb_true, Ye_true)
    assert abs(loss_zero.item()) < 1e-5

def test_loss_gradients():
    model = BustNet()
    loss_fn = MultiTaskBustLoss()
    x = torch.zeros(1, 10, 10, 128, 128)
    out = model(x)
    
    Yb_true = torch.zeros(1, 10, 4, 128, 128)
    Ye_true = torch.zeros(1, 10, 4, 128, 128)
    
    loss = loss_fn(out["bust"], out["error"], Yb_true, Ye_true)
    loss.backward()
    
    has_none = False
    for p in model.parameters():
        if p.grad is None:
            has_none = True
    assert not has_none
