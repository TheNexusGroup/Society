# An entity is a basic unit of the simulation that can be rendered and interacted with

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
import pygame
from ..assets.asset import Asset
from ..assets.animation import Animation
from ..assets.manager import AssetManager
from src.constants import EntityType, asset_map, additional_assets

class Entity:
    position: Tuple[int, int]
    size: Tuple[int, int] = (64, 64)
    entity_type: EntityType
    assets: Dict[str, Asset]
    screen: pygame.Surface
    default_asset: str
    additional_assets: Dict[str, Dict[str, Any]]
    asset_manager: AssetManager
    ecs_id: Optional[int] = None  # Store the ECS entity ID
    current_state: Optional[str] = None

    def __init__(self, entity_type: EntityType, position: Tuple[int, int]):
        self.entity_type = entity_type
        self.position = position
        self.default_asset = asset_map[self.entity_type].get("path")
        self.stateful_assets = [k for k, v in asset_map[self.entity_type].items() if k in ["eat", "mate", "work", "rest", "dead"]]
        self.additional_assets = additional_assets.get(self.entity_type, {})
        self.assets = {}
        self.asset_manager = AssetManager()
        
        self.load_asset(asset_map[self.entity_type].get("name"), self.default_asset)

        for key in self.stateful_assets:
            self.load_asset(key, asset_map[self.entity_type][key])

        if self.additional_assets:
            self.load_animation(
                self.additional_assets["name"],
                self.additional_assets["path"],
                self.additional_assets["count"]
            )
            
        self.scale_asset(self.entity_type.value, self.size[0], self.size[1])
        
    def load_asset(self, name, image_path):
        print(f"Loading asset: {name} from {image_path}")
        self.assets[name] = self.asset_manager.get_asset(image_path)
        return self.assets[name]
        
    def load_animation(self, name, pattern, frame_count, frame_delay=10):
        image_paths = [pattern.format(i) for i in range(1, frame_count + 1)]
        self.assets[name] = self.asset_manager.get_animation(image_paths, frame_delay)
        return self.assets[name]
        
    def get_asset(self, name):
        return self.assets.get(name)

    def scale_asset(self, asset_name, width, height):
        asset = self.assets[asset_name]
        
        # Replace with direct scaled asset creation
        if isinstance(asset, Animation):
            # Get the paths from the current animation
            if hasattr(asset, 'image_paths'):
                paths = asset.image_paths
            else:
                # This is a fallback if image_paths aren't stored
                # In a real implementation, we'd modify Animation to store paths
                return asset
                
            self.assets[asset_name] = self.asset_manager.get_scaled_animation(
                paths, width, height, asset.frame_delay
            )
        else:
            # For normal assets, we need the original path
            # In a real impl we'd store the path in the Asset class
            for path, stored_asset in self.asset_manager.assets.items():
                if stored_asset == asset:
                    self.assets[asset_name] = self.asset_manager.get_scaled_asset(
                        path, width, height
                    )
                    break
                    
        return self.assets[asset_name]

        
    def render_all(self):
        for asset in self.assets.values():
            asset.render(self.screen)
            
    def update_animations(self):
        for asset in self.assets.values():
            if isinstance(asset, Animation):
                asset.update()

    def position_asset(self, asset_name, x, y):
        asset = self.assets[asset_name]
        asset.set_position(x, y)

    def update(self):
        pass  # ECS handles updates now

    def update_asset_based_on_state(self, state=None):
        """Update the entity's appearance based on its current state"""
        if not hasattr(self, 'entity_type') or self.entity_type not in asset_map:
            return
        
        # Get asset configurations for this entity type
        asset_config = asset_map[self.entity_type]
        
        # Default to main asset
        asset_name = asset_config["name"]
        
        # If we're an Agent with a current state/action
        if hasattr(self, 'is_alive') and not self.is_alive:
            # Dead state takes precedence
            if "dead" in self.assets:
                asset_name = "dead"
        elif state and state in self.assets:
            # Use the asset for this state if available
            asset_name = state
        
        # Update current state
        self.current_state = asset_name

class EntityFactory:
    @staticmethod
    def create_entity(entity_type: EntityType, x: int, y: int) -> Entity:
        return Entity(
            entity_type=entity_type,
            position=(x, y)
        )
