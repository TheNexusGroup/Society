import pygame
from ..system import System
from src.ui.render.manager import RenderManager

class RenderSystem(System):
    """System for rendering entities with RenderComponent using optimized batching"""
    
    def __init__(self, world, screen):
        super().__init__(world)
        self.screen = screen
        self.render_manager = RenderManager(screen)
        # Give render manager reference to world/ECS for sorting
        self.render_manager.world = world
    
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
                
            # Check for agent state in components
            tag_comp = self.world.get_component(entity_id, "tag")
            if tag_comp and tag_comp.tag == "agent":
                # If we have a behavior component, it may have state info
                behavior = self.world.get_component(entity_id, "behavior")
                if behavior:
                    # Check if agent is dead
                    if behavior.properties.get("is_alive") is False:
                        # Find dead asset
                        for entity_asset in component.alt_assets:
                            if entity_asset.key == "dead":
                                component.asset = entity_asset.asset
                                break
                    # Otherwise check normal state
                    elif behavior.state:
                        # Try to find an asset for this state
                        for entity_asset in component.alt_assets:
                            if entity_asset.key == behavior.state:
                                component.asset = entity_asset.asset
                                break
            
            # Get the asset
            asset = component.asset
            if not asset:
                continue
                
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