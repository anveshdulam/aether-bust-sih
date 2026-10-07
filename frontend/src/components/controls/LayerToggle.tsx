import { useAppStore } from '../../store/useAppStore';

export const LayerToggle = () => {
  const { activeRaster, setActiveRaster, opacity, setOpacity } = useAppStore();

  const options: { id: 'confidence' | 'baseline' | 'error' | 'p_bust'; label: string, color: string }[] = [
    { id: 'p_bust', label: 'Bust Probability', color: 'bg-status-red' },
    { id: 'error', label: 'Expected Error', color: 'bg-status-amber' },
    { id: 'confidence', label: 'Model Confidence', color: 'bg-status-sky' },
    { id: 'baseline', label: 'Baseline Error', color: 'bg-status-amber' }
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">Map Layers</div>
        <div className="flex flex-col gap-1">
          {options.map(opt => (
            <button
              key={opt.id}
              onClick={() => setActiveRaster(opt.id)}
              className={`flex items-center gap-3 px-3 py-2 text-[13px] rounded transition-colors ${
                activeRaster === opt.id
                  ? 'bg-bg-raised text-text-primary'
                  : 'bg-transparent text-text-muted hover:bg-bg-raised/50 hover:text-text-primary'
              }`}
            >
              <div className={`w-3 h-3 rounded-sm ${opt.color} ${activeRaster !== opt.id ? 'opacity-50' : ''}`} />
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex flex-col gap-3">
        <div className="flex justify-between items-baseline">
          <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">Opacity</div>
          <div className="text-xs font-mono text-text-primary">{(opacity * 100).toFixed(0)}%</div>
        </div>
        
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={opacity}
            onChange={(e) => setOpacity(parseFloat(e.target.value))}
            className="flex-1 accent-accent bg-bg-raised h-1 outline-none cursor-pointer"
          />
        </div>
        <div className="flex gap-1">
          {[25, 50, 75, 100].map(val => (
            <button 
              key={val}
              onClick={() => setOpacity(val / 100)}
              className="flex-1 py-1 bg-bg-raised hover:bg-bg-raised/80 text-[11px] text-text-muted rounded-sm transition-colors"
            >
              {val}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
