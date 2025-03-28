from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ..component import Component

@dataclass
class EconomicComponent(Component):
    entity_id: int
    workplace_id: Optional[int] = None
    investments: List[Dict] = field(default_factory=list)
    shopping_target: Optional[int] = None
    
    # Economic behavior flags
    seeking_employment: bool = False
    seeking_investment: bool = False
    seeking_to_sell: bool = False
