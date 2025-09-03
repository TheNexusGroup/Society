"""
Data factories for consistent test data generation
"""

import random
import factory
from factory import Faker
from constants import EntityType, ActionType, Gender
from src.simulation.genetics.genome import Genome
from src.simulation.entities.types.agent import Agent
from src.simulation.entities.types.farm import Farm
from src.simulation.entities.types.workplace import WorkPlace


class GenomeFactory(factory.Factory):
    """Factory for creating test genomes."""
    
    class Meta:
        model = Genome
    
    agent_id = factory.Sequence(lambda n: n)
    agreeableness = factory.Faker('pyfloat', min_value=0.0, max_value=1.0)
    reciprocity = factory.Faker('pyfloat', min_value=0.0, max_value=1.0)
    extraversion = factory.Faker('pyfloat', min_value=0.0, max_value=1.0)
    learning_capacity = factory.Faker('pyfloat', min_value=0.001, max_value=0.1)
    corruption_resistance = factory.Faker('pyfloat', min_value=0.0, max_value=1.0)
    
    @factory.LazyAttribute
    def gender(self):
        return random.choice([Gender.MALE, Gender.FEMALE])
    
    @factory.post_generation
    def setup_q_table(self, create, extracted, **kwargs):
        """Initialize Q-table after creation."""
        if not create:
            return
        self.q_table = {}


class AgentFactory(factory.Factory):
    """Factory for creating test agents."""
    
    class Meta:
        model = Agent
    
    entity_id = factory.Sequence(lambda n: n)
    genome = factory.SubFactory(GenomeFactory)
    assets = factory.LazyFunction(dict)
    
    @factory.LazyAttribute
    def position(self):
        return (random.randint(0, 800), random.randint(0, 600))
    
    @factory.LazyAttribute
    def size(self):
        return (32, 32)
    
    @factory.post_generation
    def setup_agent_properties(self, create, extracted, **kwargs):
        """Set up agent properties after creation."""
        if not create:
            return
        
        # Set default properties
        self.is_alive = True
        self.energy = kwargs.get('energy', random.randint(50, 100))
        self.money = kwargs.get('money', random.randint(10, 100))
        self.mood = kwargs.get('mood', random.uniform(-0.5, 0.5))
        self.age = kwargs.get('age', random.randint(18, 60))
        self.corruption = kwargs.get('corruption', random.uniform(0, 0.3))
        self.food_reserves = kwargs.get('food_reserves', random.randint(5, 20))
        self.current_action = kwargs.get('current_action', 'idle')
        
        # Set corruption_level for compatibility
        self.corruption_level = self.corruption


class FarmFactory(factory.Factory):
    """Factory for creating test farms."""
    
    class Meta:
        model = Farm
    
    assets = factory.LazyFunction(dict)
    
    @factory.LazyAttribute
    def position(self):
        return (random.randint(0, 800), random.randint(0, 600))
    
    @factory.LazyAttribute
    def size(self):
        return (64, 64)
    
    @factory.post_generation
    def setup_farm_properties(self, create, extracted, **kwargs):
        """Set up farm properties after creation."""
        if not create:
            return
        
        self.entity_type = EntityType.FARM
        self.yield_amount = kwargs.get('yield_amount', random.randint(5, 15))
        self.growth_time = kwargs.get('growth_time', random.randint(50, 100))


class WorkPlaceFactory(factory.Factory):
    """Factory for creating test workplaces."""
    
    class Meta:
        model = WorkPlace
    
    assets = factory.LazyFunction(dict)
    
    @factory.LazyAttribute
    def position(self):
        return (random.randint(0, 800), random.randint(0, 600))
    
    @factory.LazyAttribute
    def size(self):
        return (64, 64)
    
    @factory.post_generation
    def setup_workplace_properties(self, create, extracted, **kwargs):
        """Set up workplace properties after creation."""
        if not create:
            return
        
        self.entity_type = EntityType.WORK
        self.capacity = kwargs.get('capacity', random.randint(3, 10))
        self.wage_rate = kwargs.get('wage_rate', random.uniform(1.0, 5.0))
        self.productivity = kwargs.get('productivity', random.uniform(0.5, 1.5))


class ScenarioDataFactory:
    """Factory for creating specific test scenarios."""
    
    @staticmethod
    def create_economic_crisis_scenario():
        """Create scenario with economic stress."""
        poor_agents = AgentFactory.create_batch(
            10,
            energy=30,
            money=5,
            mood=-0.3,
            corruption=0.1
        )
        
        few_workplaces = WorkPlaceFactory.create_batch(2, capacity=3)
        limited_farms = FarmFactory.create_batch(2, yield_amount=3)
        
        return {
            'agents': poor_agents,
            'workplaces': few_workplaces,
            'farms': limited_farms,
            'description': 'Economic crisis with high unemployment and food scarcity'
        }
    
    @staticmethod
    def create_population_boom_scenario():
        """Create scenario with rapid population growth."""
        young_agents = AgentFactory.create_batch(
            50,
            age=20,
            energy=80,
            money=30,
            mood=0.2
        )
        
        abundant_resources = {
            'farms': FarmFactory.create_batch(15, yield_amount=12),
            'workplaces': WorkPlaceFactory.create_batch(10, capacity=8)
        }
        
        return {
            'agents': young_agents,
            'farms': abundant_resources['farms'],
            'workplaces': abundant_resources['workplaces'],
            'description': 'Population boom with abundant resources'
        }
    
    @staticmethod
    def create_social_conflict_scenario():
        """Create scenario with high social tension."""
        corrupt_agents = AgentFactory.create_batch(
            5,
            corruption=0.8,
            agreeableness=0.1,
            reciprocity=0.2,
            money=100
        )
        
        honest_agents = AgentFactory.create_batch(
            15,
            corruption=0.0,
            agreeableness=0.8,
            reciprocity=0.9,
            money=20
        )
        
        all_agents = corrupt_agents + honest_agents
        
        return {
            'agents': all_agents,
            'farms': FarmFactory.create_batch(5),
            'workplaces': WorkPlaceFactory.create_batch(3),
            'description': 'Social conflict between corrupt and honest agents'
        }
    
    @staticmethod
    def create_resource_abundance_scenario():
        """Create scenario with abundant resources."""
        agents = AgentFactory.create_batch(20, energy=70, money=50)
        
        many_farms = FarmFactory.create_batch(20, yield_amount=15)
        many_workplaces = WorkPlaceFactory.create_batch(15, capacity=10)
        
        return {
            'agents': agents,
            'farms': many_farms,
            'workplaces': many_workplaces,
            'description': 'Resource abundance scenario'
        }
    
    @staticmethod
    def create_aging_population_scenario():
        """Create scenario with aging population."""
        elderly_agents = AgentFactory.create_batch(
            30,
            age=70,
            energy=40,
            money=80
        )
        
        few_young = AgentFactory.create_batch(
            5,
            age=25,
            energy=90,
            money=20
        )
        
        all_agents = elderly_agents + few_young
        
        return {
            'agents': all_agents,
            'farms': FarmFactory.create_batch(8),
            'workplaces': WorkPlaceFactory.create_batch(4),
            'description': 'Aging population with few young workers'
        }


class TestDataBuilder:
    """Builder pattern for creating complex test data."""
    
    def __init__(self):
        self.agents = []
        self.farms = []
        self.workplaces = []
        self.world_config = {
            'width': 800,
            'height': 600,
            'population_size': 0,
            'farm_count': 0,
            'work_count': 0
        }
    
    def add_agents(self, count, **kwargs):
        """Add agents to the test data."""
        new_agents = AgentFactory.create_batch(count, **kwargs)
        self.agents.extend(new_agents)
        self.world_config['population_size'] += count
        return self
    
    def add_farms(self, count, **kwargs):
        """Add farms to the test data."""
        new_farms = FarmFactory.create_batch(count, **kwargs)
        self.farms.extend(new_farms)
        self.world_config['farm_count'] += count
        return self
    
    def add_workplaces(self, count, **kwargs):
        """Add workplaces to the test data."""
        new_workplaces = WorkPlaceFactory.create_batch(count, **kwargs)
        self.workplaces.extend(new_workplaces)
        self.world_config['work_count'] += count
        return self
    
    def with_world_size(self, width, height):
        """Set world dimensions."""
        self.world_config['width'] = width
        self.world_config['height'] = height
        return self
    
    def build(self):
        """Build the final test data structure."""
        return {
            'agents': self.agents,
            'farms': self.farms,
            'workplaces': self.workplaces,
            'world_config': self.world_config.copy()
        }
    
    def build_balanced(self):
        """Build a balanced scenario."""
        agent_count = len(self.agents)
        if agent_count == 0:
            agent_count = 20
            self.add_agents(agent_count)
        
        # Add balanced resources if none specified
        if not self.farms:
            self.add_farms(max(3, agent_count // 4))
        
        if not self.workplaces:
            self.add_workplaces(max(2, agent_count // 6))
        
        return self.build()


class StateDataFactory:
    """Factory for creating specific game states."""
    
    @staticmethod
    def create_initial_state():
        """Create a typical initial game state."""
        return TestDataBuilder().add_agents(
            25,
            energy=75,
            money=25,
            age=30,
            corruption=0.1
        ).add_farms(6, yield_amount=8).add_workplaces(4, capacity=6).build_balanced()
    
    @staticmethod
    def create_mid_game_state():
        """Create a mid-game state with established relationships."""
        return TestDataBuilder().add_agents(
            40,
            energy=60,
            money=45,
            age=40,
            corruption=0.2
        ).add_farms(10, yield_amount=10).add_workplaces(8, capacity=5).build_balanced()
    
    @staticmethod
    def create_end_game_state():
        """Create an end-game state with complex dynamics."""
        return TestDataBuilder().add_agents(
            60,
            energy=50,
            money=60,
            age=50,
            corruption=0.3
        ).add_farms(15, yield_amount=6).add_workplaces(12, capacity=4).build_balanced()


# Convenience functions for easy factory usage
def create_test_agent(**kwargs):
    """Create a single test agent with custom properties."""
    return AgentFactory(**kwargs)


def create_test_agents(count, **kwargs):
    """Create multiple test agents with custom properties."""
    return AgentFactory.create_batch(count, **kwargs)


def create_test_scenario(scenario_name='balanced'):
    """Create a predefined test scenario."""
    scenarios = {
        'balanced': StateDataFactory.create_initial_state,
        'economic_crisis': ScenarioDataFactory.create_economic_crisis_scenario,
        'population_boom': ScenarioDataFactory.create_population_boom_scenario,
        'social_conflict': ScenarioDataFactory.create_social_conflict_scenario,
        'resource_abundance': ScenarioDataFactory.create_resource_abundance_scenario,
        'aging_population': ScenarioDataFactory.create_aging_population_scenario
    }
    
    if scenario_name in scenarios:
        return scenarios[scenario_name]()
    else:
        return StateDataFactory.create_initial_state()


def create_custom_scenario(agents_config=None, farms_config=None, workplaces_config=None):
    """Create a custom scenario with specific configurations."""
    builder = TestDataBuilder()
    
    if agents_config:
        builder.add_agents(agents_config.get('count', 20), **agents_config.get('properties', {}))
    
    if farms_config:
        builder.add_farms(farms_config.get('count', 5), **farms_config.get('properties', {}))
    
    if workplaces_config:
        builder.add_workplaces(workplaces_config.get('count', 3), **workplaces_config.get('properties', {}))
    
    return builder.build_balanced()