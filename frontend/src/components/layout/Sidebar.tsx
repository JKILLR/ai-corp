import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  MessageSquarePlus,
  ShieldCheck,
  Plug,
  Settings,
} from 'lucide-react';

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Projects', path: '/projects', icon: FolderKanban },
  { label: 'Agents', path: '/agents', icon: Users },
  { label: 'Discovery', path: '/discovery', icon: MessageSquarePlus },
  { label: 'Gates', path: '/gates', icon: ShieldCheck },
  { label: 'Integrations', path: '/integrations', icon: Plug },
];

const bottomNavItems: NavItem[] = [
  { label: 'Settings', path: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-56 h-screen bg-[var(--color-cosmos)] border-r border-[var(--glass-border)] flex flex-col">
      {/* Logo */}
      <div className="h-16 px-4 flex items-center border-b border-[var(--glass-border)]">
        <span className="text-[var(--color-neural)] text-xl font-semibold tracking-tight">
          AI CORP
        </span>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavItem key={item.path} {...item} />
        ))}
      </nav>

      {/* Bottom Navigation */}
      <div className="py-4 px-2 border-t border-[var(--glass-border)]">
        {bottomNavItems.map((item) => (
          <NavItem key={item.path} {...item} />
        ))}
      </div>
    </aside>
  );
}

function NavItem({ label, path, icon: Icon, badge }: NavItem) {
  return (
    <NavLink
      to={path}
      className={({ isActive }) => `
        flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-sm)]
        text-sm font-medium transition-colors
        ${
          isActive
            ? 'bg-[var(--glass-bg-active)] text-[var(--color-plasma)]'
            : 'text-[var(--color-muted)] hover:bg-[var(--glass-bg)] hover:text-[var(--color-plasma)]'
        }
      `}
    >
      {({ isActive }) => (
        <>
          <Icon className="w-5 h-5" />
          <span className="flex-1">{label}</span>
          {badge !== undefined && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className={`
                min-w-5 h-5 px-1.5 flex items-center justify-center
                text-xs font-medium rounded-full
                ${
                  isActive
                    ? 'bg-[var(--color-neural)] text-white'
                    : 'bg-[var(--color-warn)] text-white'
                }
              `}
            >
              {badge}
            </motion.span>
          )}
        </>
      )}
    </NavLink>
  );
}
