import random
import math
import pygame
from typing import List, Tuple, Dict, Any
from ..renderer.manager import RenderManager

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

class BehaviorSystem(System):
    """System for handling entity behaviors and AI"""
    
    def update(self, dt):
        # Process all entities with behavior components
        for entity_id, behavior in self.world.get_components_by_type("behavior").items():
            # Get transform component
            transform = self.world.get_component(entity_id, "transform")
            if not transform:
                continue
                
            # Get tag component to identify entity type
            tag = self.world.get_component(entity_id, "tag")
            if not tag:
                continue
                
            # Handle different entity types
            if tag.tag == "agent":
                self.update_agent(entity_id, behavior, transform, dt)
                
    def update_agent(self, entity_id, behavior, transform, dt):
        """Handle agent-specific behavior"""
        x, y = transform.position
        
        # Update behavior based on state and properties
        state = behavior.state
        properties = behavior.properties
        
        # Example: If hungry, look for food
        if state == "idle" and properties.get("hunger", 0) > 60:
            # Find nearby food using spatial system
            spatial = self.world.get_system("spatial")
            food_entities = spatial.find_by_tag(
                transform.position, 
                300,  # Search radius
                "tag", 
                "food"
            )
            
            if food_entities:
                # Target the closest food
                food_id = food_entities[0]
                food_transform = self.world.get_component(food_id, "transform")
                
                if food_transform:
                    # Set target and change state
                    behavior.target = food_id
                    behavior.state = "seeking_food"
                    behavior.target_action = "eat"  # Set the RL action
                    
                    # Calculate direction to food
                    fx, fy = food_transform.position
                    dx, dy = fx - x, fy - y
                    distance = max(1, math.sqrt(dx*dx + dy*dy))
                    
                    # Normalize and set velocity
                    transform.velocity = (dx/distance * 50, dy/distance * 50)
        
        # Example: If seeking food, move toward it
        elif state == "seeking_food":
            target_id = behavior.target
            if target_id is not None:
                target_transform = self.world.get_component(target_id, "transform")
                
                if target_transform:
                    # Calculate direction to target
                    tx, ty = target_transform.position
                    dx, dy = tx - x, ty - y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < 10:  # Close enough to eat
                        # Eat the food
                        properties["hunger"] = max(0, properties["hunger"] - 30)
                        behavior.state = "idle"
                        behavior.target = None
                        behavior.target_action = None
                        transform.velocity = (0, 0)
                        
                        # Get the entity from the world to actually remove it
                        for entity in self.world.entities:
                            if hasattr(entity, 'ecs_id') and entity.ecs_id == target_id:
                                self.world.remove_entity(entity)
                                break
                    else:
                        # Keep moving toward food
                        transform.velocity = (dx/distance * 50, dy/distance * 50)
                else:
                    # Target no longer exists
                    behavior.state = "idle"
                    behavior.target = None
                    behavior.target_action = None
                    transform.velocity = (0, 0)

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
