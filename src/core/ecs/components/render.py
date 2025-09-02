from dataclasses import dataclass, field
from typing import Any, List, Tuple
from ..component import Component

@dataclass
class AssetReference:
    """Reference to an asset with state key"""
    key: str
    asset: Any

@dataclass
class RenderComponent(Component):
    """Component for rendering entities"""
    asset: Any = None  # Holds the Asset or Animation
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (64, 64)
    visible: bool = True
    alt_assets: List[AssetReference] = field(default_factory=list)
    
    def add_asset_for_state(self, state_key, asset):
        """Add an asset to use for a specific state"""
        self.alt_assets.append(AssetReference(state_key, asset))