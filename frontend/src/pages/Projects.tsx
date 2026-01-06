import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, Filter, X, Users, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import { GlassCard, Button, StatusOrb, Badge } from '../components/ui';
import type { Status } from '../components/ui/StatusOrb';

interface ProjectAgent {
  id: string;
  name: string;
  role: string;
  status: Status;
  currentTask?: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  status: Status;
  progress: number;
  agents: number;
  tasks: { completed: number; total: number };
  lastActivity: string;
  assignedAgents: ProjectAgent[];
  milestones: { name: string; completed: boolean }[];
}

const projects: Project[] = [
  {
    id: '1',
    name: 'Website Redesign',
    description: 'Complete overhaul of the marketing website with new brand guidelines',
    status: 'ok',
    progress: 67,
    agents: 3,
    tasks: { completed: 12, total: 18 },
    lastActivity: '5 min ago',
    assignedAgents: [
      { id: 'dev-001', name: 'dev-001', role: 'Senior Developer', status: 'processing', currentTask: 'Implementing hero section' },
      { id: 'design-001', name: 'design-001', role: 'UI Designer', status: 'ok', currentTask: 'Creating component library' },
      { id: 'qa-001', name: 'qa-001', role: 'QA Engineer', status: 'ok', currentTask: 'Running visual regression tests' },
    ],
    milestones: [
      { name: 'Design System', completed: true },
      { name: 'Homepage', completed: true },
      { name: 'Product Pages', completed: false },
      { name: 'Launch', completed: false },
    ],
  },
  {
    id: '2',
    name: 'API Integration',
    description: 'Connect third-party services and build unified API layer',
    status: 'ok',
    progress: 89,
    agents: 1,
    tasks: { completed: 8, total: 9 },
    lastActivity: '12 min ago',
    assignedAgents: [
      { id: 'dev-002', name: 'dev-002', role: 'Developer', status: 'ok', currentTask: 'Finalizing OAuth flow' },
    ],
    milestones: [
      { name: 'Auth Layer', completed: true },
      { name: 'Data Sync', completed: true },
      { name: 'Testing', completed: false },
    ],
  },
  {
    id: '3',
    name: 'Data Pipeline Refactor',
    description: 'Modernize data processing infrastructure for better scalability',
    status: 'warning',
    progress: 45,
    agents: 2,
    tasks: { completed: 5, total: 11 },
    lastActivity: '1 hour ago',
    assignedAgents: [
      { id: 'research-001', name: 'research-001', role: 'Data Analyst', status: 'warning', currentTask: 'Blocked: Waiting for data access' },
      { id: 'research-002', name: 'research-002', role: 'ML Engineer', status: 'processing', currentTask: 'Optimizing batch processing' },
    ],
    milestones: [
      { name: 'Schema Design', completed: true },
      { name: 'Migration Scripts', completed: false },
      { name: 'Performance Testing', completed: false },
    ],
  },
  {
    id: '4',
    name: 'Mobile App MVP',
    description: 'Build first version of mobile application for iOS and Android',
    status: 'processing',
    progress: 23,
    agents: 4,
    tasks: { completed: 7, total: 30 },
    lastActivity: '2 min ago',
    assignedAgents: [
      { id: 'dev-003', name: 'dev-003', role: 'Developer', status: 'processing', currentTask: 'Building navigation stack' },
      { id: 'design-002', name: 'design-002', role: 'UX Designer', status: 'ok', currentTask: 'User flow diagrams' },
      { id: 'dev-004', name: 'dev-004', role: 'Mobile Developer', status: 'processing', currentTask: 'iOS native components' },
      { id: 'dev-005', name: 'dev-005', role: 'Mobile Developer', status: 'processing', currentTask: 'Android native components' },
    ],
    milestones: [
      { name: 'Wireframes', completed: true },
      { name: 'Core Features', completed: false },
      { name: 'Beta Release', completed: false },
      { name: 'App Store', completed: false },
    ],
  },
  {
    id: '5',
    name: 'Security Audit',
    description: 'Comprehensive security review and vulnerability assessment',
    status: 'waiting',
    progress: 10,
    agents: 1,
    tasks: { completed: 2, total: 20 },
    lastActivity: '3 hours ago',
    assignedAgents: [
      { id: 'sec-001', name: 'sec-001', role: 'Security Engineer', status: 'waiting', currentTask: 'Waiting for scope approval' },
    ],
    milestones: [
      { name: 'Scope Definition', completed: true },
      { name: 'Vulnerability Scan', completed: false },
      { name: 'Penetration Testing', completed: false },
      { name: 'Final Report', completed: false },
    ],
  },
];

export function Projects() {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-[var(--color-plasma)]">
          Projects
        </h2>
        <Button variant="primary" size="md">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted)]" />
          <input
            type="text"
            placeholder="Search projects..."
            className="w-full pl-10 pr-4 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] placeholder:text-[var(--color-muted)] focus:outline-none focus:border-[var(--color-neural)] transition-colors"
          />
        </div>
        <Button variant="ghost" size="md">
          <Filter className="w-4 h-4 mr-2" />
          Filter
        </Button>
      </div>

      {/* Project Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {projects.map((project, index) => (
          <ProjectCard
            key={project.id}
            project={project}
            index={index}
            onClick={() => setSelectedProject(project)}
          />
        ))}
      </div>

      {/* Project Detail Modal */}
      <AnimatePresence>
        {selectedProject && (
          <ProjectDetailModal
            project={selectedProject}
            onClose={() => setSelectedProject(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function ProjectCard({ project, index, onClick }: { project: Project; index: number; onClick: () => void }) {
  const progressColor = project.status === 'warning'
    ? 'bg-[var(--color-warn)]'
    : project.status === 'processing'
    ? 'bg-[var(--color-proc)]'
    : 'bg-[var(--color-ok)]';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={onClick}
      className="cursor-pointer"
    >
      <GlassCard variant="interactive" padding="md" className="h-full">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <StatusOrb status={project.status} size="sm" />
              <h3 className="font-medium text-[var(--color-plasma)]">
                {project.name}
              </h3>
            </div>
            <Badge status={project.status} size="sm" />
          </div>

          {/* Description */}
          <p className="text-sm text-[var(--color-muted)] mb-4 line-clamp-2">
            {project.description}
          </p>

          {/* Progress */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-[var(--color-muted)]">Progress</span>
              <span className="text-[var(--color-plasma)]">{project.progress}%</span>
            </div>
            <div className="h-1.5 bg-[var(--glass-bg)] rounded-full overflow-hidden">
              <motion.div
                className={`h-full ${progressColor}`}
                initial={{ width: 0 }}
                animate={{ width: `${project.progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut', delay: index * 0.05 }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center justify-between text-sm mt-auto pt-3 border-t border-[var(--glass-border)]">
            <div className="flex items-center gap-4">
              <span className="text-[var(--color-muted)]">
                <span className="text-[var(--color-plasma)]">{project.agents}</span> agents
              </span>
              <span className="text-[var(--color-muted)]">
                <span className="text-[var(--color-plasma)]">{project.tasks.completed}</span>/{project.tasks.total} tasks
              </span>
            </div>
            <span className="text-xs text-[var(--color-muted)]">
              {project.lastActivity}
            </span>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}

/* Project Detail Modal with Molecule Visualization */
function ProjectDetailModal({ project, onClose }: { project: Project; onClose: () => void }) {
  const progressColor = project.status === 'warning'
    ? 'bg-[var(--color-warn)]'
    : project.status === 'processing'
    ? 'bg-[var(--color-proc)]'
    : 'bg-[var(--color-ok)]';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[var(--z-modal-backdrop)] flex items-center justify-center p-6"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
        className="relative z-10 w-full max-w-4xl max-h-[85vh] overflow-y-auto"
      >
        <GlassCard variant="elevated" padding="lg">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-3">
              <StatusOrb status={project.status} size="lg" />
              <div>
                <h2 className="text-xl font-semibold text-[var(--color-plasma)]">
                  {project.name}
                </h2>
                <p className="text-sm text-[var(--color-muted)]">{project.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-[var(--glass-bg)] rounded-[var(--radius-sm)] transition-colors"
            >
              <X className="w-5 h-5 text-[var(--color-muted)]" />
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: Stats & Milestones */}
            <div className="space-y-6">
              {/* Progress */}
              <div className="p-4 rounded-[var(--radius-md)] bg-[var(--glass-bg)]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[var(--color-muted)]">Overall Progress</span>
                  <span className="text-lg font-semibold text-[var(--color-plasma)]">{project.progress}%</span>
                </div>
                <div className="h-2 bg-[var(--glass-border)] rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${progressColor}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${project.progress}%` }}
                    transition={{ duration: 0.6, ease: 'easeOut' }}
                  />
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)] text-center">
                  <Users className="w-5 h-5 text-[var(--color-neural)] mx-auto mb-1" />
                  <p className="text-lg font-semibold text-[var(--color-plasma)]">{project.agents}</p>
                  <p className="text-xs text-[var(--color-muted)]">Agents</p>
                </div>
                <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)] text-center">
                  <CheckCircle2 className="w-5 h-5 text-[var(--color-ok)] mx-auto mb-1" />
                  <p className="text-lg font-semibold text-[var(--color-plasma)]">{project.tasks.completed}/{project.tasks.total}</p>
                  <p className="text-xs text-[var(--color-muted)]">Tasks</p>
                </div>
                <div className="p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)] text-center">
                  <Clock className="w-5 h-5 text-[var(--color-synapse)] mx-auto mb-1" />
                  <p className="text-sm font-semibold text-[var(--color-plasma)]">{project.lastActivity}</p>
                  <p className="text-xs text-[var(--color-muted)]">Activity</p>
                </div>
              </div>

              {/* Milestones */}
              <div>
                <h4 className="text-sm font-medium text-[var(--color-plasma)] mb-3">Milestones</h4>
                <div className="space-y-2">
                  {project.milestones.map((milestone, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-3 p-3 rounded-[var(--radius-sm)] ${
                        milestone.completed ? 'bg-[var(--color-ok)]/10' : 'bg-[var(--glass-bg)]'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                        milestone.completed
                          ? 'bg-[var(--color-ok)]'
                          : 'border-2 border-[var(--glass-border)]'
                      }`}>
                        {milestone.completed && (
                          <CheckCircle2 className="w-3 h-3 text-white" />
                        )}
                      </div>
                      <span className={`text-sm ${milestone.completed ? 'text-[var(--color-ok)]' : 'text-[var(--color-muted)]'}`}>
                        {milestone.name}
                      </span>
                      {!milestone.completed && idx === project.milestones.findIndex(m => !m.completed) && (
                        <ArrowRight className="w-4 h-4 text-[var(--color-neural)] ml-auto" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Agent Molecule Visualization */}
            <div>
              <h4 className="text-sm font-medium text-[var(--color-plasma)] mb-3">Agent Network</h4>
              <div className="relative p-6 rounded-[var(--radius-md)] bg-[var(--glass-bg)] min-h-[300px]">
                {/* Molecule Visualization */}
                <ProjectMolecule agents={project.assignedAgents} projectName={project.name} />
              </div>

              {/* Agent List */}
              <div className="mt-4 space-y-2">
                {project.assignedAgents.map((agent) => (
                  <div
                    key={agent.id}
                    className="flex items-center gap-3 p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]"
                  >
                    <StatusOrb status={agent.status} size="sm" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--color-plasma)]">{agent.name}</p>
                      <p className="text-xs text-[var(--color-muted)]">{agent.role}</p>
                    </div>
                    {agent.currentTask && (
                      <p className="text-xs text-[var(--color-muted)] truncate max-w-[150px]">
                        {agent.currentTask}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </motion.div>
  );
}

/* Molecule Visualization Component */
function ProjectMolecule({ agents, projectName }: { agents: ProjectAgent[]; projectName: string }) {
  const centerX = 150;
  const centerY = 120;
  const radius = 80;

  // Calculate positions for agents in a circle around the center
  const agentPositions = agents.map((_, idx) => {
    const angle = (idx / agents.length) * 2 * Math.PI - Math.PI / 2;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  const statusColor = (status: Status) => {
    switch (status) {
      case 'ok': return '#22C55E';
      case 'processing': return '#8B5CF6';
      case 'warning': return '#EF4444';
      case 'waiting': return '#6366F1';
      default: return '#64748B';
    }
  };

  return (
    <svg viewBox="0 0 300 240" className="w-full h-full">
      {/* Connection lines from center to each agent */}
      {agentPositions.map((pos, idx) => (
        <motion.line
          key={`line-${idx}`}
          x1={centerX}
          y1={centerY}
          x2={pos.x}
          y2={pos.y}
          stroke="var(--color-neural)"
          strokeWidth="2"
          strokeOpacity="0.3"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.5, delay: idx * 0.1 }}
        />
      ))}

      {/* Central project node */}
      <motion.g
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', damping: 15 }}
      >
        <circle
          cx={centerX}
          cy={centerY}
          r="28"
          fill="var(--color-neural)"
          fillOpacity="0.2"
        />
        <circle
          cx={centerX}
          cy={centerY}
          r="20"
          fill="var(--color-neural)"
        />
        <text
          x={centerX}
          y={centerY + 4}
          textAnchor="middle"
          fill="white"
          fontSize="8"
          fontWeight="600"
        >
          {projectName.slice(0, 3).toUpperCase()}
        </text>
      </motion.g>

      {/* Agent nodes */}
      {agents.map((agent, idx) => {
        const pos = agentPositions[idx];
        const color = statusColor(agent.status);

        return (
          <motion.g
            key={agent.id}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 + idx * 0.1, type: 'spring', damping: 15 }}
          >
            {/* Glow effect for active agents */}
            {(agent.status === 'ok' || agent.status === 'processing') && (
              <motion.circle
                cx={pos.x}
                cy={pos.y}
                r="18"
                fill={color}
                fillOpacity="0.2"
                animate={{
                  r: [18, 22, 18],
                  fillOpacity: [0.2, 0.1, 0.2],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
            )}

            {/* Agent circle */}
            <circle
              cx={pos.x}
              cy={pos.y}
              r="14"
              fill={color}
            />

            {/* Agent label */}
            <text
              x={pos.x}
              y={pos.y + 3}
              textAnchor="middle"
              fill="white"
              fontSize="7"
              fontWeight="500"
            >
              {agent.name.slice(-3)}
            </text>
          </motion.g>
        );
      })}
    </svg>
  );
}
