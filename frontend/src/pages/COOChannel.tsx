import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Paperclip, Bot, User, Sparkles, Clock, ChevronDown, Plus, Search } from 'lucide-react';
import { GlassCard, Button, StatusOrb } from '../components/ui';

interface Message {
  id: string;
  role: 'user' | 'coo';
  content: string;
  timestamp: Date;
  context?: {
    type: 'project' | 'agent' | 'gate' | 'system';
    reference: string;
  };
}

interface ConversationThread {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  unread: boolean;
}

// Mock conversation history
const conversationHistory: Message[] = [
  {
    id: '1',
    role: 'coo',
    content: "Good morning. Starting daily brief:\n\n**Active Projects:** 5 total\n• Website Redesign: 67% (on track)\n• API Integration: 89% (nearly complete)\n• Data Pipeline: 45% (BLOCKED)\n• Mobile App: 23% (active)\n• Security Audit: 10% (waiting)\n\n**Attention Required:**\n1. Data Pipeline blocked - research-001 needs data access\n2. 2 gate approvals pending in queue\n\nHow would you like to proceed today?",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
  },
  {
    id: '2',
    role: 'user',
    content: "What's blocking the Data Pipeline exactly? And what are the gate approvals for?",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 1.9),
  },
  {
    id: '3',
    role: 'coo',
    content: "**Data Pipeline Block:**\nResearch-001 requested access to the production user analytics database for the pipeline refactor. Security team flagged PII concerns. They're asking for either:\n- Option A: Sanitized dataset (adds 2 days)\n- Option B: Anonymized aggregates only (immediate, but limited analysis)\n\n**Pending Gates:**\n1. **Deploy to Production** - Website Redesign ready for prod deployment, all tests passing. Requested by dev-003.\n2. **Security Review** - New API endpoints need security audit before going live. Flagged by qa-001.\n\nBoth have been waiting ~30 minutes. The deploy gate is higher priority given we're close to the redesign deadline.",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 1.8),
    context: { type: 'project', reference: 'Data Pipeline Refactor' },
  },
  {
    id: '4',
    role: 'user',
    content: "Go with Option A for the data pipeline - I'd rather have complete data even if it takes longer. And approve the website deploy, but hold on the security review until I look at it.",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 1.5),
  },
  {
    id: '5',
    role: 'coo',
    content: "Understood. Executing:\n\n✓ Instructed security team to prepare sanitized dataset for Data Pipeline\n✓ Approved Website Redesign production deployment\n✓ Security Review gate held - I'll remind you to review it later\n\nResearch-001 is now unblocked and will resume work once the sanitized data is ready (~2 days). Dev-003 has begun the production deployment process.\n\nIs there anything specific you'd like me to prioritize for the Mobile App MVP? It's currently the lowest completion but has the most agents assigned (4).",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 1.4),
  },
  {
    id: '6',
    role: 'user',
    content: "The mobile app is fine for now, let it run. I want to talk about expanding the team. We're going to need more agents for Q2. What's our current capacity and what would you recommend?",
    timestamp: new Date(Date.now() - 1000 * 60 * 45),
  },
  {
    id: '7',
    role: 'coo',
    content: "Current agent capacity analysis:\n\n**Active Agents:** 12 total\n• Engineering: 4 (dev-001 to dev-003, qa-001)\n• Design: 2 (design-001, design-002)\n• Research: 2 (research-001, research-002)\n• Department Heads: 3 (myself, Head of Eng, Head of Design, Head of Research)\n\n**Current Load:**\n• Average utilization: 72%\n• Peak utilization: 95% (dev-001)\n• Idle capacity: ~28%\n\n**Q2 Recommendations:**\nBased on the project pipeline you've outlined:\n\n1. **+2 Senior Developers** - Mobile App and upcoming API v2 will need more backend capacity\n2. **+1 QA Engineer** - qa-001 is stretched thin across 3 projects\n3. **+1 Security Specialist** - Dedicated security rather than borrowed from QA\n\nThis would bring us to 16 agents with better coverage. Estimated onboarding time: 1-2 days per agent.\n\nWant me to draft role specifications for these positions?",
    timestamp: new Date(Date.now() - 1000 * 60 * 40),
  },
];

// Past conversation threads
const pastThreads: ConversationThread[] = [
  {
    id: 't1',
    title: 'Q1 Planning Discussion',
    lastMessage: 'Finalized the Q1 roadmap with 5 key initiatives...',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3),
    unread: false,
  },
  {
    id: 't2',
    title: 'Security Incident Response',
    lastMessage: 'All systems verified clean. Implementing additional monitoring...',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5),
    unread: false,
  },
  {
    id: 't3',
    title: 'Team Performance Review',
    lastMessage: 'Engineering team exceeded targets. Design needs support...',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7),
    unread: false,
  },
];

export function COOChannel() {
  const [messages, setMessages] = useState<Message[]>(conversationHistory);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showThreads, setShowThreads] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
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
      };
      setMessages((prev) => [...prev, cooResponse]);
      setIsTyping(false);
    }, 1500 + Math.random() * 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full -m-6">
      {/* Conversation Threads Sidebar */}
      <AnimatePresence>
        {showThreads && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="border-r border-[var(--glass-border)] overflow-hidden flex flex-col"
          >
            <div className="p-4 border-b border-[var(--glass-border)]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted)]" />
                <input
                  type="text"
                  placeholder="Search conversations..."
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none focus:border-[var(--color-neural)]"
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              <div className="mb-4">
                <p className="px-2 py-1 text-xs font-medium text-[var(--color-muted)] uppercase">Current</p>
                <button className="w-full p-3 rounded-lg bg-[var(--color-neural)]/10 border border-[var(--color-neural)]/30 text-left">
                  <p className="text-sm font-medium text-[var(--color-plasma)]">Today's Session</p>
                  <p className="text-xs text-[var(--color-muted)] truncate mt-1">Discussing Q2 expansion...</p>
                </button>
              </div>
              <div>
                <p className="px-2 py-1 text-xs font-medium text-[var(--color-muted)] uppercase">Past Conversations</p>
                {pastThreads.map((thread) => (
                  <button
                    key={thread.id}
                    className="w-full p-3 rounded-lg hover:bg-[var(--glass-bg)] text-left transition-colors"
                  >
                    <p className="text-sm font-medium text-[var(--color-plasma)]">{thread.title}</p>
                    <p className="text-xs text-[var(--color-muted)] truncate mt-1">{thread.lastMessage}</p>
                    <p className="text-xs text-[var(--color-muted)] mt-1">{formatDate(thread.timestamp)}</p>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--glass-border)]">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowThreads(!showThreads)}
              className={`p-2 rounded-lg transition-colors ${showThreads ? 'bg-[var(--color-neural)]/10 text-[var(--color-neural)]' : 'hover:bg-[var(--glass-bg)] text-[var(--color-muted)]'}`}
            >
              <ChevronDown className={`w-5 h-5 transition-transform ${showThreads ? 'rotate-90' : '-rotate-90'}`} />
            </button>
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-[var(--color-neural)] flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <span className="absolute bottom-0 right-0 w-3 h-3 bg-[var(--color-ok)] rounded-full border-2 border-[var(--color-void)]" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-[var(--color-plasma)]">COO Channel</h2>
                <p className="text-xs text-[var(--color-ok)] flex items-center gap-1">
                  <StatusOrb status="ok" size="sm" />
                  Online • Strategic oversight active
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm">
              <Clock className="w-4 h-4 mr-2" />
              View History
            </Button>
            <Button variant="secondary" size="sm">
              <Plus className="w-4 h-4 mr-2" />
              New Thread
            </Button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Date separator */}
          <div className="flex items-center gap-4">
            <div className="flex-1 h-px bg-[var(--glass-border)]" />
            <span className="text-xs text-[var(--color-muted)]">Today</span>
            <div className="flex-1 h-px bg-[var(--glass-border)]" />
          </div>

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3"
            >
              <div className="w-9 h-9 rounded-full bg-[var(--color-neural)] flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="px-4 py-3 rounded-2xl rounded-bl-md bg-[var(--glass-bg)] border border-[var(--glass-border)]">
                <div className="flex items-center gap-1.5">
                  <motion.span
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1, repeat: Infinity }}
                    className="w-2 h-2 rounded-full bg-[var(--color-neural)]"
                  />
                  <motion.span
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                    className="w-2 h-2 rounded-full bg-[var(--color-neural)]"
                  />
                  <motion.span
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                    className="w-2 h-2 rounded-full bg-[var(--color-neural)]"
                  />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-[var(--glass-border)]">
          <GlassCard padding="sm">
            <div className="flex items-end gap-3">
              <button className="p-2 hover:bg-[var(--glass-bg)] rounded-lg transition-colors text-[var(--color-muted)] hover:text-[var(--color-plasma)]">
                <Paperclip className="w-5 h-5" />
              </button>
              <div className="flex-1">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Message the COO... Ask questions, give directions, discuss strategy"
                  rows={1}
                  className="w-full px-0 py-2 bg-transparent text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none resize-none"
                  style={{ minHeight: '24px', maxHeight: '150px' }}
                />
              </div>
              <Button
                variant="primary"
                size="md"
                onClick={handleSend}
                disabled={!input.trim()}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </GlassCard>
          <p className="text-xs text-[var(--color-muted)] mt-2 px-2 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            COO understands context, delegates to department heads, and coordinates execution
          </p>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-[var(--color-ok)]' : 'bg-[var(--color-neural)]'
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 text-sm ${
          isUser
            ? 'bg-[var(--color-neural)] text-white rounded-2xl rounded-br-md'
            : 'bg-[var(--glass-bg)] border border-[var(--glass-border)] text-[var(--color-plasma)] rounded-2xl rounded-bl-md'
        }`}>
          <div className="whitespace-pre-wrap prose-sm prose-invert">
            {formatMessageContent(message.content)}
          </div>
        </div>
        {message.context && (
          <div className={`mt-1 ${isUser ? 'text-right' : ''}`}>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[var(--glass-bg)] text-xs text-[var(--color-muted)]">
              Re: {message.context.reference}
            </span>
          </div>
        )}
        <p className={`text-xs text-[var(--color-muted)] mt-1 ${isUser ? 'text-right' : ''}`}>
          {formatTime(message.timestamp)}
        </p>
      </div>
    </motion.div>
  );
}

function formatMessageContent(content: string) {
  // Simple markdown-like formatting
  return content.split('\n').map((line, i) => {
    if (line.startsWith('**') && line.endsWith('**')) {
      return <p key={i} className="font-semibold">{line.replace(/\*\*/g, '')}</p>;
    }
    if (line.startsWith('• ')) {
      return <p key={i} className="pl-2">{line}</p>;
    }
    if (line.startsWith('✓ ')) {
      return <p key={i} className="text-[var(--color-ok)]">{line}</p>;
    }
    if (line.match(/^\d+\./)) {
      return <p key={i} className="pl-2">{line}</p>;
    }
    return <p key={i}>{line}</p>;
  });
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
}

function formatDate(date: Date): string {
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function generateCOOResponse(input: string): string {
  const lower = input.toLowerCase();

  if (lower.includes('yes') || lower.includes('draft') || lower.includes('specification')) {
    return "I'll prepare the role specifications now.\n\n**Draft: Q2 Hiring Plan**\n\n**1. Senior Developer (x2)**\n- Focus: Backend/API development\n- Requirements: 3+ years experience, Node.js/Python proficiency\n- Assignment: Mobile App MVP, API v2\n\n**2. QA Engineer**\n- Focus: Automated testing, CI/CD integration\n- Requirements: Test automation experience, security testing knowledge\n- Assignment: Cross-project quality assurance\n\n**3. Security Specialist**\n- Focus: Security audits, vulnerability assessment\n- Requirements: Security certifications, penetration testing experience\n- Assignment: Dedicated security reviews, compliance\n\nShall I proceed with creating these agent profiles? Once approved, I can begin the onboarding process immediately.";
  }

  if (lower.includes('status') || lower.includes('update') || lower.includes('report')) {
    return "Here's the latest status:\n\n**Project Updates:**\n• Website Redesign: 71% (+4%) - Deploy in progress\n• API Integration: 92% (+3%) - Final testing\n• Data Pipeline: 45% (unchanged) - Awaiting sanitized data\n• Mobile App: 25% (+2%) - Navigation complete\n• Security Audit: 10% - Awaiting your review\n\n**Agent Status:**\n• 11/12 agents active\n• research-001 on standby (waiting for data)\n• Average load: 68%\n\n**Pending Actions:**\n• Security Review gate needs your attention\n\nAnything specific you'd like me to dig into?";
  }

  if (lower.includes('problem') || lower.includes('issue') || lower.includes('concern')) {
    return "I've noted your concern. Let me investigate and provide a detailed analysis.\n\nTo give you the most useful response, could you clarify:\n\n1. Is this related to a specific project or agent?\n2. What's the urgency level - blocking work or preventative?\n3. Any particular constraints I should be aware of?\n\nI'll coordinate with the relevant department heads and report back with findings and recommended actions.";
  }

  if (lower.includes('priorit') || lower.includes('focus') || lower.includes('important')) {
    return "Based on current commitments, deadlines, and resource utilization, here's my recommended priority ordering:\n\n**Immediate (Today):**\n1. Complete Website Redesign deploy\n2. Review and resolve Security gate\n\n**This Week:**\n3. Finish API Integration\n4. Continue Mobile App development\n\n**Next Week:**\n5. Resume Data Pipeline once data ready\n6. Begin Security Audit proper\n\nWould you like me to reallocate any agents to shift these priorities? I can pull resources from lower-priority work if needed.";
  }

  if (lower.includes('meeting') || lower.includes('schedule') || lower.includes('sync')) {
    return "I can facilitate coordination across the organization. Options:\n\n**1. Department Sync**\nI'll gather status from all department heads and compile a unified report.\n\n**2. Project Deep-Dive**\nPick a project and I'll pull together all relevant agents for a focused discussion.\n\n**3. Strategic Planning**\nI'll prepare analysis and options for strategic decisions you're considering.\n\nWhich would be most valuable right now? Or if you have something else in mind, just let me know and I'll make it happen.";
  }

  return "Understood. I've processed your input and am considering the implications across our current workstreams.\n\nBased on what you've shared:\n- I'll coordinate with relevant department heads\n- Monitor for any cascading effects\n- Report back with any concerns or required decisions\n\nIs there a specific aspect you'd like me to focus on, or any constraints I should keep in mind?";
}
