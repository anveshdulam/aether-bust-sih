import torch
import numpy as np
from app.constants import SEED, T, C, H, W, CHANNEL_CODES
from app.ml.architecture import BustNet
from app.ml.xai import gradcam, integrated_gradients, narrative


def _model():
    torch.manual_seed(SEED)
    return BustNet().eval()


def _input():
    g = torch.Generator().manual_seed(SEED)
    return torch.randn(1, T, C, H, W, generator=g)


def test_gradcam_shape_and_range():
    cam = gradcam(_model(), _input(), v=0, t=0)
    assert cam.shape == (H, W)
    assert np.isfinite(cam).all()
    assert (cam >= 0.0).all() and (cam <= 1.0).all()


def test_gradcam_respects_lead_time_index():
    """Hooks must resolve the decoder call for the requested lead time."""
    model, X = _model(), _input()
    for t in (0, 5, T - 1):
        cam = gradcam(model, X, v=1, t=t)
        assert cam.shape == (H, W)
        assert (cam >= 0.0).all() and (cam <= 1.0).all()


def test_gradcam_regional_pooling():
    mask = np.zeros((H, W), dtype=np.float32)
    mask[40:70, 40:70] = 1.0
    cam = gradcam(_model(), _input(), v=0, t=3, region_mask=mask)
    assert cam.shape == (H, W)
    assert (cam >= 0.0).all() and (cam <= 1.0).all()


def test_integrated_gradients_ten_drivers_sum_to_one():
    mask = np.ones((H, W), dtype=np.float32)
    drivers = integrated_gradients(_model(), _input(), v=0, t=0, region_mask=mask, n_steps=2)

    assert len(drivers) == C
    assert {d["code"] for d in drivers} == set(CHANNEL_CODES)
    assert abs(sum(d["score"] for d in drivers) - 1.0) < 1e-6
    assert all(0.0 <= d["score"] <= 1.0 for d in drivers)
    assert all(d["sign"] in ("+", "-") for d in drivers)
    # sorted descending by score
    scores = [d["score"] for d in drivers]
    assert scores == sorted(scores, reverse=True)


def test_integrated_gradients_degenerate_input_is_uniform():
    """Input identical to the baseline yields zero attribution; stay sum-to-one."""
    X = torch.zeros(1, T, C, H, W)
    mask = np.ones((H, W), dtype=np.float32)
    drivers = integrated_gradients(_model(), X, v=0, t=0, region_mask=mask, n_steps=2)

    assert len(drivers) == C
    assert abs(sum(d["score"] for d in drivers) - 1.0) < 1e-6
    assert all(abs(d["score"] - 1.0 / C) < 1e-6 for d in drivers)


def test_narrative_mentions_top_two_drivers():
    drivers = [
        {"code": "cape", "score": 0.42, "sign": "+"},
        {"code": "tp_qpf", "score": 0.21, "sign": "-"},
    ] + [{"code": "t2m_fc", "score": 0.0, "sign": "+"} for _ in range(8)]

    text = narrative(7, "tp", "Konkan", drivers)
    assert "Day 7" in text
    assert "tp" in text
    assert "Konkan" in text
    assert "cape" in text and "tp_qpf" in text
    assert "42%" in text and "21%" in text
