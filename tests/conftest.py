"""
Pytest configuration and fixtures for Society simulation testing.
"""

import pytest
import sys
import os
import random
import numpy as np
from unittest.mock import Mock, MagicMock, patch
import pygame

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from constants import EntityType, ActionType, Gender
from src.core.ecs.core import ECS
from src.simulation.world.world import World
from src.simulation.entities.types.agent import Agent
from src.simulation.entities.types.farm import Farm
from src.simulation.entities.types.workplace import WorkPlace
from src.simulation.genetics.genome import Genome


@pytest.fixture(autouse=True)
def setup_random_seed():
    """Ensure reproducible randomness across tests."""
    random.seed(42)
    np.random.seed(42)


@pytest.fixture(scope="session", autouse=True)
def mock_pygame():
    """Mock pygame for headless testing."""
    with patch('pygame.init'):
        with patch('pygame.display.set_mode') as mock_display:
            mock_surface = Mock()
            mock_surface.get_size.return_value = (1600, 1200)
            mock_display.return_value = mock_surface
            
            with patch('pygame.display.set_caption'):
                with patch('pygame.time.Clock'):
                    with patch('pygame.event.get', return_value=[]):
                        with patch('pygame.display.flip'):
                            with patch('pygame.quit'):
                                yield mock_surface


@pytest.fixture
def mock_screen(mock_pygame):
    """Provide a mock pygame screen surface."""
    return mock_pygame


@pytest.fixture
def basic_ecs():
    """Create a basic ECS world for testing."""
    return ECS()


@pytest.fixture
def test_genome():
    """Create a test genome with known values."""
    genome = Genome(agent_id=1)
    # Set specific traits for predictable testing
    genome.agreeableness = 0.5
    genome.reciprocity = 0.5
    genome.extraversion = 0.5
    genome.learning_capacity = 0.01
    genome.gender = Gender.MALE
    return genome


@pytest.fixture
def test_agent(test_genome):
    """Create a test agent with known genome."""
    agent = Agent(
        position=(100, 100),
        size=(32, 32),
        entity_id=1,
        genome=test_genome,
        assets={}
    )
    agent.is_alive = True
    agent.energy = 100
    agent.money = 50
    agent.mood = 0.5
    agent.age = 25
    agent.corruption = 0.0
    agent.food_reserves = 10
    return agent


@pytest.fixture
def test_farm():
    """Create a test farm."""
    farm = Farm(
        position=(200, 200),
        size=(64, 64),
        assets={}
    )
    return farm


@pytest.fixture
def test_workplace():
    """Create a test workplace."""
    workplace = WorkPlace(
        position=(300, 300),
        size=(64, 64),
        assets={}
    )
    workplace.capacity = 5
    return workplace


@pytest.fixture
def test_world_config():
    """Configuration for test world."""
    return {
        'width': 800,
        'height': 600,
        'population_size': 10,
        'farm_count': 3,
        'work_count': 2
    }


@pytest.fixture
def minimal_world(mock_screen, test_world_config):
    """Create a minimal world for testing without full initialization."""
    world = World(test_world_config['width'], test_world_config['height'])
    world.world_screen = mock_screen
    world.population_size = test_world_config['population_size']
    world.farm_count = test_world_config['farm_count']
    world.work_count = test_world_config['work_count']
    
    # Mock asset manager
    world.asset_manager = Mock()
    world.asset_manager.get_asset.return_value = Mock()
    
    # Mock render manager
    world.render_manager = Mock()
    
    return world


@pytest.fixture
def populated_world(minimal_world):
    """Create a world with basic population for integration tests."""
    # Mock the entity factory for testing
    minimal_world.entity_factory = Mock()
    
    def create_test_entity(entity_type, position, screen, id=None):
        if entity_type in [EntityType.PERSON_MALE, EntityType.PERSON_FEMALE]:
            genome = Genome(agent_id=id or 0)
            agent = Agent(position, (32, 32), id or 0, genome, {})
            agent.ecs_id = id or 0
            return agent
        elif entity_type == EntityType.FARM:
            farm = Farm(position, (64, 64), {})
            farm.ecs_id = len(minimal_world.entities)
            return farm
        elif entity_type == EntityType.WORK:
            workplace = WorkPlace(position, (64, 64), {})
            workplace.ecs_id = len(minimal_world.entities)
            return workplace
        return Mock()
    
    minimal_world.entity_factory.create_entity.side_effect = create_test_entity
    
    # Setup basic ECS systems
    minimal_world.setup_systems()
    
    return minimal_world


@pytest.fixture
def agent_factory():
    """Factory function to create test agents with various configurations."""
    def create_agent(
        energy=100,
        money=50,
        mood=0.5,
        age=25,
        corruption=0.0,
        agreeableness=0.5,
        reciprocity=0.5,
        extraversion=0.5,
        gender=Gender.MALE,
        agent_id=None
    ):
        genome = Genome(agent_id=agent_id or random.randint(1, 10000))
        genome.agreeableness = agreeableness
        genome.reciprocity = reciprocity
        genome.extraversion = extraversion
        genome.gender = gender
        
        agent = Agent(
            position=(random.randint(0, 800), random.randint(0, 600)),
            size=(32, 32),
            entity_id=agent_id or genome.agent_id,
            genome=genome,
            assets={}
        )
        
        agent.is_alive = True
        agent.energy = energy
        agent.money = money
        agent.mood = mood
        agent.age = age
        agent.corruption = corruption
        agent.food_reserves = 10
        agent.ecs_id = agent.entity_id
        
        return agent
    
    return create_agent


@pytest.fixture
def memory_tracker():
    """Track memory usage during tests for leak detection."""
    import psutil
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    yield process
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Alert if memory increased significantly (more than 50MB)
    if memory_increase > 50 * 1024 * 1024:
        pytest.warning(f"Memory increased by {memory_increase / (1024*1024):.1f} MB during test")


@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    start_time = time.perf_counter()
    
    yield
    
    end_time = time.perf_counter()
    return end_time - start_time


class TestMetrics:
    """Helper class to collect test metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.warnings = []
    
    def record(self, key, value):
        self.metrics[key] = value
    
    def warn(self, message):
        self.warnings.append(message)
    
    def get_summary(self):
        return {
            'metrics': self.metrics,
            'warnings': self.warnings
        }


@pytest.fixture
def test_metrics():
    """Provide test metrics collection."""
    return TestMetrics()


# Custom markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.stress = pytest.mark.stress
pytest.mark.benchmark = pytest.mark.benchmark
pytest.mark.critical = pytest.mark.critical