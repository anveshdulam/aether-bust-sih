import numpy as np
from app.constants import W_CONF, VAR_CODES

def confidence_index(bust_prob: np.ndarray) -> np.ndarray:
    """
    Computes confidence index: C(t,i,j) = 100 * (1 - sum_v w_v * p_v(t,i,j)) clamped [0,100].
    bust_prob shape: [10, 4, 128, 128]
    Returns: [10, 128, 128]
    """
    w = np.array([W_CONF[v] for v in VAR_CODES], dtype=np.float32)
    # bust_prob is (10, 4, 128, 128) -> w is (4,)
    # w.reshape(1, 4, 1, 1) to broadcast
    w = w.reshape(1, 4, 1, 1)
    
    # sum over variables (axis 1)
    weighted_prob = np.sum(w * bust_prob, axis=1)
    
    conf = 1.0 - weighted_prob
    return np.clip(conf, 0.0, 1.0).astype(np.float32)
