"""
COO Agent - Chief Operating Officer

The COO is the primary orchestrator of AI Corp, responsible for:
- Receiving tasks from the CEO (human)
- Analyzing scope and creating molecules
- Delegating work to VPs
- Monitoring overall progress
- Reporting results to CEO
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BaseAgent, AgentIdentity
from ..core.molecule import Molecule, MoleculeStep, MoleculeStatus, StepStatus
from ..core.hook import WorkItem, WorkItemPriority
from ..core.channel import MessagePriority, ChannelType
from ..core.raci import RACI, create_raci
from ..core.gate import GateKeeper


class COOAgent(BaseAgent):
    """
    Chief Operating Officer Agent.

    The COO is the main orchestrator that:
    1. Receives high-level tasks from CEO
    2. Breaks them into molecules with steps
    3. Assigns work to VPs
    4. Monitors progress
    5. Reports back to CEO
    """

    VP_MAPPING = {
        'engineering': 'vp_engineering',
        'research': 'vp_research',
        'product': 'vp_product',
        'quality': 'vp_quality',
        'operations': 'vp_operations'
    }

    def __init__(self, corp_path: Path):
        identity = AgentIdentity(
            id="coo-001",
            role_id="coo",
            role_name="Chief Operating Officer",
            department="executive",
            level=1,
            reports_to="ceo",
            direct_reports=list(self.VP_MAPPING.values()),
            skills=[],
            capabilities=['orchestration', 'delegation', 'monitoring', 'reporting']
        )

        super().__init__(identity, corp_path)

        # Initialize gate keeper
        self.gate_keeper = GateKeeper(self.corp_path)

    def process_work(self, work_item: WorkItem) -> Dict[str, Any]:
        """Process a work item (CEO task)"""
        task_type = work_item.context.get('task_type', 'general')

        if task_type == 'new_project':
            return self._handle_new_project(work_item)
        elif task_type == 'status_check':
            return self._handle_status_check(work_item)
        elif task_type == 'review_gate':
            return self._handle_gate_review(work_item)
        else:
            return self._handle_general_task(work_item)

    def receive_ceo_task(
        self,
        title: str,
        description: str,
        priority: str = "P2_MEDIUM",
        context: Optional[Dict[str, Any]] = None
    ) -> Molecule:
        """
        Receive a task from the CEO and create a molecule for it.

        Args:
            title: Task title
            description: Task description
            priority: Priority level
            context: Additional context

        Returns:
            Created molecule
        """
        print(f"[COO] Received task from CEO: {title}")

        # Analyze the task and determine departments involved
        analysis = self._analyze_task(title, description, context or {})

        # Create the main molecule
        molecule = self.molecule_engine.create_molecule(
            name=title,
            description=description,
            created_by=self.identity.id,
            priority=priority
        )

        # Set up RACI
        molecule.raci = create_raci(
            accountable=self.identity.role_id,
            responsible=analysis['departments'],
            informed=['ceo']
        )

        # Create steps based on analysis
        self._create_molecule_steps(molecule, analysis)

        # Save the molecule
        self.molecule_engine._save_molecule(molecule)

        # Record in bead
        self.bead.create(
            entity_type='molecule',
            entity_id=molecule.id,
            data=molecule.to_dict(),
            message=f"Created molecule for CEO task: {title}"
        )

        print(f"[COO] Created molecule {molecule.id} with {len(molecule.steps)} steps")

        return molecule

    def _analyze_task(
        self,
        title: str,
        description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a task to determine scope and required departments"""
        # Simple keyword-based analysis (would be more sophisticated with LLM)
        title_lower = title.lower()
        desc_lower = description.lower()
        combined = f"{title_lower} {desc_lower}"

        departments = []
        needs_research = False
        needs_design = False
        needs_build = False
        needs_qa = False
        needs_security = False

        # Determine required phases
        if any(kw in combined for kw in ['research', 'analyze', 'study', 'investigate', 'evaluate']):
            needs_research = True
            departments.append('vp_research')

        if any(kw in combined for kw in ['design', 'ui', 'ux', 'interface', 'mockup', 'wireframe']):
            needs_design = True
            departments.append('vp_product')

        if any(kw in combined for kw in ['build', 'implement', 'create', 'develop', 'code', 'feature']):
            needs_build = True
            departments.append('vp_engineering')

        if any(kw in combined for kw in ['test', 'qa', 'quality', 'verify', 'validate']):
            needs_qa = True
            departments.append('vp_quality')

        if any(kw in combined for kw in ['security', 'secure', 'vulnerability', 'audit']):
            needs_security = True
            if 'vp_quality' not in departments:
                departments.append('vp_quality')

        # Default: if no specific departments, assume full pipeline
        if not departments:
            departments = ['vp_research', 'vp_product', 'vp_engineering', 'vp_quality']
            needs_research = True
            needs_design = True
            needs_build = True
            needs_qa = True

        # Always include operations for project tracking
        if 'vp_operations' not in departments:
            departments.append('vp_operations')

        return {
            'departments': departments,
            'needs_research': needs_research,
            'needs_design': needs_design,
            'needs_build': needs_build,
            'needs_qa': needs_qa,
            'needs_security': needs_security,
            'estimated_steps': len(departments) * 2,
            'context': context
        }

    def _create_molecule_steps(self, molecule: Molecule, analysis: Dict[str, Any]) -> None:
        """Create steps for a molecule based on analysis"""
        step_order = []

        # Research phase
        if analysis['needs_research']:
            research_step = MoleculeStep.create(
                name="Research & Analysis",
                description="Conduct necessary research and analysis",
                department="research",
                required_capabilities=['research', 'analysis']
            )
            molecule.add_step(research_step)
            step_order.append(research_step.id)

            # Research gate
            research_gate = MoleculeStep.create(
                name="Research Gate",
                description="Review research findings before proceeding",
                department="research",
                is_gate=True,
                gate_id="research",
                depends_on=[research_step.id]
            )
            molecule.add_step(research_gate)
            step_order.append(research_gate.id)

        # Design phase
        if analysis['needs_design']:
            design_step = MoleculeStep.create(
                name="Design & Planning",
                description="Create design specifications and plans",
                department="product",
                required_capabilities=['design', 'planning'],
                depends_on=[step_order[-1]] if step_order else []
            )
            molecule.add_step(design_step)
            step_order.append(design_step.id)

            # Design gate
            design_gate = MoleculeStep.create(
                name="Design Gate",
                description="Review design before implementation",
                department="product",
                is_gate=True,
                gate_id="design",
                depends_on=[design_step.id]
            )
            molecule.add_step(design_gate)
            step_order.append(design_gate.id)

        # Build phase
        if analysis['needs_build']:
            build_step = MoleculeStep.create(
                name="Implementation",
                description="Build and implement the solution",
                department="engineering",
                required_capabilities=['development', 'coding'],
                depends_on=[step_order[-1]] if step_order else []
            )
            molecule.add_step(build_step)
            step_order.append(build_step.id)

            # Build gate
            build_gate = MoleculeStep.create(
                name="Build Gate",
                description="Review implementation before testing",
                department="engineering",
                is_gate=True,
                gate_id="build",
                depends_on=[build_step.id]
            )
            molecule.add_step(build_gate)
            step_order.append(build_gate.id)

        # QA phase
        if analysis['needs_qa']:
            qa_step = MoleculeStep.create(
                name="Quality Assurance",
                description="Test and validate the solution",
                department="quality",
                required_capabilities=['testing', 'qa'],
                depends_on=[step_order[-1]] if step_order else []
            )
            molecule.add_step(qa_step)
            step_order.append(qa_step.id)

            # QA gate
            qa_gate = MoleculeStep.create(
                name="QA Gate",
                description="Review quality before security review",
                department="quality",
                is_gate=True,
                gate_id="qa",
                depends_on=[qa_step.id]
            )
            molecule.add_step(qa_gate)
            step_order.append(qa_gate.id)

        # Security phase
        if analysis['needs_security']:
            security_step = MoleculeStep.create(
                name="Security Review",
                description="Conduct security review and assessment",
                department="quality",
                required_capabilities=['security', 'review'],
                depends_on=[step_order[-1]] if step_order else []
            )
            molecule.add_step(security_step)
            step_order.append(security_step.id)

            # Security gate
            security_gate = MoleculeStep.create(
                name="Security Gate",
                description="Final security approval",
                department="quality",
                is_gate=True,
                gate_id="security",
                depends_on=[security_step.id]
            )
            molecule.add_step(security_gate)

    def delegate_molecule(self, molecule: Molecule) -> List[Dict[str, Any]]:
        """
        Delegate a molecule's steps to appropriate VPs.

        Returns:
            List of delegation results
        """
        delegations = []
        available_steps = molecule.get_next_available_steps()

        for step in available_steps:
            # Determine which VP handles this department
            vp_id = self.VP_MAPPING.get(step.department)
            if not vp_id:
                print(f"[COO] Warning: No VP for department {step.department}")
                continue

            # Create work item in VP's hook
            vp_hook = self.hook_manager.get_or_create_hook(
                name=f"{vp_id} Hook",
                owner_type='role',
                owner_id=vp_id
            )

            work_item = self.hook_manager.add_work_to_hook(
                hook_id=vp_hook.id,
                title=step.name,
                description=step.description,
                molecule_id=molecule.id,
                step_id=step.id,
                priority=WorkItemPriority[molecule.priority],
                required_capabilities=step.required_capabilities,
                context={
                    'molecule_name': molecule.name,
                    'molecule_description': molecule.description,
                    'is_gate': step.is_gate,
                    'gate_id': step.gate_id
                }
            )

            # Send delegation message
            self.delegate_to(
                recipient_id=vp_id,
                recipient_role=vp_id,
                molecule_id=molecule.id,
                step_id=step.id,
                instructions=f"""
Please handle the following task:

Molecule: {molecule.name}
Step: {step.name}
Description: {step.description}

{'This is a GATE step - approval required before proceeding.' if step.is_gate else ''}

Context:
{molecule.description}
""",
                priority=MessagePriority.NORMAL
            )

            # Update step assignment
            step.assigned_to = vp_id
            step.status = StepStatus.PENDING

            delegations.append({
                'step_id': step.id,
                'step_name': step.name,
                'delegated_to': vp_id,
                'work_item_id': work_item.id
            })

            print(f"[COO] Delegated '{step.name}' to {vp_id}")

        # Save molecule with updated assignments
        self.molecule_engine._save_molecule(molecule)

        return delegations

    def _handle_new_project(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle a new project request"""
        # Create molecule from work item
        molecule = self.receive_ceo_task(
            title=work_item.title,
            description=work_item.description,
            priority="P2_MEDIUM",
            context=work_item.context
        )

        # Start the molecule
        molecule = self.molecule_engine.start_molecule(molecule.id)

        # Delegate first steps
        delegations = self.delegate_molecule(molecule)

        return {
            'molecule_id': molecule.id,
            'status': 'started',
            'delegations': delegations
        }

    def _handle_status_check(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle a status check request"""
        # Get all active molecules
        molecules = self.molecule_engine.list_active_molecules()

        status_report = []
        for mol in molecules:
            progress = mol.get_progress()
            status_report.append({
                'molecule_id': mol.id,
                'name': mol.name,
                'status': mol.status.value,
                'progress': progress,
                'current_step': mol.get_current_step().name if mol.get_current_step() else None
            })

        return {
            'active_molecules': len(molecules),
            'molecules': status_report
        }

    def _handle_gate_review(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle a gate review request"""
        gate_id = work_item.context.get('gate_id')
        submission_id = work_item.context.get('submission_id')
        action = work_item.context.get('action', 'review')

        if action == 'approve':
            submission = self.gate_keeper.approve(
                gate_id=gate_id,
                submission_id=submission_id,
                reviewer=self.identity.id
            )
            return {'status': 'approved', 'submission_id': submission.id}

        elif action == 'reject':
            reasons = work_item.context.get('reasons', ['Not specified'])
            submission = self.gate_keeper.reject(
                gate_id=gate_id,
                submission_id=submission_id,
                reviewer=self.identity.id,
                reasons=reasons
            )
            return {'status': 'rejected', 'submission_id': submission.id}

        else:
            # Just list pending
            pending = self.gate_keeper.get_pending_submissions()
            return {
                'pending_submissions': len(pending),
                'submissions': [
                    {'id': s.id, 'gate_id': s.gate_id, 'molecule_id': s.molecule_id}
                    for s in pending
                ]
            }

    def _handle_general_task(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle a general task"""
        # Treat as new project
        return self._handle_new_project(work_item)

    def get_organization_status(self) -> Dict[str, Any]:
        """Get overall organization status"""
        molecules = self.molecule_engine.list_active_molecules()
        pending_gates = self.gate_keeper.get_pending_submissions()

        # Collect department stats
        department_stats = {}
        for vp_id in self.VP_MAPPING.values():
            hook = self.hook_manager.get_hook_for_owner('role', vp_id)
            if hook:
                department_stats[vp_id] = hook.get_stats()

        return {
            'active_molecules': len(molecules),
            'pending_gates': len(pending_gates),
            'departments': department_stats,
            'timestamp': datetime.utcnow().isoformat()
        }

    def report_to_ceo(self) -> str:
        """Generate a status report for the CEO"""
        status = self.get_organization_status()
        molecules = self.molecule_engine.list_active_molecules()

        report = f"""
AI Corp Status Report
=====================
Generated: {status['timestamp']}

Active Projects: {status['active_molecules']}
Pending Gate Reviews: {status['pending_gates']}

Project Summary:
"""
        for mol in molecules:
            progress = mol.get_progress()
            report += f"""
- {mol.name} ({mol.id})
  Status: {mol.status.value}
  Progress: {progress['percent_complete']}% ({progress['completed']}/{progress['total']} steps)
"""

        report += "\nDepartment Workloads:\n"
        for dept, stats in status['departments'].items():
            report += f"- {dept}: {stats.get('queued', 0)} queued, {stats.get('in_progress', 0)} in progress\n"

        return report
