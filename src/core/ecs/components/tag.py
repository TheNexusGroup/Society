from dataclasses import dataclass
from ..component import Component

@dataclass
class TagComponent(Component):
    """Component for tagging entities by type"""
    tag: str = ""  # Tag name like "agent", "food", "work"