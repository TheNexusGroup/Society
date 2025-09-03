"""
Stress tests for population scaling and performance
"""

import pytest
import time
import psutil
import gc
from unittest.mock import Mock
from src.simulation.world.world import World


@pytest.mark.stress
class TestPopulationScaling:
    """Test simulation performance under different population loads."""
    
    @pytest.fixture(params=[10, 50, 100])
    def population_size(self, request):
        """Parametrized population sizes for scaling tests."""
        return request.param
    
    @pytest.fixture
    def stress_world_config(self, population_size):
        """Configuration for stress testing different population sizes."""
        return {
            'width': 1600,
            'height': 1200,
            'population_size': population_size,
            'farm_count': max(3, population_size // 4),
            'work_count': max(2, population_size // 8),
            'test_duration_steps': 100
        }
    
    def setup_stress_world(self, config, mock_screen):
        """Set up world for stress testing."""
        world = World(config['width'], config['height'])
        world.world_screen = mock_screen
        world.population_size = config['population_size']
        world.farm_count = config['farm_count']
        world.work_count = config['work_count']
        
        # Mock dependencies for headless testing
        world.asset_manager = Mock()
        world.asset_manager.get_asset.return_value = Mock()
        world.render_manager = Mock()
        
        return world
    
    def test_population_creation_performance(self, mock_screen, stress_world_config):
        """Test performance of creating different population sizes."""
        world = self.setup_stress_world(stress_world_config, mock_screen)
        
        start_time = time.perf_counter()
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Setup world and create population
        world.setup_world()
        
        end_time = time.perf_counter()
        final_memory = process.memory_info().rss
        
        creation_time = end_time - start_time
        memory_used = (final_memory - initial_memory) / (1024 * 1024)  # MB
        
        population_size = stress_world_config['population_size']
        
        # Performance assertions
        assert creation_time < 10.0, f"Creation took {creation_time:.2f}s for {population_size} agents"
        assert memory_used < 500, f"Used {memory_used:.1f}MB for {population_size} agents"
        
        # Verify population was created
        agents = [e for e in world.entities if hasattr(e, 'genome')]
        assert len(agents) == population_size
        
        print(f"Population {population_size}: {creation_time:.3f}s, {memory_used:.1f}MB")
    
    def test_update_performance_scaling(self, mock_screen, stress_world_config):
        """Test update performance with different population sizes."""
        world = self.setup_stress_world(stress_world_config, mock_screen)
        world.setup_world()
        
        population_size = stress_world_config['population_size']
        test_steps = min(50, stress_world_config['test_duration_steps'])
        
        # Warmup
        for _ in range(5):
            world.update_world()
        
        # Performance measurement
        start_time = time.perf_counter()
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        for step in range(test_steps):
            world.update_world()
        
        end_time = time.perf_counter()
        final_memory = process.memory_info().rss
        
        total_time = end_time - start_time
        avg_step_time = total_time / test_steps
        memory_delta = (final_memory - initial_memory) / (1024 * 1024)  # MB
        
        # Performance thresholds based on population
        if population_size <= 10:
            max_step_time = 0.05  # 50ms per step for small populations
        elif population_size <= 50:
            max_step_time = 0.1   # 100ms per step for medium populations  
        else:
            max_step_time = 0.2   # 200ms per step for large populations
        
        assert avg_step_time < max_step_time, \
            f"Avg step time {avg_step_time:.4f}s too slow for {population_size} agents"
        
        # Memory should not grow significantly during updates
        assert abs(memory_delta) < 100, \
            f"Memory changed by {memory_delta:.1f}MB during updates"
        
        print(f"Population {population_size}: {avg_step_time:.4f}s/step, Δ{memory_delta:.1f}MB")
    
    def test_memory_stability_over_time(self, mock_screen, stress_world_config):
        """Test memory stability during extended simulation runs."""
        world = self.setup_stress_world(stress_world_config, mock_screen)
        world.setup_world()
        
        process = psutil.Process()
        memory_samples = []
        
        # Run simulation and sample memory usage
        sample_interval = 20
        total_steps = 200
        
        for step in range(total_steps):
            world.update_world()
            
            if step % sample_interval == 0:
                memory_mb = process.memory_info().rss / (1024 * 1024)
                memory_samples.append((step, memory_mb))
        
        # Analyze memory trend
        if len(memory_samples) >= 3:
            initial_memory = memory_samples[0][1]
            final_memory = memory_samples[-1][1]
            memory_growth = final_memory - initial_memory
            
            # Calculate memory growth rate
            steps_elapsed = memory_samples[-1][0] - memory_samples[0][0]
            growth_rate = memory_growth / (steps_elapsed / 100)  # MB per 100 steps
            
            population_size = stress_world_config['population_size']
            
            # Memory should not grow excessively
            max_growth = 50 + (population_size * 0.1)  # Allow more growth for larger populations
            assert memory_growth < max_growth, \
                f"Memory grew by {memory_growth:.1f}MB (rate: {growth_rate:.3f}MB/100steps)"
            
            print(f"Population {population_size}: Memory growth {memory_growth:.1f}MB over {steps_elapsed} steps")
    
    @pytest.mark.slow
    def test_large_population_stress(self, mock_screen):
        """Stress test with very large population."""
        large_config = {
            'width': 2000,
            'height': 1500,
            'population_size': 500,
            'farm_count': 100,
            'work_count': 50,
            'test_duration_steps': 50
        }
        
        world = self.setup_stress_world(large_config, mock_screen)
        
        # Test creation under stress
        start_time = time.perf_counter()
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        try:
            world.setup_world()
            creation_time = time.perf_counter() - start_time
            
            # Verify large population was created
            agents = [e for e in world.entities if hasattr(e, 'genome')]
            assert len(agents) == 500
            
            # Run some updates
            update_start = time.perf_counter()
            for step in range(20):
                world.update_world()
                
                # Check memory doesn't explode
                current_memory = process.memory_info().rss / (1024 * 1024)
                if current_memory > 2000:  # 2GB limit
                    pytest.fail(f"Memory usage exceeded 2GB: {current_memory:.0f}MB")
            
            update_time = time.perf_counter() - update_start
            avg_update_time = update_time / 20
            
            # Performance should still be reasonable
            assert creation_time < 30.0, f"Large population creation took {creation_time:.1f}s"
            assert avg_update_time < 0.5, f"Large population updates too slow: {avg_update_time:.3f}s"
            
            print(f"Large population (500): Created in {creation_time:.1f}s, {avg_update_time:.3f}s/update")
            
        except MemoryError:
            pytest.skip("System doesn't have enough memory for large population test")
    
    def test_population_death_and_cleanup(self, mock_screen, agent_factory):
        """Test memory cleanup when agents die."""
        config = {
            'width': 800,
            'height': 600,
            'population_size': 50,
            'farm_count': 5,
            'work_count': 3
        }
        
        world = self.setup_stress_world(config, mock_screen)
        world.setup_world()
        
        # Add agents with very low energy (will die quickly)
        dying_agents = []
        for i in range(20):
            dying_agent = agent_factory(energy=1, age=95, agent_id=9000+i)
            world.add_entity(dying_agent)
            dying_agents.append(dying_agent)
        
        initial_entities = len(world.entities)
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Run simulation to trigger deaths
        for step in range(100):
            world.update_world()
            
            # Force garbage collection occasionally
            if step % 20 == 0:
                gc.collect()
        
        final_entities = len([e for e in world.entities if getattr(e, 'is_alive', True)])
        final_memory = process.memory_info().rss
        memory_delta = (final_memory - initial_memory) / (1024 * 1024)
        
        # Should have fewer living entities after deaths
        living_agents = len([a for a in world.society.population if a.is_alive])
        assert living_agents < initial_entities
        
        # Memory should not grow significantly even with deaths
        assert abs(memory_delta) < 100, f"Memory changed by {memory_delta:.1f}MB after deaths"
        
        print(f"After deaths: {living_agents} living agents, Δ{memory_delta:.1f}MB memory")
    
    def test_concurrent_system_updates(self, mock_screen, stress_world_config):
        """Test performance when all systems update simultaneously."""
        world = self.setup_stress_world(stress_world_config, mock_screen)
        world.setup_world()
        
        population_size = stress_world_config['population_size']
        
        # Count active systems
        active_systems = len(world.ecs.systems) if hasattr(world.ecs, 'systems') else 0
        
        # Time system updates
        start_time = time.perf_counter()
        
        for step in range(30):
            world.update_world()
        
        total_time = time.perf_counter() - start_time
        avg_time = total_time / 30
        
        # Performance should scale reasonably with systems and population
        max_time_per_step = 0.01 + (population_size * 0.001) + (active_systems * 0.01)
        
        assert avg_time < max_time_per_step, \
            f"System updates too slow: {avg_time:.4f}s with {active_systems} systems and {population_size} agents"
        
        print(f"Population {population_size}, {active_systems} systems: {avg_time:.4f}s/step")
    
    def test_resource_contention_stress(self, mock_screen):
        """Test simulation under resource scarcity stress."""
        # Create world with many agents but few resources
        scarcity_config = {
            'width': 1000,
            'height': 800,
            'population_size': 100,
            'farm_count': 5,   # Very few farms for population
            'work_count': 3    # Very few workplaces
        }
        
        world = self.setup_stress_world(scarcity_config, mock_screen)
        world.setup_world()
        
        initial_population = len([a for a in world.society.population if a.is_alive])
        
        # Run under scarcity conditions
        for step in range(200):
            world.update_world()
            
            # Check for simulation stability
            current_population = len([a for a in world.society.population if a.is_alive])
            
            # Population may decline under scarcity but shouldn't crash to zero immediately
            if step > 50 and current_population == 0:
                pytest.fail("Entire population died too quickly under resource scarcity")
            
            # Simulation should continue running even under stress
            assert current_population >= 0
        
        final_population = len([a for a in world.society.population if a.is_alive])
        
        # Some population decline is expected under scarcity
        assert final_population <= initial_population
        
        print(f"Scarcity test: {initial_population} → {final_population} population")
    
    @pytest.mark.benchmark
    def test_fps_target_benchmark(self, mock_screen, benchmark):
        """Benchmark simulation to maintain target FPS."""
        config = {
            'width': 1200,
            'height': 900,
            'population_size': 50,
            'farm_count': 12,
            'work_count': 6
        }
        
        world = self.setup_stress_world(config, mock_screen)
        world.setup_world()
        
        def single_update():
            world.update_world()
        
        # Benchmark single update
        result = benchmark(single_update)
        
        # Should be able to maintain at least 30 FPS (33.33ms per frame)
        target_fps = 30
        max_frame_time = 1.0 / target_fps
        
        assert result < max_frame_time, \
            f"Update time {result:.4f}s too slow for {target_fps} FPS target"
        
        actual_fps = 1.0 / result
        print(f"Benchmark: {actual_fps:.1f} FPS potential with {config['population_size']} agents")