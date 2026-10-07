import { VariableToggle } from './VariableToggle';
import { LayerToggle } from './LayerToggle';
import { TopRiskRegions } from './TopRiskRegions';

export const LeftPanel = () => {
  return (
    <div className="flex flex-col h-full gap-6 p-4">
      <VariableToggle />
      <TopRiskRegions />
      <div className="flex-1" />
      <LayerToggle />
    </div>
  );
};
