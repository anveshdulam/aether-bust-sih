import { useAppStore } from '../../store/useAppStore';
import { VarCode } from '../../api/types';

export const VariableToggle = () => {
  const { variable, setVariable } = useAppStore();

  const options: { id: VarCode; label: string; unit: string }[] = [
    { id: 't2m', label: '2m Temp', unit: 'K' },
    { id: 'tp', label: 'Precip', unit: 'mm' },
    { id: 'z500', label: 'Geopotential', unit: 'gpm' },
    { id: 'ws850', label: 'Wind Shear', unit: 'm/s' }
  ];

  return (
    <div className="flex flex-col gap-2">
      <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">Target Variable</div>
      <div className="flex bg-bg-raised p-0.5 rounded border border-border">
        {options.map(opt => (
          <button
            key={opt.id}
            onClick={() => setVariable(opt.id)}
            className={`flex-1 flex flex-col items-center py-1.5 px-1 rounded-sm text-xs transition-colors ${
              variable === opt.id
                ? 'bg-bg-panel text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-primary hover:bg-bg-panel/50'
            }`}
          >
            <span className="font-semibold">{opt.label}</span>
            <span className="text-[10px] opacity-70 font-mono">{opt.id}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
