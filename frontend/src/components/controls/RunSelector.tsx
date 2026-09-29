import { useAppStore } from '../../store/useAppStore';
import { useRuns } from '../../api/queries';

export const RunSelector = () => {
  const { data: runs, isLoading } = useRuns();
  const { runId, setRunId } = useAppStore();

  if (isLoading) return <div className="text-sm text-ink-dim font-mono">Loading runs...</div>;
  if (!runs || runs.length === 0) return <div className="text-sm text-ink-dim font-mono">No runs available.</div>;

  return (
    <div className="mb-6">
      <div className="text-11 uppercase tracking-widest text-ink-dim mb-2 font-mono">Forecast Run</div>
      <div className="flex flex-col gap-1">
        {runs.map(run => (
          <button
            key={run.run_id}
            onClick={() => setRunId(run.run_id)}
            className={`text-left px-3 py-2 text-sm font-mono border transition-colors ${
              runId === run.run_id
                ? 'bg-ink text-base border-ink'
                : 'bg-transparent text-ink border-line hover:bg-inset'
            }`}
          >
            {run.run_id}
            <div className="text-11 opacity-70 mt-1">{new Date(run.init_time).toLocaleString()}</div>
          </button>
        ))}
      </div>
    </div>
  );
};
