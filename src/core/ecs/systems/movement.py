from ..system import System

class MovementSystem(System):
    """System for updating entity positions based on velocity"""
    
    def update(self, dt):
        # Get all entities with TransformComponent
        for entity_id, transform in self.world.get_components_by_type("transform").items():
            behavior = self.world.get_component(entity_id, "behavior")
            if behavior and behavior.properties.get("is_alive") is True:
                # Update position based on velocity
                x, y = transform.position
                vx, vy = transform.velocity
                transform.position = (x + vx * dt, y + vy * dt)
                
                # Update any render component to match new position
                render = self.world.get_component(entity_id, "render")
                if render:
                    render.position = transform.position