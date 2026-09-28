import React, { useEffect } from 'react';
import { useConsoleStore } from '../../store/useConsoleStore';

export const ScrubberBar: React.FC = () => {
  const { leadTime, setLeadTime, playing, setPlaying } = useConsoleStore();

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
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs text-text-muted">
        <span>Day 1</span>
        <span>Day 10</span>
      </div>
      <div className="flex items-center gap-4">
        <button 
          onClick={() => setPlaying(!playing)}
          className="w-10 h-10 shrink-0 bg-bg-elevated border border-border-strong rounded-sm flex items-center justify-center text-accent-primary hover:bg-bg-inset transition-colors"
        >
          {playing ? '⏸' : '▶'}
        </button>
        <input 
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
        <div className="shrink-0 font-mono text-sm w-16 text-right">
          Day {leadTime}
        </div>
      </div>
    </div>
  );
};
