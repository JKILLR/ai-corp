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
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BaseAgent, AgentIdentity
from ..core.molecule import Molecule, MoleculeStep, MoleculeStatus, StepStatus
from ..core.hook import WorkItem, WorkItemPriority
from ..core.channel import MessagePriority, ChannelType
from ..core.raci import RACI, create_raci
from ..core.gate import GateKeeper
from ..core.contract import ContractManager, SuccessContract
from ..core.llm import LLMRequest


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

        # Initialize contract manager
        self.contract_manager = ContractManager(self.corp_path, bead_ledger=self.bead)

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
