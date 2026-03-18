import { motion, type HTMLMotionProps } from 'framer-motion';
import { forwardRef } from 'react';

export interface ButtonProps extends HTMLMotionProps<'button'> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

const variantClasses = {
  primary: `
    bg-[var(--color-neural)] text-white
    hover:brightness-110
  `,
  secondary: `
    bg-[var(--glass-bg)] text-[var(--color-plasma)]
    border border-[var(--glass-border)]
    hover:bg-[var(--glass-bg-hover)]
  `,
  ghost: `
    bg-transparent text-[var(--color-plasma)]
    hover:bg-[var(--glass-bg)]
  `,
};

const springConfig = {
  type: 'spring' as const,
  stiffness: 400,
  damping: 30,
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      className = '',
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <motion.button
        ref={ref}
        className={`
          inline-flex items-center justify-center gap-2
          font-medium rounded-[var(--radius-sm)]
          transition-colors cursor-pointer
          disabled:opacity-50 disabled:cursor-not-allowed
          ${sizeClasses[size]}
          ${variantClasses[variant]}
          ${className}
        `}
        whileHover={disabled ? undefined : { scale: 1.02 }}
        whileTap={disabled ? undefined : { scale: 0.98 }}
        transition={springConfig}
        disabled={disabled}
        {...props}
      >
        {children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
