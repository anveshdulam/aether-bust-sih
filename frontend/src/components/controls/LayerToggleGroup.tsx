import React from 'react';
import { useConsoleStore } from '../../store/useConsoleStore';
import { LayerCode } from '../../api/types';

export const LayerToggleGroup: React.FC = () => {
  const { layer, setLayer } = useConsoleStore();
  
  const layers: { val: LayerCode, label: string }[] = [
    { val: 'confidence', label: 'Confidence Index' },
    { val: 'p_bust', label: 'Bust Probability' },
    { val: 'error', label: 'Error' }
  ];

  return (
    <div className="p-4 border-b border-border-subtle">
      <div className="text-sm font-semibold text-text-primary mb-3">Active Layer</div>
      <div className="flex flex-col gap-2">
        {layers.map(l => (
          <label key={l.val} className="flex items-center gap-2 cursor-pointer group">
            <input 
              type="radio" 
              name="layer" 
              value={l.val} 
              checked={layer === l.val} 
              onChange={() => setLayer(l.val)}
              className="accent-accent-primary"
            />
            <span className={layer === l.val ? 'text-text-primary' : 'text-text-secondary group-hover:text-text-primary'}>
              {l.label}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
};
