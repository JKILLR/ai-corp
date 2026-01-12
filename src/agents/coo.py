"""
COO Agent - Chief Operating Officer

The COO is the primary orchestrator of AI Corp, responsible for:
- Receiving tasks from the CEO (human)
- Running discovery conversations to create success contracts
- Analyzing scope and creating molecules
- Delegating work to VPs
- Monitoring overall progress
- Reporting results to CEO
"""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from datetime import datetime

from .base import BaseAgent, AgentIdentity
from ..core.molecule import Molecule, MoleculeStep, MoleculeStatus, StepStatus
from ..core.hook import WorkItem, WorkItemPriority
from ..core.channel import MessagePriority, ChannelType
from ..core.raci import RACI, create_raci
from ..core.gate import GateKeeper
from ..core.contract import ContractManager, SuccessContract
from ..core.llm import LLMRequest
from ..core.skills import SkillRegistry
from ..core.forge import (
    TheForge, Intention, IntentionType, IntentionStatus,
    ForgeSession, ForgeSynthesis, IncubationPhase
)


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

    def __init__(
        self,
        corp_path: Path,
        skill_registry: Optional[SkillRegistry] = None
    ):
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

        super().__init__(identity, corp_path, skill_registry=skill_registry)

        # Initialize gate keeper
        self.gate_keeper = GateKeeper(self.corp_path)

        # Initialize contract manager
        self.contract_manager = ContractManager(self.corp_path, bead_ledger=self.bead)

        # Initialize The Forge (intention incubation system)
        self.forge = TheForge(self.corp_path)

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
        """
        Analyze a task to determine scope and required departments.

        Enhanced with organizational memory integration:
        - Queries past decisions for similar tasks
        - Retrieves relevant lessons learned
        - Records analysis decision for future reference
        """
        title_lower = title.lower()
        desc_lower = description.lower()
        combined = f"{title_lower} {desc_lower}"

        # =====================================================================
        # Phase 1: Query Organizational Memory for Context
        # =====================================================================

        # Search for past decisions on similar tasks
        past_decisions = self.search_past_decisions(
            query=f"{title} {description[:100]}",
            tags=['task_analysis', 'department_assignment']
        )

        # Get lessons relevant to this type of task
        relevant_lessons = self.get_relevant_lessons(
            context=f"Task: {title}\nDescription: {description}"
        )

        # Extract insights from organizational memory
        memory_insights = self._extract_memory_insights(
            past_decisions, relevant_lessons, combined
        )

        departments = []
        needs_research = False
        needs_design = False
        needs_build = False
        needs_qa = False
        needs_security = False

        # =====================================================================
        # Phase 2: Apply Memory-Informed Analysis
        # =====================================================================

        # Check if we have strong historical guidance
        if memory_insights.get('recommended_departments'):
            departments = memory_insights['recommended_departments']
            needs_research = 'vp_research' in departments
            needs_design = 'vp_product' in departments
            needs_build = 'vp_engineering' in departments
            needs_qa = 'vp_quality' in departments
            needs_security = memory_insights.get('requires_security', False)
        else:
            # Fall back to keyword-based analysis with lesson-learned enhancements

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

            # Apply lessons: if past tasks like this needed security review, add it
            if memory_insights.get('security_recommended') and not needs_security:
                needs_security = True
                if 'vp_quality' not in departments:
                    departments.append('vp_quality')

            # Apply lessons: if past tasks benefited from research, add it
            if memory_insights.get('research_recommended') and not needs_research:
                needs_research = True
                if 'vp_research' not in departments:
                    departments.insert(0, 'vp_research')

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

        # =====================================================================
        # Phase 3: Record This Analysis Decision
        # =====================================================================

        decision_id = f"task-analysis-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        self.record_decision(
            decision_id=decision_id,
            title=f"Task Analysis: {title[:50]}",
            context=f"Analyzed task '{title}' with description: {description[:200]}",
            options_considered=[
                {'option': 'research_first', 'description': 'Start with research phase'},
                {'option': 'design_first', 'description': 'Start with design phase'},
                {'option': 'build_directly', 'description': 'Skip to implementation'},
                {'option': 'full_pipeline', 'description': 'Complete all phases'}
            ],
            chosen_option=self._determine_pipeline_choice(
                needs_research, needs_design, needs_build
            ),
            rationale=self._build_analysis_rationale(
                memory_insights, departments, needs_research, needs_design, needs_build
            )
        )

        return {
            'departments': departments,
            'needs_research': needs_research,
            'needs_design': needs_design,
            'needs_build': needs_build,
            'needs_qa': needs_qa,
            'needs_security': needs_security,
            'estimated_steps': len(departments) * 2,
            'context': context,
            'memory_insights': memory_insights,
            'decision_id': decision_id
        }

    def _extract_memory_insights(
        self,
        past_decisions: List[Dict[str, Any]],
        lessons: List[Dict[str, Any]],
        task_text: str
    ) -> Dict[str, Any]:
        """Extract actionable insights from organizational memory"""
        insights = {
            'has_precedent': len(past_decisions) > 0,
            'past_decision_count': len(past_decisions),
            'lesson_count': len(lessons),
            'recommended_departments': [],
            'security_recommended': False,
            'research_recommended': False,
            'warnings': [],
            'success_patterns': []
        }

        # Analyze past decisions for similar tasks
        for decision in past_decisions[:5]:  # Limit to 5 most relevant
            context_text = decision.get('context', '').lower()
            chosen = decision.get('chosen_option', '')
            rationale = decision.get('rationale', '')

            # Extract department patterns from past decisions
            if 'security' in rationale.lower() or 'security' in context_text:
                insights['security_recommended'] = True
            if 'research' in rationale.lower() and 'important' in rationale.lower():
                insights['research_recommended'] = True

        # Analyze lessons learned
        for lesson in lessons[:5]:  # Limit to 5 most relevant
            outcome = lesson.get('outcome', '').lower()
            lesson_text = lesson.get('lesson', '')
            recommendations = lesson.get('recommendations', [])

            # Check for failure patterns to avoid
            if 'failed' in outcome or 'issue' in outcome:
                insights['warnings'].append({
                    'lesson_id': lesson.get('lesson_id'),
                    'summary': lesson_text[:100],
                    'recommendations': recommendations[:2]
                })

            # Check for success patterns to replicate
            if 'success' in outcome or 'completed' in outcome:
                insights['success_patterns'].append({
                    'lesson_id': lesson.get('lesson_id'),
                    'pattern': lesson_text[:100]
                })

        return insights

    def _determine_pipeline_choice(
        self,
        needs_research: bool,
        needs_design: bool,
        needs_build: bool
    ) -> str:
        """Determine the pipeline choice based on analysis"""
        if needs_research and needs_design and needs_build:
            return 'full_pipeline'
        elif needs_research:
            return 'research_first'
        elif needs_design:
            return 'design_first'
        else:
            return 'build_directly'

    def _build_analysis_rationale(
        self,
        memory_insights: Dict[str, Any],
        departments: List[str],
        needs_research: bool,
        needs_design: bool,
        needs_build: bool
    ) -> str:
        """Build a rationale string for the analysis decision"""
        rationale_parts = []

        if memory_insights['has_precedent']:
            rationale_parts.append(
                f"Based on {memory_insights['past_decision_count']} similar past decisions."
            )

        if memory_insights['lesson_count'] > 0:
            rationale_parts.append(
                f"Informed by {memory_insights['lesson_count']} relevant lessons learned."
            )

        if memory_insights.get('warnings'):
            rationale_parts.append(
                f"Caution: {len(memory_insights['warnings'])} warning(s) from past issues."
            )

        rationale_parts.append(
            f"Assigned departments: {', '.join(departments)}."
        )

        phases = []
        if needs_research:
            phases.append('research')
        if needs_design:
            phases.append('design')
        if needs_build:
            phases.append('build')

        if phases:
            rationale_parts.append(f"Required phases: {', '.join(phases)}.")

        return ' '.join(rationale_parts) if rationale_parts else "Standard analysis applied."

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

    # =========================================================================
    # Discovery Conversation Methods
    # =========================================================================

    def run_discovery(
        self,
        initial_request: str,
        interactive: bool = True
    ) -> SuccessContract:
        """
        Have a discovery conversation to create a Success Contract.

        This implements a conversational flow where the COO asks questions
        to gather enough information to create a comprehensive contract.

        Args:
            initial_request: The initial task description from CEO
            interactive: If True, prompts for user input. If False, uses LLM to simulate.

        Returns:
            SuccessContract created from the discovery conversation

        Integration Points:
        - Discovery → Contracts: Creates contract via ContractManager
        - Discovery → Beads: Completion recorded in audit trail
        """
        print(f"[COO] Starting discovery conversation...")
        print("=" * 60)

        conversation = [{"role": "user", "content": initial_request}]

        max_turns = 10  # Prevent infinite loops
        turn = 0

        while turn < max_turns:
            turn += 1

            # Get COO's next response/question
            response = self._discovery_turn(conversation)

            # Check if COO wants to finalize
            if "[FINALIZE]" in response:
                # Remove the finalize marker for clean display
                clean_response = response.replace("[FINALIZE]", "").strip()
                print(f"\nCOO: {clean_response}")
                break

            print(f"\nCOO: {response}")

            if interactive:
                # Get user input
                user_input = input("\nYou: ").strip()

                # Check for early confirmation
                if user_input.lower() in ['done', 'yes', 'confirm', 'looks good', 'approved', 'ok']:
                    print("\n[COO] Great! Let me finalize the contract based on our discussion.")
                    break
            else:
                # In non-interactive mode, just proceed
                user_input = "Please continue and finalize when ready."

            conversation.append({"role": "assistant", "content": response})
            conversation.append({"role": "user", "content": user_input})

        # Extract contract from conversation
        contract = self._extract_contract(conversation, initial_request)

        print("\n" + "=" * 60)
        print("[COO] Discovery complete. Contract created:")
        print(contract.to_display())

        # Record discovery completion in bead
        self.bead.create(
            entity_type='contract',
            entity_id=contract.id,
            data={
                'action': 'discovery_complete',
                'contract_id': contract.id,
                'turns': turn,
                'transcript_length': len(conversation)
            },
            message=f"Discovery conversation completed for: {contract.title}"
        )

        return contract

    def _discovery_turn(self, conversation: List[Dict[str, str]]) -> str:
        """
        Execute a single turn of the discovery conversation.

        The COO asks focused questions to gather information needed
        for creating a comprehensive success contract.

        Args:
            conversation: The conversation history so far

        Returns:
            The COO's next message (question or confirmation)
        """
        # Format conversation for the prompt
        formatted_conv = self._format_conversation(conversation)

        # Count what information we have gathered
        gathered_info = self._analyze_gathered_info(conversation)

        prompt = f"""You are the COO of AI Corp conducting a discovery conversation with the CEO.
Your goal is to gather enough information to create a comprehensive Success Contract.

CONVERSATION SO FAR:
{formatted_conv}

INFORMATION GATHERED:
{json.dumps(gathered_info, indent=2)}

YOUR TASK:
Based on what has been discussed, do ONE of the following:

1. If you need MORE information about any of these areas, ask a focused follow-up question:
   - Clear objective (what problem does this solve?)
   - Success criteria (how do we know it's done? be specific and measurable)
   - Scope (what's in/out)
   - Constraints (technical, business, timeline)

2. If you have ENOUGH information (objective, at least 3 success criteria, some scope):
   Summarize your understanding and ask: "Does this capture the requirements? Reply 'yes' to confirm or let me know what to adjust."

3. If the CEO has CONFIRMED your summary:
   Start your response with [FINALIZE] and provide a final summary.

GUIDELINES:
- Be conversational and professional
- Ask ONE question at a time
- Probe vague answers (e.g., "fast" -> "what response time specifically?")
- Suggest missing items (e.g., for auth: "Should we include password reset?")
- Convert vague requirements into measurable criteria

Respond with your next message to the CEO:"""

        # Use LLM to generate response
        if hasattr(self, 'llm') and self.llm:
            try:
                response = self.llm.execute(LLMRequest(prompt=prompt))
                return response.content.strip()
            except Exception as e:
                print(f"[COO] LLM error: {e}, using fallback")

        # Fallback: simple rule-based discovery
        return self._fallback_discovery_turn(conversation, gathered_info)

    def _fallback_discovery_turn(
        self,
        conversation: List[Dict[str, str]],
        gathered_info: Dict[str, Any]
    ) -> str:
        """Fallback discovery logic when LLM is not available"""
        turn_count = len([m for m in conversation if m['role'] == 'assistant'])

        if turn_count == 0:
            return ("Thanks for bringing this to me. To create a solid success contract, "
                   "I need to understand the objective better.\n\n"
                   "What specific problem are we solving? Who will benefit?")

        elif turn_count == 1:
            return ("Got it. Now let's define success criteria.\n\n"
                   "How will we know this is done? What specific, measurable outcomes "
                   "indicate success? (e.g., 'users can log in' or 'response time < 200ms')")

        elif turn_count == 2:
            return ("Good. Let's clarify the scope.\n\n"
                   "What's explicitly IN scope for this project? "
                   "And what should we explicitly NOT include (out of scope)?")

        elif turn_count == 3:
            return ("Almost there. Any constraints I should know about?\n\n"
                   "Technical requirements, existing systems to integrate with, "
                   "timeline, or business rules?")

        else:
            # Summarize and confirm
            return ("[FINALIZE] Based on our discussion, I'll create a Success Contract "
                   "capturing the objective, success criteria, scope, and constraints "
                   "we've discussed. The team will work against these defined criteria.")

    def _extract_contract(
        self,
        conversation: List[Dict[str, str]],
        initial_request: str
    ) -> SuccessContract:
        """
        Extract a structured Success Contract from the conversation.

        Uses LLM to parse the conversation and extract:
        - Title and objective
        - Success criteria
        - Scope (in/out)
        - Constraints

        Args:
            conversation: The full discovery conversation
            initial_request: The original request text

        Returns:
            A new SuccessContract created and saved via ContractManager
        """
        formatted_conv = self._format_conversation(conversation)

        extraction_prompt = f"""Extract a Success Contract from this discovery conversation.

CONVERSATION:
{formatted_conv}

Return ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
    "title": "Short descriptive title (3-7 words)",
    "objective": "Single clear sentence describing what success looks like",
    "success_criteria": [
        "Specific measurable criterion 1",
        "Specific measurable criterion 2",
        "Specific measurable criterion 3"
    ],
    "in_scope": [
        "Item explicitly in scope 1",
        "Item explicitly in scope 2"
    ],
    "out_of_scope": [
        "Item explicitly out of scope 1"
    ],
    "constraints": [
        "Constraint or requirement 1"
    ]
}}

IMPORTANT:
- Title should be concise (e.g., "User Authentication System")
- Objective is ONE sentence describing the end goal
- Success criteria must be SPECIFIC and MEASURABLE (not vague)
- Include at least 3 success criteria
- If scope or constraints weren't discussed, use reasonable defaults based on the objective"""

        extracted_data = None

        # Try LLM extraction
        if hasattr(self, 'llm') and self.llm:
            try:
                response = self.llm.execute(LLMRequest(prompt=extraction_prompt))
                content = response.content.strip()

                # Try to parse JSON from the response
                # Handle potential markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                extracted_data = json.loads(content)
            except Exception as e:
                print(f"[COO] LLM extraction error: {e}, using fallback")

        # Fallback extraction
        if not extracted_data:
            extracted_data = self._fallback_extract_contract(conversation, initial_request)

        # Create transcript for record keeping
        transcript = "\n".join([
            f"{'CEO' if m['role'] == 'user' else 'COO'}: {m['content']}"
            for m in conversation
        ])

        # Create contract via ContractManager
        contract = self.contract_manager.create(
            title=extracted_data.get('title', initial_request[:50]),
            objective=extracted_data.get('objective', initial_request),
            created_by=self.identity.id,
            success_criteria=extracted_data.get('success_criteria', []),
            in_scope=extracted_data.get('in_scope', []),
            out_of_scope=extracted_data.get('out_of_scope', []),
            constraints=extracted_data.get('constraints', []),
            discovery_transcript=transcript
        )

        return contract

    def _fallback_extract_contract(
        self,
        conversation: List[Dict[str, str]],
        initial_request: str
    ) -> Dict[str, Any]:
        """Fallback contract extraction when LLM is not available"""
        # Simple extraction based on conversation content
        all_text = " ".join([m['content'] for m in conversation])

        # Generate title from initial request
        title = initial_request.split('.')[0][:50]
        if len(title) < 10:
            title = f"Project: {initial_request[:40]}"

        # Default success criteria based on common patterns
        success_criteria = []

        # Look for explicit criteria mentions
        criteria_patterns = [
            r'users? can ([^.]+)',
            r'should (?:be able to )?([^.]+)',
            r'must ([^.]+)',
            r'criteria[: ]+([^.]+)',
            r'success[: ]+([^.]+)',
        ]

        for pattern in criteria_patterns:
            matches = re.findall(pattern, all_text.lower())
            for match in matches[:3]:  # Limit to 3 per pattern
                criterion = match.strip().capitalize()
                if len(criterion) > 10 and criterion not in success_criteria:
                    success_criteria.append(criterion)

        # Add defaults if we don't have enough
        if len(success_criteria) < 3:
            success_criteria.extend([
                "Core functionality implemented",
                "Tests passing with reasonable coverage",
                "Code reviewed and approved"
            ][:3 - len(success_criteria)])

        return {
            'title': title,
            'objective': initial_request,
            'success_criteria': success_criteria[:5],  # Max 5 criteria
            'in_scope': ["Core implementation", "Unit tests"],
            'out_of_scope': ["Future enhancements"],
            'constraints': []
        }

    def _format_conversation(self, conversation: List[Dict[str, str]]) -> str:
        """Format conversation history for prompts"""
        lines = []
        for msg in conversation:
            role = "CEO" if msg['role'] == 'user' else "COO"
            lines.append(f"{role}: {msg['content']}")
        return "\n\n".join(lines)

    def _analyze_gathered_info(self, conversation: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze what information has been gathered from the conversation"""
        all_text = " ".join([m['content'] for m in conversation]).lower()

        return {
            'has_objective': any(word in all_text for word in ['problem', 'goal', 'objective', 'solve', 'need']),
            'has_criteria': any(word in all_text for word in ['criteria', 'success', 'measure', 'done', 'complete']),
            'has_scope': any(word in all_text for word in ['scope', 'include', 'exclude', 'in scope', 'out of scope']),
            'has_constraints': any(word in all_text for word in ['constraint', 'requirement', 'must', 'timeline', 'deadline']),
            'turn_count': len([m for m in conversation if m['role'] == 'assistant'])
        }

    def receive_ceo_task_with_discovery(
        self,
        title: str,
        description: str,
        priority: str = "P2_MEDIUM",
        context: Optional[Dict[str, Any]] = None,
        interactive: bool = True
    ) -> tuple[SuccessContract, Molecule]:
        """
        Receive a task from CEO with discovery conversation.

        This enhanced method runs a discovery conversation first to create
        a Success Contract, then creates and links a Molecule for execution.

        Args:
            title: Task title
            description: Task description
            priority: Priority level
            context: Additional context
            interactive: Whether to run interactive discovery

        Returns:
            Tuple of (SuccessContract, Molecule)

        Integration Points:
        - Discovery → Contracts: Creates contract
        - Contracts → Molecules: Links contract to molecule
        - Discovery → Beads: All operations recorded
        """
        # Run discovery to create contract
        initial_request = f"{title}: {description}"
        contract = self.run_discovery(initial_request, interactive=interactive)

        # Create molecule using standard method
        molecule = self.receive_ceo_task(
            title=contract.title,
            description=contract.objective,
            priority=priority,
            context=context
        )

        # Link contract to molecule
        self.contract_manager.link_molecule(contract.id, molecule.id, agent_id=self.identity.id)

        # Activate contract
        self.contract_manager.activate(contract.id, agent_id=self.identity.id)

        # Update molecule with contract_id
        molecule.contract_id = contract.id
        self.molecule_engine._save_molecule(molecule)

        print(f"\n[COO] Contract {contract.id} linked to Molecule {molecule.id}")
        print(f"[COO] Contract activated. Work can begin!")

        return contract, molecule

    # =========================================================================
    # CEO-COO Conversation Persistence Layer
    # =========================================================================

    def get_conversation_store_path(self) -> Path:
        """Get the path to the CEO-COO conversation store"""
        store_path = self.corp_path / "conversations" / "ceo_coo"
        store_path.mkdir(parents=True, exist_ok=True)
        return store_path

    def create_conversation_thread(
        self,
        title: str,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation thread with the CEO.

        Args:
            title: Thread title/subject
            context: Initial context for the conversation
            tags: Optional tags for categorization

        Returns:
            Thread metadata including ID
        """
        thread_id = f"thread-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        thread_data = {
            'id': thread_id,
            'title': title,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'status': 'active',
            'tags': tags or [],
            'context': context or '',
            'messages': [],
            'linked_molecules': [],
            'linked_contracts': [],
            'summary': '',
            'key_decisions': []
        }

        # Save thread
        thread_path = self.get_conversation_store_path() / f"{thread_id}.json"
        thread_path.write_text(json.dumps(thread_data, indent=2))

        # Record in bead for audit trail
        self.bead.create(
            entity_type='conversation_thread',
            entity_id=thread_id,
            data={'action': 'created', 'title': title},
            message=f"Created conversation thread: {title}"
        )

        print(f"[COO] Created conversation thread: {thread_id}")
        return thread_data

    def add_message_to_thread(
        self,
        thread_id: str,
        role: str,  # 'ceo' or 'coo'
        content: str,
        message_type: str = 'message',  # 'message', 'question', 'decision', 'directive'
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to an existing conversation thread.

        Args:
            thread_id: ID of the thread
            role: Who sent the message ('ceo' or 'coo')
            content: Message content
            message_type: Type of message
            metadata: Additional message metadata

        Returns:
            The added message
        """
        thread_path = self.get_conversation_store_path() / f"{thread_id}.json"

        if not thread_path.exists():
            raise ValueError(f"Thread {thread_id} not found")

        thread_data = json.loads(thread_path.read_text())

        message = {
            'id': f"msg-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]}",
            'role': role,
            'content': content,
            'type': message_type,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        thread_data['messages'].append(message)
        thread_data['updated_at'] = datetime.utcnow().isoformat()

        # If it's a decision, record it
        if message_type == 'decision':
            thread_data['key_decisions'].append({
                'message_id': message['id'],
                'summary': content[:200],
                'timestamp': message['timestamp']
            })

        # Save updated thread
        thread_path.write_text(json.dumps(thread_data, indent=2))

        return message

    def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation thread by ID"""
        thread_path = self.get_conversation_store_path() / f"{thread_id}.json"

        if not thread_path.exists():
            return None

        return json.loads(thread_path.read_text())

    def list_threads(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List conversation threads with optional filters.

        Args:
            status: Filter by status ('active', 'archived', 'resolved')
            tags: Filter by tags
            limit: Maximum number of threads to return

        Returns:
            List of thread metadata
        """
        threads = []
        store_path = self.get_conversation_store_path()

        for thread_file in sorted(store_path.glob("thread-*.json"), reverse=True):
            try:
                thread_data = json.loads(thread_file.read_text())

                if status and thread_data.get('status') != status:
                    continue

                if tags and not any(t in thread_data.get('tags', []) for t in tags):
                    continue

                # Return summary info, not full messages
                threads.append({
                    'id': thread_data['id'],
                    'title': thread_data['title'],
                    'status': thread_data['status'],
                    'created_at': thread_data['created_at'],
                    'updated_at': thread_data['updated_at'],
                    'message_count': len(thread_data['messages']),
                    'tags': thread_data.get('tags', [])
                })

                if len(threads) >= limit:
                    break

            except Exception as e:
                print(f"[COO] Error loading thread {thread_file}: {e}")
                continue

        return threads

    def get_thread_context(
        self,
        thread_id: str,
        max_messages: int = 20
    ) -> str:
        """
        Get formatted context from a thread for use in analysis.

        Returns recent messages formatted for LLM context injection.
        """
        thread = self.get_thread(thread_id)
        if not thread:
            return ""

        context_parts = [
            f"Conversation Thread: {thread['title']}",
            f"Created: {thread['created_at']}",
            "-" * 40
        ]

        # Get recent messages
        messages = thread['messages'][-max_messages:]

        for msg in messages:
            role_label = "CEO" if msg['role'] == 'ceo' else "COO"
            context_parts.append(f"{role_label}: {msg['content']}")

        if thread.get('key_decisions'):
            context_parts.append("-" * 40)
            context_parts.append("Key Decisions Made:")
            for decision in thread['key_decisions'][-5:]:
                context_parts.append(f"  • {decision['summary']}")

        return "\n".join(context_parts)

    def link_thread_to_molecule(
        self,
        thread_id: str,
        molecule_id: str
    ) -> None:
        """Link a conversation thread to a molecule for tracking"""
        thread_path = self.get_conversation_store_path() / f"{thread_id}.json"

        if not thread_path.exists():
            raise ValueError(f"Thread {thread_id} not found")

        thread_data = json.loads(thread_path.read_text())

        if molecule_id not in thread_data['linked_molecules']:
            thread_data['linked_molecules'].append(molecule_id)
            thread_data['updated_at'] = datetime.utcnow().isoformat()
            thread_path.write_text(json.dumps(thread_data, indent=2))

    def update_thread_summary(
        self,
        thread_id: str,
        summary: str
    ) -> None:
        """Update the summary for a conversation thread"""
        thread_path = self.get_conversation_store_path() / f"{thread_id}.json"

        if not thread_path.exists():
            raise ValueError(f"Thread {thread_id} not found")

        thread_data = json.loads(thread_path.read_text())
        thread_data['summary'] = summary
        thread_data['updated_at'] = datetime.utcnow().isoformat()
        thread_path.write_text(json.dumps(thread_data, indent=2))

    # =========================================================================
    # Lesson Learning from Execution Outcomes
    # =========================================================================

    def record_execution_outcome(
        self,
        molecule_id: str,
        outcome: str,  # 'success', 'partial', 'failed'
        details: str,
        factors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Record the outcome of a molecule execution and extract lessons.

        Args:
            molecule_id: The molecule that was executed
            outcome: Overall outcome classification
            details: Detailed description of what happened
            factors: Contributing factors (positive or negative)

        Returns:
            The recorded lesson
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        # Analyze execution for lessons
        analysis = self._analyze_execution(molecule, outcome, details, factors or [])

        # Record lesson learned
        lesson_id = f"lesson-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        lesson = self.record_lesson_learned(
            lesson_id=lesson_id,
            title=f"Execution Outcome: {molecule.name}",
            situation=f"Executed molecule '{molecule.name}' ({molecule_id})",
            action_taken=self._summarize_molecule_actions(molecule),
            outcome=f"{outcome}: {details}",
            lesson=analysis['lesson'],
            recommendations=analysis['recommendations'],
            severity=analysis['severity']
        )

        # If there were issues, flag for future similar tasks
        if outcome != 'success' and analysis.get('patterns_to_avoid'):
            self._record_avoidance_patterns(
                molecule, analysis['patterns_to_avoid']
            )

        print(f"[COO] Recorded lesson from {molecule.name}: {analysis['lesson'][:100]}")

        return lesson

    def _analyze_execution(
        self,
        molecule: Molecule,
        outcome: str,
        details: str,
        factors: List[str]
    ) -> Dict[str, Any]:
        """Analyze a molecule execution to extract lessons"""
        analysis = {
            'severity': 'info',
            'lesson': '',
            'recommendations': [],
            'patterns_to_avoid': []
        }

        if outcome == 'success':
            analysis['severity'] = 'info'
            analysis['lesson'] = f"Successfully completed {molecule.name}. " + (
                f"Key factors: {', '.join(factors[:3])}" if factors else
                "Standard execution worked well."
            )
            analysis['recommendations'] = [
                f"Continue using {molecule.steps[0].department if molecule.steps else 'standard'} approach for similar tasks"
            ]

        elif outcome == 'partial':
            analysis['severity'] = 'warning'
            analysis['lesson'] = f"Partially completed {molecule.name}. {details}"
            analysis['recommendations'] = [
                "Review step dependencies for gaps",
                "Consider adding validation checkpoints",
                "Ensure clearer success criteria"
            ]

        elif outcome == 'failed':
            analysis['severity'] = 'error'
            analysis['lesson'] = f"Failed to complete {molecule.name}. Root cause: {details}"
            analysis['recommendations'] = [
                "Add more research phase before implementation",
                "Include earlier stakeholder review",
                "Break into smaller, more manageable molecules"
            ]
            analysis['patterns_to_avoid'] = factors

        return analysis

    def _summarize_molecule_actions(self, molecule: Molecule) -> str:
        """Summarize the actions taken during molecule execution"""
        completed_steps = [s for s in molecule.steps if s.status == StepStatus.COMPLETED]
        failed_steps = [s for s in molecule.steps if s.status == StepStatus.FAILED]

        summary_parts = [
            f"Executed {len(completed_steps)}/{len(molecule.steps)} steps."
        ]

        if completed_steps:
            summary_parts.append(
                f"Completed: {', '.join(s.name for s in completed_steps[:3])}"
            )

        if failed_steps:
            summary_parts.append(
                f"Failed: {', '.join(s.name for s in failed_steps[:3])}"
            )

        return " ".join(summary_parts)

    def _record_avoidance_patterns(
        self,
        molecule: Molecule,
        patterns: List[str]
    ) -> None:
        """Record patterns to avoid in future similar tasks"""
        for pattern in patterns[:5]:  # Limit to 5 patterns
            self.bead.create(
                entity_type='avoidance_pattern',
                entity_id=f"avoid-{uuid.uuid4().hex[:8]}",
                data={
                    'pattern': pattern,
                    'source_molecule': molecule.id,
                    'molecule_name': molecule.name,
                    'recorded_at': datetime.utcnow().isoformat()
                },
                message=f"Pattern to avoid: {pattern}"
            )

    # =========================================================================
    # Context Loading on Session Start
    # =========================================================================

    def load_session_context(self) -> Dict[str, Any]:
        """
        Load comprehensive context at the start of a COO session.

        Returns organizational state, recent decisions, active threads,
        and relevant lessons for the COO to have full situational awareness.
        """
        context = {
            'loaded_at': datetime.utcnow().isoformat(),
            'ceo_preferences': [],
            'organization_status': {},
            'active_molecules': [],
            'pending_gates': [],
            'recent_decisions': [],
            'active_conversations': [],
            'recent_lessons': [],
            'warnings': []
        }

        # Load CEO preferences (highest priority)
        try:
            context['ceo_preferences'] = self.org_memory.get_priority_preferences("high")
        except Exception as e:
            context['warnings'].append(f"Failed to load CEO preferences: {e}")

        # Load organization status
        try:
            context['organization_status'] = self.get_organization_status()
        except Exception as e:
            context['warnings'].append(f"Failed to load org status: {e}")

        # Load active molecules
        try:
            molecules = self.molecule_engine.list_active_molecules()
            context['active_molecules'] = [
                {
                    'id': m.id,
                    'name': m.name,
                    'status': m.status.value,
                    'progress': m.get_progress()
                }
                for m in molecules[:10]  # Limit to 10 most recent
            ]
        except Exception as e:
            context['warnings'].append(f"Failed to load molecules: {e}")

        # Load pending gates
        try:
            pending = self.gate_keeper.get_pending_submissions()
            context['pending_gates'] = [
                {'id': s.id, 'gate_id': s.gate_id, 'molecule_id': s.molecule_id}
                for s in pending[:5]
            ]
        except Exception as e:
            context['warnings'].append(f"Failed to load gates: {e}")

        # Load recent decisions from organizational memory
        try:
            recent_decisions = self.search_past_decisions(
                query="",  # Get all recent
                tags=None
            )
            context['recent_decisions'] = recent_decisions[:10]
        except Exception as e:
            context['warnings'].append(f"Failed to load decisions: {e}")

        # Load active conversation threads
        try:
            context['active_conversations'] = self.list_threads(
                status='active',
                limit=5
            )
        except Exception as e:
            context['warnings'].append(f"Failed to load conversations: {e}")

        # Load recent lessons
        try:
            recent_lessons = self.get_relevant_lessons(
                context="Recent organizational activities"
            )
            context['recent_lessons'] = recent_lessons[:5]
        except Exception as e:
            context['warnings'].append(f"Failed to load lessons: {e}")

        print(f"[COO] Session context loaded: "
              f"{len(context['active_molecules'])} molecules, "
              f"{len(context['pending_gates'])} gates pending, "
              f"{len(context['active_conversations'])} active threads")

        return context

    def get_context_summary_for_llm(self) -> str:
        """
        Get a formatted context summary suitable for LLM prompt injection.

        This provides the COO's current situational awareness in a format
        that can be prepended to LLM prompts.
        """
        context = self.load_session_context()

        summary_parts = [
            "=== COO CONTEXT SUMMARY ===",
            f"Generated: {context['loaded_at']}",
            ""
        ]

        # CEO Preferences (highest priority - always at top)
        ceo_prefs = context.get('ceo_preferences', [])
        if ceo_prefs:
            summary_parts.append("CEO PREFERENCES (Always Follow):")
            for pref in ceo_prefs:
                summary_parts.append(f"  ★ {pref.get('rule', '')}")
            summary_parts.append("")

        # Organization status
        org_status = context.get('organization_status', {})
        summary_parts.append("ORGANIZATION STATUS:")
        summary_parts.append(f"  Active Molecules: {org_status.get('active_molecules', 0)}")
        summary_parts.append(f"  Pending Gates: {org_status.get('pending_gates', 0)}")
        summary_parts.append("")

        # Active work
        if context['active_molecules']:
            summary_parts.append("ACTIVE WORK:")
            for mol in context['active_molecules'][:5]:
                progress = mol.get('progress', {})
                summary_parts.append(
                    f"  • {mol['name']}: {progress.get('percent_complete', 0)}% complete"
                )
            summary_parts.append("")

        # Pending gates needing attention
        if context['pending_gates']:
            summary_parts.append("PENDING GATES (need review):")
            for gate in context['pending_gates']:
                summary_parts.append(f"  • Gate {gate['gate_id']} for molecule {gate['molecule_id']}")
            summary_parts.append("")

        # Recent decisions for continuity
        if context['recent_decisions']:
            summary_parts.append("RECENT DECISIONS:")
            for decision in context['recent_decisions'][:3]:
                summary_parts.append(
                    f"  • {decision.get('title', 'Unknown')}: {decision.get('chosen_option', 'N/A')}"
                )
            summary_parts.append("")

        # Active conversations with CEO
        if context['active_conversations']:
            summary_parts.append("ACTIVE CEO CONVERSATIONS:")
            for thread in context['active_conversations']:
                summary_parts.append(
                    f"  • {thread['title']} ({thread['message_count']} messages)"
                )
            summary_parts.append("")

        # Warnings/lessons to keep in mind
        if context['recent_lessons']:
            summary_parts.append("RECENT LESSONS (keep in mind):")
            for lesson in context['recent_lessons'][:2]:
                summary_parts.append(f"  • {lesson.get('lesson', '')[:100]}")
            summary_parts.append("")

        if context['warnings']:
            summary_parts.append("WARNINGS:")
            for warning in context['warnings']:
                summary_parts.append(f"  ⚠ {warning}")

        summary_parts.append("=== END CONTEXT ===")

        return "\n".join(summary_parts)

    # =========================================================================
    # The Forge - Intention Incubation Integration
    # =========================================================================

    def capture_intention(
        self,
        title: str,
        description: str,
        intention_type: str = "idea",
        priority: int = 3,
        from_thread: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Intention:
        """
        Capture a new intention into The Forge.

        Can be called directly or from conversation context.

        Args:
            title: Short title for the intention
            description: Full description
            intention_type: 'idea', 'goal', 'vision', 'problem', 'wish'
            priority: 1 (highest) to 5 (lowest)
            from_thread: Thread ID if captured from conversation
            tags: Optional categorization tags
        """
        type_map = {
            'idea': IntentionType.IDEA,
            'goal': IntentionType.GOAL,
            'vision': IntentionType.VISION,
            'problem': IntentionType.PROBLEM,
            'wish': IntentionType.WISH
        }

        int_type = type_map.get(intention_type.lower(), IntentionType.IDEA)

        intention = self.forge.capture(
            title=title,
            description=description,
            intention_type=int_type,
            source="ceo" if not from_thread else "ceo_conversation",
            priority=priority,
            captured_in_thread=from_thread,
            tags=tags
        )

        # Record in bead
        self.bead.create(
            entity_type='intention',
            entity_id=intention.id,
            data={'action': 'captured', 'title': title, 'type': intention_type},
            message=f"Captured intention: {title}"
        )

        return intention

    def triage_intention(
        self,
        intention_id: str,
        passed: bool,
        notes: str = "",
        adjusted_priority: Optional[int] = None
    ) -> Intention:
        """
        Triage an intention - quick COO assessment.

        Determines if intention is ready for incubation or needs
        to be discarded/clarified.
        """
        intention = self.forge.triage(
            intention_id=intention_id,
            passed=passed,
            notes=notes,
            adjusted_priority=adjusted_priority
        )

        # Record decision
        self.record_decision(
            decision_id=f"triage-{intention_id}",
            title=f"Triage: {intention.title}",
            context=f"Assessed intention for Forge incubation",
            options_considered=[
                {'option': 'pass', 'description': 'Ready for incubation'},
                {'option': 'fail', 'description': 'Discard or needs work'}
            ],
            chosen_option='pass' if passed else 'fail',
            rationale=notes or "Standard triage assessment"
        )

        return intention

    def start_forge_session(
        self,
        intention_id: str,
        time_budget_minutes: int = 120
    ) -> ForgeSession:
        """
        Start a Forge incubation session for an intention.

        Assembles the incubator team based on intention type.
        """
        intention = self.forge.get_intention(intention_id)
        if not intention:
            raise ValueError(f"Intention {intention_id} not found")

        # Determine team based on intention type
        team = self._assemble_forge_team(intention)

        session = self.forge.start_session(
            intention_id=intention_id,
            assigned_agents=list(team.keys()),
            agent_roles=team,
            time_budget_minutes=time_budget_minutes
        )

        # Record in bead
        self.bead.create(
            entity_type='forge_session',
            entity_id=session.id,
            data={
                'action': 'started',
                'intention_id': intention_id,
                'team': team
            },
            message=f"Started Forge session for: {intention.title}"
        )

        return session

    def _assemble_forge_team(self, intention: Intention) -> Dict[str, str]:
        """
        Assemble the incubator team based on intention type.

        Returns dict of agent_id -> role.
        """
        team = {}

        # Always include research for exploration
        team['research-001'] = 'Explorer'

        # Add based on intention type
        if intention.intention_type == IntentionType.IDEA:
            team['product-001'] = 'Feasibility Analyst'
            team['devils-advocate-001'] = 'Critical Reviewer'

        elif intention.intention_type == IntentionType.GOAL:
            team['product-001'] = 'Strategy Planner'
            team['engineering-001'] = 'Technical Assessor'

        elif intention.intention_type == IntentionType.VISION:
            team['product-001'] = 'Vision Architect'
            team['research-002'] = 'Trend Analyst'

        elif intention.intention_type == IntentionType.PROBLEM:
            team['engineering-001'] = 'Root Cause Analyst'
            team['product-001'] = 'Solution Designer'

        elif intention.intention_type == IntentionType.WISH:
            team['product-001'] = 'Requirements Translator'
            team['design-001'] = 'Experience Designer'

        return team

    def relay_to_forge(
        self,
        content: str,
        input_type: str = "direction"
    ) -> bool:
        """
        Relay CEO input to the active Forge session.

        Called when CEO discusses the incubating intention in chat.
        """
        session = self.forge.get_active_session()
        if not session:
            return False

        self.forge.add_ceo_input(
            session_id=session.id,
            content=content,
            input_type=input_type
        )

        return True

    def get_forge_status(self) -> Dict[str, Any]:
        """Get current Forge status for reporting."""
        return self.forge.get_status()

    def get_forge_workspace(self) -> Dict[str, Any]:
        """Get the current workspace view for UI display."""
        return self.forge.get_workspace_view()

    def approve_intention(
        self,
        intention_id: str,
        notes: str = ""
    ) -> tuple[Intention, Optional[Molecule]]:
        """
        Approve an intention and optionally create a project.

        Returns the approved intention and resulting molecule if created.
        """
        intention = self.forge.approve(
            intention_id=intention_id,
            approved_by="ceo",
            notes=notes
        )

        # Get the synthesis if available
        session = None
        if intention.forge_session_id:
            session = self.forge.get_session(intention.forge_session_id)

        molecule = None
        if session and session.synthesis:
            # Create molecule from synthesis
            molecule = self.receive_ceo_task(
                title=intention.title,
                description=session.synthesis.approach_summary,
                priority="P2_MEDIUM",
                context={
                    'from_forge': True,
                    'intention_id': intention.id,
                    'synthesis': session.synthesis.to_dict()
                }
            )

            # Link back
            intention.resulting_molecule_id = molecule.id
            self.forge._save_intention(intention)

        # Record
        self.bead.create(
            entity_type='intention',
            entity_id=intention.id,
            data={
                'action': 'approved',
                'molecule_id': molecule.id if molecule else None
            },
            message=f"Approved intention: {intention.title}"
        )

        return intention, molecule

    def hold_intention(
        self,
        intention_id: str,
        reason: str,
        until: Optional[str] = None,
        trigger: Optional[str] = None
    ) -> Intention:
        """Put an intention on hold."""
        intention = self.forge.hold(
            intention_id=intention_id,
            reason=reason,
            until=until,
            trigger=trigger
        )

        self.bead.create(
            entity_type='intention',
            entity_id=intention.id,
            data={'action': 'on_hold', 'reason': reason, 'trigger': trigger},
            message=f"Put intention on hold: {intention.title}"
        )

        return intention

    def discard_intention(
        self,
        intention_id: str,
        reason: str
    ) -> Intention:
        """Discard an intention with reasoning."""
        intention = self.forge.discard(
            intention_id=intention_id,
            reason=reason
        )

        self.bead.create(
            entity_type='intention',
            entity_id=intention.id,
            data={'action': 'discarded', 'reason': reason},
            message=f"Discarded intention: {intention.title}"
        )

        # Record lesson if there was a session
        if intention.forge_session_id:
            session = self.forge.get_session(intention.forge_session_id)
            if session:
                self.record_lesson_learned(
                    lesson_id=f"discard-{intention.id}",
                    title=f"Discarded: {intention.title}",
                    situation=f"Intention '{intention.title}' went through Forge",
                    action_taken="Full incubation with team exploration",
                    outcome=f"Discarded: {reason}",
                    lesson=f"This type of {intention.intention_type.value} may not be viable",
                    recommendations=[
                        "Consider filtering similar intentions at triage",
                        f"Key discard reason: {reason}"
                    ],
                    severity="info"
                )

        return intention

    def get_forge_summary_for_llm(self) -> str:
        """
        Get Forge status formatted for LLM context.

        Included in COO's context awareness.
        """
        status = self.forge.get_status()

        lines = [
            "=== THE FORGE STATUS ===",
            f"Inbox: {status['inbox_count']} awaiting triage",
            f"Queue: {status['queue_count']} awaiting incubation",
            f"Ready for Review: {status['ready_for_review']}",
            f"On Hold: {status['on_hold']}"
        ]

        if status['active_session']:
            s = status['active_session']
            lines.append(f"\nACTIVE INCUBATION:")
            lines.append(f"  {s['intention_title']}")
            lines.append(f"  Phase: {s['phase']}")
            lines.append(f"  Workspace entries: {s['workspace_entries']}")
            lines.append(f"  Agents: {', '.join(s['assigned_agents'])}")

        return "\n".join(lines)


# Need uuid for thread IDs
import uuid
