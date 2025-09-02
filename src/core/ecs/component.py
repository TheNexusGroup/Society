from dataclasses import dataclass

@dataclass
class Component:
    """Base class for all ECS components"""
    entity_id: int