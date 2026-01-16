"""
Director Agent - Director Agent Implementation

Directors are middle managers responsible for:
- Receiving work delegated from VPs
- Managing worker pools
- Assigning work to workers
- Ensuring work quality
- Reporting to VPs

Directors focus on specific areas within departments:
- Engineering: Architecture, Frontend, Backend, DevOps
- Research: Market Research, Technical Research
- Product: Product, Design
- Quality: QA, Security
- Operations: Project, Documentation
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base import BaseAgent, AgentIdentity
from ..core.molecule import MoleculeStep, StepStatus
from ..core.hook import WorkItem, WorkItemPriority
from ..core.channel import MessagePriority
from ..core.pool import PoolManager, WorkerPool
from ..core.memory import ContextType

logger = logging.getLogger(__name__)


class DirectorAgent(BaseAgent):
    """
    Director Agent.

    Directors receive work from VPs and delegate to worker pools.
    They may also execute work directly for smaller tasks.
    """

    def __init__(
        self,
        role_id: str,
        role_name: str,
        department: str,
        focus: str,
        reports_to: str,
        corp_path: Path,
        worker_pool_id: Optional[str] = None,
        skills: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None
    ):
        identity = AgentIdentity(
            id=f"{role_id}-001",
            role_id=role_id,
            role_name=role_name,
            department=department,
            level=3,  # Director level
            reports_to=reports_to,
            direct_reports=[],  # Workers are in pools, not direct reports
            skills=skills or [],
            capabilities=capabilities or ['management', 'execution', 'review']
        )

        super().__init__(identity, corp_path)

        self.focus = focus
        self.worker_pool_id = worker_pool_id

        # Initialize pool manager
        self.pool_manager = PoolManager(self.corp_path)

        # Get or create worker pool for this director
        self.worker_pool = self._get_or_create_pool()

    def _get_or_create_pool(self) -> Optional[WorkerPool]:
        """Get or create the worker pool for this director"""
        if self.worker_pool_id:
            pool = self.pool_manager.get_pool(self.worker_pool_id)
            if pool:
                return pool

        # Create a pool if it doesn't exist
        pool_name = f"{self.focus.replace(' ', '_')}_pool"
        existing = self.pool_manager.get_pool_by_name(pool_name)
        if existing:
            return existing

        return self.pool_manager.create_pool(
            name=pool_name,
            department=self.identity.department,
            director_id=self.identity.id,
            min_workers=1,
            max_workers=5,
            required_capabilities=self.identity.capabilities
        )

    def process_work(self, work_item: WorkItem) -> Dict[str, Any]:
        """
        Process a work item.

        Directors:
        1. Analyze the work
        2. Decide: delegate to workers or handle directly
        3. Monitor worker progress
        4. Report results to VP

        NOTE: Directors delegate to workers and return immediately.
        Workers process asynchronously - Director does NOT wait.
        """
        task_type = work_item.context.get('task_type', 'general')
        fast_mode = work_item.context.get('fast_mode', False)

        if task_type == 'delegate_to_workers':
            return self._delegate_to_workers(work_item)
        elif task_type == 'review_work':
            return self._review_worker_output(work_item)
        elif task_type == 'handle_escalation':
            return self._handle_escalation(work_item)
        elif task_type == 'peer_response':
            return self._handle_peer_request(work_item)
        else:
            return self._handle_general(work_item, fast_mode=fast_mode)

    def _handle_general(self, work_item: WorkItem, fast_mode: bool = False) -> Dict[str, Any]:
        """
        Handle a general work item.

        Args:
            work_item: The work to process
            fast_mode: If True, skip LLM analysis and delegate immediately
        """
        logger.info(f"[{self.identity.role_name}] Processing: {work_item.title}")

        if fast_mode:
            # Fast mode: skip LLM analysis, delegate immediately
            analysis = self._fast_analysis(work_item)
        else:
            # Normal mode: use LLM to analyze
            analysis = self.analyze_work_item(work_item)

            # Store context
            self.store_context(
                name=f"work_{work_item.id}",
                content={
                    'work_item': work_item.to_dict(),
                    'analysis': analysis
                },
                context_type=ContextType.MOLECULE,
                summary=f"Work analysis for {work_item.title}"
            )

        complexity = analysis.get('estimated_complexity', 'medium')

        # Decide: delegate or handle directly
        # Note: We always try delegation first since claim_worker() has stale recovery
        # that can free up stuck workers. It returns None if truly no workers available.
        if complexity == 'high' or analysis.get('delegation_candidate', True):
            if self.worker_pool:
                return self._delegate_to_workers(work_item, analysis)

        # Handle directly for simple tasks or when no workers available
        return self._handle_directly(work_item, analysis)

    def _fast_analysis(self, work_item: WorkItem) -> Dict[str, Any]:
        """
        Fast analysis without LLM - for immediate delegation.

        Uses simple heuristics to determine delegation strategy.
        """
        return {
            'delegation_candidate': True,
            'estimated_complexity': 'medium',
            'understanding': work_item.description,
            'approach': 'Direct execution',
            'fast_mode': True
        }

    def _pool_has_capacity(self) -> bool:
        """Check if worker pool has capacity (triggers stale recovery first)"""
        if not self.worker_pool:
            return False

        # Trigger stale worker recovery before checking
        # This ensures we get an accurate count of available workers
        pool = self.pool_manager.get_pool(self.worker_pool.id)
        if pool:
            self.pool_manager._cleanup_stale_workers(pool)
            # Refresh our cached pool reference
            self.worker_pool = pool

        idle_workers = self.worker_pool.get_idle_workers()
        return len(idle_workers) > 0

    def _delegate_to_workers(
        self,
        work_item: WorkItem,
        analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Delegate work to workers in the pool"""
        if not self.worker_pool:
            logger.warning(f"[{self.identity.role_name}] No worker pool available")
            return self._handle_directly(work_item, analysis or {})

        # Get required capabilities
        required_caps = work_item.required_capabilities or []

        # Find available worker
        worker = self.pool_manager.claim_worker(
            pool_id=self.worker_pool.id,
            work_item_id=work_item.id,
            molecule_id=work_item.molecule_id,
            required_capabilities=required_caps
        )

        if not worker:
            logger.warning(f"[{self.identity.role_name}] No workers available, handling directly")
            return self._handle_directly(work_item, analysis or {})

        # Create work item in worker's conceptual hook
        # In practice, workers claim from the pool's shared queue
        worker_work = self.hook_manager.add_work_to_hook(
            hook_id=self.hook.id,  # Use director's hook as shared pool queue
            title=work_item.title,
            description=work_item.description,
            molecule_id=work_item.molecule_id,
            step_id=work_item.step_id,
            priority=work_item.priority,
            required_capabilities=required_caps,
            context={
                'assigned_worker': worker.id,
                'delegated_by': self.identity.id,
                'pool_id': self.worker_pool.id,
                'analysis': analysis,
                'task_type': 'worker_execution'
            }
        )

        # Record delegation
        self.bead.record(
            action='delegate_to_worker',
            entity_type='work_item',
            entity_id=work_item.id,
            data={
                'worker_id': worker.id,
                'worker_work_id': worker_work.id
            },
            message=f"Delegated to worker {worker.id}"
        )

        logger.info(f"[{self.identity.role_name}] Delegated to worker {worker.id}: {work_item.title}")

        # Checkpoint
        self.checkpoint(
            description=f"Delegated to worker",
            data={
                'worker_id': worker.id,
                'worker_work_id': worker_work.id
            }
        )

        # Mark the molecule step as DELEGATED (not COMPLETED - worker is still processing)
        if work_item.molecule_id and work_item.step_id:
            try:
                self.molecule_engine.delegate_step(
                    molecule_id=work_item.molecule_id,
                    step_id=work_item.step_id,
                    delegations=[{
                        'worker_id': worker.id,
                        'work_item_id': worker_work.id
                    }],
                    delegated_by=self.identity.id
                )
                logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as DELEGATED to worker {worker.id}")
            except ValueError as e:
                logger.warning(f"[{self.identity.role_name}] Could not mark step as delegated: {e}")

        return {
            'status': 'delegated_to_worker',
            'worker_id': worker.id,
            'work_item_id': worker_work.id
        }

    def _handle_directly(
        self,
        work_item: WorkItem,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle work directly"""
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

        # Use LLM to execute the task
        task_prompt = f"""
You are executing this task as {self.identity.role_name} (focus: {self.focus}).

Task: {work_item.title}

Description:
{work_item.description}

Analysis:
{analysis.get('understanding', 'No prior analysis')}

Recommended Approach:
{analysis.get('approach', 'Use your judgment')}

Please complete this task. If this requires code changes, create the necessary files.
If this is a review task, provide your assessment.
If this is a planning task, create a detailed plan.

Report your results clearly.
"""

        # Execute with LLM
        response = self.execute_with_llm(task_prompt)

        if response.success:
            # Summarize results
            summary = self.llm.summarize_results(
                role=self.identity.role_name,
                task=work_item.title,
                raw_output=response.content,
                success=True
            )

            # Record in bead
            self.bead.record(
                action='completed_work',
                entity_type='work_item',
                entity_id=work_item.id,
                data={
                    'summary': summary,
                    'output_length': len(response.content)
                },
                message=f"Completed: {work_item.title}"
            )

            # Mark the molecule step as COMPLETED
            if work_item.molecule_id and work_item.step_id:
                try:
                    self.molecule_engine.complete_step(
                        molecule_id=work_item.molecule_id,
                        step_id=work_item.step_id,
                        result={
                            'summary': summary,
                            'completed_by': self.identity.id
                        }
                    )
                    logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as COMPLETED")
                except ValueError as e:
                    logger.warning(f"[{self.identity.role_name}] Could not complete step: {e}")

            return {
                'status': 'completed',
                'summary': summary,
                'output': response.content[:1000]  # Truncate for storage
            }
        else:
            logger.error(f"[{self.identity.role_name}] Failed to execute: {response.error}")

            # Mark the molecule step as FAILED
            if work_item.molecule_id and work_item.step_id:
                try:
                    self.molecule_engine.fail_step(
                        molecule_id=work_item.molecule_id,
                        step_id=work_item.step_id,
                        error=response.error or "Execution failed",
                        error_type="execution_failure",
                        context={'director': self.identity.id}
                    )
                    logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as FAILED")
                except ValueError as e:
                    logger.warning(f"[{self.identity.role_name}] Could not mark step failed: {e}")

            return {
                'status': 'failed',
                'error': response.error
            }

    def _review_worker_output(self, work_item: WorkItem) -> Dict[str, Any]:
        """Review output from a worker"""
        worker_output = work_item.context.get('worker_output', '')
        worker_id = work_item.context.get('worker_id', 'unknown')

        logger.info(f"[{self.identity.role_name}] Reviewing work from {worker_id}")

        # Use LLM to review
        review_prompt = f"""
As {self.identity.role_name}, review this work output from a worker.

Original Task: {work_item.title}
Description: {work_item.description}

Worker Output:
{worker_output[:5000]}  # Truncate

Provide your review:
1. Does this meet the requirements?
2. Are there any issues or concerns?
3. Is this approved or needs revision?

Format your response as:
APPROVED: yes/no
QUALITY: high/medium/low
ISSUES: (list any issues)
FEEDBACK: (feedback for the worker)
"""

        response = self.execute_with_llm(review_prompt)

        if not response.success:
            return {
                'status': 'review_failed',
                'error': response.error
            }

        # Parse review result
        approved = 'approved: yes' in response.content.lower()

        if approved:
            # Release worker back to pool
            if self.worker_pool:
                worker = work_item.context.get('worker_id')
                if worker:
                    self.pool_manager.release_worker(
                        self.worker_pool.id, worker, success=True
                    )

            return {
                'status': 'approved',
                'review': response.content
            }
        else:
            # Request revision
            return {
                'status': 'revision_needed',
                'review': response.content,
                'feedback': response.content
            }

    def _handle_escalation(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle escalations from workers"""
        original_issue = work_item.context.get('original_issue', work_item.description)
        escalated_by = work_item.context.get('escalated_by', 'worker')

        logger.warning(f"[{self.identity.role_name}] Handling escalation: {original_issue}")

        # Think about resolution
        thought = self.think(
            task=f"Resolve escalation: {original_issue}",
            context={
                'escalated_by': escalated_by,
                'molecule_id': work_item.molecule_id
            }
        )

        # If can't resolve, escalate to VP
        if 'escalate' in thought.chosen_action.lower():
            self._send_escalation(
                issue=f"Worker escalation: {original_issue}",
                error=f"From {escalated_by}, could not resolve at director level",
                attempted_solutions=thought.options,
                recommended_action=thought.chosen_action
            )
            return {
                'status': 'escalated_to_vp',
                'original_issue': original_issue
            }

        return {
            'status': 'resolved',
            'action': thought.chosen_action,
            'original_issue': original_issue
        }

    def _handle_peer_request(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle peer-to-peer coordination requests"""
        from_peer = work_item.context.get('from', 'unknown')
        topic = work_item.context.get('topic', 'Coordination')

        logger.info(f"[{self.identity.role_name}] Peer request from {from_peer}: {topic}")

        # Think about response
        thought = self.think(
            task=f"Respond to peer request about: {topic}",
            context={
                'from': from_peer,
                'request': work_item.description
            }
        )

        # Send peer response
        self.channel_manager.send_message(
            sender_id=self.identity.id,
            sender_role=self.identity.role_id,
            recipient_id=from_peer,
            recipient_role=from_peer,
            subject=f"Re: {topic}",
            body=f"""
Response to your request:

{thought.chosen_action}

Reasoning: {thought.reasoning}
""",
            channel_type=ChannelType.PEER,
            message_type="peer_response"
        )

        return {
            'status': 'responded',
            'to': from_peer,
            'response': thought.chosen_action
        }

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current worker pool status"""
        if not self.worker_pool:
            return {'status': 'no_pool'}

        return {
            'pool_id': self.worker_pool.id,
            'pool_name': self.worker_pool.name,
            'stats': self.worker_pool.get_stats()
        }


# Import for peer communication
from ..core.channel import ChannelType


# Factory function for creating director agents
def create_director_agent(
    role_id: str,
    role_name: str,
    department: str,
    focus: str,
    reports_to: str,
    corp_path: Path,
    skills: Optional[List[str]] = None
) -> DirectorAgent:
    """
    Create a Director agent.

    Args:
        role_id: Unique role ID (e.g., 'dir_frontend')
        role_name: Display name (e.g., 'Frontend Director')
        department: Department (e.g., 'engineering')
        focus: Focus area (e.g., 'Frontend Development')
        reports_to: VP role ID this director reports to
        corp_path: Path to corporation root
        skills: Claude Code skills to use

    Returns:
        Configured DirectorAgent
    """
    return DirectorAgent(
        role_id=role_id,
        role_name=role_name,
        department=department,
        focus=focus,
        reports_to=reports_to,
        corp_path=corp_path,
        skills=skills
    )
