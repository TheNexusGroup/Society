from dataclasses import dataclass, field
from typing import Optional
from constants import FarmState
from ..component import Component

@dataclass
class FarmComponent(Component):
    entity_id: int
    farm_state: FarmState = FarmState.TILTH
    fertility: float = 1.0  # Multiplier for yield (1.0 = normal)
    size: int = 1  # Size of farm (affects max yield)
    planted_by: Optional[int] = None  # Entity ID of the agent that planted the farm

    # Farm stats that affect yield
    max_yield: int = 100
    growth_speed: float = 1.0  # Multiplier for growth speed
    
    def change_state(self, new_state: FarmState):
        self.farm_state = new_state
        return True
    
    def calculate_yield_amount(self, harvester_skill: float = 1.0):
        """Calculate the yield amount based on farm stats and harvester skill"""
        base_yield = self.max_yield * self.fertility
        return base_yield * harvester_skill
