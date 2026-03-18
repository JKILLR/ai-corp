"""
Worker Agent - Worker Agent Implementation

Workers are the execution layer responsible for:
- Receiving work from directors
- Actually executing tasks using Claude Code
- Creating checkpoints during work
- Reporting results to directors
- Escalating blockers

Workers are the primary executors and have full Claude Code capabilities.
Each worker is a complete Claude instance with access to all tools.

Worker types include:
- Frontend Developer
- Backend Developer
- DevOps Engineer
- Researcher
- Designer
- QA Engineer
- Technical Writer
- And more...
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base import BaseAgent, AgentIdentity
from ..core.hook import WorkItem, WorkItemPriority
from ..core.memory import ContextType
from ..core.llm import LLMResponse
from ..core.gate import GateKeeper
from ..core.pool import PoolManager

logger = logging.getLogger(__name__)


class WorkerAgent(BaseAgent):
    """
    Worker Agent.

    Workers are the execution layer that actually performs tasks.
    They have full Claude Code capabilities and can:
    - Read and write files
    - Execute commands
    - Search codebases
    - Create documentation
    - And anything else Claude Code can do
    """

    def __init__(
        self,
        role_id: str,
        role_name: str,
        department: str,
        specialty: str,
        reports_to: str,
        corp_path: Path,
        skills: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None
    ):
        identity = AgentIdentity(
            id=f"{role_id}-001",
            role_id=role_id,
            role_name=role_name,
            department=department,
            level=4,  # Worker level
            reports_to=reports_to,
            direct_reports=[],  # Workers don't have reports
            skills=skills or [],
            capabilities=capabilities or ['execution', 'implementation']
        )

        super().__init__(identity, corp_path)

        self.specialty = specialty

        # Initialize pool manager for releasing back to pool after work
        self.pool_manager = PoolManager(self.corp_path)

        # Initialize gate keeper for submitting completed work
        self.gate_keeper = GateKeeper(self.corp_path)

    def process_work(self, work_item: WorkItem) -> Dict[str, Any]:
        """
        Process a work item.

        Workers:
        1. Understand the task
        2. Plan execution
        3. Execute with checkpoints
        4. Report results
        """
        task_type = work_item.context.get('task_type', 'worker_execution')

        if task_type == 'worker_execution':
            return self._execute_work(work_item)
        elif task_type == 'revision':
            return self._handle_revision(work_item)
        elif task_type == 'review_broadcast':
            return self._review_broadcast(work_item)
        else:
            return self._execute_work(work_item)

    def _execute_work(self, work_item: WorkItem) -> Dict[str, Any]:
        """Execute a work item"""
        logger.info(f"[{self.identity.role_name}] Executing: {work_item.title}")

        # Store work context for reference
        self.store_context(
            name=f"current_work_{work_item.id}",
            content=work_item.to_dict(),
            context_type=ContextType.MOLECULE,
            summary=f"Current work: {work_item.title}"
        )

        # Get any prior analysis from director
        analysis = work_item.context.get('analysis', {})

        # Mark the molecule step as IN_PROGRESS (idempotent - may already be started by VP)
        if work_item.molecule_id and work_item.step_id:
            try:
                self.molecule_engine.start_step(
                    molecule_id=work_item.molecule_id,
                    step_id=work_item.step_id,
                    assigned_to=self.identity.id
                )
                logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as IN_PROGRESS")
            except ValueError as e:
                # Step may already be in progress (started by VP) - that's fine
                logger.debug(f"[{self.identity.role_name}] Step already started: {e}")

        # Checkpoint: Starting work
        self.checkpoint(
            description="Starting task execution",
            data={'work_item_id': work_item.id, 'analysis': analysis}
        )

        # Build the execution prompt
        execution_prompt = self._build_execution_prompt(work_item, analysis)

        # Execute with LLM (this is where the actual work happens)
        response = self.execute_with_llm(execution_prompt)

        if not response.success:
            logger.error(f"[{self.identity.role_name}] Execution failed: {response.error}")

            # Mark the molecule step as FAILED
            if work_item.molecule_id and work_item.step_id:
                try:
                    self.molecule_engine.fail_step(
                        molecule_id=work_item.molecule_id,
                        step_id=work_item.step_id,
                        error=response.error or "Execution failed",
                        error_type="execution_failure",
                        context={'worker': self.identity.id}
                    )
                    logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as FAILED")
                except ValueError as e:
                    logger.warning(f"[{self.identity.role_name}] Could not mark step failed: {e}")

            # Release worker back to pool even on failure
            pool_id = work_item.context.get('pool_id')
            assigned_worker_id = work_item.context.get('assigned_worker')
            if pool_id and assigned_worker_id:
                try:
                    self.pool_manager.release_worker(pool_id, assigned_worker_id, success=False)
                    logger.info(f"[{self.identity.role_name}] Released back to pool {pool_id} (failed)")
                except Exception as e:
                    logger.warning(f"[{self.identity.role_name}] Could not release to pool: {e}")

            # Check if we should escalate
            if self._should_escalate(response.error):
                self._send_escalation(
                    issue=f"Failed to execute: {work_item.title}",
                    error=response.error or "Unknown error",
                    attempted_solutions=[execution_prompt[:500]],
                    recommended_action="Need guidance or different approach"
                )
                return {
                    'status': 'escalated',
                    'error': response.error
                }

            return {
                'status': 'failed',
                'error': response.error
            }

        # Checkpoint: Execution complete
        self.checkpoint(
            description="Execution complete",
            data={
                'output_length': len(response.content),
                'success': True
            }
        )

        # Summarize results
        summary = self.llm.summarize_results(
            role=self.identity.role_name,
            task=work_item.title,
            raw_output=response.content,
            success=True
        )

        # Store the output for potential review
        self.store_context(
            name=f"output_{work_item.id}",
            content={
                'work_item_id': work_item.id,
                'output': response.content,
                'summary': summary
            },
            context_type=ContextType.ARTIFACT,
            summary=f"Output for {work_item.title}"
        )

        # Record completion
        self.bead.record(
            action='completed_execution',
            entity_type='work_item',
            entity_id=work_item.id,
            data={
                'summary': summary.get('summary', 'Completed'),
                'artifacts': summary.get('artifacts_created', [])
            },
            message=f"Completed: {work_item.title}"
        )

        # Mark the molecule step as COMPLETED
        if work_item.molecule_id and work_item.step_id:
            try:
                step = self.molecule_engine.complete_step(
                    molecule_id=work_item.molecule_id,
                    step_id=work_item.step_id,
                    result={
                        'summary': summary.get('summary', 'Completed'),
                        'artifacts': summary.get('artifacts_created', []),
                        'completed_by': self.identity.id
                    }
                )
                logger.info(f"[{self.identity.role_name}] Marked step {work_item.step_id} as COMPLETED")

                # Submit to gate if step has a gate_id
                if step.gate_id:
                    try:
                        self.gate_keeper.submit_for_review(
                            gate_id=step.gate_id,
                            molecule_id=work_item.molecule_id,
                            step_id=work_item.step_id,
                            submitted_by=self.identity.id,
                            summary=summary.get('summary', f'Completed: {work_item.title}'),
                            artifacts=summary.get('artifacts_created', [])
                        )
                        logger.info(f"[{self.identity.role_name}] Submitted to gate {step.gate_id}")
                    except Exception as e:
                        logger.warning(f"[{self.identity.role_name}] Could not submit to gate: {e}")
            except ValueError as e:
                # Step may not exist or be in unexpected state
                logger.warning(f"[{self.identity.role_name}] Could not complete step: {e}")

        # Release worker back to pool
        pool_id = work_item.context.get('pool_id')
        assigned_worker_id = work_item.context.get('assigned_worker')
        if pool_id and assigned_worker_id:
            try:
                self.pool_manager.release_worker(pool_id, assigned_worker_id, success=True)
                logger.info(f"[{self.identity.role_name}] Released back to pool {pool_id}")
            except Exception as e:
                logger.warning(f"[{self.identity.role_name}] Could not release to pool: {e}")

        logger.info(f"[{self.identity.role_name}] Completed: {work_item.title}")

        return {
            'status': 'completed',
            'summary': summary,
            'output': response.content[:2000],  # Truncate for storage
            'artifacts': summary.get('artifacts_created', [])
        }

    def _build_execution_prompt(
        self,
        work_item: WorkItem,
        analysis: Dict[str, Any]
    ) -> str:
        """Build the execution prompt for the LLM"""

        prompt = f"""You are {self.identity.role_name}, a {self.specialty} in AI Corp.

## Your Task

**Title:** {work_item.title}

**Description:**
{work_item.description}

"""

        if analysis:
            prompt += f"""## Analysis from Manager

**Understanding:** {analysis.get('understanding', 'Use your judgment')}

**Recommended Approach:** {analysis.get('approach', 'Standard approach')}

**Resources Needed:** {', '.join(analysis.get('resources_needed', []))}

"""

        if work_item.context:
            context_str = "\n".join(
                f"- {k}: {v}" for k, v in work_item.context.items()
                if k not in ['analysis', 'task_type', 'delegated_by', 'assigned_worker']
            )
            if context_str:
                prompt += f"""## Additional Context

{context_str}

"""

        # Get relevant lessons learned
        lessons = self.get_relevant_lessons(f"{work_item.title} {work_item.description}")
        if lessons:
            prompt += "## Relevant Lessons from Past Work\n\n"
            for lesson in lessons[:3]:
                prompt += f"- **{lesson['title']}**: {lesson['lesson']}\n"
            prompt += "\n"

        prompt += f"""## Instructions

1. Complete the task described above
2. Use your full capabilities (read/write files, execute commands, etc.)
3. Create any necessary files or make required changes
4. Document what you did and any important decisions
5. Report any issues or blockers

Your specialty is: {self.specialty}
Your skills: {', '.join(self.identity.skills) if self.identity.skills else 'General development'}

Please execute this task now.
"""

        return prompt

    def _should_escalate(self, error: Optional[str]) -> bool:
        """Determine if an error should be escalated"""
        if not error:
            return False

        escalation_keywords = [
            'permission denied',
            'access denied',
            'not authorized',
            'out of scope',
            'need clarification',
            'unclear requirements',
            'conflicting',
            'blocked by'
        ]

        error_lower = error.lower()
        return any(kw in error_lower for kw in escalation_keywords)

    def _handle_revision(self, work_item: WorkItem) -> Dict[str, Any]:
        """Handle a revision request"""
        feedback = work_item.context.get('feedback', 'Please revise')
        original_output = work_item.context.get('original_output', '')

        logger.info(f"[{self.identity.role_name}] Handling revision for: {work_item.title}")

        revision_prompt = f"""You are {self.identity.role_name}, handling a revision request.

## Original Task

**Title:** {work_item.title}

**Description:**
{work_item.description}

## Feedback Received

{feedback}

## Your Previous Output (Summary)

{original_output[:2000]}

## Instructions

Please revise your work based on the feedback above.
Address all the issues mentioned and improve your output.
"""

        response = self.execute_with_llm(revision_prompt)

        if not response.success:
            return {
                'status': 'revision_failed',
                'error': response.error
            }

        # Summarize revised results
        summary = self.llm.summarize_results(
            role=self.identity.role_name,
            task=f"Revision: {work_item.title}",
            raw_output=response.content,
            success=True
        )

        return {
            'status': 'revised',
            'summary': summary,
            'output': response.content[:2000]
        }

    def _review_broadcast(self, work_item: WorkItem) -> Dict[str, Any]:
        """Review an important broadcast message"""
        message_id = work_item.context.get('message_id', '')

        logger.info(f"[{self.identity.role_name}] Reviewing broadcast: {work_item.title}")

        # Just acknowledge understanding
        self.bead.record(
            action='reviewed_broadcast',
            entity_type='message',
            entity_id=message_id,
            data={'summary': work_item.description[:200]},
            message=f"Reviewed broadcast: {work_item.title}"
        )

        return {
            'status': 'reviewed',
            'broadcast': work_item.title
        }

    def get_specialty_prompt(self) -> str:
        """Get specialty-specific prompt additions"""
        specialty_prompts = {
            'frontend': """
You specialize in frontend development:
- React, Vue, Angular, and other frontend frameworks
- HTML, CSS, JavaScript, TypeScript
- UI/UX implementation
- Responsive design
- Accessibility
""",
            'backend': """
You specialize in backend development:
- APIs and microservices
- Databases and data modeling
- Server-side frameworks
- Authentication and authorization
- Performance optimization
""",
            'devops': """
You specialize in DevOps:
- CI/CD pipelines
- Infrastructure as Code
- Cloud services (AWS, GCP, Azure)
- Docker and Kubernetes
- Monitoring and observability
""",
            'research': """
You specialize in research:
- Technical research and analysis
- Competitive analysis
- Technology evaluation
- Documentation and reporting
- Knowledge synthesis
""",
            'qa': """
You specialize in quality assurance:
- Test planning and execution
- Automated testing
- Performance testing
- Security testing
- Bug tracking and reporting
""",
            'design': """
You specialize in design:
- UI/UX design
- Wireframing and prototyping
- Visual design
- Design systems
- User research
""",
            'security': """
You specialize in security:
- Security assessments
- Vulnerability analysis
- Secure coding practices
- Compliance review
- Threat modeling
""",
            'documentation': """
You specialize in documentation:
- Technical writing
- API documentation
- User guides
- Architecture documentation
- Knowledge base articles
"""
        }

        for key, prompt in specialty_prompts.items():
            if key in self.specialty.lower():
                return prompt

        return f"You specialize in: {self.specialty}"


# Factory function for creating worker agents
def create_worker_agent(
    worker_type: str,
    department: str,
    reports_to: str,
    corp_path: Path,
    skills: Optional[List[str]] = None,
    worker_number: int = 1
) -> WorkerAgent:
    """
    Create a Worker agent.

    Args:
        worker_type: Type of worker (frontend, backend, devops, researcher, etc.)
        department: Department this worker belongs to
        reports_to: Director role ID this worker reports to
        corp_path: Path to corporation root
        skills: Claude Code skills to use
        worker_number: Worker instance number

    Returns:
        Configured WorkerAgent
    """
    worker_configs = {
        'frontend': {
            'role_id': f'worker_frontend_{worker_number:02d}',
            'role_name': f'Frontend Developer {worker_number}',
            'specialty': 'Frontend Development',
            'capabilities': ['frontend', 'ui', 'javascript', 'react'],
            'default_skills': ['frontend-design']
        },
        'backend': {
            'role_id': f'worker_backend_{worker_number:02d}',
            'role_name': f'Backend Developer {worker_number}',
            'specialty': 'Backend Development',
            'capabilities': ['backend', 'api', 'database'],
            'default_skills': []
        },
        'devops': {
            'role_id': f'worker_devops_{worker_number:02d}',
            'role_name': f'DevOps Engineer {worker_number}',
            'specialty': 'DevOps',
            'capabilities': ['infrastructure', 'ci_cd', 'cloud'],
            'default_skills': ['aws-skills', 'terraform-skills']
        },
        'researcher': {
            'role_id': f'worker_researcher_{worker_number:02d}',
            'role_name': f'Researcher {worker_number}',
            'specialty': 'Research',
            'capabilities': ['research', 'analysis', 'documentation'],
            'default_skills': []
        },
        'designer': {
            'role_id': f'worker_designer_{worker_number:02d}',
            'role_name': f'Designer {worker_number}',
            'specialty': 'Design',
            'capabilities': ['design', 'ui', 'ux'],
            'default_skills': ['frontend-design']
        },
        'qa': {
            'role_id': f'worker_qa_{worker_number:02d}',
            'role_name': f'QA Engineer {worker_number}',
            'specialty': 'Quality Assurance',
            'capabilities': ['testing', 'qa', 'automation'],
            'default_skills': ['webapp-testing']
        },
        'security': {
            'role_id': f'worker_security_{worker_number:02d}',
            'role_name': f'Security Engineer {worker_number}',
            'specialty': 'Security',
            'capabilities': ['security', 'audit', 'compliance'],
            'default_skills': ['security-bluebook-builder']
        },
        'writer': {
            'role_id': f'worker_writer_{worker_number:02d}',
            'role_name': f'Technical Writer {worker_number}',
            'specialty': 'Documentation',
            'capabilities': ['documentation', 'writing'],
            'default_skills': ['docx', 'pdf']
        }
    }

    config = worker_configs.get(worker_type.lower())
    if not config:
        # Generic worker
        config = {
            'role_id': f'worker_{worker_type}_{worker_number:02d}',
            'role_name': f'{worker_type.title()} Worker {worker_number}',
            'specialty': worker_type.title(),
            'capabilities': [worker_type],
            'default_skills': []
        }

    return WorkerAgent(
        role_id=config['role_id'],
        role_name=config['role_name'],
        department=department,
        specialty=config['specialty'],
        reports_to=reports_to,
        corp_path=corp_path,
        skills=skills or config['default_skills'],
        capabilities=config['capabilities']
    )
