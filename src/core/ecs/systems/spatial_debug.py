from ..system import System

class SpatialDebugSystem(System):
    """System for visualizing spatial partitioning grid for debugging"""
    
    def __init__(self, world, screen):
        super().__init__(world)
        self.screen = screen
        self.cell_color = (100, 100, 200, 50)  # Semi-transparent blue
        self.grid_color = (50, 50, 150)  # Darker blue for grid lines
        self.entity_colors = {
            "agent": (255, 100, 100),    # Red for agents
            "food": (100, 255, 100),     # Green for food
            "work": (100, 100, 255)      # Blue for workplaces
        }
        self.enabled = False