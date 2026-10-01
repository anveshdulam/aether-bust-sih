import numpy as np
from app.constants import T, C, H, W, V

class BaselineDetector:
    """
    Statistical baseline (non-ML) detection engine.
    Calculates residuals (forecast - observation) and flags busts based on dynamic thresholds.
    """

    def __init__(self, thresholds_path: str = None):
        # In a real system, these thresholds would be loaded from a config or NetCDF climatology file.
        # For the demo, we generate dynamic synthetic thresholds per cell and variable.
        self.thresholds = self._load_or_generate_thresholds(thresholds_path)

    def _load_or_generate_thresholds(self, path):
        # We need thresholds for each variable (V) at each grid cell (H, W).
        # We simulate a "3.2 sigma" threshold approach.
        # Shape: (V, H, W)
        # 0: Temperature, 1: Precipitation, 2: Wind, 3: Humidity (Example mapped to V=4 output variables)
        base_thresholds = np.ones((V, H, W), dtype=np.float32)
        base_thresholds[0, :, :] = 5.0  # e.g., 5 degrees error
        base_thresholds[1, :, :] = 20.0 # e.g., 20mm rainfall error
        base_thresholds[2, :, :] = 10.0 # e.g., 10m/s wind error
        base_thresholds[3, :, :] = 15.0 # e.g., 15% humidity error
        return base_thresholds

    def calculate_residuals(self, forecast: np.ndarray, observation: np.ndarray) -> np.ndarray:
        """
        Calculate the absolute residual between forecast and observation.
        forecast shape: (T, V, H, W)
        observation shape: (T, V, H, W)
        Returns shape: (T, V, H, W)
        """
        # Ensure dimensions match
        if forecast.shape != observation.shape:
            raise ValueError(f"Shape mismatch: {forecast.shape} vs {observation.shape}")
        return np.abs(forecast - observation)

    def detect_busts(self, residuals: np.ndarray) -> np.ndarray:
        """
        Flag cells where the residual exceeds the dynamic threshold.
        Returns a boolean array of shape (T, V, H, W) or (T, H, W) if fused across variables.
        Here we return the boolean flag per variable.
        """
        # Broadcast thresholds across time dimension
        thresholds_t = np.broadcast_to(self.thresholds, residuals.shape)
        return residuals > thresholds_t

    def get_reason(self, v_idx: int, residual_val: float, threshold_val: float) -> str:
        """
        Generate a plain-language reason string for a baseline bust.
        """
        var_names = ["Temperature", "Precipitation", "Wind", "Humidity"]
        var_name = var_names[v_idx] if v_idx < len(var_names) else f"Variable {v_idx}"
        return f"{var_name} residual ({residual_val:.1f}) exceeded historical dynamic threshold ({threshold_val:.1f})"
