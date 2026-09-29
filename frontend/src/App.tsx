import { ThreeColumnLayout } from './components/layout';
import { RiskMap } from './components/map/RiskMap';
import { SectionLabel } from './components/ui';
import { LeftPanel, ExportPanel } from './components/controls';
import { AttributionPanel } from './components/xai';

export default function App() {
  return (
    <ThreeColumnLayout
      left={
        <>
          <SectionLabel>Controls</SectionLabel>
          <LeftPanel />
          <ExportPanel />
        </>
      }
      center={<RiskMap />}
      right={
        <>
          <SectionLabel>Attribution</SectionLabel>
          <AttributionPanel />
        </>
      }
    />
  );
}
