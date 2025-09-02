from typing import Dict, List, Tuple, Any, Optional
from ..component import Component

class SocialRelationship:
    def __init__(self, target_id: int):
        self.target_id = target_id
        self.trust = 0.0  # -1.0 to 1.0, negative is distrust, positive is trust
        self.affinity = 0.0  # -1.0 to 1.0, negative is dislike, positive is like
        self.interaction_count = 0
        self.successful_interactions = 0
        self.last_interaction_type = None
        self.last_interaction_time = 0
        self.history = []  # Recent interactions
    
    def update_trust(self, change: float, max_change: float = 0.2):
        """Update trust with capped change amount"""
        self.trust += max(min(change, max_change), -max_change)
        self.trust = max(min(self.trust, 1.0), -1.0)  # Clamp between -1 and 1
    
    def update_affinity(self, change: float, max_change: float = 0.2):
        """Update affinity with capped change amount"""
        self.affinity += max(min(change, max_change), -max_change)
        self.affinity = max(min(self.affinity, 1.0), -1.0)  # Clamp between -1 and 1
    
    def record_interaction(self, interaction_type: str, successful: bool, time: int):
        """Record an interaction with this agent"""
        self.interaction_count += 1
        if successful:
            self.successful_interactions += 1
        
        self.last_interaction_type = interaction_type
        self.last_interaction_time = time
        
        # Add to history, keeping only the last 10 interactions
        self.history.append((interaction_type, successful, time))
        if len(self.history) > 10:
            self.history.pop(0)
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate of interactions"""
        if self.interaction_count == 0:
            return 0.0
        return self.successful_interactions / self.interaction_count

class Social(Component):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.relationships: Dict[int, SocialRelationship] = {}
        self.social_status = 0.0  # -1.0 to 1.0, negative is low status, positive is high status
        self.community_id = None  # Optional community/group membership
        
        # Social preferences
        self.trust_threshold = 0.3  # Minimum trust to consider cooperative actions
        self.affinity_threshold = 0.2  # Minimum affinity for friendly interactions
        
        # Social traits (can be influenced by genome)
        self.extraversion = 0.5  # 0.0 to 1.0, tendency to seek social interactions
        self.agreeableness = 0.5  # 0.0 to 1.0, tendency to cooperate
        self.reciprocity = 0.5  # 0.0 to 1.0, tendency to return favors/grudges
    
    def get_relationship(self, target_id: int) -> SocialRelationship:
        """Get or create relationship with target"""
        if target_id not in self.relationships:
            self.relationships[target_id] = SocialRelationship(target_id)
        return self.relationships[target_id]
    
    def update_status(self, change: float):
        """Update social status"""
        self.social_status += change
        self.social_status = max(min(self.social_status, 1.0), -1.0)  # Clamp between -1 and 1
    
    def get_trusted_agents(self, min_trust: float = 0.3) -> List[int]:
        """Get list of agents this agent trusts"""
        return [agent_id for agent_id, rel in self.relationships.items() 
                if rel.trust >= min_trust]
    
    def get_distrusted_agents(self, max_trust: float = -0.3) -> List[int]:
        """Get list of agents this agent distrusts"""
        return [agent_id for agent_id, rel in self.relationships.items() 
                if rel.trust <= max_trust]
    
    def get_liked_agents(self, min_affinity: float = 0.3) -> List[int]:
        """Get list of agents this agent likes"""
        return [agent_id for agent_id, rel in self.relationships.items() 
                if rel.affinity >= min_affinity]
    
    def get_disliked_agents(self, max_affinity: float = -0.3) -> List[int]:
        """Get list of agents this agent dislikes"""
        return [agent_id for agent_id, rel in self.relationships.items() 
                if rel.affinity <= max_affinity]
    
    def record_interaction(self, target_id: int, interaction_type: str, 
                          successful: bool, time: int,
                          trust_change: float = 0.0, affinity_change: float = 0.0):
        """Record an interaction with another agent and update relationship"""
        relationship = self.get_relationship(target_id)
        relationship.record_interaction(interaction_type, successful, time)
        
        if trust_change != 0.0:
            relationship.update_trust(trust_change)
        
        if affinity_change != 0.0:
            relationship.update_affinity(affinity_change)
    
    def calculate_compatibility(self, target_social) -> float:
        """Calculate social compatibility with another agent"""
        if not target_social:
            return 0.0
        
        # Base compatibility starts neutral
        compatibility = 0.0
        
        # If we already have a relationship, use that as baseline
        if target_social.entity_id in self.relationships:
            relationship = self.relationships[target_social.entity_id]
            compatibility += (relationship.trust + relationship.affinity) / 2
        
        # Similar social status increases compatibility
        status_diff = abs(self.social_status - target_social.social_status)
        compatibility += (1.0 - status_diff) * 0.3
        
        # Similar social traits increases compatibility (birds of a feather)
        trait_similarity = (
            (1.0 - abs(self.extraversion - target_social.extraversion)) +
            (1.0 - abs(self.agreeableness - target_social.agreeableness)) +
            (1.0 - abs(self.reciprocity - target_social.reciprocity))
        ) / 3.0
        compatibility += trait_similarity * 0.3
        
        return max(min(compatibility, 1.0), -1.0)  # Clamp between -1 and 1
