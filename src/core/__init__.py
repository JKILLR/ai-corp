"""
AI Corp Core Module

This module provides the core infrastructure for the AI Corporation:
- Molecules: Persistent workflows that survive agent crashes
- Hooks: Work queues for agents
- Beads: Git-backed ledger for state persistence
- Channels: Communication between agents
- Gates: Quality checkpoints
- Contracts: Success criteria and measurable outcomes
- Hiring: Dynamic agent onboarding
- Templates: Industry-specific configurations
- Memory: RLM-inspired context management (arXiv:2512.24601)
- LLM: Swappable LLM backend interface
- Processor: Inter-agent message processing
- Knowledge: Scoped document and context management
- Ingest: RLM-inspired document processing pipeline
- Skills: Role-based skill discovery and loading
- Scheduler: Intelligent work scheduling and orchestration
- Entity Graph: Unified entity management (Mem0/Graphiti-inspired)
- Learning: Learning System with Ralph Mode for persistent execution
"""

from .molecule import (
    Molecule, MoleculeStep, MoleculeStatus, MoleculeEngine,
    WorkflowType, SwarmConfig, ConvergenceStrategy, LoopConfig
)
from .hook import Hook, HookManager
from .bead import Bead, BeadLedger
from .channel import Channel, ChannelType, ChannelManager
from .gate import (
    Gate, GateStatus, GateKeeper, GateSubmission, GateCriterion,
    SubmissionStatus, EvaluationStatus, AsyncEvaluationResult,
    AutoApprovalPolicy, AsyncGateEvaluator
)
from .pool import WorkerPool, PoolManager
from .raci import RACI, RACIRole
from .contract import (
    SuccessContract, SuccessCriterion, ContractStatus, ContractManager
)
from .hiring import HiringManager, quick_hire
from .templates import IndustryTemplateManager, init_corp, INDUSTRY_TEMPLATES
from .memory import (
    ContextType, ContextVariable, MemoryBuffer,
    ContextEnvironment, RecursiveMemoryManager, ContextCompressor,
    OrganizationalMemory, SubAgentCall,
    create_agent_memory, load_molecule_to_memory, load_bead_history_to_memory,
    # Entity Graph integration
    EntityAwareMemory, load_entity_to_memory, load_entity_profile_to_memory,
    load_entity_context_to_memory, load_interaction_to_memory,
    get_entity_context_for_message
)
from .entities import (
    Entity, EntityType, EntitySource, EntityAlias, EntityStore,
    Relationship, RelationshipType, ConfidenceLevel
)
from .interactions import (
    Interaction, InteractionType, InteractionStore, InteractionProcessor,
    ExtractedEntity, ActionItem
)
from .entity_resolver import (
    EntityResolver, ResolutionCandidate, MergeDecision, MatchType
)
from .entity_summarizer import (
    EntitySummarizer, SummaryStore, Summary, SummaryType, SummaryScope,
    EntityProfile
)
from .graph import (
    EntityGraph, EntityContext, get_entity_graph,
    # Depth-Based Context Configuration
    DepthConfig, get_depth_for_level,
    AGENT_LEVEL_DEPTH_DEFAULTS, AGENT_LEVEL_CONTEXT_LIMITS
)
from .llm import (
    LLMBackend, LLMRequest, LLMResponse, LLMBackendFactory,
    ClaudeCodeBackend, ClaudeAPIBackend, MockBackend,
    AgentLLMInterface, AgentThought, get_llm_interface
)
from .processor import (
    MessageProcessor, MessageHandler, ProcessingResult, MessageAction
)
from .monitor import (
    SystemMonitor, SystemMetrics, AgentStatus, HealthAlert,
    AlertSeverity, HealthState
)
from .knowledge import (
    KnowledgeBase, KnowledgeEntry, KnowledgeScope, KnowledgeType,
    ScopedKnowledgeStore, get_knowledge_base, add_foundation_knowledge
)
from .ingest import (
    DocumentProcessor, ContentExtractor, DocumentChunker, FactExtractor,
    IngestResult, ProcessedChunk, ExtractionMethod,
    ingest_file, ingest_foundation, ingest_project, ingest_task
)
from .skills import (
    Skill, SkillLoader, SkillRegistry,
    parse_frontmatter, CAPABILITY_SKILL_MAP, SKILL_CAPABILITY_MAP
)
from .scheduler import (
    WorkScheduler, CapabilityMatcher, LoadBalancer, DependencyResolver,
    SchedulingDecision
)
from .learning import (
    # Enums
    InsightType, PatternType, FailureStrategy, CycleType,
    # Data classes
    Insight, Outcome, Pattern, RalphCriterion, RalphConfig,
    FailureBead, FailureContext, RalphResult,
    SourceEffectiveness, ConfidenceBucket,
    CycleResult, ImprovementSuggestion,
    Theme, Prediction, SynthesizedContext,
    # Core classes - Phase 1
    InsightStore, OutcomeTracker, PatternLibrary, MetaLearner,
    KnowledgeDistiller, RalphModeExecutor, BudgetTracker,
    # Core classes - Phase 2
    EvolutionDaemon, ContextSynthesizer,
    # Main interface
    LearningSystem, get_learning_system
)

__all__ = [
    'Molecule', 'MoleculeStep', 'MoleculeStatus', 'MoleculeEngine',
    'Hook', 'HookManager',
    'Bead', 'BeadLedger',
    'Channel', 'ChannelType', 'ChannelManager',
    # Quality Gates (with async support)
    'Gate', 'GateStatus', 'GateKeeper', 'GateSubmission', 'GateCriterion',
    'SubmissionStatus', 'EvaluationStatus', 'AsyncEvaluationResult',
    'AutoApprovalPolicy', 'AsyncGateEvaluator',
    'WorkerPool', 'PoolManager',
    'RACI', 'RACIRole',
    # Success Contracts
    'SuccessContract', 'SuccessCriterion', 'ContractStatus', 'ContractManager',
    'HiringManager', 'quick_hire',
    'IndustryTemplateManager', 'init_corp', 'INDUSTRY_TEMPLATES',
    # Memory system (RLM-inspired)
    'ContextType', 'ContextVariable', 'MemoryBuffer',
    'ContextEnvironment', 'RecursiveMemoryManager', 'ContextCompressor',
    'OrganizationalMemory', 'SubAgentCall',
    'create_agent_memory', 'load_molecule_to_memory', 'load_bead_history_to_memory',
    'EntityAwareMemory', 'load_entity_to_memory', 'load_entity_profile_to_memory',
    'load_entity_context_to_memory', 'load_interaction_to_memory',
    'get_entity_context_for_message',
    # Entity Graph (Mem0/Graphiti-inspired)
    'Entity', 'EntityType', 'EntitySource', 'EntityAlias', 'EntityStore',
    'Relationship', 'RelationshipType', 'ConfidenceLevel',
    'Interaction', 'InteractionType', 'InteractionStore', 'InteractionProcessor',
    'ExtractedEntity', 'ActionItem',
    'EntityResolver', 'ResolutionCandidate', 'MergeDecision', 'MatchType',
    'EntitySummarizer', 'SummaryStore', 'Summary', 'SummaryType', 'SummaryScope',
    'EntityProfile',
    'EntityGraph', 'EntityContext', 'get_entity_graph',
    'DepthConfig', 'get_depth_for_level',
    'AGENT_LEVEL_DEPTH_DEFAULTS', 'AGENT_LEVEL_CONTEXT_LIMITS',
    # LLM backend interface
    'LLMBackend', 'LLMRequest', 'LLMResponse', 'LLMBackendFactory',
    'ClaudeCodeBackend', 'ClaudeAPIBackend', 'MockBackend',
    'AgentLLMInterface', 'AgentThought', 'get_llm_interface',
    # Message processing
    'MessageProcessor', 'MessageHandler', 'ProcessingResult', 'MessageAction',
    # System Monitoring
    'SystemMonitor', 'SystemMetrics', 'AgentStatus', 'HealthAlert',
    'AlertSeverity', 'HealthState',
    # Knowledge Base
    'KnowledgeBase', 'KnowledgeEntry', 'KnowledgeScope', 'KnowledgeType',
    'ScopedKnowledgeStore', 'get_knowledge_base', 'add_foundation_knowledge',
    # Document Ingestion
    'DocumentProcessor', 'ContentExtractor', 'DocumentChunker', 'FactExtractor',
    'IngestResult', 'ProcessedChunk', 'ExtractionMethod',
    'ingest_file', 'ingest_foundation', 'ingest_project', 'ingest_task',
    # Skills System
    'Skill', 'SkillLoader', 'SkillRegistry',
    'parse_frontmatter', 'CAPABILITY_SKILL_MAP', 'SKILL_CAPABILITY_MAP',
    # Work Scheduler
    'WorkScheduler', 'CapabilityMatcher', 'LoadBalancer', 'DependencyResolver',
    'SchedulingDecision',
    # Learning System - Phase 1
    'InsightType', 'PatternType', 'FailureStrategy',
    'Insight', 'Outcome', 'Pattern', 'RalphCriterion', 'RalphConfig',
    'FailureBead', 'FailureContext', 'RalphResult',
    'SourceEffectiveness', 'ConfidenceBucket',
    'InsightStore', 'OutcomeTracker', 'PatternLibrary', 'MetaLearner',
    'KnowledgeDistiller', 'RalphModeExecutor', 'BudgetTracker',
    # Learning System - Phase 2
    'CycleType', 'CycleResult', 'ImprovementSuggestion',
    'Theme', 'Prediction', 'SynthesizedContext',
    'EvolutionDaemon', 'ContextSynthesizer',
    # Learning System - Main
    'LearningSystem', 'get_learning_system',
]
