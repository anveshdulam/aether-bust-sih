import { useAppStore } from '../../store/useAppStore';
import { LeadTime } from '../../api/types';

export const LeadTimeSlider = () => {
  const { leadTime, setLeadTime } = useAppStore();

  return (
    <div className="mb-6">
      <div className="flex justify-between items-baseline mb-2">
        <div className="text-11 uppercase tracking-widest text-ink-dim font-mono">Lead Time (Days)</div>
        <div className="text-sm font-mono text-ink font-bold">+{leadTime}d</div>
      </div>
      <input
        type="range"
        min={1}
        max={10}
        step={1}
        value={leadTime}
        onChange={(e) => setLeadTime(parseInt(e.target.value, 10) as LeadTime)}
        className="w-full accent-ink bg-inset h-1 outline-none appearance-none cursor-pointer"
      />
      <div className="flex justify-between text-11 text-ink-dim font-mono mt-1">
        <span>1</span>
        <span>5</span>
        <span>10</span>
      </div>
    </div>
  );
};
