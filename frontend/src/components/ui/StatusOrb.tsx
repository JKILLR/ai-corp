import { motion } from 'framer-motion';

export type Status = 'ok' | 'processing' | 'warning' | 'waiting' | 'idle' | 'off';

export interface StatusOrbProps {
  status: Status;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
};

const statusColors: Record<Status, { bg: string; glow: string }> = {
  ok: {
    bg: 'var(--color-ok)',
    glow: 'var(--color-ok-glow)',
  },
  processing: {
    bg: 'var(--color-proc)',
    glow: 'var(--color-proc-glow)',
  },
  warning: {
    bg: 'var(--color-warn)',
    glow: 'var(--color-warn-glow)',
  },
  waiting: {
    bg: 'var(--color-wait)',
    glow: 'var(--color-wait-glow)',
  },
  idle: {
    bg: 'var(--color-idle)',
    glow: 'transparent',
  },
  off: {
    bg: 'var(--color-off)',
    glow: 'transparent',
  },
};

export function StatusOrb({
  status,
  size = 'md',
  pulse = true,
  className = '',
}: StatusOrbProps) {
  const colors = statusColors[status];
  const shouldPulse = pulse && (status === 'ok' || status === 'processing');

  return (
    <span
      className={`relative inline-flex items-center justify-center ${className}`}
    >
      {/* Glow layer */}
      {shouldPulse && (
        <motion.span
          className={`absolute ${sizeClasses[size]} rounded-full`}
          style={{ backgroundColor: colors.glow }}
          animate={{
            scale: [1, 1.8, 1],
            opacity: [0.6, 0, 0.6],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}

      {/* Core orb */}
      <motion.span
        className={`${sizeClasses[size]} rounded-full`}
        style={{ backgroundColor: colors.bg }}
        animate={
          status === 'processing'
            ? { scale: [1, 1.1, 1] }
            : undefined
        }
        transition={
          status === 'processing'
            ? { duration: 1, repeat: Infinity, ease: 'easeInOut' }
            : undefined
        }
      />
    </span>
  );
}
