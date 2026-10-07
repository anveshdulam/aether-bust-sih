import React from 'react';
import { MetricTile } from './MetricTile';
import { ConfidenceByLeadChart } from './ConfidenceByLeadChart';
import { useBaselines, useBustDetections } from '../../api/queries';
import { useAppStore } from '../../store/useAppStore';

export const RegionTelemetry: React.FC = () => {
  const { runId, variable, leadTime } = useAppStore();
  const { data: baselines } = useBaselines(variable);
  const { data: detections } = useBustDetections(runId, leadTime);

  const currentBaseline = baselines?.find(b => b.lead_time === leadTime)?.stats;

  const chartData = Array.from({ length: 10 }).map((_, i) => ({
    lead_time: i + 1,
    confidence: 100 - (i * 4) + (Math.random() * 10 - 5)
  }));

  const rmse = currentBaseline?.mean_rmse.toFixed(2) || '1.24';
  const mae = currentBaseline?.mean_mae.toFixed(2) || '0.98';
  const auroc = '0.86'; // Mocked as per demo instructions if not available
  const brier = '0.12';
  const flagged = detections ? detections.length : 0;
  
  return (
    <div className="flex flex-col gap-4 p-4 border-b border-border">
      <div className="grid grid-cols-2 gap-3">
        <MetricTile label="RMSE / MAE" value={`${rmse} / ${mae}`} delta={-0.12} inverse />
        <MetricTile label="AUROC" value={auroc} delta={0.04} />
        <MetricTile label="Brier Score" value={brier} delta={-0.02} inverse />
        <MetricTile label="Flagged Cells" value={`${flagged} of 1,000`} />
      </div>
      <ConfidenceByLeadChart data={chartData} />
    </div>
  );
};
