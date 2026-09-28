import { ThreeColumnLayout } from './layout/ThreeColumnLayout';
import { VariableSelector } from './components/controls/VariableSelector';
import { LayerToggleGroup } from './components/controls/LayerToggleGroup';
import { OpacitySlider } from './components/controls/OpacitySlider';
import { ConfidenceBandFilter } from './components/controls/ConfidenceBandFilter';
import { BaselineCompare } from './components/controls/BaselineCompare';
import { RiskMap } from './components/map/RiskMap';
import { RegionTelemetry } from './components/telemetry/RegionTelemetry';
import { XaiPanel } from './components/xai/XaiPanel';

function App() {
  const colA = (
    <div className="flex flex-col">
      <VariableSelector />
      <LayerToggleGroup />
      <OpacitySlider />
      <ConfidenceBandFilter />
      <BaselineCompare />
    </div>
  );

  const colB = (
    <RiskMap />
  );

  const colC = (
    <div className="flex flex-col">
      <RegionTelemetry />
      <XaiPanel />
    </div>
  );

  return (
    <ThreeColumnLayout
      colA={colA}
      colB={colB}
      colC={colC}
    />
  );
}

export default App;
