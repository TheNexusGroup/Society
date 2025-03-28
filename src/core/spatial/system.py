from typing import Dict, List, Tuple, Callable, Any, Optional
import math

class SpatialSystem:
    """System that maintains the spatial grid by tracking entity positions"""
    
    def __init__(self, world, grid):
        self.world = world
        self.grid = grid
        
    def update(self, dt):
        # Update all entities with transform components
        for entity_id, transform in self.world.get_components_by_type("transform").items():
            x, y = transform.position
            self.grid.update(entity_id, x, y)
    
    def find_nearest(self, position: Tuple[float, float], 
                    component_type: str = None,
                    max_results: int = 5, 
                    max_distance: float = 500) -> List[int]:
        """
        Find the nearest entities to a position, optionally filtered by component type
        
        Args:
            position: Query position (x, y)
            component_type: Optional component type to filter by
            max_results: Maximum number of results
            max_distance: Maximum search distance
            
        Returns:
            List of entity IDs sorted by distance
        """
        x, y = position
        
        # Get entities in radius
        entity_ids = self.grid.get_entities_in_radius(x, y, max_distance)
        
        # Filter by component type if specified
        if component_type:
            components = self.world.get_components_by_type(component_type)
            entity_ids = [eid for eid in entity_ids if eid in components]
        
        # Sort by distance
        entities_with_distances = []
        for eid in entity_ids:
            transform = self.world.get_component(eid, "transform")
            if transform:
                # Calculate distance
                ex, ey = transform.position
                distance = math.sqrt((ex - x) ** 2 + (ey - y) ** 2)
                entities_with_distances.append((eid, distance))
        
        # Sort by distance and return entity IDs
        entities_with_distances.sort(key=lambda x: x[1])
        return [eid for eid, _ in entities_with_distances[:max_results]]
    
    def find_in_radius(self, position: Tuple[float, float], 
                      radius: float,
                      component_type: str = None) -> List[int]:
        """Find all entities within a radius, optionally filtered by component type"""
        x, y = position
        
        # Get entities in radius
        entity_ids = self.grid.get_entities_in_radius(x, y, radius)
        
        # Filter by component type if specified
        if component_type:
            components = self.world.get_components_by_type(component_type)
            entity_ids = [eid for eid in entity_ids if eid in components]
            
        return list(entity_ids)
    
    def find_by_tag(self, position: Tuple[float, float],
                  radius: float,
                  tag_component: str,
                  tag_value: str) -> List[int]:
        """Find entities with a specific tag component value within a radius"""
        # Get entities in radius
        entity_ids = self.find_in_radius(position, radius)
        
        # Filter by tag value
        result = []
        for eid in entity_ids:
            component = self.world.get_component(eid, tag_component)
            if component and hasattr(component, 'tag') and component.tag == tag_value:
                result.append(eid)
                
        return result
