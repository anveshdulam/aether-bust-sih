import numpy as np
from scipy.ndimage import label, generate_binary_structure
from shapely.geometry import MultiPoint
import math

class BustBlob:
    def __init__(self, bbox, polygon, peak_p, mean_p, area_km2, dominant_driver, n_cells):
        self.bbox = bbox
        self.polygon = polygon
        self.peak_probability = peak_p
        self.mean_probability = mean_p
        self.area_km2 = area_km2
        self.dominant_driver = dominant_driver
        self.n_cells = n_cells

def get_lat_lon(i, j):
    from app.constants import PHI_MIN, LAMBDA_MIN, DELTA
    return LAMBDA_MIN + j * DELTA, PHI_MIN + i * DELTA

def get_cell_area(i):
    from app.constants import PHI_MIN, DELTA
    lat = PHI_MIN + i * DELTA
    # 1 deg ~ 111.32 km
    dy = DELTA * 111.32
    dx = DELTA * 111.32 * math.cos(math.radians(lat))
    return dx * dy

def extract_blobs(p_agg: np.ndarray, attribution_driver_map: np.ndarray = None) -> list[BustBlob]:
    """
    p_agg: [128, 128]
    attribution_driver_map: [128, 128] optional string map
    Returns: list[BustBlob]
    """
    from app.constants import MIN_BLOB_CELLS
    
    mask = p_agg >= 0.5
    s = generate_binary_structure(2, 2) # 8-connectivity
    labeled_array, num_features = label(mask, structure=s)
    
    blobs = []
    for blob_id in range(1, num_features + 1):
        blob_mask = (labeled_array == blob_id)
        n_cells = blob_mask.sum()
        if n_cells < MIN_BLOB_CELLS:
            continue
            
        peak_p = float(p_agg[blob_mask].max())
        mean_p = float(p_agg[blob_mask].mean())
        
        # Calculate area
        y_idx, x_idx = np.where(blob_mask)
        area_km2 = sum(get_cell_area(i) for i in y_idx)
        
        # Convex hull for polygon
        points = []
        for y, x in zip(y_idx, x_idx):
            lon, lat = get_lat_lon(y, x)
            # Add corners of the cell to the convex hull to ensure bbox contains it properly
            from app.constants import DELTA
            d2 = DELTA / 2
            points.extend([
                (lon - d2, lat - d2), (lon + d2, lat - d2),
                (lon + d2, lat + d2), (lon - d2, lat + d2)
            ])
            
        mp = MultiPoint(points)
        hull = mp.convex_hull
        
        # format to GeoJSON dict
        if hull.geom_type == 'Polygon':
            poly_dict = {"type": "Polygon", "coordinates": [list(hull.exterior.coords)]}
        else:
            poly_dict = {"type": "Polygon", "coordinates": []}
            
        bbox = list(hull.bounds) # [minx, miny, maxx, maxy]
        
        dominant = "t2m"
        if attribution_driver_map is not None:
            from collections import Counter
            drivers = attribution_driver_map[blob_mask].tolist()
            dominant = Counter(drivers).most_common(1)[0][0]
            
        blobs.append(BustBlob(
            bbox=bbox,
            polygon=poly_dict,
            peak_p=peak_p,
            mean_p=mean_p,
            area_km2=area_km2,
            dominant_driver=dominant,
            n_cells=int(n_cells)
        ))
    return blobs
