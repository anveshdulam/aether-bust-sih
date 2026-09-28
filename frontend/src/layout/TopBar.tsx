import React, { useEffect, useState } from 'react';
import { useConsoleStore } from '../store/useConsoleStore';
import { useHealth, useRuns } from '../api/queries';
import { StatusDot } from '../components/common/StatusDot';
import { Pill } from '../components/common/Pill';
import { SCALE_CONFIDENCE } from '../theme/colormaps';
import { createCssColorScale } from '../utils/colorScale';

const confScale = createCssColorScale(SCALE_CONFIDENCE, 100);

export const TopBar: React.FC = () => {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const { data: health } = useHealth();
  const { data: runs } = useRuns();
  const { runId, setRunId } = useConsoleStore();

  const activeRun = runs?.find(r => r.run_id === runId);
  
  useEffect(() => {
    if (!runId && runs && runs.length > 0) {
      setRunId(runs[0].run_id);
    }
  }, [runs, runId, setRunId]);

  return (
    <div className="h-14 bg-bg-panel border-b border-border-subtle flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-6">
        <div className="font-bold text-lg tracking-wider text-text-primary">
          <span className="text-accent-primary">AETHER</span>-BUST
        </div>
        
        {/* Run Selector */}
        <select 
          className="bg-bg-inset border border-border-strong rounded-md px-3 py-1.5 text-sm text-text-primary outline-none focus:ring-1 focus:ring-accent-focus"
          value={runId || ''}
          onChange={(e) => setRunId(e.target.value)}
        >
          {runs?.map(r => (
            <option key={r.run_id} value={r.run_id}>
              {new Date(r.init_time).toISOString().substring(0, 16).replace('T', ' ')}Z ({r.source_model})
            </option>
          ))}
          {!runs && <option>Loading runs...</option>}
        </select>
      </div>

      <div className="flex items-center gap-6">
        <div className="font-mono text-text-secondary text-sm">
          {time.toISOString().substring(0, 19).replace('T', ' ')} UTC
        </div>
        
        {activeRun && (
          <Pill color={confScale(activeRun.mean_confidence)}>
            Mean Conf: {activeRun.mean_confidence.toFixed(1)}
          </Pill>
        )}
        
        <div className="flex items-center gap-2" title={`Mongo: ${health?.mongo}, Model: ${health?.model_loaded}`}>
          <span className="text-xs text-text-muted">SYSTEM</span>
          <StatusDot status={health?.status === 'ok' ? 'ok' : 'warn'} />
        </div>
      </div>
    </div>
  );
};
