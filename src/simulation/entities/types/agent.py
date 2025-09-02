from dataclasses import dataclass
from typing import Tuple, Optional, Any
from ..entity import Entity
from constants import EntityType, Gender, ActionType, asset_map
from src.simulation.genetics.genome import Genome
import random
import pygame

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
    previous_action: Optional[ActionType] = None
    mate_target: Optional['Agent'] = None
    size: Tuple[int, int]
    brain: Any = None  # Will be set by BehaviorSystem
    corruption_level: float = 0.0  # Added corruption level for tracking agent's behavior

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
        self.previous_action = None
        self.size = (64, 64)
        # Initialize corruption level from genome
        self.corruption_level = self.genome.corruption
        
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
        corruption_level = "high" if self.corruption_level > 0.6 else "medium" if self.corruption_level > 0.3 else "low"
        
        return f"{energy_level}_{money_level}_{mood_level}_{corruption_level}"

    @property
    def current_action(self):
        return self._current_action
        
    @current_action.setter
    def current_action(self, value):
        self._current_action = value
        # We'll update visibility directly in the update method

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
