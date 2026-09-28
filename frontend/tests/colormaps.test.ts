import { expect, test, describe } from 'vitest';
import {
  SCALE_CONFIDENCE,
  SCALE_BUST_RISK,
  SCALE_ERROR_DIVERGING
} from '../src/theme/colormaps';

describe('Colormaps UX-4 Assertions', () => {
  test('SCALE_CONFIDENCE matches UI_UX_DOC.md control points exactly', () => {
    expect(SCALE_CONFIDENCE.length).toBe(7);
    expect(SCALE_CONFIDENCE[0]).toEqual({ stop: 0.00, hex: '#7A0C2E', rgba: [122, 12, 46, 255] });
    expect(SCALE_CONFIDENCE[6]).toEqual({ stop: 1.00, hex: '#1B6E9B', rgba: [27, 110, 155, 255] });
  });

  test('SCALE_BUST_RISK matches UI_UX_DOC.md control points exactly', () => {
    expect(SCALE_BUST_RISK.length).toBe(9);
    expect(SCALE_BUST_RISK[0]).toEqual({ stop: 0.00, hex: '#0D3B66', rgba: [13, 59, 102, 255] });
    expect(SCALE_BUST_RISK[8]).toEqual({ stop: 1.00, hex: '#FF1FA0', rgba: [255, 31, 160, 255] });
  });

  test('SCALE_ERROR_DIVERGING matches UI_UX_DOC.md control points exactly', () => {
    expect(SCALE_ERROR_DIVERGING.length).toBe(5);
    expect(SCALE_ERROR_DIVERGING[0]).toEqual({ stop: 0.00, hex: '#053061', rgba: [5, 48, 97, 255] });
    expect(SCALE_ERROR_DIVERGING[4]).toEqual({ stop: 1.00, hex: '#67001F', rgba: [103, 0, 31, 255] });
  });
});
