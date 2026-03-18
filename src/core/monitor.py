"""
System Monitoring - Lightweight Background Service

Provides system observability through:
- Agent heartbeat tracking
- Queue depth monitoring
- Molecule progress tracking
- Health alerts with suggested actions

Integration Points:
- Monitor ← Hooks: Reads queue depths
- Monitor ← Molecules: Reads progress
- Monitor ← Agents: Reads heartbeats
- Monitor ← Channels: Reads pending message counts
- Monitor → Beads: Critical alerts recorded
- Monitor → Channels: Alerts broadcast
"""

import yaml
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthState(Enum):
    """Health states for components"""
    HEALTHY = "healthy"
    SLOW = "slow"
    UNRESPONSIVE = "unresponsive"
    UNKNOWN = "unknown"


@dataclass
class AgentStatus:
    """Status of a single agent"""
    agent_id: str
    role: str
    department: str
    last_heartbeat: Optional[str]
    current_work: Optional[str]
    queue_depth: int
    health: HealthState

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'department': self.department,
            'last_heartbeat': self.last_heartbeat,
            'current_work': self.current_work,
            'queue_depth': self.queue_depth,
            'health': self.health.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentStatus':
        data['health'] = HealthState(data['health'])
        return cls(**data)


@dataclass
class HealthAlert:
    """Alert requiring attention"""
    id: str
    severity: AlertSeverity
    component: str
    message: str
    suggested_action: str
    created_at: str
    resolved_at: Optional[str] = None
    acknowledged_by: Optional[str] = None

    @classmethod
    def create(
        cls,
        severity: AlertSeverity,
        component: str,
        message: str,
        suggested_action: str
    ) -> 'HealthAlert':
        import uuid
        return cls(
            id=f"ALERT-{uuid.uuid4().hex[:8].upper()}",
            severity=severity,
            component=component,
            message=message,
            suggested_action=suggested_action,
            created_at=datetime.utcnow().isoformat()
        )

    def resolve(self) -> None:
        self.resolved_at = datetime.utcnow().isoformat()

    def acknowledge(self, by: str) -> None:
        self.acknowledged_by = by

    def is_active(self) -> bool:
        return self.resolved_at is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'severity': self.severity.value,
            'component': self.component,
            'message': self.message,
            'suggested_action': self.suggested_action,
            'created_at': self.created_at,
            'resolved_at': self.resolved_at,
            'acknowledged_by': self.acknowledged_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthAlert':
        data['severity'] = AlertSeverity(data['severity'])
        return cls(**data)


@dataclass
class SystemMetrics:
    """Current system state snapshot"""
    timestamp: str
    agents: Dict[str, AgentStatus]
    queues: Dict[str, int]  # agent_id -> queue depth
    molecules: Dict[str, float]  # molecule_id -> progress %
    errors: List[str]  # Recent errors
    pending_gates: int
    active_molecules: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'agents': {k: v.to_dict() for k, v in self.agents.items()},
            'queues': self.queues,
            'molecules': self.molecules,
            'errors': self.errors,
            'pending_gates': self.pending_gates,
            'active_molecules': self.active_molecules
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemMetrics':
        data['agents'] = {k: AgentStatus.from_dict(v) for k, v in data.get('agents', {}).items()}
        return cls(**data)

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'SystemMetrics':
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class SystemMonitor:
    """
    Lightweight monitoring service.

    Collects metrics from all system components and generates health alerts.

    Integration:
    - Reads from: HookManager, MoleculeEngine, GateKeeper, ChannelManager
    - Writes to: Metrics files, Alerts, Beads (for audit), Channels (for broadcast)
    """

    def __init__(
        self,
        corp_path: Path,
        bead_ledger=None,
        channel_manager=None
    ):
        self.corp_path = Path(corp_path)
        self.metrics_path = self.corp_path / "metrics"
        self.metrics_path.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.metrics_path / "current.yaml"
        self.alerts_file = self.metrics_path / "alerts.yaml"
        self.heartbeats_file = self.metrics_path / "heartbeats.yaml"

        # For bead and channel integration
        self.bead_ledger = bead_ledger
        self.channel_manager = channel_manager

        # Health thresholds (in seconds)
        self.thresholds = {
            'heartbeat_warning': 60,     # 1 minute without heartbeat
            'heartbeat_critical': 300,   # 5 minutes without heartbeat
            'queue_warning': 10,         # 10 items in queue
            'queue_critical': 50,        # 50 items in queue
            'stale_work_warning': 3600,  # 1 hour oldest item age
            'stale_work_critical': 7200, # 2 hours oldest item age
        }

        # Initialize files if they don't exist
        self._init_metrics_files()

    def _init_metrics_files(self) -> None:
        """Initialize metrics files if they don't exist"""
        if not self.heartbeats_file.exists():
            self._save_heartbeats({})
        if not self.alerts_file.exists():
            self._save_alerts([])

    def collect_metrics(self) -> SystemMetrics:
        """
        Collect current system metrics from all sources.

        Integration Points:
        - HookManager: Queue depths, current work
        - MoleculeEngine: Molecule progress
        - GateKeeper: Pending submissions
        """
        from .hook import HookManager
        from .molecule import MoleculeEngine
        from .gate import GateKeeper

        agents = {}
        queues = {}
        molecules = {}
        errors = []

        # Get heartbeats
        heartbeats = self._load_heartbeats()

        # Scan hooks for queue depths and agent status
        try:
            hook_manager = HookManager(self.corp_path)
            for hook in hook_manager.list_hooks():
                stats = hook.get_stats()
                queue_depth = stats.get('queued', 0) + stats.get('in_progress', 0)
                queues[hook.owner_id] = queue_depth

                # Get current work item if any
                current_work = None
                in_progress_items = [item for item in hook.items
                                     if item.status.value == 'in_progress']
                if in_progress_items:
                    current_work = in_progress_items[0].title

                # Determine agent health based on heartbeat
                health = self._assess_agent_health(
                    hook.owner_id,
                    heartbeats.get(hook.owner_id)
                )

                agents[hook.owner_id] = AgentStatus(
                    agent_id=hook.owner_id,
                    role=hook.owner_type,
                    department=self._get_department(hook.owner_id),
                    last_heartbeat=heartbeats.get(hook.owner_id),
                    current_work=current_work,
                    queue_depth=queue_depth,
                    health=health
                )
        except Exception as e:
            errors.append(f"Error scanning hooks: {str(e)}")

        # Scan molecules for progress
        active_molecules = 0
        try:
            engine = MoleculeEngine(self.corp_path)
            for mol in engine.list_active_molecules():
                progress = mol.get_progress()
                molecules[mol.id] = progress.get('percent_complete', 0)
                active_molecules += 1
        except Exception as e:
            errors.append(f"Error scanning molecules: {str(e)}")

        # Scan gates for pending submissions
        pending_gates = 0
        try:
            gate_keeper = GateKeeper(self.corp_path)
            pending_submissions = gate_keeper.get_pending_submissions()
            pending_gates = len(pending_submissions)
        except Exception as e:
            errors.append(f"Error scanning gates: {str(e)}")

        # Get recent errors from beads if available
        if self.bead_ledger:
            try:
                recent_errors = self._get_recent_errors_from_beads()
                errors.extend(recent_errors)
            except Exception:
                pass

        metrics = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            agents=agents,
            queues=queues,
            molecules=molecules,
            errors=errors[-10:],  # Keep last 10 errors
            pending_gates=pending_gates,
            active_molecules=active_molecules
        )

        self._save_metrics(metrics)
        return metrics

    def check_health(self) -> List[HealthAlert]:
        """
        Check system health and generate alerts.

        Returns list of new alerts generated. Also:
        - Records critical alerts as bead entries
        - Broadcasts critical alerts via channels
        """
        metrics = self.collect_metrics()
        new_alerts = []
        existing_alerts = self._load_alerts()

        # Check each agent
        for agent_id, status in metrics.agents.items():
            # Check heartbeat health
            if status.health == HealthState.UNRESPONSIVE:
                alert = self._create_alert_if_new(
                    existing_alerts,
                    AlertSeverity.CRITICAL,
                    f'agent:{agent_id}',
                    f'Agent {agent_id} is unresponsive (no heartbeat)',
                    f'Restart agent: ai-corp restart {agent_id}'
                )
                if alert:
                    new_alerts.append(alert)

            elif status.health == HealthState.SLOW:
                alert = self._create_alert_if_new(
                    existing_alerts,
                    AlertSeverity.WARNING,
                    f'agent:{agent_id}',
                    f'Agent {agent_id} heartbeat is delayed',
                    f'Monitor agent {agent_id} - may need attention'
                )
                if alert:
                    new_alerts.append(alert)

            # Check queue depth
            if status.queue_depth >= self.thresholds['queue_critical']:
                alert = self._create_alert_if_new(
                    existing_alerts,
                    AlertSeverity.CRITICAL,
                    f'queue:{agent_id}',
                    f'Queue depth {status.queue_depth} exceeds critical threshold',
                    f'Scale workers or investigate bottleneck for {agent_id}'
                )
                if alert:
                    new_alerts.append(alert)

            elif status.queue_depth >= self.thresholds['queue_warning']:
                alert = self._create_alert_if_new(
                    existing_alerts,
                    AlertSeverity.WARNING,
                    f'queue:{agent_id}',
                    f'Queue depth {status.queue_depth} exceeds warning threshold',
                    f'Monitor queue for {agent_id}'
                )
                if alert:
                    new_alerts.append(alert)

        # Check for stalled molecules
        for mol_id, progress in metrics.molecules.items():
            # Check if molecule has been stuck (would need historical data)
            pass

        # Record critical alerts in beads and broadcast
        for alert in new_alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                self._record_alert_bead(alert)
                self._broadcast_alert(alert)

        # Save all alerts
        all_alerts = existing_alerts + new_alerts
        self._save_alerts([a for a in all_alerts if a.is_active()])

        return new_alerts

    def _create_alert_if_new(
        self,
        existing_alerts: List[HealthAlert],
        severity: AlertSeverity,
        component: str,
        message: str,
        suggested_action: str
    ) -> Optional[HealthAlert]:
        """Create alert only if similar active alert doesn't exist"""
        # Check if similar alert already exists
        for alert in existing_alerts:
            if alert.component == component and alert.is_active():
                return None

        return HealthAlert.create(
            severity=severity,
            component=component,
            message=message,
            suggested_action=suggested_action
        )

    def record_heartbeat(self, agent_id: str) -> None:
        """
        Record a heartbeat from an agent.

        Called by agents during their run cycle.
        """
        heartbeats = self._load_heartbeats()
        heartbeats[agent_id] = datetime.utcnow().isoformat()
        self._save_heartbeats(heartbeats)

    def get_agent_heartbeat(self, agent_id: str) -> Optional[str]:
        """Get the last heartbeat timestamp for an agent"""
        heartbeats = self._load_heartbeats()
        return heartbeats.get(agent_id)

    def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an active alert"""
        alerts = self._load_alerts()
        for alert in alerts:
            if alert.id == alert_id:
                alert.resolve()
                self._save_alerts(alerts)

                # Record resolution in bead
                if self.bead_ledger and alert.severity == AlertSeverity.CRITICAL:
                    self._record_bead(
                        action='resolve_alert',
                        entity_type='alert',
                        entity_id=alert.id,
                        data=alert.to_dict(),
                        message=f"Alert resolved by {resolved_by}: {alert.message}",
                        agent_id=resolved_by
                    )

                return True
        return False

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        alerts = self._load_alerts()
        for alert in alerts:
            if alert.id == alert_id:
                alert.acknowledge(acknowledged_by)
                self._save_alerts(alerts)
                return True
        return False

    def get_active_alerts(self) -> List[HealthAlert]:
        """Get all active (unresolved) alerts"""
        alerts = self._load_alerts()
        return [a for a in alerts if a.is_active()]

    def get_status_summary(self) -> str:
        """
        Get human-readable status summary.

        Used by CLI status command and COO reports.
        """
        metrics = self._load_metrics()
        alerts = self.get_active_alerts()

        if not metrics:
            return "No metrics available"

        healthy_count = sum(
            1 for a in metrics.agents.values()
            if a.health == HealthState.HEALTHY
        )
        total_agents = len(metrics.agents)

        critical_count = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        warning_count = len([a for a in alerts if a.severity == AlertSeverity.WARNING])

        if critical_count > 0:
            status_icon = "CRITICAL"
            return f"{status_icon} | {critical_count} critical, {warning_count} warnings | {healthy_count}/{total_agents} agents healthy"
        elif warning_count > 0:
            status_icon = "WARNING"
            return f"{status_icon} | {warning_count} warnings | {healthy_count}/{total_agents} agents healthy"
        else:
            status_icon = "OPERATIONAL"
            return f"{status_icon} | All systems healthy | {healthy_count}/{total_agents} agents"

    def _assess_agent_health(
        self,
        agent_id: str,
        last_heartbeat: Optional[str]
    ) -> HealthState:
        """Assess agent health based on heartbeat timestamp"""
        if not last_heartbeat:
            return HealthState.UNKNOWN

        try:
            heartbeat_time = datetime.fromisoformat(last_heartbeat)
            age_seconds = (datetime.utcnow() - heartbeat_time).total_seconds()

            if age_seconds > self.thresholds['heartbeat_critical']:
                return HealthState.UNRESPONSIVE
            elif age_seconds > self.thresholds['heartbeat_warning']:
                return HealthState.SLOW
            else:
                return HealthState.HEALTHY
        except Exception:
            return HealthState.UNKNOWN

    def _get_department(self, agent_id: str) -> str:
        """Determine department from agent_id naming convention"""
        if 'engineering' in agent_id:
            return 'engineering'
        elif 'product' in agent_id:
            return 'product'
        elif 'quality' in agent_id:
            return 'quality'
        elif 'research' in agent_id:
            return 'research'
        elif 'operations' in agent_id:
            return 'operations'
        elif 'coo' in agent_id:
            return 'executive'
        else:
            return 'unknown'

    def _get_recent_errors_from_beads(self) -> List[str]:
        """Get recent errors from bead entries"""
        errors = []
        if self.bead_ledger:
            try:
                # Get recent entries with 'error' or 'fail' actions
                entries = self.bead_ledger.list_entries()
                for entry in entries[-20:]:  # Last 20 entries
                    if entry.action in ['error', 'fail', 'failed']:
                        errors.append(f"{entry.entity_type}:{entry.entity_id} - {entry.message}")
            except Exception:
                pass
        return errors[-5:]  # Return last 5

    def _record_alert_bead(self, alert: HealthAlert) -> None:
        """Record an alert as a bead entry for audit trail"""
        if self.bead_ledger:
            self._record_bead(
                action='alert',
                entity_type='alert',
                entity_id=alert.id,
                data=alert.to_dict(),
                message=f"[{alert.severity.value.upper()}] {alert.message}",
                agent_id='system_monitor'
            )

    def _record_bead(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        message: str,
        agent_id: str = "system"
    ) -> None:
        """Record an entry in the bead ledger"""
        if self.bead_ledger:
            # Handle both Bead and BeadLedger types
            if hasattr(self.bead_ledger, 'agent_id'):
                # This is a Bead instance
                self.bead_ledger.record(
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    data=data,
                    message=message
                )
            else:
                # This is a BeadLedger instance
                self.bead_ledger.record(
                    agent_id=agent_id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    data=data,
                    message=message
                )

    def _broadcast_alert(self, alert: HealthAlert) -> None:
        """Broadcast alert via channel system"""
        if self.channel_manager:
            from .channel import MessagePriority

            try:
                self.channel_manager.broadcast(
                    content={
                        'type': 'health_alert',
                        'alert_id': alert.id,
                        'severity': alert.severity.value,
                        'component': alert.component,
                        'message': alert.message,
                        'suggested_action': alert.suggested_action
                    },
                    sender_id='system_monitor',
                    priority=MessagePriority.HIGH if alert.severity == AlertSeverity.CRITICAL else MessagePriority.NORMAL
                )
            except Exception:
                pass  # Don't fail monitoring if broadcast fails

    # File operations

    def _save_metrics(self, metrics: SystemMetrics) -> None:
        """Save metrics to disk"""
        self.metrics_file.write_text(metrics.to_yaml())

    def _load_metrics(self) -> Optional[SystemMetrics]:
        """Load metrics from disk"""
        if not self.metrics_file.exists():
            return None
        try:
            return SystemMetrics.from_yaml(self.metrics_file.read_text())
        except Exception:
            return None

    def _save_alerts(self, alerts: List[HealthAlert]) -> None:
        """Save alerts to disk"""
        data = [a.to_dict() for a in alerts]
        self.alerts_file.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False)
        )

    def _load_alerts(self) -> List[HealthAlert]:
        """Load alerts from disk"""
        if not self.alerts_file.exists():
            return []
        try:
            data = yaml.safe_load(self.alerts_file.read_text())
            if not data:
                return []
            return [HealthAlert.from_dict(a) for a in data]
        except Exception:
            return []

    def _save_heartbeats(self, heartbeats: Dict[str, str]) -> None:
        """Save heartbeats to disk"""
        self.heartbeats_file.write_text(
            yaml.dump(heartbeats, default_flow_style=False, sort_keys=False)
        )

    def _load_heartbeats(self) -> Dict[str, str]:
        """Load heartbeats from disk"""
        if not self.heartbeats_file.exists():
            return {}
        try:
            data = yaml.safe_load(self.heartbeats_file.read_text())
            return data if data else {}
        except Exception:
            return {}
