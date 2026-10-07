import { ThreeColumnLayout } from './layout/ThreeColumnLayout';
import { RiskMap } from './components/map/RiskMap';
import { SectionLabel } from './components/ui';
import { LeftPanel, ExportPanel } from './components/controls';
import { AttributionPanel } from './components/xai';
import { RegionTelemetry } from './components/telemetry/RegionTelemetry';
import { ChatWidget } from './components/chat/ChatWidget';
import { useAppStore } from './store/useAppStore';
import { useRuns } from './api/queries';
import { RefreshCw, Database } from 'lucide-react';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

export default function App() {
  useKeyboardShortcuts();
  
  const runId = useAppStore(s => s.runId);
  const { data: runs, isLoading, isError, refetch } = useRuns();

  const renderColB = () => {
    if (isLoading) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center text-text-muted h-full">
          <RefreshCw className="animate-spin mb-4" size={32} />
          <p>Loading runs from database...</p>
        </div>
      );
    }
    if (isError) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center text-status-red h-full gap-4">
          <Database size={48} />
          <p>Failed to connect to the backend database.</p>
          <button onClick={() => refetch()} className="px-4 py-2 bg-bg-raised hover:bg-bg-panel border border-border rounded text-text-primary">
            Retry Connection
          </button>
        </div>
      );
    }
    if (!runId || runs?.length === 0) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center text-text-muted h-full">
          <Database size={48} className="mb-4 opacity-50" />
          <p>No model evaluation runs found.</p>
          <p className="text-xs mt-2 opacity-75">Generate synthetic data or run an evaluation script to populate.</p>
        </div>
      );
    }
    return <RiskMap />;
  };

  return (
    <>
      <ThreeColumnLayout
        colA={
          <>
            <SectionLabel>Controls</SectionLabel>
            <LeftPanel />
            <ExportPanel />
          </>
        }
        colB={renderColB()}
        colC={
          <div id="xai-panel" className="flex flex-col h-full overflow-y-auto">
            <SectionLabel>Telemetry</SectionLabel>
            <RegionTelemetry />
            <SectionLabel>Explainability (XAI)</SectionLabel>
            <AttributionPanel />
          </div>
        }
      />
      <ChatWidget />
    </>
  );
}
