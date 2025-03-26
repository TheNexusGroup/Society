# Here we handle the individual rendering aspects of the simulation

import pygame
import os
from .asset import Asset
from .animation import Animation

class Renderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Societal Simulation")
        self.format_display()

    def format_display(self):
        # Clear the screen before rendering
        self.screen.fill((50, 100, 50))

        # Creates a dark grey background with white grid lines
        for i in range(0, self.width, 100):
            pygame.draw.line(self.screen, (25, 65, 155), (i, 0), (i, self.height), 2)
        for i in range(0, self.height, 100):
            pygame.draw.line(self.screen, (25, 65, 155), (0, i), (self.width, i), 2)

