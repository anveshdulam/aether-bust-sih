import React, { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { useBustDetections } from '../../api/queries';

export const ScrubberBar: React.FC = () => {
  const { runId, leadTime, setLeadTime } = useAppStore();
  const [playing, setPlaying] = React.useState(false);
  const [riskyDays, setRiskyDays] = useState<number[]>([]);

  // To find risky days, we can either fetch them all or just simulate a quick scan.
  // Since we know the model generates extreme alerts on Day 9/Day 10 (synthetic), 
  // we can use a lightweight fetch for all 10 days to see if they have detections >= 0.8
  useEffect(() => {
    if (!runId) return;
    let mounted = true;
    
    // Fire off 10 lightweight requests to populate the markers. In production, 
    // this would be a single /timeline-summary endpoint.
    Promise.all(
      Array.from({length: 10}, (_, i) => i + 1).map(day => 
        fetch(`http://localhost:8000/api/v1/bust-detections?run_id=${runId}&lead_time=${day}`)
          .then(res => res.json())
          .then(data => ({ day, hasRisk: data.items?.some((d: any) => d.peak_probability >= 0.8) }))
          .catch(() => ({ day, hasRisk: false }))
      )
    ).then(results => {
      if (!mounted) return;
      setRiskyDays(results.filter(r => r.hasRisk).map(r => r.day));
    });

    return () => { mounted = false; };
  }, [runId]);

  useEffect(() => {
    let interval: number;
    if (playing) {
      interval = window.setInterval(() => {
        setLeadTime(leadTime >= 10 ? 1 : leadTime + 1);
      }, 900);
    }
    return () => clearInterval(interval);
  }, [playing, leadTime, setLeadTime]);

  return (
    <div className="absolute bottom-4 left-0 right-0 px-12 z-20">
      <div className="bg-bg-panel/90 border border-border-subtle rounded-sm p-3">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-text-muted px-12">
            <span>Day 1</span>
            <span>Day 10</span>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setPlaying(!playing)}
              className="w-10 h-10 shrink-0 bg-bg-elevated border border-border-strong rounded-md flex items-center justify-center text-accent-primary hover:bg-bg-inset transition-colors"
            >
              {playing ? '⏸' : '▶'}
            </button>
            <div className="w-full relative flex items-center">
              {/* Event Markers Container */}
              <div className="absolute left-0 right-0 h-full pointer-events-none px-2 z-0 flex items-center">
                {Array.from({length: 10}, (_, i) => i + 1).map(day => (
                  <div 
                    key={day} 
                    className="absolute h-2 w-1 -translate-y-1/2 top-1/2 rounded-full transition-opacity"
                    style={{ 
                      left: `${((day - 1) / 9) * 100}%`,
                      backgroundColor: riskyDays.includes(day) ? '#ef4444' : 'transparent', // Tailwind red-500
                      boxShadow: riskyDays.includes(day) ? '0 0 8px #ef4444' : 'none'
                    }} 
                  />
                ))}
              </div>
              
              <input 
                id="scrubber"
                type="range"
                min="1"
                max="10"
                step="1"
                value={leadTime}
                onChange={(e) => {
                  setPlaying(false);
                  setLeadTime(parseInt(e.target.value));
                }}
                className="w-full accent-accent-primary relative z-10"
                style={{ background: 'transparent' }} // Let markers show behind the track if possible
              />
            </div>
            <div className="shrink-0 font-mono text-sm w-16 text-right text-text-primary">
              Day {leadTime}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
