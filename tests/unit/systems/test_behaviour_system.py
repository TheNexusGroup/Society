"""
Unit tests for BehaviorSystem
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.core.ecs.systems.behaviour import BehaviorSystem
from constants import ActionType


@pytest.mark.unit
class TestBehaviorSystem:
    """Test BehaviorSystem functionality."""
    
    @pytest.fixture
    def mock_world(self):
        """Create a mock world for testing."""
        world = Mock()
        world.ecs = Mock()
        world.spatial_grid = Mock()
        return world
    
    @pytest.fixture
    def behavior_system(self, mock_world):
        """Create a BehaviorSystem for testing."""
        return BehaviorSystem(mock_world)
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock()
        agent.energy = 50
        agent.money = 30
        agent.mood = 0.1
        agent.corruption_level = 0.2
        agent.age = 25
        agent.genome = Mock()
        agent.genome.q_table = {}
        agent.brain = None
        return agent
    
    def test_initialization(self, mock_world):
        """Test system initialization."""
        system = BehaviorSystem(mock_world)
        
        assert system.world == mock_world
        assert system.update_frequency == 1
        assert hasattr(system, 'q_learning')
        assert hasattr(system, 'REWARD_SCALES')
    
    def test_reward_normalization(self, behavior_system):
        """Test reward normalization functionality."""
        # Test valid action category
        normalized = behavior_system.normalize_reward('eat', 5.0)
        assert normalized <= 2.0  # Should be clamped to max
        
        normalized = behavior_system.normalize_reward('eat', -2.0)
        assert normalized >= -0.5  # Should be clamped to min
        
        # Test invalid action category
        normalized = behavior_system.normalize_reward('invalid', 5.0)
        assert normalized <= 2.0  # Should use default clamp
        
        normalized = behavior_system.normalize_reward('invalid', -5.0)
        assert normalized >= -1.0  # Should use default clamp
    
    @pytest.mark.parametrize("energy,expected", [
        (10, "low"),
        (30, "medium"),
        (50, "medium"),
        (70, "high"),
        (100, "high")
    ])
    def test_energy_level_categorization(self, behavior_system, energy, expected):
        """Test energy level categorization."""
        result = behavior_system._get_energy_level(energy)
        assert result == expected
    
    @pytest.mark.parametrize("money,expected", [
        (10, "low"),
        (20, "medium"),
        (40, "medium"),
        (60, "high"),
        (100, "high")
    ])
    def test_money_level_categorization(self, behavior_system, money, expected):
        """Test money level categorization."""
        result = behavior_system._get_money_level(money)
        assert result == expected
    
    @pytest.mark.parametrize("mood,expected", [
        (-0.5, "negative"),
        (-0.3, "neutral"),
        (0.0, "neutral"),
        (0.3, "positive"),
        (0.5, "positive")
    ])
    def test_mood_level_categorization(self, behavior_system, mood, expected):
        """Test mood level categorization."""
        result = behavior_system._get_mood_level(mood)
        assert result == expected
    
    @pytest.mark.parametrize("corruption,expected", [
        (0.1, "low"),
        (0.3, "medium"),
        (0.5, "medium"),
        (0.7, "high"),
        (0.9, "high")
    ])
    def test_corruption_level_categorization(self, behavior_system, corruption, expected):
        """Test corruption level categorization."""
        result = behavior_system._get_corruption_level(corruption)
        assert result == expected
    
    def test_state_representation(self, behavior_system, mock_agent):
        """Test state representation generation."""
        state = behavior_system.get_state_representation(mock_agent)
        
        assert isinstance(state, str)
        assert "medium_low_neutral_low" == state  # Expected based on mock_agent values
    
    def test_state_representation_consistency(self, behavior_system, mock_agent):
        """Test that state representation is consistent for same inputs."""
        state1 = behavior_system.get_state_representation(mock_agent)
        state2 = behavior_system.get_state_representation(mock_agent)
        
        assert state1 == state2
    
    def test_action_selection_with_brain(self, behavior_system, mock_agent):
        """Test action selection when agent has a brain."""
        # Setup agent with brain
        mock_brain = Mock()
        mock_brain.select_action.return_value = "eat"
        mock_agent.brain = mock_brain
        
        action = behavior_system.select_action(mock_agent)
        
        assert action == "eat"
        mock_brain.select_action.assert_called_once()
        
        # Check that the state_dict was passed correctly
        call_args = mock_brain.select_action.call_args
        state_dict = call_args[0][0]
        exploration_rate = call_args[0][1]
        
        assert 'energy' in state_dict
        assert 'money' in state_dict
        assert 'mood' in state_dict
        assert isinstance(exploration_rate, float)
        assert 0 <= exploration_rate <= 1
    
    def test_action_selection_without_brain(self, behavior_system, mock_agent):
        """Test action selection fallback when agent has no brain."""
        # Ensure no brain
        mock_agent.brain = None
        
        # Mock q_learning select_action
        behavior_system.q_learning.select_action = Mock(return_value="work")
        
        action = behavior_system.select_action(mock_agent)
        
        assert action == "work"
        behavior_system.q_learning.select_action.assert_called_once()
    
    def test_exploration_rate_calculation(self, behavior_system):
        """Test exploration rate calculation based on age."""
        # Young agent should have higher exploration
        young_agent = Mock()
        young_agent.age = 10
        young_agent.energy = 50
        young_agent.money = 30
        young_agent.mood = 0.1
        young_agent.corruption_level = 0.2
        young_agent.genome = Mock()
        young_agent.genome.q_table = {}
        young_agent.brain = None
        
        behavior_system.q_learning.select_action = Mock(return_value="explore")
        behavior_system.select_action(young_agent)
        
        call_args = behavior_system.q_learning.select_action.call_args
        young_exploration_rate = call_args[0][2]
        
        # Old agent should have lower exploration
        old_agent = Mock()
        old_agent.age = 100
        old_agent.energy = 50
        old_agent.money = 30
        old_agent.mood = 0.1
        old_agent.corruption_level = 0.2
        old_agent.genome = Mock()
        old_agent.genome.q_table = {}
        old_agent.brain = None
        
        behavior_system.q_learning.select_action = Mock(return_value="work")
        behavior_system.select_action(old_agent)
        
        call_args = behavior_system.q_learning.select_action.call_args
        old_exploration_rate = call_args[0][2]
        
        assert young_exploration_rate > old_exploration_rate
    
    def test_reward_scales_coverage(self, behavior_system):
        """Test that reward scales cover expected action categories."""
        expected_categories = [
            'eat', 'work', 'rest', 'mate', 'search',
            'plant', 'harvest', 'gift', 'trade', 'invest', 'buy', 'sell'
        ]
        
        for category in expected_categories:
            assert category in behavior_system.REWARD_SCALES
            scales = behavior_system.REWARD_SCALES[category]
            assert 'min' in scales
            assert 'max' in scales
            assert 'base' in scales
            assert scales['min'] <= scales['max']
    
    def test_reward_scale_bounds(self, behavior_system):
        """Test that reward scale bounds are reasonable."""
        for category, scales in behavior_system.REWARD_SCALES.items():
            # Minimum should be negative or zero (punishment possible)
            assert scales['min'] <= 0
            
            # Maximum should be positive (reward possible)
            assert scales['max'] > 0
            
            # Base should be between min and max
            assert scales['min'] <= scales['base'] <= scales['max']
    
    @pytest.mark.parametrize("raw_reward,category,expected_bounds", [
        (5.0, 'eat', (-0.5, 2.0)),
        (-2.0, 'work', (-1.0, 2.0)),
        (1.0, 'rest', (0.0, 1.5)),
        (10.0, 'invalid', (-1.0, 2.0))
    ])
    def test_reward_normalization_bounds(self, behavior_system, raw_reward, category, expected_bounds):
        """Test reward normalization respects bounds."""
        normalized = behavior_system.normalize_reward(category, raw_reward)
        min_bound, max_bound = expected_bounds
        
        assert min_bound <= normalized <= max_bound
    
    def test_system_consistency(self, behavior_system, mock_agent):
        """Test that system produces consistent results."""
        # Multiple calls with same agent should produce same state representation
        states = [behavior_system.get_state_representation(mock_agent) for _ in range(5)]
        assert all(state == states[0] for state in states)
    
    def test_edge_case_values(self, behavior_system):
        """Test system handles edge case values properly."""
        edge_agent = Mock()
        edge_agent.energy = 0  # Minimum energy
        edge_agent.money = 0   # No money
        edge_agent.mood = -1.0 # Extreme negative mood
        edge_agent.corruption_level = 1.0  # Maximum corruption
        edge_agent.age = 0     # Newborn
        edge_agent.genome = Mock()
        edge_agent.genome.q_table = {}
        edge_agent.brain = None
        
        # Should not crash and should produce valid state
        state = behavior_system.get_state_representation(edge_agent)
        assert isinstance(state, str)
        assert len(state.split('_')) == 4  # Should have 4 components
    
    def test_system_update_frequency(self, behavior_system):
        """Test that system has correct update frequency for critical behavior."""
        # Behavior system should update every frame (frequency = 1)
        assert behavior_system.update_frequency == 1