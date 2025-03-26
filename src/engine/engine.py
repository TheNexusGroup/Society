# The engine is the main entry point for the simulation

import pygame
import sys
from .world import World
from .assets.manager import AssetManager
from .ecs.system import SpatialDebugSystem
from .renderer.manager import RenderManager

class Simulation:
    def __init__(self, width=1600, height=1200):
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Societal Simulation")
        
        # Initialize components using composition
        self.asset_manager = AssetManager()
        self.world = World(width, height)
        self.render_manager = RenderManager(self.screen)
        
        # Connect components
        self.world.world_screen = self.screen
        self.world.asset_manager = self.asset_manager
        
        # Set up systems
        self.world.setup_systems()
        
        # Add spatial debug system
        self.spatial_debug = SpatialDebugSystem(self.world.ecs, self.screen)
        self.world.ecs.add_system(self.spatial_debug)
        
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Initialize the world
        self.world.setup_world()
        
    def run(self):
        self.running = True
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                    # Toggle spatial debug view
                    self.spatial_debug.enabled = not self.spatial_debug.enabled
            
            # Update world (includes rendering via ECS systems)
            self.world.update_world()

            # Flip display
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()