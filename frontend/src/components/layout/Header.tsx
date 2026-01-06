import { motion } from 'framer-motion';
import { Bell, Search, User } from 'lucide-react';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  return (
    <header className="h-16 px-6 flex items-center justify-between border-b border-[var(--glass-border)] bg-[var(--color-cosmos)]">
      {/* Left: Page Title */}
      <div className="flex flex-col">
        {title && (
          <h1 className="text-lg font-semibold text-[var(--color-plasma)]">
            {title}
          </h1>
        )}
        {subtitle && (
          <p className="text-sm text-[var(--color-muted)]">{subtitle}</p>
        )}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="p-2 rounded-[var(--radius-sm)] text-[var(--color-muted)] hover:text-[var(--color-plasma)] hover:bg-[var(--glass-bg)] transition-colors"
          aria-label="Search"
        >
          <Search className="w-5 h-5" />
        </motion.button>

        {/* Notifications */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative p-2 rounded-[var(--radius-sm)] text-[var(--color-muted)] hover:text-[var(--color-plasma)] hover:bg-[var(--glass-bg)] transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          {/* Notification dot */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[var(--color-warn)] rounded-full" />
        </motion.button>

        {/* User menu */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="ml-2 flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-sm)] hover:bg-[var(--glass-bg)] transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-[var(--color-neural)] flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-medium text-[var(--color-plasma)]">
            Admin
          </span>
        </motion.button>
      </div>
    </header>
  );
}
