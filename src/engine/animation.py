import pygame

class Animation:
    def __init__(self, images, frame_delay=10, image_paths=None):
        self.images = images
        self.current_frame = 0
        self.frame_delay = frame_delay
        self.frame_counter = 0
        self.rect = self.images[0].get_rect()
        self.image_paths = image_paths  # Store the paths for scaling
        self.dirty = True  # Mark as needing redraw when frame changes
        
    def set_position(self, x, y):
        old_pos = (self.rect.x, self.rect.y)
        self.rect.x = x
        self.rect.y = y
        
        # Mark as dirty if position changed
        if old_pos != (x, y):
            self.dirty = True
        
    def update(self):
        self.frame_counter += 1
        if self.frame_counter >= self.frame_delay:
            self.frame_counter = 0
            old_frame = self.current_frame
            self.current_frame = (self.current_frame + 1) % len(self.images)
            
            # Mark as dirty when animation frame changes
            if old_frame != self.current_frame:
                self.dirty = True

    def render(self, surface):
        surface.blit(self.images[self.current_frame], self.rect)
        self.dirty = False  # Reset dirty flag after rendering
        
    def get_current_image(self):
        return self.images[self.current_frame]
        