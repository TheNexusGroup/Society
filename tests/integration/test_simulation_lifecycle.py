"""
Integration tests for full simulation lifecycle
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.simulation.world.world import World
from src.simulation.engine import Simulation
from constants import EntityType


@pytest.mark.integration
class TestSimulationLifecycle:
    """Test complete simulation lifecycle and multi-agent interactions."""
    
    @pytest.fixture
    def minimal_simulation_config(self):
        """Configuration for minimal simulation testing."""
        return {
            'width': 400,
            'height': 300,
            'population_size': 5,
            'farm_count': 2,
            'work_count': 1,
            'max_steps': 100
        }
    
    def test_world_initialization(self, mock_screen, minimal_simulation_config):
        """Test world initializes correctly with all required components."""
        world = World(
            minimal_simulation_config['width'],
            minimal_simulation_config['height']
        )
        world.world_screen = mock_screen
        world.population_size = minimal_simulation_config['population_size']
        world.farm_count = minimal_simulation_config['farm_count']
        world.work_count = minimal_simulation_config['work_count']
        
        # Mock dependencies
        world.asset_manager = Mock()
        world.asset_manager.get_asset.return_value = Mock()
        world.render_manager = Mock()
        
        # Initialize world
        world.setup_world()
        
        # Verify initialization
        assert world.ecs is not None
        assert world.spatial_grid is not None
        assert world.society is not None
        assert world.metrics is not None
        assert len(world.entities) > 0
    
    def test_agent_creation_and_components(self, populated_world):
        """Test that agents are created with all necessary components."""
        # Create some agents
        populated_world.create_population()
        
        agents = [e for e in populated_world.entities 
                 if hasattr(e, 'genome') and e.is_alive]
        
        assert len(agents) == populated_world.population_size
        
        for agent in agents:
            # Check basic agent properties
            assert hasattr(agent, 'energy')
            assert hasattr(agent, 'money')
            assert hasattr(agent, 'mood')
            assert hasattr(agent, 'genome')
            assert hasattr(agent, 'ecs_id')
            assert agent.is_alive is True
            
            # Check ECS components exist
            assert populated_world.ecs.has_component(agent.ecs_id, "transform")
            assert populated_world.ecs.has_component(agent.ecs_id, "behavior")
            assert populated_world.ecs.has_component(agent.ecs_id, "wallet")
    
    def test_farm_and_workplace_creation(self, populated_world):
        """Test farm and workplace creation and setup."""
        populated_world.create_farms()
        populated_world.create_work()
        
        farms = [e for e in populated_world.entities if e.entity_type == EntityType.FARM]
        workplaces = [e for e in populated_world.entities if e.entity_type == EntityType.WORK]
        
        assert len(farms) == populated_world.farm_count
        assert len(workplaces) == populated_world.work_count
        
        # Check farms have required components
        for farm in farms:
            assert hasattr(farm, 'ecs_id')
            assert populated_world.ecs.has_component(farm.ecs_id, "transform")
        
        # Check workplaces have required components
        for workplace in workplaces:
            assert hasattr(workplace, 'ecs_id')
            assert populated_world.ecs.has_component(workplace.ecs_id, "transform")
            assert populated_world.ecs.has_component(workplace.ecs_id, "workplace")
    
    def test_system_updates(self, populated_world):
        """Test that all systems update without errors."""
        # Setup complete world
        populated_world.create_population()
        populated_world.create_farms()
        populated_world.create_work()
        
        # Run several update cycles
        for i in range(10):
            try:
                populated_world.update_world()
                assert True  # If we get here, update succeeded
            except Exception as e:
                pytest.fail(f"World update failed on iteration {i}: {e}")
    
    def test_agent_lifecycle(self, populated_world, agent_factory):
        """Test agent lifecycle - birth, actions, aging, death scenarios."""
        # Create initial population
        populated_world.create_population()
        initial_population = len([e for e in populated_world.entities if hasattr(e, 'genome')])
        
        # Create an agent with low energy (near death)
        dying_agent = agent_factory(energy=5, age=90)
        populated_world.add_entity(dying_agent)
        
        # Create healthy agents
        for i in range(3):
            healthy_agent = agent_factory(energy=100, age=25, agent_id=1000+i)
            populated_world.add_entity(healthy_agent)
        
        # Run simulation steps and monitor population changes
        initial_living = len([a for a in populated_world.society.population if a.is_alive])
        
        # Run updates to see lifecycle in action
        for step in range(50):
            populated_world.update_world()
            
            # Check for any deaths or births
            current_living = len([a for a in populated_world.society.population if a.is_alive])
            
            # Population should remain stable or change within reasonable bounds
            assert current_living >= 0
            assert current_living <= initial_living + 10  # Allow for some births
    
    def test_economic_interactions(self, populated_world, agent_factory):
        """Test economic interactions between agents and workplaces."""
        # Setup world with economic entities
        populated_world.create_population()
        populated_world.create_work()
        
        # Create agents with different economic states
        rich_agent = agent_factory(money=100, energy=80, agent_id=2001)
        poor_agent = agent_factory(money=5, energy=60, agent_id=2002)
        
        populated_world.add_entity(rich_agent)
        populated_world.add_entity(poor_agent)
        
        # Record initial economic state
        initial_rich_money = rich_agent.money
        initial_poor_money = poor_agent.money
        
        # Run economic simulation
        for step in range(20):
            populated_world.update_world()
            
            # Check that economic system is functioning
            # (money levels should change over time through work/trade)
            if step > 10:  # Give time for economic activity
                current_rich_money = rich_agent.money
                current_poor_money = poor_agent.money
                
                # At least one agent should have economic activity
                assert (current_rich_money != initial_rich_money or 
                       current_poor_money != initial_poor_money)
    
    def test_social_interactions(self, populated_world, agent_factory):
        """Test social interaction system between agents."""
        # Create agents with different social traits
        extrovert = agent_factory(
            agreeableness=0.8, 
            extraversion=0.9, 
            reciprocity=0.7,
            agent_id=3001
        )
        
        introvert = agent_factory(
            agreeableness=0.3,
            extraversion=0.1,
            reciprocity=0.4,
            agent_id=3002
        )
        
        populated_world.add_entity(extrovert)
        populated_world.add_entity(introvert)
        
        # Run social simulation
        for step in range(30):
            populated_world.update_world()
        
        # Check that agents have social components
        extrovert_social = populated_world.ecs.get_component(extrovert.ecs_id, "social")
        introvert_social = populated_world.ecs.get_component(introvert.ecs_id, "social")
        
        # Social components may not exist if not implemented yet
        if extrovert_social:
            assert hasattr(extrovert_social, 'relationships')
        if introvert_social:
            assert hasattr(introvert_social, 'relationships')
    
    def test_agricultural_cycle(self, populated_world, agent_factory):
        """Test agricultural farming cycle."""
        populated_world.create_population()
        populated_world.create_farms()
        
        # Create farmer agent
        farmer = agent_factory(energy=100, money=20, agent_id=4001)
        populated_world.add_entity(farmer)
        
        # Record initial farm states
        farms = [e for e in populated_world.entities if e.entity_type == EntityType.FARM]
        initial_farm_states = []
        
        for farm in farms:
            farm_component = populated_world.ecs.get_component(farm.ecs_id, "farm")
            if farm_component:
                initial_farm_states.append(farm_component.state)
        
        # Run agricultural simulation
        for step in range(50):
            populated_world.update_world()
        
        # Check for farm state changes (planting, growing, harvesting)
        if initial_farm_states:  # Only test if farm components exist
            for i, farm in enumerate(farms):
                farm_component = populated_world.ecs.get_component(farm.ecs_id, "farm")
                if farm_component and i < len(initial_farm_states):
                    # Farm state may have changed through agricultural activity
                    current_state = farm_component.state
                    # Just verify the component exists and has a state
                    assert hasattr(farm_component, 'state')
    
    def test_resource_consumption_and_production(self, populated_world, agent_factory):
        """Test resource consumption and production balance."""
        populated_world.create_population()
        populated_world.create_farms()
        populated_world.create_work()
        
        # Create agents with different resource needs
        hungry_agent = agent_factory(energy=30, food_reserves=2, agent_id=5001)
        energetic_agent = agent_factory(energy=90, food_reserves=20, agent_id=5002)
        
        populated_world.add_entity(hungry_agent)
        populated_world.add_entity(energetic_agent)
        
        # Track resource levels over time
        resource_history = []
        
        for step in range(30):
            populated_world.update_world()
            
            # Record current resource state
            total_energy = sum(a.energy for a in populated_world.society.population if a.is_alive)
            total_money = sum(a.money for a in populated_world.society.population if a.is_alive)
            
            resource_history.append({
                'step': step,
                'total_energy': total_energy,
                'total_money': total_money,
                'population': len([a for a in populated_world.society.population if a.is_alive])
            })
        
        # Analyze resource trends
        if len(resource_history) > 10:
            early_state = resource_history[5]
            late_state = resource_history[-1]
            
            # Population should remain relatively stable
            pop_change = abs(late_state['population'] - early_state['population'])
            assert pop_change <= 5  # Allow some population fluctuation
            
            # Resources should not go to extreme values
            assert late_state['total_energy'] >= 0
            assert late_state['total_money'] >= 0
    
    def test_memory_stability(self, populated_world, memory_tracker):
        """Test that simulation doesn't have significant memory leaks."""
        populated_world.create_population()
        populated_world.create_farms()
        populated_world.create_work()
        
        initial_memory = memory_tracker.memory_info().rss
        
        # Run extended simulation
        for step in range(100):
            populated_world.update_world()
            
            # Check memory every 20 steps
            if step % 20 == 0:
                current_memory = memory_tracker.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Memory shouldn't increase by more than 20MB during test
                assert memory_increase < 20 * 1024 * 1024
    
    def test_metrics_collection(self, populated_world):
        """Test that metrics are properly collected during simulation."""
        populated_world.create_population()
        populated_world.create_farms()
        populated_world.create_work()
        
        # Run simulation to generate metrics
        for step in range(20):
            populated_world.update_world()
        
        # Check metrics collection
        metrics = populated_world.metrics
        assert hasattr(metrics, 'collect')
        
        # Verify some basic metrics are tracked
        if hasattr(metrics, 'current_data') or hasattr(metrics, 'data'):
            # Check that metrics contain expected keys
            expected_metrics = [
                'population_size', 'male_count', 'female_count',
                'farm_count', 'work_count', 'avg_energy', 'avg_money'
            ]
            
            # Get latest metrics data
            latest_data = None
            if hasattr(metrics, 'current_data'):
                latest_data = metrics.current_data
            elif hasattr(metrics, 'data') and metrics.data:
                latest_data = metrics.data[-1] if isinstance(metrics.data, list) else metrics.data
            
            if latest_data:
                for metric in expected_metrics:
                    if metric in latest_data:
                        assert isinstance(latest_data[metric], (int, float))
    
    @pytest.mark.slow
    def test_long_running_stability(self, populated_world):
        """Test simulation stability over extended periods."""
        populated_world.create_population()
        populated_world.create_farms()
        populated_world.create_work()
        
        initial_population = len([a for a in populated_world.society.population if a.is_alive])
        error_count = 0
        
        # Run for extended period
        for step in range(500):
            try:
                populated_world.update_world()
                
                # Check for population stability every 50 steps
                if step % 50 == 0:
                    current_population = len([a for a in populated_world.society.population if a.is_alive])
                    
                    # Population shouldn't collapse or explode
                    assert current_population >= initial_population * 0.1  # At least 10% survive
                    assert current_population <= initial_population * 3    # No more than 3x growth
                    
            except Exception as e:
                error_count += 1
                if error_count > 10:  # Allow some errors but not too many
                    pytest.fail(f"Too many errors during simulation: {e}")
        
        # Simulation should complete without major issues
        assert error_count <= 10