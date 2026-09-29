import { useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { TileLayer } from '@deck.gl/geo-layers';
import { BitmapLayer, PathLayer } from '@deck.gl/layers';
import { useAppStore } from '../../store/useAppStore';
import { useConfidenceMap } from '../../api/queries';
import { createRasterImage } from './gridUtils';



const getConfidenceColor = (val: number): [number, number, number, number] => {
  // Map 0 -> lowest confidence -> opaque red (#B8402F)
  // Map 1 -> highest confidence -> transparent
  if (val > 0.8) return [0, 0, 0, 0]; // Transparent
  
  if (val > 0.5) return [201, 154, 59, 64]; // Ochre (25%)
  if (val > 0.2) return [208, 112, 47, 153]; // Orange (60%)
  
  return [184, 64, 47, 230]; // Brick (90%)
};

export const RiskMap = () => {
  const { runId, viewState, setViewState, setSelectedCell, activeRaster, opacity } = useAppStore();
  
  // Hardcode leadtime 1 for now
  const { data: confidenceData } = useConfidenceMap(runId, 1);

  const rasterLayer = useMemo(() => {
    if (!confidenceData || activeRaster !== 'confidence') return null;

    const { values, grid } = confidenceData;
    const imageData = createRasterImage(values, grid, getConfidenceColor);

    return new BitmapLayer({
      id: 'confidence-raster',
      bounds: [grid.lon_min, grid.lat_min, grid.lon_max, grid.lat_max],
      image: imageData,
      opacity: opacity,
      pickable: false,
    });
  }, [confidenceData, activeRaster, opacity]);

  const layers = [
    new TileLayer({
      id: 'basemap-tiles',
      data: 'https://c.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png',
      minZoom: 0,
      maxZoom: 19,
      tileSize: 256,
      renderSubLayers: (props) => {
        const { boundingBox } = props.tile;
        return new BitmapLayer(props, {
          data: undefined,
          image: props.data,
          bounds: [boundingBox[0][0], boundingBox[0][1], boundingBox[1][0], boundingBox[1][1]]
        });
      }
    }),
    rasterLayer,
    new TileLayer({
      id: 'label-tiles',
      data: 'https://c.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}.png',
      minZoom: 0,
      maxZoom: 19,
      tileSize: 256,
      renderSubLayers: (props) => {
        const { boundingBox } = props.tile;
        return new BitmapLayer(props, {
          data: undefined,
          image: props.data,
          bounds: [boundingBox[0][0], boundingBox[0][1], boundingBox[1][0], boundingBox[1][1]]
        });
      }
    }),
    new PathLayer({
      id: 'graticule',
      data: (() => {
        const lines = [];
        // Latitudes (every 5 degrees)
        for (let lat = 10; lat <= 35; lat += 5) {
          lines.push({ path: [[68.0, lat], [99.75, lat]] });
        }
        // Longitudes (every 5 degrees)
        for (let lon = 70; lon <= 95; lon += 5) {
          lines.push({ path: [[lon, 6.0], [lon, 37.75]] });
        }
        return lines;
      })(),
      pickable: false,
      widthScale: 1,
      widthMinPixels: 1,
      getColor: [217, 224, 234, 30], // ink with low opacity
      getPath: d => d.path
    }),
  ].filter(Boolean);

  return (
    <div className="w-full h-full relative bg-inset overflow-hidden cursor-crosshair">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState }) => setViewState(viewState as any)}
        controller={true}
        layers={layers}
        onClick={(info) => {
          if (info.coordinate) {
            setSelectedCell([info.coordinate[1], info.coordinate[0]]);
          }
        }}
      />
      <div className="absolute bottom-4 left-4 bg-panel border border-line p-2 font-mono text-11 text-ink flex gap-4 pointer-events-none">
        <span>{viewState.latitude.toFixed(2)}°N {viewState.longitude.toFixed(2)}°E</span>
        <span>zoom: {viewState.zoom.toFixed(1)}</span>
        <span>layer: {activeRaster}</span>
      </div>
    </div>
  );
};
