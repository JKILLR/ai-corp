import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, X, Minimize2, Maximize2, Wifi, WifiOff, AlertCircle } from 'lucide-react';
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

interface ActivityPanelProps {
  /** Initial state of the panel */
  initialState?: PanelState;
  /** Whether to auto-open on new events */
  autoOpen?: boolean;
  /** WebSocket URL override (defaults to /api/ws/activity) */
  wsUrl?: string;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const PANEL_WIDTH = 340;
const MAX_EVENTS = 50;
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000]; // Exponential backoff

// Severity to status mapping for StatusOrb
const severityToStatus: Record<string, 'ok' | 'processing' | 'warning' | 'waiting' | 'idle'> = {
  success: 'ok',
  info: 'processing',
  warning: 'warning',
  error: 'warning',
};

// Connection status config (defined outside component to avoid recreation on each render)
const CONNECTION_STATUS_CONFIG: Record<ConnectionStatus, { text: string; color: string }> = {
  connecting: { text: 'Connecting...', color: 'text-[var(--color-wait)]' },
  connected: { text: 'Live', color: 'text-[var(--color-ok)]' },
  disconnected: { text: 'Disconnected', color: 'text-[var(--color-muted)]' },
  error: { text: 'Error', color: 'text-[var(--color-warn)]' },
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

// =============================================================================
// ACTIVITY PANEL COMPONENT
// =============================================================================

export function ActivityPanel({
  initialState = 'hidden',
  autoOpen = true,
  wsUrl,
}: ActivityPanelProps) {
  // State
  const [panelState, setPanelState] = useState<PanelState>(initialState);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [unreadCount, setUnreadCount] = useState(0);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);
  const hasReceivedFirstEvent = useRef(false);
  const panelStateRef = useRef(panelState);

  // Keep ref in sync with state (avoid stale closures)
  panelStateRef.current = panelState;

  // Auto-scroll to bottom when new events arrive
  const scrollToBottom = useCallback(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Handle a single activity event
  const handleActivityEvent = useCallback((event: ActivityEvent) => {
    setEvents((prev) => {
      const newEvents = [...prev, event];
      // Keep only the last MAX_EVENTS
      return newEvents.slice(-MAX_EVENTS);
    });

    // Auto-open logic
    if (autoOpen) {
      // Auto-open on first event ever
      if (!hasReceivedFirstEvent.current) {
        hasReceivedFirstEvent.current = true;
        setPanelState('open');
      }
      // Auto-open on errors
      else if (event.display.severity === 'error') {
        setPanelState('open');
      }
      // Auto-open on new molecule started
      else if (event.raw_type === 'molecule.created' || event.raw_type === 'molecule.started') {
        setPanelState('open');
      }
    }

    // Track unread if panel is not open (use ref to avoid stale closure)
    if (panelStateRef.current !== 'open') {
      setUnreadCount((prev) => prev + 1);
    }
  }, [autoOpen]);

  // Handle incoming WebSocket messages (supports different message types)
  const handleMessage = useCallback((rawData: unknown) => {
    // Type guard for message structure
    if (!rawData || typeof rawData !== 'object') return;

    const data = rawData as Record<string, unknown>;

    // Handle history message (sent on connection)
    if (data.type === 'history' && Array.isArray(data.events)) {
      const historyEvents = data.events as ActivityEvent[];
      if (historyEvents.length > 0) {
        setEvents(historyEvents.slice(-MAX_EVENTS));
        hasReceivedFirstEvent.current = true;
      }
      return;
    }

    // Handle pong (keepalive response) - no action needed
    if (data.type === 'pong') {
      return;
    }

    // Handle stats response - no action needed for now
    if (data.type === 'stats') {
      return;
    }

    // Handle individual activity event (has event_id and display)
    if (data.event_id && data.display) {
      handleActivityEvent(data as unknown as ActivityEvent);
    }
  }, [handleActivityEvent]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

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

      ws.onerror = () => {
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Auto-reconnect with exponential backoff
        const attempt = reconnectAttemptRef.current;
        const delay = RECONNECT_DELAYS[Math.min(attempt, RECONNECT_DELAYS.length - 1)];
        reconnectAttemptRef.current = attempt + 1;

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err) {
      setConnectionStatus('error');
    }
  }, [wsUrl, handleMessage]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Scroll to bottom when events change and panel is open
  useEffect(() => {
    if (panelState === 'open') {
      scrollToBottom();
    }
  }, [events, panelState, scrollToBottom]);

  // Clear unread count when panel opens
  useEffect(() => {
    if (panelState === 'open') {
      setUnreadCount(0);
    }
  }, [panelState]);

  // Panel controls
  const openPanel = () => setPanelState('open');
  const closePanel = () => setPanelState('hidden');
  const toggleMinimize = () => setPanelState(panelState === 'minimized' ? 'open' : 'minimized');

  // Render connection indicator
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

  return (
    <>
      {/* Trigger button when panel is hidden */}
      <AnimatePresence>
        {panelState === 'hidden' && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            onClick={openPanel}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="fixed bottom-24 right-6 w-12 h-12 rounded-full bg-[var(--glass-bg)] border border-[var(--glass-border)] backdrop-blur-[var(--glass-blur)] shadow-lg flex items-center justify-center z-[var(--z-modal)] hover:bg-[var(--glass-bg-hover)] transition-colors"
            title="Open Activity Feed"
          >
            <Activity className="w-5 h-5 text-[var(--color-neural)]" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-[var(--color-neural)] rounded-full flex items-center justify-center text-[10px] text-white font-bold">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Panel */}
      <AnimatePresence>
        {panelState !== 'hidden' && (
          <motion.div
            initial={{ x: PANEL_WIDTH + 24, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: PANEL_WIDTH + 24, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 h-full z-[var(--z-modal)]"
            style={{ width: PANEL_WIDTH }}
          >
            <GlassCard
              variant="elevated"
              padding="none"
              className="h-full flex flex-col rounded-none rounded-l-[var(--radius-lg)] border-r-0"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--glass-border)]">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[rgba(139,92,246,0.15)] flex items-center justify-center">
                    <Activity className="w-4 h-4 text-[var(--color-neural)]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-[var(--color-plasma)]">Activity</h3>
                    {renderConnectionStatus()}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={toggleMinimize}
                    className="p-1.5 hover:bg-[var(--glass-bg-hover)] rounded transition-colors"
                    title={panelState === 'minimized' ? 'Expand' : 'Minimize'}
                  >
                    {panelState === 'minimized' ? (
                      <Maximize2 className="w-4 h-4 text-[var(--color-muted)]" />
                    ) : (
                      <Minimize2 className="w-4 h-4 text-[var(--color-muted)]" />
                    )}
                  </button>
                  <button
                    onClick={closePanel}
                    className="p-1.5 hover:bg-[var(--glass-bg-hover)] rounded transition-colors"
                    title="Close"
                  >
                    <X className="w-4 h-4 text-[var(--color-muted)]" />
                  </button>
                </div>
              </div>

              {/* Events list */}
              {panelState === 'open' && (
                <div className="flex-1 overflow-y-auto">
                  {events.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center p-6">
                      <Activity className="w-12 h-12 text-[var(--color-muted)] mb-3 opacity-50" />
                      <p className="text-sm text-[var(--color-muted)]">No activity yet</p>
                      <p className="text-xs text-[var(--color-muted)] mt-1 opacity-70">
                        Events will appear here as work progresses
                      </p>
                    </div>
                  ) : (
                    <div className="py-2">
                      {events.map((event, index) => (
                        <ActivityEventItem
                          key={event.event_id || index}
                          event={event}
                          isLast={index === events.length - 1}
                        />
                      ))}
                      <div ref={eventsEndRef} />
                    </div>
                  )}
                </div>
              )}

              {/* Minimized state - show just event count */}
              {panelState === 'minimized' && (
                <div
                  className="flex-1 flex items-center justify-center cursor-pointer hover:bg-[var(--glass-bg-hover)] transition-colors"
                  onClick={() => setPanelState('open')}
                >
                  <div className="text-center p-4">
                    <p className="text-2xl font-bold text-[var(--color-plasma)]">{events.length}</p>
                    <p className="text-xs text-[var(--color-muted)]">events</p>
                  </div>
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
}

function ActivityEventItem({ event, isLast }: ActivityEventItemProps) {
  const status = severityToStatus[event.display.severity] || 'idle';

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`px-4 py-3 hover:bg-[var(--glass-bg-hover)] transition-colors ${
        !isLast ? 'border-b border-[var(--glass-border)]' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Icon/Status indicator */}
        <div className="flex-shrink-0 mt-0.5">
          <div className="w-6 h-6 rounded-full bg-[var(--glass-bg)] border border-[var(--glass-border)] flex items-center justify-center">
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
          </div>
          <p className="text-sm text-[var(--color-plasma)] leading-tight">
            {event.display.message}
          </p>
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

