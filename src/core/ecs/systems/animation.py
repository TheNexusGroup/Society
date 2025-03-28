from ..system import System

class AnimationSystem(System):
    """System for updating entity animations"""
    
    def update(self, dt):
        # Get all entities with AnimationComponent
        for entity_id, component in self.world.get_components_by_type("animation").items():
            if component.active:
                component.animation.update()