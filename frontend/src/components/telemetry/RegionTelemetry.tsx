import React from 'react';
import { MetricTile } from './MetricTile';
import { ConfidenceByLeadChart } from './ConfidenceByLeadChart';

export const RegionTelemetry: React.FC = () => {
  // Mock data for Phase 5 UI structure
  const chartData = Array.from({ length: 10 }).map((_, i) => ({
    lead_time: i + 1,
    confidence: 100 - (i * 4) + (Math.random() * 10 - 5)
  }));

  return (
    <div className="flex flex-col gap-4 p-4 border-b border-border-subtle">
      <div className="grid grid-cols-2 gap-3">
        <MetricTile label="RMSE" value="1.24" delta={-0.12} inverse />
        <MetricTile label="MAE" value="0.98" delta={-0.05} inverse />
        <MetricTile label="Bust Freq" value="4.2%" delta={1.1} deltaLabel="%" inverse />
        <MetricTile label="Mean Conf" value="82.4" delta={2.4} />
      </div>
      <ConfidenceByLeadChart data={chartData} />
    </div>
  );
};
