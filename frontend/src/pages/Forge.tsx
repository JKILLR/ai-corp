import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lightbulb, Target, Eye, AlertTriangle, Sparkles,
  Clock, CheckCircle, PauseCircle, XCircle,
  ChevronRight, Plus, MessageSquare, Play,
  Brain, Zap, Search
} from 'lucide-react';
import { GlassCard, Button, StatusOrb } from '../components/ui';
import { useNavigate } from 'react-router-dom';

// Types
interface Intention {
  id: string;
  title: string;
  description: string;
  type: 'idea' | 'goal' | 'vision' | 'problem' | 'wish';
  status: 'captured' | 'queued' | 'incubating' | 'ready' | 'approved' | 'on_hold' | 'discarded';
  priority: number;
  source: string;
  capturedAt: Date;
  tags: string[];
}

interface WorkspaceEntry {
  id: string;
  agentId: string;
  agentRole: string;
  type: 'finding' | 'insight' | 'concern' | 'question' | 'connection' | 'synthesis';
  content: string;
  timestamp: Date;
}

interface ForgeSession {
  id: string;
  intentionTitle: string;
  phase: 'researching' | 'exploring' | 'synthesizing' | 'finalizing';
  agents: { id: string; role: string; status: string }[];
  workspaceEntries: WorkspaceEntry[];
  startedAt: Date;
}

// Mock data
const mockIntentions: Intention[] = [
  {
    id: 'int-001',
    title: 'Add voice control to the dashboard',
    description: 'Users should be able to navigate and control the dashboard using voice commands. Think "Hey AI Corp, show me project status"',
    type: 'idea',
    status: 'captured',
    priority: 3,
    source: 'ceo',
    capturedAt: new Date(Date.now() - 1000 * 60 * 30),
    tags: ['ux', 'accessibility']
  },
  {
    id: 'int-002',
    title: 'Reduce customer churn by 20%',
    description: 'Our monthly churn is currently at 8%. We need strategies and features that can bring this down to 6.4% or lower.',
    type: 'goal',
    status: 'queued',
    priority: 1,
    source: 'ceo',
    capturedAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
    tags: ['growth', 'retention']
  },
  {
    id: 'int-003',
    title: 'Become the default tool for AI agent orchestration',
    description: 'In 2 years, when someone thinks about orchestrating AI agents, AI Corp should be the first name that comes to mind.',
    type: 'vision',
    status: 'incubating',
    priority: 2,
    source: 'ceo',
    capturedAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
    tags: ['strategy', 'market']
  },
  {
    id: 'int-004',
    title: 'Users abandoning during onboarding',
    description: 'Analytics show 40% of users drop off during the onboarding flow. We need to understand why and fix it.',
    type: 'problem',
    status: 'ready',
    priority: 1,
    source: 'coo_insight',
    capturedAt: new Date(Date.now() - 1000 * 60 * 60 * 48),
    tags: ['onboarding', 'ux']
  },
  {
    id: 'int-005',
    title: 'Make the agent interactions feel magical',
    description: 'When users watch agents work, it should feel like watching something intelligent and alive, not mechanical.',
    type: 'wish',
    status: 'on_hold',
    priority: 4,
    source: 'ceo',
    capturedAt: new Date(Date.now() - 1000 * 60 * 60 * 72),
    tags: ['ux', 'design']
  }
];

const mockActiveSession: ForgeSession = {
  id: 'forge-abc123',
  intentionTitle: 'Become the default tool for AI agent orchestration',
  phase: 'exploring',
  agents: [
    { id: 'research-001', role: 'Explorer', status: 'active' },
    { id: 'product-001', role: 'Vision Architect', status: 'active' },
    { id: 'research-002', role: 'Trend Analyst', status: 'thinking' }
  ],
  workspaceEntries: [
    {
      id: 'ws-001',
      agentId: 'research-001',
      agentRole: 'Explorer',
      type: 'finding',
      content: 'Current market leaders: LangChain (dev-focused), AutoGPT (consumer), CrewAI (emerging). Gap exists for enterprise orchestration with human oversight.',
      timestamp: new Date(Date.now() - 1000 * 60 * 15)
    },
    {
      id: 'ws-002',
      agentId: 'product-001',
      agentRole: 'Vision Architect',
      type: 'insight',
      content: 'Key differentiator potential: "Human-in-the-loop" is seen as a limitation by competitors, but enterprises see it as a requirement. We should position oversight as a feature, not a bug.',
      timestamp: new Date(Date.now() - 1000 * 60 * 12)
    },
    {
      id: 'ws-003',
      agentId: 'research-002',
      agentRole: 'Trend Analyst',
      type: 'finding',
      content: 'Enterprise AI adoption growing 40% YoY. 73% cite "lack of control/visibility" as primary concern with autonomous agents. This aligns with our COO/CEO model.',
      timestamp: new Date(Date.now() - 1000 * 60 * 8)
    },
    {
      id: 'ws-004',
      agentId: 'research-001',
      agentRole: 'Explorer',
      type: 'connection',
      content: 'Connecting market gap (enterprise orchestration) + differentiator (human oversight) + trend (control concerns) = Position as "Enterprise AI Orchestration with Built-in Governance"',
      timestamp: new Date(Date.now() - 1000 * 60 * 5)
    },
    {
      id: 'ws-005',
      agentId: 'product-001',
      agentRole: 'Vision Architect',
      type: 'synthesis',
      content: 'EMERGING THESIS: To become default, focus on enterprise segment first. Key pillars: 1) Visibility (see what agents do), 2) Control (gates, approvals), 3) Auditability (bead ledger). Marketing angle: "The orchestration platform your compliance team will love."',
      timestamp: new Date(Date.now() - 1000 * 60 * 2)
    }
  ],
  startedAt: new Date(Date.now() - 1000 * 60 * 20)
};

// Helper functions
const getTypeIcon = (type: Intention['type']) => {
  switch (type) {
    case 'idea': return Lightbulb;
    case 'goal': return Target;
    case 'vision': return Eye;
    case 'problem': return AlertTriangle;
    case 'wish': return Sparkles;
  }
};

const getTypeColor = (type: Intention['type']) => {
  switch (type) {
    case 'idea': return 'text-yellow-400';
    case 'goal': return 'text-green-400';
    case 'vision': return 'text-purple-400';
    case 'problem': return 'text-red-400';
    case 'wish': return 'text-pink-400';
  }
};

const getStatusIcon = (status: Intention['status']) => {
  switch (status) {
    case 'captured': return Clock;
    case 'queued': return Clock;
    case 'incubating': return Brain;
    case 'ready': return CheckCircle;
    case 'approved': return CheckCircle;
    case 'on_hold': return PauseCircle;
    case 'discarded': return XCircle;
  }
};

const getStatusColor = (status: Intention['status']) => {
  switch (status) {
    case 'captured': return 'text-gray-400';
    case 'queued': return 'text-blue-400';
    case 'incubating': return 'text-purple-400';
    case 'ready': return 'text-green-400';
    case 'approved': return 'text-green-500';
    case 'on_hold': return 'text-yellow-400';
    case 'discarded': return 'text-gray-500';
  }
};

const getEntryTypeStyle = (type: WorkspaceEntry['type']) => {
  switch (type) {
    case 'finding': return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', icon: Search };
    case 'insight': return { bg: 'bg-purple-500/10', border: 'border-purple-500/30', icon: Lightbulb };
    case 'concern': return { bg: 'bg-red-500/10', border: 'border-red-500/30', icon: AlertTriangle };
    case 'question': return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', icon: MessageSquare };
    case 'connection': return { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', icon: Zap };
    case 'synthesis': return { bg: 'bg-green-500/10', border: 'border-green-500/30', icon: Brain };
  }
};

const formatTimeAgo = (date: Date) => {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
};

// Components
function IntentionCard({ intention, onClick }: { intention: Intention; onClick: () => void }) {
  const TypeIcon = getTypeIcon(intention.type);
  const StatusIcon = getStatusIcon(intention.status);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-3 cursor-pointer hover:bg-white/5 transition-colors"
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg bg-white/5 ${getTypeColor(intention.type)}`}>
          <TypeIcon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-medium text-white truncate">{intention.title}</h4>
            {intention.priority <= 2 && (
              <span className="px-1.5 py-0.5 text-[10px] bg-red-500/20 text-red-400 rounded">
                P{intention.priority}
              </span>
            )}
          </div>
          <p className="text-xs text-white/50 mt-1 line-clamp-2">{intention.description}</p>
          <div className="flex items-center gap-3 mt-2">
            <span className={`flex items-center gap-1 text-xs ${getStatusColor(intention.status)}`}>
              <StatusIcon className="w-3 h-3" />
              {intention.status}
            </span>
            <span className="text-xs text-white/30">{formatTimeAgo(intention.capturedAt)}</span>
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-white/30 flex-shrink-0" />
      </div>
    </motion.div>
  );
}

function WorkspaceEntryCard({ entry }: { entry: WorkspaceEntry }) {
  const style = getEntryTypeStyle(entry.type);
  const Icon = style.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`p-3 rounded-lg border ${style.bg} ${style.border}`}
    >
      <div className="flex items-start gap-2">
        <Icon className="w-4 h-4 text-white/60 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-white/80">{entry.agentRole}</span>
            <span className="text-[10px] text-white/40 uppercase">{entry.type}</span>
            <span className="text-[10px] text-white/30 ml-auto">{formatTimeAgo(entry.timestamp)}</span>
          </div>
          <p className="text-sm text-white/70 leading-relaxed">{entry.content}</p>
        </div>
      </div>
    </motion.div>
  );
}

function AgentStatusBadge({ agent }: { agent: ForgeSession['agents'][0] }) {
  const isActive = agent.status === 'active';
  const isThinking = agent.status === 'thinking';

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
      <div className="relative">
        <StatusOrb status={isActive ? 'ok' : 'warning'} size="sm" />
        {isThinking && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-purple-400"
            animate={{ scale: [1, 1.5, 1], opacity: [1, 0, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
      </div>
      <span className="text-xs text-white/70">{agent.role}</span>
      {isThinking && (
        <motion.span
          className="text-[10px] text-purple-400"
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          thinking...
        </motion.span>
      )}
    </div>
  );
}

export function Forge() {
  const navigate = useNavigate();
  const [selectedIntention, setSelectedIntention] = useState<Intention | null>(null);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [quickAddTitle, setQuickAddTitle] = useState('');
  const [filter, setFilter] = useState<'all' | 'inbox' | 'queue' | 'ready' | 'hold'>('all');

  const inbox = mockIntentions.filter(i => i.status === 'captured');
  const queue = mockIntentions.filter(i => i.status === 'queued');
  const incubating = mockIntentions.filter(i => i.status === 'incubating');
  const ready = mockIntentions.filter(i => i.status === 'ready');
  const onHold = mockIntentions.filter(i => i.status === 'on_hold');

  const filteredIntentions = filter === 'all' ? mockIntentions :
    filter === 'inbox' ? inbox :
    filter === 'queue' ? queue :
    filter === 'ready' ? ready :
    onHold;

  const handleQuickAdd = () => {
    if (quickAddTitle.trim()) {
      // Would call API to capture intention
      console.log('Capturing:', quickAddTitle);
      setQuickAddTitle('');
      setQuickAddOpen(false);
    }
  };

  const handleDiscuss = (intention: Intention) => {
    // Navigate to COO channel with context
    navigate('/coo', { state: { discussIntention: intention.id } });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">The Forge</h1>
          <p className="text-white/50 text-sm mt-1">Transform intentions into actionable plans</p>
        </div>
        <Button
          variant="primary"
          onClick={() => setQuickAddOpen(true)}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Quick Capture
        </Button>
      </div>

      {/* Quick Add Modal */}
      <AnimatePresence>
        {quickAddOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center"
            onClick={() => setQuickAddOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-panel p-6 w-full max-w-lg mx-4"
              onClick={e => e.stopPropagation()}
            >
              <h2 className="text-lg font-medium text-white mb-4">Quick Capture</h2>
              <input
                type="text"
                value={quickAddTitle}
                onChange={e => setQuickAddTitle(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleQuickAdd()}
                placeholder="What's on your mind? (idea, goal, vision, problem...)"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-purple-500/50"
                autoFocus
              />
              <p className="text-xs text-white/40 mt-2">
                Just capture the essence. The COO will triage and expand on it.
              </p>
              <div className="flex justify-end gap-3 mt-4">
                <Button variant="ghost" onClick={() => setQuickAddOpen(false)}>Cancel</Button>
                <Button variant="primary" onClick={handleQuickAdd}>Capture</Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status Overview */}
      <div className="grid grid-cols-5 gap-4">
        {[
          { label: 'Inbox', count: inbox.length, filter: 'inbox' as const, color: 'text-gray-400' },
          { label: 'Queue', count: queue.length, filter: 'queue' as const, color: 'text-blue-400' },
          { label: 'Incubating', count: incubating.length, filter: 'all' as const, color: 'text-purple-400' },
          { label: 'Ready', count: ready.length, filter: 'ready' as const, color: 'text-green-400' },
          { label: 'On Hold', count: onHold.length, filter: 'hold' as const, color: 'text-yellow-400' }
        ].map(stat => (
          <button
            key={stat.label}
            onClick={() => setFilter(stat.filter)}
            className={`glass-panel p-4 text-left transition-all ${filter === stat.filter ? 'ring-1 ring-purple-500/50' : 'hover:bg-white/5'}`}
          >
            <div className={`text-2xl font-bold ${stat.color}`}>{stat.count}</div>
            <div className="text-sm text-white/50">{stat.label}</div>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Panel - Intentions List */}
        <div className="col-span-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-white">
              {filter === 'all' ? 'All Intentions' :
               filter === 'inbox' ? 'Inbox (Awaiting Triage)' :
               filter === 'queue' ? 'Queue (Awaiting Incubation)' :
               filter === 'ready' ? 'Ready for Review' :
               'On Hold'}
            </h2>
            <button
              onClick={() => setFilter('all')}
              className="text-xs text-white/40 hover:text-white/60"
            >
              Show all
            </button>
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
            {filteredIntentions.map(intention => (
              <IntentionCard
                key={intention.id}
                intention={intention}
                onClick={() => setSelectedIntention(intention)}
              />
            ))}
            {filteredIntentions.length === 0 && (
              <div className="text-center py-8 text-white/30">
                No intentions in this category
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Active Incubation / Details */}
        <div className="col-span-8">
          {mockActiveSession ? (
            <GlassCard className="h-full">
              <div className="p-4 border-b border-white/10">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Brain className="w-5 h-5 text-purple-400" />
                      <h2 className="text-lg font-medium text-white">Active Incubation</h2>
                      <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded-full">
                        {mockActiveSession.phase}
                      </span>
                    </div>
                    <p className="text-sm text-white/60 mt-1">{mockActiveSession.intentionTitle}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-white/40">Running for</div>
                    <div className="text-sm text-white/70">{formatTimeAgo(mockActiveSession.startedAt)}</div>
                  </div>
                </div>

                {/* Agent Status */}
                <div className="flex items-center gap-2 mt-4 flex-wrap">
                  <span className="text-xs text-white/40 mr-2">Team:</span>
                  {mockActiveSession.agents.map(agent => (
                    <AgentStatusBadge key={agent.id} agent={agent} />
                  ))}
                </div>
              </div>

              {/* Workspace */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-white/70">Shared Workspace</h3>
                  <span className="text-xs text-white/40">
                    {mockActiveSession.workspaceEntries.length} entries
                  </span>
                </div>
                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                  {mockActiveSession.workspaceEntries.map(entry => (
                    <WorkspaceEntryCard key={entry.id} entry={entry} />
                  ))}
                </div>
              </div>
            </GlassCard>
          ) : selectedIntention ? (
            <GlassCard className="h-full">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3">
                      {(() => {
                        const Icon = getTypeIcon(selectedIntention.type);
                        return <Icon className={`w-6 h-6 ${getTypeColor(selectedIntention.type)}`} />;
                      })()}
                      <div>
                        <h2 className="text-xl font-medium text-white">{selectedIntention.title}</h2>
                        <span className={`text-sm ${getStatusColor(selectedIntention.status)}`}>
                          {selectedIntention.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedIntention.status === 'ready' && (
                      <>
                        <Button variant="ghost" onClick={() => handleDiscuss(selectedIntention)}>
                          <MessageSquare className="w-4 h-4 mr-2" />
                          Discuss
                        </Button>
                        <Button variant="primary">
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Approve
                        </Button>
                      </>
                    )}
                    {selectedIntention.status === 'captured' && (
                      <Button variant="primary">
                        <Play className="w-4 h-4 mr-2" />
                        Triage
                      </Button>
                    )}
                    {selectedIntention.status === 'queued' && (
                      <Button variant="primary">
                        <Brain className="w-4 h-4 mr-2" />
                        Start Incubation
                      </Button>
                    )}
                  </div>
                </div>

                <div className="mt-6">
                  <h3 className="text-sm font-medium text-white/70 mb-2">Description</h3>
                  <p className="text-white/60 leading-relaxed">{selectedIntention.description}</p>
                </div>

                <div className="mt-6 flex items-center gap-4">
                  <div>
                    <span className="text-xs text-white/40">Priority</span>
                    <div className="text-sm text-white/70">P{selectedIntention.priority}</div>
                  </div>
                  <div>
                    <span className="text-xs text-white/40">Source</span>
                    <div className="text-sm text-white/70">{selectedIntention.source}</div>
                  </div>
                  <div>
                    <span className="text-xs text-white/40">Captured</span>
                    <div className="text-sm text-white/70">{formatTimeAgo(selectedIntention.capturedAt)}</div>
                  </div>
                </div>

                {selectedIntention.tags.length > 0 && (
                  <div className="mt-6">
                    <span className="text-xs text-white/40">Tags</span>
                    <div className="flex gap-2 mt-1">
                      {selectedIntention.tags.map(tag => (
                        <span key={tag} className="px-2 py-1 text-xs bg-white/5 text-white/60 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </GlassCard>
          ) : (
            <GlassCard className="h-full flex items-center justify-center">
              <div className="text-center py-12">
                <Brain className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/40">Select an intention to view details</p>
                <p className="text-white/30 text-sm mt-1">or start incubating from the queue</p>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}
