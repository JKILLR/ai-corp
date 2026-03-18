import { motion } from 'framer-motion';
import { Plus, ExternalLink, Settings } from 'lucide-react';
import { GlassCard, Button, StatusOrb, Badge } from '../components/ui';
import type { Status } from '../components/ui/StatusOrb';

type IntegrationCategory = 'code' | 'communication' | 'storage' | 'deployment';

interface Integration {
  id: string;
  name: string;
  description: string;
  category: IntegrationCategory;
  status: Status;
  connected: boolean;
  lastSync?: string;
  icon: string;
}

const integrations: Integration[] = [
  {
    id: 'github',
    name: 'GitHub',
    description: 'Source control and CI/CD workflows',
    category: 'code',
    status: 'ok',
    connected: true,
    lastSync: '2 min ago',
    icon: 'GH',
  },
  {
    id: 'gitlab',
    name: 'GitLab',
    description: 'DevOps platform with built-in CI',
    category: 'code',
    status: 'idle',
    connected: false,
    icon: 'GL',
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Team communication and alerts',
    category: 'communication',
    status: 'ok',
    connected: true,
    lastSync: '5 min ago',
    icon: 'SK',
  },
  {
    id: 'discord',
    name: 'Discord',
    description: 'Community and team chat',
    category: 'communication',
    status: 'idle',
    connected: false,
    icon: 'DC',
  },
  {
    id: 'linear',
    name: 'Linear',
    description: 'Issue tracking and project management',
    category: 'code',
    status: 'ok',
    connected: true,
    lastSync: '1 min ago',
    icon: 'LN',
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'Documentation and knowledge base',
    category: 'storage',
    status: 'warning',
    connected: true,
    lastSync: '1 hour ago',
    icon: 'NT',
  },
  {
    id: 'aws',
    name: 'AWS',
    description: 'Cloud infrastructure and services',
    category: 'deployment',
    status: 'ok',
    connected: true,
    lastSync: '30 sec ago',
    icon: 'AW',
  },
  {
    id: 'vercel',
    name: 'Vercel',
    description: 'Frontend deployment platform',
    category: 'deployment',
    status: 'ok',
    connected: true,
    lastSync: '15 min ago',
    icon: 'VC',
  },
  {
    id: 'gcp',
    name: 'Google Cloud',
    description: 'Cloud platform and AI services',
    category: 'deployment',
    status: 'idle',
    connected: false,
    icon: 'GC',
  },
];

const categoryLabels: Record<IntegrationCategory, string> = {
  code: 'Code & Projects',
  communication: 'Communication',
  storage: 'Storage & Docs',
  deployment: 'Deployment',
};

const categoryColors: Record<IntegrationCategory, string> = {
  code: 'bg-[var(--color-neural)]',
  communication: 'bg-[var(--color-synapse)]',
  storage: 'bg-[var(--color-proc)]',
  deployment: 'bg-[var(--color-ok)]',
};

export function Integrations() {
  const connectedCount = integrations.filter((i) => i.connected).length;
  const categories = ['code', 'communication', 'storage', 'deployment'] as IntegrationCategory[];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-[var(--color-plasma)]">
            Integrations
          </h2>
          <p className="text-sm text-[var(--color-muted)] mt-1">
            {connectedCount} of {integrations.length} integrations connected
          </p>
        </div>
        <Button variant="primary" size="md">
          <Plus className="w-4 h-4 mr-2" />
          Add Integration
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {categories.map((category) => {
          const categoryIntegrations = integrations.filter((i) => i.category === category);
          const connected = categoryIntegrations.filter((i) => i.connected).length;
          return (
            <GlassCard key={category} padding="md">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${categoryColors[category]}`} />
                <div>
                  <p className="text-sm text-[var(--color-muted)]">{categoryLabels[category]}</p>
                  <p className="text-lg font-semibold text-[var(--color-plasma)]">
                    {connected}/{categoryIntegrations.length}
                  </p>
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>

      {/* Integration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {integrations.map((integration, index) => (
          <IntegrationCard key={integration.id} integration={integration} index={index} />
        ))}
      </div>
    </div>
  );
}

function IntegrationCard({ integration, index }: { integration: Integration; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <GlassCard variant="interactive" padding="md">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={`w-12 h-12 rounded-[var(--radius-md)] ${categoryColors[integration.category]} flex items-center justify-center text-white font-semibold text-sm`}>
            {integration.icon}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-[var(--color-plasma)]">
                {integration.name}
              </h3>
              {integration.connected ? (
                <Badge status="ok" size="sm" />
              ) : (
                <Badge status="off" size="sm" />
              )}
            </div>
            <p className="text-sm text-[var(--color-muted)] mb-3">
              {integration.description}
            </p>

            {/* Status Row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusOrb status={integration.status} size="sm" pulse={false} />
                <span className="text-xs text-[var(--color-muted)]">
                  {integration.connected
                    ? `Synced ${integration.lastSync}`
                    : 'Not connected'}
                </span>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1">
                {integration.connected ? (
                  <>
                    <button className="p-1.5 hover:bg-[var(--glass-bg)] rounded text-[var(--color-muted)] hover:text-[var(--color-plasma)]">
                      <Settings className="w-4 h-4" />
                    </button>
                    <button className="p-1.5 hover:bg-[var(--glass-bg)] rounded text-[var(--color-muted)] hover:text-[var(--color-plasma)]">
                      <ExternalLink className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  <Button variant="secondary" size="sm">
                    Connect
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  );
}
