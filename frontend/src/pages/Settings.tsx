import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Settings as SettingsIcon,
  Building2,
  Users,
  ShieldCheck,
  Zap,
  Bell,
  Palette,
  Database,
  Key,
  ChevronRight,
  Moon,
  Sun,
  Monitor,
  Save,
} from 'lucide-react';
import { GlassCard, Button, Badge } from '../components/ui';
import { useTheme } from '../hooks/useTheme';

type SettingsSection = 'general' | 'organization' | 'gates' | 'notifications' | 'appearance' | 'advanced';

interface NavItem {
  id: SettingsSection;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

const navItems: NavItem[] = [
  { id: 'general', label: 'General', icon: SettingsIcon },
  { id: 'organization', label: 'Organization', icon: Building2 },
  { id: 'gates', label: 'Gates', icon: ShieldCheck, badge: 3 },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'advanced', label: 'Advanced', icon: Zap },
];

export function Settings() {
  const [activeSection, setActiveSection] = useState<SettingsSection>('general');

  return (
    <div className="flex gap-6 h-full">
      {/* Navigation */}
      <div className="w-64 flex-shrink-0">
        <GlassCard padding="md">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] transition-colors ${
                    isActive
                      ? 'bg-[var(--glass-bg-active)] text-[var(--color-plasma)]'
                      : 'text-[var(--color-muted)] hover:bg-[var(--glass-bg)] hover:text-[var(--color-plasma)]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="flex-1 text-left text-sm">{item.label}</span>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-xs bg-[var(--color-warn)] text-white rounded">
                      {item.badge}
                    </span>
                  )}
                  {isActive && <ChevronRight className="w-4 h-4" />}
                </button>
              );
            })}
          </nav>
        </GlassCard>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <motion.div
          key={activeSection}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2 }}
        >
          {activeSection === 'general' && <GeneralSettings />}
          {activeSection === 'organization' && <OrganizationSettings />}
          {activeSection === 'gates' && <GatesSettings />}
          {activeSection === 'notifications' && <NotificationSettings />}
          {activeSection === 'appearance' && <AppearanceSettings />}
          {activeSection === 'advanced' && <AdvancedSettings />}
        </motion.div>
      </div>
    </div>
  );
}

function SettingsHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-semibold text-[var(--color-plasma)]">{title}</h2>
      <p className="text-sm text-[var(--color-muted)] mt-1">{description}</p>
    </div>
  );
}

function SettingsRow({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-4 border-b border-[var(--glass-border)] last:border-0">
      <div>
        <p className="text-sm font-medium text-[var(--color-plasma)]">{label}</p>
        {description && <p className="text-xs text-[var(--color-muted)] mt-0.5">{description}</p>}
      </div>
      <div>{children}</div>
    </div>
  );
}

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (value: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative w-11 h-6 rounded-full transition-colors ${
        enabled ? 'bg-[var(--color-neural)]' : 'bg-[var(--glass-bg)]'
      }`}
    >
      <motion.div
        className="absolute top-1 w-4 h-4 bg-white rounded-full shadow"
        animate={{ left: enabled ? 24 : 4 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </button>
  );
}

function GeneralSettings() {
  const [corpName, setCorpName] = useState('AI Corp');
  const [timezone, setTimezone] = useState('America/Los_Angeles');
  const [autoSave, setAutoSave] = useState(true);

  return (
    <div className="space-y-6">
      <SettingsHeader
        title="General Settings"
        description="Configure basic corporation settings and preferences"
      />

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Building2 className="w-4 h-4" />
          Corporation
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-xs text-[var(--color-muted)] mb-1.5">Corporation Name</label>
            <input
              type="text"
              value={corpName}
              onChange={(e) => setCorpName(e.target.value)}
              className="w-full px-3 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] focus:outline-none focus:border-[var(--color-neural)]"
            />
          </div>

          <div>
            <label className="block text-xs text-[var(--color-muted)] mb-1.5">Timezone</label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full px-3 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] focus:outline-none focus:border-[var(--color-neural)]"
            >
              <option value="America/Los_Angeles">Pacific Time (PT)</option>
              <option value="America/Denver">Mountain Time (MT)</option>
              <option value="America/Chicago">Central Time (CT)</option>
              <option value="America/New_York">Eastern Time (ET)</option>
              <option value="Europe/London">London (GMT)</option>
              <option value="Europe/Paris">Paris (CET)</option>
              <option value="Asia/Tokyo">Tokyo (JST)</option>
            </select>
          </div>
        </div>
      </GlassCard>

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <SettingsIcon className="w-4 h-4" />
          Preferences
        </h3>

        <SettingsRow label="Auto-save drafts" description="Automatically save work in progress">
          <Toggle enabled={autoSave} onChange={setAutoSave} />
        </SettingsRow>
      </GlassCard>

      <div className="flex justify-end">
        <Button variant="primary" size="md">
          <Save className="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </div>
    </div>
  );
}

function OrganizationSettings() {
  const [maxAgents, setMaxAgents] = useState('50');
  const [hierarchyDepth, setHierarchyDepth] = useState('5');

  return (
    <div className="space-y-6">
      <SettingsHeader
        title="Organization"
        description="Configure departments, hierarchy, and agent limits"
      />

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Users className="w-4 h-4" />
          Agent Limits
        </h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--color-muted)] mb-1.5">Max Concurrent Agents</label>
            <input
              type="number"
              value={maxAgents}
              onChange={(e) => setMaxAgents(e.target.value)}
              className="w-full px-3 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] focus:outline-none focus:border-[var(--color-neural)]"
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--color-muted)] mb-1.5">Max Hierarchy Depth</label>
            <input
              type="number"
              value={hierarchyDepth}
              onChange={(e) => setHierarchyDepth(e.target.value)}
              className="w-full px-3 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] focus:outline-none focus:border-[var(--color-neural)]"
            />
          </div>
        </div>
      </GlassCard>

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Building2 className="w-4 h-4" />
          Departments
        </h3>

        <div className="space-y-3">
          {['Engineering', 'Design', 'Research', 'Operations'].map((dept) => (
            <div
              key={dept}
              className="flex items-center justify-between p-3 rounded-[var(--radius-md)] bg-[var(--glass-bg)]"
            >
              <span className="text-sm text-[var(--color-plasma)]">{dept}</span>
              <Badge status="ok" size="sm" />
            </div>
          ))}
        </div>

        <Button variant="secondary" size="sm" className="mt-4">
          Add Department
        </Button>
      </GlassCard>
    </div>
  );
}

function GatesSettings() {
  const [deployGate, setDeployGate] = useState(true);
  const [budgetGate, setBudgetGate] = useState(true);
  const [securityGate, setSecurityGate] = useState(true);
  const [deleteGate, setDeleteGate] = useState(true);
  const [budgetThreshold, setBudgetThreshold] = useState('1000');

  return (
    <div className="space-y-6">
      <SettingsHeader
        title="Gate Configuration"
        description="Configure approval gates and their trigger rules"
      />

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4" />
          Gate Types
        </h3>

        <SettingsRow label="Production Deployments" description="Require approval for all production deployments">
          <Toggle enabled={deployGate} onChange={setDeployGate} />
        </SettingsRow>

        <SettingsRow label="Budget Threshold" description="Require approval when spending exceeds limit">
          <Toggle enabled={budgetGate} onChange={setBudgetGate} />
        </SettingsRow>

        <SettingsRow label="Security-Sensitive Operations" description="Require approval for security changes">
          <Toggle enabled={securityGate} onChange={setSecurityGate} />
        </SettingsRow>

        <SettingsRow label="Destructive Actions" description="Require approval for deletions and data removal">
          <Toggle enabled={deleteGate} onChange={setDeleteGate} />
        </SettingsRow>
      </GlassCard>

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Thresholds
        </h3>

        <div>
          <label className="block text-xs text-[var(--color-muted)] mb-1.5">Budget Threshold ($)</label>
          <input
            type="number"
            value={budgetThreshold}
            onChange={(e) => setBudgetThreshold(e.target.value)}
            className="w-full px-3 py-2 rounded-[var(--radius-md)] bg-[var(--glass-bg)] border border-[var(--glass-border)] text-sm text-[var(--color-plasma)] focus:outline-none focus:border-[var(--color-neural)]"
          />
          <p className="text-xs text-[var(--color-muted)] mt-1">
            Gate triggers when estimated cost exceeds this amount
          </p>
        </div>
      </GlassCard>
    </div>
  );
}

function NotificationSettings() {
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [slackNotifications, setSlackNotifications] = useState(true);
  const [gateAlerts, setGateAlerts] = useState(true);
  const [projectUpdates, setProjectUpdates] = useState(false);
  const [weeklyDigest, setWeeklyDigest] = useState(true);

  return (
    <div className="space-y-6">
      <SettingsHeader
        title="Notifications"
        description="Configure how you receive updates and alerts"
      />

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Bell className="w-4 h-4" />
          Channels
        </h3>

        <SettingsRow label="Email Notifications" description="Receive notifications via email">
          <Toggle enabled={emailNotifications} onChange={setEmailNotifications} />
        </SettingsRow>

        <SettingsRow label="Slack Integration" description="Send notifications to Slack">
          <Toggle enabled={slackNotifications} onChange={setSlackNotifications} />
        </SettingsRow>
      </GlassCard>

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Alert Types
        </h3>

        <SettingsRow label="Gate Approvals Required" description="Alert when agents need approval">
          <Toggle enabled={gateAlerts} onChange={setGateAlerts} />
        </SettingsRow>

        <SettingsRow label="Project Status Updates" description="Updates when projects change status">
          <Toggle enabled={projectUpdates} onChange={setProjectUpdates} />
        </SettingsRow>

        <SettingsRow label="Weekly Digest" description="Summary of corporation activity">
          <Toggle enabled={weeklyDigest} onChange={setWeeklyDigest} />
        </SettingsRow>
      </GlassCard>
    </div>
  );
}

function AppearanceSettings() {
  const { theme, toggleTheme } = useTheme();

  const themes = [
    { id: 'dark', label: 'Dark', icon: Moon, description: 'Dark theme for low-light environments' },
    { id: 'light', label: 'Light', icon: Sun, description: 'Light theme for bright environments' },
    { id: 'system', label: 'System', icon: Monitor, description: 'Follow system preferences' },
  ];

  return (
    <div className="space-y-6">
      <SettingsHeader
        title="Appearance"
        description="Customize the look and feel of your interface"
      />

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Palette className="w-4 h-4" />
          Theme
        </h3>

        <div className="grid grid-cols-3 gap-3">
          {themes.map((t) => {
            const Icon = t.icon;
            const isActive = theme === t.id || (t.id === 'system' && theme !== 'dark' && theme !== 'light');
            return (
              <button
                key={t.id}
                onClick={() => {
                  if (t.id === 'dark' && theme !== 'dark') toggleTheme();
                  if (t.id === 'light' && theme !== 'light') toggleTheme();
                }}
                className={`p-4 rounded-[var(--radius-md)] border transition-colors text-center ${
                  isActive
                    ? 'bg-[var(--glass-bg-active)] border-[var(--color-neural)]'
                    : 'bg-[var(--glass-bg)] border-[var(--glass-border)] hover:border-[var(--color-neural)]'
                }`}
              >
                <Icon className={`w-6 h-6 mx-auto mb-2 ${isActive ? 'text-[var(--color-neural)]' : 'text-[var(--color-muted)]'}`} />
                <p className={`text-sm font-medium ${isActive ? 'text-[var(--color-plasma)]' : 'text-[var(--color-muted)]'}`}>
                  {t.label}
                </p>
              </button>
            );
          })}
        </div>
      </GlassCard>

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Animations
        </h3>

        <SettingsRow label="Enable Animations" description="Smooth transitions and motion effects">
          <Toggle enabled={true} onChange={() => {}} />
        </SettingsRow>

        <SettingsRow label="Reduced Motion" description="Minimize animations for accessibility">
          <Toggle enabled={false} onChange={() => {}} />
        </SettingsRow>
      </GlassCard>
    </div>
  );
}

function AdvancedSettings() {
  const [debugMode, setDebugMode] = useState(false);
  const [verboseLogging, setVerboseLogging] = useState(false);

  return (
    <div className="space-y-6">
      <SettingsHeader
        title="Advanced Settings"
        description="Performance tuning, logging, and data management"
      />

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Database className="w-4 h-4" />
          Developer Options
        </h3>

        <SettingsRow label="Debug Mode" description="Enable debug information in console">
          <Toggle enabled={debugMode} onChange={setDebugMode} />
        </SettingsRow>

        <SettingsRow label="Verbose Logging" description="Log detailed operation information">
          <Toggle enabled={verboseLogging} onChange={setVerboseLogging} />
        </SettingsRow>
      </GlassCard>

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Key className="w-4 h-4" />
          API Keys
        </h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-[var(--radius-md)] bg-[var(--glass-bg)]">
            <div>
              <p className="text-sm text-[var(--color-plasma)]">Production API Key</p>
              <p className="text-xs text-[var(--color-muted)] font-mono">sk-****************************1234</p>
            </div>
            <Button variant="ghost" size="sm">Regenerate</Button>
          </div>
          <div className="flex items-center justify-between p-3 rounded-[var(--radius-md)] bg-[var(--glass-bg)]">
            <div>
              <p className="text-sm text-[var(--color-plasma)]">Development API Key</p>
              <p className="text-xs text-[var(--color-muted)] font-mono">sk-dev-************************5678</p>
            </div>
            <Button variant="ghost" size="sm">Regenerate</Button>
          </div>
        </div>
      </GlassCard>

      <GlassCard padding="lg">
        <h3 className="text-sm font-medium text-[var(--color-plasma)] mb-4 flex items-center gap-2">
          <Database className="w-4 h-4" />
          Data Management
        </h3>

        <div className="space-y-3">
          <Button variant="secondary" size="md" className="w-full justify-start">
            Export Configuration
          </Button>
          <Button variant="secondary" size="md" className="w-full justify-start">
            Import Configuration
          </Button>
          <Button variant="ghost" size="md" className="w-full justify-start text-[var(--color-warn)]">
            Reset to Defaults
          </Button>
        </div>
      </GlassCard>

      <GlassCard padding="lg" className="border-[var(--color-warn)] border-opacity-50">
        <h3 className="text-sm font-medium text-[var(--color-warn)] mb-4">Danger Zone</h3>
        <p className="text-xs text-[var(--color-muted)] mb-4">
          These actions are irreversible. Please proceed with caution.
        </p>
        <Button variant="ghost" size="md" className="text-[var(--color-warn)]">
          Delete All Data
        </Button>
      </GlassCard>
    </div>
  );
}
