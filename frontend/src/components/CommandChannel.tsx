import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, X, Minimize2, Maximize2, MessageSquare, Sparkles, User, Bot } from 'lucide-react';
import { GlassCard, Button } from './ui';

interface Message {
  id: string;
  role: 'user' | 'coo';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'thinking';
}

// Mock conversation for demo
const initialMessages: Message[] = [
  {
    id: '1',
    role: 'coo',
    content: "Good morning. I've reviewed the overnight activity. The Website Redesign is progressing well - we're at 67% completion. However, I need your input on the Data Pipeline project. Research-001 is blocked waiting for data access approval. Should I escalate this or wait for the standard approval process?",
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    status: 'sent',
  },
  {
    id: '2',
    role: 'user',
    content: "Let's escalate the data access. It's been blocking for too long. What's the holdup?",
    timestamp: new Date(Date.now() - 1000 * 60 * 25),
    status: 'sent',
  },
  {
    id: '3',
    role: 'coo',
    content: "The security team flagged concerns about PII exposure in the raw dataset. I can either: (1) Have the security team sanitize the data first, adding ~2 days, or (2) Scope down to anonymized aggregates only, which would let us proceed immediately but limit our analysis depth. Which approach aligns better with your priorities for this quarter?",
    timestamp: new Date(Date.now() - 1000 * 60 * 20),
    status: 'sent',
  },
];

interface CommandChannelProps {
  isOpen: boolean;
  onClose: () => void;
  isMinimized: boolean;
  onToggleMinimize: () => void;
}

export function CommandChannel({ isOpen, onClose, isMinimized, onToggleMinimize }: CommandChannelProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
      status: 'sent',
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate COO thinking and responding
    setTimeout(() => {
      const cooResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'coo',
        content: generateCOOResponse(input.trim()),
        timestamp: new Date(),
        status: 'sent',
      };
      setMessages((prev) => [...prev, cooResponse]);
      setIsTyping(false);
    }, 1500 + Math.random() * 1000);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{
          opacity: 1,
          y: 0,
          scale: 1,
          height: isMinimized ? 'auto' : '600px',
        }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed bottom-6 right-6 w-[420px] z-[var(--z-modal)] flex flex-col"
      >
        <GlassCard variant="elevated" padding="none" className="flex flex-col h-full overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--glass-border)] bg-[rgba(139,92,246,0.1)]">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--color-neural)] flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--color-plasma)]">COO Channel</h3>
                <p className="text-xs text-[var(--color-ok)] flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-ok)]" />
                  Online • Ready to assist
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={onToggleMinimize}
                className="p-1.5 hover:bg-[var(--glass-bg)] rounded transition-colors"
              >
                {isMinimized ? (
                  <Maximize2 className="w-4 h-4 text-[var(--color-muted)]" />
                ) : (
                  <Minimize2 className="w-4 h-4 text-[var(--color-muted)]" />
                )}
              </button>
              <button
                onClick={onClose}
                className="p-1.5 hover:bg-[var(--glass-bg)] rounded transition-colors"
              >
                <X className="w-4 h-4 text-[var(--color-muted)]" />
              </button>
            </div>
          </div>

          {/* Messages */}
          {!isMinimized && (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}

                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-start gap-2"
                  >
                    <div className="w-7 h-7 rounded-full bg-[var(--color-neural)] flex items-center justify-center flex-shrink-0">
                      <Bot className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div className="px-3 py-2 rounded-lg bg-[var(--glass-bg)] border border-[var(--glass-border)]">
                      <div className="flex items-center gap-1">
                        <motion.span
                          animate={{ opacity: [0.4, 1, 0.4] }}
                          transition={{ duration: 1, repeat: Infinity }}
                          className="w-1.5 h-1.5 rounded-full bg-[var(--color-neural)]"
                        />
                        <motion.span
                          animate={{ opacity: [0.4, 1, 0.4] }}
                          transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                          className="w-1.5 h-1.5 rounded-full bg-[var(--color-neural)]"
                        />
                        <motion.span
                          animate={{ opacity: [0.4, 1, 0.4] }}
                          transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                          className="w-1.5 h-1.5 rounded-full bg-[var(--color-neural)]"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-3 border-t border-[var(--glass-border)]">
                <div className="flex items-end gap-2">
                  <div className="flex-1 relative">
                    <textarea
                      ref={inputRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Message the COO..."
                      rows={1}
                      className="w-full px-3 py-2 pr-10 rounded-lg bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none focus:border-[var(--color-neural)] resize-none transition-colors"
                      style={{ minHeight: '40px', maxHeight: '120px' }}
                    />
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleSend}
                    disabled={!input.trim()}
                    className="h-10 w-10 p-0 flex items-center justify-center"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-[var(--color-muted)] mt-2 flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  COO will delegate tasks and coordinate with department heads
                </p>
              </div>
            </>
          )}
        </GlassCard>
      </motion.div>
    </AnimatePresence>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-[var(--color-ok)]' : 'bg-[var(--color-neural)]'
      }`}>
        {isUser ? (
          <User className="w-3.5 h-3.5 text-white" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-white" />
        )}
      </div>
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-3 py-2 rounded-lg text-sm ${
          isUser
            ? 'bg-[var(--color-neural)] text-white rounded-br-sm'
            : 'bg-[var(--glass-bg)] border border-[var(--glass-border)] text-[var(--color-plasma)] rounded-bl-sm'
        }`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <p className={`text-xs text-[var(--color-muted)] mt-1 ${isUser ? 'text-right' : ''}`}>
          {formatTime(message.timestamp)}
        </p>
      </div>
    </motion.div>
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
}

// Simple response generator for demo
function generateCOOResponse(input: string): string {
  const lower = input.toLowerCase();

  if (lower.includes('sanitize') || lower.includes('option 1') || lower.includes('security')) {
    return "Understood. I'll instruct the security team to prioritize data sanitization. I'll have Head of Research coordinate with them to define exactly which fields need anonymization. Expected completion: 2 days. I'll update you when the sanitized dataset is ready and Research-001 can resume. Anything else you'd like me to prioritize?";
  }

  if (lower.includes('aggregate') || lower.includes('option 2') || lower.includes('proceed')) {
    return "Got it. I'll have Research-001 proceed with anonymized aggregates immediately. This limits our ability to do user-level analysis, but we can still derive meaningful insights for the pipeline optimization. I'll flag if we hit any blockers that require the full dataset. The team should have initial results by end of day.";
  }

  if (lower.includes('status') || lower.includes('update') || lower.includes('how')) {
    return "Here's the current status across projects:\n\n• Website Redesign: 67% - On track, dev-001 implementing hero section\n• API Integration: 89% - Nearly complete, finalizing OAuth\n• Data Pipeline: 45% - Blocked on data access (awaiting your decision)\n• Mobile App: 23% - Active development, 4 agents working\n• Security Audit: 10% - Waiting for scope approval\n\nWould you like me to dive deeper into any of these?";
  }

  if (lower.includes('priorit') || lower.includes('focus') || lower.includes('important')) {
    return "Based on current commitments and deadlines, I'd recommend prioritizing:\n\n1. **Data Pipeline** - It's blocking downstream work\n2. **Website Redesign** - Closest to completion, high visibility\n3. **API Integration** - Nearly done, quick win\n\nThe Mobile App and Security Audit can continue at current pace. Should I reallocate any agents to accelerate specific projects?";
  }

  if (lower.includes('agent') || lower.includes('team') || lower.includes('resource')) {
    return "Current agent allocation:\n\n• Engineering: 4 agents (dev-001 through dev-003, qa-001)\n• Design: 2 agents (design-001, design-002)\n• Research: 2 agents (research-001, research-002)\n\nAll agents are at healthy load levels except research-001 who is blocked. I can spin up additional agents if we need to accelerate any workstream. What would you like to adjust?";
  }

  return "I've noted that. Let me think through the implications and coordinate with the relevant department heads. Is there a specific timeline or constraint I should be aware of for this? I want to make sure we align execution with your expectations.";
}

// Floating trigger button component
export function CommandChannelTrigger({ onClick, hasUnread }: { onClick: () => void; hasUnread?: boolean }) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-[var(--color-neural)] shadow-lg shadow-[var(--color-neural)]/30 flex items-center justify-center z-[var(--z-modal)] hover:shadow-[var(--color-neural)]/50 transition-shadow"
    >
      <MessageSquare className="w-6 h-6 text-white" />
      {hasUnread && (
        <span className="absolute top-0 right-0 w-4 h-4 bg-[var(--color-warn)] rounded-full flex items-center justify-center text-[10px] text-white font-bold">
          1
        </span>
      )}
    </motion.button>
  );
}
