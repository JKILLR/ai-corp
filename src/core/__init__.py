"""
AI Corp Core Module

This module provides the core infrastructure for the AI Corporation:
- Molecules: Persistent workflows that survive agent crashes
- Hooks: Work queues for agents
- Beads: Git-backed ledger for state persistence
- Channels: Communication between agents
- Gates: Quality checkpoints
"""

from .molecule import Molecule, MoleculeStep, MoleculeStatus, MoleculeEngine
from .hook import Hook, HookManager
from .bead import Bead, BeadLedger
from .channel import Channel, ChannelType, ChannelManager
from .gate import Gate, GateStatus, GateKeeper
from .pool import WorkerPool, PoolManager
from .raci import RACI, RACIRole

__all__ = [
    'Molecule', 'MoleculeStep', 'MoleculeStatus', 'MoleculeEngine',
    'Hook', 'HookManager',
    'Bead', 'BeadLedger',
    'Channel', 'ChannelType', 'ChannelManager',
    'Gate', 'GateStatus', 'GateKeeper',
    'WorkerPool', 'PoolManager',
    'RACI', 'RACIRole',
]
