import numpy as np
import pytest
from app.ml.masking import extract_blobs

def test_masking():
    p_agg = np.zeros((128, 128), dtype=np.float32)
    p_agg[10:14, 10:14] = 0.8

    blobs = extract_blobs(p_agg)
    assert len(blobs) == 1
    b = blobs[0]
    assert b.n_cells == 16
    # p_agg is float32, so 0.8 round-trips as 0.800000011920929
    assert b.peak_probability == pytest.approx(0.8, abs=1e-6)
    assert b.mean_probability == pytest.approx(0.8, abs=1e-6)
    assert len(b.bbox) == 4

    p_agg[50:52, 50:52] = 0.9
    blobs2 = extract_blobs(p_agg)
    assert len(blobs2) == 1

def test_bbox_contains_polygon():
    """PRD 3.5: the reported bbox must fully contain the convex-hull polygon."""
    p_agg = np.zeros((128, 128), dtype=np.float32)
    p_agg[30:40, 60:75] = 0.75
    p_agg[32, 80] = 0.99  # isolated cell, below MIN_BLOB_CELLS -> discarded

    blobs = extract_blobs(p_agg)
    assert len(blobs) == 1
    b = blobs[0]

    min_x, min_y, max_x, max_y = b.bbox
    ring = b.polygon["coordinates"][0]
    assert len(ring) >= 4
    for lon, lat in ring:
        assert min_x <= lon <= max_x
        assert min_y <= lat <= max_y

def test_min_blob_cells_discarded():
    p_agg = np.zeros((128, 128), dtype=np.float32)
    p_agg[5:7, 5:7] = 0.95  # 4 cells < MIN_BLOB_CELLS (9)
    assert extract_blobs(p_agg) == []
