import type { Status } from './StatusOrb';

export interface BadgeProps {
  status: Status;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const statusLabels: Record<Status, string> = {
  ok: 'OK',
  processing: 'PROC',
  warning: 'WARN',
  waiting: 'WAIT',
  idle: 'IDLE',
  off: 'OFF',
};

const statusTextColors: Record<Status, string> = {
  ok: 'text-[var(--color-ok)]',
  processing: 'text-[var(--color-proc)]',
  warning: 'text-[var(--color-warn)]',
  waiting: 'text-[var(--color-wait)]',
  idle: 'text-[var(--color-idle)]',
  off: 'text-[var(--color-off)]',
};

const sizeClasses = {
  sm: 'text-[10px]',
  md: 'text-xs',
  lg: 'text-sm',
};

export function Badge({ status, size = 'md', className = '' }: BadgeProps) {
  return (
    <span
      className={`
        font-mono font-medium tracking-wider uppercase
        ${sizeClasses[size]}
        ${statusTextColors[status]}
        ${className}
      `}
    >
      [{statusLabels[status]}]
    </span>
  );
}
