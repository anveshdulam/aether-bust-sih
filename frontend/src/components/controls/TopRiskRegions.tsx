import { useAppStore } from '../../store/useAppStore';
import { useBustDetections } from '../../api/queries';
import { FlyToInterpolator } from '@deck.gl/core';

export const TopRiskRegions = () => {
  const { runId, leadTime, setViewState, setSelectedCell } = useAppStore();
  const { data: detections } = useBustDetections(runId, leadTime);

  // BustDetection uses peak_probability now, wait no, let's check types.ts, it uses peak_probability!
  // I will just calculate lat and lon from bbox and use peak_probability.
  const topRegions = detections
    ? [...detections].sort((a, b) => b.peak_probability - a.peak_probability).slice(0, 5)
    : [];

  const handleRegionClick = (lat: number, lon: number) => {
    setViewState({
      latitude: lat,
      longitude: lon,
      zoom: 7,
      pitch: 0,
      bearing: 0,
      transitionDuration: 1500,
      transitionInterpolator: new FlyToInterpolator()
    });
    setSelectedCell([lat, lon]);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">Top Risk Regions</div>
      {topRegions.length === 0 ? (
        <div className="text-sm text-text-muted italic px-1 py-2">No high-risk regions detected.</div>
      ) : (
        <div className="flex flex-col gap-1">
          {topRegions.map((region, idx) => {
            const lon = (region.bbox[0] + region.bbox[2]) / 2;
            const lat = (region.bbox[1] + region.bbox[3]) / 2;
            
            return (
              <button
                key={`${region.detection_id}-${idx}`}
                onClick={() => handleRegionClick(lat, lon)}
                className="flex justify-between items-center px-3 py-2 text-sm rounded bg-bg-raised hover:bg-bg-raised/80 border border-transparent hover:border-border transition-all text-left group"
              >
                <div className="flex flex-col">
                  <span className="text-text-primary group-hover:text-accent font-medium transition-colors">
                    {lat.toFixed(2)}°N, {lon.toFixed(2)}°E
                  </span>
                  <span className="text-[11px] text-text-muted">Day {leadTime}</span>
                </div>
                <div className="text-right">
                  <div className={`font-mono font-bold ${region.peak_probability >= 0.8 ? 'text-status-red' : 'text-status-amber'}`}>
                    {(region.peak_probability * 100).toFixed(0)}%
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
