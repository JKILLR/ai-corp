#!/usr/bin/env python3
"""
AI Corp CLI - Main Entry Point

Usage:
    ai-corp init [path] --preset=X --name=Y   Initialize AI Corp from a preset
    ai-corp presets [list|show]               List or show available presets
    ai-corp ceo <task>                        Submit a task as CEO
    ai-corp ceo <task> --discover             Submit task with discovery conversation
    ai-corp ceo <task> --discover --execute   Full flow: conversation → hierarchy execution
    ai-corp coo                               Start the COO orchestrator
    ai-corp status                            View system status
    ai-corp status --health                   View health monitoring with alerts
    ai-corp dashboard                         View terminal dashboard
    ai-corp dashboard --live                  Live-updating dashboard
    ai-corp org                               View organization structure
    ai-corp hire <type> <args>                Hire new agents
    ai-corp templates                         List industry templates (legacy)
    ai-corp molecules [list|show]             Manage molecules
    ai-corp hooks [list|show]                 Manage hooks
    ai-corp gates [list|show]                 Manage quality gates
    ai-corp contracts [list|show|create|check|link|activate]  Manage success contracts
    ai-corp knowledge [list|show|add|search|stats|remove]     Manage knowledge base

CEO Command Flow:
    The --execute flag runs the full agent hierarchy after task delegation:

    1. CEO submits task via CLI
    2. COO runs discovery conversation (if --discover)
    3. COO creates Success Contract and Molecule
    4. COO delegates to VPs
    5. With --execute: CorporationExecutor runs VPs → Directors → Workers
    6. Workers execute tasks using Claude CLI

    Example:
        ai-corp ceo "Build a user dashboard" --discover --execute

Examples:
    # Initialize a new AI Corp with default software-company preset
    ai-corp init ~/projects/my-startup

    # Initialize with a specific preset and name
    ai-corp init --preset=software-company --name="Acme Dev Studio" ~/projects/acme

    # Full workflow: discovery conversation + autonomous execution
    ai-corp ceo "Add dark mode toggle" --discover --execute

    # Run multiple execution cycles (for complex tasks)
    ai-corp ceo "Refactor auth module" --discover --execute --cycles 3
"""

import argparse
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.coo import COOAgent
from src.agents.runtime import AgentRuntime
from src.agents.executor import CorporationExecutor
from src.core.molecule import MoleculeEngine
from src.core.hook import HookManager
from src.core.gate import GateKeeper
from src.core.bead import BeadLedger
from src.core.hiring import HiringManager
from src.core.templates import IndustryTemplateManager, init_corp, INDUSTRY_TEMPLATES
from src.core.preset import PresetManager, init_from_preset
from src.core.contract import ContractManager, SuccessContract, ContractStatus
from src.core.knowledge import KnowledgeBase, KnowledgeScope, KnowledgeType
from src.core.ingest import DocumentProcessor, ingest_file
from src.cli.dashboard import Dashboard, run_dashboard, get_status_line


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


def _run_corporation_executor(corp_path: Path, cycles: int = 1, skip_coo: bool = False) -> None:
    """
    Run the CorporationExecutor to process work through all agent tiers.

    This is the key function that connects CEO task submission to full
    autonomous execution through COO → VP → Director → Worker hierarchy.

    Args:
        corp_path: Path to the corporation
        cycles: Number of execution cycles
        skip_coo: If True, skip COO tier (used when delegation already happened)
    """
    print()
    print("=" * 60)
    print("RUNNING CORPORATION EXECUTOR")
    print("Processing work through: VP → Director → Worker")
    print("=" * 60)
    print()

    executor = CorporationExecutor(corp_path)
    executor.initialize()

    print(f"Initialized: {len(executor.vps)} VPs, {len(executor.directors)} Directors, {len(executor.workers)} Workers")
    print()

    for cycle in range(1, cycles + 1):
        print(f"--- Cycle {cycle}/{cycles} ---")

        if skip_coo:
            # Skip COO since delegation already happened
            results = executor.run_cycle_skip_coo()
        else:
            results = executor.run_cycle()

        # Show summary for each tier
        for tier, result in results.items():
            if result.total_agents > 0:
                print(f"  {tier}: {result.completed}/{result.total_agents} agents completed")

        if cycle < cycles:
            print("  Waiting before next cycle...")
            time.sleep(5)

    print()
    print("Corporation execution complete!")


def cmd_ceo(args):
    """Submit a task as CEO"""
    corp_path = get_corp_path()
    coo = COOAgent(corp_path)

    print(f"Submitting task to AI Corp...")
    print(f"Title: {args.title}")
    print(f"Description: {args.description or args.title}")
    print()

    # Create molecule (with or without discovery)
    if args.discover:
        print("=" * 60)
        print("DISCOVERY MODE: Creating Success Contract")
        print("=" * 60)
        print()

        contract, molecule = coo.receive_ceo_task_with_discovery(
            title=args.title,
            description=args.description or args.title,
            priority=args.priority,
            interactive=True
        )

        print(f"\nContract created: {contract.id}")
        print(f"Molecule created: {molecule.id}")
        print(f"Steps: {len(molecule.steps)}")
    else:
        molecule = coo.receive_ceo_task(
            title=args.title,
            description=args.description or args.title,
            priority=args.priority
        )

        print(f"Created molecule: {molecule.id}")
        print(f"Steps: {len(molecule.steps)}")

    # Start and delegate if requested
    if args.start or args.execute:
        print("\nStarting molecule and delegating work...")
        molecule = coo.molecule_engine.start_molecule(molecule.id)
        delegations = coo.delegate_molecule(molecule)
        print(f"Delegated {len(delegations)} steps")

        # Run full hierarchy if --execute
        if args.execute:
            # skip_coo=True because we already delegated above
            _run_corporation_executor(corp_path, args.cycles, skip_coo=True)

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
    elif args.health:
        # Show health monitoring status
        from src.core.monitor import SystemMonitor, AlertSeverity
        monitor = SystemMonitor(corp_path)

        print("AI Corp Health Status")
        print("=" * 50)
        print()
        print(f"Status: {monitor.get_status_summary()}")
        print()

        # Collect and show metrics
        metrics = monitor.collect_metrics()

        print("Agent Health:")
        print("-" * 40)
        for agent_id, status in metrics.agents.items():
            health_icon = {"healthy": "[OK]", "slow": "[!]", "unresponsive": "[X]", "unknown": "[?]"}
            icon = health_icon.get(status.health.value, "[?]")
            work = status.current_work or "idle"
            print(f"  {icon} {agent_id}: {work} (queue: {status.queue_depth})")

        if not metrics.agents:
            print("  No agents registered yet")

        print()
        print("Active Projects:")
        print("-" * 40)
        for mol_id, progress in metrics.molecules.items():
            bar_filled = int(progress / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            print(f"  [{bar}] {progress:.0f}% - {mol_id}")

        if not metrics.molecules:
            print("  No active projects")

        # Show alerts
        alerts = monitor.get_active_alerts()
        if alerts:
            print()
            print("Active Alerts:")
            print("-" * 40)
            for alert in alerts:
                severity_icon = {"critical": "[CRITICAL]", "warning": "[WARNING]", "info": "[INFO]"}
                icon = severity_icon.get(alert.severity.value, "[ALERT]")
                print(f"  {icon} {alert.message}")
                print(f"    Action: {alert.suggested_action}")
        else:
            print()
            print("No active alerts")

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


def cmd_contracts(args):
    """Manage success contracts"""
    corp_path = get_corp_path()
    bead_ledger = BeadLedger(corp_path, auto_commit=False)
    manager = ContractManager(corp_path, bead_ledger=bead_ledger)

    if args.action == 'list':
        # List all contracts
        status_filter = None
        if args.status:
            status_filter = ContractStatus(args.status)

        contracts = manager.list_contracts(status=status_filter)
        if not contracts:
            print("No contracts found")
            return

        print(f"Success Contracts ({len(contracts)}):")
        print("-" * 60)
        for contract in contracts:
            progress = contract.get_progress()
            print(f"{contract.id}: {contract.title}")
            print(f"  Status: {contract.status.value}")
            print(f"  Molecule: {contract.molecule_id or 'Not linked'}")
            print(f"  Progress: {progress['met']}/{progress['total']} ({progress['percent_complete']:.0f}%)")
            print()

    elif args.action == 'show':
        if not args.contract_id:
            print("Error: contract_id required for show")
            return

        contract = manager.get(args.contract_id)
        if not contract:
            print(f"Contract {args.contract_id} not found")
            return

        print(contract.to_display())

    elif args.action == 'create':
        # Interactive contract creation
        print("Creating new Success Contract")
        print("-" * 40)

        title = args.title or input("Title: ").strip()
        if not title:
            print("Error: Title is required")
            return

        objective = args.objective or input("Objective: ").strip()
        if not objective:
            print("Error: Objective is required")
            return

        # Gather success criteria
        print("\nEnter success criteria (one per line, empty line to finish):")
        criteria = []
        if args.criteria:
            criteria = [c.strip() for c in args.criteria.split(';') if c.strip()]
        else:
            while True:
                criterion = input(f"  {len(criteria) + 1}. ").strip()
                if not criterion:
                    break
                criteria.append(criterion)

        if not criteria:
            print("Error: At least one criterion is required")
            return

        # Create the contract
        contract = manager.create(
            title=title,
            objective=objective,
            created_by=args.created_by or 'cli_user',
            success_criteria=criteria,
            in_scope=[s.strip() for s in (args.in_scope or '').split(';') if s.strip()],
            out_of_scope=[s.strip() for s in (args.out_of_scope or '').split(';') if s.strip()],
            constraints=[s.strip() for s in (args.constraints or '').split(';') if s.strip()]
        )

        print(f"\nCreated contract: {contract.id}")
        print(contract.to_display())

    elif args.action == 'check':
        # Mark a criterion as met
        if not args.contract_id:
            print("Error: contract_id required")
            return
        if args.criterion_index is None:
            print("Error: criterion index required (use --index N)")
            return

        contract = manager.update_criterion(
            contract_id=args.contract_id,
            criterion_index=args.criterion_index,
            is_met=True,
            verifier=args.verifier or 'cli_user'
        )

        if not contract:
            print(f"Error: Contract {args.contract_id} not found or invalid criterion index")
            return

        criterion = contract.get_criterion_by_index(args.criterion_index)
        print(f"Marked criterion {args.criterion_index} as met:")
        print(f"  \u2611 {criterion.description}")
        print(f"  Verified by: {criterion.verified_by}")

        progress = contract.get_progress()
        print(f"\nProgress: {progress['met']}/{progress['total']} ({progress['percent_complete']:.0f}%)")

        if contract.is_complete():
            print("\n\u2713 All criteria met! Contract completed.")

    elif args.action == 'link':
        # Link contract to molecule
        if not args.contract_id:
            print("Error: contract_id required")
            return
        if not args.molecule_id:
            print("Error: molecule_id required (use --molecule)")
            return

        contract = manager.link_molecule(
            contract_id=args.contract_id,
            molecule_id=args.molecule_id
        )

        if not contract:
            print(f"Error: Contract {args.contract_id} not found")
            return

        print(f"Linked contract {contract.id} to molecule {args.molecule_id}")

    elif args.action == 'activate':
        if not args.contract_id:
            print("Error: contract_id required")
            return

        contract = manager.activate(args.contract_id)
        if not contract:
            print(f"Error: Contract {args.contract_id} not found")
            return

        print(f"Activated contract: {contract.id}")
        print(f"Status: {contract.status.value}")

    else:
        print(f"Unknown action: {args.action}")


def cmd_init(args):
    """Initialize AI Corp from a preset"""
    from pathlib import Path

    # Determine target path
    if args.path:
        target_path = Path(args.path).resolve()
    else:
        target_path = Path.cwd()

    # Get preset
    preset_id = args.preset or 'software-company'

    print(f"Initializing AI Corp")
    print(f"  Preset: {preset_id}")
    print(f"  Name: {args.name or '(default)'}")
    print(f"  Path: {target_path}")
    print()

    try:
        aicorp_path = init_from_preset(
            preset_id=preset_id,
            target_path=target_path,
            name=args.name
        )

        # Get preset info for display
        manager = PresetManager()
        preset = manager.get_preset(preset_id)

        print(f"AI Corp initialized successfully!")
        print(f"  Location: {aicorp_path}")
        print(f"  Industry: {preset.metadata.industry if preset else 'unknown'}")
        print()
        print("Next steps:")
        print(f"  cd {target_path}")
        print("  ai-corp ceo 'Your first task'")

    except ValueError as e:
        print(f"Error: {e}")
        return
    except FileExistsError as e:
        print(f"Error: {e}")
        print("Use --force to overwrite existing configuration.")
        return


def cmd_presets(args):
    """List or show available presets"""
    manager = PresetManager()

    if args.action == 'list':
        presets = manager.list_presets()
        if not presets:
            print("No presets found.")
            return

        print("Available Presets:")
        print("-" * 60)
        for preset in presets:
            print(f"  {preset.id}")
            print(f"    {preset.name}")
            print(f"    Industry: {preset.industry}")
            print(f"    Complexity: {'*' * preset.complexity}")
            print(f"    Team size: {preset.team_size_min}-{preset.team_size_max}")
            print()

    elif args.action == 'show':
        if not args.preset_id:
            print("Error: preset ID required for show")
            return

        preset = manager.get_preset(args.preset_id)
        if not preset:
            print(f"Preset '{args.preset_id}' not found")
            return

        print(f"Preset: {preset.metadata.name}")
        print("=" * 60)
        print(f"ID:          {preset.metadata.id}")
        print(f"Industry:    {preset.metadata.industry}")
        print(f"Version:     {preset.metadata.version}")
        print(f"Author:      {preset.metadata.author}")
        print(f"Complexity:  {'*' * preset.metadata.complexity} ({preset.metadata.complexity}/5)")
        print()
        print(f"Description:")
        print(f"  {preset.metadata.description}")
        print()
        print(f"Team Size:   {preset.metadata.team_size_min}-{preset.metadata.team_size_max} (default: {preset.metadata.team_size_default})")
        if preset.metadata.tags:
            print(f"Tags:        {', '.join(preset.metadata.tags)}")
        print()

        # Show includes
        includes = preset.includes
        if includes:
            print("Includes:")
            if 'org' in includes:
                print("  Organization:")
                print(f"    - {includes['org'].get('hierarchy', 'N/A')}")
                for role in includes['org'].get('roles', []):
                    print(f"    - {role}")
                for dept in includes['org'].get('departments', []):
                    print(f"    - {dept}")

            if includes.get('workflows'):
                print("  Workflows:")
                for wf in includes['workflows']:
                    print(f"    - {wf}")

            if includes.get('gates'):
                print("  Gates:")
                for gate in includes['gates']:
                    print(f"    - {gate}")


def cmd_init_legacy(args):
    """Initialize AI Corp for an industry (legacy)"""
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


def cmd_knowledge(args):
    """Manage knowledge base"""
    corp_path = get_corp_path()
    kb = KnowledgeBase(corp_path)

    if args.action == 'list':
        # Parse scope filter
        scope = None
        if args.scope:
            scope = KnowledgeScope(args.scope)

        entries = kb.list_entries(scope=scope)

        if not entries:
            print("No knowledge entries found.")
            return

        print(f"Knowledge Entries ({len(entries)}):")
        print("-" * 70)

        for entry in entries:
            scope_str = f"[{entry.scope.value}]"
            if entry.scope_id:
                scope_str += f" ({entry.scope_id[:12]}...)"

            type_str = entry.knowledge_type.value
            print(f"  {entry.id}: {entry.name}")
            print(f"    {scope_str} | Type: {type_str}")
            if entry.tags:
                print(f"    Tags: {', '.join(entry.tags)}")
            print()

    elif args.action == 'show':
        if not args.entry_id:
            print("Error: Entry ID required for show")
            return

        entry = kb.get_entry(args.entry_id)
        if not entry:
            print(f"Entry not found: {args.entry_id}")
            return

        print(f"Knowledge Entry: {entry.name}")
        print("=" * 60)
        print(f"ID:          {entry.id}")
        print(f"Scope:       {entry.scope.value}")
        if entry.scope_id:
            print(f"Scope ID:    {entry.scope_id}")
        print(f"Type:        {entry.knowledge_type.value}")
        print(f"Description: {entry.description[:200]}...")
        print()
        if entry.source_file:
            print(f"Source File: {entry.source_file}")
        if entry.source_url:
            print(f"Source URL:  {entry.source_url}")
        print(f"Uploaded By: {entry.uploaded_by}")
        print(f"Uploaded At: {entry.uploaded_at}")
        if entry.tags:
            print(f"Tags:        {', '.join(entry.tags)}")
        if entry.metadata:
            print(f"\nMetadata:")
            for key, value in entry.metadata.items():
                if key not in ['chunks', 'all_facts']:  # Skip large fields
                    print(f"  {key}: {value}")

    elif args.action == 'add':
        # Determine scope
        if args.foundation:
            scope = KnowledgeScope.FOUNDATION
            scope_id = None
        elif args.project:
            scope = KnowledgeScope.PROJECT
            scope_id = args.project
        elif args.task:
            scope = KnowledgeScope.TASK
            scope_id = args.task
        else:
            scope = KnowledgeScope.FOUNDATION
            scope_id = None

        # Parse tags
        tags = args.tags.split(',') if args.tags else None

        if args.file:
            # Add file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {args.file}")
                return

            print(f"Processing: {file_path.name}...")

            result = ingest_file(
                corp_path=corp_path,
                file_path=file_path,
                scope=scope,
                scope_id=scope_id,
                name=args.name,
                description=args.description,
                tags=tags,
                uploaded_by=args.uploaded_by or "cli"
            )

            if result.success:
                print(f"Added: {result.entry.id}")
                print(f"  Name: {result.entry.name}")
                print(f"  Type: {result.entry.knowledge_type.value}")
                if result.chunks_processed > 0:
                    print(f"  Chunks: {result.chunks_processed}")
                if result.facts_extracted > 0:
                    print(f"  Facts extracted: {result.facts_extracted}")
            else:
                print(f"Error: {result.error}")

        elif args.url:
            # Add URL reference
            processor = DocumentProcessor(kb)
            result = processor.process_url(
                url=args.url,
                scope=scope,
                scope_id=scope_id,
                name=args.name or args.url,
                description=args.description,
                tags=tags,
                uploaded_by=args.uploaded_by or "cli"
            )

            if result.success:
                print(f"Added URL reference: {result.entry.id}")
            else:
                print(f"Error: {result.error}")

        elif args.note:
            # Add text note
            processor = DocumentProcessor(kb)
            result = processor.process_note(
                content=args.note,
                scope=scope,
                scope_id=scope_id,
                name=args.name or "Note",
                description=args.description,
                tags=tags,
                uploaded_by=args.uploaded_by or "cli"
            )

            if result.success:
                print(f"Added note: {result.entry.id}")
            else:
                print(f"Error: {result.error}")

        else:
            print("Error: Must specify --file, --url, or --note")

    elif args.action == 'search':
        if not args.query:
            print("Error: Search query required")
            return

        results = kb.search(args.query)

        if not results:
            print(f"No results found for: {args.query}")
            return

        print(f"Search Results for '{args.query}' ({len(results)}):")
        print("-" * 60)

        for entry in results:
            print(f"  {entry.id}: {entry.name}")
            print(f"    [{entry.scope.value}] {entry.description[:80]}...")
            print()

    elif args.action == 'stats':
        stats = kb.get_stats()

        print("Knowledge Base Statistics")
        print("=" * 40)
        print(f"Total Entries: {stats['total_entries']}")
        print()
        print(f"Foundation: {stats['foundation']['count']} entries")
        print(f"  Size: {stats['foundation']['size']:,} bytes")
        print()
        print(f"Projects:   {stats['projects']['count']} entries")
        print(f"  Size: {stats['projects']['size']:,} bytes")
        print()
        print(f"Tasks:      {stats['tasks']['count']} entries")
        print(f"  Size: {stats['tasks']['size']:,} bytes")

    elif args.action == 'remove':
        if not args.entry_id:
            print("Error: Entry ID required for remove")
            return

        if kb.remove_entry(args.entry_id):
            print(f"Removed: {args.entry_id}")
        else:
            print(f"Entry not found: {args.entry_id}")

    else:
        print(f"Unknown action: {args.action}")


def cmd_dashboard(args):
    """Show the terminal dashboard"""
    corp_path = get_corp_path()

    if args.status_line:
        # Just print a single-line status
        print(get_status_line(corp_path))
        return

    run_dashboard(
        corp_path=corp_path,
        live=args.live,
        refresh_interval=args.interval,
        compact=args.compact
    )


def main():
    parser = argparse.ArgumentParser(
        description='AI Corp - Autonomous AI Corporation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Init command (new preset-based)
    init_parser = subparsers.add_parser('init', help='Initialize AI Corp from a preset')
    init_parser.add_argument('path', nargs='?', help='Target directory (default: current directory)')
    init_parser.add_argument('-p', '--preset', default='software-company',
                            help='Preset to use (default: software-company)')
    init_parser.add_argument('-n', '--name', help='Custom name for this AI Corp instance')
    init_parser.add_argument('-f', '--force', action='store_true',
                            help='Overwrite existing .aicorp directory')
    init_parser.set_defaults(func=cmd_init)

    # Presets command
    presets_parser = subparsers.add_parser('presets', help='List or show available presets')
    presets_parser.add_argument('action', choices=['list', 'show'], default='list', nargs='?')
    presets_parser.add_argument('preset_id', nargs='?', help='Preset ID for show')
    presets_parser.set_defaults(func=cmd_presets)

    # Templates command (legacy)
    templates_parser = subparsers.add_parser('templates', help='List industry templates (legacy)')
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
                           help='Start the molecule immediately (delegates to VPs only)')
    ceo_parser.add_argument('--discover', action='store_true',
                           help='Run discovery conversation to create Success Contract first')
    ceo_parser.add_argument('-x', '--execute', action='store_true',
                           help='Execute work through full hierarchy (VP → Director → Worker)')
    ceo_parser.add_argument('-c', '--cycles', type=int, default=1,
                           help='Number of execution cycles (default: 1)')
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
    status_parser.add_argument('--health', action='store_true',
                              help='Show health monitoring status with alerts')
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

    # Contracts command
    contracts_parser = subparsers.add_parser('contracts', help='Manage success contracts')
    contracts_parser.add_argument('action', choices=['list', 'show', 'create', 'check', 'link', 'activate'],
                                  default='list', nargs='?')
    contracts_parser.add_argument('contract_id', nargs='?', help='Contract ID')
    contracts_parser.add_argument('--status', choices=['draft', 'active', 'completed', 'failed', 'amended'],
                                  help='Filter by status (for list)')
    contracts_parser.add_argument('--title', help='Contract title (for create)')
    contracts_parser.add_argument('--objective', help='Contract objective (for create)')
    contracts_parser.add_argument('--criteria', help='Success criteria separated by ; (for create)')
    contracts_parser.add_argument('--in-scope', help='In scope items separated by ; (for create)')
    contracts_parser.add_argument('--out-of-scope', help='Out of scope items separated by ; (for create)')
    contracts_parser.add_argument('--constraints', help='Constraints separated by ; (for create)')
    contracts_parser.add_argument('--created-by', help='Creator ID (for create)')
    contracts_parser.add_argument('--index', type=int, dest='criterion_index',
                                  help='Criterion index to mark as met (for check)')
    contracts_parser.add_argument('--verifier', help='Verifier ID (for check)')
    contracts_parser.add_argument('--molecule', dest='molecule_id', help='Molecule ID (for link)')
    contracts_parser.set_defaults(func=cmd_contracts)

    # Knowledge command
    knowledge_parser = subparsers.add_parser('knowledge', help='Manage knowledge base')
    knowledge_parser.add_argument('action', choices=['list', 'show', 'add', 'search', 'stats', 'remove'],
                                   default='list', nargs='?')
    knowledge_parser.add_argument('entry_id', nargs='?', help='Entry ID (for show/remove)')
    knowledge_parser.add_argument('--scope', choices=['foundation', 'project', 'task'],
                                   help='Filter by scope (for list)')
    knowledge_parser.add_argument('--foundation', action='store_true',
                                   help='Add to foundation scope')
    knowledge_parser.add_argument('--project', metavar='MOLECULE_ID',
                                   help='Add to project scope with molecule ID')
    knowledge_parser.add_argument('--task', metavar='WORK_ITEM_ID',
                                   help='Add to task scope with work item ID')
    knowledge_parser.add_argument('--file', help='File to add')
    knowledge_parser.add_argument('--url', help='URL to add as reference')
    knowledge_parser.add_argument('--note', help='Text note to add')
    knowledge_parser.add_argument('--name', help='Display name for entry')
    knowledge_parser.add_argument('--description', help='Description for entry')
    knowledge_parser.add_argument('--tags', help='Comma-separated tags')
    knowledge_parser.add_argument('--uploaded-by', help='Uploader identifier')
    knowledge_parser.add_argument('--query', '-q', help='Search query (for search)')
    knowledge_parser.set_defaults(func=cmd_knowledge)

    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='View terminal dashboard')
    dashboard_parser.add_argument('-l', '--live', action='store_true',
                                   help='Run in live mode with auto-refresh')
    dashboard_parser.add_argument('-i', '--interval', type=float, default=5.0,
                                   help='Refresh interval in seconds (default: 5)')
    dashboard_parser.add_argument('-c', '--compact', action='store_true',
                                   help='Show compact single-line output')
    dashboard_parser.add_argument('--status-line', action='store_true',
                                   help='Output plain status line (for scripts/prompts)')
    dashboard_parser.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == '__main__':
    main()
