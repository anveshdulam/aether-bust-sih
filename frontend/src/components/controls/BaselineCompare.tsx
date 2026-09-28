import React from 'react';
import { useConsoleStore } from '../../store/useConsoleStore';

export const BaselineCompare: React.FC = () => {
  const { baselineCompare, setBaselineCompare } = useConsoleStore();
  
  return (
    <div className="p-4">
      <label className="flex items-center gap-3 cursor-pointer group">
        <input 
          type="checkbox" 
          checked={baselineCompare}
          onChange={(e) => setBaselineCompare(e.target.checked)}
          className="accent-accent-primary w-4 h-4"
        />
        <div>
          <div className="text-sm font-semibold text-text-primary">Baseline Compare</div>
          <div className="text-xs text-text-muted">Anomaly vs historical baselines</div>
        </div>
      </label>
    </div>
  );
};
