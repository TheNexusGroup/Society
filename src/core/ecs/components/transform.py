from dataclasses import dataclass
from typing import Tuple
from ..component import Component

@dataclass
class TransformComponent(Component):
    """Component for position and movement"""
    position: Tuple[float, float] = (0, 0)
    velocity: Tuple[float, float] = (0, 0)
    rotation: float = 0
    scale: float = 1.0