import { motion } from 'framer-motion';
import { Plus, Search, Filter } from 'lucide-react';
import { GlassCard, Button, StatusOrb, Badge } from '../components/ui';
import type { Status } from '../components/ui/StatusOrb';

interface Project {
  id: string;
  name: string;
  description: string;
  status: Status;
  progress: number;
  agents: number;
  tasks: { completed: number; total: number };
  lastActivity: string;
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
  },
];

export function Projects() {
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
          <ProjectCard key={project.id} project={project} index={index} />
        ))}
      </div>
    </div>
  );
}

function ProjectCard({ project, index }: { project: Project; index: number }) {
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
