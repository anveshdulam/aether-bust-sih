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
    <div className="mb-6">
      <div className="text-11 uppercase tracking-widest text-ink-dim mb-2 font-mono">Target Variable</div>
      <div className="grid grid-cols-2 gap-1">
        {options.map(opt => (
          <button
            key={opt.id}
            onClick={() => setVariable(opt.id)}
            className={`px-3 py-2 border font-mono text-xs flex flex-col items-center transition-colors ${
              variable === opt.id
                ? 'bg-ink text-base border-ink'
                : 'bg-transparent text-ink border-line hover:bg-inset'
            }`}
          >
            <span className="font-bold">{opt.id}</span>
            <span className="text-11 mt-0.5 opacity-70">{opt.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
