import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity, X, Minimize2, Maximize2, Wifi, WifiOff, AlertCircle,
  CheckCircle, Trash2, ExternalLink, MessageSquare, Filter
} from 'lucide-react';
import { GlassCard } from './ui';
import { StatusOrb } from './ui/StatusOrb';

// =============================================================================
// TYPES
// =============================================================================

interface ActivityEvent {
  event_id: string;
  timestamp: string;
  display: {
    message: string;
    icon: string;
    severity: 'info' | 'success' | 'warning' | 'error';
    phase: string;
  };
  raw_type: string;
  molecule_id?: string;
  step_id?: string;
  gate_id?: string;
  aggregated_count?: number;
  aggregated_events?: string[];
}

type PanelState = 'hidden' | 'open' | 'minimized';
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
type WorkflowStatus = 'idle' | 'working' | 'completed' | 'error';

interface ActivityPanelProps {
  /** Initial state of the panel */
  initialState?: PanelState;
  /** Whether to auto-open on new events */
  autoOpen?: boolean;
  /** WebSocket URL override (defaults to /api/ws/activity) */
  wsUrl?: string;
  /** Callback when molecule completes - use to trigger COO summary */
  onMoleculeComplete?: (moleculeId: string, moleculeName?: string) => void;
  /** Callback when error occurs - use to notify user */
  onError?: (error: ActivityEvent) => void;
  /** Session molecule IDs to highlight (from current chat session) */
  sessionMoleculeIds?: string[];
}

// =============================================================================
// CONSTANTS
// =============================================================================

const PANEL_WIDTH = 340;
const PANEL_WIDTH_MOBILE = '100vw';
const MAX_EVENTS = 100;
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000];
const AUTO_MINIMIZE_DELAY = 10000; // 10 seconds
const HISTORY_STORAGE_KEY = 'ai-corp-activity-history';
const SESSION_STORAGE_KEY = 'ai-corp-activity-session';

// Severity to status mapping for StatusOrb
const severityToStatus: Record<string, 'ok' | 'processing' | 'warning' | 'waiting' | 'idle'> = {
  success: 'ok',
  info: 'processing',
  warning: 'warning',
  error: 'warning',
};

// Connection status config
const CONNECTION_STATUS_CONFIG: Record<ConnectionStatus, { text: string; color: string }> = {
  connecting: { text: 'Connecting...', color: 'text-[var(--color-wait)]' },
  connected: { text: 'Live', color: 'text-[var(--color-ok)]' },
  disconnected: { text: 'Disconnected', color: 'text-[var(--color-muted)]' },
  error: { text: 'Error', color: 'text-[var(--color-warn)]' },
};

// Workflow status config
const WORKFLOW_STATUS_CONFIG: Record<WorkflowStatus, { text: string; color: string; bgColor: string }> = {
  idle: { text: 'Idle', color: 'text-[var(--color-muted)]', bgColor: 'bg-transparent' },
  working: { text: 'Working...', color: 'text-[var(--color-neural)]', bgColor: 'bg-[rgba(139,92,246,0.1)]' },
  completed: { text: 'Complete', color: 'text-[var(--color-ok)]', bgColor: 'bg-[rgba(34,197,94,0.1)]' },
  error: { text: 'Error', color: 'text-[var(--color-warn)]', bgColor: 'bg-[rgba(239,68,68,0.1)]' },
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);

  if (diffSec < 5) return 'just now';
  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  return date.toLocaleDateString();
}

function getWsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/api/ws/activity`;
}

function getSessionId(): string {
  let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

function loadHistoryFromStorage(): ActivityEvent[] {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as ActivityEvent[];
      // Filter to last hour
      const oneHourAgo = Date.now() - 60 * 60 * 1000;
      return parsed.filter(e => new Date(e.timestamp).getTime() > oneHourAgo);
    }
  } catch (e) {
    console.warn('Failed to load activity history:', e);
  }
  return [];
}

function saveHistoryToStorage(events: ActivityEvent[]): void {
  try {
    // Keep last 100 events, last hour only
    const oneHourAgo = Date.now() - 60 * 60 * 1000;
    const filtered = events
      .filter(e => new Date(e.timestamp).getTime() > oneHourAgo)
      .slice(-MAX_EVENTS);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(filtered));
  } catch (e) {
    console.warn('Failed to save activity history:', e);
  }
}

// =============================================================================
// CUSTOM HOOK: useMediaQuery
// =============================================================================

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(query).matches : false
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
}

// =============================================================================
// ACTIVITY PANEL COMPONENT
// =============================================================================

export function ActivityPanel({
  initialState = 'hidden',
  autoOpen = true,
  wsUrl,
  onMoleculeComplete,
  onError,
  sessionMoleculeIds = [],
}: ActivityPanelProps) {
  // Responsive
  const isMobile = useMediaQuery('(max-width: 640px)');
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');

  // State
  const [panelState, setPanelState] = useState<PanelState>(initialState);
  const [events, setEvents] = useState<ActivityEvent[]>(() => loadHistoryFromStorage());
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [unreadCount, setUnreadCount] = useState(0);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus>('idle');
  const [hasUnacknowledgedError, setHasUnacknowledgedError] = useState(false);
  const [filterToSession, setFilterToSession] = useState(false);
  const [expandedErrorId, setExpandedErrorId] = useState<string | null>(null);

  // Session tracking - track molecules started this session
  const [sessionMolecules, setSessionMolecules] = useState<Set<string>>(
    () => new Set(sessionMoleculeIds)
  );

  // Initialize session ID on mount (side effect, so use useEffect)
  useEffect(() => {
    getSessionId();
  }, []);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);
  const hasReceivedFirstEvent = useRef(events.length > 0);
  const panelStateRef = useRef(panelState);
  const autoMinimizeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasUnacknowledgedErrorRef = useRef(hasUnacknowledgedError);

  // Keep refs in sync (avoids stale closures in callbacks)
  panelStateRef.current = panelState;
  hasUnacknowledgedErrorRef.current = hasUnacknowledgedError;

  // Filtered events for display
  const displayEvents = useMemo(() => {
    if (!filterToSession || sessionMolecules.size === 0) {
      return events;
    }
    return events.filter(e => e.molecule_id && sessionMolecules.has(e.molecule_id));
  }, [events, filterToSession, sessionMolecules]);

  // Completed molecules count
  const completedCount = useMemo(() => {
    return events.filter(e => e.raw_type === 'molecule.completed').length;
  }, [events]);

  // Error count
  const errorCount = useMemo(() => {
    return events.filter(e => e.display.severity === 'error').length;
  }, [events]);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    if (!prefersReducedMotion) {
      eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    } else {
      eventsEndRef.current?.scrollIntoView();
    }
  }, [prefersReducedMotion]);

  // Reset auto-minimize timer
  const resetAutoMinimizeTimer = useCallback(() => {
    if (autoMinimizeTimeoutRef.current) {
      clearTimeout(autoMinimizeTimeoutRef.current);
      autoMinimizeTimeoutRef.current = null;
    }
  }, []);

  // Start auto-minimize timer
  const startAutoMinimizeTimer = useCallback(() => {
    // Don't auto-minimize if there are unacknowledged errors (use ref for current value)
    if (hasUnacknowledgedErrorRef.current) return;

    resetAutoMinimizeTimer();
    autoMinimizeTimeoutRef.current = setTimeout(() => {
      // Check ref again inside timeout to get current value
      if (panelStateRef.current === 'open' && !hasUnacknowledgedErrorRef.current) {
        setPanelState('minimized');
      }
    }, AUTO_MINIMIZE_DELAY);
  }, [resetAutoMinimizeTimer]);

  // Handle a single activity event
  const handleActivityEvent = useCallback((event: ActivityEvent) => {
    setEvents((prev) => {
      const newEvents = [...prev, event];
      const limited = newEvents.slice(-MAX_EVENTS);
      // Save to localStorage asynchronously
      setTimeout(() => saveHistoryToStorage(limited), 0);
      return limited;
    });

    // Track session molecules
    if (event.molecule_id) {
      if (event.raw_type === 'molecule.created' || event.raw_type === 'molecule.started') {
        setSessionMolecules(prev => new Set(prev).add(event.molecule_id!));
      }
    }

    // Update workflow status
    if (event.raw_type === 'molecule.created' || event.raw_type === 'molecule.started') {
      setWorkflowStatus('working');
      resetAutoMinimizeTimer();
    } else if (event.raw_type === 'molecule.completed') {
      setWorkflowStatus('completed');
      // Trigger completion callback
      if (onMoleculeComplete && event.molecule_id) {
        onMoleculeComplete(event.molecule_id, event.display.message);
      }
      // Start auto-minimize timer after completion
      startAutoMinimizeTimer();
    } else if (event.display.severity === 'error') {
      setWorkflowStatus('error');
      setHasUnacknowledgedError(true);
      // Trigger error callback
      if (onError) {
        onError(event);
      }
    } else {
      // Reset timer on any activity
      resetAutoMinimizeTimer();
    }

    // Auto-open logic
    if (autoOpen) {
      if (!hasReceivedFirstEvent.current) {
        hasReceivedFirstEvent.current = true;
        setPanelState('open');
      } else if (event.display.severity === 'error') {
        setPanelState('open');
      } else if (event.raw_type === 'molecule.created' || event.raw_type === 'molecule.started') {
        setPanelState('open');
      }
    }

    // Track unread
    if (panelStateRef.current !== 'open') {
      setUnreadCount((prev) => prev + 1);
    }
  }, [autoOpen, onMoleculeComplete, onError, resetAutoMinimizeTimer, startAutoMinimizeTimer]);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((rawData: unknown) => {
    if (!rawData || typeof rawData !== 'object') return;

    const data = rawData as Record<string, unknown>;

    if (data.type === 'history' && Array.isArray(data.events)) {
      const historyEvents = data.events as ActivityEvent[];
      if (historyEvents.length > 0) {
        setEvents(prev => {
          // Merge with existing, dedupe by event_id, sort by timestamp
          const existing = new Set(prev.map(e => e.event_id));
          const newEvents = historyEvents.filter(e => !existing.has(e.event_id));
          const merged = [...prev, ...newEvents]
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
            .slice(-MAX_EVENTS);
          setTimeout(() => saveHistoryToStorage(merged), 0);
          return merged;
        });
        hasReceivedFirstEvent.current = true;
      }
      return;
    }

    if (data.type === 'pong' || data.type === 'stats') {
      return;
    }

    if (data.event_id && data.display) {
      handleActivityEvent(data as unknown as ActivityEvent);
    }
  }, [handleActivityEvent]);

  // WebSocket connection
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const url = wsUrl || getWsUrl();
    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('connected');
        reconnectAttemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleMessage(data);
        } catch (err) {
          console.error('Failed to parse activity event:', err);
        }
      };

      ws.onerror = () => setConnectionStatus('error');

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        wsRef.current = null;

        const attempt = reconnectAttemptRef.current;
        const delay = RECONNECT_DELAYS[Math.min(attempt, RECONNECT_DELAYS.length - 1)];
        reconnectAttemptRef.current = attempt + 1;

        reconnectTimeoutRef.current = setTimeout(() => connect(), delay);
      };
    } catch {
      setConnectionStatus('error');
    }
  }, [wsUrl, handleMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (autoMinimizeTimeoutRef.current) {
      clearTimeout(autoMinimizeTimeoutRef.current);
      autoMinimizeTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Scroll on events change
  useEffect(() => {
    if (panelState === 'open') {
      scrollToBottom();
    }
  }, [events, panelState, scrollToBottom]);

  // Clear unread when panel opens
  useEffect(() => {
    if (panelState === 'open') {
      setUnreadCount(0);
    }
  }, [panelState]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && panelState !== 'hidden') {
        setPanelState('hidden');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [panelState]);

  // Panel controls
  const openPanel = () => setPanelState('open');
  const closePanel = () => setPanelState('hidden');
  const toggleMinimize = () => setPanelState(panelState === 'minimized' ? 'open' : 'minimized');

  const clearHistory = () => {
    setEvents([]);
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    setHasUnacknowledgedError(false);
    setWorkflowStatus('idle');
  };

  const acknowledgeErrors = () => {
    setHasUnacknowledgedError(false);
    setExpandedErrorId(null);
  };

  // Render connection status
  const renderConnectionStatus = () => {
    const config = CONNECTION_STATUS_CONFIG[connectionStatus];
    const icon = connectionStatus === 'connecting' ? (
      <Wifi className="w-3 h-3 animate-pulse" />
    ) : connectionStatus === 'connected' ? (
      <Wifi className="w-3 h-3" />
    ) : connectionStatus === 'error' ? (
      <AlertCircle className="w-3 h-3" />
    ) : (
      <WifiOff className="w-3 h-3" />
    );

    return (
      <span className={`flex items-center gap-1 text-xs ${config.color}`}>
        {icon}
        {config.text}
      </span>
    );
  };

  // Render workflow status badge
  const renderWorkflowStatus = () => {
    const config = WORKFLOW_STATUS_CONFIG[workflowStatus];
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.color} ${config.bgColor}`}>
        {config.text}
        {workflowStatus === 'completed' && completedCount > 0 && ` (${completedCount})`}
        {workflowStatus === 'error' && errorCount > 0 && ` (${errorCount})`}
      </span>
    );
  };

  // Animation variants respecting reduced motion
  const panelVariants = prefersReducedMotion ? {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  } : {
    initial: { x: PANEL_WIDTH + 24, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: PANEL_WIDTH + 24, opacity: 0 },
  };

  const buttonVariants = prefersReducedMotion ? {} : {
    initial: { scale: 0, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 0, opacity: 0 },
  };

  return (
    <>
      {/* Trigger button when panel is hidden */}
      <AnimatePresence>
        {panelState === 'hidden' && (
          <motion.button
            {...buttonVariants}
            onClick={openPanel}
            whileHover={prefersReducedMotion ? {} : { scale: 1.05 }}
            whileTap={prefersReducedMotion ? {} : { scale: 0.95 }}
            className="fixed bottom-24 right-6 w-12 h-12 rounded-full bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-[var(--glass-blur)] shadow-lg flex items-center justify-center z-[var(--z-modal)] hover:bg-[var(--glass-bg-hover)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-neural)]"
            title="Open Activity Feed (Escape to close)"
            aria-label={`Open Activity Feed. ${unreadCount} unread events.`}
          >
            <Activity className="w-5 h-5 text-[var(--color-neural)]" />
            {unreadCount > 0 && (
              <span
                className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-[var(--color-neural)] rounded-full flex items-center justify-center text-[10px] text-white font-bold"
                aria-hidden="true"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
            {/* Completed badge */}
            {completedCount > 0 && workflowStatus === 'completed' && (
              <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-[var(--color-ok)] rounded-full flex items-center justify-center">
                <CheckCircle className="w-3 h-3 text-white" />
              </span>
            )}
            {/* Error indicator */}
            {hasUnacknowledgedError && (
              <span className="absolute -bottom-1 -left-1 w-4 h-4 bg-[var(--color-warn)] rounded-full flex items-center justify-center animate-pulse">
                <AlertCircle className="w-3 h-3 text-white" />
              </span>
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Panel */}
      <AnimatePresence>
        {panelState !== 'hidden' && (
          <motion.div
            {...panelVariants}
            transition={prefersReducedMotion ? { duration: 0 } : { type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 h-full z-[var(--z-modal)]"
            style={{ width: isMobile ? PANEL_WIDTH_MOBILE : PANEL_WIDTH }}
            role="dialog"
            aria-label="Activity Feed"
            aria-modal="true"
          >
            <GlassCard
              variant="elevated"
              padding="none"
              className="h-full flex flex-col rounded-none rounded-l-[var(--radius-lg)] border-r-0"
            >
              {/* Header */}
              <div className={`flex items-center justify-between px-4 py-3 border-b border-[var(--glass-border)] ${WORKFLOW_STATUS_CONFIG[workflowStatus].bgColor}`}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[rgba(139,92,246,0.15)] flex items-center justify-center">
                    <Activity className="w-4 h-4 text-[var(--color-neural)]" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-[var(--color-plasma)]">Activity</h3>
                      {renderWorkflowStatus()}
                    </div>
                    {renderConnectionStatus()}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {/* Filter toggle */}
                  {sessionMolecules.size > 0 && (
                    <button
                      onClick={() => setFilterToSession(!filterToSession)}
                      className={`p-1.5 rounded transition-colors ${filterToSession ? 'bg-[var(--color-neural)]/20 text-[var(--color-neural)]' : 'hover:bg-[var(--glass-bg-hover)] text-[var(--color-muted)]'}`}
                      title={filterToSession ? 'Show all events' : 'Show only my work'}
                      aria-pressed={filterToSession}
                    >
                      <Filter className="w-4 h-4" />
                    </button>
                  )}
                  {/* Clear history */}
                  <button
                    onClick={clearHistory}
                    className="p-1.5 hover:bg-[var(--glass-bg-hover)] rounded transition-colors text-[var(--color-muted)]"
                    title="Clear history"
                    aria-label="Clear activity history"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  {/* Minimize/Expand */}
                  <button
                    onClick={toggleMinimize}
                    className="p-1.5 hover:bg-[var(--glass-bg-hover)] rounded transition-colors"
                    title={panelState === 'minimized' ? 'Expand' : 'Minimize'}
                    aria-label={panelState === 'minimized' ? 'Expand panel' : 'Minimize panel'}
                  >
                    {panelState === 'minimized' ? (
                      <Maximize2 className="w-4 h-4 text-[var(--color-muted)]" />
                    ) : (
                      <Minimize2 className="w-4 h-4 text-[var(--color-muted)]" />
                    )}
                  </button>
                  {/* Close */}
                  <button
                    onClick={closePanel}
                    className="p-1.5 hover:bg-[var(--glass-bg-hover)] rounded transition-colors"
                    title="Close (Escape)"
                    aria-label="Close activity panel"
                  >
                    <X className="w-4 h-4 text-[var(--color-muted)]" />
                  </button>
                </div>
              </div>

              {/* Error acknowledgment banner */}
              {hasUnacknowledgedError && panelState === 'open' && (
                <div className="px-4 py-2 bg-[rgba(239,68,68,0.1)] border-b border-[var(--color-warn)]/30 flex items-center justify-between">
                  <span className="text-xs text-[var(--color-warn)] flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Errors occurred during execution
                  </span>
                  <button
                    onClick={acknowledgeErrors}
                    className="text-xs text-[var(--color-warn)] hover:underline"
                  >
                    Dismiss
                  </button>
                </div>
              )}

              {/* Events list */}
              {panelState === 'open' && (
                <div
                  className="flex-1 overflow-y-auto"
                  role="log"
                  aria-label="Activity events"
                  aria-live="polite"
                >
                  {displayEvents.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center p-6">
                      <Activity className="w-12 h-12 text-[var(--color-muted)] mb-3 opacity-50" />
                      <p className="text-sm text-[var(--color-muted)]">
                        {filterToSession ? 'No activity for your session yet' : 'No activity yet'}
                      </p>
                      <p className="text-xs text-[var(--color-muted)] mt-1 opacity-70">
                        Events will appear here as work progresses
                      </p>
                    </div>
                  ) : (
                    <div className="py-2">
                      {displayEvents.map((event, index) => (
                        <ActivityEventItem
                          key={event.event_id || index}
                          event={event}
                          isLast={index === displayEvents.length - 1}
                          isSessionEvent={event.molecule_id ? sessionMolecules.has(event.molecule_id) : false}
                          isExpanded={expandedErrorId === event.event_id}
                          onToggleExpand={() => setExpandedErrorId(
                            expandedErrorId === event.event_id ? null : event.event_id
                          )}
                          prefersReducedMotion={prefersReducedMotion}
                        />
                      ))}
                      <div ref={eventsEndRef} />
                    </div>
                  )}
                </div>
              )}

              {/* Minimized state */}
              {panelState === 'minimized' && (
                <button
                  className="flex-1 flex items-center justify-center cursor-pointer hover:bg-[var(--glass-bg-hover)] transition-colors"
                  onClick={() => setPanelState('open')}
                  aria-label={`${displayEvents.length} events. Click to expand.`}
                >
                  <div className="text-center p-4">
                    <p className="text-2xl font-bold text-[var(--color-plasma)]">{displayEvents.length}</p>
                    <p className="text-xs text-[var(--color-muted)]">events</p>
                    {completedCount > 0 && (
                      <p className="text-xs text-[var(--color-ok)] mt-1">
                        {completedCount} completed
                      </p>
                    )}
                    {errorCount > 0 && (
                      <p className="text-xs text-[var(--color-warn)] mt-1">
                        {errorCount} errors
                      </p>
                    )}
                  </div>
                </button>
              )}

              {/* Footer with summary request */}
              {panelState === 'open' && workflowStatus === 'completed' && onMoleculeComplete && (
                <div className="px-4 py-3 border-t border-[var(--glass-border)] bg-[rgba(34,197,94,0.05)]">
                  <button
                    onClick={() => {
                      // Find most recent completed molecule
                      const lastCompleted = [...events]
                        .reverse()
                        .find(e => e.raw_type === 'molecule.completed');
                      if (lastCompleted?.molecule_id) {
                        onMoleculeComplete(lastCompleted.molecule_id, 'summary');
                      }
                    }}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-[var(--color-ok)]/10 hover:bg-[var(--color-ok)]/20 text-[var(--color-ok)] text-sm font-medium transition-colors"
                  >
                    <MessageSquare className="w-4 h-4" />
                    Get Summary in Chat
                  </button>
                </div>
              )}
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// =============================================================================
// ACTIVITY EVENT ITEM COMPONENT
// =============================================================================

interface ActivityEventItemProps {
  event: ActivityEvent;
  isLast?: boolean;
  isSessionEvent?: boolean;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  prefersReducedMotion?: boolean;
}

function ActivityEventItem({
  event,
  isLast,
  isSessionEvent,
  isExpanded,
  onToggleExpand,
  prefersReducedMotion,
}: ActivityEventItemProps) {
  const status = severityToStatus[event.display.severity] || 'idle';
  const isError = event.display.severity === 'error';

  return (
    <motion.div
      initial={prefersReducedMotion ? {} : { opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`px-4 py-3 transition-colors ${
        !isLast ? 'border-b border-[var(--glass-border)]' : ''
      } ${isSessionEvent ? 'bg-[rgba(139,92,246,0.05)]' : ''} ${
        isError ? 'hover:bg-[rgba(239,68,68,0.05)]' : 'hover:bg-[var(--glass-bg-hover)]'
      }`}
      role="article"
      aria-label={`${event.display.phase}: ${event.display.message}`}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
            isError
              ? 'bg-[rgba(239,68,68,0.15)] border border-[var(--color-warn)]/30'
              : 'bg-[var(--glass-bg)] border border-[var(--glass-border)]'
          }`}>
            <span className="text-xs">{event.display.icon}</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <StatusOrb status={status} size="sm" pulse={status === 'processing'} />
            <span className="text-xs text-[var(--color-muted)] uppercase tracking-wider">
              {event.display.phase}
            </span>
            {isSessionEvent && (
              <span className="text-[10px] text-[var(--color-neural)] bg-[rgba(139,92,246,0.15)] px-1.5 py-0.5 rounded">
                Your work
              </span>
            )}
          </div>
          <p className={`text-sm leading-tight ${isError ? 'text-[var(--color-warn)]' : 'text-[var(--color-plasma)]'}`}>
            {event.display.message}
          </p>

          {/* Error details (expandable) */}
          {isError && (
            <div className="mt-2">
              <button
                onClick={onToggleExpand}
                className="text-xs text-[var(--color-warn)] hover:underline flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                {isExpanded ? 'Hide details' : 'View details'}
              </button>
              {isExpanded && (
                <div className="mt-2 p-2 rounded bg-[rgba(239,68,68,0.1)] text-xs text-[var(--color-warn)]/80 font-mono">
                  Event ID: {event.event_id}
                  {event.molecule_id && <div>Molecule: {event.molecule_id}</div>}
                  {event.step_id && <div>Step: {event.step_id}</div>}
                </div>
              )}
            </div>
          )}

          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-[var(--color-muted)]">
              {formatRelativeTime(event.timestamp)}
            </span>
            {event.aggregated_count && event.aggregated_count > 1 && (
              <span className="text-xs text-[var(--color-neural)] bg-[rgba(139,92,246,0.15)] px-1.5 py-0.5 rounded">
                +{event.aggregated_count - 1} more
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
