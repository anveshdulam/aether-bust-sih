import React from 'react';
import { useConsoleStore } from '../../store/useConsoleStore';
import { SegmentedControl } from '../common/SegmentedControl';
import { VarCode } from '../../api/types';

export const VariableSelector: React.FC = () => {
  const { variable, setVariable } = useConsoleStore();
  
  return (
    <div className="p-4 border-b border-border-subtle">
      <div className="text-sm font-semibold text-text-primary mb-3">Target Variable</div>
      <SegmentedControl<VarCode>
        options={[
          { label: 't2m', value: 't2m', sublabel: 'K' },
          { label: 'tp', value: 'tp', sublabel: 'mm' },
          { label: 'z500', value: 'z500', sublabel: 'gpm' },
          { label: 'ws850', value: 'ws850', sublabel: 'm/s' }
        ]}
        value={variable}
        onChange={setVariable}
      />
    </div>
  );
};
