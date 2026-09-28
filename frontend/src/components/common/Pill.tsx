import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface PillProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  color?: string; // hex
}

export const Pill: React.FC<PillProps> = ({ children, color, className, ...props }) => {
  return (
    <div 
      className={cn("px-2 py-0.5 rounded-sm text-xs font-semibold flex items-center gap-1.5 border border-white/10", className)}
      style={{ backgroundColor: color ? `${color}40` : undefined, color: color || 'inherit' }}
      {...props}
    >
      {children}
    </div>
  );
};
