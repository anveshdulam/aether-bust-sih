import numpy as np

# Spatial Domain
PHI_MIN = 6.0
PHI_MAX = 37.75
LAMBDA_MIN = 68.0
LAMBDA_MAX = 99.75
DELTA = 0.25
H = 128
W = 128

# Temporal Domain
T = 10

# Target Variables & Predictors
C = 10
V = 4
VAR_CODES = ("t2m", "tp", "z500", "ws850")
CHANNEL_CODES = ("t2m", "tp", "z500", "u850", "v850", "ws850", "cape", "mslp", "z500_anom", "shear_850_250")

# Determinism
SEED = 26079

# Bust Thresholds and Confidence Weights
TAU = {"t2m": 3.0, "tp": 20.0, "z500": 60.0, "ws850": 5.0}
W_CONF = {"t2m": 0.25, "tp": 0.35, "z500": 0.25, "ws850": 0.15}

# Other threshold constants
TP_EVENT = 20.0
BF_CRIT = 0.30
MIN_BLOB_CELLS = 9

def lat_vector() -> np.ndarray:
    return np.linspace(PHI_MIN, PHI_MAX, H, dtype=np.float32)

def lon_vector() -> np.ndarray:
    return np.linspace(LAMBDA_MIN, LAMBDA_MAX, W, dtype=np.float32)
