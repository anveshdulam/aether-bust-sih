import { useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { TileLayer } from '@deck.gl/geo-layers';
import { BitmapLayer, PathLayer } from '@deck.gl/layers';
import { useAppStore } from '../../store/useAppStore';
import { useConfidenceMap } from '../../api/queries';
import { createRasterImage } from './gridUtils';
import { ScrubberBar } from './ScrubberBar';
import { useBustPolygonLayer } from './useBustPolygonLayer';

const turboColormap = [
  [48, 18, 59], [62, 74, 137], [49, 104, 142], [38, 130, 142],
  [31, 158, 137], [53, 183, 121], [109, 205, 89], [180, 222, 44],
  [240, 229, 33], [253, 174, 97], [244, 109, 67], [213, 62, 79],
  [158, 1, 66]
];

const getConfidenceColor = (val: number): [number, number, number, number] => {
  const normalized = Math.max(0, Math.min(1, 1 - val));
  
  if (val > 0.8) return [0, 0, 0, 0];

  const maxIdx = turboColormap.length - 1;
  const exactIdx = normalized * maxIdx;
  const idx1 = Math.floor(exactIdx);
  const idx2 = Math.ceil(exactIdx);
  const frac = exactIdx - idx1;

  const c1 = turboColormap[idx1];
  const c2 = turboColormap[idx2];

  const r = c1[0] + (c2[0] - c1[0]) * frac;
  const g = c1[1] + (c2[1] - c1[1]) * frac;
  const b = c1[2] + (c2[2] - c1[2]) * frac;
  
  const a = val < 0.2 ? 220 : val < 0.5 ? 180 : 120;

  return [r, g, b, a];
};

export const RiskMap = () => {
  const { runId, viewState, setViewState, setSelectedCell, activeRaster, opacity } = useAppStore();
  
  const { data: confidenceData } = useConfidenceMap(runId, 1);
  const bustLayer = useBustPolygonLayer();

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
      textureParameters: {
        10241: 9729,
        10240: 9729,
      }
    });
  }, [confidenceData, activeRaster, opacity]);

  const layers = [
    new TileLayer({
      id: 'basemap-tiles',
      data: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
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
    bustLayer,
    new TileLayer({
      id: 'label-tiles',
      data: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
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
        for (let lat = 10; lat <= 35; lat += 5) {
          lines.push({ path: [[68.0, lat], [99.75, lat]] });
        }
        for (let lon = 70; lon <= 95; lon += 5) {
          lines.push({ path: [[lon, 6.0], [lon, 37.75]] });
        }
        return lines;
      })(),
      pickable: false,
      widthScale: 1,
      widthMinPixels: 1,
      getColor: [217, 224, 234, 30],
      getPath: d => d.path
    }),
  ].filter(Boolean);

  return (
    <div className="w-full h-full relative bg-inset overflow-hidden cursor-crosshair">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState }) => setViewState(viewState as any)}
        controller={true}
        layers={layers as any[]}
        onClick={(info) => {
          if (info.coordinate) {
            setSelectedCell([info.coordinate[1], info.coordinate[0]]);
          }
        }}
        getCursor={({ isHovering }) => isHovering ? 'pointer' : 'crosshair'}
      />
      <div className="absolute bottom-4 left-4 bg-panel border border-line p-2 font-mono text-11 text-ink flex gap-4 pointer-events-none">
        <span>{viewState.latitude.toFixed(2)}°N {viewState.longitude.toFixed(2)}°E</span>
        <span>zoom: {viewState.zoom.toFixed(1)}</span>
        <span>layer: {activeRaster}</span>
      </div>
      <ScrubberBar />
    </div>
  );
};

