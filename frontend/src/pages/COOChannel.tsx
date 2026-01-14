import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Paperclip, Bot, User, Clock, ChevronDown, Plus, Search, X, Image as ImageIcon, Terminal as TerminalIcon } from 'lucide-react';
import { GlassCard, Button, StatusOrb } from '../components/ui';
import { api } from '../api/client';
import type { ImageAttachment } from '../api/client';
import Terminal from '../components/Terminal';

interface Message {
  id: string;
  role: 'user' | 'coo';
  content: string;
  timestamp: Date;
  images?: ImageAttachment[];  // Attached images
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

// Initial welcome message shown when starting a new conversation
const welcomeMessage: Message = {
  id: 'welcome',
  role: 'coo',
  content: "Good morning. I'm your Chief Operating Officer. I'm here to help you manage and coordinate AI Corp.\n\n**I can help you with:**\n• Status updates on projects and agents\n• Brainstorming and refining ideas\n• Creating new projects through discovery\n• Approving or reviewing gates\n• Strategic planning and prioritization\n\nWhat would you like to discuss?",
  timestamp: new Date(),
};

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

const THREAD_STORAGE_KEY = 'ai-corp-coo-thread-id';

export function COOChannel() {
  const [messages, setMessages] = useState<Message[]>([welcomeMessage]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showThreads, setShowThreads] = useState(false);
  const [threadId, setThreadId] = useState<string | undefined>(undefined);
  const [, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [attachedImages, setAttachedImages] = useState<ImageAttachment[]>([]);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check API health and restore session on mount
  useEffect(() => {
    const initializeSession = async () => {
      try {
        await api.healthCheck();
        setIsConnected(true);

        // Try to restore previous thread
        const savedThreadId = localStorage.getItem(THREAD_STORAGE_KEY);
        if (savedThreadId) {
          setIsLoadingHistory(true);
          try {
            const thread = await api.getCOOThread(savedThreadId);
            if (thread && thread.messages && thread.messages.length > 0) {
              // Restore messages from thread
              const restoredMessages: Message[] = thread.messages.map((msg: any, idx: number) => ({
                id: msg.id || `restored-${idx}`,
                role: msg.role === 'user' ? 'user' : 'coo',
                content: msg.content,
                timestamp: new Date(msg.timestamp),
              }));
              setMessages([welcomeMessage, ...restoredMessages]);
              setThreadId(savedThreadId);
            }
          } catch (err) {
            // Thread not found or error - start fresh
            console.log('Could not restore thread, starting fresh');
            localStorage.removeItem(THREAD_STORAGE_KEY);
          } finally {
            setIsLoadingHistory(false);
          }
        }
      } catch {
        setIsConnected(false);
      }
    };

    initializeSession();
  }, []);

  const handleSend = async () => {
    if (!input.trim() && attachedImages.length === 0) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim() || (attachedImages.length > 0 ? '[Image]' : ''),
      timestamp: new Date(),
      images: attachedImages.length > 0 ? [...attachedImages] : undefined,
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageText = input.trim();
    const imagesToSend = [...attachedImages];
    setInput('');
    setAttachedImages([]);  // Clear attached images after sending
    setIsTyping(true);
    setError(null);

    try {
      // Call real API with images
      console.log('[COOChannel] Sending message with', imagesToSend.length, 'images');
      const response = await api.sendCOOMessage(messageText, threadId, undefined, imagesToSend);

      // Save thread ID for conversation continuity
      if (response.thread_id) {
        setThreadId(response.thread_id);
        localStorage.setItem(THREAD_STORAGE_KEY, response.thread_id);
      }

      const cooResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'coo',
        content: response.response,
        timestamp: new Date(response.timestamp),
      };
      setMessages((prev) => [...prev, cooResponse]);
      setIsConnected(true);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError(err instanceof Error ? err.message : 'Failed to communicate with COO');
      setIsConnected(false);

      // Add error message to chat
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'coo',
        content: `I'm having trouble connecting to the system. Please check that the API server is running.\n\nError: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewThread = () => {
    // Clear current session and start fresh
    setMessages([welcomeMessage]);
    setThreadId(undefined);
    localStorage.removeItem(THREAD_STORAGE_KEY);
    setAttachedImages([]);
    setError(null);
  };

  // Handle image paste from clipboard
  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    console.log('[COOChannel] Paste event - items:', items?.length, 'types:', items ? Array.from(items).map(i => i.type) : []);
    if (!items) return;

    for (const item of items) {
      console.log('[COOChannel] Checking item:', item.type, item.kind);
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        console.log('[COOChannel] Got image file:', file?.name, file?.size, 'bytes');
        if (file) {
          processImageFile(file);
        }
        break;
      }
    }
  }, []);

  // Process an image file into base64
  const processImageFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1]; // Remove data:image/xxx;base64, prefix
      const mediaType = file.type || 'image/png';
      console.log('[COOChannel] Image processed - size:', base64.length, 'chars, type:', mediaType);
      setAttachedImages((prev) => {
        console.log('[COOChannel] Attaching image, total will be:', prev.length + 1);
        return [...prev, { data: base64, media_type: mediaType }];
      });
    };
    reader.readAsDataURL(file);
  };

  // Handle file upload via button
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    for (const file of files) {
      if (file.type.startsWith('image/')) {
        processImageFile(file);
      }
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  // Remove an attached image
  const removeImage = (index: number) => {
    setAttachedImages((prev) => prev.filter((_, i) => i !== index));
  };

  // Memoize image data URLs to avoid recreating large strings on every keystroke
  const imageDataUrls = useMemo(() =>
    attachedImages.map(img => `data:${img.media_type};base64,${img.data}`),
    [attachedImages]
  );

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
                <p className={`text-xs flex items-center gap-1 ${isConnected ? 'text-[var(--color-ok)]' : 'text-[var(--color-warn)]'}`}>
                  <StatusOrb status={isConnected ? 'ok' : 'warning'} size="sm" />
                  {isConnected ? 'Online • Strategic oversight active' : 'Offline • API server not connected'}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm">
              <Clock className="w-4 h-4 mr-2" />
              View History
            </Button>
            <Button
              variant={isTerminalOpen ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setIsTerminalOpen(!isTerminalOpen)}
              title="Open live terminal for COO execution"
            >
              <TerminalIcon className="w-4 h-4 mr-2" />
              Terminal
            </Button>
            <Button variant="secondary" size="sm" onClick={handleNewThread}>
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
            <span className="text-xs text-[var(--color-muted)]">
              {isLoadingHistory ? 'Restoring conversation...' : 'Today'}
            </span>
            <div className="flex-1 h-px bg-[var(--glass-border)]" />
          </div>

          {isLoadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center gap-2 text-[var(--color-muted)]">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-5 h-5 border-2 border-[var(--color-neural)] border-t-transparent rounded-full"
                />
                <span className="text-sm">Loading conversation history...</span>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}

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
          {/* Image Preview Area */}
          {imageDataUrls.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {imageDataUrls.map((dataUrl, idx) => (
                <div key={idx} className="relative group">
                  <img
                    src={dataUrl}
                    alt={`Attachment ${idx + 1}`}
                    className="h-20 w-auto rounded-lg border border-[var(--glass-border)] object-cover"
                  />
                  <button
                    onClick={() => removeImage(idx)}
                    className="absolute -top-2 -right-2 w-5 h-5 bg-[var(--color-warn)] rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3 text-white" />
                  </button>
                </div>
              ))}
            </div>
          )}
          <GlassCard padding="sm">
            <div className="flex items-end gap-3">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept="image/*"
                multiple
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 hover:bg-[var(--glass-bg)] rounded-lg transition-colors text-[var(--color-muted)] hover:text-[var(--color-plasma)]"
                title="Attach image"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              <div className="flex-1">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onPaste={handlePaste}
                  placeholder={attachedImages.length > 0 ? "Add a message with your image(s)..." : "Message the COO... Paste screenshots or type"}
                  rows={1}
                  className="w-full px-0 py-2 bg-transparent text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none resize-none"
                  style={{ minHeight: '24px', maxHeight: '150px' }}
                />
              </div>
              <Button
                variant="primary"
                size="md"
                onClick={handleSend}
                disabled={!input.trim() && attachedImages.length === 0}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </GlassCard>
          <p className="text-xs text-[var(--color-muted)] mt-2 px-2 flex items-center gap-1">
            <ImageIcon className="w-3 h-3" />
            Paste screenshots directly or click the paperclip to attach images
          </p>
        </div>
      </div>

      {/* Live Terminal for COO execution */}
      <Terminal
        isOpen={isTerminalOpen}
        onClose={() => setIsTerminalOpen(false)}
        threadId={threadId}
      />
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
        {/* Display attached images */}
        {message.images && message.images.length > 0 && (
          <div className={`mb-2 flex flex-wrap gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
            {message.images.map((img, idx) => (
              <img
                key={idx}
                src={`data:${img.media_type};base64,${img.data}`}
                alt={`Attachment ${idx + 1}`}
                className="max-h-48 max-w-full rounded-lg border border-[var(--glass-border)] object-contain cursor-pointer hover:opacity-90 transition-opacity"
                onClick={() => {
                  // Open image in new tab for full view
                  const win = window.open();
                  if (win) {
                    win.document.write(`<img src="data:${img.media_type};base64,${img.data}" style="max-width:100%;height:auto;" />`);
                  }
                }}
              />
            ))}
          </div>
        )}
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

// Note: COO responses now come from the real API at /api/coo/message
