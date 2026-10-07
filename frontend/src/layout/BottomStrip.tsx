import React from 'react';
import { useAppStore } from '../store/useAppStore';

export const BottomStrip: React.FC = () => {
  const { viewState, activeRaster } = useAppStore();

  return (
    <div className="h-8 bg-bg-canvas border-t border-border flex items-center px-4 justify-between shrink-0 text-[11px] text-text-muted font-mono tracking-wide z-20">
      <div className="flex items-center gap-6">
        <div className="flex gap-2">
          <span>{viewState.latitude.toFixed(2)}°N {viewState.longitude.toFixed(2)}°E</span>
          <span className="text-border">|</span>
          <span>Zoom: {viewState.zoom.toFixed(1)}</span>
          <span className="text-border">|</span>
          <span>Layer: {activeRaster}</span>
        </div>
      </div>
      <div className="flex items-center gap-4 text-text-muted/70">
        <span>AETHER v1.0.0</span>
        <span className="text-border">|</span>
        <span>Source: GFS 0.25°</span>
      </div>
    </div>
  );
};
