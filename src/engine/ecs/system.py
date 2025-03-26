import random
import math

class System:
    """Base class for all systems"""
    
    def __init__(self, world):
        self.world = world
    
    def update(self, dt):
        pass

class RenderSystem(System):
    """System for rendering entities with RenderComponent"""
    
    def __init__(self, world, screen):
        super().__init__(world)
        self.screen = screen
    
    def update(self, dt):
        # Get all entities with RenderComponent
        for entity_id, component in self.world.get_components_by_type("render").items():
            # Skip if not visible
            if not component.visible:
                continue
                
            # Position the asset and render it
            asset = component.asset
            asset.set_position(*component.position)
            asset.render(self.screen)

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
                        transform.velocity = (0, 0)
                        
                        # Remove the food entity
                        # This would need to be handled by a message system
                        # or a separate food system
                    else:
                        # Keep moving toward food
                        transform.velocity = (dx/distance * 50, dy/distance * 50)
                else:
                    # Target no longer exists
                    behavior.state = "idle"
                    behavior.target = None
                    transform.velocity = (0, 0)
