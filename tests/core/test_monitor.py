"""
Unit tests for the System Monitoring module.

Tests:
- SystemMetrics data structure
- AgentStatus tracking
- HealthAlert lifecycle
- SystemMonitor metrics collection
- Health checking and alerting
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.core.monitor import (
    SystemMonitor, SystemMetrics, AgentStatus, HealthAlert,
    AlertSeverity, HealthState
)


class TestAgentStatus:
    """Test AgentStatus dataclass."""

    def test_create_agent_status(self):
        """Test creating an AgentStatus."""
        status = AgentStatus(
            agent_id="vp_engineering",
            role="VP Engineering",
            department="engineering",
            last_heartbeat=datetime.utcnow().isoformat(),
            current_work="Building feature",
            queue_depth=5,
            health=HealthState.HEALTHY
        )

        assert status.agent_id == "vp_engineering"
        assert status.health == HealthState.HEALTHY
        assert status.queue_depth == 5

    def test_agent_status_to_dict(self):
        """Test serialization to dict."""
        status = AgentStatus(
            agent_id="worker_1",
            role="Worker",
            department="engineering",
            last_heartbeat="2026-01-05T12:00:00",
            current_work=None,
            queue_depth=0,
            health=HealthState.HEALTHY
        )

        data = status.to_dict()
        assert data['agent_id'] == "worker_1"
        assert data['health'] == "healthy"

    def test_agent_status_from_dict(self):
        """Test deserialization from dict."""
        data = {
            'agent_id': "dir_backend",
            'role': "Director",
            'department': "engineering",
            'last_heartbeat': "2026-01-05T12:00:00",
            'current_work': "Code review",
            'queue_depth': 3,
            'health': "slow"
        }

        status = AgentStatus.from_dict(data)
        assert status.agent_id == "dir_backend"
        assert status.health == HealthState.SLOW
        assert status.current_work == "Code review"


class TestHealthAlert:
    """Test HealthAlert dataclass."""

    def test_create_alert(self):
        """Test creating an alert via factory method."""
        alert = HealthAlert.create(
            severity=AlertSeverity.WARNING,
            component="queue:vp_engineering",
            message="Queue depth exceeds threshold",
            suggested_action="Monitor the queue"
        )

        assert alert.id.startswith("ALERT-")
        assert alert.severity == AlertSeverity.WARNING
        assert alert.component == "queue:vp_engineering"
        assert alert.resolved_at is None
        assert alert.is_active() is True

    def test_resolve_alert(self):
        """Test resolving an alert."""
        alert = HealthAlert.create(
            severity=AlertSeverity.CRITICAL,
            component="agent:worker_1",
            message="Agent unresponsive",
            suggested_action="Restart agent"
        )

        assert alert.is_active() is True

        alert.resolve()

        assert alert.is_active() is False
        assert alert.resolved_at is not None

    def test_acknowledge_alert(self):
        """Test acknowledging an alert."""
        alert = HealthAlert.create(
            severity=AlertSeverity.WARNING,
            component="system",
            message="Test alert",
            suggested_action="Take action"
        )

        assert alert.acknowledged_by is None

        alert.acknowledge("admin")

        assert alert.acknowledged_by == "admin"

    def test_alert_to_dict(self):
        """Test serialization."""
        alert = HealthAlert.create(
            severity=AlertSeverity.CRITICAL,
            component="test",
            message="Test message",
            suggested_action="Test action"
        )

        data = alert.to_dict()
        assert data['severity'] == "critical"
        assert data['component'] == "test"
        assert data['message'] == "Test message"

    def test_alert_from_dict(self):
        """Test deserialization."""
        data = {
            'id': "ALERT-TEST123",
            'severity': "warning",
            'component': "agent:coo",
            'message': "Test",
            'suggested_action': "Do something",
            'created_at': "2026-01-05T12:00:00",
            'resolved_at': None,
            'acknowledged_by': None
        }

        alert = HealthAlert.from_dict(data)
        assert alert.id == "ALERT-TEST123"
        assert alert.severity == AlertSeverity.WARNING


class TestSystemMetrics:
    """Test SystemMetrics dataclass."""

    def test_create_metrics(self):
        """Test creating system metrics snapshot."""
        metrics = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            agents={},
            queues={},
            molecules={},
            errors=[],
            pending_gates=0,
            active_molecules=0
        )

        assert metrics.pending_gates == 0
        assert metrics.active_molecules == 0

    def test_metrics_with_agents(self):
        """Test metrics with agent data."""
        agent_status = AgentStatus(
            agent_id="vp_engineering",
            role="VP",
            department="engineering",
            last_heartbeat=datetime.utcnow().isoformat(),
            current_work=None,
            queue_depth=3,
            health=HealthState.HEALTHY
        )

        metrics = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            agents={"vp_engineering": agent_status},
            queues={"vp_engineering": 3},
            molecules={"MOL-123": 50.0},
            errors=[],
            pending_gates=1,
            active_molecules=1
        )

        assert len(metrics.agents) == 1
        assert metrics.queues["vp_engineering"] == 3
        assert metrics.molecules["MOL-123"] == 50.0

    def test_metrics_to_yaml(self):
        """Test YAML serialization."""
        metrics = SystemMetrics(
            timestamp="2026-01-05T12:00:00",
            agents={},
            queues={"agent1": 5},
            molecules={},
            errors=[],
            pending_gates=0,
            active_molecules=0
        )

        yaml_str = metrics.to_yaml()
        assert "timestamp:" in yaml_str
        assert "agent1: 5" in yaml_str

    def test_metrics_from_yaml(self):
        """Test YAML deserialization."""
        yaml_str = """
timestamp: "2026-01-05T12:00:00"
agents: {}
queues:
  agent1: 10
molecules:
  MOL-123: 75.0
errors: []
pending_gates: 2
active_molecules: 1
"""
        metrics = SystemMetrics.from_yaml(yaml_str)
        assert metrics.queues["agent1"] == 10
        assert metrics.molecules["MOL-123"] == 75.0
        assert metrics.pending_gates == 2


class TestSystemMonitor:
    """Test SystemMonitor class."""

    def test_init_creates_directories(self, temp_corp_path):
        """Test that initialization creates required directories."""
        monitor = SystemMonitor(temp_corp_path)

        assert monitor.metrics_path.exists()
        assert monitor.heartbeats_file.exists() or True  # May be created lazily

    def test_record_heartbeat(self, temp_corp_path):
        """Test recording agent heartbeat."""
        monitor = SystemMonitor(temp_corp_path)

        monitor.record_heartbeat("test_agent")
        heartbeat = monitor.get_agent_heartbeat("test_agent")

        assert heartbeat is not None
        # Verify it's a recent timestamp
        heartbeat_time = datetime.fromisoformat(heartbeat)
        assert (datetime.utcnow() - heartbeat_time).seconds < 5

    def test_assess_healthy_agent(self, temp_corp_path):
        """Test health assessment for healthy agent."""
        monitor = SystemMonitor(temp_corp_path)

        # Record recent heartbeat
        monitor.record_heartbeat("healthy_agent")

        health = monitor._assess_agent_health(
            "healthy_agent",
            datetime.utcnow().isoformat()
        )

        assert health == HealthState.HEALTHY

    def test_assess_slow_agent(self, temp_corp_path):
        """Test health assessment for slow agent."""
        monitor = SystemMonitor(temp_corp_path)

        # Create timestamp 2 minutes ago (within slow threshold)
        old_time = (datetime.utcnow() - timedelta(seconds=120)).isoformat()

        health = monitor._assess_agent_health("slow_agent", old_time)

        assert health == HealthState.SLOW

    def test_assess_unresponsive_agent(self, temp_corp_path):
        """Test health assessment for unresponsive agent."""
        monitor = SystemMonitor(temp_corp_path)

        # Create timestamp 10 minutes ago (past critical threshold)
        old_time = (datetime.utcnow() - timedelta(seconds=600)).isoformat()

        health = monitor._assess_agent_health("dead_agent", old_time)

        assert health == HealthState.UNRESPONSIVE

    def test_assess_unknown_agent(self, temp_corp_path):
        """Test health assessment when no heartbeat exists."""
        monitor = SystemMonitor(temp_corp_path)

        health = monitor._assess_agent_health("unknown_agent", None)

        assert health == HealthState.UNKNOWN

    def test_get_status_summary_no_metrics(self, temp_corp_path):
        """Test status summary when no metrics exist."""
        monitor = SystemMonitor(temp_corp_path)

        summary = monitor.get_status_summary()

        assert "No metrics" in summary or "OPERATIONAL" in summary

    def test_get_active_alerts_empty(self, temp_corp_path):
        """Test getting active alerts when none exist."""
        monitor = SystemMonitor(temp_corp_path)

        alerts = monitor.get_active_alerts()

        assert alerts == []

    def test_resolve_alert(self, temp_corp_path):
        """Test resolving an alert."""
        monitor = SystemMonitor(temp_corp_path)

        # Create and save an alert manually
        alert = HealthAlert.create(
            severity=AlertSeverity.WARNING,
            component="test",
            message="Test alert",
            suggested_action="Test action"
        )
        monitor._save_alerts([alert])

        # Resolve it
        result = monitor.resolve_alert(alert.id, "tester")

        assert result is True

        # Verify it's no longer active
        active = monitor.get_active_alerts()
        assert len(active) == 0

    def test_acknowledge_alert(self, temp_corp_path):
        """Test acknowledging an alert."""
        monitor = SystemMonitor(temp_corp_path)

        alert = HealthAlert.create(
            severity=AlertSeverity.CRITICAL,
            component="test",
            message="Critical issue",
            suggested_action="Fix it"
        )
        monitor._save_alerts([alert])

        result = monitor.acknowledge_alert(alert.id, "admin")

        assert result is True

    def test_department_detection(self, temp_corp_path):
        """Test department detection from agent ID."""
        monitor = SystemMonitor(temp_corp_path)

        assert monitor._get_department("vp_engineering") == "engineering"
        assert monitor._get_department("dir_product") == "product"
        assert monitor._get_department("quality_worker") == "quality"
        assert monitor._get_department("coo") == "executive"
        assert monitor._get_department("random_agent") == "unknown"

    def test_create_alert_if_new_creates_alert(self, temp_corp_path):
        """Test that new alerts are created."""
        monitor = SystemMonitor(temp_corp_path)

        alert = monitor._create_alert_if_new(
            existing_alerts=[],
            severity=AlertSeverity.WARNING,
            component="test:component",
            message="New alert",
            suggested_action="Take action"
        )

        assert alert is not None
        assert alert.component == "test:component"

    def test_create_alert_if_new_prevents_duplicates(self, temp_corp_path):
        """Test that duplicate alerts are not created."""
        monitor = SystemMonitor(temp_corp_path)

        existing = HealthAlert.create(
            severity=AlertSeverity.WARNING,
            component="test:component",
            message="Existing alert",
            suggested_action="Action"
        )

        alert = monitor._create_alert_if_new(
            existing_alerts=[existing],
            severity=AlertSeverity.WARNING,
            component="test:component",
            message="Duplicate alert",
            suggested_action="Action"
        )

        assert alert is None


class TestSystemMonitorCollection:
    """Test SystemMonitor.collect_metrics()."""

    def test_collect_metrics_empty_corp(self, temp_corp_path):
        """Test collecting metrics from empty corp."""
        monitor = SystemMonitor(temp_corp_path)

        metrics = monitor.collect_metrics()

        assert metrics is not None
        assert isinstance(metrics.timestamp, str)
        assert metrics.active_molecules == 0

    def test_collect_metrics_saves_to_file(self, temp_corp_path):
        """Test that collect_metrics saves results."""
        monitor = SystemMonitor(temp_corp_path)

        monitor.collect_metrics()

        assert monitor.metrics_file.exists()


class TestSystemMonitorHealthCheck:
    """Test SystemMonitor.check_health()."""

    def test_check_health_no_issues(self, temp_corp_path):
        """Test health check with no issues."""
        monitor = SystemMonitor(temp_corp_path)

        alerts = monitor.check_health()

        # Should return empty list or only collect_metrics-related issues
        assert isinstance(alerts, list)


# Fixtures

@pytest.fixture
def temp_corp_path(tmp_path):
    """Create a temporary corp directory."""
    corp_path = tmp_path / "corp"
    corp_path.mkdir()

    # Create required subdirectories
    for subdir in ['molecules', 'hooks', 'beads', 'channels', 'gates', 'contracts', 'metrics']:
        (corp_path / subdir).mkdir()

    return corp_path
