from src.simulation.entities.types.farm import Farm
from src.simulation.entities.types.workplace import WorkPlace
from src.simulation.entities.types.agent import Agent
from src.core.ecs.core import ECS
from src.core.ecs.components.render import RenderComponent
from src.core.ecs.components.animation import AnimationComponent
from src.core.ecs.components.transform import TransformComponent
from src.core.ecs.components.behaviour import BehaviorComponent
from src.core.ecs.components.tag import TagComponent
from src.core.ecs.systems.render import RenderSystem
from src.core.ecs.systems.animation import AnimationSystem
from src.core.ecs.systems.movement import MovementSystem
from src.core.ecs.systems.behaviour import BehaviorSystem
from src.core.spatial.grid import SpatialGrid
from src.core.spatial.system import SpatialSystem
from constants import EntityType
from src.utils.pool import EntityPool
from src.simulation.entities.factory import EntityFactory
from src.simulation.society.population import Population
from src.core.ecs.systems.reproduction import ReproductionSystem
from src.core.ecs.systems.navigation import NavigationSystem
from src.data.metrics import MetricsCollector
from src.core.ecs.components.workplace import WorkplaceComponent
from src.core.ecs.components.wallet import WalletComponent
import random

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.entities = []
        self.population_size = 100
        self.farm_count = 25
        self.work_count = 15
        self.world_screen = None  # Will be set by Simulation
        
        # Initialize metrics collector
        self.metrics = MetricsCollector()
        
        # Initialize ECS world
        self.ecs = ECS()
        
        # Initialize spatial grid
        self.spatial_grid = SpatialGrid(width, height)
        
        # Initialize entity pools
        self.entity_pools = {
            Agent: EntityPool(Agent),
            Farm: EntityPool(Farm),
            WorkPlace: EntityPool(WorkPlace)
        }
        
        # Initialize entity factory
        self.entity_factory = None  # Will be set after asset_manager is available
        
        # Initialize society
        self.society = Population(self)
        
        # Initialize reproduction system
        self.reproduction_system = ReproductionSystem(self)
        
    def setup_systems(self):
        # Add systems to the ECS world
        self.ecs.add_system(RenderSystem(self.ecs, self.world_screen))
        self.ecs.add_system(AnimationSystem(self.ecs))
        self.ecs.add_system(MovementSystem(self.ecs))
        self.ecs.add_system(BehaviorSystem(self))
        
        # Add navigation system
        self.navigation_system = NavigationSystem(self)
        self.ecs.add_system(self.navigation_system)
        
        # Add spatial system
        self.spatial_system = SpatialSystem(self.ecs, self.spatial_grid)
        self.ecs.add_system(self.spatial_system)
        
        # Initialize entity factory now that we have asset_manager
        self.entity_factory = EntityFactory(
            self.asset_manager,
            self.ecs,
            self.spatial_grid,
            self.entity_pools
        )

    def setup_world(self):
        # Setup ECS systems first
        self.setup_systems()
        
        # Create entities
        self.create_population()
        self.create_farms()
        self.create_work()
        
    def create_population(self):
        for i in range(self.population_size):
            agent = self.entity_factory.create_entity(
                EntityType.PERSON_MALE if i % 2 == 0 else EntityType.PERSON_FEMALE, 
                (random.randint(0, self.width), random.randint(0, self.height)),
                self.world_screen,
                id=i
            )
            self.entities.append(agent)
            self.society.population.append(agent)

    def create_farms(self):
        # Only create food if we don't have enough
        current_farm_count = sum(1 for e in self.entities if e.entity_type == EntityType.FARM)
        for i in range(current_farm_count, self.farm_count):
            food = self.entity_factory.create_entity(
                EntityType.FARM,
                (random.randint(0, self.width), random.randint(0, self.height)),
                self.world_screen
            )
            self.entities.append(food)

    def create_work(self):
        # Only create workplaces if we don't have enough
        current_work_count = sum(1 for e in self.entities if e.entity_type == EntityType.WORK)
        for i in range(current_work_count, self.work_count):
            workplace = self.entity_factory.create_entity(
                EntityType.WORK,
                (random.randint(0, self.width), random.randint(0, self.height)),
                self.world_screen
            )
            self.entities.append(workplace)
        
    def add_entity(self, entity):
        self.entities.append(entity)
        
        # Create an ECS entity and add components
        entity_id = self.ecs.create_entity()
        
        # Store ECS entity ID with the entity
        entity.ecs_id = entity_id
        entity.world = self  # Add reference to world
        
        # Add transform component
        self.ecs.add_component(
            entity_id,
            "transform",
            TransformComponent(entity_id, position=entity.position)
        )
        
        # Add entity to spatial grid
        self.spatial_grid.insert(entity_id, entity.position[0], entity.position[1])
        
        # Add tag component based on entity type
        tag_value = None
        if hasattr(entity, 'genome'):
            tag_value = "agent"
            # Add wallet component for agents
            self.ecs.add_component(
                entity_id,
                "wallet",
                WalletComponent(entity_id, money=entity.money)
            )
        elif entity.entity_type == EntityType.FARM:
            tag_value = "farm"
        elif entity.entity_type == EntityType.WORK:
            tag_value = "work"
            # Add workplace component for workplaces
            self.ecs.add_component(
                entity_id,
                "workplace",
                WorkplaceComponent(
                    entity_id,
                    max_workers=entity.capacity
                )
            )
        
        if tag_value:
            self.ecs.add_component(
                entity_id,
                "tag",
                TagComponent(entity_id, tag=tag_value)
            )
        
        # Add render component for main asset
        render_component = RenderComponent(
            entity_id,
            entity.get_asset(entity.entity_type.value),
            position=entity.position,
            size=entity.size
        )
        
        # Add state-specific assets to the render component
        for name, asset in entity.assets.items():
            if name != entity.entity_type.value:
                render_component.add_asset_for_state(name, asset)
        
        self.ecs.add_component(entity_id, "render", render_component)
        
        # Add animation components if any
        for name, asset in entity.assets.items():
            if hasattr(asset, 'update'):
                self.ecs.add_component(
                    entity_id,
                    "animation",
                    AnimationComponent(
                        entity_id,
                        asset,
                        position=entity.position,
                        name=name
                    )
                )
        
        # Add behavior component for agents
        if hasattr(entity, 'genome'):
            self.ecs.add_component(
                entity_id,
                "behavior",
                BehaviorComponent(
                    entity_id,
                    state="idle",
                    properties={
                        "energy": entity.energy,
                        "money": entity.money,
                        "mood": entity.mood
                    }
                )
            )

    def remove_entity(self, entity):
        # For dead agents, don't remove from entities list immediately
        # This allows them to still be rendered with their "dead" state
        if entity in self.entities and (not hasattr(entity, 'is_alive') or entity.is_alive):
            self.entities.remove(entity)
            
            # Remove from spatial grid
            self.spatial_grid.remove(entity.ecs_id)
            
            # Remove from ECS
            self.ecs.delete_entity(entity.ecs_id)
            
            # Return to pool
            entity_type = type(entity)
            if entity_type in self.entity_pools:
                self.entity_pools[entity_type].release(entity)

    def update_world(self):
        # Update the ECS world instead of individual entities
        self.ecs.update(1.0)  # Using 1.0 as a fixed delta time
        
        # Update metrics
        self.collect_metrics()

    def collect_metrics(self):
        """Collect current world state metrics"""
        # Count males and females
        males = sum(1 for agent in self.society.population if agent.genome.gender.value == 'male')
        females = len(self.society.population) - males
        
        # Calculate agent averages
        avg_age = avg_energy = avg_money = avg_mood = 0
        if self.society.population:
            avg_age = sum(agent.age for agent in self.society.population) / len(self.society.population)
            avg_energy = sum(agent.energy for agent in self.society.population) / len(self.society.population)
            avg_money = sum(agent.money for agent in self.society.population) / len(self.society.population)
            avg_mood = sum(agent.mood for agent in self.society.population) / len(self.society.population)
            
        # Count actions
        action_counts = {'eat': 0, 'work': 0, 'rest': 0, 'mate': 0, 'search': 0}
        for agent in self.society.population:
            if agent.current_action and agent.current_action in action_counts:
                action_counts[agent.current_action] += 1
                
        # Update metrics collector
        self.metrics.collect({
            'population_size': len([agent for agent in self.society.population if agent.is_alive]),
            'male_count': males,
            'female_count': females,
            'farm_count': sum(1 for e in self.entities if e.entity_type == EntityType.FARM),
            'work_count': sum(1 for e in self.entities if e.entity_type == EntityType.WORK),
            'avg_age': avg_age,
            'avg_energy': avg_energy,
            'avg_money': avg_money,
            'avg_mood': avg_mood,
            'action_eat': action_counts['eat'],
            'action_work': action_counts['work'],
            'action_rest': action_counts['rest'],
            'action_mate': action_counts['mate'],
            'action_search': action_counts['search'],
            'epoch': self.society.epoch
        })

    def get_entity_by_id(self, entity_id):
        """Find an entity by its ECS ID"""
        for entity in self.entities:
            if hasattr(entity, 'ecs_id') and entity.ecs_id == entity_id:
                return entity
        return None

    def reset_world(self):
        """Reset the world state between epochs"""
        # Clear all entities from the world
        entities_to_remove = self.entities.copy()
        for entity in entities_to_remove:
            # Force removal of all entities including dead ones
            if entity in self.entities:
                self.entities.remove(entity)
                
                # Remove from spatial grid if it has an ECS ID
                if hasattr(entity, 'ecs_id'):
                    self.spatial_grid.remove(entity.ecs_id)
                    
                    # Return to pool
                    entity_type = type(entity)
                    if entity_type in self.entity_pools:
                        self.entity_pools[entity_type].release(entity)
        
        # Reset the ECS world
        self.ecs = ECS()
        
        # Reset spatial grid
        self.spatial_grid = SpatialGrid(self.width, self.height)
        
        # Reset entity lists
        self.entities = []
        self.society.population = []
        
        # Reset entity pools
        for pool in self.entity_pools.values():
            pool.clear()
        
        # Re-setup systems with the new ECS world
        self.setup_systems()