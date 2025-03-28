from dataclasses import dataclass
from ..entity import Entity
from constants import EntityType
import pygame
import random

@dataclass
class WorkPlace(Entity):
    def __init__(self, screen: pygame.Surface):
        self.entity_type = EntityType.WORK
        self.position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        self.screen = screen
        super().__init__(entity_type=self.entity_type, position=self.position)
        capacity = random.randint(1, 5)
        self.capacity = capacity
        self.current_workers = []
        self.size = (64, 64)
        
    def reset(self, screen: pygame.Surface):
        self.position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        self.screen = screen
        self.capacity = random.randint(1, 5)
        self.current_workers = []
        return self

    @property
    def is_full(self):
        if hasattr(self, 'ecs_id'):
            workplace_comp = getattr(self, 'world', None) and self.world.ecs.get_component(self.ecs_id, "workplace")
            if workplace_comp:
                return len(workplace_comp.workers) >= workplace_comp.max_workers
        return len(self.current_workers) >= self.capacity

    @property
    def animation_key(self):
        if hasattr(self, 'ecs_id'):
            workplace_comp = getattr(self, 'world', None) and self.world.ecs.get_component(self.ecs_id, "workplace")
            if workplace_comp:
                return "working" if workplace_comp.has_staff else None
        return "working" if self.current_workers else None

    def update(self):
        self.render_all()

    def __hash__(self):
        """Make WorkPlace hashable by using its memory ID"""
        return hash(id(self))
    
    def __eq__(self, other):
        """Equality check to complement the hash method"""
        if not isinstance(other, WorkPlace):
            return False
        return id(self) == id(other)
    
    def clear_references(self):
        """Clear any references that might cause memory leaks"""
        self.assets = {}