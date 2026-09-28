export interface ColorStop {
  stop: number;
  rgba: [number, number, number, number];
  hex: string;
}

// 3.1 SCALE_CONFIDENCE (0–100 confidence index)
export const SCALE_CONFIDENCE: ColorStop[] = [
  { stop: 0.00, hex: '#7A0C2E', rgba: [122, 12, 46, 255] },
  { stop: 0.15, hex: '#B21E3B', rgba: [178, 30, 59, 255] },
  { stop: 0.30, hex: '#E4572E', rgba: [228, 87, 46, 255] },
  { stop: 0.50, hex: '#F2C14E', rgba: [242, 193, 78, 255] },
  { stop: 0.70, hex: '#8FD14F', rgba: [143, 209, 79, 255] },
  { stop: 0.85, hex: '#2EA043', rgba: [46, 160, 67, 255] },
  { stop: 1.00, hex: '#1B6E9B', rgba: [27, 110, 155, 255] }
];

// 3.2 SCALE_BUST_RISK (0–1 bust probability)
export const SCALE_BUST_RISK: ColorStop[] = [
  { stop: 0.00, hex: '#0D3B66', rgba: [13, 59, 102, 255] },
  { stop: 0.15, hex: '#1B7FA8', rgba: [27, 127, 168, 255] },
  { stop: 0.30, hex: '#2EB398', rgba: [46, 179, 152, 255] },
  { stop: 0.45, hex: '#9BD64A', rgba: [155, 214, 74, 255] },
  { stop: 0.55, hex: '#F4D03F', rgba: [244, 208, 63, 255] },
  { stop: 0.70, hex: '#F39C12', rgba: [243, 156, 18, 255] },
  { stop: 0.82, hex: '#E8412E', rgba: [232, 65, 46, 255] },
  { stop: 0.92, hex: '#C2185B', rgba: [194, 24, 91, 255] },
  { stop: 1.00, hex: '#FF1FA0', rgba: [255, 31, 160, 255] }
];

// 3.3 SCALE_ERROR_DIVERGING (signed error)
export const SCALE_ERROR_DIVERGING: ColorStop[] = [
  { stop: 0.00, hex: '#053061', rgba: [5, 48, 97, 255] },
  { stop: 0.25, hex: '#4393C3', rgba: [67, 147, 195, 255] },
  { stop: 0.50, hex: '#F7F7F7', rgba: [247, 247, 247, 255] },
  { stop: 0.75, hex: '#D6604D', rgba: [214, 96, 77, 255] },
  { stop: 1.00, hex: '#67001F', rgba: [103, 0, 31, 255] }
];

// 3.4 Predictor Overlay Ramps
export const SCALE_PRECIP: ColorStop[] = [
  { stop: 0.00, hex: '#FFFFFF00', rgba: [255, 255, 255, 0] },
  { stop: 0.25, hex: '#A6D96A', rgba: [166, 217, 106, 255] },
  { stop: 0.50, hex: '#1A9850', rgba: [26, 152, 80, 255] },
  { stop: 0.75, hex: '#313695', rgba: [49, 54, 149, 255] },
  { stop: 1.00, hex: '#762A83', rgba: [118, 42, 131, 255] }
];

export const SCALE_WIND: ColorStop[] = [
  { stop: 0.00, hex: '#EDF8FB', rgba: [237, 248, 251, 255] },
  { stop: 0.33, hex: '#2CA25F', rgba: [44, 162, 95, 255] },
  { stop: 0.66, hex: '#006D2C', rgba: [0, 109, 44, 255] },
  { stop: 1.00, hex: '#99000D', rgba: [153, 0, 13, 255] }
];

export const SCALE_GEOPOT: ColorStop[] = [
  { stop: 0.00, hex: '#313695', rgba: [49, 54, 149, 255] },
  { stop: 0.25, hex: '#74ADD1', rgba: [116, 173, 209, 255] },
  { stop: 0.50, hex: '#FFFFBF', rgba: [255, 255, 191, 255] },
  { stop: 0.75, hex: '#F46D43', rgba: [244, 109, 67, 255] },
  { stop: 1.00, hex: '#A50026', rgba: [165, 0, 38, 255] }
];
