from typing import Set, List, Type, Any
import weakref

# Object pooling for common entities
class EntityPool:
    """Object pool for entity reuse"""
    
    def __init__(self, entity_class):
        self.entity_class = entity_class
        self.available = []
        # Use a list instead of WeakSet since our entities may not be hashable
        self.active = []
        
    def acquire(self, *args, **kwargs):
        """Get an entity from the pool or create a new one"""
        if self.available:
            entity = self.available.pop()
            entity.reset(*args, **kwargs)
        else:
            entity = self.entity_class(*args, **kwargs)
            
        self.active.append(entity)  # Using append instead of add
        return entity
        
    def release(self, entity):
        """Return an entity to the pool"""
        if entity in self.active:
            self.active.remove(entity)
            # Clear any references that might cause memory leaks
            if hasattr(entity, 'clear_references'):
                entity.clear_references()
            self.available.append(entity)
            
    def clear(self):
        """Clear all pooled entities"""
        self.available.clear()
        self.active.clear()