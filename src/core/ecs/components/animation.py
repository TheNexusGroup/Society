from dataclasses import dataclass
from typing import Any, Tuple
from ..component import Component

@dataclass
class AnimationComponent(Component):
    """Component for animating entities"""
    animation: Any = None  # Holds the Animation
    position: Tuple[int, int] = (0, 0)
    active: bool = True
    name: str = ""