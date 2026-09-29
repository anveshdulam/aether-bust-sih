import { create } from 'zustand';
import { VarCode } from '../api/types';

interface ViewState {
  longitude: number;
  latitude: number;
  zoom: number;
  pitch: number;
  bearing: number;
}

interface AppState {
  runId: string | null;
  variable: VarCode;
  selectedCell: [number, number] | null; // [lat, lon]
  activeRaster: 'confidence' | 'p_bust' | 'error' | 'baseline';
  opacity: number;
  confidenceBand: [number, number];
  baselineMode: boolean;
  leadTime: number;
  viewState: ViewState;

  // Actions
  setRunId: (id: string | null) => void;
  setVariable: (v: VarCode) => void;
  setSelectedCell: (cell: [number, number] | null) => void;
  setActiveRaster: (raster: 'confidence' | 'p_bust' | 'error' | 'baseline') => void;
  setOpacity: (opacity: number) => void;
  setConfidenceBand: (band: [number, number]) => void;
  setBaselineMode: (mode: boolean) => void;
  setViewState: (vs: ViewState) => void;
  setLeadTime: (lt: number) => void;
}

// Helper to parse URL params initially
const getInitialStateFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  const cellParam = params.get('cell');
  
  return {
    runId: params.get('run') || null,
    variable: (params.get('var') as VarCode) || 't2m',
    selectedCell: cellParam ? (cellParam.split(',').map(Number) as [number, number]) : null,
    activeRaster: (params.get('raster') as 'confidence' | 'p_bust') || 'confidence',
    opacity: Number(params.get('op')) || 0.8,
    baselineMode: params.get('base') === 'true',
    leadTime: Number(params.get('lt')) || 1,
  };
};

const initialUrlState = getInitialStateFromUrl();

export const useAppStore = create<AppState>((set) => ({
  runId: initialUrlState.runId,
  variable: initialUrlState.variable,
  selectedCell: initialUrlState.selectedCell,
  activeRaster: initialUrlState.activeRaster,
  opacity: initialUrlState.opacity,
  confidenceBand: [0, 1],
  baselineMode: initialUrlState.baselineMode,
  leadTime: initialUrlState.leadTime,
  viewState: {
    longitude: 83.87, // Center of India
    latitude: 21.87,
    zoom: 4,
    pitch: 0,
    bearing: 0,
  },

  setRunId: (id) => set({ runId: id }),
  setVariable: (variable) => set({ variable }),
  setSelectedCell: (cell) => set({ selectedCell: cell }),
  setActiveRaster: (raster) => set({ activeRaster: raster }),
  setOpacity: (opacity) => set({ opacity }),
  setConfidenceBand: (band) => set({ confidenceBand: band }),
  setBaselineMode: (mode) => set({ baselineMode: mode }),
  setViewState: (vs) => set({ viewState: vs }),
  setLeadTime: (lt) => set({ leadTime: lt }),
}));

// Sync Zustand state to URL (one-way: Store -> URL)
useAppStore.subscribe((state) => {
  const params = new URLSearchParams(window.location.search);
  
  if (state.runId) params.set('run', state.runId);
  else params.delete('run');
  
  params.set('var', state.variable);
  params.set('raster', state.activeRaster);
  params.set('op', state.opacity.toString());
  params.set('lt', state.leadTime.toString());
  
  if (state.selectedCell) {
    params.set('cell', `${state.selectedCell[0].toFixed(2)},${state.selectedCell[1].toFixed(2)}`);
  } else {
    params.delete('cell');
  }

  if (state.baselineMode) params.set('base', 'true');
  else params.delete('base');

  const newUrl = `${window.location.pathname}?${params.toString()}`;
  if (newUrl !== window.location.pathname + window.location.search) {
    window.history.replaceState({}, '', newUrl);
  }
});
