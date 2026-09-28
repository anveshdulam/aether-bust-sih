import React from 'react';
import { Card } from '../common/Card';

interface NarrativeCardProps {
  narrative: string;
}

export const NarrativeCard: React.FC<NarrativeCardProps> = ({ narrative }) => {
  // Highlight top variables if they exist in the text (e.g. bolding them)
  return (
    <Card className="bg-bg-inset border-l-2 border-l-accent-primary p-3">
      <div className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">AI Synopsis</div>
      <p className="text-sm text-text-primary leading-relaxed">
        {narrative}
      </p>
    </Card>
  );
};
