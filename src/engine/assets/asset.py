import pygame

class Asset:
    def __init__(self, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.dirty = True  # Mark as needing redraw initially
    
    def set_position(self, x, y):
        old_pos = (self.rect.x, self.rect.y)
        self.rect.x = x
        self.rect.y = y
        
        # Mark as dirty if position changed
        if old_pos != (x, y):
            self.dirty = True
        
    def render(self, surface):
        surface.blit(self.image, self.rect)
        self.dirty = False  # Reset dirty flag after rendering
        