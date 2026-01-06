import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap,
  X,
  ChevronRight,
  ChevronDown,
  Terminal,
  FileCode,
  Search,
  MessageSquare,
  GitBranch,
  Cpu,
  Maximize2,
} from 'lucide-react';
import { GlassCard, Button } from '../components/ui';
import { StatusOrb } from '../components/ui/StatusOrb';
import { Badge } from '../components/ui/Badge';
import type { Status } from '../components/ui/StatusOrb';

// Agent data types
interface Agent {
  id: string;
  name: string;
  role: string;
  status: Status;
  currentTask?: string;
  tasksCompleted: number;
  toolsInUse?: string[];
}

interface Department {
  id: string;
  name: string;
  head: string;
  status: Status;
  agentCount: number;
  activeCount: number;
  agents: Agent[];
}

// Mock department data
const departments: Department[] = [
  {
    id: 'engineering',
    name: 'Engineering',
    head: 'Head of Engineering',
    status: 'ok',
    agentCount: 5,
    activeCount: 4,
    agents: [
      {
        id: 'dev-001',
        name: 'dev-001',
        role: 'Frontend Developer',
        status: 'processing',
        currentTask: 'Implementing user dashboard components',
        tasksCompleted: 12,
        toolsInUse: ['FileEdit', 'Terminal', 'Search'],
      },
      {
        id: 'dev-002',
        name: 'dev-002',
        role: 'Backend Developer',
        status: 'ok',
        currentTask: 'API endpoint optimization',
        tasksCompleted: 8,
        toolsInUse: ['Terminal', 'GitCommit'],
      },
      {
        id: 'dev-003',
        name: 'dev-003',
        role: 'Full Stack Developer',
        status: 'processing',
        currentTask: 'Database migration scripts',
        tasksCompleted: 15,
        toolsInUse: ['FileEdit', 'Terminal'],
      },
      {
        id: 'qa-001',
        name: 'qa-001',
        role: 'QA Engineer',
        status: 'warning',
        currentTask: 'Reviewing security vulnerability',
        tasksCompleted: 6,
        toolsInUse: ['Search', 'FileRead'],
      },
      {
        id: 'devops-001',
        name: 'devops-001',
        role: 'DevOps Engineer',
        status: 'idle',
        tasksCompleted: 4,
      },
    ],
  },
  {
    id: 'design',
    name: 'Design',
    head: 'Head of Design',
    status: 'ok',
    agentCount: 3,
    activeCount: 2,
    agents: [
      {
        id: 'design-001',
        name: 'design-001',
        role: 'UI Designer',
        status: 'processing',
        currentTask: 'Creating component library documentation',
        tasksCompleted: 9,
        toolsInUse: ['FileEdit', 'Search'],
      },
      {
        id: 'design-002',
        name: 'design-002',
        role: 'UX Researcher',
        status: 'ok',
        currentTask: 'User flow analysis complete',
        tasksCompleted: 5,
      },
      {
        id: 'design-003',
        name: 'design-003',
        role: 'Brand Designer',
        status: 'idle',
        tasksCompleted: 3,
      },
    ],
  },
  {
    id: 'research',
    name: 'Research',
    head: 'Head of Research',
    status: 'warning',
    agentCount: 2,
    activeCount: 2,
    agents: [
      {
        id: 'research-001',
        name: 'research-001',
        role: 'Market Analyst',
        status: 'processing',
        currentTask: 'Competitor analysis for Q1 strategy',
        tasksCompleted: 7,
        toolsInUse: ['WebSearch', 'FileEdit'],
      },
      {
        id: 'research-002',
        name: 'research-002',
        role: 'Data Scientist',
        status: 'warning',
        currentTask: 'Awaiting data access approval',
        tasksCompleted: 2,
        toolsInUse: ['Terminal'],
      },
    ],
  },
];

// Tool icon mapping
const toolIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  FileEdit: FileCode,
  FileRead: FileCode,
  Terminal: Terminal,
  Search: Search,
  WebSearch: Search,
  GitCommit: GitBranch,
  Message: MessageSquare,
};

export function Dashboard() {
  const [isNetworkExpanded, setIsNetworkExpanded] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  return (
    <div className="flex gap-6 h-full">
      {/* Main Content */}
      <div className="flex-1 space-y-6 overflow-y-auto">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="ACTIVE" sublabel="agents" value="12" status="ok" />
          <StatCard label="PROCESSING" sublabel="tasks" value="4" status="ok" />
          <StatCard label="QUEUED" sublabel="tasks" value="7" status="ok" />
          <StatCard label="ATTENTION" sublabel="gates" value="2" status="warning" />
        </div>

        {/* Active Workflows */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-[var(--color-synapse)]" />
            <h3 className="text-lg font-medium text-[var(--color-plasma)]">
              Active Workflows
            </h3>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <WorkflowCard
              name="Website Redesign"
              status="ok"
              progress={67}
              agents={3}
              eta="2.3h"
              stage="Design > Dev"
              stages={5}
              currentStage={2}
            />
            <WorkflowCard
              name="API Integration"
              status="ok"
              progress={89}
              agents={1}
              eta="0.5h"
              stage="Testing"
              stages={5}
              currentStage={4}
            />
            <WorkflowCard
              name="Data Pipeline Refactor"
              status="warning"
              progress={45}
              agents={2}
              blocked="Needs approval"
              stage="Awaiting Gate"
              stages={5}
              currentStage={2}
            />
          </div>
        </div>

        {/* Agent Network Preview - Clickable */}
        <GlassCard
          variant="elevated"
          padding="lg"
          className="cursor-pointer hover:border-[var(--color-neural)] transition-colors"
          onClick={() => setIsNetworkExpanded(true)}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <StatusOrb status="processing" size="sm" />
              <h3 className="text-lg font-medium text-[var(--color-plasma)]">
                Agent Network
              </h3>
            </div>
            <div className="flex items-center gap-2 text-[var(--color-muted)]">
              <span className="text-sm">Click to expand</span>
              <Maximize2 className="w-4 h-4" />
            </div>
          </div>

          <div className="flex flex-col items-center py-8">
            {/* CEO Node */}
            <AgentNode label="YOU (CEO)" sublabel="Oversight" status="ok" />

            {/* Connection line */}
            <div className="w-px h-8 bg-[var(--color-synapse)] opacity-50" />

            {/* COO Node */}
            <AgentNode label="COO" sublabel="47 tasks today" status="processing" isMulti />

            {/* Connection lines */}
            <div className="flex items-start justify-center w-full max-w-md mt-2">
              <div className="flex-1 h-8 border-t border-r border-[var(--color-synapse)] opacity-50 rounded-tr-lg" />
              <div className="w-px h-8 bg-[var(--color-synapse)] opacity-50" />
              <div className="flex-1 h-8 border-t border-l border-[var(--color-synapse)] opacity-50 rounded-tl-lg" />
            </div>

            {/* Department Heads */}
            <div className="flex gap-4 mt-2">
              {departments.map((dept) => (
                <AgentNodeSmall key={dept.id} status={dept.status} label={dept.name.slice(0, 3)} />
              ))}
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Neural Activity Sidebar */}
      <div className="w-80 flex-shrink-0">
        <GlassCard variant="elevated" padding="md" className="h-full">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-[var(--color-synapse)]" />
            <h3 className="text-lg font-medium text-[var(--color-plasma)]">
              Neural Activity
            </h3>
          </div>

          <div className="space-y-4">
            <ActivityItem
              status="ok"
              message="design-agent completed component review"
              time="2:34 PM"
            />
            <ActivityItem
              status="processing"
              message="research-agent spawned for market analysis"
              time="2:31 PM"
            />
            <ActivityItem
              status="warning"
              message="qa-agent flagged security concern"
              time="2:28 PM"
            />
            <ActivityItem
              status="ok"
              message="dev-002 pushed to staging"
              time="2:15 PM"
            />
            <ActivityItem
              status="processing"
              message="COO delegated 3 tasks to engineering"
              time="2:10 PM"
            />
          </div>
        </GlassCard>
      </div>

      {/* Expanded Agent Network Modal */}
      <AnimatePresence>
        {isNetworkExpanded && (
          <AgentNetworkModal
            onClose={() => {
              setIsNetworkExpanded(false);
              setSelectedAgent(null);
            }}
            selectedAgent={selectedAgent}
            onSelectAgent={setSelectedAgent}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// Agent Network Modal
interface AgentNetworkModalProps {
  onClose: () => void;
  selectedAgent: Agent | null;
  onSelectAgent: (agent: Agent | null) => void;
}

function AgentNetworkModal({ onClose, selectedAgent, onSelectAgent }: AgentNetworkModalProps) {
  const [expandedDepts, setExpandedDepts] = useState<string[]>(['engineering']);

  const toggleDept = (deptId: string) => {
    setExpandedDepts((prev) =>
      prev.includes(deptId) ? prev.filter((id) => id !== deptId) : [...prev, deptId]
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="w-full max-w-6xl h-[85vh] bg-[var(--color-cosmos)] border border-[var(--glass-border)] rounded-[var(--radius-lg)] overflow-hidden flex"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Main Network View */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--glass-border)]">
            <div className="flex items-center gap-3">
              <StatusOrb status="processing" size="md" />
              <div>
                <h2 className="text-xl font-semibold text-[var(--color-plasma)]">
                  Agent Network
                </h2>
                <p className="text-sm text-[var(--color-muted)]">
                  12 agents active across 3 departments
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-[var(--glass-bg)] rounded-[var(--radius-sm)] transition-colors"
            >
              <X className="w-5 h-5 text-[var(--color-muted)]" />
            </button>
          </div>

          {/* Network Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* CEO & COO */}
            <div className="flex flex-col items-center mb-8">
              <div className="px-8 py-4 rounded-[var(--radius-md)] border-2 border-[var(--color-synapse)] bg-[var(--glass-bg)] text-center">
                <StatusOrb status="ok" size="md" />
                <p className="font-semibold text-[var(--color-plasma)] mt-2">YOU (CEO)</p>
                <p className="text-xs text-[var(--color-muted)]">Strategic Oversight</p>
              </div>

              <div className="w-px h-6 bg-[var(--color-synapse)]" />

              <div className="px-8 py-4 rounded-[var(--radius-md)] border border-[var(--glass-border)] bg-[var(--glass-bg)] text-center">
                <div className="flex justify-center gap-1 mb-2">
                  <StatusOrb status="processing" size="sm" />
                  <StatusOrb status="processing" size="sm" />
                  <StatusOrb status="processing" size="sm" />
                </div>
                <p className="font-semibold text-[var(--color-plasma)]">COO</p>
                <p className="text-xs text-[var(--color-muted)]">47 tasks coordinated today</p>
              </div>

              <div className="w-px h-6 bg-[var(--color-synapse)]" />
            </div>

            {/* Departments */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {departments.map((dept) => (
                <DepartmentBlock
                  key={dept.id}
                  department={dept}
                  isExpanded={expandedDepts.includes(dept.id)}
                  onToggle={() => toggleDept(dept.id)}
                  onSelectAgent={onSelectAgent}
                  selectedAgentId={selectedAgent?.id}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Agent Detail Panel */}
        <AnimatePresence>
          {selectedAgent && (
            <AgentDetailPanel
              agent={selectedAgent}
              onClose={() => onSelectAgent(null)}
            />
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}

// Department Block
interface DepartmentBlockProps {
  department: Department;
  isExpanded: boolean;
  onToggle: () => void;
  onSelectAgent: (agent: Agent) => void;
  selectedAgentId?: string;
}

function DepartmentBlock({
  department,
  isExpanded,
  onToggle,
  onSelectAgent,
  selectedAgentId,
}: DepartmentBlockProps) {
  return (
    <GlassCard variant="elevated" padding="none" className="overflow-hidden">
      {/* Department Header */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-[var(--glass-bg)] transition-colors"
      >
        <div className="flex items-center gap-3">
          <StatusOrb status={department.status} size="sm" />
          <div className="text-left">
            <p className="font-medium text-[var(--color-plasma)]">{department.name}</p>
            <p className="text-xs text-[var(--color-muted)]">
              {department.activeCount}/{department.agentCount} active
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-[var(--color-muted)]" />
        ) : (
          <ChevronRight className="w-4 h-4 text-[var(--color-muted)]" />
        )}
      </button>

      {/* Agents List */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-[var(--glass-border)]"
          >
            <div className="p-2 space-y-1">
              {department.agents.map((agent) => (
                <AgentRow
                  key={agent.id}
                  agent={agent}
                  isSelected={selectedAgentId === agent.id}
                  onClick={() => onSelectAgent(agent)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </GlassCard>
  );
}

// Agent Row in Department
interface AgentRowProps {
  agent: Agent;
  isSelected: boolean;
  onClick: () => void;
}

function AgentRow({ agent, isSelected, onClick }: AgentRowProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full px-3 py-2 rounded-[var(--radius-sm)] flex items-center gap-3 transition-colors ${
        isSelected
          ? 'bg-[var(--color-neural)] bg-opacity-20 border border-[var(--color-neural)]'
          : 'hover:bg-[var(--glass-bg)]'
      }`}
    >
      <StatusOrb status={agent.status} size="sm" pulse={agent.status === 'processing'} />
      <div className="flex-1 text-left min-w-0">
        <p className="text-sm font-medium text-[var(--color-plasma)] truncate">{agent.name}</p>
        <p className="text-xs text-[var(--color-muted)] truncate">{agent.role}</p>
      </div>
      {agent.toolsInUse && agent.toolsInUse.length > 0 && (
        <div className="flex items-center gap-1">
          {agent.toolsInUse.slice(0, 2).map((tool) => {
            const Icon = toolIcons[tool] || Terminal;
            return (
              <div
                key={tool}
                className="w-5 h-5 rounded bg-[var(--glass-bg)] flex items-center justify-center"
                title={tool}
              >
                <Icon className="w-3 h-3 text-[var(--color-synapse)]" />
              </div>
            );
          })}
          {agent.toolsInUse.length > 2 && (
            <span className="text-xs text-[var(--color-muted)]">+{agent.toolsInUse.length - 2}</span>
          )}
        </div>
      )}
    </button>
  );
}

// Agent Detail Panel
interface AgentDetailPanelProps {
  agent: Agent;
  onClose: () => void;
}

function AgentDetailPanel({ agent, onClose }: AgentDetailPanelProps) {
  // Mock inner dialogue/activity
  const activityLog = [
    { time: '2:34:12', type: 'thought', content: 'Analyzing component structure for optimization opportunities...' },
    { time: '2:34:08', type: 'tool', tool: 'FileRead', content: 'Reading src/components/Dashboard.tsx' },
    { time: '2:33:55', type: 'thought', content: 'Need to check existing implementation before making changes.' },
    { time: '2:33:41', type: 'tool', tool: 'Search', content: 'Searching for "StatusOrb" usage patterns' },
    { time: '2:33:30', type: 'thought', content: 'Starting task: Implementing user dashboard components' },
  ];

  return (
    <motion.div
      initial={{ width: 0, opacity: 0 }}
      animate={{ width: 400, opacity: 1 }}
      exit={{ width: 0, opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="border-l border-[var(--glass-border)] bg-[var(--color-cosmos)] overflow-hidden"
    >
      <div className="w-[400px] h-full flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[var(--glass-border)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <StatusOrb status={agent.status} size="md" pulse={agent.status === 'processing'} />
            <div>
              <p className="font-semibold text-[var(--color-plasma)]">{agent.name}</p>
              <p className="text-xs text-[var(--color-muted)]">{agent.role}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-[var(--glass-bg)] rounded-[var(--radius-sm)] transition-colors"
          >
            <X className="w-4 h-4 text-[var(--color-muted)]" />
          </button>
        </div>

        {/* Current Task */}
        {agent.currentTask && (
          <div className="px-4 py-3 border-b border-[var(--glass-border)]">
            <p className="text-xs text-[var(--color-muted)] uppercase tracking-wide mb-1">Current Task</p>
            <p className="text-sm text-[var(--color-plasma)]">{agent.currentTask}</p>
          </div>
        )}

        {/* Stats */}
        <div className="px-4 py-3 border-b border-[var(--glass-border)] grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-lg font-semibold text-[var(--color-synapse)]">{agent.tasksCompleted}</p>
            <p className="text-xs text-[var(--color-muted)]">Tasks Done</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold text-[var(--color-plasma)]">{agent.toolsInUse?.length || 0}</p>
            <p className="text-xs text-[var(--color-muted)]">Active Tools</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold text-[var(--color-ok)]">98%</p>
            <p className="text-xs text-[var(--color-muted)]">Success Rate</p>
          </div>
        </div>

        {/* Tools in Use */}
        {agent.toolsInUse && agent.toolsInUse.length > 0 && (
          <div className="px-4 py-3 border-b border-[var(--glass-border)]">
            <p className="text-xs text-[var(--color-muted)] uppercase tracking-wide mb-2">Tools in Use</p>
            <div className="flex flex-wrap gap-2">
              {agent.toolsInUse.map((tool) => {
                const Icon = toolIcons[tool] || Terminal;
                return (
                  <div
                    key={tool}
                    className="px-2 py-1 rounded-[var(--radius-sm)] bg-[var(--glass-bg)] flex items-center gap-1.5"
                  >
                    <Icon className="w-3.5 h-3.5 text-[var(--color-synapse)]" />
                    <span className="text-xs text-[var(--color-plasma)]">{tool}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Activity / Inner Dialogue */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="px-4 py-2 border-b border-[var(--glass-border)] flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[var(--color-synapse)]" />
            <p className="text-xs text-[var(--color-muted)] uppercase tracking-wide">Live Activity</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {activityLog.map((entry, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex gap-3"
              >
                <div className="flex-shrink-0 flex flex-col items-center">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      entry.type === 'thought'
                        ? 'bg-[var(--color-neural)] bg-opacity-20'
                        : 'bg-[var(--color-synapse)] bg-opacity-20'
                    }`}
                  >
                    {entry.type === 'thought' ? (
                      <MessageSquare className="w-3 h-3 text-[var(--color-neural)]" />
                    ) : (
                      <Terminal className="w-3 h-3 text-[var(--color-synapse)]" />
                    )}
                  </div>
                  {index < activityLog.length - 1 && (
                    <div className="w-px flex-1 bg-[var(--glass-border)] mt-1" />
                  )}
                </div>
                <div className="flex-1 pb-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-[var(--color-muted)]">{entry.time}</span>
                    {entry.type === 'tool' && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--glass-bg)] text-[var(--color-synapse)]">
                        {entry.tool}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-[var(--color-plasma)]">{entry.content}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="px-4 py-3 border-t border-[var(--glass-border)] flex gap-2">
          <Button variant="secondary" size="sm" className="flex-1">
            Pause Agent
          </Button>
          <Button variant="ghost" size="sm" className="flex-1">
            View Full Log
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

interface StatCardProps {
  label: string;
  sublabel: string;
  value: string;
  status: Status;
}

function StatCard({ label, sublabel, value, status }: StatCardProps) {
  const valueColor = status === 'warning'
    ? 'text-[var(--color-warn)]'
    : 'text-[var(--color-synapse)]';

  return (
    <GlassCard variant="interactive" padding="lg">
      <div className="flex flex-col items-center text-center">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm font-medium text-[var(--color-muted)] uppercase tracking-wider">
            {label}
          </span>
          <Badge status={status} size="sm" />
        </div>
        <p className={`text-4xl font-semibold ${valueColor}`}>
          {value}
        </p>
        <p className="text-sm text-[var(--color-muted)] mt-1">{sublabel}</p>
      </div>
    </GlassCard>
  );
}

interface WorkflowCardProps {
  name: string;
  status: Status;
  progress: number;
  agents: number;
  eta?: string;
  blocked?: string;
  stage: string;
  stages: number;
  currentStage: number;
}

function WorkflowCard({
  name,
  status,
  progress,
  agents,
  eta,
  blocked,
  stages,
  currentStage,
}: WorkflowCardProps) {
  const progressColor = status === 'warning'
    ? 'bg-[var(--color-warn)]'
    : 'bg-[var(--color-ok)]';

  return (
    <GlassCard variant="interactive" padding="md">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-[var(--color-plasma)]">{name}</h4>
          <Badge status={status} />
        </div>

        {/* Progress bar */}
        <div className="h-1.5 bg-[var(--glass-bg)] rounded-full overflow-hidden">
          <motion.div
            className={`h-full ${progressColor}`}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>

        {/* Info row */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-[var(--color-muted)]">
            {agents} agent{agents !== 1 ? 's' : ''} active
          </span>
          {blocked ? (
            <span className="text-[var(--color-warn)]">BLOCKED: {blocked}</span>
          ) : (
            <span className="text-[var(--color-muted)]">ETA {eta}</span>
          )}
        </div>

        {/* Pipeline stages */}
        <div className="flex items-center gap-2 pt-2">
          {Array.from({ length: stages }).map((_, i) => (
            <div key={i} className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full ${
                  i < currentStage
                    ? 'bg-[var(--color-ok)]'
                    : i === currentStage
                    ? status === 'warning'
                      ? 'bg-[var(--color-warn)]'
                      : 'bg-[var(--color-synapse)]'
                    : 'bg-[var(--glass-border)]'
                }`}
              />
              {i < stages - 1 && (
                <div
                  className={`w-8 h-0.5 ${
                    i < currentStage
                      ? 'bg-[var(--color-ok)]'
                      : 'bg-[var(--glass-border)]'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </GlassCard>
  );
}

interface AgentNodeProps {
  label: string;
  sublabel: string;
  status: Status;
  isMulti?: boolean;
}

function AgentNode({ label, sublabel, status, isMulti }: AgentNodeProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="px-6 py-4 rounded-[var(--radius-md)] border border-[var(--glass-border)] bg-[var(--glass-bg)] text-center"
    >
      <div className="flex justify-center mb-2">
        {isMulti ? (
          <div className="flex -space-x-1">
            <StatusOrb status={status} size="sm" />
            <StatusOrb status={status} size="sm" />
            <StatusOrb status={status} size="sm" />
          </div>
        ) : (
          <StatusOrb status={status} size="sm" />
        )}
      </div>
      <p className="font-medium text-[var(--color-plasma)]">{label}</p>
      <p className="text-xs text-[var(--color-muted)]">{sublabel}</p>
    </motion.div>
  );
}

function AgentNodeSmall({ status, label }: { status: Status; label?: string }) {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className="w-16 h-12 rounded-[var(--radius-sm)] border border-[var(--glass-border)] bg-[var(--glass-bg)] flex flex-col items-center justify-center gap-1"
    >
      <StatusOrb status={status} size="sm" />
      {label && <span className="text-[8px] text-[var(--color-muted)] uppercase">{label}</span>}
    </motion.div>
  );
}

interface ActivityItemProps {
  status: Status;
  message: string;
  time: string;
}

function ActivityItem({ status, message, time }: ActivityItemProps) {
  return (
    <div className="flex items-start gap-3">
      <StatusOrb status={status} size="sm" pulse={false} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-[var(--color-plasma)]">{message}</p>
        <p className="text-xs text-[var(--color-muted)]">{time}</p>
      </div>
    </div>
  );
}
