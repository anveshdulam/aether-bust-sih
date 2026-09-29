import MockAdapter from 'axios-mock-adapter';
import { apiClient } from './client';
import { ConfidenceMapResponse, GridMeta, AttributionResponse } from './types';

export const mock = new MockAdapter(apiClient, { delayResponse: 500 });

const gridMeta: GridMeta = {
  lat_min: 6.0,
  lat_max: 37.75,
  lon_min: 68.0,
  lon_max: 99.75,
  resolution: 0.25,
  n_rows: 128,
  n_cols: 128,
};

// Generate some mock confidence map values (128x128 array)
const generateMockGrid = () => {
  const grid: number[][] = [];
  for (let r = 0; r < 128; r++) {
    const row: number[] = [];
    for (let c = 0; c < 128; c++) {
      // Create some spatial pattern: higher confidence near center, lower at edges
      const dist = Math.sqrt(Math.pow(r - 64, 2) + Math.pow(c - 64, 2));
      let val = 1.0 - (dist / 64) * 0.8; 
      val = Math.max(0, Math.min(1, val + (Math.random() * 0.2 - 0.1)));
      row.push(val);
    }
    grid.push(row);
  }
  return grid;
};

mock.onGet(/\/confidence\/.+/).reply((config) => {
  const url = config.url || '';
  const run_id = url.split('/').pop() || 'sim-1';
  
  const response: ConfidenceMapResponse = {
    run_id,
    lead_time: config.params?.lead_time || 1,
    grid: gridMeta,
    values: generateMockGrid(),
    stats: { min: 0.1, max: 0.98, mean: 0.65 }
  };
  return [200, response];
});

mock.onGet('/attribution').reply((config) => {
  const params = config.params || {};
  const response: AttributionResponse = {
    run_id: params.run_id || 'sim-1',
    variable: params.variable || 't2m',
    lead_time: params.lead_time || 1,
    lat: params.lat || 20.0,
    lon: params.lon || 80.0,
    drivers: [
      { channel_code: 'ws850', channel_name: '850 hPa Wind Shear', score: 0.85, sign: '+' },
      { channel_code: 'z500', channel_name: '500 hPa Geopotential', score: 0.42, sign: '+' },
      { channel_code: 't2m', channel_name: '2m Temperature', score: 0.31, sign: '-' },
    ],
    spatial_gradcam: generateMockGrid(),
    narrative: `Bust risk is 73% for this cell. The main contributors are 850 hPa wind shear (97th percentile for the season) and few similar past cases. BustNet and the baseline differ by 6.2 mm.`
  };
  return [200, response];
});

mock.onGet('/forecast-runs').reply(200, {
  items: [
    {
      run_id: 'sim-1',
      init_time: new Date().toISOString(),
      source_model: 'SYNTHETIC',
      n_lead_times: 10,
      created_at: new Date().toISOString(),
      mean_confidence: 0.82
    }
  ]
});

mock.onAny().reply(404);
