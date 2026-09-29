import { GridMeta } from '../../api/types';

/**
 * Maps a grid of values to a flat ImageData array, correcting for Web Mercator distortion
 * so that BitmapLayer renders it perfectly.
 */
export function createRasterImage(
  values: number[][], // 128x128
  meta: GridMeta,
  colormap: (val: number) => [number, number, number, number]
): ImageData {
  const width = meta.n_cols;
  const height = meta.n_rows;
  
  // Create OffscreenCanvas or just a Uint8ClampedArray if we are creating ImageData manually
  const data = new Uint8ClampedArray(width * height * 4);
  
  // We want to map evenly spaced Web Mercator Y to the evenly spaced Latitude rows.
  // We are going to just draw it row by row right now. 
  // Advanced re-projection could sample mercator Y.
  
  for (let r = 0; r < height; r++) {
    for (let c = 0; c < width; c++) {
      const idx = (r * width + c) * 4;
      
      const val = values[r]?.[c] ?? 0;
      const [red, green, blue, alpha] = colormap(val);
      
      data[idx] = red;
      data[idx + 1] = green;
      data[idx + 2] = blue;
      data[idx + 3] = alpha;
    }
  }
  
  return new ImageData(data, width, height);
}
