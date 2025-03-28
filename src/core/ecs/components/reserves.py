from dataclasses import dataclass, field
from typing import Dict, Any
from ..component import Component

@dataclass
class ReservesComponent(Component):
    entity_id: int
    food: float = 0.0  # Current food reserves
    max_food: float = 100.0  # Maximum food storage
    
    def add_food(self, amount: float) -> float:
        """Add food to reserves, returns amount actually stored"""
        space_left = self.max_food - self.food
        stored_amount = min(amount, space_left)
        self.food += stored_amount
        return stored_amount
    
    def remove_food(self, amount: float) -> float:
        """Remove food from reserves, returns amount actually removed"""
        available = min(amount, self.food)
        return available