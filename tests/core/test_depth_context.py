"""
Tests for Depth-Based Context System.

Tests agent-level depth configuration for Entity Graph context retrieval.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.core.graph import (
    EntityGraph, EntityContext, get_entity_graph,
    DepthConfig, get_depth_for_level,
    AGENT_LEVEL_DEPTH_DEFAULTS, AGENT_LEVEL_CONTEXT_LIMITS
)
from src.core.entities import (
    Entity, EntityType, EntitySource, EntityStore,
    Relationship, RelationshipType
)
from src.agents.base import BaseAgent, AgentIdentity


class TestDepthConfig:
    """Tests for DepthConfig class"""

    def test_depth_config_defaults(self):
        """Test DepthConfig has correct defaults"""
        config = DepthConfig()
        assert config.depth == 1
        assert config.max_entities == 10
        assert config.max_relationships == 10
        assert config.max_interactions == 5
        assert config.include_network is False

    def test_for_executive_level(self):
        """Test depth config for executive (level 1)"""
        config = DepthConfig.for_agent_level(1)
        assert config.depth == 3
        assert config.max_entities == 20
        assert config.max_relationships == 30
        assert config.max_interactions == 15
        assert config.include_network is True

    def test_for_vp_level(self):
        """Test depth config for VP (level 2)"""
        config = DepthConfig.for_agent_level(2)
        assert config.depth == 2
        assert config.max_entities == 15
        assert config.max_relationships == 20
        assert config.max_interactions == 10
        assert config.include_network is True

    def test_for_director_level(self):
        """Test depth config for director (level 3)"""
        config = DepthConfig.for_agent_level(3)
        assert config.depth == 1
        assert config.max_entities == 10
        assert config.max_relationships == 10
        assert config.max_interactions == 5
        assert config.include_network is False

    def test_for_worker_level(self):
        """Test depth config for worker (level 4)"""
        config = DepthConfig.for_agent_level(4)
        assert config.depth == 0
        assert config.max_entities == 5
        assert config.max_relationships == 5
        assert config.max_interactions == 3
        assert config.include_network is False

    def test_executive_shorthand(self):
        """Test DepthConfig.executive() shorthand"""
        config = DepthConfig.executive()
        assert config.depth == 3
        assert config.include_network is True

    def test_vp_shorthand(self):
        """Test DepthConfig.vp() shorthand"""
        config = DepthConfig.vp()
        assert config.depth == 2
        assert config.include_network is True

    def test_director_shorthand(self):
        """Test DepthConfig.director() shorthand"""
        config = DepthConfig.director()
        assert config.depth == 1

    def test_worker_shorthand(self):
        """Test DepthConfig.worker() shorthand"""
        config = DepthConfig.worker()
        assert config.depth == 0

    def test_custom_config(self):
        """Test custom depth configuration"""
        config = DepthConfig.custom(
            depth=5,
            max_entities=50,
            max_relationships=100,
            max_interactions=25,
            include_network=True
        )
        assert config.depth == 5
        assert config.max_entities == 50
        assert config.max_relationships == 100
        assert config.max_interactions == 25
        assert config.include_network is True

    def test_unknown_level_defaults_to_director(self):
        """Test unknown level uses director defaults"""
        config = DepthConfig.for_agent_level(99)
        # Should use director defaults
        assert config.max_entities == 10
        assert config.depth == 1  # Fallback depth


class TestGetDepthForLevel:
    """Tests for get_depth_for_level function"""

    def test_executive_depth(self):
        """Test executive gets depth 3"""
        assert get_depth_for_level(1) == 3

    def test_vp_depth(self):
        """Test VP gets depth 2"""
        assert get_depth_for_level(2) == 2

    def test_director_depth(self):
        """Test director gets depth 1"""
        assert get_depth_for_level(3) == 1

    def test_worker_depth(self):
        """Test worker gets depth 0"""
        assert get_depth_for_level(4) == 0

    def test_unknown_level_defaults(self):
        """Test unknown level defaults to 1"""
        assert get_depth_for_level(99) == 1


class TestAgentLevelDefaults:
    """Tests for AGENT_LEVEL_DEPTH_DEFAULTS constant"""

    def test_all_levels_defined(self):
        """Test all 4 levels have depth definitions"""
        assert 1 in AGENT_LEVEL_DEPTH_DEFAULTS
        assert 2 in AGENT_LEVEL_DEPTH_DEFAULTS
        assert 3 in AGENT_LEVEL_DEPTH_DEFAULTS
        assert 4 in AGENT_LEVEL_DEPTH_DEFAULTS

    def test_depth_decreases_with_level(self):
        """Test that depth decreases as level increases"""
        assert AGENT_LEVEL_DEPTH_DEFAULTS[1] > AGENT_LEVEL_DEPTH_DEFAULTS[2]
        assert AGENT_LEVEL_DEPTH_DEFAULTS[2] > AGENT_LEVEL_DEPTH_DEFAULTS[3]
        assert AGENT_LEVEL_DEPTH_DEFAULTS[3] > AGENT_LEVEL_DEPTH_DEFAULTS[4]


class TestAgentLevelContextLimits:
    """Tests for AGENT_LEVEL_CONTEXT_LIMITS constant"""

    def test_all_levels_have_limits(self):
        """Test all 4 levels have context limits"""
        for level in [1, 2, 3, 4]:
            assert level in AGENT_LEVEL_CONTEXT_LIMITS
            limits = AGENT_LEVEL_CONTEXT_LIMITS[level]
            assert 'max_entities' in limits
            assert 'max_relationships' in limits
            assert 'max_interactions' in limits
            assert 'include_network' in limits

    def test_limits_decrease_with_level(self):
        """Test that limits decrease as level increases"""
        assert AGENT_LEVEL_CONTEXT_LIMITS[1]['max_entities'] > \
               AGENT_LEVEL_CONTEXT_LIMITS[4]['max_entities']

    def test_network_enabled_for_executives(self):
        """Test that network is enabled for executives and VPs"""
        assert AGENT_LEVEL_CONTEXT_LIMITS[1]['include_network'] is True
        assert AGENT_LEVEL_CONTEXT_LIMITS[2]['include_network'] is True
        assert AGENT_LEVEL_CONTEXT_LIMITS[3]['include_network'] is False
        assert AGENT_LEVEL_CONTEXT_LIMITS[4]['include_network'] is False


class TestEntityGraphDepthContext:
    """Tests for EntityGraph.get_context_for_agent method"""

    @pytest.fixture
    def temp_corp(self):
        """Create temporary corp directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def entity_graph(self, temp_corp):
        """Create an entity graph with test data"""
        graph = get_entity_graph(temp_corp)

        # Create some test entities
        alice = graph.entity_store.create_entity(
            name="Alice",
            entity_type=EntityType.PERSON,
            source=EntitySource.MANUAL
        )
        bob = graph.entity_store.create_entity(
            name="Bob",
            entity_type=EntityType.PERSON,
            source=EntitySource.MANUAL
        )
        charlie = graph.entity_store.create_entity(
            name="Charlie",
            entity_type=EntityType.PERSON,
            source=EntitySource.MANUAL
        )

        # Create relationships
        graph.entity_store.create_relationship(
            source_id=alice.id,
            target_id=bob.id,
            relationship_type=RelationshipType.COLLEAGUE
        )
        graph.entity_store.create_relationship(
            source_id=bob.id,
            target_id=charlie.id,
            relationship_type=RelationshipType.COLLEAGUE
        )

        # Store entity IDs for tests
        graph._test_entities = {
            'alice': alice.id,
            'bob': bob.id,
            'charlie': charlie.id
        }

        return graph

    def test_get_context_for_executive(self, entity_graph):
        """Test executive gets full context"""
        entity_ids = [entity_graph._test_entities['alice']]
        context = entity_graph.get_context_for_agent(
            entity_ids=entity_ids,
            agent_level=1
        )

        assert isinstance(context, EntityContext)
        assert context.summary is not None

    def test_get_context_for_worker(self, entity_graph):
        """Test worker gets limited context"""
        entity_ids = [entity_graph._test_entities['alice']]
        context = entity_graph.get_context_for_agent(
            entity_ids=entity_ids,
            agent_level=4
        )

        assert isinstance(context, EntityContext)
        # Worker should not get network context
        worker_config = DepthConfig.for_agent_level(4)
        assert worker_config.include_network is False

    def test_context_with_custom_config(self, entity_graph):
        """Test context with custom depth config"""
        entity_ids = [entity_graph._test_entities['alice']]
        custom_config = DepthConfig.custom(
            depth=0,
            max_entities=1,
            max_relationships=1,
            max_interactions=1,
            include_network=False
        )

        context = entity_graph.get_context_for_agent(
            entity_ids=entity_ids,
            agent_level=1,
            depth_config=custom_config
        )

        assert isinstance(context, EntityContext)

    def test_empty_entity_ids(self, entity_graph):
        """Test handling of empty entity IDs"""
        context = entity_graph.get_context_for_agent(
            entity_ids=[],
            agent_level=1
        )

        assert isinstance(context, EntityContext)
        assert len(context.entities) == 0


class TestAgentDepthIntegration:
    """Tests for BaseAgent depth integration"""

    @pytest.fixture
    def temp_corp(self):
        """Create temporary corp directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_agent_has_depth_config(self, temp_corp):
        """Test that agents get appropriate depth config"""
        # Create identities for different levels
        levels = {
            1: "COO",
            2: "VP",
            3: "Director",
            4: "Worker"
        }

        for level, name in levels.items():
            identity = AgentIdentity(
                id=f"agent-{level}",
                role_id=f"role-{level}",
                role_name=name,
                department="test",
                level=level
            )

            # Create a minimal test to verify depth config is set
            # (Can't fully instantiate BaseAgent as it's abstract)
            config = DepthConfig.for_agent_level(level)
            expected_depth = AGENT_LEVEL_DEPTH_DEFAULTS[level]
            assert config.depth == expected_depth

    def test_depth_config_consistency(self, temp_corp):
        """Test depth config matches AGENT_LEVEL_DEPTH_DEFAULTS"""
        for level in [1, 2, 3, 4]:
            config = DepthConfig.for_agent_level(level)
            assert config.depth == AGENT_LEVEL_DEPTH_DEFAULTS[level]

    def test_depth_config_limits_consistency(self, temp_corp):
        """Test depth config limits match AGENT_LEVEL_CONTEXT_LIMITS"""
        for level in [1, 2, 3, 4]:
            config = DepthConfig.for_agent_level(level)
            limits = AGENT_LEVEL_CONTEXT_LIMITS[level]
            assert config.max_entities == limits['max_entities']
            assert config.max_relationships == limits['max_relationships']
            assert config.max_interactions == limits['max_interactions']
            assert config.include_network == limits['include_network']


class TestDepthConfigToPrompt:
    """Tests for EntityContext.to_prompt() method"""

    @pytest.fixture
    def temp_corp(self):
        """Create temporary corp directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def entity_graph(self, temp_corp):
        """Create an entity graph with test data"""
        graph = get_entity_graph(temp_corp)

        # Create test entity
        alice = graph.entity_store.create_entity(
            name="Alice Smith",
            entity_type=EntityType.PERSON,
            source=EntitySource.MANUAL
        )
        graph._test_entities = {'alice': alice.id}
        return graph

    def test_context_to_prompt(self, entity_graph):
        """Test EntityContext can be converted to prompt"""
        entity_ids = [entity_graph._test_entities['alice']]
        context = entity_graph.get_context_for_agent(
            entity_ids=entity_ids,
            agent_level=1
        )

        prompt = context.to_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_context_to_dict(self, entity_graph):
        """Test EntityContext can be converted to dict"""
        entity_ids = [entity_graph._test_entities['alice']]
        context = entity_graph.get_context_for_agent(
            entity_ids=entity_ids,
            agent_level=1
        )

        context_dict = context.to_dict()
        assert isinstance(context_dict, dict)
        assert 'entities' in context_dict
        assert 'relationships' in context_dict
        assert 'summary' in context_dict


# Run a quick smoke test
if __name__ == "__main__":
    print("Running depth-based context smoke tests...")

    # Test DepthConfig
    config = DepthConfig.for_agent_level(1)
    assert config.depth == 3, "Executive should have depth 3"
    print("✓ DepthConfig for executive")

    config = DepthConfig.for_agent_level(4)
    assert config.depth == 0, "Worker should have depth 0"
    print("✓ DepthConfig for worker")

    # Test get_depth_for_level
    assert get_depth_for_level(1) == 3
    assert get_depth_for_level(4) == 0
    print("✓ get_depth_for_level")

    # Test constants
    assert len(AGENT_LEVEL_DEPTH_DEFAULTS) == 4
    assert len(AGENT_LEVEL_CONTEXT_LIMITS) == 4
    print("✓ Constants defined")

    print("\nAll smoke tests passed!")
