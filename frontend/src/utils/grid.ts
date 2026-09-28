import { GridMeta } from '../api/types';

// Converts lat/lon to grid indices based on GridMeta
export function coordToIndex(lat: number, lon: number, grid: GridMeta): [number, number] {
  // PRD 0.1: array is [lat(south->north), lon(west->east)]
  // But API returns it north-up (row 0 = lat_max). So row index:
  const row = Math.round((grid.lat_max - lat) / grid.resolution);
  const col = Math.round((lon - grid.lon_min) / grid.resolution);
  return [Math.max(0, Math.min(grid.n_rows - 1, row)), Math.max(0, Math.min(grid.n_cols - 1, col))];
}

// Converts grid indices to lat/lon
export function indexToCoord(row: number, col: number, grid: GridMeta): [number, number] {
  const lat = grid.lat_max - (row * grid.resolution);
  const lon = grid.lon_min + (col * grid.resolution);
  return [lat, lon];
}
