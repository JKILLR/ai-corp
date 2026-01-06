import { motion, type HTMLMotionProps } from 'framer-motion';
import { forwardRef } from 'react';

export interface GlassCardProps extends HTMLMotionProps<'div'> {
  variant?: 'default' | 'elevated' | 'interactive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

const springConfig = {
  type: 'spring' as const,
  stiffness: 300,
  damping: 25,
};

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ variant = 'default', padding = 'md', className = '', children, ...props }, ref) => {
    const baseClasses = `
      rounded-[var(--radius-md)]
      border border-[var(--glass-border)]
      backdrop-blur-[var(--glass-blur)]
      ${paddingClasses[padding]}
    `;

    const variantClasses = {
      default: 'bg-[var(--glass-bg)]',
      elevated: 'bg-[var(--glass-bg)] shadow-[var(--shadow-card)]',
      interactive: 'bg-[var(--glass-bg)] cursor-pointer',
    };

    if (variant === 'interactive') {
      return (
        <motion.div
          ref={ref}
          className={`${baseClasses} ${variantClasses[variant]} ${className}`}
          whileHover={{
            backgroundColor: 'var(--glass-bg-hover)',
            y: -2,
          }}
          whileTap={{
            scale: 0.99,
          }}
          transition={springConfig}
          {...props}
        >
          {children}
        </motion.div>
      );
    }

    return (
      <motion.div
        ref={ref}
        className={`${baseClasses} ${variantClasses[variant]} ${className}`}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

GlassCard.displayName = 'GlassCard';
