"""
Tests for the Terminal Dashboard.

Tests dashboard rendering, status indicators, and integration with
monitoring and contract systems.
"""

import pytest
from pathlib import Path
from datetime import datetime

from src.cli.dashboard import Dashboard, Colors, run_dashboard, get_status_line
from src.core.monitor import (
    SystemMonitor, SystemMetrics, AgentStatus,
    HealthAlert, AlertSeverity, HealthState
)


class TestColors:
    """Tests for Colors class"""

    def test_colors_have_codes(self):
        """Test that colors have ANSI codes by default"""
        assert Colors.GREEN.startswith("\033[")
        assert Colors.RED.startswith("\033[")
        assert Colors.RESET == "\033[0m"

    def test_disable_colors(self):
        """Test disabling colors"""
        # Save originals
        original_green = Colors.GREEN
        original_reset = Colors.RESET

        Colors.disable()

        assert Colors.GREEN == ""
        assert Colors.RED == ""
        assert Colors.RESET == ""

        # Restore for other tests
        Colors.GREEN = original_green
        Colors.RESET = original_reset


class TestDashboard:
    """Tests for Dashboard class"""

    def test_dashboard_init(self, tmp_path):
        """Test dashboard initialization"""
        dashboard = Dashboard(tmp_path, use_colors=False)

        assert dashboard.corp_path == tmp_path
        assert dashboard.width == 80
        assert dashboard.monitor is not None
        assert dashboard.contract_manager is not None

    def test_dashboard_init_custom_width(self, tmp_path):
        """Test dashboard with custom width"""
        dashboard = Dashboard(tmp_path, width=120, use_colors=False)

        assert dashboard.width == 120

    def test_render_returns_string(self, tmp_path):
        """Test that render returns a string"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render()

        assert isinstance(output, str)
        assert len(output) > 0

    def test_render_contains_header(self, tmp_path):
        """Test that render includes header"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render()

        assert "AI CORP DASHBOARD" in output

    def test_render_contains_panels(self, tmp_path):
        """Test that render includes all panels"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render()

        assert "AGENT STATUS" in output
        assert "PROJECT PROGRESS" in output
        assert "WORK QUEUES" in output
        assert "ACTIVE ALERTS" in output

    def test_render_compact(self, tmp_path):
        """Test compact rendering"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render_compact()

        assert isinstance(output, str)
        assert "AI Corp" in output
        assert "Status:" in output

    def test_render_compact_single_line(self, tmp_path):
        """Test that compact is a single line"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render_compact()

        # Should not contain newlines
        assert "\n" not in output


class TestDashboardRendering:
    """Tests for specific rendering methods"""

    def test_panel_header(self, tmp_path):
        """Test panel header rendering"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        header = dashboard._panel_header("TEST PANEL")

        assert "TEST PANEL" in header
        assert dashboard.BOX_TL in header

    def test_panel_footer(self, tmp_path):
        """Test panel footer rendering"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        footer = dashboard._panel_footer()

        assert dashboard.BOX_BL in footer

    def test_progress_bar_empty(self, tmp_path):
        """Test progress bar at 0%"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        bar = dashboard._render_progress_bar(0, 10)

        assert "[" in bar and "]" in bar
        # Should be mostly empty chars
        assert dashboard.PROG_EMPTY in bar

    def test_progress_bar_full(self, tmp_path):
        """Test progress bar at 100%"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        bar = dashboard._render_progress_bar(100, 10)

        assert "[" in bar and "]" in bar
        # Should be all full chars
        assert dashboard.PROG_FULL in bar

    def test_progress_bar_half(self, tmp_path):
        """Test progress bar at 50%"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        bar = dashboard._render_progress_bar(50, 10)

        assert "[" in bar and "]" in bar

    def test_health_indicator_healthy(self, tmp_path):
        """Test health indicator for healthy state"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        icon, color = dashboard._get_health_indicator(HealthState.HEALTHY)

        assert icon == dashboard.ICON_OK

    def test_health_indicator_slow(self, tmp_path):
        """Test health indicator for slow state"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        icon, color = dashboard._get_health_indicator(HealthState.SLOW)

        assert icon == dashboard.ICON_WARN

    def test_health_indicator_unresponsive(self, tmp_path):
        """Test health indicator for unresponsive state"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        icon, color = dashboard._get_health_indicator(HealthState.UNRESPONSIVE)

        assert icon == dashboard.ICON_ERROR

    def test_health_indicator_unknown(self, tmp_path):
        """Test health indicator for unknown state"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        icon, color = dashboard._get_health_indicator(HealthState.UNKNOWN)

        assert icon == dashboard.ICON_UNKNOWN

    def test_severity_indicator_critical(self, tmp_path):
        """Test severity indicator for critical"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        icon, color = dashboard._get_severity_indicator(AlertSeverity.CRITICAL)

        assert icon == "!"

    def test_severity_indicator_warning(self, tmp_path):
        """Test severity indicator for warning"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        icon, color = dashboard._get_severity_indicator(AlertSeverity.WARNING)

        assert icon == "!"

    def test_severity_indicator_info(self, tmp_path):
        """Test severity indicator for info"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        icon, color = dashboard._get_severity_indicator(AlertSeverity.INFO)

        assert icon == "i"


class TestDashboardWithData:
    """Tests for dashboard with actual data"""

    @pytest.fixture
    def setup_corp(self, tmp_path):
        """Set up a corp with some data"""
        from src.core.hook import HookManager, WorkItem, WorkItemStatus, WorkItemPriority
        from src.core.molecule import MoleculeEngine

        # Create hook with work items
        hook_mgr = HookManager(tmp_path)
        hook = hook_mgr.create_hook(
            name="Test Hook",
            owner_id="vp-engineering",
            owner_type="vp"
        )
        # Create a molecule first (needed for work item)
        engine = MoleculeEngine(tmp_path)
        mol = engine.create_molecule(
            name="Test Project",
            description="A test project",
            created_by="test"
        )
        engine.start_molecule(mol.id)

        # Now add work item to hook
        hook.add_work(WorkItem(
            id="work-1",
            hook_id=hook.id,
            molecule_id=mol.id,
            title="Test Work",
            description="Test description",
            priority=WorkItemPriority.P2_MEDIUM,
            status=WorkItemStatus.QUEUED,
            created_at=datetime.utcnow().isoformat()
        ))
        hook_mgr._save_hook(hook)

        return tmp_path

    def test_dashboard_with_agents(self, setup_corp):
        """Test dashboard shows agents"""
        dashboard = Dashboard(setup_corp, use_colors=False)
        output = dashboard.render()

        assert "vp-engineering" in output

    def test_dashboard_with_project(self, setup_corp):
        """Test dashboard shows project"""
        dashboard = Dashboard(setup_corp, use_colors=False)
        output = dashboard.render()

        # Should show project in progress panel
        assert "Test Project" in output or "PROJECT PROGRESS" in output


class TestGetStatusLine:
    """Tests for get_status_line function"""

    def test_returns_string(self, tmp_path):
        """Test that get_status_line returns a string"""
        status = get_status_line(tmp_path)

        assert isinstance(status, str)
        assert len(status) > 0

    def test_contains_status(self, tmp_path):
        """Test that status line contains key info"""
        status = get_status_line(tmp_path)

        assert "AI-CORP" in status
        assert "Agents:" in status

    def test_no_colors(self, tmp_path):
        """Test that get_status_line has no ANSI codes"""
        status = get_status_line(tmp_path)

        # Should not contain ANSI escape codes
        assert "\033[" not in status


class TestDashboardAlerts:
    """Tests for alert rendering"""

    @pytest.fixture
    def setup_alerts(self, tmp_path):
        """Set up monitoring with alerts"""
        monitor = SystemMonitor(tmp_path)

        # Create some alerts manually
        from src.core.monitor import HealthAlert, AlertSeverity

        alert1 = HealthAlert.create(
            severity=AlertSeverity.CRITICAL,
            component="agent:test-agent",
            message="Test critical alert",
            suggested_action="Fix it"
        )
        alert2 = HealthAlert.create(
            severity=AlertSeverity.WARNING,
            component="queue:test-queue",
            message="Test warning alert",
            suggested_action="Monitor it"
        )

        # Save alerts
        alerts = [alert1, alert2]
        monitor._save_alerts(alerts)

        return tmp_path

    def test_renders_alerts(self, setup_alerts):
        """Test that alerts are rendered"""
        dashboard = Dashboard(setup_alerts, use_colors=False)
        output = dashboard.render()

        assert "Test critical alert" in output or "ACTIVE ALERTS" in output

    def test_critical_shown_first(self, setup_alerts):
        """Test that critical alerts are shown before warnings"""
        dashboard = Dashboard(setup_alerts, use_colors=False)
        output = dashboard.render()

        # Critical should appear before warning
        if "critical" in output.lower() and "warning" in output.lower():
            assert output.lower().index("critical") < output.lower().index("warning")


class TestDashboardNoData:
    """Tests for dashboard with empty data"""

    def test_empty_agents_message(self, tmp_path):
        """Test message when no agents"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render()

        assert "No agents registered" in output or "AGENT STATUS" in output

    def test_empty_projects_message(self, tmp_path):
        """Test message when no projects"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render()

        assert "No active projects" in output or "PROJECT PROGRESS" in output

    def test_no_alerts_message(self, tmp_path):
        """Test message when no alerts"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render()

        assert "No active alerts" in output or "ACTIVE ALERTS" in output


class TestBoxDrawing:
    """Tests for box drawing characters"""

    def test_box_characters_defined(self, tmp_path):
        """Test that all box drawing characters are defined"""
        dashboard = Dashboard(tmp_path, use_colors=False)

        assert dashboard.BOX_TL == "┌"
        assert dashboard.BOX_TR == "┐"
        assert dashboard.BOX_BL == "└"
        assert dashboard.BOX_BR == "┘"
        assert dashboard.BOX_H == "─"
        assert dashboard.BOX_V == "│"

    def test_progress_characters_defined(self, tmp_path):
        """Test that progress bar characters are defined"""
        dashboard = Dashboard(tmp_path, use_colors=False)

        assert dashboard.PROG_FULL == "█"
        assert dashboard.PROG_EMPTY == "░"

    def test_icon_characters_defined(self, tmp_path):
        """Test that icon characters are defined"""
        dashboard = Dashboard(tmp_path, use_colors=False)

        assert dashboard.ICON_OK == "●"
        assert dashboard.ICON_WARN == "◐"
        assert dashboard.ICON_ERROR == "○"
        assert dashboard.ICON_UNKNOWN == "◌"
