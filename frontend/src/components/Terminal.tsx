/**
 * Terminal Component - Live execution view for COO
 *
 * Shows real-time streaming output from Claude execution:
 * - Thinking/reasoning (collapsible)
 * - Tool usage (Read, Write, Bash, etc.)
 * - Tool results
 * - Final content
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Terminal as TerminalIcon,
  ChevronDown,
  ChevronRight,
  Play,
  Square,
  Loader2,
  FileText,
  Code,
  Search,
  Globe,
  CheckCircle,
  XCircle,
  Brain,
  Maximize2,
  Minimize2,
  X
} from 'lucide-react';
import { GlassCard } from './ui';

interface StreamEvent {
  type: 'start' | 'thinking' | 'content' | 'tool_use' | 'tool_input' | 'tool_result' | 'done' | 'error';
  content?: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_result?: string;
}

interface TerminalProps {
  isOpen: boolean;
  onClose: () => void;
  onExecute: (prompt: string) => void;
  threadId?: string;
}

const API_WS_URL = import.meta.env.VITE_API_WS_URL || 'ws://localhost:8001';

export function Terminal({ isOpen, onClose, threadId }: TerminalProps) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [expandedThinking, setExpandedThinking] = useState<Set<number>>(new Set());

  const wsRef = useRef<WebSocket | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [events]);

  // Connect WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${API_WS_URL}/api/ws/coo/execute`);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('Terminal WebSocket connected');
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsExecuting(false);
      console.log('Terminal WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('Terminal WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onmessage = (event) => {
      try {
        const data: StreamEvent = JSON.parse(event.data);
        setEvents(prev => [...prev, data]);

        if (data.type === 'done' || data.type === 'error') {
          setIsExecuting(false);
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    wsRef.current = ws;
  }, []);

  // Disconnect on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  // Connect when opened
  useEffect(() => {
    if (isOpen && !isConnected) {
      connect();
    }
  }, [isOpen, isConnected, connect]);

  const executePrompt = () => {
    if (!prompt.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    setIsExecuting(true);
    setEvents([]);

    wsRef.current.send(JSON.stringify({
      type: 'execute',
      prompt: prompt.trim(),
      thread_id: threadId
    }));

    setPrompt('');
  };

  const stopExecution = () => {
    wsRef.current?.close();
    setIsExecuting(false);
    setIsConnected(false);
  };

  const toggleThinking = (index: number) => {
    setExpandedThinking(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName?.toLowerCase()) {
      case 'read':
        return <FileText className="w-4 h-4" />;
      case 'write':
      case 'edit':
        return <Code className="w-4 h-4" />;
      case 'bash':
        return <TerminalIcon className="w-4 h-4" />;
      case 'glob':
      case 'grep':
        return <Search className="w-4 h-4" />;
      case 'webfetch':
      case 'websearch':
        return <Globe className="w-4 h-4" />;
      default:
        return <Code className="w-4 h-4" />;
    }
  };

  const renderEvent = (event: StreamEvent, index: number) => {
    switch (event.type) {
      case 'start':
        return (
          <div key={index} className="flex items-center gap-2 text-blue-400 py-1">
            <Play className="w-4 h-4" />
            <span>{event.content}</span>
          </div>
        );

      case 'thinking':
        if (!event.content) return null;
        const isExpanded = expandedThinking.has(index);
        return (
          <div key={index} className="py-1">
            <button
              onClick={() => toggleThinking(index)}
              className="flex items-center gap-2 text-purple-400 hover:text-purple-300 transition-colors"
            >
              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <Brain className="w-4 h-4" />
              <span className="text-sm">Thinking...</span>
            </button>
            {isExpanded && (
              <pre className="mt-1 ml-6 p-2 text-xs text-gray-400 bg-gray-900/50 rounded overflow-x-auto">
                {event.content}
              </pre>
            )}
          </div>
        );

      case 'tool_use':
        return (
          <div key={index} className="flex items-center gap-2 text-yellow-400 py-1">
            {getToolIcon(event.tool_name || '')}
            <span className="font-mono">{event.tool_name}</span>
            {event.tool_input && (
              <span className="text-gray-500 text-sm truncate max-w-md">
                {JSON.stringify(event.tool_input).slice(0, 100)}...
              </span>
            )}
          </div>
        );

      case 'tool_result':
        return (
          <div key={index} className="py-1 ml-6">
            <pre className="text-xs text-green-400/80 bg-gray-900/50 p-2 rounded overflow-x-auto max-h-48 overflow-y-auto">
              {event.tool_result?.slice(0, 2000)}
              {(event.tool_result?.length || 0) > 2000 && '... (truncated)'}
            </pre>
          </div>
        );

      case 'content':
        if (!event.content) return null;
        return (
          <div key={index} className="text-gray-200 py-0.5 whitespace-pre-wrap">
            {event.content}
          </div>
        );

      case 'done':
        return (
          <div key={index} className="flex items-center gap-2 text-green-400 py-2 border-t border-gray-700 mt-2">
            <CheckCircle className="w-4 h-4" />
            <span>Execution complete</span>
          </div>
        );

      case 'error':
        return (
          <div key={index} className="flex items-center gap-2 text-red-400 py-1">
            <XCircle className="w-4 h-4" />
            <span>{event.content}</span>
          </div>
        );

      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        className={`fixed ${isFullscreen ? 'inset-4' : 'bottom-4 right-4 w-[600px] h-[500px]'} z-50`}
      >
        <GlassCard className="h-full flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <TerminalIcon className="w-5 h-5 text-green-400" />
              <span className="font-medium">COO Terminal</span>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-1.5 hover:bg-white/10 rounded transition-colors"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={onClose}
                className="p-1.5 hover:bg-white/10 rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Terminal Output */}
          <div
            ref={terminalRef}
            className="flex-1 p-3 overflow-y-auto font-mono text-sm bg-black/30"
          >
            {events.length === 0 && !isExecuting && (
              <div className="text-gray-500 text-center py-8">
                Enter a command below to execute with full system access
              </div>
            )}
            {events.map((event, index) => renderEvent(event, index))}
            {isExecuting && events[events.length - 1]?.type !== 'done' && (
              <div className="flex items-center gap-2 text-blue-400 py-1">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Executing...</span>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-3 border-t border-white/10">
            <div className="flex gap-2">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && executePrompt()}
                placeholder="Enter command for COO to execute..."
                className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-500/50"
                disabled={isExecuting}
              />
              {isExecuting ? (
                <button
                  onClick={stopExecution}
                  className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Square className="w-4 h-4" />
                  Stop
                </button>
              ) : (
                <button
                  onClick={executePrompt}
                  disabled={!prompt.trim() || !isConnected}
                  className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="w-4 h-4" />
                  Execute
                </button>
              )}
            </div>
            {!isConnected && (
              <button
                onClick={connect}
                className="mt-2 text-sm text-blue-400 hover:text-blue-300"
              >
                Reconnect to terminal
              </button>
            )}
          </div>
        </GlassCard>
      </motion.div>
    </AnimatePresence>
  );
}

export default Terminal;
