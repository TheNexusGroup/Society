from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional
import numpy as np
from ..engine.entity import Entity, EntityType
import random
import pygame

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

class ActionType(Enum):
    EAT = "eat"
    WORK = "work"
    REST = "rest"
    MATE = "mate"
    SEARCH = "search"

class ResourceType(Enum):
    FOOD = "food"
    MONEY = "money"
    ENERGY = "energy"

class Genome:
    gender: Gender
    metabolism: float  # Rate at which energy is consumed
    stamina: float  # Ability to do actions
    learning_capacity: float  # Learning rate in Q-learning
    attraction_profile: float  # Threshold for seeking mate (-1 to 1)
    q_table: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def __init__(self, idx: int):
        self.idx = idx
        self.gender = Gender.MALE if idx % 2 == 0 else Gender.FEMALE
        self.metabolism = random.uniform(0.5, 1.5)
        self.stamina = random.uniform(0.5, 1.5)
        self.learning_capacity = random.uniform(0.1, 0.9)
        self.attraction_profile = random.uniform(-1, 1)
        self.q_table = {}

@dataclass
class Agent(Entity):
    genome: Genome
    age: int
    energy: float
    hunger: float
    money: float
    mood: float
    generation: int
    offspring_generations: int 
    offspring_count: int
    position: Tuple[int, int]
    current_action: Optional[ActionType]
    mate_target: Optional['Agent']
    size: Tuple[int, int]

    def __init__(self, idx: int, screen: pygame.Surface):
        self.genome = Genome(idx)
        position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        entity_type = EntityType.PERSON_MALE if self.genome.gender == Gender.MALE else EntityType.PERSON_FEMALE
        super().__init__(entity_type=entity_type, position=position)
        self.screen = screen
        self.age = 0
        self.energy = 100.0
        self.hunger = 0.0
        self.money = 50.0
        self.mood = 0.0
        self.generation = 0
        self.offspring_generations = 0
        self.offspring_count = 0
        self.current_action = None
        self.mate_target = None
        self.size = (32, 32)

    def get_state_representation(self) -> str:
        """Returns a string representation of the agent's current state for Q-learning"""
        hunger_level = "high" if self.hunger > 70 else "medium" if self.hunger > 30 else "low"
        energy_level = "high" if self.energy > 70 else "medium" if self.energy > 30 else "low"
        money_level = "high" if self.money > 70 else "medium" if self.money > 30 else "low"
        mood_level = "positive" if self.mood > 0.3 else "negative" if self.mood < -0.3 else "neutral"
        
        return f"{hunger_level}_{energy_level}_{money_level}_{mood_level}"

    def update(self):
        self.render_all()

class WorkPlace(Entity):
    def __init__(self, screen: pygame.Surface):
        self.entity_type = EntityType.WORK
        self.position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        self.screen = screen
        super().__init__(entity_type=self.entity_type, position=self.position)
        capacity = random.randint(1, 5)
        self.capacity = capacity
        self.current_workers = []
        
    @property
    def is_full(self):
        return len(self.current_workers) >= self.capacity

    @property
    def animation_key(self):
        return "working" if self.current_workers else None

    def update(self):
        self.render_all()

class Food(Entity):
    def __init__(self, screen: pygame.Surface):
        self.entity_type = EntityType.FOOD
        self.position = (random.randint(0, screen.get_width()), random.randint(0, screen.get_height()))
        self.screen = screen
        super().__init__(entity_type=self.entity_type, position=self.position)
        self.nutrition_value = random.uniform(10, 50)
    
    def update(self):
        self.render_all()
