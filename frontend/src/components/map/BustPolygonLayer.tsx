import { GeoJsonLayer } from '@deck.gl/layers';
import { BustDetection } from '../../api/types';
import { SCALE_BUST_RISK } from '../../theme/colormaps';
import { createColorScale } from '../../utils/colorScale';

const riskScale = createColorScale(SCALE_BUST_RISK, 1);

export function createBustPolygonLayer(
  id: string,
  detections: BustDetection[],
  opacity: number,
  onHover?: (info: any) => void,
  onClick?: (info: any) => void
) {
  if (!detections || detections.length === 0) return null;

  const geojsonData = {
    type: 'FeatureCollection' as const,
    features: detections.map(d => ({
      type: 'Feature' as const,
      geometry: d.polygon,
      properties: {
        id: d.detection_id,
        peak: d.peak_probability,
        driver: d.dominant_driver,
        conf: d.confidence
      }
    }))
  };

  return new GeoJsonLayer({
    id,
    data: geojsonData,
    opacity,
    stroked: true,
    filled: true,
    extruded: false,
    lineWidthUnits: 'pixels',
    lineWidthMinPixels: 2,
    lineWidthMaxPixels: 6,
    lineWidthScale: 1.5,
    getFillColor: (f: any) => {
      const [r, g, b] = riskScale(f.properties.peak);
      return [r, g, b, 75]; // Soft, premium semi-transparent fill
    },
    getLineColor: (f: any) => {
      const [r, g, b] = riskScale(f.properties.peak);
      return [r, g, b, 255]; // Vibrant, opaque border matching the risk level
    },
    getLineWidth: 2,
    pickable: true,
    autoHighlight: true,
    highlightColor: [255, 255, 255, 60],
    onHover,
    onClick
  });
}
