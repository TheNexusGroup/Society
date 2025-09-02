class Entity:
    """Simple entity class - just an ID with ability to add/get components"""
    
    _next_id = 0
    
    @classmethod
    def get_id(cls):
        entity_id = cls._next_id
        cls._next_id += 1
        return entity_id
    
    def __init__(self):
        self.id = Entity.get_id()
        self.components = {}
        
    def add_component(self, component_type, component):
        component.entity_id = self.id
        self.components[component_type] = component
        
    def get_component(self, component_type):
        return self.components.get(component_type)
        
    def has_component(self, component_type):
        return component_type in self.components
        
    def remove_component(self, component_type):
        if component_type in self.components:
            del self.components[component_type]
