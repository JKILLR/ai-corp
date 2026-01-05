"""
AI Corp Core Module

This module provides the core infrastructure for the AI Corporation:
- Molecules: Persistent workflows that survive agent crashes
- Hooks: Work queues for agents
- Beads: Git-backed ledger for state persistence
- Channels: Communication between agents
- Gates: Quality checkpoints
- Hiring: Dynamic agent onboarding
- Templates: Industry-specific configurations
- Memory: RLM-inspired context management (arXiv:2512.24601)
"""

from .molecule import Molecule, MoleculeStep, MoleculeStatus, MoleculeEngine
from .hook import Hook, HookManager
from .bead import Bead, BeadLedger
from .channel import Channel, ChannelType, ChannelManager
from .gate import Gate, GateStatus, GateKeeper
from .pool import WorkerPool, PoolManager
from .raci import RACI, RACIRole
from .hiring import HiringManager, quick_hire
from .templates import IndustryTemplateManager, init_corp, INDUSTRY_TEMPLATES
from .memory import (
    ContextType, ContextVariable, MemoryBuffer,
    ContextEnvironment, RecursiveMemoryManager, ContextCompressor,
    OrganizationalMemory, SubAgentCall,
    create_agent_memory, load_molecule_to_memory, load_bead_history_to_memory
)

__all__ = [
    'Molecule', 'MoleculeStep', 'MoleculeStatus', 'MoleculeEngine',
    'Hook', 'HookManager',
    'Bead', 'BeadLedger',
    'Channel', 'ChannelType', 'ChannelManager',
    'Gate', 'GateStatus', 'GateKeeper',
    'WorkerPool', 'PoolManager',
    'RACI', 'RACIRole',
    'HiringManager', 'quick_hire',
    'IndustryTemplateManager', 'init_corp', 'INDUSTRY_TEMPLATES',
    # Memory system (RLM-inspired)
    'ContextType', 'ContextVariable', 'MemoryBuffer',
    'ContextEnvironment', 'RecursiveMemoryManager', 'ContextCompressor',
    'OrganizationalMemory', 'SubAgentCall',
    'create_agent_memory', 'load_molecule_to_memory', 'load_bead_history_to_memory',
]
