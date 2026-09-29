import React from 'react';
import { cn } from './Pill';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Card: React.FC<CardProps> = ({ className, children, ...props }) => {
  return (
    <div className={cn("bg-panel rounded p-4 border border-line", className)} {...props}>
      {children}
    </div>
  );
};
