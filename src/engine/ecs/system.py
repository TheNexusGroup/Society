import random
import math
import pygame
from typing import List, Tuple, Dict, Any
from ..renderer.manager import RenderManager
from src.agent.behaviour import BehaviorSystem as AgentBehaviours

class System:
    """Base class for all systems"""
    
    def __init__(self, world):
        self.world = world
    
    def update(self, dt):
        pass

class RenderSystem(System):
    """System for rendering entities with RenderComponent using optimized batching"""
    
    def __init__(self, world, screen):
        super().__init__(world)
        self.screen = screen
        self.render_manager = RenderManager(screen)
    
    def update(self, dt):
        # Clear batches for this frame
        self.render_manager.clear()
        
        # Batch visible entities for efficient rendering
        self._batch_visible_entities()
        
        # Perform the actual rendering
        self.render_manager.render()
        
    def _batch_visible_entities(self):
        """Batch visible entities for efficient rendering"""
        # Get all entities with RenderComponent
        for entity_id, component in self.world.get_components_by_type("render").items():
            # Skip if not visible
            if not component.visible:
                continue
                
            # Get transform component for position
            transform = self.world.get_component(entity_id, "transform")
            if not transform:
                continue
                
            # Get the asset
            asset = component.asset
            
            # Create a unique texture ID (for animations we'll need the frame)
            if hasattr(asset, 'image'):
                # Regular asset
                texture_id = (asset.image, entity_id)
                self.render_manager.add_to_batch(
                    texture_id, 
                    transform.position,
                    None,
                    pygame.Rect(transform.position[0], transform.position[1], 
                              component.size[0], component.size[1])
                )
            elif hasattr(asset, 'images') and asset.images:
                # Animation - use current frame
                current_image = asset.images[asset.current_frame]
                texture_id = (current_image, entity_id, asset.current_frame)
                self.render_manager.add_to_batch(
                    texture_id,
                    transform.position,
                    None,
                    pygame.Rect(transform.position[0], transform.position[1], 
                              component.size[0], component.size[1])
                )

class AnimationSystem(System):
    """System for updating entity animations"""
    
    def update(self, dt):
        # Get all entities with AnimationComponent
        for entity_id, component in self.world.get_components_by_type("animation").items():
            if component.active:
                component.animation.update()

class MovementSystem(System):
    """System for updating entity positions based on velocity"""
    
    def update(self, dt):
        # Get all entities with TransformComponent
        for entity_id, transform in self.world.get_components_by_type("transform").items():
            # Update position based on velocity
            x, y = transform.position
            vx, vy = transform.velocity
            transform.position = (x + vx * dt, y + vy * dt)
            
            # Update any render component to match new position
            render = self.world.get_component(entity_id, "render")
            if render:
                render.position = transform.position

class SpatialDebugSystem(System):
    """System for visualizing spatial partitioning grid for debugging"""
    
    def __init__(self, world, screen):
        super().__init__(world)
        self.screen = screen
        self.cell_color = (100, 100, 200, 50)  # Semi-transparent blue
        self.grid_color = (50, 50, 150)  # Darker blue for grid lines
        self.entity_colors = {
            "agent": (255, 100, 100),    # Red for agents
            "food": (100, 255, 100),     # Green for food
            "work": (100, 100, 255)      # Blue for workplaces
        }
        self.enabled = False

class BehaviorSystem(System):
    """System for handling agent behaviors within ECS"""
    
    def __init__(self, world):
        super().__init__(world)
        # Use the existing behavior system from agent module for logic
        self.agent_behavior = AgentBehaviours(world)
    
    def update(self, dt):
        """Process behavior components"""
        # Get all entities with behavior components
        behavior_components = self.world.ecs.get_components_by_type("behavior")
        
        # Create a list of entity IDs to prevent dictionary changed size during iteration errors
        entity_ids = list(behavior_components.keys())
        
        for entity_id in entity_ids:
            # Check if entity still exists (may have been removed during iteration)
            if entity_id in behavior_components:
                # Use the agent behavior system to update this entity
                self.agent_behavior.update(entity_id)
