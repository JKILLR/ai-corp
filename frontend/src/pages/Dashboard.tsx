import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';
import { GlassCard } from '../components/ui';
import { StatusOrb } from '../components/ui/StatusOrb';
import { Badge } from '../components/ui/Badge';
import type { Status } from '../components/ui/StatusOrb';

export function Dashboard() {
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

        {/* Agent Network Preview */}
        <GlassCard variant="elevated" padding="lg">
          <div className="flex items-center gap-2 mb-6">
            <StatusOrb status="processing" size="sm" />
            <h3 className="text-lg font-medium text-[var(--color-plasma)]">
              Agent Network
            </h3>
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
              <AgentNodeSmall status="ok" />
              <AgentNodeSmall status="ok" />
              <AgentNodeSmall status="warning" />
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
    </div>
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

function AgentNodeSmall({ status }: { status: Status }) {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className="w-16 h-10 rounded-[var(--radius-sm)] border border-[var(--glass-border)] bg-[var(--glass-bg)] flex items-center justify-center"
    >
      <StatusOrb status={status} size="sm" />
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
