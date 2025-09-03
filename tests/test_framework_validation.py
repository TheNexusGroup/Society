"""
Framework validation tests to ensure testing infrastructure works correctly
"""

import pytest
import sys
import os


def test_framework_setup():
    """Test that the testing framework is properly set up."""
    # Check that we can import main modules
    try:
        import constants
        assert hasattr(constants, 'EntityType')
        assert hasattr(constants, 'ActionType')
    except ImportError as e:
        pytest.fail(f"Cannot import constants module: {e}")
    
    # Check pytest configuration
    assert pytest is not None
    
    # Check that test directory structure exists
    test_dir = os.path.dirname(__file__)
    assert os.path.exists(os.path.join(test_dir, 'unit'))
    assert os.path.exists(os.path.join(test_dir, 'integration'))
    assert os.path.exists(os.path.join(test_dir, 'stress'))
    assert os.path.exists(os.path.join(test_dir, 'benchmarks'))


def test_fixtures_available():
    """Test that test fixtures are available."""
    from tests.conftest import (
        mock_pygame, basic_ecs, test_genome, test_agent,
        test_farm, test_workplace, agent_factory
    )
    
    # Just check that fixtures can be imported
    assert mock_pygame is not None
    assert basic_ecs is not None
    assert test_genome is not None
    assert test_agent is not None
    assert test_farm is not None
    assert test_workplace is not None
    assert agent_factory is not None


def test_data_factories_available():
    """Test that data factories work correctly."""
    try:
        from tests.fixtures.data_factories import (
            GenomeFactory, AgentFactory, create_test_scenario
        )
        
        # Test factory creation
        genome = GenomeFactory()
        assert hasattr(genome, 'agreeableness')
        assert hasattr(genome, 'learning_capacity')
        
        # Test scenario creation
        scenario = create_test_scenario('balanced')
        assert 'agents' in scenario
        assert 'farms' in scenario or 'workplaces' in scenario
        
    except Exception as e:
        pytest.fail(f"Data factories not working: {e}")


@pytest.mark.benchmark
def test_benchmark_capability(benchmark):
    """Test that benchmarking framework works."""
    def simple_operation():
        return sum(range(100))
    
    result = benchmark(simple_operation)
    assert result == sum(range(100))


def test_memory_tracking():
    """Test memory tracking capabilities."""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        assert memory_info.rss > 0
    except ImportError:
        pytest.skip("psutil not available for memory tracking")


def test_mock_pygame():
    """Test pygame mocking works correctly."""
    import pygame
    # Should not raise errors in headless environment
    pygame.init()
    pygame.display.set_mode((100, 100))
    pygame.quit()


@pytest.mark.unit
def test_unit_test_marker():
    """Test unit test marker works."""
    assert True


@pytest.mark.integration  
def test_integration_test_marker():
    """Test integration test marker works."""
    assert True


@pytest.mark.stress
def test_stress_test_marker():
    """Test stress test marker works."""
    assert True


@pytest.mark.critical
def test_critical_test_marker():
    """Test critical test marker works."""
    assert True


def test_python_version_compatibility():
    """Test Python version compatibility."""
    # Ensure we're running on supported Python version
    assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"
    
    # Test f-string support (Python 3.6+)
    name = "test"
    formatted = f"Hello {name}"
    assert formatted == "Hello test"
    
    # Test type hints work
    def typed_function(x: int) -> int:
        return x * 2
    
    assert typed_function(5) == 10


def test_imports_work():
    """Test that key simulation modules can be imported."""
    try:
        from src.simulation.world.world import World
        from src.core.ecs.core import ECS
        from src.simulation.genetics.genome import Genome
        
        # Basic instantiation test
        ecs = ECS()
        genome = Genome(agent_id=1)
        
        assert ecs is not None
        assert genome is not None
        assert genome.agent_id == 1
        
    except ImportError as e:
        pytest.fail(f"Cannot import core simulation modules: {e}")


if __name__ == '__main__':
    # Quick validation run
    pytest.main([__file__, '-v'])