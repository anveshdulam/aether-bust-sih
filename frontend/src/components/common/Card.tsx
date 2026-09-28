import React from 'react';
import { cn } from './Pill';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Card: React.FC<CardProps> = ({ className, children, ...props }) => {
  return (
    <div className={cn("bg-bg-elevated rounded-xl shadow-panel p-4 border border-border-subtle", className)} {...props}>
      {children}
    </div>
  );
};
