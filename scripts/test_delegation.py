#!/usr/bin/env python3
"""
COO Delegation Test - Quick test for full delegation chain.

Tests the COO → VP → Director → Worker delegation flow without
requiring real Claude CLI execution (uses MockBackend).

Run from repo root: python3 scripts/test_delegation.py
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.preset import init_from_preset
from src.core.molecule import MoleculeEngine, MoleculeStatus, StepStatus
from src.core.hook import HookManager
from src.core.bead import BeadLedger
from src.agents.coo import COOAgent
from src.agents.executor import CorporationExecutor


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(num: int, text: str):
    """Print a step indicator."""
    print(f"\n[{num}] {text}")
    print("-" * 50)


def show_molecule(engine: MoleculeEngine, mol_id: str):
    """Display molecule status."""
    mol = engine.get_molecule(mol_id)
    if not mol:
        print("  Molecule not found!")
        return

    print(f"\n  Molecule: {mol.name}")
    print(f"  Status: {mol.status.value}")
    progress = mol.get_progress()
    print(f"  Progress: {progress['percent_complete']:.0f}% ({progress['completed']}/{progress['total']} steps)")

    status_icons = {
        "pending": "○",
        "in_progress": "◐",
        "completed": "●",
        "failed": "✗",
        "blocked": "⊘"
    }

    print("\n  Steps:")
    for i, step in enumerate(mol.steps, 1):
        icon = status_icons.get(step.status.value, "?")
        gate = " [GATE]" if step.is_gate else ""
        assigned = f" → {step.assigned_to}" if step.assigned_to else ""
        print(f"    {icon} {i}. {step.name}{gate}{assigned}")
        if step.result:
            preview = str(step.result)[:50] + "..." if len(str(step.result)) > 50 else str(step.result)
            print(f"       Result: {preview}")


def show_hooks(hook_manager: HookManager, labels: list):
    """Show hook status for specified hooks."""
    print("\n  Work Queues:")
    hooks = hook_manager.list_hooks()
    for hook in hooks:
        if any(label in hook.owner_id for label in labels):
            stats = hook.get_stats()
            total = stats['queued'] + stats['in_progress'] + stats['completed']
            if total > 0:
                print(f"    {hook.owner_id}: Q={stats['queued']} P={stats['in_progress']} C={stats['completed']}")


def main():
    print_header("COO Delegation Test")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

    # Step 1: Initialize test corporation
    print_step(1, "Initialize test corporation")

    test_dir = Path(tempfile.mkdtemp(prefix="coo_test_"))
    print(f"  Directory: {test_dir}")

    try:
        corp_path = init_from_preset(
            preset_id="software-company",
            target_path=test_dir,
            name="Test Corp"
        )
        os.environ['AI_CORP_PATH'] = str(corp_path)
        print("  ✓ Corporation initialized")

        # Initialize engines
        molecule_engine = MoleculeEngine(corp_path)
        hook_manager = HookManager(corp_path)

        # Step 2: Create agents via CorporationExecutor
        print_step(2, "Create agent hierarchy")

        corp_executor = CorporationExecutor(corp_path)
        corp_executor.initialize(departments=['engineering', 'research', 'quality', 'product'])

        coo = corp_executor.coo
        print(f"  ✓ COO: {coo.identity.role_name}")
        print(f"  ✓ VPs: {len(corp_executor.vps)}")
        print(f"  ✓ Directors: {len(corp_executor.directors)}")
        print(f"  ✓ Workers: {len(corp_executor.workers)}")

        # Step 3: Submit task as CEO
        print_step(3, "Submit CEO task to COO")

        task_title = "Create a unit test for user authentication"
        task_desc = "Write a Python unit test that verifies user login functionality works correctly."

        # Use fast task creation (no LLM)
        molecule = coo.receive_ceo_task_fast(
            title=task_title,
            description=task_desc,
            priority="P2_MEDIUM"
        )

        print(f"  ✓ Task submitted: {task_title}")
        print(f"  ✓ Molecule ID: {molecule.id}")
        show_molecule(molecule_engine, molecule.id)

        # Step 4: Start and delegate molecule
        print_step(4, "Start molecule and delegate to VPs")

        molecule = molecule_engine.start_molecule(molecule.id)
        print(f"  Molecule status: {molecule.status.value}")

        delegations = coo.delegate_molecule(molecule)
        print(f"  ✓ Delegated {len(delegations)} work items")

        show_molecule(molecule_engine, molecule.id)
        show_hooks(hook_manager, ['vp_', 'dir_', 'worker_'])

        # Step 5: Run corporation cycle (with mock LLM)
        print_step(5, "Run corporation execution cycle")

        # Run the delegation chain
        results = corp_executor.run_cycle()

        print(f"  COO result: {results.get('coo', {}).get('processed', 0)} processed")
        print(f"  VP result: {results.get('vps', {}).get('processed', 0)} processed")
        print(f"  Director result: {results.get('directors', {}).get('processed', 0)} processed")
        print(f"  Worker result: {results.get('workers', {}).get('processed', 0)} processed")

        # Step 6: Check final state
        print_step(6, "Final molecule state")

        # Reload molecule from disk
        final_mol = molecule_engine.get_molecule(molecule.id)
        show_molecule(molecule_engine, final_mol.id if final_mol else molecule.id)

        # Show any work items
        show_hooks(hook_manager, ['vp_', 'dir_', 'worker_'])

        # Summary
        print_header("Test Complete")

        progress = final_mol.get_progress() if final_mol else {'percent_complete': 0, 'completed': 0, 'total': 0}

        # Check for issues
        issues = []

        # Check if work was delegated
        all_hooks = hook_manager.list_hooks()
        total_work = sum(h.get_stats()['queued'] + h.get_stats()['in_progress'] + h.get_stats()['completed'] for h in all_hooks)
        if total_work == 0:
            issues.append("No work items in any hook")

        # Check if steps progressed
        if final_mol:
            in_progress_count = sum(1 for s in final_mol.steps if s.status == StepStatus.IN_PROGRESS)
            completed_count = sum(1 for s in final_mol.steps if s.status == StepStatus.COMPLETED)
            if in_progress_count == 0 and completed_count == 0:
                issues.append("No steps moved from PENDING")

        if issues:
            print("\n  Issues Found:")
            for issue in issues:
                print(f"    ⚠ {issue}")
        else:
            print(f"\n  ✓ Progress: {progress['percent_complete']:.0f}%")
            print(f"  ✓ Steps completed: {progress['completed']}/{progress['total']}")

        print(f"\n  Test directory: {test_dir}")
        print(f"  Cleanup: rm -rf {test_dir}")

        return 0 if not issues else 1

    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
