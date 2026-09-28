import { BitmapLayer } from '@deck.gl/layers';
import { GridMeta } from '../../api/types';
import { ColorStop } from '../../theme/colormaps';
import { createColorScale } from '../../utils/colorScale';

export function createDeckGridLayer(
  id: string,
  grid: GridMeta | undefined,
  values: number[][] | undefined, // 128x128
  stops: ColorStop[],
  opacity: number,
  domainMax: number = 100
) {
  if (!grid || !values) return null;

  // Create an offscreen canvas to render the 128x128 grid
  const canvas = document.createElement('canvas');
  canvas.width = grid.n_cols;
  canvas.height = grid.n_rows;
  const ctx = canvas.getContext('2d');
  
  if (ctx) {
    const imgData = ctx.createImageData(grid.n_cols, grid.n_rows);
    const colorScale = createColorScale(stops, domainMax);
    
    for (let i = 0; i < grid.n_rows; i++) {
      for (let j = 0; j < grid.n_cols; j++) {
        const val = values[i]?.[j];
        const idx = (i * grid.n_cols + j) * 4;
        
        if (val !== undefined && val !== null) {
          const [r, g, b, a] = colorScale(val);
          imgData.data[idx] = r;
          imgData.data[idx + 1] = g;
          imgData.data[idx + 2] = b;
          imgData.data[idx + 3] = a;
        } else {
          imgData.data[idx + 3] = 0; // transparent
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);
  }

  return new BitmapLayer({
    id,
    bounds: [grid.lon_min, grid.lat_min, grid.lon_max, grid.lat_max],
    image: canvas,
    opacity,
    pickable: true,
  });
}
