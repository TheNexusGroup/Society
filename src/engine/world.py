from ..population.types import Agent, WorkPlace, Food
from .ecs_core import ECS
from .ecs.components import RenderComponent, AnimationComponent, TransformComponent, BehaviorComponent, TagComponent
from .ecs.system import RenderSystem, AnimationSystem, MovementSystem, BehaviorSystem
from .spatial_system.grid import SpatialGrid
from .spatial_system.system import SpatialSystem
from .constants import EntityType

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.entities = []
        self.population = []
        self.population_size = 25
        self.food_count = 5
        self.work_count = 3
        self.world_screen = None  # Will be set by Simulation
        
        # Initialize ECS world
        self.ecs = ECS()
        
        # Initialize spatial grid
        self.spatial_grid = SpatialGrid(width, height)
        
    def setup_systems(self):
        # Add systems to the ECS world
        self.ecs.add_system(RenderSystem(self.ecs, self.world_screen))
        self.ecs.add_system(AnimationSystem(self.ecs))
        self.ecs.add_system(MovementSystem(self.ecs))
        self.ecs.add_system(BehaviorSystem(self.ecs))
        
        # Add spatial system
        self.spatial_system = SpatialSystem(self.ecs, self.spatial_grid)
        self.ecs.add_system(self.spatial_system)

    def setup_world(self):
        # Setup ECS systems first
        self.setup_systems()
        
        # Create entities
        self.create_population()
        self.create_food()
        self.create_work()

    def create_population(self):
        for i in range(self.population_size):
            self.add_entity(Agent(i, self.world_screen))

    def create_food(self):
        for i in range(self.food_count):
            self.add_entity(Food(self.world_screen))

    def create_work(self):
        for i in range(self.work_count):
            self.add_entity(WorkPlace(self.world_screen))
        
    def add_entity(self, entity):
        self.entities.append(entity)
        
        # Create an ECS entity and add components
        entity_id = self.ecs.create_entity()
        
        # Store ECS entity ID with the entity
        entity.ecs_id = entity_id
        
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
        elif entity.entity_type == EntityType.FOOD:
            tag_value = "food"
        elif entity.entity_type == EntityType.WORK:
            tag_value = "work"
        
        if tag_value:
            self.ecs.add_component(
                entity_id,
                "tag",
                TagComponent(entity_id, tag=tag_value)
            )
        
        # Add render component for main asset
        main_asset = entity.get_asset(entity.entity_type.value)
        if main_asset:
            self.ecs.add_component(
                entity_id,
                "render",
                RenderComponent(
                    entity_id,
                    main_asset,
                    position=entity.position,
                    size=entity.size
                )
            )
        
        # Add animation components if any
        for name, asset in entity.assets.items():
            if name != entity.entity_type.value and hasattr(asset, 'update'):
                self.ecs.add_component(
                    entity_id,
                    "animation",
                    AnimationComponent(
                        entity_id,
                        asset,
                        position=entity.position
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
                        "hunger": entity.hunger,
                        "money": entity.money,
                        "mood": entity.mood
                    }
                )
            )

    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
            
            # Find and remove the ECS entity
            for entity_id, component in self.ecs.get_components_by_type("render").items():
                if component.asset in entity.assets.values():
                    self.ecs.delete_entity(entity_id)
                    break

    def update_world(self):
        # Update the ECS world instead of individual entities
        self.ecs.update(1.0)  # Using 1.0 as a fixed delta time
