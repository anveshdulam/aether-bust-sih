import { RunSelector } from './RunSelector';
import { VariableToggle } from './VariableToggle';
import { LeadTimeSlider } from './LeadTimeSlider';
import { LayerToggle } from './LayerToggle';

export const LeftPanel = () => {
  return (
    <div className="flex flex-col h-full">
      <RunSelector />
      <VariableToggle />
      <LeadTimeSlider />
      <div className="flex-1" />
      <LayerToggle />
    </div>
  );
};
