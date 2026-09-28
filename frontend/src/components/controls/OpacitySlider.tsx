import React from 'react';
import { useConsoleStore } from '../../store/useConsoleStore';

export const OpacitySlider: React.FC = () => {
  const { opacity, setOpacity } = useConsoleStore();
  
  return (
    <div className="p-4 border-b border-border-subtle">
      <div className="flex justify-between items-center mb-2">
        <div className="text-sm font-semibold text-text-primary">Opacity</div>
        <div className="text-xs text-text-muted font-mono">{Math.round(opacity * 100)}%</div>
      </div>
      <input 
        type="range" 
        min="0.15" 
        max="0.95" 
        step="0.05"
        value={opacity}
        onChange={(e) => setOpacity(parseFloat(e.target.value))}
        className="w-full accent-accent-primary"
      />
    </div>
  );
};
