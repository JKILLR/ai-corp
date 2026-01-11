#!/usr/bin/env python3
"""
AI Corp Demo Script - Full System Test with Monitoring

Run this from a SEPARATE TERMINAL (not within Claude Code) to test
the complete system with real Claude CLI execution.

Usage:
    python scripts/demo.py

This will:
1. Initialize a test corporation
2. Submit a task as CEO
3. Run full agent chain: COO → VP → Director → Worker
4. Monitor flow and health throughout
5. Show bead audit trail
"""

import sys
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.preset import init_from_preset
from src.core.molecule import MoleculeEngine, MoleculeStatus
from src.core.hook import HookManager
from src.core.bead import BeadLedger
from src.core.monitor import SystemMonitor
from src.agents.coo import COOAgent
from src.agents.vp import create_vp_agent
from src.agents.director import create_director_agent
from src.agents.worker import create_worker_agent
from src.core.llm import ClaudeCodeBackend


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()


def print_step(num: int, text: str):
    """Print a step indicator."""
    print(f"\n[Step {num}] {text}")
    print("-" * 50)


def print_substep(text: str):
    """Print a substep."""
    print(f"  → {text}")


def show_molecule_status(engine: MoleculeEngine, mol_id: str):
    """Display molecule status."""
    mol = engine.get_molecule(mol_id)
    if not mol:
        print("  Molecule not found")
        return

    progress = mol.get_progress()
    print(f"\n  Molecule: {mol.name}")
    print(f"  Status: {mol.status.value}")
    print(f"  Progress: {progress['percent_complete']:.0f}%")
    print()

    status_icons = {
        "pending": "○",
        "in_progress": "◐",
        "completed": "●",
        "failed": "✗",
        "blocked": "⊘"
    }

    for i, step in enumerate(mol.steps, 1):
        icon = status_icons.get(step.status.value, "?")
        gate = " [GATE]" if step.is_gate else ""
        assigned = f" → {step.assigned_to}" if step.assigned_to else ""
        print(f"  {icon} {i}. {step.name}{gate}{assigned}")
        print(f"      Status: {step.status.value}")
        if step.result:
            result_preview = str(step.result)[:60] + "..." if len(str(step.result)) > 60 else str(step.result)
            print(f"      Result: {result_preview}")


def show_health_status(monitor: SystemMonitor):
    """Display system health."""
    print("\n  System Health:")
    print("  " + "-" * 40)

    metrics = monitor.collect_metrics()

    # Agent health
    if metrics.agents:
        for agent_id, status in metrics.agents.items():
            health_icons = {"healthy": "✓", "slow": "!", "unresponsive": "✗", "unknown": "?"}
            icon = health_icons.get(status.health.value, "?")
            work = status.current_work or "idle"
            print(f"  [{icon}] {agent_id}: {work}")
    else:
        print("  No agents registered")

    # Alerts
    alerts = monitor.get_active_alerts()
    if alerts:
        print("\n  Active Alerts:")
        for alert in alerts:
            print(f"  [{alert.severity.value.upper()}] {alert.message}")


def show_beads(ledger: BeadLedger, limit: int = 5):
    """Show recent beads (audit trail)."""
    print("\n  Recent Audit Trail (Beads):")
    print("  " + "-" * 40)

    beads = ledger.list_beads(limit=limit)
    if not beads:
        print("  No beads recorded yet")
        return

    for bead in beads[:limit]:
        timestamp = bead.created_at[:19] if bead.created_at else "unknown"
        print(f"  [{timestamp}] {bead.event_type}")
        print(f"    Actor: {bead.actor_id}")
        if bead.summary:
            print(f"    Summary: {bead.summary[:50]}...")


def show_hooks(hook_manager: HookManager):
    """Show hook status."""
    print("\n  Work Queues (Hooks):")
    print("  " + "-" * 40)

    hooks = hook_manager.list_hooks()
    if not hooks:
        print("  No hooks found")
        return

    for hook in hooks:
        stats = hook.get_stats()
        print(f"  {hook.name} ({hook.owner_id})")
        print(f"    Queued: {stats['queued']} | In Progress: {stats['in_progress']} | Completed: {stats['completed']}")


def main():
    print_header("AI Corp - Full System Demo")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Check Claude CLI
    print_step(1, "Checking Claude CLI availability")

    import subprocess
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✓ Claude CLI: {result.stdout.strip()}")
        else:
            print(f"✗ Claude CLI error: {result.stderr}")
            return 1
    except FileNotFoundError:
        print("✗ Claude CLI not found - install Claude Code CLI first")
        return 1
    except subprocess.TimeoutExpired:
        print("✗ Claude CLI timed out")
        return 1

    # Step 2: Initialize corporation
    print_step(2, "Initializing test corporation")

    test_dir = Path(tempfile.mkdtemp(prefix="aicorp_full_demo_"))
    print(f"  Directory: {test_dir}")

    try:
        corp_path = init_from_preset(
            preset_id="software-company",
            target_path=test_dir,
            name="Demo Corp"
        )
        print(f"✓ Corporation initialized")
        os.environ['AI_CORP_PATH'] = str(corp_path)

        # Initialize core components
        molecule_engine = MoleculeEngine(corp_path)
        hook_manager = HookManager(corp_path)
        bead_ledger = BeadLedger(corp_path, auto_commit=False)
        monitor = SystemMonitor(corp_path)

        print_substep("Core components initialized")

        # Step 3: Create agents
        print_step(3, "Creating agent hierarchy")

        coo = COOAgent(corp_path)
        print_substep("COO Agent created")

        # Create VP (factory uses department to configure)
        vp = create_vp_agent(
            department="engineering",
            corp_path=corp_path
        )
        print_substep("VP Engineering created")

        # Create Director
        director = create_director_agent(
            role_id="dir_backend",
            role_name="Director of Backend",
            department="engineering",
            focus="backend development",
            reports_to="vp_engineering",
            corp_path=corp_path
        )
        print_substep("Director Backend created")

        # Create Worker (uses worker_type instead of role_id)
        worker = create_worker_agent(
            worker_type="backend",
            department="engineering",
            reports_to="dir_backend",
            corp_path=corp_path
        )
        print_substep("Backend Worker created")

        # Step 4: Submit task
        print_step(4, "Submitting task as CEO")

        task_title = "Create a Python function that adds two numbers"
        task_desc = "Write a simple Python function called 'add' that takes two numbers and returns their sum. Include a docstring."

        molecule = coo.receive_ceo_task(
            title=task_title,
            description=task_desc,
            priority="P2_MEDIUM"
        )

        print(f"✓ Task submitted")
        print(f"  Molecule ID: {molecule.id}")
        show_molecule_status(molecule_engine, molecule.id)

        # Step 5: COO processes and delegates
        print_step(5, "COO processing and delegating")

        # Start molecule
        molecule = molecule_engine.start_molecule(molecule.id)
        print_substep(f"Molecule started: {molecule.status.value}")

        # COO delegates
        delegations = coo.delegate_molecule(molecule)
        print_substep(f"Delegated {len(delegations)} work items")

        show_molecule_status(molecule_engine, molecule.id)
        show_hooks(hook_manager)

        # Step 6: VP processes work
        print_step(6, "VP processing delegated work")

        try:
            vp_result = vp.run() or {}
            processed = vp_result.get('processed', 0) if isinstance(vp_result, dict) else 0
            print_substep(f"VP processed: {processed} items")
        except Exception as e:
            print_substep(f"VP run error: {e}")

        show_molecule_status(molecule_engine, molecule.id)
        show_hooks(hook_manager)

        # Step 7: Director processes work
        print_step(7, "Director processing work")

        try:
            dir_result = director.run() or {}
            processed = dir_result.get('processed', 0) if isinstance(dir_result, dict) else 0
            print_substep(f"Director processed: {processed} items")
        except Exception as e:
            print_substep(f"Director run error: {e}")

        show_molecule_status(molecule_engine, molecule.id)
        show_hooks(hook_manager)

        # Step 8: Worker executes (THIS IS WHERE CLAUDE RUNS)
        print_step(8, "Worker executing with Claude CLI")
        print("  (This step will call real Claude CLI...)")
        print()

        response = input("  Run worker with real Claude? (y/n): ").strip().lower()

        if response == 'y':
            print()
            print("  Executing...")
            print("  " + "-" * 40)

            try:
                worker_result = worker.run() or {}
                print()
                print(f"✓ Worker execution complete")

                if isinstance(worker_result, dict):
                    print(f"  Processed: {worker_result.get('processed', 0)} items")

                    if worker_result.get('results'):
                        for item_id, result in worker_result['results'].items():
                            print(f"\n  Work Item: {item_id}")
                            if isinstance(result, dict):
                                if result.get('output'):
                                    print(f"  Output: {result['output'][:200]}...")
                                if result.get('error'):
                                    print(f"  Error: {result['error']}")
                            else:
                                print(f"  Result: {str(result)[:200]}...")
                else:
                    print(f"  Result: {worker_result}")

            except Exception as e:
                print(f"✗ Worker execution failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("  Skipped worker execution")

        # Step 9: Show final status
        print_step(9, "Final System Status")

        show_molecule_status(molecule_engine, molecule.id)
        show_health_status(monitor)
        show_beads(bead_ledger)
        show_hooks(hook_manager)

        # Summary
        print_header("Demo Complete")

        final_mol = molecule_engine.get_molecule(molecule.id)
        final_progress = final_mol.get_progress() if final_mol else {'percent_complete': 0}

        print(f"  Corporation: {test_dir}")
        print(f"  Molecule: {molecule.id}")
        print(f"  Final Progress: {final_progress['percent_complete']:.0f}%")
        print()
        print("  Continue experimenting:")
        print(f"    cd {test_dir}")
        print("    ai-corp status")
        print("    ai-corp molecules list")
        print("    ai-corp coo  # Run another COO cycle")
        print()
        print("  Cleanup:")
        print(f"    rm -rf {test_dir}")

        return 0

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
