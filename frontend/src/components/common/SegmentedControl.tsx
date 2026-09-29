import { cn } from './Pill';

interface SegmentedControlProps<T extends string> {
  options: { label: string; value: T; sublabel?: string }[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

export function SegmentedControl<T extends string>({ options, value, onChange, className }: SegmentedControlProps<T>) {
  return (
    <div className={cn("flex bg-bg-inset p-1 rounded-md gap-1", className)}>
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            "flex-1 py-1.5 px-3 text-sm rounded-md transition-colors font-medium flex flex-col items-center justify-center",
            value === opt.value 
              ? "bg-panel text-ink border border-line-strong" 
              : "text-ink-dim hover:text-ink hover:bg-panel border border-transparent"
          )}
        >
          <span>{opt.label}</span>
          {opt.sublabel && <span className="text-xs text-text-muted font-normal">{opt.sublabel}</span>}
        </button>
      ))}
    </div>
  );
}
