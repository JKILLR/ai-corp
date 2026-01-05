"""
Pytest Configuration and Fixtures

Provides shared fixtures for all AI Corp tests.
"""

import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_corp_path():
    """Create a temporary corporation directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix='ai_corp_test_')
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def initialized_corp(temp_corp_path):
    """Create an initialized corporation with standard structure."""
    from src.core.templates import init_corp

    init_corp(Path(temp_corp_path), industry='software')
    return temp_corp_path


@pytest.fixture
def molecule_engine(temp_corp_path):
    """Create a MoleculeEngine instance."""
    from src.core.molecule import MoleculeEngine

    # MoleculeEngine takes base_path and creates molecules/ subdirectory internally
    return MoleculeEngine(temp_corp_path)


@pytest.fixture
def hook_manager(temp_corp_path):
    """Create a HookManager instance."""
    from src.core.hook import HookManager

    hooks_path = os.path.join(temp_corp_path, 'hooks')
    os.makedirs(hooks_path, exist_ok=True)
    return HookManager(hooks_path)


@pytest.fixture
def bead_ledger(temp_corp_path):
    """Create a BeadLedger instance."""
    from src.core.bead import BeadLedger

    # BeadLedger creates beads/ subdir automatically
    return BeadLedger(temp_corp_path)


@pytest.fixture
def channel_manager(temp_corp_path):
    """Create a ChannelManager instance."""
    from src.core.channel import ChannelManager

    channels_path = os.path.join(temp_corp_path, 'channels')
    os.makedirs(channels_path, exist_ok=True)
    return ChannelManager(channels_path)


@pytest.fixture
def gate_keeper(temp_corp_path):
    """Create a GateKeeper instance."""
    from src.core.gate import GateKeeper

    gates_path = os.path.join(temp_corp_path, 'gates')
    os.makedirs(gates_path, exist_ok=True)
    return GateKeeper(gates_path)


@pytest.fixture
def pool_manager(temp_corp_path):
    """Create a PoolManager instance."""
    from src.core.pool import PoolManager

    pools_path = os.path.join(temp_corp_path, 'pools')
    os.makedirs(pools_path, exist_ok=True)
    return PoolManager(pools_path)


@pytest.fixture
def mock_backend():
    """Create a MockBackend for LLM testing."""
    from src.core.llm import MockBackend
    return MockBackend()


@pytest.fixture
def sample_raci():
    """Create a sample RACI assignment."""
    from src.core.raci import RACI, RACIRole

    return RACI(
        responsible=['worker-001'],
        accountable='dir_frontend',
        consulted=['vp_engineering'],
        informed=['coo']
    )


@pytest.fixture
def sample_molecule_data():
    """Sample data for creating a molecule."""
    return {
        'name': 'Test Molecule',
        'description': 'A test molecule for unit tests',
        'steps': [
            {
                'id': 'step-1',
                'name': 'Research',
                'description': 'Research the problem',
                'assigned_to': 'vp_research',
                'dependencies': []
            },
            {
                'id': 'step-2',
                'name': 'Design',
                'description': 'Design the solution',
                'assigned_to': 'vp_product',
                'dependencies': ['step-1']
            },
            {
                'id': 'step-3',
                'name': 'Build',
                'description': 'Build the solution',
                'assigned_to': 'vp_engineering',
                'dependencies': ['step-2']
            }
        ]
    }


@pytest.fixture
def sample_work_item_data():
    """Sample data for creating a work item."""
    return {
        'title': 'Test Work Item',
        'description': 'A test work item',
        'molecule_id': 'MOL-TEST123',
        'step_id': 'step-1',
        'priority': 1,
        'required_capabilities': ['research', 'analysis'],
        'context': {
            'molecule_name': 'Test Molecule',
            'is_gate': False
        }
    }
