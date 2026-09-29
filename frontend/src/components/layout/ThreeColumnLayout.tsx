import React from 'react';

interface ThreeColumnLayoutProps {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
}

export const ThreeColumnLayout: React.FC<ThreeColumnLayoutProps> = ({ left, center, right }) => {
  return (
    <div className="flex h-screen w-screen bg-base text-ink overflow-hidden font-sans antialiased selection:bg-accent selection:text-white">
      {/* Left Column: Controls */}
      <div className="w-80 flex-shrink-0 bg-panel border-r border-line flex flex-col">
        <div className="p-4 flex-1 overflow-y-auto">
          {left}
        </div>
      </div>
      
      {/* Center Column: RiskMap */}
      <div className="flex-1 min-w-0 bg-inset relative">
        {center}
      </div>
      
      {/* Right Column: XAI / Documents */}
      <div className="w-96 flex-shrink-0 bg-panel border-l border-line flex flex-col">
        <div className="p-4 flex-1 overflow-y-auto">
          {right}
        </div>
      </div>
    </div>
  );
};
