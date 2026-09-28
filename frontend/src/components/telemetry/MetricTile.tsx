import React from 'react';
import { Card } from '../common/Card';

interface MetricTileProps {
  label: string;
  value: string | number;
  delta?: number;
  deltaLabel?: string;
  inverse?: boolean;
}

export const MetricTile: React.FC<MetricTileProps> = ({ label, value, delta, deltaLabel, inverse = false }) => {
  let deltaColor = 'text-text-muted';
  let deltaSymbol = '';
  
  if (delta !== undefined) {
    if (delta > 0) {
      deltaColor = inverse ? 'text-status-crit' : 'text-status-ok';
      deltaSymbol = '↑';
    } else if (delta < 0) {
      deltaColor = inverse ? 'text-status-ok' : 'text-status-crit';
      deltaSymbol = '↓';
    }
  }

  return (
    <Card className="flex flex-col gap-1 p-3">
      <div className="text-xs font-semibold text-text-secondary uppercase tracking-wider">{label}</div>
      <div className="flex items-baseline justify-between">
        <div className="text-xl font-bold text-text-primary">{value}</div>
        {delta !== undefined && (
          <div className={`text-xs font-medium ${deltaColor}`}>
            {deltaSymbol}{Math.abs(delta).toFixed(1)}{deltaLabel}
          </div>
        )}
      </div>
    </Card>
  );
};
