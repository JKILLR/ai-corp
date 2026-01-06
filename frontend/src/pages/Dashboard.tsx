import { GlassCard } from '../components/ui';
import { StatusOrb } from '../components/ui/StatusOrb';
import { Badge } from '../components/ui/Badge';

export function Dashboard() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-[var(--color-plasma)]">
        Dashboard
      </h2>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Projects"
          value="12"
          status="ok"
        />
        <StatCard
          label="Running Agents"
          value="47"
          status="processing"
        />
        <StatCard
          label="Pending Reviews"
          value="8"
          status="waiting"
        />
        <StatCard
          label="Gate Failures"
          value="3"
          status="warning"
        />
      </div>

      {/* Activity Feed Placeholder */}
      <GlassCard variant="elevated" padding="lg">
        <h3 className="text-lg font-medium text-[var(--color-plasma)] mb-4">
          Recent Activity
        </h3>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="flex items-center gap-3 py-2 border-b border-[var(--glass-border)] last:border-0"
            >
              <StatusOrb status={i % 2 === 0 ? 'ok' : 'processing'} size="sm" />
              <span className="flex-1 text-sm text-[var(--color-muted)]">
                Agent completed task #{i}
              </span>
              <span className="text-xs text-[var(--color-muted)]">2m ago</span>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  status: 'ok' | 'processing' | 'warning' | 'waiting' | 'idle' | 'off';
}

function StatCard({ label, value, status }: StatCardProps) {
  return (
    <GlassCard variant="interactive" padding="md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--color-muted)]">{label}</p>
          <p className="text-3xl font-semibold text-[var(--color-plasma)] mt-1">
            {value}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusOrb status={status} size="md" />
          <Badge status={status} size="sm" />
        </div>
      </div>
    </GlassCard>
  );
}
