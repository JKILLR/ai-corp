import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
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
  AlertCircle,
} from 'lucide-react';
import { GlassCard, Button } from '../components/ui';
import { StatusOrb } from '../components/ui/StatusOrb';
import { Badge } from '../components/ui/Badge';
import type { Status } from '../components/ui/StatusOrb';
import { api, type Project } from '../api/client';

// Map status to glow class
const statusGlowClass: Record<Status, string> = {
  ok: 'glow-ok',
  processing: 'glow-processing',
  warning: 'glow-warning',
  waiting: 'glow-waiting',
  idle: 'glow-idle',
  off: '',
};

const agentGlowClass: Record<Status, string> = {
  ok: 'agent-glow-ok',
  processing: 'agent-glow-processing',
  warning: 'agent-glow-warning',
  waiting: 'agent-glow-waiting',
  idle: 'agent-glow-idle',
  off: '',
};

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

// Empty - no mock data. Will come from API
const departments: Department[] = [];

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

// Default stats when API is unavailable (show zeros, not fake data)
const defaultStats = {
  agentsActive: 0,
  taskProcessing: 0,
  taskQueued: 0,
  gatesPending: 0,
};

// Empty workflows when API is unavailable
const defaultWorkflows: Array<{ name: string; status: Status; progress: number; agents: number; eta?: string; blocked?: string; stages: number; currentStage: number }> = [];

// Empty activity when API is unavailable
const defaultActivity: Array<{ status: Status; message: string; time: string }> = [];

export function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Initialize network expanded state from URL parameter
  const shouldOpenNetwork = searchParams.get('network') === 'open';
  const [isNetworkExpanded, setIsNetworkExpanded] = useState(shouldOpenNetwork);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  // API state
  const [isConnected, setIsConnected] = useState(true);
  const [stats, setStats] = useState(defaultStats);
  const [workflows, setWorkflows] = useState(defaultWorkflows);
  const [activity, setActivity] = useState(defaultActivity);
  const [isLoading, setIsLoading] = useState(true);

  // Clear URL parameter if it was used (only on initial mount)
  useEffect(() => {
    if (shouldOpenNetwork) {
      searchParams.delete('network');
      setSearchParams(searchParams, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Intentionally only run on mount

  // Fetch dashboard data from API
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const data = await api.getDashboard();
        setIsConnected(true);

        // Update stats from API
        setStats({
          agentsActive: data.metrics.agents_active,
          taskProcessing: data.metrics.projects_active,
          taskQueued: data.metrics.queue_depth,
          gatesPending: data.metrics.gates_pending,
        });

        // Convert projects to workflow format
        if (data.projects && data.projects.length > 0) {
          const apiWorkflows = data.projects.map((p: Project) => ({
            name: p.name,
            status: (p.status === 'blocked' ? 'warning' : p.status === 'active' ? 'ok' : 'idle') as Status,
            progress: p.progress,
            agents: p.workers_active || 1,
            eta: p.status === 'active' ? '~' : undefined,
            blocked: p.status === 'blocked' ? 'Needs approval' : undefined,
            stages: p.steps_total || 5,
            currentStage: p.steps_completed || 0,
          }));
          setWorkflows(apiWorkflows);
        }

        // Convert activity
        if (data.activity && data.activity.length > 0) {
          const apiActivity = data.activity.map((a) => ({
            status: 'ok' as Status,
            message: `${a.agent_id}: ${a.message}`,
            time: new Date(a.timestamp).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
          }));
          setActivity(apiActivity);
        }
      } catch (err) {
        console.log('Dashboard API unavailable, using mock data');
        setIsConnected(false);
        // Keep using default mock data
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboard();

    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex gap-6 h-full">
      {/* Main Content */}
      <div className="flex-1 space-y-6 overflow-y-auto">
        {/* Connection status banner */}
        {!isConnected && !isLoading && (
          <div className="flex items-center gap-2 px-4 py-2 bg-[var(--color-warn)] bg-opacity-10 border border-[var(--color-warn)] rounded-lg text-sm text-[var(--color-warn)]">
            <AlertCircle className="w-4 h-4" />
            <span>API server not connected. Showing demo data.</span>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <StatusOrb status="processing" size="lg" />
            <span className="ml-3 text-[var(--color-muted)]">Loading dashboard...</span>
          </div>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="ACTIVE" sublabel="agents" value={String(stats.agentsActive)} status="ok" />
          <StatCard label="PROCESSING" sublabel="tasks" value={String(stats.taskProcessing)} status="ok" />
          <StatCard label="QUEUED" sublabel="tasks" value={String(stats.taskQueued)} status="ok" />
          <StatCard label="ATTENTION" sublabel="gates" value={String(stats.gatesPending)} status={stats.gatesPending > 0 ? "warning" : "ok"} />
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
            {workflows.map((workflow, index) => (
              <WorkflowCard
                key={workflow.name + index}
                name={workflow.name}
                status={workflow.status}
                progress={workflow.progress}
                agents={workflow.agents}
                eta={workflow.eta}
                blocked={workflow.blocked}
                stage={workflow.blocked ? 'Awaiting Gate' : `Stage ${workflow.currentStage + 1}/${workflow.stages}`}
                stages={workflow.stages}
                currentStage={workflow.currentStage}
              />
            ))}
            {workflows.length === 0 && (
              <div className="col-span-2 text-center py-8 text-[var(--color-muted)]">
                No active workflows
              </div>
            )}
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

            {/* Flowing connection to COO */}
            <FlowingConnection height={32} />

            {/* COO Node */}
            <AgentNode label="COO" sublabel="Orchestrating" status="processing" isMulti />

            {/* Branch connections to departments */}
            <PreviewBranchConnector count={departments.length} />

            {/* Department Heads */}
            <div className="flex gap-4">
              {departments.map((dept) => (
                <div
                  key={dept.id}
                  className={`w-16 h-12 rounded-[var(--radius-sm)] border border-[var(--glass-border)] bg-[var(--glass-bg)] flex flex-col items-center justify-center gap-1 ${statusGlowClass[dept.status]}`}
                >
                  <StatusOrb status={dept.status} size="sm" />
                  <span className="text-[8px] text-[var(--color-muted)] uppercase">{dept.name.slice(0, 3)}</span>
                </div>
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
            {activity.map((item, index) => (
              <ActivityItem
                key={index}
                status={item.status}
                message={item.message}
                time={item.time}
              />
            ))}
            {activity.length === 0 && (
              <div className="text-center py-4 text-sm text-[var(--color-muted)]">
                No recent activity
              </div>
            )}
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

  // Calculate totals from departments data
  const totalAgents = departments.reduce((sum, dept) => sum + dept.agentCount, 0);
  const activeAgents = departments.reduce((sum, dept) => sum + dept.activeCount, 0);

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
                  {activeAgents} of {totalAgents} agents active across {departments.length} departments
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
            {/* CEO & COO with flowing connections */}
            <div className="flex flex-col items-center">
              {/* CEO Node */}
              <div className="px-8 py-4 rounded-[var(--radius-md)] border-2 border-[var(--color-synapse)] bg-[var(--glass-bg)] text-center glow-ok relative z-10">
                <StatusOrb status="ok" size="md" />
                <p className="font-semibold text-[var(--color-plasma)] mt-2">YOU (CEO)</p>
                <p className="text-xs text-[var(--color-muted)]">Strategic Oversight</p>
              </div>

              {/* Connection: CEO to COO */}
              <FlowingConnection height={40} />

              {/* COO Node */}
              <div className="px-8 py-4 rounded-[var(--radius-md)] border border-[var(--glass-border)] bg-[var(--glass-bg)] text-center glow-processing relative z-10">
                <div className="flex justify-center gap-1 mb-2">
                  <StatusOrb status="processing" size="sm" />
                  <StatusOrb status="processing" size="sm" />
                  <StatusOrb status="processing" size="sm" />
                </div>
                <p className="font-semibold text-[var(--color-plasma)]">COO</p>
                <p className="text-xs text-[var(--color-muted)]">Task Orchestration</p>
              </div>

              {/* Vertical line down from COO */}
              <div className="w-0.5 h-6 bg-gradient-to-b from-[var(--color-synapse)] to-[var(--color-neural)] opacity-70" />

              {/* Horizontal distribution bar */}
              <div className="w-full max-w-2xl h-0.5 bg-gradient-to-r from-transparent via-[var(--color-synapse)] to-transparent opacity-70" />

              {/* Departments with integrated connectors */}
              <div className="grid grid-cols-3 gap-4 w-full max-w-3xl">
                {departments.map((dept) => (
                  <div key={dept.id} className="flex flex-col items-center">
                    {/* Vertical drop line to this department */}
                    <div className="w-0.5 h-6 bg-gradient-to-b from-[var(--color-synapse)] to-[var(--color-neural)] opacity-70" />
                    {/* Pulsing connector node */}
                    <div className="w-3 h-3 rounded-full bg-[var(--color-neural)] mb-3 shadow-[0_0_8px_var(--color-neural)] animate-pulse" />
                    {/* Department card */}
                    <DepartmentBlock
                      department={dept}
                      isExpanded={expandedDepts.includes(dept.id)}
                      onToggle={() => toggleDept(dept.id)}
                      onSelectAgent={onSelectAgent}
                      selectedAgentId={selectedAgent?.id}
                    />
                  </div>
                ))}
              </div>
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
  const glowClass = statusGlowClass[department.status];

  return (
    <GlassCard variant="elevated" padding="none" className={`overflow-hidden ${glowClass}`}>
      {/* Department Header */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-[var(--glass-bg-hover)] transition-colors"
      >
        <div className="flex items-center gap-3">
          <StatusOrb status={department.status} size="sm" pulse={department.status === 'processing'} />
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
  const glowClass = agentGlowClass[agent.status];

  return (
    <button
      onClick={onClick}
      className={`w-full px-3 py-2 rounded-[var(--radius-sm)] flex items-center gap-3 transition-all ${
        isSelected
          ? 'bg-[var(--color-neural)] bg-opacity-20 border border-[var(--color-neural)]'
          : `hover:bg-[var(--glass-bg)] ${glowClass}`
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
  // Activity log - will come from API
  const activityLog: Array<{ time: string; type: string; tool?: string; content: string }> = [];

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

// Flowing connection line with animated gradient
function FlowingConnection({ height = 40 }: { height?: number }) {
  return (
    <svg width="4" height={height} className="overflow-visible">
      <defs>
        <linearGradient id="flowGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="var(--color-synapse)" stopOpacity="0.8">
            <animate
              attributeName="stopOpacity"
              values="0.8;0.4;0.8"
              dur="2s"
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="50%" stopColor="var(--color-neural)" stopOpacity="1">
            <animate
              attributeName="stopOpacity"
              values="1;0.6;1"
              dur="2s"
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="100%" stopColor="var(--color-synapse)" stopOpacity="0.8">
            <animate
              attributeName="stopOpacity"
              values="0.8;0.4;0.8"
              dur="2s"
              repeatCount="indefinite"
            />
          </stop>
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <line
        x1="2"
        y1="0"
        x2="2"
        y2={height}
        stroke="url(#flowGradient)"
        strokeWidth="2"
        filter="url(#glow)"
      />
      {/* Animated particles flowing down */}
      <circle r="2" fill="var(--color-synapse)" filter="url(#glow)">
        <animate
          attributeName="cy"
          values={`0;${height}`}
          dur="1.5s"
          repeatCount="indefinite"
        />
        <animate
          attributeName="opacity"
          values="0;1;1;0"
          dur="1.5s"
          repeatCount="indefinite"
        />
      </circle>
    </svg>
  );
}

// Smaller preview branch connector for dashboard card
function PreviewBranchConnector({ count }: { count: number }) {
  const width = 200;
  const spacing = width / (count + 1);

  return (
    <svg width={width} height="30" className="overflow-visible">
      <defs>
        <linearGradient id="previewGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="var(--color-synapse)" stopOpacity="0.5" />
          <stop offset="100%" stopColor="var(--color-neural)" stopOpacity="0.3" />
        </linearGradient>
      </defs>
      {/* Vertical line from COO */}
      <line
        x1={width / 2}
        y1="0"
        x2={width / 2}
        y2="10"
        stroke="url(#previewGradient)"
        strokeWidth="1.5"
      />
      {/* Horizontal line */}
      <line
        x1={spacing}
        y1="10"
        x2={width - spacing}
        y2="10"
        stroke="url(#previewGradient)"
        strokeWidth="1.5"
      >
        <animate
          attributeName="stroke-opacity"
          values="0.3;0.6;0.3"
          dur="2s"
          repeatCount="indefinite"
        />
      </line>
      {/* Vertical lines to departments */}
      {Array.from({ length: count }).map((_, i) => (
        <line
          key={i}
          x1={spacing + i * spacing}
          y1="10"
          x2={spacing + i * spacing}
          y2="28"
          stroke="url(#previewGradient)"
          strokeWidth="1.5"
        />
      ))}
    </svg>
  );
}

