from typing import Tuple, Any
from .entity import EntityType
from .types.farm import Farm
from .types.agent import Agent 
from .types.workplace import WorkPlace
from src.core.ecs.components.transform import TransformComponent
from src.core.ecs.components.render import RenderComponent
from src.core.ecs.components.animation import AnimationComponent
from src.core.ecs.components.behaviour import BehaviorComponent
from src.core.ecs.components.tag import TagComponent
from src.core.ecs.components.workplace import WorkplaceComponent
from src.core.ecs.components.wallet import WalletComponent
from src.core.ecs.components.farm import FarmComponent
from src.core.ecs.components.reserves import ReservesComponent
from constants import FarmState
import random

class EntityFactory:
    """Factory for creating game entities with consistent initialization"""
    
    def __init__(self, asset_manager, ecs, spatial_grid, entity_pools):
        self.asset_manager = asset_manager
        self.ecs = ecs
        self.spatial_grid = spatial_grid
        self.entity_pools = entity_pools
        
    def create_entity(self, entity_type: EntityType, position: Tuple[int, int], 
                     screen=None, **kwargs) -> Any:
        """Create an entity of the specified type with consistent initialization"""
        # Map entity type to class
        entity_class = None
        tag_value = None
        
        if entity_type in [EntityType.PERSON_MALE, EntityType.PERSON_FEMALE]:
            entity_class = Agent
            tag_value = "agent"
            # Agent needs an ID
            if "id" not in kwargs:
                kwargs["id"] = 0
        elif entity_type == EntityType.FARM:
            entity_class = Farm
            tag_value = "farm"
        elif entity_type == EntityType.WORK:
            entity_class = WorkPlace
            tag_value = "work"
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
            
        # Get entity from pool if available
        entity = self.entity_pools[entity_class].acquire(
            *([kwargs.get("id", 0), screen] if entity_class == Agent else [screen])
        )
        
        # Set position
        entity.position = position
        
        # Create ECS entity
        entity_id = self.ecs.create_entity()
        entity.ecs_id = entity_id
        
        # Add components
        self._add_standard_components(entity, entity_id, tag_value)
        
        # Add entity to spatial grid
        self.spatial_grid.insert(entity_id, position[0], position[1])
        
        return entity
    
    def _add_standard_components(self, entity, entity_id, tag_value):
        """Add standard components to entity"""
        # Add transform component
        self.ecs.add_component(
            entity_id,
            "transform",
            TransformComponent(entity_id, position=entity.position)
        )
        
        # Add tag component
        if tag_value:
            self.ecs.add_component(
                entity_id,
                "tag",
                TagComponent(entity_id, tag=tag_value)
            )
        
        # Add wallet component for all entities that need money
        if hasattr(entity, 'money') or tag_value in ["agent", "work"]:
            initial_money = getattr(entity, 'money', 0.0)
            if tag_value == "work":
                initial_money = 1000.0  # Initial capital for workplaces
            
            self.ecs.add_component(
                entity_id,
                "wallet",
                WalletComponent(entity_id, money=initial_money)
            )
        
        # Add specific components based on entity type
        if hasattr(entity, 'entity_type'):
            # Add farm component for farm entities
            if entity.entity_type == EntityType.FARM:
                self.ecs.add_component(
                    entity_id,
                    "farm",
                    FarmComponent(
                        entity_id,
                        farm_state=FarmState.TILTH,
                        fertility=random.uniform(0.8, 1.2),
                        size=1
                    )
                )
            
            # Add workplace component for workplace entities
            elif entity.entity_type == EntityType.WORK:
                self.ecs.add_component(
                    entity_id,
                    "workplace",
                    WorkplaceComponent(
                        entity_id,
                        max_workers=entity.capacity
                    )
                )
            
            # Add reserves component for agent entities
            elif entity.entity_type in [EntityType.PERSON_MALE, EntityType.PERSON_FEMALE]:
                self.ecs.add_component(
                    entity_id,
                    "reserves",
                    ReservesComponent(entity_id)
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
                    size=entity.size,
                    visible=True
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
                        entity.position
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

    def register_existing_entity(self, entity):
        """Register an already created entity with the ECS system"""
        # Create ECS entity if needed
        if not hasattr(entity, 'ecs_id') or entity.ecs_id is None:
            entity_id = self.ecs.create_entity()
            entity.ecs_id = entity_id
        else:
            entity_id = entity.ecs_id
            
        # Determine tag value
        tag_value = None
        if hasattr(entity, 'genome'):
            tag_value = "agent"
        elif hasattr(entity, 'entity_type'):
            if entity.entity_type == EntityType.FARM:
                tag_value = "farm"
            elif entity.entity_type == EntityType.WORK:
                tag_value = "work"
        
        # Add standard components
        self._add_standard_components(entity, entity_id, tag_value)
        
        # Add entity to spatial grid
        self.spatial_grid.insert(entity_id, entity.position[0], entity.position[1])
        
        # Set reference to the world
        if hasattr(self, 'world'):
            entity.world = self.world
            
        return entity
