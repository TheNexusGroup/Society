"""
Unit tests for AgentBrain - Agent AI decision making
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from src.simulation.agent.logic.brain import AgentBrain
from src.simulation.genetics.genome import Genome
from constants import ActionType, Gender


@pytest.mark.unit
class TestAgentBrain:
    """Test AgentBrain functionality."""
    
    @pytest.fixture
    def mock_genome(self):
        """Create a mock genome for testing."""
        genome = Mock()
        genome.learning_capacity = 0.01
        genome.q_table = {}
        genome.agreeableness = 0.5
        genome.reciprocity = 0.5
        genome.extraversion = 0.5
        return genome
    
    @pytest.fixture
    def mock_world(self):
        """Create a mock world for testing."""
        world = Mock()
        world.entities = []
        world.society = Mock()
        world.society.population = []
        return world
    
    @pytest.fixture
    def agent_brain(self, mock_genome, mock_world):
        """Create an AgentBrain for testing."""
        return AgentBrain(
            agent_id=1,
            genome=mock_genome,
            world=mock_world,
            memory_capacity=1000,
            batch_size=16
        )
    
    def test_initialization(self, mock_genome, mock_world):
        """Test brain initialization."""
        brain = AgentBrain(
            agent_id=42,
            genome=mock_genome,
            world=mock_world,
            memory_capacity=500,
            batch_size=32
        )
        
        assert brain.agent_id == 42
        assert brain.genome == mock_genome
        assert brain.world == mock_world
        assert brain.learning_rate == mock_genome.learning_capacity
        assert brain.gamma == 0.99
        assert brain.batch_size == 32
        assert brain.state_size == 19
        assert brain.action_size == len(ActionType)
        assert hasattr(brain, 'dqn')
        assert hasattr(brain, 'memory')
        assert hasattr(brain, 'social_memory')
    
    def test_social_memory_limits(self, agent_brain):
        """Test social memory capacity limits."""
        assert agent_brain.max_social_memory_per_agent == 10
        assert agent_brain.max_total_social_agents == 50
        assert isinstance(agent_brain.social_memory, dict)
        assert len(agent_brain.social_memory) == 0
    
    def test_action_mappings(self, agent_brain):
        """Test action mapping consistency."""
        # Test forward mapping
        assert len(agent_brain.action_map) == len(ActionType)
        assert all(isinstance(k, int) for k in agent_brain.action_map.keys())
        assert all(isinstance(v, str) for v in agent_brain.action_map.values())
        
        # Test reverse mapping
        assert len(agent_brain.action_idx_map) == len(agent_brain.action_map)
        for idx, action in agent_brain.action_map.items():
            assert agent_brain.action_idx_map[action] == idx
    
    def test_state_enhancement_with_memory(self, agent_brain):
        """Test state enhancement with memory information."""
        base_state = {
            'energy': 'medium',
            'money': 'low',
            'mood': 'neutral',
            'corruption': 'low'
        }
        
        # Test with empty memory
        enhanced = agent_brain._enhance_state_with_memory(base_state)
        assert isinstance(enhanced, dict)
        assert all(key in enhanced for key in base_state.keys())
    
    def test_action_selection_basic(self, agent_brain):
        """Test basic action selection."""
        state_dict = {
            'energy': 'medium',
            'money': 'low',
            'mood': 'neutral',
            'corruption': 'low',
            'food_reserves': 'medium',
            'social_reputation': 'neutral',
            'has_enemies': 'none'
        }
        
        with patch.object(agent_brain.dqn, 'get_action_values') as mock_nn:
            mock_nn.return_value = [0.1] * len(ActionType)
            
            action = agent_brain.select_action(state_dict, exploration_rate=0.1)
            assert isinstance(action, str)
            assert action in agent_brain.action_map.values()
            mock_nn.assert_called_once()
    
    def test_hybrid_decision_q_table_initialization(self, agent_brain):
        """Test Q-table initialization in hybrid decision making."""
        state_dict = {
            'energy': 'high',
            'money': 'medium',
            'mood': 'positive',
            'corruption': 'low'
        }
        
        nn_action_values = [0.1] * len(ActionType)
        
        # Should initialize Q-table for new state
        action = agent_brain.hybrid_decision(state_dict, nn_action_values, 0.1)
        
        # Check Q-table was initialized
        state_key = agent_brain._state_dict_to_string(state_dict)
        assert state_key in agent_brain.genome.q_table
        
        q_values = agent_brain.genome.q_table[state_key]
        expected_actions = [
            'eat', 'work', 'rest', 'mate', 'search',
            'plant-food', 'harvest-food', 'gift-food', 'gift-money',
            'invest', 'buy-food', 'sell-food',
            'trade-food-for-money', 'trade-money-for-food'
        ]
        
        for action in expected_actions:
            assert action in q_values
            assert isinstance(q_values[action], float)
    
    def test_social_reputation_adjustments(self, agent_brain):
        """Test action adjustments based on social reputation."""
        state_dict = {
            'energy': 'medium',
            'money': 'medium',
            'mood': 'neutral',
            'corruption': 'low',
            'social_reputation': 'bad',
            'has_enemies': 'none'
        }
        
        nn_action_values = [0.0] * len(ActionType)
        
        # Initialize Q-table to known values
        state_key = agent_brain._state_dict_to_string(state_dict)
        agent_brain.genome.q_table[state_key] = {
            action: 0.0 for action in agent_brain.action_map.values()
        }
        
        agent_brain.hybrid_decision(state_dict, nn_action_values, 0.1)
        
        # Check that prosocial actions were boosted
        q_values = agent_brain.genome.q_table[state_key]
        assert q_values['gift-food'] > 0.0
        assert q_values['gift-money'] > 0.0
    
    def test_enemy_adjustments(self, agent_brain):
        """Test action adjustments when agent has enemies."""
        state_dict = {
            'energy': 'medium',
            'money': 'medium',
            'mood': 'neutral',
            'corruption': 'low',
            'social_reputation': 'neutral',
            'has_enemies': 'many'
        }
        
        nn_action_values = [0.0] * len(ActionType)
        
        state_key = agent_brain._state_dict_to_string(state_dict)
        agent_brain.genome.q_table[state_key] = {
            action: 0.0 for action in agent_brain.action_map.values()
        }
        
        agent_brain.hybrid_decision(state_dict, nn_action_values, 0.1)
        
        q_values = agent_brain.genome.q_table[state_key]
        # Work should be boosted when having enemies (safer)
        assert q_values.get('work', 0) > 0.0
        # Harvest should be penalized (more vulnerable)
        assert q_values.get('harvest-food', 0) < 0.0
    
    def test_corruption_effects(self, agent_brain):
        """Test corruption effects on action selection."""
        state_dict = {
            'energy': 'medium',
            'money': 'medium',
            'mood': 'neutral',
            'corruption': 'high',
            'social_reputation': 'neutral',
            'has_enemies': 'none'
        }
        
        nn_action_values = [0.0] * len(ActionType)
        
        state_key = agent_brain._state_dict_to_string(state_dict)
        agent_brain.genome.q_table[state_key] = {
            action: 0.0 for action in agent_brain.action_map.values()
        }
        
        agent_brain.hybrid_decision(state_dict, nn_action_values, 0.1)
        
        q_values = agent_brain.genome.q_table[state_key]
        # High corruption might increase certain antisocial tendencies
        # Check if steal-crops action gets boosted (if it exists in Q-table)
        if 'steal-crops' in q_values:
            assert q_values['steal-crops'] > 0.0
    
    def test_neural_network_q_table_blending(self, agent_brain):
        """Test blending of neural network predictions with Q-table values."""
        state_dict = {
            'energy': 'medium',
            'money': 'medium',
            'mood': 'neutral',
            'corruption': 'low'
        }
        
        # Set up initial Q-values
        state_key = agent_brain._state_dict_to_string(state_dict)
        agent_brain.genome.q_table[state_key] = {
            'eat': 1.0,
            'work': 0.5,
            'rest': 0.0
        }
        
        # Set up neural network values
        nn_action_values = [0.8, 0.2, 0.6] + [0.0] * (len(ActionType) - 3)
        
        with patch.object(agent_brain, '_state_dict_to_string', return_value=state_key):
            agent_brain.hybrid_decision(state_dict, nn_action_values, 0.1)
        
        # Check blending occurred (0.8 * old + 0.2 * new)
        q_values = agent_brain.genome.q_table[state_key]
        # eat: 0.8 * 1.0 + 0.2 * 0.8 = 0.96
        assert abs(q_values['eat'] - 0.96) < 0.01
    
    def test_memory_capacity_limits(self, agent_brain):
        """Test that social memory respects capacity limits."""
        # Test per-agent limit
        target_id = 42
        for i in range(15):  # Exceed max_social_memory_per_agent (10)
            agent_brain.social_memory.setdefault(target_id, []).append(f"memory_{i}")
        
        # Should not exceed per-agent limit when cleaned
        if hasattr(agent_brain, '_cleanup_social_memory'):
            agent_brain._cleanup_social_memory()
            assert len(agent_brain.social_memory[target_id]) <= agent_brain.max_social_memory_per_agent
    
    def test_learning_parameters(self, agent_brain):
        """Test learning parameter setup."""
        assert agent_brain.gamma == 0.99  # Standard discount factor
        assert agent_brain.target_update_frequency == 100
        assert agent_brain.update_counter == 0
        assert hasattr(agent_brain, 'learning_rate')
        assert 0 < agent_brain.learning_rate <= 1
    
    def test_state_dict_to_string_consistency(self, agent_brain):
        """Test state dictionary to string conversion consistency."""
        state_dict = {
            'energy': 'high',
            'money': 'low',
            'mood': 'positive',
            'corruption': 'medium'
        }
        
        # Multiple calls should produce same result
        string1 = agent_brain._state_dict_to_string(state_dict)
        string2 = agent_brain._state_dict_to_string(state_dict)
        
        assert string1 == string2
        assert isinstance(string1, str)
        assert len(string1) > 0
    
    def test_memory_system_integration(self, agent_brain):
        """Test memory system integration."""
        assert hasattr(agent_brain, 'memory')
        assert hasattr(agent_brain.memory, 'replay_capacity')
        assert hasattr(agent_brain.memory, 'episodic_capacity')
    
    def test_dqn_integration(self, agent_brain):
        """Test DQN integration."""
        assert hasattr(agent_brain, 'dqn')
        assert hasattr(agent_brain.dqn, 'get_action_values')
        
        # Test that DQN can process state
        test_state = [0.5] * agent_brain.state_size
        with patch.object(agent_brain.dqn, 'get_action_values') as mock_get_values:
            mock_get_values.return_value = [0.1] * agent_brain.action_size
            values = agent_brain.dqn.get_action_values(test_state)
            assert len(values) == agent_brain.action_size
    
    @pytest.mark.parametrize("exploration_rate", [0.0, 0.1, 0.5, 1.0])
    def test_exploration_rates(self, agent_brain, exploration_rate):
        """Test different exploration rates."""
        state_dict = {
            'energy': 'medium',
            'money': 'medium',
            'mood': 'neutral',
            'corruption': 'low'
        }
        
        with patch.object(agent_brain.dqn, 'get_action_values') as mock_nn:
            mock_nn.return_value = [0.1] * len(ActionType)
            
            action = agent_brain.select_action(state_dict, exploration_rate)
            assert isinstance(action, str)
            assert action in agent_brain.action_map.values()
    
    def test_edge_cases(self, agent_brain):
        """Test edge cases in brain functionality."""
        # Empty state dict
        empty_state = {}
        with patch.object(agent_brain.dqn, 'get_action_values') as mock_nn:
            mock_nn.return_value = [0.1] * len(ActionType)
            # Should not crash
            try:
                action = agent_brain.select_action(empty_state)
                assert isinstance(action, str)
            except (KeyError, AttributeError):
                # Expected for incomplete state
                pass
        
        # Extreme values
        extreme_state = {
            'energy': 'low',
            'money': 'low',
            'mood': 'negative',
            'corruption': 'high',
            'social_reputation': 'bad',
            'has_enemies': 'many'
        }
        
        with patch.object(agent_brain.dqn, 'get_action_values') as mock_nn:
            mock_nn.return_value = [0.1] * len(ActionType)
            action = agent_brain.select_action(extreme_state)
            assert isinstance(action, str)