import pygame

class Animation:
    def __init__(self, images, frame_delay=10, image_paths=None):
        self.images = images
        self.current_frame = 0
        self.frame_delay = frame_delay
        self.frame_counter = 0
        self.rect = self.images[0].get_rect()
        self.image_paths = image_paths  # Store the paths for scaling
        
    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
        
    def update(self):
        self.frame_counter += 1
        if self.frame_counter >= self.frame_delay:
            self.frame_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.images)

    def render(self, surface):
        surface.blit(self.images[self.current_frame], self.rect)
        