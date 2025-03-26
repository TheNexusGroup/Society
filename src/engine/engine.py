# The engine is the main entry point for the simulation

import pygame
import sys
from .render import Renderer
from .world import World
from .assetmanager import AssetManager

class Simulation(Renderer, World):
    def __init__(self, width=1600, height=1200):
        # Initialize the asset manager first
        self.asset_manager = AssetManager()
        
        Renderer.__init__(self, width, height)
        World.__init__(self, width, height)
        
        # Pass screen to world
        self.world_screen = self.screen
        
        # Set up systems after the screen is ready
        self.setup_systems()
        self.clock = pygame.time.Clock()
        self.running = False
        self.setup_world()
        
    def run(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    
            # Clear the screen before rendering
            self.format_display()
            self.update_world()

            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()