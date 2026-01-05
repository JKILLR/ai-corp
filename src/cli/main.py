#!/usr/bin/env python3
"""
AI Corp CLI - Main Entry Point

Usage:
    ai-corp ceo <task>              Submit a task as CEO
    ai-corp coo                     Start the COO orchestrator
    ai-corp status                  View system status
    ai-corp molecules [list|show]   Manage molecules
    ai-corp hooks [list|show]       Manage hooks
    ai-corp gates [list|show]       Manage quality gates
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.coo import COOAgent
from src.agents.runtime import AgentRuntime
from src.core.molecule import MoleculeEngine
from src.core.hook import HookManager
from src.core.gate import GateKeeper
from src.core.bead import BeadLedger


def get_corp_path() -> Path:
    """Get the AI Corp base path"""
    # Check environment variable first
    import os
    env_path = os.environ.get('AI_CORP_PATH')
    if env_path:
        return Path(env_path)

    # Default to current directory's corp folder
    cwd = Path.cwd()
    if (cwd / 'corp').exists():
        return cwd / 'corp'

    # Or the parent if we're inside src
    if (cwd.parent / 'corp').exists():
        return cwd.parent / 'corp'

    return cwd / 'corp'


def cmd_ceo(args):
    """Submit a task as CEO"""
    corp_path = get_corp_path()
    coo = COOAgent(corp_path)

    print(f"Submitting task to AI Corp...")
    print(f"Title: {args.title}")
    print(f"Description: {args.description or args.title}")
    print()

    molecule = coo.receive_ceo_task(
        title=args.title,
        description=args.description or args.title,
        priority=args.priority
    )

    print(f"Created molecule: {molecule.id}")
    print(f"Steps: {len(molecule.steps)}")

    if args.start:
        print("\nStarting molecule and delegating work...")
        coo.molecule_engine.start_molecule(molecule.id)
        delegations = coo.delegate_molecule(molecule)
        print(f"Delegated {len(delegations)} steps")

    print("\nDone!")


def cmd_coo(args):
    """Start the COO orchestrator"""
    corp_path = get_corp_path()
    coo = COOAgent(corp_path)

    print("Starting COO Agent...")
    print()

    if args.interactive:
        # Interactive mode - run continuously
        print("Running in interactive mode. Press Ctrl+C to stop.")
        try:
            while True:
                coo.run()
                import time
                time.sleep(5)  # Check every 5 seconds
        except KeyboardInterrupt:
            print("\nShutting down COO...")
    else:
        # Single run
        coo.run()


def cmd_status(args):
    """Show system status"""
    corp_path = get_corp_path()
    coo = COOAgent(corp_path)

    if args.report:
        print(coo.report_to_ceo())
    else:
        status = coo.get_organization_status()
        print(f"AI Corp Status")
        print(f"==============")
        print(f"Active Molecules: {status['active_molecules']}")
        print(f"Pending Gates: {status['pending_gates']}")
        print()
        print("Department Workloads:")
        for dept, stats in status['departments'].items():
            print(f"  {dept}:")
            print(f"    Queued: {stats.get('queued', 0)}")
            print(f"    In Progress: {stats.get('in_progress', 0)}")
            print(f"    Completed: {stats.get('completed', 0)}")


def cmd_molecules(args):
    """Manage molecules"""
    corp_path = get_corp_path()
    engine = MoleculeEngine(corp_path)

    if args.action == 'list':
        molecules = engine.list_active_molecules()
        if not molecules:
            print("No active molecules")
            return

        print(f"Active Molecules ({len(molecules)}):")
        print("-" * 60)
        for mol in molecules:
            progress = mol.get_progress()
            print(f"{mol.id}: {mol.name}")
            print(f"  Status: {mol.status.value}")
            print(f"  Progress: {progress['percent_complete']}%")
            print()

    elif args.action == 'show':
        if not args.molecule_id:
            print("Error: molecule_id required for show")
            return

        mol = engine.get_molecule(args.molecule_id)
        if not mol:
            print(f"Molecule {args.molecule_id} not found")
            return

        print(f"Molecule: {mol.id}")
        print(f"Name: {mol.name}")
        print(f"Status: {mol.status.value}")
        print(f"Priority: {mol.priority}")
        print(f"Created: {mol.created_at}")
        print()
        print("Steps:")
        for i, step in enumerate(mol.steps, 1):
            gate_marker = " [GATE]" if step.is_gate else ""
            print(f"  {i}. {step.name}{gate_marker}")
            print(f"     Status: {step.status.value}")
            if step.assigned_to:
                print(f"     Assigned: {step.assigned_to}")


def cmd_hooks(args):
    """Manage hooks"""
    corp_path = get_corp_path()
    manager = HookManager(corp_path)

    if args.action == 'list':
        hooks = manager.list_hooks()
        if not hooks:
            print("No hooks found")
            return

        print(f"Hooks ({len(hooks)}):")
        print("-" * 60)
        for hook in hooks:
            stats = hook.get_stats()
            print(f"{hook.id}: {hook.name}")
            print(f"  Owner: {hook.owner_type}/{hook.owner_id}")
            print(f"  Queued: {stats['queued']} | In Progress: {stats['in_progress']}")
            print()

    elif args.action == 'show':
        if not args.hook_id:
            print("Error: hook_id required for show")
            return

        hook = manager.get_hook(args.hook_id)
        if not hook:
            print(f"Hook {args.hook_id} not found")
            return

        print(f"Hook: {hook.id}")
        print(f"Name: {hook.name}")
        print(f"Owner: {hook.owner_type}/{hook.owner_id}")
        print()
        print("Work Items:")
        for item in hook.items:
            print(f"  {item.id}: {item.title}")
            print(f"    Status: {item.status.value}")
            print(f"    Priority: {item.priority.name}")


def cmd_gates(args):
    """Manage quality gates"""
    corp_path = get_corp_path()
    keeper = GateKeeper(corp_path)

    if args.action == 'list':
        gates = keeper.list_gates()
        if not gates:
            print("No gates found")
            return

        print(f"Quality Gates ({len(gates)}):")
        print("-" * 60)
        for gate in gates:
            pending = gate.get_pending_submissions()
            print(f"{gate.id}: {gate.name}")
            print(f"  Stage: {gate.pipeline_stage}")
            print(f"  Owner: {gate.owner_role}")
            print(f"  Pending: {len(pending)}")
            print()

    elif args.action == 'show':
        if not args.gate_id:
            print("Error: gate_id required for show")
            return

        gate = keeper.get_gate(args.gate_id)
        if not gate:
            print(f"Gate {args.gate_id} not found")
            return

        print(f"Gate: {gate.id}")
        print(f"Name: {gate.name}")
        print(f"Stage: {gate.pipeline_stage}")
        print(f"Owner: {gate.owner_role}")
        print()
        print("Criteria:")
        for c in gate.criteria:
            req = "[Required]" if c.required else "[Optional]"
            print(f"  - {c.name} {req}")
        print()
        print("Pending Submissions:")
        for sub in gate.get_pending_submissions():
            print(f"  {sub.id}: {sub.summary[:50]}...")


def main():
    parser = argparse.ArgumentParser(
        description='AI Corp - Autonomous AI Corporation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # CEO command
    ceo_parser = subparsers.add_parser('ceo', help='Submit a task as CEO')
    ceo_parser.add_argument('title', help='Task title')
    ceo_parser.add_argument('-d', '--description', help='Task description')
    ceo_parser.add_argument('-p', '--priority', default='P2_MEDIUM',
                           choices=['P0_CRITICAL', 'P1_HIGH', 'P2_MEDIUM', 'P3_LOW'])
    ceo_parser.add_argument('-s', '--start', action='store_true',
                           help='Start the molecule immediately')
    ceo_parser.set_defaults(func=cmd_ceo)

    # COO command
    coo_parser = subparsers.add_parser('coo', help='Start the COO orchestrator')
    coo_parser.add_argument('-i', '--interactive', action='store_true',
                           help='Run in interactive mode')
    coo_parser.set_defaults(func=cmd_coo)

    # Status command
    status_parser = subparsers.add_parser('status', help='View system status')
    status_parser.add_argument('-r', '--report', action='store_true',
                              help='Generate full report')
    status_parser.set_defaults(func=cmd_status)

    # Molecules command
    mol_parser = subparsers.add_parser('molecules', help='Manage molecules')
    mol_parser.add_argument('action', choices=['list', 'show'], default='list', nargs='?')
    mol_parser.add_argument('molecule_id', nargs='?', help='Molecule ID for show')
    mol_parser.set_defaults(func=cmd_molecules)

    # Hooks command
    hooks_parser = subparsers.add_parser('hooks', help='Manage hooks')
    hooks_parser.add_argument('action', choices=['list', 'show'], default='list', nargs='?')
    hooks_parser.add_argument('hook_id', nargs='?', help='Hook ID for show')
    hooks_parser.set_defaults(func=cmd_hooks)

    # Gates command
    gates_parser = subparsers.add_parser('gates', help='Manage quality gates')
    gates_parser.add_argument('action', choices=['list', 'show'], default='list', nargs='?')
    gates_parser.add_argument('gate_id', nargs='?', help='Gate ID for show')
    gates_parser.set_defaults(func=cmd_gates)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == '__main__':
    main()
