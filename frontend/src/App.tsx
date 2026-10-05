import { ThreeColumnLayout } from './layout/ThreeColumnLayout';
import { RiskMap } from './components/map/RiskMap';
import { SectionLabel } from './components/ui';
import { LeftPanel, ExportPanel } from './components/controls';
import { AttributionPanel } from './components/xai';
import { RegionTelemetry } from './components/telemetry/RegionTelemetry';
import { ChatWidget } from './components/chat/ChatWidget';

export default function App() {
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
        colB={<RiskMap />}
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
