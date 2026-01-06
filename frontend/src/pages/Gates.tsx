import { motion } from 'framer-motion';
import { Check, X, Clock, AlertTriangle, Shield, DollarSign, Trash2, Rocket } from 'lucide-react';
import { GlassCard, Button, StatusOrb, Badge } from '../components/ui';
import type { Status } from '../components/ui/StatusOrb';

type GateType = 'deploy' | 'budget' | 'security' | 'delete';

interface Gate {
  id: string;
  type: GateType;
  title: string;
  description: string;
  project: string;
  agent: string;
  requestedAt: string;
  status: Status;
  priority: 'high' | 'medium' | 'low';
}

const pendingGates: Gate[] = [
  {
    id: '1',
    type: 'deploy',
    title: 'Deploy to Production',
    description: 'Website Redesign ready for production deployment. All tests passing.',
    project: 'Website Redesign',
    agent: 'dev-003',
    requestedAt: '10 min ago',
    status: 'warning',
    priority: 'high',
  },
  {
    id: '2',
    type: 'security',
    title: 'Security Review Required',
    description: 'New API endpoints require security audit before going live.',
    project: 'API Integration',
    agent: 'qa-001',
    requestedAt: '45 min ago',
    status: 'warning',
    priority: 'high',
  },
];

const recentGates: Gate[] = [
  {
    id: '3',
    type: 'budget',
    title: 'Budget Threshold Exceeded',
    description: 'Requested additional compute resources for data processing.',
    project: 'Data Pipeline Refactor',
    agent: 'dev-001',
    requestedAt: '2 hours ago',
    status: 'ok',
    priority: 'medium',
  },
  {
    id: '4',
    type: 'delete',
    title: 'Delete Legacy Resources',
    description: 'Clean up deprecated API endpoints and database tables.',
    project: 'API Integration',
    agent: 'dev-002',
    requestedAt: '1 day ago',
    status: 'ok',
    priority: 'low',
  },
];

const gateIcons: Record<GateType, React.ComponentType<{ className?: string }>> = {
  deploy: Rocket,
  budget: DollarSign,
  security: Shield,
  delete: Trash2,
};

const gateColors: Record<GateType, string> = {
  deploy: 'text-[var(--color-synapse)]',
  budget: 'text-[var(--color-proc)]',
  security: 'text-[var(--color-warn)]',
  delete: 'text-[var(--color-muted)]',
};

export function Gates() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-[var(--color-plasma)]">
            Gates
          </h2>
          <p className="text-sm text-[var(--color-muted)] mt-1">
            Review and approve agent requests requiring human oversight
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-[var(--color-muted)]">
            {pendingGates.length} pending
          </span>
          <StatusOrb status="warning" size="sm" />
        </div>
      </div>

      {/* Pending Approvals */}
      {pendingGates.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-[var(--color-plasma)] flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-[var(--color-warn)]" />
            Pending Approval
          </h3>
          <div className="space-y-3">
            {pendingGates.map((gate, index) => (
              <GateCard key={gate.id} gate={gate} index={index} isPending />
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-[var(--color-plasma)] flex items-center gap-2">
          <Clock className="w-5 h-5 text-[var(--color-muted)]" />
          Recently Resolved
        </h3>
        <div className="space-y-3">
          {recentGates.map((gate, index) => (
            <GateCard key={gate.id} gate={gate} index={index} />
          ))}
        </div>
      </div>

      {/* Info Card */}
      <GlassCard padding="lg">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-[var(--radius-md)] bg-[var(--glass-bg)]">
            <Shield className="w-6 h-6 text-[var(--color-neural)]" />
          </div>
          <div>
            <h4 className="font-medium text-[var(--color-plasma)] mb-1">
              About Gates
            </h4>
            <p className="text-sm text-[var(--color-muted)]">
              Gates are checkpoints where agents pause for human approval. They trigger for
              high-impact actions like production deployments, budget overruns, security-sensitive
              operations, or destructive actions. Configure gate rules in Settings.
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}

function GateCard({ gate, index, isPending }: { gate: Gate; index: number; isPending?: boolean }) {
  const Icon = gateIcons[gate.type];
  const iconColor = gateColors[gate.type];

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <GlassCard variant={isPending ? 'elevated' : 'default'} padding="md">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={`p-2 rounded-[var(--radius-sm)] bg-[var(--glass-bg)] ${iconColor}`}>
            <Icon className="w-5 h-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-[var(--color-plasma)]">
                    {gate.title}
                  </h4>
                  {isPending && <Badge status="warning" size="sm" />}
                  {!isPending && <Badge status="ok" size="sm" />}
                </div>
                <p className="text-sm text-[var(--color-muted)] mb-2">
                  {gate.description}
                </p>
                <div className="flex items-center gap-4 text-xs text-[var(--color-muted)]">
                  <span>Project: <span className="text-[var(--color-plasma)]">{gate.project}</span></span>
                  <span>Agent: <span className="text-[var(--color-plasma)]">{gate.agent}</span></span>
                  <span>{gate.requestedAt}</span>
                </div>
              </div>

              {/* Actions */}
              {isPending && (
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Button variant="ghost" size="sm">
                    <X className="w-4 h-4 mr-1" />
                    Reject
                  </Button>
                  <Button variant="primary" size="sm">
                    <Check className="w-4 h-4 mr-1" />
                    Approve
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
