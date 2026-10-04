import numpy as np
from enum import Enum

class Severity(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class FusionEngine:
    """
    Fuses outputs from the Statistical Baseline and Deep Learning (BustNet) layers.
    Controls false-positives by requiring agreement for High/Critical alerts.
    """



    def fuse(self, baseline_flags: np.ndarray, ml_probs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Takes baseline boolean flags (T, V, H, W) and ML probabilities (T, H, W) or (T, V, H, W)
        and outputs a fused confidence map (0-1) and severity map (0-3 for enum).
        
        For simplicity, let's assume baseline_flags is reduced to (T, H, W) by taking any(axis=1)
        and ml_probs is (T, H, W) [0.0 to 1.0].
        
        Returns:
            fused_confidence: np.ndarray of shape (T, H, W)
            severity_map: np.ndarray of shape (T, H, W) encoded as int (0: Low, 1: Medium, 2: High, 3: Critical)
        """
        # Reduce baseline flags across variables if not already done: True if ANY variable busted.
        if baseline_flags.ndim == 4:
            base_flag = np.any(baseline_flags, axis=1) # Shape: (T, H, W)
        else:
            base_flag = baseline_flags

        # Base confidence is ML prob. But we adjust based on baseline agreement.
        # If baseline=False and ML=High, confidence decreases (ML might be hallucinating).
        # If baseline=True and ML=High, confidence increases.
        
        fused_confidence = np.copy(ml_probs)
        
        # Boost confidence when baseline agrees, penalize when it disagrees
        fused_confidence = np.where(base_flag & (ml_probs > 0.5), np.clip(ml_probs + 0.2, 0, 1), fused_confidence)
        fused_confidence = np.where(~base_flag & (ml_probs > 0.5), np.clip(ml_probs - 0.2, 0, 1), fused_confidence)

        # Calculate Severity based on fused confidence and agreement
        severity_map = np.zeros_like(fused_confidence, dtype=np.int8) # 0: LOW
        
        # Medium: ML prob > 0.4 or Baseline is True
        severity_map = np.where((fused_confidence > 0.4) | base_flag, 1, severity_map)
        
        # High: ML prob > 0.7 AND Baseline is True
        severity_map = np.where((fused_confidence > 0.7) & base_flag, 2, severity_map)
        
        # Critical: ML prob > 0.9 AND Baseline is True
        severity_map = np.where((fused_confidence > 0.9) & base_flag, 3, severity_map)
        
        # Quality check to drop sensor blips (isolated single pixels) can be added here
        # e.g., using scipy.ndimage for morphological opening.
        
        return fused_confidence, severity_map

    @staticmethod
    def get_severity_label(val: int) -> str:
        mapping = {0: Severity.LOW.value, 1: Severity.MEDIUM.value, 2: Severity.HIGH.value, 3: Severity.CRITICAL.value}
        return mapping.get(val, Severity.LOW.value)
