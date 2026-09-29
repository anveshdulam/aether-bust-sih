import { ThreeColumnLayout } from './components/layout';
import { RiskMap } from './components/map/RiskMap';
import { SectionLabel } from './components/ui';
import { LeftPanel } from './components/controls';
import { AttributionPanel } from './components/xai';

export default function App() {
  return (
    <ThreeColumnLayout
      left={
        <>
          <SectionLabel>Controls</SectionLabel>
          <LeftPanel />
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
