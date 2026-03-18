"""
VP Agent - Vice President Agent Implementation

VPs are department heads responsible for:
- Receiving work delegated from COO
- Breaking down work into director-level tasks
- Managing directors and worker pools
- Ensuring quality gates are met
- Reporting to COO

Each department has one VP:
- VP Engineering
- VP Research
- VP Product
- VP Quality
- VP Operations
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base import BaseAgent, AgentIdentity
from ..core.molecule import MoleculeStep, StepStatus
from ..core.hook import WorkItem, WorkItemPriority
from ..core.channel import MessagePriority
from ..core.gate import GateKeeper
from ..core.pool import PoolManager
from ..core.memory import ContextType

logger = logging.getLogger(__name__)


class VPAgent(BaseAgent):
    """
    Vice President Agent.

    VPs receive work from COO and delegate to directors.
    They are responsible for department-level outcomes.
    """

    def __init__(
        self,
        role_id: str,
        role_name: str,
        department: str,
        corp_path: Path,
        direct_reports: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None
    ):
        identity = AgentIdentity(
            id=f"{role_id}-001",
            role_id=role_id,
            role_name=role_name,
            department=department,
            level=2,  # VP level
            reports_to="coo",
            direct_reports=direct_reports or [],
            skills=skills or [],
            capabilities=capabilities or ['delegation', 'planning', 'review']
        )

        super().__init__(identity, corp_path)

        # Initialize gate keeper for quality gate management
        self.gate_keeper = GateKeeper(self.corp_path)

        # Initialize pool manager for worker pool oversight
        self.pool_manager = PoolManager(self.corp_path)

    def process_work(self, work_item: WorkItem) -> Dict[str, Any]:
        """
        Process a work item.

        VPs typically:
        1. Analyze the work requirement
        2. Break into sub-tasks for directors
        3. Delegate to appropriate directors
        4. Monitor progress

        NOTE: VPs delegate and return immediately - they do NOT wait
        for directors/workers to complete. The subordinates will pick up
        work from their hooks asynchronously.
        """
        task_type = work_item.context.get('task_type', 'delegation')

        # Check for fast mode (skip LLM analysis)
        fast_mode = work_item.context.get('fast_mode', False)

        if task_type == 'delegation':
            return self._handle_delegation(work_item, fast_mode=fast_mode)
        elif task_type == 'delegate_next':
            return self._handle_delegate_next(work_item)
        elif task_type == 'review_blockers':
            return self._handle_blockers(work_item)
        elif task_type == 'gate_review':
            return self._handle_gate_review(work_item)
        elif task_type == 'handle_escalation':
            return self._handle_escalation(work_item)
        else:
            return self._handle_general(work_item)

    def _handle_delegation(self, work_item: WorkItem, fast_mode: bool = False) -> Dict[str, Any]:
        """
        Handle a delegation from COO.

        Args:
            work_item: The work to process
            fast_mode: If True, skip LLM analysis and delegate immediately

        NOTE: This method delegates to directors and returns immediately.
        Directors will pick up their work asynchronously - VP does NOT wait.
        """
        logger.info(f"[{self.identity.role_name}] Processing delegation: {work_item.title}")

        if fast_mode:
            # Fast mode: skip LLM analysis, delegate immediately
            analysis = self._fast_analysis(work_item)
        else:
            # Normal mode: use LLM to analyze
            analysis = self.analyze_work_item(work_item)

            # Store context for future reference
            self.store_context(
                name=f"delegation_{work_item.id}",
                content={
                    'work_item': work_item.to_dict(),
                    'analysis': analysis
                },
                context_type=ContextType.MOLECULE,
                summary=f"Delegation analysis for {work_item.title}"
            )

        # Check if this should be delegated to directors
        if analysis.get('delegation_candidate', True) and self.identity.direct_reports:
            return self._delegate_to_directors(work_item, analysis)

        # Otherwise, handle directly (rare for VPs)
        return self._handle_directly(work_item, analysis)

    def _fast_analysis(self, work_item: WorkItem) -> Dict[str, Any]:
        """
        Fast analysis without LLM - for immediate delegation.

        Uses simple heuristics to determine delegation strategy.
        """
        # Default to delegating to first director with the task as-is
        target_director = self.identity.direct_reports[0] if self.identity.direct_reports else None

        return {
            'delegation_candidate': True,
            'delegation_to': target_director,
            'subtasks': [work_item.title],
            'understanding': work_item.description,
            'approach': 'Direct delegation for execution',
            'fast_mode': True
        }

    def _delegate_to_directors(
        self,
        work_item: WorkItem,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delegate work to directors.

        Creates a SINGLE work item for the director with the full task.
        The VP's strategic analysis is included as context - the Director
        decides how to break it down for workers.
        """
        # Mark the molecule step as IN_PROGRESS when we start delegating
        if work_item.molecule_id and work_item.step_id:
            try:
                self.molecule_engine.start_step(
                    molecule_id=work_item.molecule_id,
                    step_id=work_item.step_id,
                    assigned_to=self.identity.id
                )
                logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as IN_PROGRESS")
            except ValueError as e:
                # Step may already be in progress or completed
                logger.warning(f"[{self.identity.role_name}] Could not start step: {e}")

        # Determine which director to assign to
        target_director = analysis.get('delegation_to')

        # Validate that LLM's suggestion is actually one of our direct reports
        if target_director and self.identity.direct_reports:
            if target_director not in self.identity.direct_reports:
                logger.warning(
                    f"LLM suggested '{target_director}' but not in direct_reports "
                    f"{self.identity.direct_reports}, using first direct report"
                )
                target_director = self.identity.direct_reports[0]
        elif not target_director and self.identity.direct_reports:
            # Default to first direct report
            target_director = self.identity.direct_reports[0]

        if not target_director:
            logger.warning(f"No directors available for delegation")
            return self._handle_directly(work_item, analysis)

        # Get or create the director's hook
        dir_hook = self.hook_manager.get_or_create_hook(
            name=f"{target_director} Hook",
            owner_type='role',
            owner_id=target_director
        )

        # Extract subtask suggestions (if any) as guidance, not separate work items
        subtask_suggestions = analysis.get('subtasks', [])

        # Create ONE work item with the full task + strategic guidance
        dir_work_item = self.hook_manager.add_work_to_hook(
            hook_id=dir_hook.id,
            title=work_item.title,  # Keep original title
            description=work_item.description,  # Keep original description
            molecule_id=work_item.molecule_id,
            step_id=work_item.step_id,
            priority=work_item.priority,
            context={
                'parent_work_item': work_item.id,
                'delegated_by': self.identity.id,
                'strategic_analysis': analysis,  # VP's full analysis
                'subtask_suggestions': subtask_suggestions,  # Suggestions, not requirements
                'priority': analysis.get('priority', 'normal'),
                'task_type': 'director_execution'
            }
        )

        # Send delegation message
        self.delegate_to(
            recipient_id=target_director,
            recipient_role=target_director,
            molecule_id=work_item.molecule_id,
            step_id=work_item.step_id,
            instructions=f"""
Task: {work_item.title}

Context: {work_item.description}

Strategic Analysis: {analysis.get('understanding', 'Please analyze and execute.')}

Approach: {analysis.get('approach', 'Use your judgment.')}

Suggested breakdown (optional guidance):
{chr(10).join(f'- {s}' for s in subtask_suggestions) if subtask_suggestions else '- Use your judgment to break this down as needed'}
""",
            priority=MessagePriority.NORMAL
        )

        delegation_info = {
            'director': target_director,
            'work_item_id': dir_work_item.id,
            'task': work_item.title
        }

        logger.info(f"[{self.identity.role_name}] Delegated to {target_director}: {work_item.title}")

        # Checkpoint
        self.checkpoint(
            description=f"Delegated to director",
            data={'delegation': delegation_info}
        )

        # Mark the molecule step as DELEGATED (not COMPLETED - work is still in progress)
        if work_item.molecule_id and work_item.step_id:
            try:
                self.molecule_engine.delegate_step(
                    molecule_id=work_item.molecule_id,
                    step_id=work_item.step_id,
                    delegations=[delegation_info],
                    delegated_by=self.identity.id
                )
                logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as DELEGATED")
            except ValueError as e:
                logger.warning(f"[{self.identity.role_name}] Could not mark step as delegated: {e}")

        return {
            'status': 'delegated',
            'delegations': [delegation_info],
            'target_director': target_director
        }

    def _handle_directly(
        self,
        work_item: WorkItem,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle work directly (usually for oversight/review tasks)"""
        logger.info(f"[{self.identity.role_name}] Handling directly: {work_item.title}")

        # Mark the molecule step as IN_PROGRESS
        if work_item.molecule_id and work_item.step_id:
            try:
                self.molecule_engine.start_step(
                    molecule_id=work_item.molecule_id,
                    step_id=work_item.step_id,
                    assigned_to=self.identity.id
                )
                logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as IN_PROGRESS")
            except ValueError as e:
                logger.debug(f"[{self.identity.role_name}] Step already started: {e}")

        # Use LLM to think about and execute
        thought = self.think(
            task=work_item.title,
            context={
                'description': work_item.description,
                'analysis': analysis
            }
        )

        # Record decision
        self.record_decision(
            decision_id=f"dec-{work_item.id}",
            title=f"How to handle: {work_item.title}",
            context=work_item.description,
            options_considered=[{'option': opt, 'description': ''} for opt in thought.options],
            chosen_option=thought.chosen_action,
            rationale=thought.reasoning
        )

        # Mark the molecule step as COMPLETED
        if work_item.molecule_id and work_item.step_id:
            try:
                self.molecule_engine.complete_step(
                    molecule_id=work_item.molecule_id,
                    step_id=work_item.step_id,
                    result={
                        'action': thought.chosen_action,
                        'reasoning': thought.reasoning,
                        'completed_by': self.identity.id
                    }
                )
                logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as COMPLETED")
            except ValueError as e:
                logger.warning(f"[{self.identity.role_name}] Could not complete step: {e}")

        return {
            'status': 'completed',
            'action': thought.chosen_action,
            'reasoning': thought.reasoning
        }

    def _handle_delegate_next(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle delegation of next available steps"""
        available_steps = work_item.context.get('available_steps', [])

        if not self.current_molecule:
            self.current_molecule = self.molecule_engine.get_molecule(work_item.molecule_id)

        if not self.current_molecule:
            return {'status': 'error', 'error': 'Molecule not found'}

        delegations = []
        for step_id in available_steps:
            step = self.current_molecule.get_step(step_id)
            if step and step.status == StepStatus.PENDING:
                # Determine which director handles this
                target_director = self._get_director_for_step(step)

                if target_director:
                    # Create work item for director
                    dir_hook = self.hook_manager.get_or_create_hook(
                        name=f"{target_director} Hook",
                        owner_type='role',
                        owner_id=target_director
                    )

                    dir_work = self.hook_manager.add_work_to_hook(
                        hook_id=dir_hook.id,
                        title=step.name,
                        description=step.description,
                        molecule_id=self.current_molecule.id,
                        step_id=step.id,
                        priority=WorkItemPriority.P2_MEDIUM,
                        required_capabilities=step.required_capabilities
                    )

                    # Send delegation message
                    self.delegate_to(
                        recipient_id=target_director,
                        recipient_role=target_director,
                        molecule_id=self.current_molecule.id,
                        step_id=step.id,
                        instructions=f"Please complete: {step.name}\n\n{step.description}"
                    )

                    delegation_info = {
                        'step_id': step.id,
                        'step_name': step.name,
                        'director': target_director,
                        'work_item_id': dir_work.id
                    }
                    delegations.append(delegation_info)

                    # Mark step as DELEGATED (not COMPLETED - work is still in progress)
                    try:
                        self.molecule_engine.delegate_step(
                            molecule_id=self.current_molecule.id,
                            step_id=step.id,
                            delegations=[delegation_info],
                            delegated_by=self.identity.id
                        )
                        logger.info(f"[{self.identity.role_name}] Marked step {step.id} as DELEGATED to {target_director}")
                    except ValueError as e:
                        logger.warning(f"[{self.identity.role_name}] Could not mark step as delegated: {e}")

        return {
            'status': 'delegated',
            'delegations': delegations
        }

    def _get_director_for_step(self, step: MoleculeStep) -> Optional[str]:
        """Determine which director should handle a step"""
        # Match by department
        department = step.department

        # Look for matching director in direct reports
        for director in self.identity.direct_reports:
            if department.lower() in director.lower():
                return director

        # Default to first director
        if self.identity.direct_reports:
            return self.identity.direct_reports[0]

        return None

    def _handle_blockers(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle reported blockers from subordinates"""
        blockers = work_item.context.get('blockers', [])
        reported_by = work_item.context.get('reported_by', 'unknown')

        logger.warning(f"[{self.identity.role_name}] Reviewing blockers from {reported_by}")

        # Think about how to resolve
        thought = self.think(
            task=f"Resolve blockers: {', '.join(blockers)}",
            context={
                'reported_by': reported_by,
                'molecule_id': work_item.molecule_id,
                'blockers': blockers
            }
        )

        # If can't resolve, escalate to COO
        if 'escalate' in thought.chosen_action.lower():
            self._send_escalation(
                issue=f"Blockers require attention: {', '.join(blockers)}",
                error=f"Reported by {reported_by}",
                attempted_solutions=thought.options,
                recommended_action=thought.chosen_action
            )
            return {
                'status': 'escalated',
                'to': 'coo',
                'blockers': blockers
            }

        # Otherwise, record resolution plan
        self.record_decision(
            decision_id=f"blocker-{work_item.id}",
            title=f"Blocker resolution for {work_item.molecule_id}",
            context=f"Blockers: {', '.join(blockers)}",
            options_considered=[{'option': opt, 'description': ''} for opt in thought.options],
            chosen_option=thought.chosen_action,
            rationale=thought.reasoning
        )

        return {
            'status': 'resolution_planned',
            'action': thought.chosen_action,
            'blockers': blockers
        }

    def _handle_gate_review(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle quality gate review requests"""
        gate_id = work_item.context.get('gate_id')
        submission_id = work_item.context.get('submission_id')

        if not gate_id or not submission_id:
            return {'status': 'error', 'error': 'Missing gate_id or submission_id'}

        gate = self.gate_keeper.get_gate(gate_id)
        if not gate:
            return {'status': 'error', 'error': f'Gate {gate_id} not found'}

        submission = gate.get_submission(submission_id)
        if not submission:
            return {'status': 'error', 'error': f'Submission {submission_id} not found'}

        # Check if all criteria are met
        criteria_check = gate.check_criteria(submission.checklist_results)

        if criteria_check['passed']:
            # Approve
            self.gate_keeper.approve(gate_id, submission_id, self.identity.id)
            return {
                'status': 'approved',
                'gate_id': gate_id,
                'submission_id': submission_id
            }
        else:
            # Reject with reasons
            reasons = []
            if criteria_check['missing']:
                reasons.append(f"Missing: {', '.join(criteria_check['missing'])}")
            if criteria_check['failed']:
                reasons.append(f"Failed: {', '.join(criteria_check['failed'])}")

            self.gate_keeper.reject(
                gate_id, submission_id, self.identity.id, reasons
            )
            return {
                'status': 'rejected',
                'gate_id': gate_id,
                'reasons': reasons
            }

    def _handle_escalation(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle escalations from directors"""
        escalated_by = work_item.context.get('escalated_by', 'unknown')
        original_issue = work_item.context.get('original_issue', work_item.description)

        logger.warning(f"[{self.identity.role_name}] Handling escalation from {escalated_by}")

        # Think about how to resolve
        thought = self.think(
            task=f"Handle escalation: {original_issue}",
            context={
                'escalated_by': escalated_by,
                'molecule_id': work_item.molecule_id
            }
        )

        # Check if we need to further escalate to COO
        if 'escalate' in thought.chosen_action.lower() or 'cannot' in thought.chosen_action.lower():
            self._send_escalation(
                issue=f"Escalation from {escalated_by}: {original_issue}",
                error="Could not resolve at VP level",
                attempted_solutions=thought.options,
                recommended_action=thought.chosen_action
            )
            return {
                'status': 'escalated_to_coo',
                'original_issue': original_issue
            }

        # Record resolution
        return {
            'status': 'resolved',
            'action': thought.chosen_action,
            'original_issue': original_issue
        }

    def _handle_general(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle general tasks"""
        analysis = self.analyze_work_item(work_item)

        if analysis.get('delegation_candidate', False) and self.identity.direct_reports:
            return self._delegate_to_directors(work_item, analysis)

        return self._handle_directly(work_item, analysis)


# Factory function for creating VP agents
def create_vp_agent(
    department: str,
    corp_path: Path,
    directors: Optional[List[str]] = None
) -> VPAgent:
    """
    Create a VP agent for a department.

    Args:
        department: Department name (engineering, research, product, quality, operations)
        corp_path: Path to corporation root
        directors: List of director role IDs that report to this VP

    Returns:
        Configured VPAgent
    """
    dept_config = {
        'engineering': {
            'role_id': 'vp_engineering',
            'role_name': 'VP Engineering',
            'directors': ['director_engineering', 'dir_frontend', 'dir_backend'],
            'capabilities': ['engineering', 'technical_leadership', 'architecture', 'code_review']
        },
        'research': {
            'role_id': 'vp_research',
            'role_name': 'VP Research',
            'directors': ['dir_research'],
            'capabilities': ['research', 'analysis', 'evaluation']
        },
        'product': {
            'role_id': 'vp_product',
            'role_name': 'VP Product',
            'directors': ['dir_product'],
            'capabilities': ['product', 'product_strategy', 'design', 'requirements', 'planning']
        },
        'quality': {
            'role_id': 'vp_quality',
            'role_name': 'VP Quality',
            'directors': ['dir_qa'],
            'capabilities': ['quality', 'quality_assurance', 'testing', 'security']
        },
        'operations': {
            'role_id': 'vp_operations',
            'role_name': 'VP Operations',
            'directors': [],  # No directors defined in CorporationExecutor
            'capabilities': ['operations', 'project_management', 'documentation', 'coordination']
        }
    }

    config = dept_config.get(department.lower())
    if not config:
        raise ValueError(f"Unknown department: {department}")

    return VPAgent(
        role_id=config['role_id'],
        role_name=config['role_name'],
        department=department,
        corp_path=corp_path,
        direct_reports=directors or config['directors'],
        capabilities=config['capabilities']
    )
