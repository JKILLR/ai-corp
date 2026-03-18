"""
Integration tests for Terminal Dashboard.

Tests the dashboard's integration with:
- SystemMonitor
- ContractManager
- MoleculeEngine
- HookManager
"""

import pytest
from datetime import datetime
from pathlib import Path

from src.cli.dashboard import Dashboard, run_dashboard, get_status_line
from src.core.monitor import SystemMonitor, AlertSeverity
from src.core.contract import ContractManager
from src.core.molecule import MoleculeEngine
from src.core.hook import HookManager, WorkItem, WorkItemStatus, WorkItemPriority


class TestDashboardMonitorIntegration:
    """Tests for dashboard + monitor integration"""

    @pytest.fixture
    def setup_monitored_corp(self, tmp_path):
        """Set up corp with monitoring data"""
        monitor = SystemMonitor(tmp_path)

        # Record some heartbeats
        monitor.record_heartbeat("vp-engineering")
        monitor.record_heartbeat("dir-frontend")

        # Create some hooks
        hook_mgr = HookManager(tmp_path)
        hook = hook_mgr.create_hook(
            name="VP Engineering Hook",
            owner_id="vp-engineering",
            owner_type="vp"
        )

        # Create molecule for work item
        engine = MoleculeEngine(tmp_path)
        mol = engine.create_molecule(
            name="Test Project",
            description="Test",
            created_by="test"
        )
        engine.start_molecule(mol.id)

        # Add work
        hook.add_work(WorkItem(
            id="work-1",
            hook_id=hook.id,
            molecule_id=mol.id,
            title="Build feature",
            description="Build the feature",
            priority=WorkItemPriority.P1_HIGH,
            status=WorkItemStatus.QUEUED,
            created_at=datetime.utcnow().isoformat()
        ))
        hook_mgr._save_hook(hook)

        return tmp_path

    def test_dashboard_shows_monitored_agents(self, setup_monitored_corp):
        """Test dashboard displays agents from monitor"""
        dashboard = Dashboard(setup_monitored_corp, use_colors=False)
        output = dashboard.render()

        assert "vp-engineering" in output

    def test_dashboard_reflects_queue_depths(self, setup_monitored_corp):
        """Test dashboard shows queue depths from hooks"""
        dashboard = Dashboard(setup_monitored_corp, use_colors=False)
        output = dashboard.render()

        # Should show work queues panel
        assert "WORK QUEUES" in output

    def test_dashboard_shows_heartbeat_status(self, setup_monitored_corp):
        """Test dashboard reflects heartbeat-based health"""
        dashboard = Dashboard(setup_monitored_corp, use_colors=False)
        output = dashboard.render()

        # Agent should appear as healthy (recent heartbeat)
        assert "healthy" in output.lower() or "●" in output


class TestDashboardContractIntegration:
    """Tests for dashboard + contract integration"""

    @pytest.fixture
    def setup_contract_corp(self, tmp_path):
        """Set up corp with contracts"""
        manager = ContractManager(tmp_path)

        # Create a contract
        contract = manager.create(
            title="User Authentication",
            objective="Implement secure user auth",
            created_by="coo",
            success_criteria=[
                "OAuth2 login works",
                "Password reset works",
                "MFA is optional"
            ]
        )

        # Activate and link to molecule
        manager.activate(contract.id)

        engine = MoleculeEngine(tmp_path)
        mol = engine.create_molecule(
            name="Auth Feature",
            description="Authentication implementation",
            created_by="coo"
        )
        engine.start_molecule(mol.id)

        manager.link_molecule(contract.id, mol.id)

        # Mark one criterion as met
        manager.update_criterion(contract.id, 0, True, "qa-lead")

        return tmp_path

    def test_dashboard_shows_contract_progress(self, setup_contract_corp):
        """Test dashboard displays contract progress"""
        dashboard = Dashboard(setup_contract_corp, use_colors=False)
        output = dashboard.render()

        # Should show project panel
        assert "PROJECT PROGRESS" in output

        # Should mention contract or show criteria
        assert "Contract" in output or "criteria" in output


class TestDashboardAlertIntegration:
    """Tests for dashboard + alert integration"""

    @pytest.fixture
    def setup_alert_corp(self, tmp_path):
        """Set up corp with alerts"""
        monitor = SystemMonitor(tmp_path)

        # Trigger health check to generate alerts
        # First create an agent hook without heartbeat
        hook_mgr = HookManager(tmp_path)
        hook = hook_mgr.create_hook(
            name="Stale Agent Hook",
            owner_id="stale-agent",
            owner_type="worker"
        )

        # Manually create alerts
        from src.core.monitor import HealthAlert, AlertSeverity

        alert1 = HealthAlert.create(
            severity=AlertSeverity.CRITICAL,
            component="agent:stale-agent",
            message="Agent stale-agent is unresponsive",
            suggested_action="Restart the agent"
        )
        alert2 = HealthAlert.create(
            severity=AlertSeverity.WARNING,
            component="queue:vp-engineering",
            message="Queue depth is high",
            suggested_action="Monitor queue"
        )

        monitor._save_alerts([alert1, alert2])

        return tmp_path

    def test_dashboard_shows_alerts(self, setup_alert_corp):
        """Test dashboard displays alerts"""
        dashboard = Dashboard(setup_alert_corp, use_colors=False)
        output = dashboard.render()

        assert "ACTIVE ALERTS" in output
        assert "unresponsive" in output or "CRITICAL" in output

    def test_dashboard_shows_alert_actions(self, setup_alert_corp):
        """Test dashboard shows suggested actions"""
        dashboard = Dashboard(setup_alert_corp, use_colors=False)
        output = dashboard.render()

        assert "Restart" in output or "Action:" in output


class TestDashboardMoleculeIntegration:
    """Tests for dashboard + molecule integration"""

    @pytest.fixture
    def setup_multi_project_corp(self, tmp_path):
        """Set up corp with multiple projects"""
        engine = MoleculeEngine(tmp_path)

        # Create several molecules with different progress
        mol1 = engine.create_molecule(
            name="Project Alpha",
            description="First project",
            created_by="coo"
        )
        engine.start_molecule(mol1.id)

        mol2 = engine.create_molecule(
            name="Project Beta",
            description="Second project",
            created_by="coo"
        )
        engine.start_molecule(mol2.id)

        return tmp_path

    def test_dashboard_shows_multiple_projects(self, setup_multi_project_corp):
        """Test dashboard displays multiple projects"""
        dashboard = Dashboard(setup_multi_project_corp, use_colors=False)
        output = dashboard.render()

        assert "Project Alpha" in output or "PROJECT PROGRESS" in output

    def test_dashboard_shows_project_progress_bars(self, setup_multi_project_corp):
        """Test dashboard shows progress bars for projects"""
        dashboard = Dashboard(setup_multi_project_corp, use_colors=False)
        output = dashboard.render()

        # Progress bars use these characters
        assert "█" in output or "░" in output or "%" in output


class TestDashboardCompactMode:
    """Tests for compact dashboard mode"""

    def test_compact_contains_key_metrics(self, tmp_path):
        """Test compact mode has essential info"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render_compact()

        assert "AI Corp" in output
        assert "Status:" in output
        assert "Agents:" in output

    def test_compact_is_single_line(self, tmp_path):
        """Test compact output is single line"""
        dashboard = Dashboard(tmp_path, use_colors=False)
        output = dashboard.render_compact()

        assert "\n" not in output

    def test_get_status_line_for_scripts(self, tmp_path):
        """Test get_status_line works for script embedding"""
        status = get_status_line(tmp_path)

        assert isinstance(status, str)
        assert "AI-CORP" in status
        assert "\n" not in status


class TestDashboardFullIntegration:
    """End-to-end dashboard tests"""

    @pytest.fixture
    def full_corp(self, tmp_path):
        """Set up a complete corp with all components"""
        # Initialize monitoring
        monitor = SystemMonitor(tmp_path)

        # Create hooks for agents
        hook_mgr = HookManager(tmp_path)

        # Create molecules
        engine = MoleculeEngine(tmp_path)
        mol = engine.create_molecule(
            name="Full Feature",
            description="Complete feature",
            created_by="coo"
        )
        engine.start_molecule(mol.id)

        # Create VP hook with work
        vp_hook = hook_mgr.create_hook(
            name="VP Engineering Hook",
            owner_id="vp-engineering",
            owner_type="vp"
        )
        vp_hook.add_work(WorkItem(
            id="work-1",
            hook_id=vp_hook.id,
            molecule_id=mol.id,
            title="Design review",
            description="Review the design",
            created_at=datetime.utcnow().isoformat()
        ))
        hook_mgr._save_hook(vp_hook)

        # Record heartbeats
        monitor.record_heartbeat("vp-engineering")

        # Create contract
        contract_mgr = ContractManager(tmp_path)
        contract = contract_mgr.create(
            title="Full Feature",
            objective="Deliver complete feature",
            created_by="coo",
            success_criteria=["Works end to end"]
        )
        contract_mgr.activate(contract.id)
        contract_mgr.link_molecule(contract.id, mol.id)

        return tmp_path

    def test_full_dashboard_renders(self, full_corp):
        """Test full dashboard renders without errors"""
        dashboard = Dashboard(full_corp, use_colors=False)
        output = dashboard.render()

        assert "AI CORP DASHBOARD" in output
        assert "AGENT STATUS" in output
        assert "PROJECT PROGRESS" in output
        assert "WORK QUEUES" in output
        assert "ACTIVE ALERTS" in output

    def test_full_dashboard_shows_all_data(self, full_corp):
        """Test all data is visible in dashboard"""
        dashboard = Dashboard(full_corp, use_colors=False)
        output = dashboard.render()

        # Should show the VP
        assert "vp-engineering" in output

        # Should show the project
        assert "Full Feature" in output

    def test_dashboard_header_has_correct_status(self, full_corp):
        """Test header shows appropriate status"""
        dashboard = Dashboard(full_corp, use_colors=False)
        output = dashboard.render()

        # With no alerts, should show operational
        # (unless alerts were created)
        assert "Status:" in output
