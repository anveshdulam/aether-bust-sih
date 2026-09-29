import React from 'react';

export const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="text-11 tracking-wide uppercase text-ink-dim font-sans border-b border-line pb-2 mb-4">
    {children}
  </div>
);
