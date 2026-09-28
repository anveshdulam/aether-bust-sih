import { create } from 'zustand';
import { VarCode, LayerCode, LeadTime, BBox } from '../api/types';

interface SelectionState {
  mode: 'none' | 'cell' | 'region';
  lat?: number;
  lon?: number;
  bbox?: BBox;
}

interface ConsoleStore {
  runId: string | null;
  variable: VarCode;
  layer: LayerCode;
  leadTime: LeadTime;
  opacity: number;
  activeBands: string[];
  selection: SelectionState;
  baselineCompare: boolean;
  playing: boolean;
  
  setRunId: (id: string | null) => void;
  setVariable: (v: VarCode) => void;
  setLayer: (l: LayerCode) => void;
  setLeadTime: (t: LeadTime) => void;
  setOpacity: (o: number) => void;
  setActiveBands: (bands: string[]) => void;
  setSelection: (sel: SelectionState) => void;
  setBaselineCompare: (b: boolean) => void;
  setPlaying: (p: boolean) => void;
}

export const useConsoleStore = create<ConsoleStore>((set) => ({
  runId: null,
  variable: 't2m',
  layer: 'confidence',
  leadTime: 1,
  opacity: 0.85,
  activeBands: ['VERY_LOW', 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH'],
  selection: { mode: 'none' },
  baselineCompare: false,
  playing: false,

  setRunId: (runId) => set({ runId }),
  setVariable: (variable) => set({ variable }),
  setLayer: (layer) => set({ layer }),
  setLeadTime: (leadTime) => set({ leadTime }),
  setOpacity: (opacity) => set({ opacity }),
  setActiveBands: (activeBands) => set({ activeBands }),
  setSelection: (selection) => set({ selection }),
  setBaselineCompare: (baselineCompare) => set({ baselineCompare }),
  setPlaying: (playing) => set({ playing }),
}));
