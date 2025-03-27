# The engine is the main entry point for the simulation

import pygame
import sys
from .world import World
from .assets.manager import AssetManager
from .ecs.system import SpatialDebugSystem
from .renderer.manager import RenderManager
from src.ui.info_panel import InfoPanel

class Simulation:
    def __init__(self, width=1600, height=1200):
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Societal Simulation")
        
        # Initialize UI components first
        self.info_panel = InfoPanel(self.screen)
        
        # Initialize components using composition
        self.asset_manager = AssetManager()
        self.render_manager = RenderManager(self.screen, ui_rects=[self.info_panel.rect])
        
        # Initialize world
        self.world = World(width, height)
        self.world.world_screen = self.screen
        self.world.asset_manager = self.asset_manager
        self.world.render_manager = self.render_manager
        self.world.setup_systems()
        
        # Add spatial debug system
        self.spatial_debug = SpatialDebugSystem(self.world.ecs, self.screen)
        self.world.ecs.add_system(self.spatial_debug)
        
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Initialize the world
        self.world.setup_world()
        
    def run(self):
        """Main simulation loop"""
        self.running = True
        
        while self.running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_F1:
                        # Toggle debug view
                        self.spatial_debug.toggle()
                    elif event.key == pygame.K_F2:
                        # Toggle info panel
                        self.info_panel.toggle()
            
            # Update the world
            self.world.update_world()
            
            # Update and render UI
            self.info_panel.update(self.world)
            self.info_panel.render()
            
            # Flip display
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()