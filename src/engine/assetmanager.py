import os
import pygame
from typing import Dict, List, Optional, Union, Tuple
from .animation import Animation
from .asset import Asset
from .constants import EntityType, asset_map, additional_assets

class AssetManager:
    """Centralized asset management system to load, cache and manage game assets"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.images: Dict[str, pygame.Surface] = {}
        self.animations: Dict[str, Animation] = {}
        self.assets: Dict[str, Asset] = {}
    
    def get_image(self, path: str) -> pygame.Surface:
        """Load image and cache it, or return from cache if already loaded"""
        if path not in self.images:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                self.images[path] = pygame.image.load(path)
            except (FileNotFoundError, pygame.error):
                self.images[path] = self._create_placeholder(50, 50)
        return self.images[path]
    
    def get_animation(self, paths: List[str], frame_delay=10) -> Animation:
        """Get animation from cache or create a new one"""
        key = ",".join(paths) + f",{frame_delay}"
        if key not in self.animations:
            images = [self.get_image(path) for path in paths]
            self.animations[key] = Animation(images, frame_delay, image_paths=paths)
        return self.animations[key]
    
    def get_asset(self, path: str) -> Asset:
        """Get asset from cache or create a new one"""
        if path not in self.assets:
            image = self.get_image(path)
            asset = Asset(image)
            self.assets[path] = asset
        return self.assets[path]
    
    def _create_placeholder(self, width, height) -> pygame.Surface:
        surface = pygame.Surface((width, height))
        surface.fill((100, 100, 100))
        return surface
    
    def scale_image(self, image: pygame.Surface, width: int, height: int) -> pygame.Surface:
        """Scale an image and return the result"""
        return pygame.transform.scale(image, (width, height))
        
    def load_spritesheet(self, path: str, sprite_width: int, sprite_height: int, rows: int, cols: int) -> List[pygame.Surface]:
        """Load a spritesheet and split it into individual sprites"""
        spritesheet = self.get_image(path)
        sprites = []
        
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(
                    col * sprite_width, 
                    row * sprite_height, 
                    sprite_width, 
                    sprite_height
                )
                sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                sprite.blit(spritesheet, (0, 0), rect)
                sprites.append(sprite)
                
        return sprites
    
    def get_scaled_asset(self, path: str, width: int, height: int) -> Asset:
        """Get scaled asset directly"""
        key = f"{path}_{width}_{height}"
        if key not in self.assets:
            image = self.get_image(path)
            scaled_image = self.scale_image(image, width, height)
            self.assets[key] = Asset(scaled_image)
        return self.assets[key]
    
    def get_scaled_animation(self, paths: List[str], width: int, height: int, frame_delay=10) -> Animation:
        """Get scaled animation directly"""
        key = f"{','.join(paths)}_{width}_{height}_{frame_delay}"
        if key not in self.animations:
            images = [self.scale_image(self.get_image(path), width, height) for path in paths]
            self.animations[key] = Animation(images, frame_delay, image_paths=paths)
        return self.animations[key]

    def get_render_component(self, entity_type: str, position: Tuple[int, int], size: Tuple[int, int]) -> dict:
        """Create a render component configuration for ECS"""
        path = asset_map.get(entity_type, "")
        if not path:
            return {}
        
        return {
            "type": "render",
            "asset": self.get_scaled_asset(path, size[0], size[1]),
            "position": position
        }
    
    def get_animation_component(self, entity_type: str, animation_name: str, 
                               position: Tuple[int, int], size: Tuple[int, int]) -> dict:
        """Create an animation component configuration for ECS"""
        anim_config = additional_assets.get(entity_type, {})
        if not anim_config:
            return {}
        
        paths = [anim_config["path"].format(i) for i in range(1, anim_config.get("count", 0) + 1)]
        if not paths:
            return {}
        
        return {
            "type": "animation",
            "animation": self.get_scaled_animation(paths, size[0], size[1]),
            "position": position,
            "name": animation_name
        }
