import React, { useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';

export const ScrubberBar: React.FC = () => {
  const { leadTime, setLeadTime } = useAppStore();
  // playing state not in useAppStore currently, let's keep it local
  const [playing, setPlaying] = React.useState(false);

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
              className="w-full accent-accent-primary"
            />
            <div className="shrink-0 font-mono text-sm w-16 text-right text-text-primary">
              Day {leadTime}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
