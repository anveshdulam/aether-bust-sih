import React from 'react';
import { cn } from './Pill';

interface StatusDotProps {
  status: 'ok' | 'warn' | 'crit' | 'info';
  className?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({ status, className }) => {
  const bgClass = {
    'ok': 'bg-status-ok',
    'warn': 'bg-status-warn',
    'crit': 'bg-status-crit',
    'info': 'bg-status-info'
  }[status];

  return (
    <div className={cn("w-2.5 h-2.5 rounded-sm", bgClass, className)} />
  );
};
