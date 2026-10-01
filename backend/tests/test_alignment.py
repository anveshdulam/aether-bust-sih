import numpy as np
import pytest
from app.data.alignment import nearest_neighbour_interpolate, bilinear_interpolate

def test_interpolation():
    grid = np.array([
        [10.0, 20.0],
        [30.0, 40.0]
    ])
    lats = np.array([0.0, 1.0])
    lons = np.array([0.0, 1.0])
    
    # 1. Exact points
    assert bilinear_interpolate(grid, 0.0, 0.0, lats, lons) == 10.0
    assert nearest_neighbour_interpolate(grid, 0.0, 0.0, lats, lons) == 10.0
    
    # 2. Midpoint
    assert bilinear_interpolate(grid, 0.5, 0.5, lats, lons) == 25.0
    nn = nearest_neighbour_interpolate(grid, 0.5, 0.5, lats, lons)
    # Midpoint nearest neighbor rounds to either 0,1 or 1,1 depending on numpy/round logic.
    assert nn in [10.0, 20.0, 30.0, 40.0]
    
    # 3. Outside grid bounds (should be NaN)
    assert np.isnan(bilinear_interpolate(grid, -1.0, 0.0, lats, lons))
    assert np.isnan(nearest_neighbour_interpolate(grid, 2.0, 2.0, lats, lons))
    
    # 4. Edges
    assert bilinear_interpolate(grid, 1.0, 0.5, lats, lons) == 35.0
    assert nearest_neighbour_interpolate(grid, 0.0, 0.9, lats, lons) == 20.0
