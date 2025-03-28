from typing import Dict, List, Tuple, Set, Optional, Any
import math

class SpatialGrid:
    """
    A grid-based spatial partitioning system that divides the world into cells
    for efficient spatial queries.
    """
    
    def __init__(self, width: int, height: int, cell_size: int = 100):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        # Calculate grid dimensions
        self.cols = math.ceil(width / cell_size)
        self.rows = math.ceil(height / cell_size)
        
        # Initialize the grid cells
        self.grid: Dict[Tuple[int, int], Set[int]] = {}
        
        # Entity to cell mapping for fast lookups
        self.entity_cells: Dict[int, Tuple[int, int]] = {}
    
    def get_cell_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid cell coordinates"""
        col = max(0, min(self.cols - 1, int(x / self.cell_size)))
        row = max(0, min(self.rows - 1, int(y / self.cell_size)))
        return (col, row)
    
    def insert(self, entity_id: int, x: float, y: float) -> None:
        """Insert an entity into the grid at the specified position"""
        cell_coords = self.get_cell_coords(x, y)
        
        # Remove from previous cell if it exists
        self.remove(entity_id)
        
        # Create cell if it doesn't exist
        if cell_coords not in self.grid:
            self.grid[cell_coords] = set()
        
        # Add entity to cell
        self.grid[cell_coords].add(entity_id)
        
        # Store entity's cell for fast lookups
        self.entity_cells[entity_id] = cell_coords
    
    def remove(self, entity_id: int) -> None:
        """Remove an entity from the grid"""
        if entity_id in self.entity_cells:
            cell_coords = self.entity_cells[entity_id]
            if cell_coords in self.grid and entity_id in self.grid[cell_coords]:
                self.grid[cell_coords].remove(entity_id)
                
                # Clean up empty cells
                if not self.grid[cell_coords]:
                    del self.grid[cell_coords]
                    
            del self.entity_cells[entity_id]
    
    def update(self, entity_id: int, x: float, y: float) -> None:
        """Update an entity's position in the grid"""
        new_cell = self.get_cell_coords(x, y)
        
        # If in same cell, do nothing
        if entity_id in self.entity_cells and self.entity_cells[entity_id] == new_cell:
            return
            
        # Otherwise, re-insert
        self.insert(entity_id, x, y)
    
    def get_entities_in_cell(self, col: int, row: int) -> Set[int]:
        """Get all entities in a specific cell"""
        return self.grid.get((col, row), set())
    
    def get_entities_in_radius(self, x: float, y: float, radius: float) -> Set[int]:
        """Get all entities within a radius of a point"""
        # Calculate cell range to check
        start_col, start_row = self.get_cell_coords(x - radius, y - radius)
        end_col, end_row = self.get_cell_coords(x + radius, y + radius)
        
        # Collect entities from all cells in range
        result = set()
        for col in range(start_col, end_col + 1):
            for row in range(start_row, end_row + 1):
                result.update(self.get_entities_in_cell(col, row))
        
        return result
    
    def get_entities_in_rect(self, x: float, y: float, width: float, height: float) -> Set[int]:
        """Get all entities within a rectangular region"""
        # Calculate cell range to check
        start_col, start_row = self.get_cell_coords(x, y)
        end_col, end_row = self.get_cell_coords(x + width, y + height)
        
        # Collect entities from all cells in range
        result = set()
        for col in range(start_col, end_col + 1):
            for row in range(start_row, end_row + 1):
                result.update(self.get_entities_in_cell(col, row))
        
        return result
    
    def get_nearest_entities(self, x: float, y: float, 
                            entity_filter=None, max_results=5, max_radius=500) -> List[int]:
        """
        Get the nearest entities to a point, optionally filtered
        
        Args:
            x, y: Query position
            entity_filter: Optional function to filter entities (entity_id -> bool)
            max_results: Maximum number of results to return
            max_radius: Maximum search radius
        
        Returns:
            List of entity IDs sorted by distance
        """
        # Start with a small radius and expand until we find enough entities
        radius = self.cell_size
        results = []
        
        while radius <= max_radius and len(results) < max_results:
            entities = self.get_entities_in_radius(x, y, radius)
            
            # Filter entities if needed
            if entity_filter:
                entities = [e for e in entities if entity_filter(e)]
            
            # If we found entities, return them sorted by distance
            if entities:
                # We need positions to calculate distances - this requires the ECS
                # This will be implemented in the integration with ECS
                pass
            
            # Expand search radius
            radius *= 2
        
        return results[:max_results]
