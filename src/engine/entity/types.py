from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Tuple, Optional, Any
from .entity import Entity
from src.constants import EntityType, Gender, ActionType
import random
import pygame

from src.population.genome import Genome
from src.engine.assets.manager import AssetManager
from src.constants import asset_map
@dataclass
class Agent(Entity):
    is_alive: bool
    genome: Genome
    age: int
    energy: float
    money: float
    mood: float
    generation: int
    offspring_generations: int 
    offspring_count: int
    position: Tuple[int, int]
    current_action: Optional[ActionType] = None
    mate_target: Optional['Agent'] = None
    size: Tuple[int, int]
    brain: Any = None  # Will be set by BehaviorSystem

    def __init__(self, idx: int, screen: pygame.Surface):
        self.is_alive = True
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        self.genome = Genome(gender, idx)
        position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        entity_type = EntityType.PERSON_MALE if self.genome.gender == Gender.MALE else EntityType.PERSON_FEMALE
        super().__init__(entity_type=entity_type, position=position)
        self.id = idx
        self.screen = screen
        self.age = 0
        self.energy = 100.0
        self.money = 50.0
        self.mood = 0.0
        self.generation = 0 # Related to Offspring/Birth
        self.offspring_generations = 0
        self.offspring_count = 0
        self.current_action = None
        self.mate_target = None
        self.size = (64, 64)
        
        # Flag to control whether this agent uses neural network or Q-table
        self.genome.use_neural_network = random.random() < 0.5  # 50% chance initially

        # Preload all state assets for this entity type
        self.preload_state_assets()
        
        # Set initial state
        self.update_asset_based_on_state()

    def __hash__(self):
        """Make Agent hashable by using its ID"""
        return hash(self.id if hasattr(self, 'id') else id(self))
    
    def __eq__(self, other):
        """Equality check to complement the hash method"""
        if not isinstance(other, Agent):
            return False
        return (hasattr(self, 'id') and hasattr(other, 'id') and 
                self.id == other.id)
    
    def clear_references(self):
        """Clear any references that might cause memory leaks"""
        # Reset attributes that might hold references
        self.assets = {}
        if hasattr(self, 'target'):
            self.target = None

    def get_state_representation(self) -> str:
        """Returns a string representation of the agent's current state for Q-learning"""
        energy_level = "high" if self.energy > 70 else "medium" if self.energy > 30 else "low"
        money_level = "high" if self.money > 70 else "medium" if self.money > 30 else "low"
        mood_level = "positive" if self.mood > 0.3 else "negative" if self.mood < -0.3 else "neutral"
        
        return f"{energy_level}_{money_level}_{mood_level}"

    def update(self):
        self.render_all()

    @property
    def current_action(self):
        return self._current_action
        
    @current_action.setter
    def current_action(self, value):
        self._current_action = value
        if value and hasattr(self, 'update_asset_based_on_state'):
            # Convert enum value to string if needed
            action_str = value.value if hasattr(value, 'value') else value
            self.update_asset_based_on_state(action_str)

    def preload_state_assets(self):
        """Preload all possible state assets for this entity type"""
        if self.entity_type not in asset_map:
            return
        
        asset_config = asset_map[self.entity_type]
        
        # Load the default asset
        self.load_asset(asset_config["name"], asset_config["path"])
        
        # Load all state-specific assets
        for state, path in asset_config.items():
            if state != "name" and state != "path" and isinstance(path, str):
                self.load_asset(state, path)
        
        # Scale all loaded assets to the entity's size
        for asset_name in list(self.assets.keys()):
            self.scale_asset(asset_name, self.size[0], self.size[1])

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
        return len(self.current_workers) >= self.capacity

    @property
    def animation_key(self):
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

class Food(Entity):
    def __init__(self, screen: pygame.Surface):
        self.entity_type = EntityType.FOOD
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
        if not isinstance(other, Food):
            return False
        return id(self) == id(other)
    
    def clear_references(self):
        """Clear any references that might cause memory leaks"""
        self.assets = {}
