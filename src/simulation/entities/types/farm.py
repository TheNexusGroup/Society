from dataclasses import dataclass, field
from ..entity import Entity
from constants import EntityType
import random
import pygame


class Farm(Entity):
    def __init__(self, screen: pygame.Surface):
        self.entity_type = EntityType.FARM
        self.position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        self.screen = screen
        super().__init__(entity_type=self.entity_type, position=self.position)
        self.nutrition_value = random.uniform(10, 50)
        self.size = (64, 64)
    
    def reset(self, screen: pygame.Surface):
        self.position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        self.screen = screen
        self.nutrition_value = random.uniform(10, 50)
        return self
    
    def update(self):
        self.render_all()

    def __hash__(self):
        """Make Food hashable by using its memory ID"""
        return hash(id(self))
    
    def __eq__(self, other):
        """Equality check to complement the hash method"""
        if not isinstance(other, Farm):
            return False
        return id(self) == id(other)
    
    def clear_references(self):
        """Clear any references that might cause memory leaks"""
        self.assets = {}
