import { useMemo } from 'react';
import { GeoJsonLayer } from '@deck.gl/layers';
import { useBustDetections } from '../../api/queries';
import { useAppStore } from '../../store/useAppStore';
import { SCALE_BUST_RISK } from '../../theme/colormaps';

const getPolygonColor = (val: number): [number, number, number, number] => {
  const normalized = Math.max(0, Math.min(1, val));
  
  // Find color stop
  let lower = SCALE_BUST_RISK[0];
  let upper = SCALE_BUST_RISK[SCALE_BUST_RISK.length - 1];
  
  for (let i = 0; i < SCALE_BUST_RISK.length - 1; i++) {
    if (normalized >= SCALE_BUST_RISK[i].stop && normalized <= SCALE_BUST_RISK[i+1].stop) {
      lower = SCALE_BUST_RISK[i];
      upper = SCALE_BUST_RISK[i+1];
      break;
    }
  }
  
  const range = upper.stop - lower.stop;
  const frac = range === 0 ? 0 : (normalized - lower.stop) / range;
  
  const r = lower.rgba[0] + (upper.rgba[0] - lower.rgba[0]) * frac;
  const g = lower.rgba[1] + (upper.rgba[1] - lower.rgba[1]) * frac;
  const b = lower.rgba[2] + (upper.rgba[2] - lower.rgba[2]) * frac;
  const a = lower.rgba[3] + (upper.rgba[3] - lower.rgba[3]) * frac;
  
  return [r, g, b, a];
};

export const useBustPolygonLayer = () => {
  const { runId, activeRaster, opacity, setSelectedCell, leadTime } = useAppStore();
  const { data: detections } = useBustDetections(runId, leadTime);

  return useMemo(() => {
    if (!detections || activeRaster !== 'p_bust') return null;

    const geojsonData = {
      type: 'FeatureCollection',
      features: detections.map((d: any) => ({
        type: 'Feature',
        geometry: d.polygon,
        properties: {
          detection_id: d.detection_id,
          peak_probability: d.peak_probability,
          mean_probability: d.mean_probability,
          dominant_driver: d.dominant_driver,
          bbox: d.bbox
        }
      }))
    };

    return new GeoJsonLayer({
      id: 'bust-polygon-layer',
      data: geojsonData as any,
      opacity: opacity,
      stroked: true,
      filled: true,
      extruded: false,
      wireframe: true,
      getFillColor: (f: any) => getPolygonColor(f.properties.peak_probability),
      getLineColor: [255, 255, 255, 255],
      getLineWidth: 2,
      lineWidthMinPixels: 2,
      pickable: true,
      onClick: (info: any) => {
        if (info.object) {
          // Calculate centroid of bbox
          const [min_lat, min_lon, max_lat, max_lon] = info.object.properties.bbox;
          const centerLat = (min_lat + max_lat) / 2;
          const centerLon = (min_lon + max_lon) / 2;
          setSelectedCell([centerLat, centerLon]);
        }
      }
    });
  }, [detections, activeRaster, opacity, setSelectedCell]);
};
