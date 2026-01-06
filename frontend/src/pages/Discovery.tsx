import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Paperclip, ArrowLeft, HelpCircle, Check, Circle, FileText, Target, CheckSquare, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { GlassCard, Button, Badge } from '../components/ui';

interface Message {
  id: string;
  role: 'coo' | 'user' | 'system';
  content: string;
  timestamp: string;
  quickActions?: string[];
}

interface ContractItem {
  text: string;
  checked: boolean;
}

interface Contract {
  objective: string;
  successCriteria: ContractItem[];
  inScope: string[];
  outOfScope: string[];
  constraints: string[];
  confidence: number;
}

const initialMessages: Message[] = [
  {
    id: '1',
    role: 'coo',
    content: "Hello! I'm the COO and I'll help you define this project clearly before we start building.\n\nWhat would you like the corporation to work on today?",
    timestamp: '2:30 PM',
  },
];

const mockConversation: Message[] = [
  {
    id: '2',
    role: 'user',
    content: 'Build a user authentication system for our web app. Users should be able to register, log in, and reset passwords.',
    timestamp: '2:32 PM',
  },
  {
    id: '3',
    role: 'coo',
    content: "Great, an auth system. Let me ask a few clarifying questions:\n\n1. **Users**: Public users or internal team only?\n\n2. **Security**: Do you need two-factor authentication (2FA)?\n\n3. **Integration**: Any existing auth systems or databases to connect?",
    timestamp: '2:33 PM',
    quickActions: ['Public users', 'Internal only', 'Both'],
  },
  {
    id: '4',
    role: 'user',
    content: "Public users. 2FA would be nice to have but not required for v1. No existing systems, this is a new project.",
    timestamp: '2:35 PM',
  },
  {
    id: '5',
    role: 'coo',
    content: "Perfect. Based on your requirements, I'm proposing the following phases:\n\n**Phase 1: Core Auth (3-5 days)**\n- Registration form with email verification\n- Login with session management\n- Password reset flow\n\n**Phase 2: Enhancement (2-3 days)**\n- Remember me functionality\n- Account lockout after failed attempts\n- Optional 2FA\n\nDoes this breakdown look right?",
    timestamp: '2:36 PM',
    quickActions: ['Looks good', 'Modify phases', 'I have questions'],
  },
  {
    id: '6',
    role: 'system',
    content: 'Contract Updated - Added social login (Google, GitHub) to Phase 2 scope',
    timestamp: '2:37 PM',
  },
];

const mockContract: Contract = {
  objective: 'Build a user authentication system that allows public users to register, log in, and manage their accounts securely.',
  successCriteria: [
    { text: 'Users can register with email and password', checked: true },
    { text: 'Users can log in and receive a valid session', checked: true },
    { text: 'Users can reset their password via email', checked: true },
    { text: 'Sessions expire after 24 hours of inactivity', checked: true },
    { text: 'Users can enable two-factor authentication', checked: false },
    { text: 'Users can log in with Google or GitHub', checked: false },
  ],
  inScope: [
    'User registration',
    'Login/logout',
    'Password reset',
    'Session management',
  ],
  outOfScope: [
    'Payment processing',
    'User profile management',
    'Admin dashboard',
    'Email notifications',
  ],
  constraints: [
    'Must use bcrypt for password hashing',
    'JWT tokens for sessions',
    'HTTPS required',
  ],
  confidence: 78,
};

export function Discovery() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [contract, setContract] = useState<Contract | null>(null);
  const [showDemo, setShowDemo] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate COO response
    setTimeout(() => {
      setIsTyping(false);
      const cooResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'coo',
        content: "I understand. Let me analyze your requirements and update the contract accordingly.\n\nCould you tell me more about the technical constraints? What stack are you using?",
        timestamp: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        quickActions: ['React + Node.js', 'Python + Django', 'Other'],
      };
      setMessages((prev) => [...prev, cooResponse]);

      // Start showing contract after first exchange
      if (!contract) {
        setContract({
          objective: input.slice(0, 100) + (input.length > 100 ? '...' : ''),
          successCriteria: [],
          inScope: [],
          outOfScope: [],
          constraints: [],
          confidence: 25,
        });
      }
    }, 1500);
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    setTimeout(() => handleSend(), 100);
  };

  const loadDemo = () => {
    setShowDemo(true);
    setMessages(initialMessages);

    // Progressively add messages
    mockConversation.forEach((msg, index) => {
      setTimeout(() => {
        setMessages((prev) => [...prev, msg]);
        if (index === mockConversation.length - 1) {
          setContract(mockContract);
        } else if (index >= 1) {
          // Gradually build contract
          setContract({
            ...mockContract,
            confidence: 25 + (index * 15),
            successCriteria: mockContract.successCriteria.slice(0, index),
          });
        }
      }, (index + 1) * 1000);
    });
  };

  return (
    <div className="flex flex-col h-full -m-6">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--glass-border)]">
        <div className="flex items-center gap-4">
          <Link to="/" className="p-2 hover:bg-[var(--glass-bg)] rounded-[var(--radius-sm)] transition-colors">
            <ArrowLeft className="w-5 h-5 text-[var(--color-muted)]" />
          </Link>
          <div>
            <h2 className="text-lg font-semibold text-[var(--color-plasma)]">
              New Project
            </h2>
            <p className="text-xs text-[var(--color-muted)]">
              Discovery conversation with COO
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!showDemo && (
            <Button variant="ghost" size="sm" onClick={loadDemo}>
              Load Demo
            </Button>
          )}
          <button className="p-2 hover:bg-[var(--glass-bg)] rounded-[var(--radius-sm)] transition-colors">
            <HelpCircle className="w-5 h-5 text-[var(--color-muted)]" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <AnimatePresence mode="popLayout">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onQuickAction={handleQuickAction}
                />
              ))}
            </AnimatePresence>

            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-[var(--color-neural)] flex items-center justify-center text-white text-xs font-medium">
                  COO
                </div>
                <div className="px-4 py-3 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)]">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-[var(--color-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-[var(--color-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-[var(--color-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-[var(--glass-border)]">
            <div className="flex items-end gap-3">
              <button className="p-2 hover:bg-[var(--glass-bg)] rounded-[var(--radius-sm)] transition-colors text-[var(--color-muted)] hover:text-[var(--color-plasma)]">
                <Paperclip className="w-5 h-5" />
              </button>
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Describe what you want to build..."
                  className="w-full px-4 py-3 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none focus:border-[var(--color-neural)] transition-colors resize-none"
                  rows={1}
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
          </div>
        </div>

        {/* Contract Panel */}
        <AnimatePresence>
          {contract && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 384 }}
              exit={{ opacity: 0, width: 0 }}
              className="border-l border-[var(--glass-border)] overflow-hidden"
            >
              <ContractPanel contract={contract} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--glass-border)]">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="md">
            Cancel
          </Button>
          <Button variant="secondary" size="md">
            Save Draft
          </Button>
        </div>
        <Button
          variant="primary"
          size="md"
          disabled={!contract || contract.confidence < 70}
        >
          Finalize Contract
        </Button>
      </div>
    </div>
  );
}

function MessageBubble({ message, onQuickAction }: { message: Message; onQuickAction: (action: string) => void }) {
  if (message.role === 'system') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="flex justify-center"
      >
        <div className="px-4 py-2 rounded-full bg-[var(--glass-bg)] border border-[var(--glass-border)] text-xs text-[var(--color-muted)] flex items-center gap-2">
          <FileText className="w-3 h-3" />
          {message.content}
        </div>
      </motion.div>
    );
  }

  const isCOO = message.role === 'coo';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`flex items-start gap-3 ${isCOO ? '' : 'flex-row-reverse'}`}
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-medium flex-shrink-0 ${
        isCOO ? 'bg-[var(--color-neural)]' : 'bg-[var(--color-synapse)]'
      }`}>
        {isCOO ? 'COO' : 'You'}
      </div>
      <div className={`max-w-[70%] ${isCOO ? '' : 'text-right'}`}>
        <div className={`px-4 py-3 rounded-[var(--radius-md)] ${
          isCOO
            ? 'bg-[var(--glass-bg)] border border-[var(--glass-border)]'
            : 'bg-[var(--color-neural)] text-white'
        }`}>
          <p className={`text-sm whitespace-pre-wrap ${isCOO ? 'text-[var(--color-plasma)]' : ''}`}>
            {message.content}
          </p>
        </div>
        <span className="text-xs text-[var(--color-muted)] mt-1 inline-block">
          {message.timestamp}
        </span>

        {/* Quick Actions */}
        {isCOO && message.quickActions && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.quickActions.map((action) => (
              <button
                key={action}
                onClick={() => onQuickAction(action)}
                className="px-3 py-1.5 text-xs rounded-full bg-[var(--glass-bg)] border border-[var(--glass-border)] text-[var(--color-plasma)] hover:border-[var(--color-neural)] transition-colors"
              >
                {action}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function ContractPanel({ contract }: { contract: Contract }) {
  return (
    <div className="h-full overflow-y-auto p-6 w-96">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-[var(--color-plasma)]">
            Live Extraction
          </h3>
          <Badge
            status={contract.confidence >= 70 ? 'ok' : contract.confidence >= 40 ? 'warning' : 'idle'}
            size="sm"
          />
        </div>

        {/* Confidence */}
        <div>
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-[var(--color-muted)]">Confidence</span>
            <span className="text-[var(--color-plasma)] font-medium">{contract.confidence}%</span>
          </div>
          <div className="h-2 bg-[var(--glass-bg)] rounded-full overflow-hidden">
            <motion.div
              className={`h-full ${
                contract.confidence >= 70 ? 'bg-[var(--color-ok)]' :
                contract.confidence >= 40 ? 'bg-[var(--color-warn)]' :
                'bg-[var(--color-muted)]'
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${contract.confidence}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Objective */}
        <GlassCard padding="md">
          <div className="flex items-start gap-2 mb-2">
            <Target className="w-4 h-4 text-[var(--color-neural)] mt-0.5" />
            <span className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">
              Objective
            </span>
          </div>
          <p className="text-sm text-[var(--color-plasma)]">
            {contract.objective || 'Waiting for project description...'}
          </p>
        </GlassCard>

        {/* Success Criteria */}
        {contract.successCriteria.length > 0 && (
          <GlassCard padding="md">
            <div className="flex items-start gap-2 mb-3">
              <CheckSquare className="w-4 h-4 text-[var(--color-ok)] mt-0.5" />
              <span className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">
                Success Criteria
              </span>
            </div>
            <div className="space-y-2">
              {contract.successCriteria.map((item, index) => (
                <div key={index} className="flex items-start gap-2">
                  {item.checked ? (
                    <Check className="w-4 h-4 text-[var(--color-ok)] mt-0.5" />
                  ) : (
                    <Circle className="w-4 h-4 text-[var(--color-muted)] mt-0.5" />
                  )}
                  <span className={`text-sm ${item.checked ? 'text-[var(--color-plasma)]' : 'text-[var(--color-muted)]'}`}>
                    {item.text}
                  </span>
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Scope */}
        {(contract.inScope.length > 0 || contract.outOfScope.length > 0) && (
          <div className="grid grid-cols-2 gap-3">
            {contract.inScope.length > 0 && (
              <GlassCard padding="sm">
                <p className="text-xs font-medium text-[var(--color-ok)] mb-2">In Scope</p>
                <ul className="space-y-1">
                  {contract.inScope.map((item, index) => (
                    <li key={index} className="text-xs text-[var(--color-plasma)] flex items-start gap-1">
                      <span className="text-[var(--color-ok)]">+</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </GlassCard>
            )}
            {contract.outOfScope.length > 0 && (
              <GlassCard padding="sm">
                <p className="text-xs font-medium text-[var(--color-muted)] mb-2">Out of Scope</p>
                <ul className="space-y-1">
                  {contract.outOfScope.map((item, index) => (
                    <li key={index} className="text-xs text-[var(--color-muted)] flex items-start gap-1">
                      <span>-</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </GlassCard>
            )}
          </div>
        )}

        {/* Constraints */}
        {contract.constraints.length > 0 && (
          <GlassCard padding="md">
            <div className="flex items-start gap-2 mb-3">
              <AlertCircle className="w-4 h-4 text-[var(--color-warn)] mt-0.5" />
              <span className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wide">
                Constraints
              </span>
            </div>
            <ul className="space-y-1">
              {contract.constraints.map((item, index) => (
                <li key={index} className="text-sm text-[var(--color-plasma)]">
                  {item}
                </li>
              ))}
            </ul>
          </GlassCard>
        )}

        {/* Edit Contract Button */}
        <Button variant="secondary" size="md" className="w-full">
          Edit Contract
        </Button>
      </div>
    </div>
  );
}
