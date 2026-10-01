import { create } from 'zustand';

export type VariableType = 't2m' | 'tp' | 'z500' | 'ws850';
export type LayerType = 'confidence' | 'bust' | 'error';
export type ConfidenceBand = 'VERY_LOW' | 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';

export interface SelectionState {
  mode: 'none' | 'cell' | 'region';
  lat?: number;
  lon?: number;
  bbox?: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
}

interface ConsoleState {
  runId: string | null;
  source: string;
  variable: VariableType;
  layer: LayerType;
  leadTime: number; // 1 to 10
  opacity: number;
  activeBands: ConfidenceBand[];
  selection: SelectionState;
  baselineCompare: boolean;
  playing: boolean;
  activeOverlays: string[]; // e.g. ['precip', 'wind']

  // Actions
  setRunId: (id: string | null) => void;
  setVariable: (v: VariableType) => void;
  setLayer: (l: LayerType) => void;
  setLeadTime: (t: number) => void;
  setOpacity: (o: number) => void;
  toggleBand: (band: ConfidenceBand) => void;
  setSelection: (sel: SelectionState) => void;
  setBaselineCompare: (b: boolean) => void;
  setPlaying: (p: boolean) => void;
  toggleOverlay: (overlay: string) => void;
}

export const useConsoleStore = create<ConsoleState>((set) => ({
  runId: null,
  source: 'GFS',
  variable: 'tp',
  layer: 'confidence',
  leadTime: 1,
  opacity: 0.85,
  activeBands: ['VERY_LOW', 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH'],
  selection: { mode: 'none' },
  baselineCompare: false,
  playing: false,
  activeOverlays: [],

  setRunId: (id) => set({ runId: id }),
  setVariable: (v) => set({ variable: v }),
  setLayer: (l) => set({ layer: l }),
  setLeadTime: (t) => set({ leadTime: Math.max(1, Math.min(10, t)) }),
  setOpacity: (o) => set({ opacity: Math.max(0.15, Math.min(0.95, o)) }),
  toggleBand: (band) =>
    set((state) => ({
      activeBands: state.activeBands.includes(band)
        ? state.activeBands.filter((b) => b !== band)
        : [...state.activeBands, band],
    })),
  setSelection: (sel) => set({ selection: sel }),
  setBaselineCompare: (b) => set({ baselineCompare: b }),
  setPlaying: (p) => set({ playing: p }),
  toggleOverlay: (overlay) =>
    set((state) => ({
      activeOverlays: state.activeOverlays.includes(overlay)
        ? state.activeOverlays.filter((o) => o !== overlay)
        : [...state.activeOverlays, overlay],
    })),
}));
