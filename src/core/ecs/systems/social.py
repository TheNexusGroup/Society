# We want to build a social system that allows agents to interact with each other
# The idea is that they build up trust, as well as positive and negative memories
# about one another, that has an influence on their behaviours.
# This should integrate with trade, gift, mating, and even potential work/investment opportunities.
# In theory they might even enact violence, or also work together to achieve a common goal.

from ..system import System
from ..components.social import Social, SocialRelationship
import random
import math

class SocialSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.world = world
        self.interaction_types = {
            # Positive interactions
            'gift': {'trust_mod': 0.2, 'affinity_mod': 0.15},
            'trade': {'trust_mod': 0.1, 'affinity_mod': 0.05},
            'mate': {'trust_mod': 0.3, 'affinity_mod': 0.4},
            'work': {'trust_mod': 0.1, 'affinity_mod': 0.05},
            'invest': {'trust_mod': 0.2, 'affinity_mod': 0.1},
            # Negative interactions
            'violence': {'trust_mod': 0.4, 'affinity_mod': 0.5},
            'theft': {'trust_mod': 0.3, 'affinity_mod': 0.2},
            'scam_trade': {'trust_mod': 0.3, 'affinity_mod': 0.2},
            'work_sabotage': {'trust_mod': 0.25, 'affinity_mod': 0.15},
            'investment_fraud': {'trust_mod': 0.35, 'affinity_mod': 0.25}
        }
        self.time = 0  # Simulation time counter
        self.grudge_threshold = -0.7  # Trust below this means a grudge
        self.revenge_probability = 0.4  # Chance of revenge action if grudge exists
    
    def update(self, dt):
        """Update social relationships - decay old connections, update time"""
        self.time += dt
        
        # Process social components for relationship decay
        for entity_id, social in self.world.ecs.get_components("social"):
            self._decay_old_relationships(social)
            
            # Occasionally update social status based on relationships
            if random.random() < 0.01:  # 1% chance per update
                self._update_social_status(social)
    
    def register_interaction(self, agent_id, target_id, interaction_type, successful, details=None):
        """Register a social interaction between two agents"""
        # Get social components for both agents
        agent_social = self.world.ecs.get_component(agent_id, "social")
        target_social = self.world.ecs.get_component(target_id, "social")
        
        if not agent_social or not target_social:
            return False
        
        # Get interaction modifiers
        interaction = self.interaction_types.get(interaction_type, {'trust_mod': 0.0, 'affinity_mod': 0.0})
        
        # Calculate trust and affinity changes
        trust_change = interaction['trust_mod'] if successful else -interaction['trust_mod']
        affinity_change = interaction['affinity_mod'] if successful else -interaction['affinity_mod']
        
        # Apply agent's personality traits as modifiers
        trust_change *= (1.0 + agent_social.reciprocity - 0.5)  # Reciprocity increases/decreases impact
        affinity_change *= (1.0 + agent_social.agreeableness - 0.5)  # Agreeableness increases/decreases impact
        
        # Record interaction in both directions
        agent_social.record_interaction(target_id, interaction_type, successful, self.time, 
                                        trust_change, affinity_change)
        
        # Target's reciprocal reaction may be different
        target_trust_change = interaction['trust_mod'] if successful else -interaction['trust_mod']
        target_affinity_change = interaction['affinity_mod'] if successful else -interaction['affinity_mod']
        
        # Apply target's personality traits
        target_trust_change *= (1.0 + target_social.reciprocity - 0.5)
        target_affinity_change *= (1.0 + target_social.agreeableness - 0.5)
        
        target_social.record_interaction(agent_id, interaction_type, successful, self.time,
                                        target_trust_change, target_affinity_change)
        
        # Store in agent memories
        self._store_social_memory(agent_id, target_id, interaction_type, successful, details)
        self._store_social_memory(target_id, agent_id, interaction_type, successful, details)
        
        return True
    
    def get_relationship_score(self, agent_id, target_id):
        """Get relationship score between two agents (combined trust and affinity)"""
        agent_social = self.world.ecs.get_component(agent_id, "social")
        if not agent_social:
            return 0.0
        
        if target_id in agent_social.relationships:
            rel = agent_social.relationships[target_id]
            return (rel.trust + rel.affinity) / 2
        return 0.0
    
    def get_potential_partners(self, agent_id, min_score=0.3):
        """Find potential partners for cooperation/mating based on relationship score"""
        agent_social = self.world.ecs.get_component(agent_id, "social")
        if not agent_social:
            return []
        
        partners = []
        for target_id, rel in agent_social.relationships.items():
            score = (rel.trust + rel.affinity) / 2
            if score >= min_score:
                partners.append((target_id, score))
        
        # Sort by relationship score (highest first)
        partners.sort(key=lambda x: x[1], reverse=True)
        return partners
    
    def enhance_decision_making(self, agent_id, action_probs, nearby_agents):
        """Modify action probabilities based on social relationships"""
        agent_social = self.world.ecs.get_component(agent_id, "social")
        if not agent_social or not nearby_agents:
            return action_probs
        
        # Copy original probabilities
        modified_probs = action_probs.copy()
        
        # Calculate total relationship value for nearby agents
        total_rel_value = 0
        for nearby_id in nearby_agents:
            rel_score = self.get_relationship_score(agent_id, nearby_id)
            total_rel_value += rel_score + 1.0  # Add 1.0 to make values positive
        
        if total_rel_value > 0:
            # Increase social action probabilities based on relationships
            social_boost = min(total_rel_value / len(nearby_agents), 1.0)
            
            # Boost social actions if there are positive relationships
            if social_boost > 0.5:
                for action in ['gift-food', 'gift-money', 'trade-food-for-money', 
                               'trade-money-for-food', 'mate']:
                    if action in modified_probs:
                        modified_probs[action] *= (1.0 + social_boost)
            
            # Boost community-focused actions if extraversion is high
            if agent_social.extraversion > 0.6:
                for action in ['work', 'invest']:
                    if action in modified_probs:
                        modified_probs[action] *= (1.0 + agent_social.extraversion * 0.5)
        
        # Normalize probabilities
        total = sum(modified_probs.values())
        if total > 0:
            for action in modified_probs:
                modified_probs[action] /= total
        
        return modified_probs
    
    def find_best_interaction_target(self, agent_id, interaction_type, nearby_agents):
        """Find the best target for a specific interaction among nearby agents"""
        if not nearby_agents:
            return None
        
        agent_social = self.world.ecs.get_component(agent_id, "social")
        if not agent_social:
            return random.choice(nearby_agents)
        
        # Choose target based on relationship and interaction type
        best_target = None
        best_score = -float('inf')
        
        for target_id in nearby_agents:
            if target_id == agent_id:
                continue
                
            # Get relationship with this target
            if target_id in agent_social.relationships:
                rel = agent_social.relationships[target_id]
                
                # Calculate score based on interaction type
                score = 0
                if interaction_type in ['gift-food', 'gift-money']:
                    # Gifts are more likely to high-affinity agents
                    score = rel.affinity * 2 + rel.trust
                elif interaction_type in ['trade-food-for-money', 'trade-money-for-food']:
                    # Trades are more likely with high-trust agents
                    score = rel.trust * 2 + rel.affinity
                elif interaction_type == 'mate':
                    # Mating requires high affinity and trust
                    score = rel.affinity * 1.5 + rel.trust * 1.5
                    
                    # Check if target is compatible for mating
                    target_agent = self.world.get_entity_by_id(target_id)
                    agent = self.world.get_entity_by_id(agent_id)
                    if (target_agent and agent and 
                        hasattr(target_agent, 'genome') and hasattr(agent, 'genome')):
                        # Penalize same-gender mating attempts
                        if target_agent.genome.gender == agent.genome.gender:
                            score -= 5.0
                        
                # Add some randomness
                score += random.uniform(-0.2, 0.2)
                
                if score > best_score:
                    best_score = score
                    best_target = target_id
            else:
                # No existing relationship, might try with new agents
                # Lower score but still possible
                score = 0.1 + random.uniform(0, 0.3)
                if score > best_score:
                    best_score = score
                    best_target = target_id
        
        return best_target
    
    def _decay_old_relationships(self, social):
        """Decay old relationships that haven't been refreshed"""
        current_time = self.time
        for target_id, relationship in list(social.relationships.items()):
            # Calculate time since last interaction
            time_diff = current_time - relationship.last_interaction_time
            
            # Decay trust and affinity based on time
            if time_diff > 100:  # Arbitrary time threshold
                decay_factor = 0.99  # Slow decay
                
                # Apply decay
                relationship.trust *= decay_factor
                relationship.affinity *= decay_factor
                
                # Remove very weak relationships
                if abs(relationship.trust) < 0.05 and abs(relationship.affinity) < 0.05:
                    if relationship.interaction_count < 3:
                        del social.relationships[target_id]
    
    def _update_social_status(self, social):
        """Update agent's social status based on relationships"""
        if not social.relationships:
            return
        
        # Calculate average relationship quality
        total_score = 0
        for rel in social.relationships.values():
            total_score += (rel.trust + rel.affinity) / 2
        
        avg_score = total_score / len(social.relationships)
        
        # More relationships increases status
        relationship_factor = min(len(social.relationships) / 10, 1.0)  # Cap at 10 relationships
        
        # Update social status (small incremental changes)
        status_change = (avg_score * 0.1 + relationship_factor * 0.1) / 2
        social.update_status(status_change)
    
    def _store_social_memory(self, agent_id, target_id, interaction_type, successful, details=None, importance_boost=0.0):
        """Store social interaction in agent's memory"""
        agent = self.world.get_entity_by_id(agent_id)
        if not hasattr(agent, 'brain') or not agent.brain:
            return
        
        # Calculate importance based on interaction type and outcome
        importance = 0.5 + importance_boost
        if successful:
            importance += 0.2
        else:
            importance -= 0.1
            
        # Different interaction types have different importance
        if interaction_type == 'mate':
            importance += 0.3
        elif interaction_type.startswith('gift'):
            importance += 0.2
            
        # Create memory details
        memory_details = {
            'target_id': target_id,
            'interaction_type': interaction_type,
            'successful': successful,
            'time': self.time
        }
        
        # Add any extra details provided
        if details:
            memory_details.update(details)
            
        # Store in agent's memory
        agent.brain.memory.add_social_memory(target_id, interaction_type, successful, importance)
        
        # Also store as general event
        event_type = f"social_{interaction_type}"
        agent.brain.memory.add_memory(event_type, memory_details, importance)
    
    def register_negative_interaction(self, agent_id, target_id, interaction_type, details=None):
        """Register a negative social interaction between two agents"""
        # Get social components for both agents
        agent_social = self.world.ecs.get_component(agent_id, "social")
        target_social = self.world.ecs.get_component(target_id, "social")
        
        if not agent_social or not target_social:
            return False
        
        # Get interaction modifiers
        interaction = self.interaction_types.get(interaction_type, {'trust_mod': 0.3, 'affinity_mod': 0.2})
        
        # Calculate negative trust and affinity changes (always negative)
        trust_change = -interaction['trust_mod']
        affinity_change = -interaction['affinity_mod']
        
        # Apply target's personality traits as modifiers
        # More agreeable people are more hurt by betrayal
        trust_change *= (1.0 + target_social.agreeableness)
        affinity_change *= (1.0 + target_social.agreeableness)
        
        # Record interaction in target's memory (they were wronged)
        target_social.record_interaction(agent_id, interaction_type, False, self.time, 
                                        trust_change, affinity_change)
        
        # Store memory with high importance
        self._store_social_memory(target_id, agent_id, interaction_type, False, details, importance_boost=0.3)
        
        # Possibly notify others (gossip) about this negative interaction
        self._spread_negative_reputation(agent_id, target_id, interaction_type)
        
        return True
    
    def check_for_revenge(self, agent_id, nearby_agents):
        """Check if agent wants to take revenge on any nearby agents"""
        agent_social = self.world.ecs.get_component(agent_id, "social")
        if not agent_social:
            return None, None
            
        # Look for grudges among nearby agents
        for target_id in nearby_agents:
            if target_id == agent_id:
                continue
                
            # Check if there's a strong grudge
            if target_id in agent_social.relationships:
                relationship = agent_social.relationships[target_id]
                
                # If trust is very negative, there's a grudge
                if relationship.trust < self.grudge_threshold:
                    # Chance to take revenge
                    if random.random() < self.revenge_probability:
                        # Choose revenge action based on relationship history
                        revenge_action = self._select_revenge_action(relationship)
                        return target_id, revenge_action
                        
        return None, None
    
    def register_theft(self, thief_id, victim_id, resource_type, amount):
        """Register theft of resources between agents"""
        details = {
            'resource_type': resource_type,
            'amount': amount
        }
        
        # Register as negative interaction
        self.register_negative_interaction(thief_id, victim_id, 'theft', details)
        
        # Apply psychological impact to victim
        victim = self.world.get_entity_by_id(victim_id)
        if victim:
            # Decrease victim's mood
            victim.mood -= min(0.3, amount * 0.05)
    
    def register_trade_scam(self, scammer_id, victim_id, unfair_ratio):
        """Register an unfair trade as a scam"""
        # Only register as scam if the ratio is significantly unfair
        if unfair_ratio > 2.0:  # Twice as much value taken than given
            details = {
                'unfair_ratio': unfair_ratio
            }
            
            self.register_negative_interaction(scammer_id, victim_id, 'scam_trade', details)
    
    def register_workplace_misconduct(self, employee_id, workplace_id, misconduct_type, damage_amount):
        """Register workplace misconduct"""
        details = {
            'workplace_id': workplace_id,
            'misconduct_type': misconduct_type,
            'damage_amount': damage_amount
        }
        
        # Affect all workers and investors
        workplace = self.world.ecs.get_component(workplace_id, "workplace")
        if not workplace:
            return
        
        for worker_id in workplace.workers:
            if worker_id != employee_id:
                self.register_negative_interaction(employee_id, worker_id, 'work_sabotage', details)
        
        for investor in workplace.investors:
            investor_id = investor.get('investor_id')
            if investor_id and investor_id != employee_id:
                self.register_negative_interaction(employee_id, investor_id, 'work_sabotage', details)
    
    def register_investment_fraud(self, fraudster_id, investor_id, amount):
        """Register investment fraud"""
        details = {
            'amount': amount
        }
        
        self.register_negative_interaction(fraudster_id, investor_id, 'investment_fraud', details)
    
    def register_violence(self, attacker_id, victim_id, severity):
        """Register violence between agents"""
        details = {
            'severity': severity  # 0.0 to 1.0 scale
        }
        
        self.register_negative_interaction(attacker_id, victim_id, 'violence', details)
        
        # Apply physical impacts to victim
        victim = self.world.get_entity_by_id(victim_id)
        if victim:
            # Decrease energy proportional to severity
            damage = 20 * severity
            victim.energy = max(1, victim.energy - damage)
            victim.mood -= min(0.5, severity)
    
    def _select_revenge_action(self, relationship):
        """Select appropriate revenge action based on history"""
        # Check history to see what wrong was done
        for interaction_type, successful, _ in relationship.history:
            if not successful and interaction_type in ['theft', 'violence', 'scam_trade']:
                # Return similar type of revenge
                if interaction_type == 'theft':
                    return 'theft'
                elif interaction_type == 'violence':
                    return 'violence'
                elif interaction_type == 'scam_trade':
                    return 'scam_trade'
        
        # Default to most common revenge type
        return random.choice(['theft', 'violence'])
    
    def _spread_negative_reputation(self, wrongdoer_id, victim_id, interaction_type):
        """Spread negative reputation to nearby agents (gossip)"""
        # Get victim location
        victim_transform = self.world.ecs.get_component(victim_id, "transform")
        if not victim_transform:
            return
            
        # Find nearby agents who might witness or hear about this
        spatial = self.world.ecs.get_system("spatial")
        if spatial:
            nearby_witnesses = spatial.find_by_tag(victim_transform.position, 100, "tag", "agent")
            
            # Filter out the wrongdoer and victim
            nearby_witnesses = [a for a in nearby_witnesses 
                               if a != wrongdoer_id and a != victim_id]
            
            # Spread the reputation damage (weaker than direct experience)
            for witness_id in nearby_witnesses:
                witness_social = self.world.ecs.get_component(witness_id, "social")
                if witness_social:
                    # Witnesses get a weaker negative impression
                    trust_change = -self.interaction_types[interaction_type]['trust_mod'] * 0.4
                    affinity_change = -self.interaction_types[interaction_type]['affinity_mod'] * 0.4
                    
                    # Record the information
                    witness_social.record_interaction(wrongdoer_id, f"witnessed_{interaction_type}", 
                                                     False, self.time, trust_change, affinity_change)
                    
                    # Store memory
                    self._store_social_memory(witness_id, wrongdoer_id, f"witnessed_{interaction_type}", 
                                             False, {'victim_id': victim_id})
    
    def register_crop_theft(self, thief_id, owner_id, farm_id):
        """Register when an agent harvests crops planted by another agent"""
        details = {
            'farm_id': farm_id
        }
        
        self.register_negative_interaction(thief_id, owner_id, 'theft', details)
        
        # Spread knowledge about the theft to nearby agents
        self._spread_negative_reputation(thief_id, owner_id, 'theft')
        
        # Store memory for the victim
        victim = self.world.get_entity_by_id(owner_id)
        if hasattr(victim, 'brain') and victim.brain:
            importance = 0.8  # Crop theft is significant
            memory_details = {'thief_id': thief_id, 'farm_id': farm_id}
            victim.brain.memory.add_memory('was_stolen_from', memory_details, importance)
    
    def register_scam_trade(self, scammer_id, victim_id, promised_amount, actual_amount, resource_type):
        """Register when an agent scams another in a trade"""
        details = {
            'promised_amount': promised_amount,
            'actual_amount': actual_amount,
            'resource_type': resource_type
        }
        
        self.register_negative_interaction(scammer_id, victim_id, 'scam_trade', details)
        
        # Apply effects to victim
        victim = self.world.get_entity_by_id(victim_id)
        if victim:
            # Decrease mood proportional to scam severity
            severity = (promised_amount - actual_amount) / promised_amount
            victim.mood -= min(0.4, severity * 0.8)
            
        # Store memory for the victim
        if hasattr(victim, 'brain') and victim.brain:
            importance = 0.7
            memory_details = {
                'scammer_id': scammer_id, 
                'promised': promised_amount,
                'received': actual_amount,
                'resource': resource_type
            }
            victim.brain.memory.add_memory('was_scammed', memory_details, importance)