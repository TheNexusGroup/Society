import pygame

class Asset:
    def __init__(self, image):
        self.image = image
        self.rect = self.image.get_rect()
    
    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
        
    def render(self, surface):
        surface.blit(self.image, self.rect)
        