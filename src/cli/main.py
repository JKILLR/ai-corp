#!/usr/bin/env python3
"""
AI Corp CLI - Main Entry Point

Usage:
    ai-corp init <industry>         Initialize AI Corp for an industry
    ai-corp ceo <task>              Submit a task as CEO
    ai-corp coo                     Start the COO orchestrator
    ai-corp status                  View system status
    ai-corp org                     View organization structure
    ai-corp hire <type> <args>      Hire new agents
    ai-corp templates               List industry templates
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
from src.core.hiring import HiringManager
from src.core.templates import IndustryTemplateManager, init_corp, INDUSTRY_TEMPLATES


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


def cmd_init(args):
    """Initialize AI Corp for an industry"""
    corp_path = get_corp_path()

    print(f"Initializing AI Corp for: {args.industry}")
    print(f"Corp path: {corp_path}")
    print()

    result = init_corp(corp_path, args.industry)

    print(f"\nAI Corp initialized successfully!")
    print(f"  Industry: {result['industry']}")
    print(f"  Departments: {len(result['departments'])}")
    print(f"  VPs: {len(result['vps'])}")
    print(f"  Directors: {len(result['directors'])}")
    print(f"  Workers: {len(result['workers'])}")


def cmd_templates(args):
    """List or show industry templates"""
    if args.action == 'list':
        print("Available Industry Templates:")
        print("-" * 60)
        for name, template in INDUSTRY_TEMPLATES.items():
            print(f"  {name}")
            print(f"    {template['description']}")
            print(f"    Departments: {len(template['departments'])}")
            print()

    elif args.action == 'show':
        if not args.template_name:
            print("Error: template name required")
            return

        template = INDUSTRY_TEMPLATES.get(args.template_name)
        if not template:
            print(f"Template '{args.template_name}' not found")
            return

        print(f"Template: {template['name']}")
        print(f"Description: {template['description']}")
        print()
        print("Departments:")
        for dept in template['departments']:
            print(f"  - {dept['name']} (VP: {dept['vp']})")
            print(f"    Directors: {len(dept['directors'])}")
            print(f"    Worker types: {len(dept.get('worker_types', []))}")
        print()
        print(f"Quality Gates: {', '.join(template['quality_gates'])}")


def cmd_org(args):
    """View organization structure"""
    corp_path = get_corp_path()
    hiring = HiringManager(corp_path)

    if args.chart:
        print(hiring.get_org_chart())
    else:
        roles = hiring.list_all_roles()
        print("AI Corp Organization")
        print("=" * 60)

        print(f"\nExecutives ({len(roles['executives'])}):")
        for role in roles['executives']:
            print(f"  - {role['name']} ({role['id']})")

        print(f"\nVice Presidents ({len(roles['vps'])}):")
        for role in roles['vps']:
            print(f"  - {role['name']} ({role['id']}) - {role.get('department', 'N/A')}")

        print(f"\nDirectors ({len(roles['directors'])}):")
        for role in roles['directors']:
            print(f"  - {role['name']} ({role['id']}) -> {role.get('reports_to', 'N/A')}")

        print(f"\nWorkers ({len(roles['workers'])}):")
        for role in roles['workers']:
            print(f"  - {role['name']} ({role['id']}) @ {role.get('pool', 'N/A')}")


def cmd_hire(args):
    """Hire new agents"""
    corp_path = get_corp_path()
    hiring = HiringManager(corp_path)

    if args.role_type == 'vp':
        if not all([args.role_id, args.name, args.department]):
            print("Error: VP requires --role-id, --name, --department")
            return

        role = hiring.hire_vp(
            role_id=args.role_id,
            name=args.name,
            department=args.department,
            responsibilities=args.responsibilities.split(',') if args.responsibilities else ['Lead department'],
            skills=args.skills.split(',') if args.skills else []
        )
        print(f"Hired VP: {role['name']}")

    elif args.role_type == 'director':
        if not all([args.role_id, args.name, args.department, args.reports_to]):
            print("Error: Director requires --role-id, --name, --department, --reports-to")
            return

        role = hiring.hire_director(
            role_id=args.role_id,
            name=args.name,
            department=args.department,
            reports_to=args.reports_to,
            focus=args.focus or args.name,
            responsibilities=args.responsibilities.split(',') if args.responsibilities else ['Lead team'],
            skills=args.skills.split(',') if args.skills else []
        )
        print(f"Hired Director: {role['name']}")

    elif args.role_type == 'worker':
        if not all([args.role_id, args.name, args.department, args.pool, args.director]):
            print("Error: Worker requires --role-id, --name, --department, --pool, --director")
            return

        role = hiring.hire_worker(
            role_id=args.role_id,
            name=args.name,
            department=args.department,
            pool=args.pool,
            director=args.director,
            description=args.description or args.name,
            capabilities=args.capabilities.split(',') if args.capabilities else [],
            responsibilities=args.responsibilities.split(',') if args.responsibilities else ['Execute tasks'],
            skills=args.skills.split(',') if args.skills else []
        )
        print(f"Hired Worker: {role['name']}")

    else:
        print(f"Unknown role type: {args.role_type}")


def main():
    parser = argparse.ArgumentParser(
        description='AI Corp - Autonomous AI Corporation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize AI Corp for an industry')
    init_parser.add_argument('industry', choices=list(INDUSTRY_TEMPLATES.keys()),
                            help='Industry template to use')
    init_parser.set_defaults(func=cmd_init)

    # Templates command
    templates_parser = subparsers.add_parser('templates', help='List industry templates')
    templates_parser.add_argument('action', choices=['list', 'show'], default='list', nargs='?')
    templates_parser.add_argument('template_name', nargs='?', help='Template name for show')
    templates_parser.set_defaults(func=cmd_templates)

    # Org command
    org_parser = subparsers.add_parser('org', help='View organization structure')
    org_parser.add_argument('-c', '--chart', action='store_true', help='Show org chart')
    org_parser.set_defaults(func=cmd_org)

    # Hire command
    hire_parser = subparsers.add_parser('hire', help='Hire new agents')
    hire_parser.add_argument('role_type', choices=['vp', 'director', 'worker'],
                            help='Type of role to hire')
    hire_parser.add_argument('--role-id', help='Unique role ID')
    hire_parser.add_argument('--name', help='Display name')
    hire_parser.add_argument('--department', help='Department')
    hire_parser.add_argument('--reports-to', help='Manager role ID (for directors)')
    hire_parser.add_argument('--pool', help='Worker pool (for workers)')
    hire_parser.add_argument('--director', help='Director role ID (for workers)')
    hire_parser.add_argument('--focus', help='Role focus area')
    hire_parser.add_argument('--description', help='Role description')
    hire_parser.add_argument('--capabilities', help='Comma-separated capabilities')
    hire_parser.add_argument('--responsibilities', help='Comma-separated responsibilities')
    hire_parser.add_argument('--skills', help='Comma-separated Claude Code skills')
    hire_parser.set_defaults(func=cmd_hire)

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
