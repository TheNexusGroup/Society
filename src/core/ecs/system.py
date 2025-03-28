class System:
    """Base class for all systems"""
    
    def __init__(self, world):
        self.world = world
    
    def update(self, dt):
        pass
