export function formatNumber(val: number, decimals: number = 2): string {
  return val.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

export function formatCoord(lat: number, lon: number): string {
  const latStr = Math.abs(lat).toFixed(2) + (lat >= 0 ? '°N' : '°S');
  const lonStr = Math.abs(lon).toFixed(2) + (lon >= 0 ? '°E' : '°W');
  return `${latStr}, ${lonStr}`;
}
