from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
import pygame

@dataclass
class Component:
    """Base class for all components"""
    entity_id: int

@dataclass
class RenderComponent(Component):
    """Component for entity rendering"""
    asset: Any  # Asset or Animation
    position: Tuple[float, float] = (0.0, 0.0)
    size: Tuple[int, int] = (64, 64)
    visible: bool = True
    z_index: int = 0

@dataclass
class AnimationComponent(Component):
    """Component for entity animations"""
    animation: Any
    position: Tuple[int, int]
    active: bool = True

@dataclass
class TransformComponent(Component):
    """Component for position, rotation, scale"""
    position: Tuple[int, int]
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)
    velocity: Tuple[float, float] = (0.0, 0.0)

@dataclass
class BehaviorComponent(Component):
    """Component for entity behavior and AI"""
    state: str = "idle"
    target: Optional[int] = None  # Target entity ID
    target_action: Optional[str] = None  # Action chosen by Q-learning
    action_cooldown: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TagComponent(Component):
    """Component for entity type identification"""
    tag: str
