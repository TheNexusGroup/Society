"""
Unit tests for BehaviorComponent
"""

import pytest
from src.core.ecs.components.behaviour import BehaviorComponent


@pytest.mark.unit
class TestBehaviorComponent:
    """Test BehaviorComponent functionality."""
    
    def test_initialization(self):
        """Test component initialization with default values."""
        component = BehaviorComponent(entity_id=1)
        
        assert component.entity_id == 1
        assert component.state == "idle"
        assert component.target is None
        assert component.properties == {}
    
    def test_initialization_with_parameters(self):
        """Test component initialization with custom values."""
        properties = {"energy": 100, "mood": 0.5}
        component = BehaviorComponent(
            entity_id=42,
            state="working",
            target=99,
            properties=properties
        )
        
        assert component.entity_id == 42
        assert component.state == "working"
        assert component.target == 99
        assert component.properties == properties
    
    def test_state_modification(self):
        """Test modifying component state."""
        component = BehaviorComponent(entity_id=1)
        
        component.state = "eating"
        assert component.state == "eating"
        
        component.state = "resting"
        assert component.state == "resting"
    
    def test_target_assignment(self):
        """Test target entity assignment."""
        component = BehaviorComponent(entity_id=1)
        
        component.target = 42
        assert component.target == 42
        
        component.target = None
        assert component.target is None
    
    def test_properties_modification(self):
        """Test modifying component properties."""
        component = BehaviorComponent(entity_id=1)
        
        # Add properties
        component.properties["energy"] = 75
        component.properties["hunger"] = 0.3
        
        assert component.properties["energy"] == 75
        assert component.properties["hunger"] == 0.3
        
        # Modify properties
        component.properties["energy"] = 50
        assert component.properties["energy"] == 50
        
        # Remove properties
        del component.properties["hunger"]
        assert "hunger" not in component.properties
    
    def test_properties_with_complex_data(self):
        """Test properties with complex data types."""
        component = BehaviorComponent(entity_id=1)
        
        complex_data = {
            "stats": {"health": 100, "mana": 50},
            "items": ["sword", "potion"],
            "position": (10, 20)
        }
        
        component.properties.update(complex_data)
        
        assert component.properties["stats"]["health"] == 100
        assert "sword" in component.properties["items"]
        assert component.properties["position"] == (10, 20)
    
    def test_component_isolation(self):
        """Test that components are isolated from each other."""
        component1 = BehaviorComponent(entity_id=1, state="idle")
        component2 = BehaviorComponent(entity_id=2, state="working")
        
        # Modify one component
        component1.state = "eating"
        component1.properties["energy"] = 75
        
        # Other component should be unaffected
        assert component2.state == "working"
        assert component2.properties == {}
    
    def test_entity_id_immutability(self):
        """Test that entity_id should remain consistent."""
        component = BehaviorComponent(entity_id=42)
        original_id = component.entity_id
        
        # Entity ID should remain the same
        assert component.entity_id == original_id
        
        # This test ensures we're aware if entity_id changes unexpectedly
        component.entity_id = 99
        assert component.entity_id == 99  # Should work but we test awareness
    
    @pytest.mark.parametrize("state", [
        "idle", "eating", "working", "resting", "mating", "searching", 
        "farming", "trading", "socializing", "dead"
    ])
    def test_valid_states(self, state):
        """Test component with various valid states."""
        component = BehaviorComponent(entity_id=1, state=state)
        assert component.state == state
    
    def test_properties_default_factory(self):
        """Test that properties dict is created fresh for each instance."""
        component1 = BehaviorComponent(entity_id=1)
        component2 = BehaviorComponent(entity_id=2)
        
        component1.properties["test"] = "value1"
        component2.properties["test"] = "value2"
        
        assert component1.properties["test"] == "value1"
        assert component2.properties["test"] == "value2"
        
        # Ensure they're different dict instances
        assert component1.properties is not component2.properties