import React from 'react';
import { useTelemetry } from '../../api/queries';
import { cn } from '../common/Pill';

export const AlertsTicker: React.FC = () => {
  const { data: telemetry } = useTelemetry();

  const alerts = telemetry?.filter(t => t.kind === 'ALERT') || [];

  if (alerts.length === 0) return null;

  return (
    <div className="bg-bg-panel border-t border-border-strong px-4 py-1.5 flex items-center gap-4 overflow-hidden shrink-0">
      <div className="text-xs font-bold text-status-crit uppercase tracking-widest shrink-0">CRITICAL ALERTS</div>
      <div className="flex gap-6 overflow-x-auto whitespace-nowrap text-xs text-text-primary scrollbar-hide">
        {alerts.map((a, i) => (
          <div key={a.event_id} className="flex items-center gap-2">
            <span className={cn("w-1.5 h-1.5 rounded-sm", a.severity === 'CRITICAL' ? 'bg-status-crit' : 'bg-status-warn')} />
            <span>{a.message}</span>
            {i < alerts.length - 1 && <span className="text-text-muted ml-4">|</span>}
          </div>
        ))}
      </div>
    </div>
  );
};
