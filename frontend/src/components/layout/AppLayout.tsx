import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MessageSquare } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface AppLayoutProps {
  title?: string;
}

export function AppLayout({ title }: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isOnCOOPage = location.pathname === '/coo';

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>

      {/* Quick access to COO Channel when not on that page */}
      {!isOnCOOPage && (
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          onClick={() => navigate('/coo')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-[var(--color-neural)] shadow-lg shadow-[var(--color-neural)]/30 flex items-center justify-center z-50 hover:shadow-[var(--color-neural)]/50 transition-shadow"
          title="Open COO Channel"
        >
          <MessageSquare className="w-6 h-6 text-white" />
          <span className="absolute top-0 right-0 w-3 h-3 bg-[var(--color-ok)] rounded-full border-2 border-[var(--color-void)]" />
        </motion.button>
      )}
    </div>
  );
}
