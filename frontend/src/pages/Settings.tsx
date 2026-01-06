import { GlassCard } from '../components/ui';

export function Settings() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-[var(--color-plasma)]">
        Settings
      </h2>
      <GlassCard padding="lg">
        <p className="text-[var(--color-muted)]">
          System settings - Coming soon
        </p>
      </GlassCard>
    </div>
  );
}
