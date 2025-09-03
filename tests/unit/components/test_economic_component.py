"""
Unit tests for EconomicComponent
"""

import pytest
from src.core.ecs.components.economic import EconomicComponent


@pytest.mark.unit
class TestEconomicComponent:
    """Test EconomicComponent functionality."""
    
    def test_initialization(self):
        """Test component initialization with default values."""
        component = EconomicComponent(entity_id=1)
        
        assert component.entity_id == 1
        assert component.workplace_id is None
        assert component.investments == []
        assert component.shopping_target is None
        assert component.seeking_employment is False
        assert component.seeking_investment is False
        assert component.seeking_to_sell is False
    
    def test_initialization_with_parameters(self):
        """Test component initialization with custom values."""
        investments = [{"target": 42, "amount": 100, "expected_return": 0.05}]
        component = EconomicComponent(
            entity_id=99,
            workplace_id=5,
            investments=investments,
            shopping_target=10,
            seeking_employment=True,
            seeking_investment=True,
            seeking_to_sell=True
        )
        
        assert component.entity_id == 99
        assert component.workplace_id == 5
        assert component.investments == investments
        assert component.shopping_target == 10
        assert component.seeking_employment is True
        assert component.seeking_investment is True
        assert component.seeking_to_sell is True
    
    def test_workplace_assignment(self):
        """Test workplace assignment and updates."""
        component = EconomicComponent(entity_id=1)
        
        # Assign workplace
        component.workplace_id = 42
        assert component.workplace_id == 42
        
        # Change workplace
        component.workplace_id = 99
        assert component.workplace_id == 99
        
        # Unemployed
        component.workplace_id = None
        assert component.workplace_id is None
    
    def test_investment_management(self):
        """Test investment list management."""
        component = EconomicComponent(entity_id=1)
        
        # Add investment
        investment1 = {"target": 10, "amount": 50, "expected_return": 0.03}
        component.investments.append(investment1)
        assert len(component.investments) == 1
        assert component.investments[0] == investment1
        
        # Add another investment
        investment2 = {"target": 20, "amount": 100, "expected_return": 0.05}
        component.investments.append(investment2)
        assert len(component.investments) == 2
        
        # Remove investment
        component.investments.remove(investment1)
        assert len(component.investments) == 1
        assert component.investments[0] == investment2
    
    def test_shopping_target(self):
        """Test shopping target management."""
        component = EconomicComponent(entity_id=1)
        
        # Set shopping target
        component.shopping_target = 15
        assert component.shopping_target == 15
        
        # Change shopping target
        component.shopping_target = 25
        assert component.shopping_target == 25
        
        # Clear shopping target
        component.shopping_target = None
        assert component.shopping_target is None
    
    def test_economic_behavior_flags(self):
        """Test economic behavior flag modifications."""
        component = EconomicComponent(entity_id=1)
        
        # Test employment seeking
        component.seeking_employment = True
        assert component.seeking_employment is True
        component.seeking_employment = False
        assert component.seeking_employment is False
        
        # Test investment seeking
        component.seeking_investment = True
        assert component.seeking_investment is True
        component.seeking_investment = False
        assert component.seeking_investment is False
        
        # Test selling seeking
        component.seeking_to_sell = True
        assert component.seeking_to_sell is True
        component.seeking_to_sell = False
        assert component.seeking_to_sell is False
    
    def test_complex_investment_scenarios(self):
        """Test complex investment scenarios."""
        component = EconomicComponent(entity_id=1)
        
        # Multiple investment types
        investments = [
            {"type": "workplace", "target": 10, "amount": 100, "expected_return": 0.05},
            {"type": "farm", "target": 20, "amount": 50, "expected_return": 0.03},
            {"type": "social", "target": 30, "amount": 25, "expected_return": 0.02}
        ]
        component.investments = investments
        
        # Test total investment calculation
        total_invested = sum(inv["amount"] for inv in component.investments)
        assert total_invested == 175
        
        # Test investment filtering
        workplace_investments = [inv for inv in component.investments if inv["type"] == "workplace"]
        assert len(workplace_investments) == 1
        assert workplace_investments[0]["target"] == 10
    
    def test_component_state_transitions(self):
        """Test realistic state transitions for economic behavior."""
        component = EconomicComponent(entity_id=1)
        
        # Unemployed agent seeking work
        component.seeking_employment = True
        assert component.workplace_id is None
        assert component.seeking_employment is True
        
        # Gets employed
        component.workplace_id = 5
        component.seeking_employment = False
        assert component.workplace_id == 5
        assert component.seeking_employment is False
        
        # Starts investing surplus income
        component.seeking_investment = True
        investment = {"target": 10, "amount": 50, "expected_return": 0.04}
        component.investments.append(investment)
        assert len(component.investments) == 1
        assert component.seeking_investment is True
        
        # No longer seeking investment after making one
        component.seeking_investment = False
        assert component.seeking_investment is False
    
    def test_investments_list_isolation(self):
        """Test that investment lists are isolated between components."""
        component1 = EconomicComponent(entity_id=1)
        component2 = EconomicComponent(entity_id=2)
        
        # Add investment to first component
        investment1 = {"target": 10, "amount": 50, "expected_return": 0.03}
        component1.investments.append(investment1)
        
        # Second component should have empty investments
        assert len(component1.investments) == 1
        assert len(component2.investments) == 0
        assert component1.investments is not component2.investments
    
    @pytest.mark.parametrize("workplace_id", [None, 1, 5, 10, 100])
    def test_workplace_ids(self, workplace_id):
        """Test component with various workplace IDs."""
        component = EconomicComponent(entity_id=1, workplace_id=workplace_id)
        assert component.workplace_id == workplace_id
    
    def test_investment_validation(self):
        """Test investment data structure validation."""
        component = EconomicComponent(entity_id=1)
        
        # Valid investment structure
        valid_investment = {
            "target": 42,
            "amount": 100,
            "expected_return": 0.05,
            "timestamp": 1000,
            "status": "active"
        }
        
        component.investments.append(valid_investment)
        assert len(component.investments) == 1
        assert component.investments[0]["target"] == 42
        assert component.investments[0]["amount"] == 100
        assert component.investments[0]["expected_return"] == 0.05