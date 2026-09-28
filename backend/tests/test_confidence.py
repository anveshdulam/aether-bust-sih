import numpy as np
from app.ml.confidence import confidence_index

def test_confidence():
    bust_prob = np.zeros((10, 4, 128, 128), dtype=np.float32)
    conf = confidence_index(bust_prob)
    
    assert conf.shape == (10, 128, 128)
    assert conf.dtype == np.float32
    assert (conf >= 0).all() and (conf <= 100).all()
    
    assert np.allclose(conf, 100.0)
