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
    bg: '#22C55E', // Terminal green
    glow: 'rgba(34, 197, 94, 0.4)',
  },
  processing: {
    bg: '#8B5CF6', // Deep purple
    glow: 'rgba(139, 92, 246, 0.4)',
  },
  warning: {
    bg: '#EF4444', // Red
    glow: 'rgba(239, 68, 68, 0.4)',
  },
  waiting: {
    bg: '#6366F1', // Indigo
    glow: 'rgba(99, 102, 241, 0.4)',
  },
  idle: {
    bg: '#64748B', // Muted slate
    glow: 'transparent',
  },
  off: {
    bg: '#475569', // Darker slate
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
