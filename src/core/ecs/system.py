class System:
    """Base class for all systems"""
    
    def __init__(self, world, update_frequency=1):
        """
        Initialize system
        
        Args:
            world: The world instance
            update_frequency: How often to update (1 = every frame, 2 = every 2nd frame, etc.)
        """
        self.world = world
        self.update_frequency = update_frequency
        self.frame_count = 0
        
    def should_update(self):
        """Check if this system should update this frame"""
        return self.frame_count % self.update_frequency == 0
    
    def update(self, dt):
        """Update the system - subclasses should override this"""
        pass
        
    def tick(self, dt):
        """Called every frame - handles throttling logic"""
        self.frame_count += 1
        if self.should_update():
            self.update(dt)
