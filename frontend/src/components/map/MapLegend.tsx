import React from 'react';

export const MapLegend: React.FC = () => {
  return (
    <div className="absolute top-4 right-4 z-[500] bg-bg-panel/90 p-3 rounded-lg shadow-panel border border-border-subtle">
      <div className="text-xs font-semibold mb-2">Legend</div>
      <div className="w-48 h-2 bg-gradient-to-r from-[#0D3B66] to-[#FF1FA0] rounded-sm mb-1" />
      <div className="flex justify-between text-[10px] text-text-muted">
        <span>Low</span>
        <span>High</span>
      </div>
    </div>
  );
};
