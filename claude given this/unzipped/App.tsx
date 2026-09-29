import { ThreeColumnLayout } from './components/layout';
import { RiskMap } from './components/map/RiskMap';
import { SectionLabel } from './components/ui';

export default function App() {
  return (
    <ThreeColumnLayout
      left={<SectionLabel>Controls (Phase 4)</SectionLabel>}
      center={<RiskMap />}
      right={
        <p className="max-w-[40ch] leading-5 text-ink-dim">
          Select a cell on the map to see why BustNet expects this forecast to fail or hold.
        </p>
      }
    />
  );
}
