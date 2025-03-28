from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from ..component import Component

@dataclass
class BehaviorComponent(Component):
    """Component for agent behavior"""
    state: str = "idle"  # Current behavior state
    target: Optional[int] = None  # Target entity ID if any
    properties: Dict[str, Any] = field(default_factory=dict)  # Additional properties
