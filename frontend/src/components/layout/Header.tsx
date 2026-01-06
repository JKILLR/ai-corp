import { motion } from 'framer-motion';
import { Bell, Search, User } from 'lucide-react';

interface HeaderProps {
  title?: string;
}

export function Header({ title = 'Neural Command Center' }: HeaderProps) {
  return (
    <header className="h-16 px-6 flex items-center justify-between border-b border-[var(--glass-border)] bg-[var(--color-cosmos)]">
      {/* Left: Page Title */}
      <h1 className="text-xl font-semibold text-[var(--color-plasma)]">
        {title}
      </h1>

      {/* Right: Search + Actions */}
      <div className="flex items-center gap-4">
        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted)]" />
          <input
            type="text"
            placeholder="Search or press Cmd+K"
            className="w-64 pl-10 pr-4 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none focus:border-[var(--color-neural)] transition-colors"
          />
        </div>

        {/* Notifications */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative p-2 rounded-[var(--radius-sm)] text-[var(--color-muted)] hover:text-[var(--color-plasma)] hover:bg-[var(--glass-bg)] transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[var(--color-warn)] rounded-full" />
        </motion.button>

        {/* User menu */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-sm)] hover:bg-[var(--glass-bg)] transition-colors"
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
