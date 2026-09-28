import React from 'react';
import { DriverBarChart } from './DriverBarChart';
import { GradcamThumb } from './GradcamThumb';
import { NarrativeCard } from './NarrativeCard';
import { useConsoleStore } from '../../store/useConsoleStore';

export const XaiPanel: React.FC = () => {
  const { selection } = useConsoleStore();

  // Mock attribution data to satisfy UI UX-5
  const mockDrivers = [
    { channel_code: 'cape', channel_name: 'CAPE', score: 0.35, sign: '+' as const },
    { channel_code: 'z500', channel_name: 'Geopotential 500hPa', score: 0.22, sign: '+' as const },
    { channel_code: 't850', channel_name: 'Temp 850hPa', score: 0.15, sign: '-' as const },
    { channel_code: 'ws850', channel_name: 'Wind Speed 850hPa', score: 0.12, sign: '+' as const },
    { channel_code: 't2m', channel_name: '2m Temp', score: 0.08, sign: '-' as const },
    { channel_code: 'q850', channel_name: 'Specific Humidity', score: 0.04, sign: '+' as const },
    { channel_code: 'tp', channel_name: 'Total Precip', score: 0.02, sign: '+' as const },
    { channel_code: 'msl', channel_name: 'Mean Sea Level Press', score: 0.01, sign: '-' as const },
    { channel_code: 'u10', channel_name: '10m U Wind', score: 0.005, sign: '+' as const },
    { channel_code: 'v10', channel_name: '10m V Wind', score: 0.005, sign: '-' as const },
  ];

  const mockGradcam = Array.from({ length: 128 }, () => Array.from({ length: 128 }, () => Math.random()));
  const mockNarrative = "Anomalously high CAPE combined with strong Z500 ridging strongly suggests convective initiation, dominating the bust probability in this region.";

  return (
    <div className="flex flex-col gap-4 p-4" id="xai-panel">
      <div className="text-sm font-semibold text-text-primary">Explainability (XAI)</div>
      {!selection ? (
        <div className="text-sm text-text-muted text-center mt-10">Select a bust detection region to view attribution.</div>
      ) : (
        <>
          <NarrativeCard narrative={mockNarrative} />
          <div className="grid grid-cols-[1fr_100px] gap-4">
            <div>
              <div className="text-xs font-semibold text-text-secondary uppercase">Top Drivers (IG)</div>
              <DriverBarChart drivers={mockDrivers} />
            </div>
            <div>
              <div className="text-xs font-semibold text-text-secondary uppercase mb-2">Grad-CAM</div>
              <GradcamThumb gradcam={mockGradcam} />
            </div>
          </div>
        </>
      )}
    </div>
  );
};
