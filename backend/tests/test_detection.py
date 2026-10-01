import numpy as np
import pytest

from app.constants import T, C, H, W, V
from app.ml.baseline import BaselineDetector
from app.ml.fusion import FusionEngine, Severity

def test_baseline_detector():
    detector = BaselineDetector()
    # Mock data
    forecast = np.zeros((T, V, H, W), dtype=np.float32)
    obs = np.zeros((T, V, H, W), dtype=np.float32)
    
    # 1. No error case
    residuals = detector.calculate_residuals(forecast, obs)
    flags = detector.detect_busts(residuals)
    assert not np.any(flags), "Should have no flags when forecast equals observation"

    # 2. Large error case (inject error in temperature, which is V=0)
    # Threshold for V=0 is 5.0
    obs[0, 0, 10, 10] = 6.0 
    residuals = detector.calculate_residuals(forecast, obs)
    flags = detector.detect_busts(residuals)
    
    assert flags[0, 0, 10, 10] == True, "Should flag bust when residual > threshold"
    assert not flags[0, 0, 11, 11], "Should not flag unaffected cells"

    # 3. Reason formatting
    reason = detector.get_reason(0, 6.0, 5.0)
    assert "Temperature" in reason
    assert "6.0" in reason

def test_fusion_engine():
    engine = FusionEngine()
    
    # Mock baseline flags: T=10, H=128, W=128
    baseline_flags = np.zeros((T, H, W), dtype=bool)
    # Mock ml_probs: T=10, H=128, W=128
    ml_probs = np.zeros((T, H, W), dtype=np.float32)
    
    # Case 1: Both disagree (Baseline False, ML High) -> False Positive control
    ml_probs[0, 5, 5] = 0.95 
    conf, sev = engine.fuse(baseline_flags, ml_probs)
    # Confidence should be penalized (-0.2), so 0.75. Severity should be 1 (Medium) because it's not supported by baseline
    assert conf[0, 5, 5] == np.float32(0.75)
    assert sev[0, 5, 5] == 1 # Medium

    # Case 2: Both agree (Baseline True, ML High)
    baseline_flags[0, 10, 10] = True
    ml_probs[0, 10, 10] = 0.8
    conf, sev = engine.fuse(baseline_flags, ml_probs)
    # Confidence boosted (+0.2), so 1.0. Severity should be 3 (Critical) because conf > 0.9 and baseline is True
    assert conf[0, 10, 10] == np.float32(1.0)
    assert sev[0, 10, 10] == 3 # Critical

    # Case 3: Baseline True, ML low (ML missed it)
    baseline_flags[0, 20, 20] = True
    ml_probs[0, 20, 20] = 0.1
    conf, sev = engine.fuse(baseline_flags, ml_probs)
    # Confidence untouched because ML is low (or penalization logic doesn't touch it if < 0.5)
    # Severity should be 1 (Medium) because baseline is True but ML is low.
    assert sev[0, 20, 20] == 1 # Medium
