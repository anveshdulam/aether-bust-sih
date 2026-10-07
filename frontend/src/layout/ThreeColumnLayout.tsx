import React from 'react';
import { TopBar } from './TopBar';
import { BottomStrip } from './BottomStrip';

interface ThreeColumnLayoutProps {
  colA: React.ReactNode;
  colB: React.ReactNode;
  colC: React.ReactNode;
}

export const ThreeColumnLayout: React.FC<ThreeColumnLayoutProps> = ({ colA, colB, colC }) => {
  return (
    <div className="flex flex-col h-screen w-screen bg-bg-canvas overflow-hidden">
      <TopBar />
      
      <div className="flex flex-1 overflow-hidden relative">
        {/* COL A (Fixed 320px) */}
        <div className="w-[320px] flex-shrink-0 border-r border-border bg-bg-panel overflow-y-auto flex flex-col z-10">
          {colA}
        </div>
        
        {/* COL B (Fluid) */}
        <div className="flex-1 min-w-0 relative bg-bg-canvas overflow-hidden flex flex-col z-0">
          {colB}
        </div>
        
        {/* COL C (Fixed 380px) */}
        <div className="w-[380px] flex-shrink-0 border-l border-border bg-bg-panel overflow-y-auto flex flex-col z-10">
          {colC}
        </div>
      </div>
      
      <BottomStrip />
    </div>
  );
};
