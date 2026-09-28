import React from 'react';
import { useConsoleStore } from '../../store/useConsoleStore';

const BANDS = [
  { id: 'VERY_LOW', label: 'Very Low', color: '#B21E3B' },
  { id: 'LOW', label: 'Low', color: '#E4572E' },
  { id: 'MODERATE', label: 'Moderate', color: '#F2C14E' },
  { id: 'HIGH', label: 'High', color: '#8FD14F' },
  { id: 'VERY_HIGH', label: 'Very High', color: '#2EA043' }
];

export const ConfidenceBandFilter: React.FC = () => {
  const { activeBands, setActiveBands } = useConsoleStore();
  
  const toggleBand = (id: string) => {
    if (activeBands.includes(id)) {
      setActiveBands(activeBands.filter(b => b !== id));
    } else {
      setActiveBands([...activeBands, id]);
    }
  };

  return (
    <div className="p-4 border-b border-border-subtle">
      <div className="text-sm font-semibold text-text-primary mb-3">Confidence Bands</div>
      <div className="flex flex-wrap gap-2">
        {BANDS.map(b => {
          const active = activeBands.includes(b.id);
          return (
            <button
              key={b.id}
              onClick={() => toggleBand(b.id)}
              className="px-2 py-1 text-xs rounded-sm transition-colors border"
              style={{
                borderColor: b.color,
                backgroundColor: active ? `${b.color}30` : 'transparent',
                color: active ? '#FFF' : '#9FB0C9'
              }}
            >
              {b.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};
