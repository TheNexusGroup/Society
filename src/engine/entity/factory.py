from typing import Tuple, Any
from .types import EntityType, Agent, Food, WorkPlace
from ..ecs.components import TransformComponent, RenderComponent, AnimationComponent, BehaviorComponent, TagComponent

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
        elif entity_type == EntityType.FOOD:
            entity_class = Food
            tag_value = "food"
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
                        "hunger": entity.hunger,
                        "money": entity.money,
                        "mood": entity.mood
                    }
                )
            )
