import React from 'react';

export const BottomStrip: React.FC = () => {
  return (
    <div className="h-10 bg-bg-panel border-t border-border-subtle flex items-center px-4 justify-between shrink-0 text-xs text-text-muted">
      <div className="flex items-center gap-2">
        <span>●</span>
        <span>Monitoring Telemetry...</span>
      </div>
      <div className="flex gap-4">
        {/* GridReadout placeholder */}
        <div id="grid-readout" className="font-mono">
          Hover map for readout
        </div>
      </div>
    </div>
  );
};
