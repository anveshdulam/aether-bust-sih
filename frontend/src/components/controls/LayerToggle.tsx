import { useAppStore } from '../../store/useAppStore';

export const LayerToggle = () => {
  const { activeRaster, setActiveRaster, opacity, setOpacity } = useAppStore();

  const options: { id: 'confidence' | 'baseline' | 'error' | 'p_bust'; label: string }[] = [
    { id: 'confidence', label: 'BustNet Confidence' },
    { id: 'p_bust', label: 'Bust Probability Risk' },
    { id: 'baseline', label: 'Baseline Err' },
    { id: 'error', label: 'Predicted Err' }
  ];

  return (
    <div className="mb-6">
      <div className="text-11 uppercase tracking-widest text-ink-dim mb-2 font-mono">Raster Layer</div>
      <div className="flex flex-col gap-1 mb-4">
        {options.map(opt => (
          <button
            key={opt.id}
            onClick={() => setActiveRaster(opt.id)}
            className={`text-left px-3 py-2 text-xs font-mono border transition-colors ${
              activeRaster === opt.id
                ? 'bg-ink text-base border-ink'
                : 'bg-transparent text-ink border-line hover:bg-inset'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
      
      <div className="flex justify-between items-baseline mb-2">
        <div className="text-11 uppercase tracking-widest text-ink-dim font-mono">Opacity</div>
        <div className="text-xs font-mono text-ink">{(opacity * 100).toFixed(0)}%</div>
      </div>
      <input
        type="range"
        min={0}
        max={1}
        step={0.1}
        value={opacity}
        onChange={(e) => setOpacity(parseFloat(e.target.value))}
        className="w-full accent-ink bg-inset h-1 outline-none appearance-none cursor-pointer"
      />
    </div>
  );
};
