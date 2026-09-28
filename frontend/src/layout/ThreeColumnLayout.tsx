import React from 'react';
import { TopBar } from './TopBar';
import { BottomStrip } from './BottomStrip';
import { AlertsTicker } from '../components/alerts/AlertsTicker';

interface ThreeColumnLayoutProps {
  colA: React.ReactNode;
  colB: React.ReactNode;
  colC: React.ReactNode;
}

export const ThreeColumnLayout: React.FC<ThreeColumnLayoutProps> = ({ colA, colB, colC }) => {
  return (
    <div className="flex flex-col h-screen w-screen bg-bg-base overflow-hidden">
      <TopBar />
      <AlertsTicker />
      
      <div className="flex flex-1 overflow-hidden relative">
        {/* COL A (Fixed 320px) */}
        <div className="w-[320px] shrink-0 border-r border-border-subtle bg-bg-base overflow-y-auto hidden xl:block z-10">
          {colA}
        </div>
        
        {/* COL B (Fluid) */}
        <div className="flex-1 relative bg-bg-inset overflow-hidden flex flex-col z-0">
          {colB}
        </div>
        
        {/* COL C (Fixed 380px) */}
        <div className="w-[380px] shrink-0 border-l border-border-subtle bg-bg-base overflow-y-auto hidden lg:block z-10">
          {colC}
        </div>
      </div>
      
      <BottomStrip />
    </div>
  );
};
