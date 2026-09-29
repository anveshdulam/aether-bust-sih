import { useAppStore } from '../../store/useAppStore';
import { useAttribution } from '../../api/queries';

export const AttributionPanel = () => {
  const { runId, variable, leadTime, selectedCell } = useAppStore();

  const { data: attr, isLoading } = useAttribution(
    runId,
    variable,
    leadTime,
    selectedCell ? selectedCell[0] : 0,
    selectedCell ? selectedCell[1] : 0,
    !!selectedCell
  );

  if (!selectedCell) {
    return (
      <div className="flex flex-col h-full">
        <p className="max-w-[40ch] leading-5 text-ink-dim font-mono text-sm">
          Select a cell on the map to see why BustNet expects this forecast to fail or hold.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="text-sm text-ink-dim font-mono">Running attribution analysis...</div>
      </div>
    );
  }

  if (!attr) {
    return (
      <div className="flex flex-col h-full">
        <div className="text-sm text-ink-dim font-mono">No attribution data found.</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full font-mono text-sm">
      <div className="mb-6">
        <div className="text-11 uppercase tracking-widest text-ink-dim mb-2 border-b border-line pb-1">
          Cell Context
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-ink-dim text-11">Location</div>
            <div className="font-bold">{attr.lat.toFixed(2)}°N, {attr.lon.toFixed(2)}°E</div>
          </div>
          <div>
            <div className="text-ink-dim text-11">Target</div>
            <div className="font-bold">{attr.variable} (+{attr.lead_time}d)</div>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <div className="text-11 uppercase tracking-widest text-ink-dim mb-2 border-b border-line pb-1">
          Top Drivers
        </div>
        <div className="flex flex-col gap-2">
          {attr.drivers.map((driver) => (
            <div key={driver.channel_code} className="flex justify-between items-center bg-inset px-3 py-2 border border-line">
              <div>
                <div className="font-bold">{driver.channel_code}</div>
                <div className="text-11 text-ink-dim">{driver.channel_name}</div>
              </div>
              <div className="text-right">
                <div className={`font-bold ${driver.sign === '+' ? 'text-[#D0702F]' : 'text-[#5A8F70]'}`}>
                  {driver.sign} {(driver.score * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <div className="text-11 uppercase tracking-widest text-ink-dim mb-2 border-b border-line pb-1">
          Summary Narrative
        </div>
        <div className="leading-5 text-ink">
          {attr.narrative}
        </div>
      </div>

      {/* GradCAM Mini Map could go here */}
      <div className="flex-1" />
      <div className="text-11 text-ink-dim border-t border-line pt-2 mt-4">
        Attribution computed via Captum Integrated Grads on BustNet v1.
      </div>
    </div>
  );
};
