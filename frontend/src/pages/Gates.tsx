import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, Clock, AlertTriangle, Shield, DollarSign, Trash2, Rocket, Info, ChevronRight } from 'lucide-react';
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
  const [confirmAction, setConfirmAction] = useState<{ gate: Gate; action: 'approve' | 'reject' } | null>(null);
  const [selectedGate, setSelectedGate] = useState<Gate | null>(null);

  const handleAction = (gate: Gate, action: 'approve' | 'reject') => {
    setConfirmAction({ gate, action });
  };

  const executeAction = () => {
    // In a real app, this would call an API
    console.log(`${confirmAction?.action} gate ${confirmAction?.gate.id}`);
    setConfirmAction(null);
  };

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
              <GateCard
                key={gate.id}
                gate={gate}
                index={index}
                isPending
                onApprove={() => handleAction(gate, 'approve')}
                onReject={() => handleAction(gate, 'reject')}
                onViewDetails={() => setSelectedGate(gate)}
              />
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
            <GateCard
              key={gate.id}
              gate={gate}
              index={index}
              onViewDetails={() => setSelectedGate(gate)}
            />
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

      {/* Confirmation Modal */}
      <AnimatePresence>
        {confirmAction && (
          <ConfirmationModal
            gate={confirmAction.gate}
            action={confirmAction.action}
            onConfirm={executeAction}
            onCancel={() => setConfirmAction(null)}
          />
        )}
      </AnimatePresence>

      {/* Gate Details Modal */}
      <AnimatePresence>
        {selectedGate && (
          <GateDetailsModal
            gate={selectedGate}
            onClose={() => setSelectedGate(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

interface GateCardProps {
  gate: Gate;
  index: number;
  isPending?: boolean;
  onApprove?: () => void;
  onReject?: () => void;
  onViewDetails?: () => void;
}

function GateCard({ gate, index, isPending, onApprove, onReject, onViewDetails }: GateCardProps) {
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
              <div className="flex items-center gap-2 flex-shrink-0">
                <Button variant="ghost" size="sm" onClick={onViewDetails}>
                  <Info className="w-4 h-4 mr-1" />
                  Details
                </Button>
                {isPending && (
                  <>
                    <Button variant="ghost" size="sm" onClick={onReject}>
                      <X className="w-4 h-4 mr-1" />
                      Reject
                    </Button>
                    <Button variant="primary" size="sm" onClick={onApprove}>
                      <Check className="w-4 h-4 mr-1" />
                      Approve
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}

/* Confirmation Modal */
function ConfirmationModal({
  gate,
  action,
  onConfirm,
  onCancel,
}: {
  gate: Gate;
  action: 'approve' | 'reject';
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const isApprove = action === 'approve';
  const Icon = gateIcons[gate.type];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[var(--z-modal-backdrop)] flex items-center justify-center p-6"
      onClick={onCancel}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
        className="relative z-10 w-full max-w-md"
      >
        <GlassCard variant="elevated" padding="lg">
          <div className="text-center">
            {/* Icon */}
            <div className={`inline-flex p-4 rounded-full mb-4 ${
              isApprove ? 'bg-[var(--color-ok)]/10' : 'bg-[var(--color-warn)]/10'
            }`}>
              {isApprove ? (
                <Check className="w-8 h-8 text-[var(--color-ok)]" />
              ) : (
                <X className="w-8 h-8 text-[var(--color-warn)]" />
              )}
            </div>

            {/* Title */}
            <h3 className="text-xl font-semibold text-[var(--color-plasma)] mb-2">
              {isApprove ? 'Approve Request?' : 'Reject Request?'}
            </h3>

            {/* Description */}
            <p className="text-sm text-[var(--color-muted)] mb-6">
              {isApprove
                ? `This will allow ${gate.agent} to proceed with "${gate.title}".`
                : `This will block ${gate.agent} from proceeding with "${gate.title}".`}
            </p>

            {/* Gate Summary */}
            <div className="p-4 rounded-[var(--radius-md)] bg-[var(--glass-bg)] mb-6 text-left">
              <div className="flex items-center gap-3 mb-2">
                <Icon className="w-5 h-5 text-[var(--color-neural)]" />
                <span className="font-medium text-[var(--color-plasma)]">{gate.title}</span>
              </div>
              <p className="text-xs text-[var(--color-muted)]">
                Project: {gate.project} • Agent: {gate.agent}
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button variant="secondary" size="md" className="flex-1" onClick={onCancel}>
                Cancel
              </Button>
              <Button
                variant={isApprove ? 'primary' : 'ghost'}
                size="md"
                className={`flex-1 ${!isApprove ? 'border border-[var(--color-warn)] text-[var(--color-warn)]' : ''}`}
                onClick={onConfirm}
              >
                {isApprove ? 'Approve' : 'Reject'}
              </Button>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </motion.div>
  );
}

/* Gate Details Modal */
function GateDetailsModal({ gate, onClose }: { gate: Gate; onClose: () => void }) {
  const Icon = gateIcons[gate.type];
  const iconColor = gateColors[gate.type];

  // Mock workflow steps
  const workflowSteps = [
    { name: 'Request Initiated', time: gate.requestedAt, completed: true },
    { name: 'Validation Passed', time: '2 min later', completed: true },
    { name: 'Awaiting Approval', time: 'Current', completed: false },
    { name: 'Execution', time: 'Pending', completed: false },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[var(--z-modal-backdrop)] flex items-center justify-center p-6"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
        className="relative z-10 w-full max-w-2xl max-h-[85vh] overflow-y-auto"
      >
        <GlassCard variant="elevated" padding="lg">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-[var(--radius-md)] bg-[var(--glass-bg)] ${iconColor}`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-[var(--color-plasma)]">
                  {gate.title}
                </h2>
                <p className="text-sm text-[var(--color-muted)]">{gate.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-[var(--glass-bg)] rounded-[var(--radius-sm)] transition-colors"
            >
              <X className="w-5 h-5 text-[var(--color-muted)]" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left: Details */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-[var(--color-plasma)]">Request Details</h4>

              <div className="space-y-3">
                <div className="flex justify-between p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
                  <span className="text-sm text-[var(--color-muted)]">Project</span>
                  <span className="text-sm text-[var(--color-plasma)]">{gate.project}</span>
                </div>
                <div className="flex justify-between p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
                  <span className="text-sm text-[var(--color-muted)]">Requesting Agent</span>
                  <span className="text-sm text-[var(--color-plasma)]">{gate.agent}</span>
                </div>
                <div className="flex justify-between p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
                  <span className="text-sm text-[var(--color-muted)]">Gate Type</span>
                  <span className="text-sm text-[var(--color-plasma)] capitalize">{gate.type}</span>
                </div>
                <div className="flex justify-between p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
                  <span className="text-sm text-[var(--color-muted)]">Priority</span>
                  <Badge status={gate.priority === 'high' ? 'warning' : gate.priority === 'medium' ? 'processing' : 'idle'} size="sm" />
                </div>
                <div className="flex justify-between p-3 rounded-[var(--radius-sm)] bg-[var(--glass-bg)]">
                  <span className="text-sm text-[var(--color-muted)]">Requested</span>
                  <span className="text-sm text-[var(--color-plasma)]">{gate.requestedAt}</span>
                </div>
              </div>
            </div>

            {/* Right: Workflow */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-[var(--color-plasma)]">Workflow Progress</h4>

              <div className="space-y-1">
                {workflowSteps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`w-3 h-3 rounded-full ${
                        step.completed ? 'bg-[var(--color-ok)]' : 'bg-[var(--glass-border)]'
                      }`} />
                      {idx < workflowSteps.length - 1 && (
                        <div className={`w-0.5 h-8 ${
                          step.completed ? 'bg-[var(--color-ok)]' : 'bg-[var(--glass-border)]'
                        }`} />
                      )}
                    </div>
                    <div className="flex-1 pb-6">
                      <p className={`text-sm ${step.completed ? 'text-[var(--color-plasma)]' : 'text-[var(--color-muted)]'}`}>
                        {step.name}
                      </p>
                      <p className="text-xs text-[var(--color-muted)]">{step.time}</p>
                    </div>
                    {!step.completed && idx === workflowSteps.findIndex(s => !s.completed) && (
                      <ChevronRight className="w-4 h-4 text-[var(--color-neural)] animate-pulse" />
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
