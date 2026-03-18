import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, X, MessageSquare, Pause, Play, ChevronDown, ChevronRight, Network, ExternalLink } from 'lucide-react';
import { GlassCard, Button, StatusOrb, Badge } from '../components/ui';
import type { Status } from '../components/ui/StatusOrb';

interface Agent {
  id: string;
  name: string;
  role: string;
  status: Status;
  load: number;
  tasksToday: number;
  currentTask?: string;
  uptime: string;
  children?: Agent[];
}

// Org chart structure - will be populated from API
// For now, showing the base hierarchy without mock agent data
const orgChart: Agent = {
  id: 'ceo',
  name: 'YOU',
  role: 'CEO',
  status: 'ok',
  load: 0,
  tasksToday: 0,
  uptime: '-',
  children: [
    {
      id: 'coo',
      name: 'COO',
      role: 'Chief Operating Officer',
      status: 'idle',
      load: 0,
      tasksToday: 0,
      uptime: '-',
      children: [
        {
          id: 'vp-engineering',
          name: 'VP Engineering',
          role: 'Engineering',
          status: 'idle',
          load: 0,
          tasksToday: 0,
          uptime: '-',
          children: [],
        },
        {
          id: 'vp-research',
          name: 'VP Research',
          role: 'Research',
          status: 'idle',
          load: 0,
          tasksToday: 0,
          uptime: '-',
          children: [],
        },
        {
          id: 'vp-product',
          name: 'VP Product',
          role: 'Product',
          status: 'idle',
          load: 0,
          tasksToday: 0,
          uptime: '-',
          children: [],
        },
        {
          id: 'vp-quality',
          name: 'VP Quality',
          role: 'Quality',
          status: 'idle',
          load: 0,
          tasksToday: 0,
          uptime: '-',
          children: [],
        },
      ],
    },
  ],
};

export function Agents() {
  const navigate = useNavigate();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['ceo', 'coo']));

  const toggleNode = (id: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Count agents by status
  const countByStatus = (node: Agent): Record<Status, number> => {
    const counts: Record<Status, number> = { ok: 0, processing: 0, warning: 0, waiting: 0, idle: 0, off: 0 };
    const traverse = (n: Agent) => {
      if (n.id !== 'ceo') counts[n.status]++;
      n.children?.forEach(traverse);
    };
    traverse(node);
    return counts;
  };

  const statusCounts = countByStatus(orgChart);
  const totalAgents = Object.values(statusCounts).reduce((a, b) => a + b, 0);

  return (
    <div className="flex gap-6 h-full">
      {/* Main Content */}
      <div className="flex-1 space-y-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-[var(--color-plasma)]">
              Agent Network
            </h2>
            <p className="text-sm text-[var(--color-muted)] mt-1">
              {totalAgents} agents across 3 departments
            </p>
          </div>
          <Button variant="secondary" size="md" onClick={() => navigate('/?network=open')}>
            <Network className="w-4 h-4 mr-2" />
            View Visual Network
            <ExternalLink className="w-3 h-3 ml-2 opacity-60" />
          </Button>
        </div>

        {/* Status Summary */}
        <div className="grid grid-cols-5 gap-3">
          <StatusSummaryCard status="ok" count={statusCounts.ok} label="Active" />
          <StatusSummaryCard status="processing" count={statusCounts.processing} label="Processing" />
          <StatusSummaryCard status="warning" count={statusCounts.warning} label="Attention" />
          <StatusSummaryCard status="waiting" count={statusCounts.waiting} label="Waiting" />
          <StatusSummaryCard status="idle" count={statusCounts.idle} label="Idle" />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted)]" />
            <input
              type="text"
              placeholder="Search agents..."
              className="w-full pl-10 pr-4 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none focus:border-[var(--color-neural)] transition-colors"
            />
          </div>
          <Button variant="ghost" size="md">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
        </div>

        {/* Org Chart */}
        <GlassCard variant="elevated" padding="lg">
          <div className="space-y-2">
            <AgentTreeNode
              agent={orgChart}
              level={0}
              expandedNodes={expandedNodes}
              toggleNode={toggleNode}
              selectedAgent={selectedAgent}
              onSelect={setSelectedAgent}
            />
          </div>
        </GlassCard>
      </div>

      {/* Agent Detail Panel */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-96 flex-shrink-0"
          >
            <AgentDetailPanel agent={selectedAgent} onClose={() => setSelectedAgent(null)} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface AgentTreeNodeProps {
  agent: Agent;
  level: number;
  expandedNodes: Set<string>;
  toggleNode: (id: string) => void;
  selectedAgent: Agent | null;
  onSelect: (agent: Agent) => void;
}

function AgentTreeNode({ agent, level, expandedNodes, toggleNode, selectedAgent, onSelect }: AgentTreeNodeProps) {
  const hasChildren = agent.children && agent.children.length > 0;
  const isExpanded = expandedNodes.has(agent.id);
  const isSelected = selectedAgent?.id === agent.id;
  const isCEO = agent.id === 'ceo';

  return (
    <div>
      <motion.div
        onClick={() => !isCEO && onSelect(agent)}
        className={`
          flex items-center gap-3 px-3 py-3 rounded-[var(--radius-md)] cursor-pointer transition-colors
          ${isSelected ? 'bg-[var(--glass-bg-active)] border border-[var(--color-neural)]' : 'hover:bg-[var(--glass-bg)]'}
        `}
        style={{ marginLeft: level * 24 }}
        whileHover={{ x: 2 }}
      >
        {/* Expand/Collapse */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              toggleNode(agent.id);
            }}
            className="p-1 hover:bg-[var(--glass-bg)] rounded"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-[var(--color-muted)]" />
            ) : (
              <ChevronRight className="w-4 h-4 text-[var(--color-muted)]" />
            )}
          </button>
        ) : (
          <div className="w-6" />
        )}

        {/* Status Orb */}
        {isCEO ? (
          <div className="w-8 h-8 rounded-full bg-[var(--color-neural)] flex items-center justify-center text-white text-xs font-medium">
            You
          </div>
        ) : (
          <StatusOrb status={agent.status} size="md" />
        )}

        {/* Name and Role */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-[var(--color-plasma)]">{agent.name}</span>
            <Badge status={agent.status} size="sm" />
          </div>
          <span className="text-xs text-[var(--color-muted)]">{agent.role}</span>
        </div>

        {/* Stats */}
        {!isCEO && (
          <div className="flex items-center gap-4 text-xs text-[var(--color-muted)]">
            <span>{agent.tasksToday} tasks</span>
            <div className="w-16">
              <div className="flex items-center justify-between mb-1">
                <span>Load</span>
                <span className="text-[var(--color-plasma)]">{agent.load}%</span>
              </div>
              <div className="h-1 bg-[var(--glass-bg)] rounded-full overflow-hidden">
                <div
                  className={`h-full ${agent.load > 80 ? 'bg-[var(--color-warn)]' : 'bg-[var(--color-ok)]'}`}
                  style={{ width: `${agent.load}%` }}
                />
              </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          {agent.children!.map((child) => (
            <AgentTreeNode
              key={child.id}
              agent={child}
              level={level + 1}
              expandedNodes={expandedNodes}
              toggleNode={toggleNode}
              selectedAgent={selectedAgent}
              onSelect={onSelect}
            />
          ))}
        </motion.div>
      )}
    </div>
  );
}

function AgentDetailPanel({ agent, onClose }: { agent: Agent; onClose: () => void }) {
  const statusColor = agent.status === 'warning'
    ? 'text-[var(--color-warn)]'
    : agent.status === 'processing'
    ? 'text-[var(--color-proc)]'
    : 'text-[var(--color-ok)]';

  return (
    <GlassCard variant="elevated" padding="md" className="h-full">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <StatusOrb status={agent.status} size="lg" />
            <div>
              <h3 className="font-semibold text-[var(--color-plasma)]">{agent.name}</h3>
              <p className="text-sm text-[var(--color-muted)]">{agent.role}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[var(--glass-bg)] rounded"
          >
            <X className="w-5 h-5 text-[var(--color-muted)]" />
          </button>
        </div>

        {/* Status */}
        <div className="flex items-center gap-2 mb-6">
          <Badge status={agent.status} />
          <span className={`text-sm ${statusColor}`}>
            {agent.status === 'processing' ? 'Processing' :
             agent.status === 'warning' ? 'Needs Attention' :
             agent.status === 'waiting' ? 'Waiting' :
             agent.status === 'idle' ? 'Idle' : 'Active'}
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
            <p className="text-xs text-[var(--color-muted)] mb-1">Load</p>
            <p className="text-xl font-semibold text-[var(--color-plasma)]">{agent.load}%</p>
          </div>
          <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
            <p className="text-xs text-[var(--color-muted)] mb-1">Tasks Today</p>
            <p className="text-xl font-semibold text-[var(--color-plasma)]">{agent.tasksToday}</p>
          </div>
          <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
            <p className="text-xs text-[var(--color-muted)] mb-1">Uptime</p>
            <p className="text-xl font-semibold text-[var(--color-plasma)]">{agent.uptime}</p>
          </div>
          <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
            <p className="text-xs text-[var(--color-muted)] mb-1">Reports To</p>
            <p className="text-sm font-medium text-[var(--color-plasma)]">COO</p>
          </div>
        </div>

        {/* Current Task */}
        {agent.currentTask && (
          <div className="mb-6">
            <p className="text-xs text-[var(--color-muted)] mb-2">Current Task</p>
            <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
              <p className="text-sm text-[var(--color-plasma)]">{agent.currentTask}</p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mt-auto pt-4 border-t border-[var(--glass-border)]">
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" className="flex-1">
              <MessageSquare className="w-4 h-4 mr-1" />
              Message
            </Button>
            <Button variant="ghost" size="sm" className="flex-1">
              {agent.status === 'idle' ? (
                <>
                  <Play className="w-4 h-4 mr-1" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="w-4 h-4 mr-1" />
                  Pause
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}

/* Status Summary Card */
function StatusSummaryCard({ status, count, label }: { status: Status; count: number; label: string }) {
  const bgClass = status === 'ok' ? 'bg-[var(--color-ok)]/10'
    : status === 'processing' ? 'bg-[var(--color-proc)]/10'
    : status === 'warning' ? 'bg-[var(--color-warn)]/10'
    : status === 'waiting' ? 'bg-[var(--color-wait)]/10'
    : 'bg-[var(--glass-bg)]';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-3 rounded-[var(--radius-md)] ${bgClass}`}
    >
      <div className="flex items-center gap-2 mb-1">
        <StatusOrb status={status} size="sm" pulse={count > 0} />
        <span className="text-xs text-[var(--color-muted)]">{label}</span>
      </div>
      <p className="text-2xl font-semibold text-[var(--color-plasma)]">{count}</p>
    </motion.div>
  );
}
