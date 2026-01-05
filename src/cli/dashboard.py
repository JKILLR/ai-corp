"""
Terminal Dashboard for AI Corp

Provides a rich terminal-based view of system status including:
- System health summary
- Agent status with heartbeat indicators
- Project progress with visual progress bars
- Work queue depths
- Active alerts with severity indicators
- Contract progress tracking

Supports both static view and live refresh modes.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from ..core.monitor import (
    SystemMonitor, SystemMetrics, AgentStatus,
    HealthAlert, AlertSeverity, HealthState
)
from ..core.contract import ContractManager, ContractStatus
from ..core.molecule import MoleculeEngine
from ..core.skills import SkillRegistry, CAPABILITY_SKILL_MAP
from ..core.scheduler import WorkScheduler


class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Status colors
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"

    # Background colors
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_GREEN = "\033[42m"

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)"""
        cls.RESET = ""
        cls.BOLD = ""
        cls.DIM = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.RED = ""
        cls.BLUE = ""
        cls.CYAN = ""
        cls.MAGENTA = ""
        cls.WHITE = ""
        cls.BG_RED = ""
        cls.BG_YELLOW = ""
        cls.BG_GREEN = ""


class Dashboard:
    """
    Terminal dashboard for AI Corp system monitoring.

    Provides real-time visibility into:
    - Overall system health
    - Agent status and heartbeats
    - Project/molecule progress
    - Work queue depths
    - Active alerts
    - Contract progress
    """

    # Box drawing characters
    BOX_TL = "┌"
    BOX_TR = "┐"
    BOX_BL = "└"
    BOX_BR = "┘"
    BOX_H = "─"
    BOX_V = "│"
    BOX_CROSS = "┼"
    BOX_T_DOWN = "┬"
    BOX_T_UP = "┴"
    BOX_T_RIGHT = "├"
    BOX_T_LEFT = "┤"

    # Progress bar characters
    PROG_FULL = "█"
    PROG_EMPTY = "░"
    PROG_PARTIAL = ["▏", "▎", "▍", "▌", "▋", "▊", "▉"]

    # Status icons
    ICON_OK = "●"
    ICON_WARN = "◐"
    ICON_ERROR = "○"
    ICON_UNKNOWN = "◌"

    def __init__(
        self,
        corp_path: Path,
        width: int = 80,
        use_colors: bool = True
    ):
        """
        Initialize the dashboard.

        Args:
            corp_path: Path to the corp directory
            width: Terminal width for rendering
            use_colors: Whether to use ANSI colors
        """
        self.corp_path = Path(corp_path)
        self.width = width
        self.use_colors = use_colors

        # Initialize components
        self.monitor = SystemMonitor(self.corp_path)
        self.contract_manager = ContractManager(self.corp_path)
        self.molecule_engine = MoleculeEngine(self.corp_path)
        self.skill_registry = SkillRegistry(self.corp_path)
        self.scheduler = WorkScheduler(self.corp_path, self.skill_registry)

        # Disable colors if not a TTY
        if not use_colors or not sys.stdout.isatty():
            Colors.disable()
            self.use_colors = False

    def render(self) -> str:
        """
        Render the full dashboard.

        Returns:
            String containing the complete dashboard output
        """
        lines = []

        # Collect current metrics
        metrics = self.monitor.collect_metrics()
        alerts = self.monitor.get_active_alerts()
        contracts = self.contract_manager.list_active_contracts()

        # Header
        lines.extend(self._render_header(metrics, alerts))
        lines.append("")

        # Main panels
        lines.extend(self._render_agent_panel(metrics))
        lines.append("")

        lines.extend(self._render_project_panel(metrics, contracts))
        lines.append("")

        lines.extend(self._render_queue_panel(metrics))
        lines.append("")

        lines.extend(self._render_capability_panel())
        lines.append("")

        lines.extend(self._render_alert_panel(alerts))
        lines.append("")

        # Footer
        lines.extend(self._render_footer())

        return "\n".join(lines)

    def render_compact(self) -> str:
        """
        Render a compact single-line status.

        Returns:
            Single line status string
        """
        metrics = self.monitor.collect_metrics()
        alerts = self.monitor.get_active_alerts()

        # Count by severity
        critical = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        warning = len([a for a in alerts if a.severity == AlertSeverity.WARNING])

        # Count agent health
        healthy = sum(1 for a in metrics.agents.values() if a.health == HealthState.HEALTHY)
        total = len(metrics.agents)

        # Build status
        if critical > 0:
            status_color = Colors.RED
            status_text = f"CRITICAL ({critical})"
        elif warning > 0:
            status_color = Colors.YELLOW
            status_text = f"WARNING ({warning})"
        else:
            status_color = Colors.GREEN
            status_text = "HEALTHY"

        return (
            f"{Colors.BOLD}AI Corp{Colors.RESET} | "
            f"Status: {status_color}{status_text}{Colors.RESET} | "
            f"Agents: {healthy}/{total} | "
            f"Projects: {metrics.active_molecules} | "
            f"Gates: {metrics.pending_gates}"
        )

    def _render_header(self, metrics: SystemMetrics, alerts: List[HealthAlert]) -> List[str]:
        """Render the dashboard header with overall status"""
        lines = []

        # Determine overall status
        critical = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        warning = len([a for a in alerts if a.severity == AlertSeverity.WARNING])

        if critical > 0:
            status_color = Colors.RED
            status_bg = Colors.BG_RED
            status_text = "CRITICAL"
        elif warning > 0:
            status_color = Colors.YELLOW
            status_bg = Colors.BG_YELLOW
            status_text = "WARNING"
        else:
            status_color = Colors.GREEN
            status_bg = Colors.BG_GREEN
            status_text = "OPERATIONAL"

        # Title bar
        title = " AI CORP DASHBOARD "
        padding = (self.width - len(title)) // 2

        lines.append(f"{Colors.BOLD}{self.BOX_H * self.width}{Colors.RESET}")
        lines.append(f"{Colors.BOLD}{' ' * padding}{title}{' ' * padding}{Colors.RESET}")
        lines.append(f"{Colors.BOLD}{self.BOX_H * self.width}{Colors.RESET}")

        # Status line
        timestamp = datetime.fromisoformat(metrics.timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
        status_line = f"  Status: {status_color}{Colors.BOLD}{status_text}{Colors.RESET}"
        status_line += f"  {Colors.DIM}|{Colors.RESET}  Last Update: {timestamp}"
        lines.append(status_line)

        # Quick stats
        healthy_agents = sum(1 for a in metrics.agents.values() if a.health == HealthState.HEALTHY)
        total_agents = len(metrics.agents)

        stats_line = (
            f"  Agents: {healthy_agents}/{total_agents} healthy  "
            f"{Colors.DIM}|{Colors.RESET}  "
            f"Projects: {metrics.active_molecules}  "
            f"{Colors.DIM}|{Colors.RESET}  "
            f"Pending Gates: {metrics.pending_gates}  "
            f"{Colors.DIM}|{Colors.RESET}  "
            f"Alerts: {len(alerts)}"
        )
        lines.append(stats_line)

        return lines

    def _render_agent_panel(self, metrics: SystemMetrics) -> List[str]:
        """Render the agent status panel"""
        lines = []

        # Panel header
        lines.append(self._panel_header("AGENT STATUS"))

        if not metrics.agents:
            lines.append(f"  {Colors.DIM}No agents registered{Colors.RESET}")
            lines.append(self._panel_footer())
            return lines

        # Column headers
        header = f"  {'Agent':<25} {'Health':<12} {'Current Work':<25} {'Queue':<6}"
        lines.append(f"{Colors.DIM}{header}{Colors.RESET}")
        lines.append(f"  {'-' * 25} {'-' * 12} {'-' * 25} {'-' * 6}")

        # Sort agents by department, then role
        sorted_agents = sorted(
            metrics.agents.values(),
            key=lambda a: (a.department, a.role, a.agent_id)
        )

        for agent in sorted_agents:
            health_icon, health_color = self._get_health_indicator(agent.health)
            work = (agent.current_work or "idle")[:25]

            # Queue depth coloring
            if agent.queue_depth >= 50:
                queue_color = Colors.RED
            elif agent.queue_depth >= 10:
                queue_color = Colors.YELLOW
            else:
                queue_color = Colors.GREEN

            line = (
                f"  {agent.agent_id:<25} "
                f"{health_color}{health_icon} {agent.health.value:<10}{Colors.RESET} "
                f"{work:<25} "
                f"{queue_color}{agent.queue_depth:<6}{Colors.RESET}"
            )
            lines.append(line)

        lines.append(self._panel_footer())
        return lines

    def _render_project_panel(
        self,
        metrics: SystemMetrics,
        contracts: List[Any]
    ) -> List[str]:
        """Render the project/molecule progress panel"""
        lines = []

        lines.append(self._panel_header("PROJECT PROGRESS"))

        if not metrics.molecules:
            lines.append(f"  {Colors.DIM}No active projects{Colors.RESET}")
            lines.append(self._panel_footer())
            return lines

        # Get molecule details
        for mol_id, progress in metrics.molecules.items():
            mol = self.molecule_engine.get_molecule(mol_id)
            if not mol:
                continue

            # Find linked contract if any
            contract = self.contract_manager.get_by_molecule(mol_id)

            # Progress bar
            bar_width = 30
            progress_bar = self._render_progress_bar(progress, bar_width)

            # Status color
            if progress >= 100:
                status_color = Colors.GREEN
            elif progress > 0:
                status_color = Colors.CYAN
            else:
                status_color = Colors.YELLOW

            name = mol.name[:35] if mol.name else mol_id[:35]
            lines.append(f"  {name}")
            lines.append(f"    {progress_bar} {status_color}{progress:5.1f}%{Colors.RESET}")

            # Show contract progress if linked
            if contract:
                ctr_progress = contract.get_progress()
                ctr_bar = self._render_progress_bar(
                    ctr_progress['percent_complete'],
                    bar_width,
                    fill_char="▓",
                    empty_char="░"
                )
                lines.append(
                    f"    {Colors.DIM}Contract: {ctr_bar} "
                    f"{ctr_progress['met']}/{ctr_progress['total']} criteria{Colors.RESET}"
                )

        lines.append(self._panel_footer())
        return lines

    def _render_queue_panel(self, metrics: SystemMetrics) -> List[str]:
        """Render the work queue depths panel"""
        lines = []

        lines.append(self._panel_header("WORK QUEUES"))

        if not metrics.queues:
            lines.append(f"  {Colors.DIM}No queues with work{Colors.RESET}")
            lines.append(self._panel_footer())
            return lines

        # Sort by queue depth descending
        sorted_queues = sorted(
            metrics.queues.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10

        # Find max for bar scaling
        max_depth = max(q[1] for q in sorted_queues) if sorted_queues else 1
        bar_width = 20

        for agent_id, depth in sorted_queues:
            if depth == 0:
                continue

            # Bar based on relative depth
            bar_fill = int((depth / max_depth) * bar_width) if max_depth > 0 else 0
            bar = self.PROG_FULL * bar_fill + self.PROG_EMPTY * (bar_width - bar_fill)

            # Color based on depth
            if depth >= 50:
                color = Colors.RED
            elif depth >= 10:
                color = Colors.YELLOW
            else:
                color = Colors.GREEN

            lines.append(f"  {agent_id:<25} [{color}{bar}{Colors.RESET}] {depth:>3}")

        lines.append(self._panel_footer())
        return lines

    def _render_capability_panel(self) -> List[str]:
        """Render the capability and skill panel"""
        lines = []

        lines.append(self._panel_header("CAPABILITIES & SKILLS"))

        # Get scheduler report
        report = self.scheduler.get_scheduling_report()
        agents = report.get('agents', [])

        if not agents:
            lines.append(f"  {Colors.DIM}No agents registered with scheduler{Colors.RESET}")
            lines.append(self._panel_footer())
            return lines

        # Group agents by capability
        capability_agents: Dict[str, List[str]] = {}
        for agent_id in agents:
            caps = self.scheduler.capability_matcher.get_agent_capabilities(agent_id)
            for cap in caps:
                if cap not in capability_agents:
                    capability_agents[cap] = []
                capability_agents[cap].append(agent_id)

        # Show capabilities with their agents
        if capability_agents:
            lines.append(f"  {Colors.BOLD}By Capability:{Colors.RESET}")
            for cap in sorted(capability_agents.keys()):
                agent_list = capability_agents[cap]
                skills = CAPABILITY_SKILL_MAP.get(cap, [])
                skill_str = f" ({', '.join(skills)})" if skills else ""

                lines.append(
                    f"    {Colors.CYAN}{cap}{Colors.RESET}{Colors.DIM}{skill_str}{Colors.RESET}"
                )
                agent_names = ", ".join(sorted(agent_list)[:5])
                if len(agent_list) > 5:
                    agent_names += f" +{len(agent_list) - 5} more"
                lines.append(f"      {Colors.DIM}Agents: {agent_names}{Colors.RESET}")
        else:
            # Show agents without capabilities
            lines.append(f"  {Colors.DIM}No capabilities mapped yet{Colors.RESET}")

        # Summary line
        lines.append("")
        skill_summary = self.skill_registry.get_skill_summary()
        lines.append(
            f"  {Colors.DIM}Total: {len(agents)} agents | "
            f"{len(capability_agents)} capabilities | "
            f"{skill_summary.get('total_unique_skills', 0)} unique skills{Colors.RESET}"
        )

        lines.append(self._panel_footer())
        return lines

    def _render_alert_panel(self, alerts: List[HealthAlert]) -> List[str]:
        """Render the active alerts panel"""
        lines = []

        lines.append(self._panel_header("ACTIVE ALERTS"))

        if not alerts:
            lines.append(f"  {Colors.GREEN}No active alerts{Colors.RESET}")
            lines.append(self._panel_footer())
            return lines

        # Sort by severity (critical first)
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.INFO: 2
        }
        sorted_alerts = sorted(alerts, key=lambda a: severity_order.get(a.severity, 99))

        for alert in sorted_alerts[:5]:  # Show top 5
            icon, color = self._get_severity_indicator(alert.severity)

            lines.append(f"  {color}{icon} [{alert.severity.value.upper()}]{Colors.RESET} {alert.message}")
            lines.append(f"    {Colors.DIM}Action: {alert.suggested_action}{Colors.RESET}")

        if len(alerts) > 5:
            lines.append(f"  {Colors.DIM}... and {len(alerts) - 5} more alerts{Colors.RESET}")

        lines.append(self._panel_footer())
        return lines

    def _render_footer(self) -> List[str]:
        """Render the dashboard footer"""
        lines = []

        lines.append(f"{Colors.DIM}{self.BOX_H * self.width}{Colors.RESET}")
        lines.append(
            f"{Colors.DIM}  Press Ctrl+C to exit | "
            f"Refresh: ai-corp dashboard | "
            f"Live mode: ai-corp dashboard --live{Colors.RESET}"
        )

        return lines

    def _panel_header(self, title: str) -> str:
        """Create a panel header"""
        return f"{Colors.BOLD}{self.BOX_TL}{self.BOX_H} {title} {self.BOX_H * (self.width - len(title) - 5)}{Colors.RESET}"

    def _panel_footer(self) -> str:
        """Create a panel footer"""
        return f"{Colors.DIM}{self.BOX_BL}{self.BOX_H * (self.width - 1)}{Colors.RESET}"

    def _render_progress_bar(
        self,
        percent: float,
        width: int,
        fill_char: str = None,
        empty_char: str = None
    ) -> str:
        """Render a progress bar"""
        fill_char = fill_char or self.PROG_FULL
        empty_char = empty_char or self.PROG_EMPTY

        filled = int(percent / 100 * width)
        empty = width - filled

        # Color based on progress
        if percent >= 100:
            color = Colors.GREEN
        elif percent >= 50:
            color = Colors.CYAN
        elif percent >= 25:
            color = Colors.YELLOW
        else:
            color = Colors.RED

        bar = f"{color}{fill_char * filled}{Colors.RESET}{Colors.DIM}{empty_char * empty}{Colors.RESET}"
        return f"[{bar}]"

    def _get_health_indicator(self, health: HealthState) -> Tuple[str, str]:
        """Get icon and color for health state"""
        if health == HealthState.HEALTHY:
            return self.ICON_OK, Colors.GREEN
        elif health == HealthState.SLOW:
            return self.ICON_WARN, Colors.YELLOW
        elif health == HealthState.UNRESPONSIVE:
            return self.ICON_ERROR, Colors.RED
        else:
            return self.ICON_UNKNOWN, Colors.DIM

    def _get_severity_indicator(self, severity: AlertSeverity) -> Tuple[str, str]:
        """Get icon and color for alert severity"""
        if severity == AlertSeverity.CRITICAL:
            return "!", Colors.RED
        elif severity == AlertSeverity.WARNING:
            return "!", Colors.YELLOW
        else:
            return "i", Colors.CYAN


def run_dashboard(
    corp_path: Path,
    live: bool = False,
    refresh_interval: float = 5.0,
    compact: bool = False
) -> None:
    """
    Run the dashboard.

    Args:
        corp_path: Path to the corp directory
        live: Whether to run in live refresh mode
        refresh_interval: Seconds between refreshes (live mode)
        compact: Show compact single-line output
    """
    dashboard = Dashboard(corp_path)

    if compact:
        print(dashboard.render_compact())
        return

    if not live:
        print(dashboard.render())
        return

    # Live mode
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name != 'nt' else 'cls')

            # Render dashboard
            print(dashboard.render())

            # Wait for next refresh
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print(f"\n{Colors.DIM}Dashboard stopped.{Colors.RESET}")


def get_status_line(corp_path: Path) -> str:
    """
    Get a single-line status for embedding in prompts or scripts.

    Args:
        corp_path: Path to the corp directory

    Returns:
        Single line status string
    """
    dashboard = Dashboard(corp_path, use_colors=False)
    metrics = dashboard.monitor.collect_metrics()
    alerts = dashboard.monitor.get_active_alerts()

    critical = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
    warning = len([a for a in alerts if a.severity == AlertSeverity.WARNING])
    healthy = sum(1 for a in metrics.agents.values() if a.health == HealthState.HEALTHY)
    total = len(metrics.agents)

    if critical > 0:
        status = f"CRITICAL({critical})"
    elif warning > 0:
        status = f"WARN({warning})"
    else:
        status = "OK"

    return f"AI-CORP: {status} | Agents:{healthy}/{total} | Projects:{metrics.active_molecules}"
