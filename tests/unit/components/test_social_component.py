"""
Unit tests for Social Component and SocialRelationship
"""

import pytest
from src.core.ecs.components.social import Social, SocialRelationship


@pytest.mark.unit
class TestSocialRelationship:
    """Test SocialRelationship functionality."""
    
    def test_initialization(self):
        """Test relationship initialization."""
        relationship = SocialRelationship(target_id=42)
        
        assert relationship.target_id == 42
        assert relationship.trust == 0.0
        assert relationship.affinity == 0.0
        assert relationship.interaction_count == 0
        assert relationship.successful_interactions == 0
        assert relationship.last_interaction_type is None
        assert relationship.last_interaction_time == 0
        assert relationship.history == []
    
    def test_trust_update(self):
        """Test trust value updates."""
        relationship = SocialRelationship(target_id=1)
        
        # Positive trust update
        relationship.update_trust(0.3)
        assert relationship.trust == 0.3
        
        # Negative trust update
        relationship.update_trust(-0.5)
        assert relationship.trust == -0.2
        
        # Test clamping at maximum
        relationship.update_trust(2.0)
        assert relationship.trust == 1.0  # Should be clamped
        
        # Test clamping at minimum
        relationship.update_trust(-3.0)
        assert relationship.trust == -1.0  # Should be clamped
    
    def test_trust_update_with_max_change(self):
        """Test trust updates with maximum change limits."""
        relationship = SocialRelationship(target_id=1)
        
        # Large positive change should be capped
        relationship.update_trust(0.5, max_change=0.1)
        assert relationship.trust == 0.1
        
        # Large negative change should be capped
        relationship.update_trust(-0.5, max_change=0.1)
        assert relationship.trust == 0.0  # 0.1 - 0.1 = 0.0
    
    def test_affinity_update(self):
        """Test affinity value updates."""
        relationship = SocialRelationship(target_id=1)
        
        # Positive affinity update
        relationship.update_affinity(0.4)
        assert relationship.affinity == 0.4
        
        # Negative affinity update
        relationship.update_affinity(-0.6)
        assert relationship.affinity == -0.2
        
        # Test clamping
        relationship.update_affinity(2.0)
        assert relationship.affinity == 1.0
        relationship.update_affinity(-3.0)
        assert relationship.affinity == -1.0
    
    def test_record_interaction(self):
        """Test interaction recording."""
        relationship = SocialRelationship(target_id=1)
        
        # Record successful interaction
        relationship.record_interaction("trade", True, 100)
        
        assert relationship.interaction_count == 1
        assert relationship.successful_interactions == 1
        assert relationship.last_interaction_type == "trade"
        assert relationship.last_interaction_time == 100
        assert len(relationship.history) == 1
        assert relationship.history[0] == ("trade", True, 100)
    
    def test_record_multiple_interactions(self):
        """Test recording multiple interactions."""
        relationship = SocialRelationship(target_id=1)
        
        # Record multiple interactions
        relationship.record_interaction("trade", True, 100)
        relationship.record_interaction("gift", False, 200)
        relationship.record_interaction("work", True, 300)
        
        assert relationship.interaction_count == 3
        assert relationship.successful_interactions == 2
        assert relationship.last_interaction_type == "work"
        assert relationship.last_interaction_time == 300
        assert len(relationship.history) == 3
    
    def test_history_limit(self):
        """Test that history is limited to 10 interactions."""
        relationship = SocialRelationship(target_id=1)
        
        # Add 15 interactions
        for i in range(15):
            relationship.record_interaction(f"action_{i}", i % 2 == 0, i * 100)
        
        # History should only contain last 10
        assert len(relationship.history) == 10
        assert relationship.history[0][0] == "action_5"  # First in history should be action_5
        assert relationship.history[-1][0] == "action_14"  # Last should be action_14
        
        # But total counts should reflect all interactions
        assert relationship.interaction_count == 15
        assert relationship.successful_interactions == 8  # 0,2,4,6,8,10,12,14 (8 successful)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        relationship = SocialRelationship(target_id=1)
        
        # No interactions
        assert relationship.calculate_success_rate() == 0.0
        
        # All successful
        relationship.record_interaction("trade", True, 100)
        relationship.record_interaction("gift", True, 200)
        assert relationship.calculate_success_rate() == 1.0
        
        # Mixed success
        relationship.record_interaction("work", False, 300)
        relationship.record_interaction("help", False, 400)
        assert relationship.calculate_success_rate() == 0.5  # 2 successful out of 4


@pytest.mark.unit
class TestSocial:
    """Test Social component functionality."""
    
    def test_initialization(self):
        """Test social component initialization."""
        social = Social(entity_id=42)
        
        assert social.entity_id == 42
        assert social.relationships == {}
        assert social.social_status == 0.0
        assert social.community_id is None
        assert social.trust_threshold == 0.3
        assert social.affinity_threshold == 0.2
        assert social.extraversion == 0.5
        assert social.agreeableness == 0.5
        assert social.reciprocity == 0.5
    
    def test_get_relationship(self):
        """Test getting/creating relationships."""
        social = Social(entity_id=1)
        
        # Get new relationship (should create)
        rel = social.get_relationship(42)
        assert isinstance(rel, SocialRelationship)
        assert rel.target_id == 42
        assert 42 in social.relationships
        
        # Get existing relationship (should return same)
        rel2 = social.get_relationship(42)
        assert rel is rel2
    
    def test_status_update(self):
        """Test social status updates."""
        social = Social(entity_id=1)
        
        # Positive status change
        social.update_status(0.3)
        assert social.social_status == 0.3
        
        # Negative status change
        social.update_status(-0.5)
        assert social.social_status == -0.2
        
        # Test clamping
        social.update_status(2.0)
        assert social.social_status == 1.0
        social.update_status(-3.0)
        assert social.social_status == -1.0
    
    def test_trusted_agents(self):
        """Test getting list of trusted agents."""
        social = Social(entity_id=1)
        
        # Create relationships with different trust levels
        social.get_relationship(10).update_trust(0.5)  # Trusted
        social.get_relationship(20).update_trust(0.1)  # Not enough trust
        social.get_relationship(30).update_trust(0.4)  # Trusted
        social.get_relationship(40).update_trust(-0.2)  # Distrusted
        
        trusted = social.get_trusted_agents()
        assert 10 in trusted
        assert 30 in trusted
        assert 20 not in trusted
        assert 40 not in trusted
        assert len(trusted) == 2
    
    def test_trusted_agents_custom_threshold(self):
        """Test getting trusted agents with custom threshold."""
        social = Social(entity_id=1)
        
        social.get_relationship(10).update_trust(0.6)
        social.get_relationship(20).update_trust(0.4)
        social.get_relationship(30).update_trust(0.2)
        
        # Default threshold (0.3)
        trusted_default = social.get_trusted_agents()
        assert len(trusted_default) == 2  # 10 and 20
        
        # Custom higher threshold
        trusted_high = social.get_trusted_agents(min_trust=0.5)
        assert len(trusted_high) == 1  # Only 10
        assert 10 in trusted_high
    
    def test_distrusted_agents(self):
        """Test getting list of distrusted agents."""
        social = Social(entity_id=1)
        
        social.get_relationship(10).update_trust(-0.5)  # Distrusted
        social.get_relationship(20).update_trust(-0.2)  # Not enough distrust
        social.get_relationship(30).update_trust(-0.4)  # Distrusted
        social.get_relationship(40).update_trust(0.2)   # Trusted
        
        distrusted = social.get_distrusted_agents()
        assert 10 in distrusted
        assert 30 in distrusted
        assert 20 not in distrusted
        assert 40 not in distrusted
        assert len(distrusted) == 2
    
    def test_liked_agents(self):
        """Test getting list of liked agents."""
        social = Social(entity_id=1)
        
        social.get_relationship(10).update_affinity(0.5)   # Liked
        social.get_relationship(20).update_affinity(0.1)   # Not enough affinity
        social.get_relationship(30).update_affinity(0.4)   # Liked
        social.get_relationship(40).update_affinity(-0.2)  # Disliked
        
        liked = social.get_liked_agents()
        assert 10 in liked
        assert 30 in liked
        assert 20 not in liked
        assert 40 not in liked
        assert len(liked) == 2
    
    def test_disliked_agents(self):
        """Test getting list of disliked agents."""
        social = Social(entity_id=1)
        
        social.get_relationship(10).update_affinity(-0.5)  # Disliked
        social.get_relationship(20).update_affinity(-0.2)  # Not enough dislike
        social.get_relationship(30).update_affinity(-0.4)  # Disliked
        social.get_relationship(40).update_affinity(0.2)   # Liked
        
        disliked = social.get_disliked_agents()
        assert 10 in disliked
        assert 30 in disliked
        assert 20 not in disliked
        assert 40 not in disliked
        assert len(disliked) == 2
    
    def test_record_interaction(self):
        """Test recording interactions with relationship updates."""
        social = Social(entity_id=1)
        
        # Record interaction with trust and affinity changes
        social.record_interaction(
            target_id=42,
            interaction_type="trade",
            successful=True,
            time=100,
            trust_change=0.1,
            affinity_change=0.2
        )
        
        relationship = social.relationships[42]
        assert relationship.interaction_count == 1
        assert relationship.successful_interactions == 1
        assert relationship.trust == 0.1
        assert relationship.affinity == 0.2
        assert relationship.last_interaction_type == "trade"
    
    def test_calculate_compatibility(self):
        """Test compatibility calculation between agents."""
        social1 = Social(entity_id=1)
        social2 = Social(entity_id=2)
        
        # Set up social2 properties
        social2.social_status = 0.2
        social2.extraversion = 0.6
        social2.agreeableness = 0.4
        social2.reciprocity = 0.7
        
        # Test compatibility without existing relationship
        compatibility = social1.calculate_compatibility(social2)
        assert isinstance(compatibility, float)
        assert -1.0 <= compatibility <= 1.0
    
    def test_calculate_compatibility_with_relationship(self):
        """Test compatibility with existing relationship."""
        social1 = Social(entity_id=1)
        social2 = Social(entity_id=2)
        
        # Create existing relationship
        social1.get_relationship(2).update_trust(0.4)
        social1.get_relationship(2).update_affinity(0.3)
        
        # Set similar social traits
        social2.social_status = 0.0  # Similar to default 0.0
        social2.extraversion = 0.5   # Same as default
        social2.agreeableness = 0.5  # Same as default
        social2.reciprocity = 0.5    # Same as default
        
        compatibility = social1.calculate_compatibility(social2)
        assert compatibility > 0  # Should be positive due to similar traits and good relationship
    
    def test_calculate_compatibility_none_target(self):
        """Test compatibility calculation with None target."""
        social = Social(entity_id=1)
        assert social.calculate_compatibility(None) == 0.0
    
    def test_multiple_relationships_management(self):
        """Test managing multiple relationships simultaneously."""
        social = Social(entity_id=1)
        
        # Create multiple relationships
        targets = [10, 20, 30, 40, 50]
        for target in targets:
            rel = social.get_relationship(target)
            rel.update_trust(0.1 * target)  # Different trust levels
            rel.update_affinity(0.05 * target)  # Different affinity levels
        
        assert len(social.relationships) == 5
        
        # Test filtering works correctly
        trusted = social.get_trusted_agents(min_trust=2.0)  # Very high threshold
        assert 50 in trusted  # Only highest trust (5.0)
        
        liked = social.get_liked_agents(min_affinity=0.2)
        assert 40 in liked  # 0.2 affinity
        assert 50 in liked  # 0.25 affinity