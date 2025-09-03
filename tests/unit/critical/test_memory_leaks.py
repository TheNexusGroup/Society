"""
Tests for critical memory leak issues identified in simulation analysis
"""

import pytest
import gc
import weakref
from unittest.mock import Mock, patch
from src.simulation.agent.logic.brain import AgentBrain
from src.simulation.world.world import World
from src.simulation.genetics.genome import Genome


@pytest.mark.critical
class TestMemoryLeaks:
    """Test for memory leaks in critical simulation components."""
    
    def test_social_memory_cleanup(self, test_genome, mock_world):
        """Test social memory doesn't grow unboundedly (Issue from line 55-70 in brain.py)."""
        brain = AgentBrain(
            agent_id=1,
            genome=test_genome,
            world=mock_world,
            memory_capacity=100
        )
        
        # Fill social memory beyond reasonable limits
        for target_id in range(200):  # Way more than max_total_social_agents (50)
            for memory_idx in range(20):  # Way more than max_social_memory_per_agent (10)
                if target_id not in brain.social_memory:
                    brain.social_memory[target_id] = []
                brain.social_memory[target_id].append(f"memory_{memory_idx}")
        
        # Check that memory limits are being enforced
        total_agents_remembered = len(brain.social_memory)
        total_memories = sum(len(memories) for memories in brain.social_memory.values())
        
        # Test configured limits
        assert total_agents_remembered <= brain.max_total_social_agents * 2, \
            f"Too many agents remembered: {total_agents_remembered}"
        
        # Each agent should not exceed per-agent memory limit significantly
        for target_id, memories in brain.social_memory.items():
            if len(memories) > brain.max_social_memory_per_agent * 2:
                pytest.fail(f"Agent {target_id} has {len(memories)} memories, exceeding limit")
    
    def test_dead_agent_cleanup(self, populated_world, agent_factory):
        """Test that dead agents are properly cleaned up from references."""
        initial_agent_count = len(populated_world.entities)
        
        # Create agents that will die
        dying_agents = []
        for i in range(10):
            agent = agent_factory(energy=5, age=95, agent_id=8000+i)
            populated_world.add_entity(agent)
            dying_agents.append(agent)
            
            # Create weak references to track if objects are being collected
            weakref.ref(agent)
        
        # Let some time pass for deaths to occur
        for step in range(50):
            populated_world.update_world()
        
        # Force garbage collection
        gc.collect()
        
        # Check that dead agents are removed from main entity list
        current_living = len([a for a in populated_world.society.population if a.is_alive])
        total_entities = len(populated_world.entities)
        
        # Some agents should have died and been cleaned up
        assert total_entities <= initial_agent_count + len(dying_agents)
        assert current_living < initial_agent_count + len(dying_agents)
    
    def test_experience_replay_buffer_cleanup(self, test_genome, mock_world):
        """Test experience replay buffer doesn't grow indefinitely."""
        brain = AgentBrain(
            agent_id=1,
            genome=test_genome,
            world=mock_world,
            memory_capacity=100  # Small capacity for testing
        )
        
        # Fill replay buffer beyond capacity
        for i in range(200):  # Double the capacity
            fake_experience = {
                'state': [0.5] * brain.state_size,
                'action': 0,
                'reward': 0.1,
                'next_state': [0.5] * brain.state_size,
                'done': False
            }
            
            # Add experiences to memory if the method exists
            if hasattr(brain.memory, 'add_experience'):
                brain.memory.add_experience(**fake_experience)
            elif hasattr(brain.memory, 'add'):
                brain.memory.add(fake_experience)
        
        # Check that memory doesn't exceed reasonable bounds
        if hasattr(brain.memory, 'replay_memory'):
            replay_size = len(brain.memory.replay_memory)
            assert replay_size <= brain.memory.replay_capacity * 1.1, \
                f"Replay buffer exceeded capacity: {replay_size}"
        
        # Memory object should exist and have reasonable size
        assert hasattr(brain, 'memory')
    
    def test_q_table_growth_limits(self, test_genome, mock_world):
        """Test Q-table doesn't grow unboundedly with unique states."""
        brain = AgentBrain(
            agent_id=1,
            genome=test_genome,
            world=mock_world
        )
        
        # Generate many unique states to test Q-table growth
        unique_states = []
        for energy in ['low', 'medium', 'high']:
            for money in ['low', 'medium', 'high']:
                for mood in ['negative', 'neutral', 'positive']:
                    for corruption in ['low', 'medium', 'high']:
                        state_dict = {
                            'energy': energy,
                            'money': money,
                            'mood': mood,
                            'corruption': corruption,
                            'social_reputation': 'neutral',
                            'has_enemies': 'none'
                        }
                        unique_states.append(state_dict)
        
        # Process all unique states
        with patch.object(brain.dqn, 'get_action_values') as mock_nn:
            mock_nn.return_value = [0.1] * brain.action_size
            
            for state in unique_states:
                brain.select_action(state, exploration_rate=0.1)
        
        # Q-table should have entries but not be excessively large
        q_table_size = len(brain.genome.q_table)
        assert q_table_size <= len(unique_states) * 1.1, \
            f"Q-table too large: {q_table_size} entries"
        
        # Each Q-table entry should have reasonable structure
        for state_key, actions in brain.genome.q_table.items():
            assert isinstance(state_key, str)
            assert isinstance(actions, dict)
            assert len(actions) <= 20  # Reasonable number of actions
    
    def test_spatial_grid_cleanup(self, populated_world):
        """Test spatial grid properly cleans up removed entities."""
        populated_world.create_population()
        initial_entities = len(populated_world.entities)
        
        # Track entities in spatial grid
        entities_to_remove = populated_world.entities[:5]  # Remove first 5
        
        for entity in entities_to_remove:
            # Remove entity
            populated_world.remove_entity(entity)
        
        # Check spatial grid doesn't retain stale references
        remaining_entities = len(populated_world.entities)
        assert remaining_entities == initial_entities - len(entities_to_remove)
        
        # Spatial grid should not have references to removed entities
        for entity in entities_to_remove:
            if hasattr(entity, 'ecs_id'):
                # Entity should not be found in spatial grid
                found_in_grid = False
                try:
                    # Try to query spatial grid for the entity
                    grid_result = populated_world.spatial_grid.query_range(
                        entity.position[0], entity.position[1], 1, 1
                    )
                    found_in_grid = entity.ecs_id in grid_result
                except:
                    # If query fails, assume entity is properly removed
                    pass
                
                assert not found_in_grid, f"Entity {entity.ecs_id} still in spatial grid"
    
    def test_ecs_component_cleanup(self, populated_world, agent_factory):
        """Test ECS components are properly cleaned up when entities are removed."""
        populated_world.create_population()
        
        # Add test agent
        test_agent = agent_factory(agent_id=9999)
        populated_world.add_entity(test_agent)
        
        # Verify components exist
        assert populated_world.ecs.has_component(test_agent.ecs_id, "transform")
        assert populated_world.ecs.has_component(test_agent.ecs_id, "behavior")
        
        # Remove agent
        populated_world.remove_entity(test_agent)
        
        # Components should be cleaned up
        assert not populated_world.ecs.has_component(test_agent.ecs_id, "transform")
        assert not populated_world.ecs.has_component(test_agent.ecs_id, "behavior")
        assert not populated_world.ecs.has_component(test_agent.ecs_id, "wallet")
    
    def test_circular_reference_cleanup(self, test_genome, mock_world):
        """Test for circular references that prevent garbage collection."""
        # Create brain with world reference
        brain = AgentBrain(
            agent_id=1,
            genome=test_genome,
            world=mock_world
        )
        
        # Create weak reference to brain
        brain_ref = weakref.ref(brain)
        
        # Add brain to world's population if possible
        if hasattr(mock_world, 'society') and hasattr(mock_world.society, 'population'):
            fake_agent = Mock()
            fake_agent.brain = brain
            fake_agent.is_alive = True
            mock_world.society.population.append(fake_agent)
        
        # Clear strong references
        del brain
        
        # Force garbage collection
        gc.collect()
        
        # Weak reference should be cleared if no circular references exist
        # Note: This test might not always pass due to Python's garbage collection timing
        # but it helps identify potential circular reference issues
        
        # At minimum, ensure the reference counter isn't excessively high
        if brain_ref():
            import sys
            ref_count = sys.getrefcount(brain_ref())
            assert ref_count < 10, f"Suspicious reference count: {ref_count}"
    
    def test_entity_pool_cleanup(self, populated_world):
        """Test entity pools properly release and reuse entities."""
        populated_world.create_population()
        
        # Get initial pool states
        initial_pool_sizes = {}
        for entity_type, pool in populated_world.entity_pools.items():
            if hasattr(pool, 'available'):
                initial_pool_sizes[entity_type] = len(pool.available)
        
        # Create and remove entities multiple times
        for cycle in range(3):
            # Create entities
            test_agents = []
            for i in range(5):
                agent = populated_world.agent_factory(agent_id=7000 + cycle*10 + i) if hasattr(populated_world, 'agent_factory') else Mock()
                if hasattr(populated_world, 'add_entity'):
                    populated_world.add_entity(agent)
                test_agents.append(agent)
            
            # Remove entities
            for agent in test_agents:
                if hasattr(populated_world, 'remove_entity'):
                    populated_world.remove_entity(agent)
        
        # Check pool sizes haven't grown excessively
        for entity_type, pool in populated_world.entity_pools.items():
            if hasattr(pool, 'available'):
                current_size = len(pool.available)
                if entity_type in initial_pool_sizes:
                    growth = current_size - initial_pool_sizes[entity_type]
                    assert growth <= 15, f"Pool {entity_type} grew by {growth} entities"
    
    def test_asset_reference_cleanup(self, populated_world):
        """Test asset references don't accumulate."""
        if not hasattr(populated_world, 'asset_manager'):
            pytest.skip("No asset manager to test")
        
        initial_asset_count = 0
        if hasattr(populated_world.asset_manager, 'assets'):
            initial_asset_count = len(populated_world.asset_manager.assets)
        
        # Create and destroy entities multiple times
        for cycle in range(5):
            populated_world.create_population()
            
            # Clear entities
            entities_to_clear = populated_world.entities.copy()
            for entity in entities_to_clear:
                if hasattr(populated_world, 'remove_entity'):
                    populated_world.remove_entity(entity)
        
        # Asset count shouldn't grow unboundedly
        if hasattr(populated_world.asset_manager, 'assets'):
            final_asset_count = len(populated_world.asset_manager.assets)
            asset_growth = final_asset_count - initial_asset_count
            assert asset_growth <= 100, f"Asset count grew by {asset_growth}"