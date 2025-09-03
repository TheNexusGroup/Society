"""
Performance benchmarks for Society simulation
"""

import pytest
import time
import psutil
from unittest.mock import Mock
from src.simulation.world.world import World
from src.simulation.agent.logic.brain import AgentBrain


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Benchmark critical simulation performance."""
    
    def test_world_creation_benchmark(self, benchmark, mock_screen):
        """Benchmark world creation time."""
        def create_world():
            world = World(800, 600)
            world.world_screen = mock_screen
            world.population_size = 50
            world.farm_count = 10
            world.work_count = 5
            
            # Mock dependencies
            world.asset_manager = Mock()
            world.asset_manager.get_asset.return_value = Mock()
            world.render_manager = Mock()
            
            world.setup_world()
            return world
        
        result = benchmark(create_world)
        
        # Verify world was created properly
        assert result is not None
        assert len(result.entities) > 0
        assert hasattr(result, 'ecs')
        assert hasattr(result, 'spatial_grid')
    
    def test_single_update_benchmark(self, benchmark, populated_world):
        """Benchmark single world update performance."""
        populated_world.create_population()
        populated_world.create_farms()
        populated_world.create_work()
        
        # Warmup
        for _ in range(5):
            populated_world.update_world()
        
        def single_update():
            populated_world.update_world()
        
        result = benchmark(single_update)
        
        # Should complete update cycle
        assert result is None  # update_world returns None
    
    def test_agent_decision_benchmark(self, benchmark, test_genome, mock_world):
        """Benchmark agent decision making performance."""
        brain = AgentBrain(
            agent_id=1,
            genome=test_genome,
            world=mock_world,
            memory_capacity=1000
        )
        
        state_dict = {
            'energy': 'medium',
            'money': 'low',
            'mood': 'neutral',
            'corruption': 'low',
            'food_reserves': 'medium',
            'social_reputation': 'neutral',
            'has_enemies': 'none'
        }
        
        def make_decision():
            return brain.select_action(state_dict, exploration_rate=0.1)
        
        result = benchmark(make_decision)
        
        # Should return valid action
        assert isinstance(result, str)
        assert result in brain.action_map.values()
    
    def test_spatial_query_benchmark(self, benchmark, populated_world):
        """Benchmark spatial grid query performance."""
        populated_world.create_population()
        
        def spatial_query():
            # Query center of world
            x, y = populated_world.width // 2, populated_world.height // 2
            return populated_world.spatial_grid.query_range(x, y, 100, 100)
        
        result = benchmark(spatial_query)
        
        # Should return some results
        assert isinstance(result, (list, set))
    
    def test_ecs_component_access_benchmark(self, benchmark, populated_world):
        """Benchmark ECS component access performance."""
        populated_world.create_population()
        
        # Get some entity IDs
        agents = [e for e in populated_world.entities if hasattr(e, 'genome')][:10]
        entity_ids = [agent.ecs_id for agent in agents if hasattr(agent, 'ecs_id')]
        
        if not entity_ids:
            pytest.skip("No entities with ECS IDs found")
        
        def access_components():
            results = []
            for entity_id in entity_ids:
                transform = populated_world.ecs.get_component(entity_id, "transform")
                behavior = populated_world.ecs.get_component(entity_id, "behavior")
                results.append((transform, behavior))
            return results
        
        result = benchmark(access_components)
        
        # Should return component data
        assert isinstance(result, list)
        assert len(result) == len(entity_ids)
    
    def test_memory_usage_benchmark(self, mock_screen):
        """Benchmark memory usage for different population sizes."""
        process = psutil.Process()
        
        memory_results = {}
        population_sizes = [10, 25, 50, 100]
        
        for pop_size in population_sizes:
            # Create world
            world = World(800, 600)
            world.world_screen = mock_screen
            world.population_size = pop_size
            world.farm_count = pop_size // 4
            world.work_count = pop_size // 8
            
            # Mock dependencies
            world.asset_manager = Mock()
            world.asset_manager.get_asset.return_value = Mock()
            world.render_manager = Mock()
            
            # Measure memory before
            memory_before = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Setup world
            world.setup_world()
            
            # Measure memory after
            memory_after = process.memory_info().rss / (1024 * 1024)  # MB
            memory_used = memory_after - memory_before
            
            memory_results[pop_size] = {
                'memory_mb': memory_used,
                'memory_per_agent': memory_used / pop_size if pop_size > 0 else 0
            }
            
            # Clean up
            del world
        
        # Analyze memory scaling
        for pop_size, data in memory_results.items():
            memory_per_agent = data['memory_per_agent']
            
            # Memory per agent should be reasonable (< 5MB per agent)
            assert memory_per_agent < 5.0, \
                f"Memory per agent too high: {memory_per_agent:.2f}MB for pop {pop_size}"
            
            print(f"Population {pop_size}: {data['memory_mb']:.1f}MB total, "
                  f"{memory_per_agent:.2f}MB per agent")
    
    def test_fps_capability_benchmark(self, mock_screen):
        """Benchmark maximum sustainable FPS."""
        world = World(1200, 900)
        world.world_screen = mock_screen
        world.population_size = 100
        world.farm_count = 20
        world.work_count = 10
        
        # Mock dependencies
        world.asset_manager = Mock()
        world.asset_manager.get_asset.return_value = Mock()
        world.render_manager = Mock()
        
        world.setup_world()
        
        # Warmup
        for _ in range(10):
            world.update_world()
        
        # Measure update times
        update_times = []
        test_iterations = 50
        
        for _ in range(test_iterations):
            start_time = time.perf_counter()
            world.update_world()
            end_time = time.perf_counter()
            
            update_times.append(end_time - start_time)
        
        # Calculate FPS metrics
        avg_update_time = sum(update_times) / len(update_times)
        min_update_time = min(update_times)
        max_update_time = max(update_times)
        
        avg_fps = 1.0 / avg_update_time
        max_fps = 1.0 / min_update_time
        min_fps = 1.0 / max_update_time
        
        # Performance assertions
        assert avg_fps >= 30, f"Average FPS too low: {avg_fps:.1f}"
        assert min_fps >= 15, f"Minimum FPS too low: {min_fps:.1f}"
        
        print(f"FPS Capability - Avg: {avg_fps:.1f}, Min: {min_fps:.1f}, Max: {max_fps:.1f}")
        print(f"Update Times - Avg: {avg_update_time*1000:.2f}ms, "
              f"Min: {min_update_time*1000:.2f}ms, Max: {max_update_time*1000:.2f}ms")
    
    def test_system_scaling_benchmark(self, mock_screen):
        """Benchmark how performance scales with number of systems."""
        base_world = World(600, 600)
        base_world.world_screen = mock_screen
        base_world.population_size = 30
        base_world.farm_count = 6
        base_world.work_count = 3
        
        # Mock dependencies
        base_world.asset_manager = Mock()
        base_world.asset_manager.get_asset.return_value = Mock()
        base_world.render_manager = Mock()
        
        base_world.setup_world()
        
        # Count active systems
        system_count = len(base_world.ecs.systems) if hasattr(base_world.ecs, 'systems') else 0
        
        # Benchmark with all systems
        update_times = []
        for _ in range(20):
            start_time = time.perf_counter()
            base_world.update_world()
            end_time = time.perf_counter()
            update_times.append(end_time - start_time)
        
        avg_update_time = sum(update_times) / len(update_times)
        time_per_system = avg_update_time / max(1, system_count)
        
        # Systems should not be excessively slow
        assert time_per_system < 0.01, f"Time per system too high: {time_per_system*1000:.2f}ms"
        
        print(f"System Scaling - {system_count} systems, {time_per_system*1000:.3f}ms per system")
    
    def test_memory_allocation_benchmark(self, benchmark):
        """Benchmark object allocation patterns."""
        from src.simulation.genetics.genome import Genome
        from src.simulation.entities.types.agent import Agent
        
        def allocate_objects():
            objects = []
            
            # Create genomes
            for i in range(10):
                genome = Genome(agent_id=i)
                objects.append(genome)
            
            # Create agents (if possible without dependencies)
            try:
                for i in range(5):
                    agent = Agent(
                        position=(i*10, i*10),
                        size=(32, 32),
                        entity_id=i,
                        genome=objects[i],
                        assets={}
                    )
                    objects.append(agent)
            except:
                pass  # Skip if agent creation requires more dependencies
            
            return objects
        
        result = benchmark(allocate_objects)
        
        # Should create objects successfully
        assert len(result) > 0
    
    @pytest.mark.slow
    def test_long_term_performance_benchmark(self, mock_screen):
        """Benchmark performance degradation over extended simulation."""
        world = World(800, 600)
        world.world_screen = mock_screen
        world.population_size = 50
        world.farm_count = 10
        world.work_count = 5
        
        # Mock dependencies
        world.asset_manager = Mock()
        world.asset_manager.get_asset.return_value = Mock()
        world.render_manager = Mock()
        
        world.setup_world()
        
        # Measure performance at different intervals
        performance_samples = []
        sample_intervals = [0, 100, 200, 500, 1000]
        
        step = 0
        for target_step in sample_intervals:
            # Run simulation to target step
            while step < target_step:
                world.update_world()
                step += 1
            
            # Sample performance
            if step > 0:
                sample_times = []
                for _ in range(10):
                    start_time = time.perf_counter()
                    world.update_world()
                    end_time = time.perf_counter()
                    sample_times.append(end_time - start_time)
                    step += 1
                
                avg_time = sum(sample_times) / len(sample_times)
                performance_samples.append((step, avg_time))
        
        # Check for performance degradation
        if len(performance_samples) >= 2:
            initial_time = performance_samples[0][1]
            final_time = performance_samples[-1][1]
            
            performance_ratio = final_time / initial_time
            
            # Performance shouldn't degrade by more than 50%
            assert performance_ratio < 1.5, \
                f"Performance degraded by {(performance_ratio-1)*100:.1f}%"
            
            print(f"Long-term Performance - Initial: {initial_time*1000:.2f}ms, "
                  f"Final: {final_time*1000:.2f}ms, Ratio: {performance_ratio:.2f}")
    
    def test_concurrent_agent_benchmark(self, benchmark, populated_world):
        """Benchmark concurrent agent processing."""
        populated_world.create_population()
        
        agents = [e for e in populated_world.entities if hasattr(e, 'genome')][:20]
        
        def process_agents_concurrently():
            results = []
            for agent in agents:
                # Simulate agent processing
                if hasattr(agent, 'brain') and agent.brain:
                    state_dict = {
                        'energy': 'medium',
                        'money': 'low',
                        'mood': 'neutral',
                        'corruption': 'low'
                    }
                    action = agent.brain.select_action(state_dict)
                    results.append(action)
                else:
                    results.append('idle')
            return results
        
        result = benchmark(process_agents_concurrently)
        
        # Should process all agents
        assert len(result) == len(agents)