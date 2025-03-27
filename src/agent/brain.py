import random
from typing import Dict, List, Tuple, Any
import numpy as np
from .memory import AgentMemory
from .network import DQNetwork
from src.constants import ActionType

class AgentBrain:
    def __init__(self, agent_id, genome, memory_capacity=10000, batch_size=32, target_update=100):
        # Agent identification
        self.agent_id = agent_id
        self.genome = genome
        
        # Learning parameters
        self.learning_rate = self.genome.learning_capacity
        self.gamma = 0.99  # Discount factor
        self.batch_size = batch_size
        self.target_update_frequency = target_update
        self.update_counter = 0
        
        # State encoding parameters
        self.state_size = 9  # 3 state variables with 3 possible values each
        self.action_size = len(ActionType)
        
        # Memory system
        self.memory = AgentMemory(replay_capacity=memory_capacity, episodic_capacity=100)
        
        # Neural networks for reinforcement learning
        if self.genome.use_neural_network:
            self.dqn = DQNetwork(self.state_size, self.action_size, learning_rate=self.learning_rate)
        
        # Initialize social memory
        self.social_memory = {}
    
    def select_action(self, state_dict, exploration_rate=0.1):
        """Determine the next action based on current state"""
        if self.genome.use_neural_network:
            return self.neural_network_decision(state_dict, exploration_rate)
        else:
            return self.q_learning_decision(state_dict, exploration_rate)
    
    def neural_network_decision(self, state_dict, exploration_rate):
        """Use neural network to decide action"""
        action_idx = self.dqn.select_action(state_dict, exploration_rate)
        return list(ActionType)[action_idx].value
        
    def q_learning_decision(self, state_dict, exploration_rate):
        """Use Q-learning to decide action"""
        # Create state string key
        state_key = f"{state_dict['energy']}_{state_dict['money']}_{state_dict['mood']}"
        
        # Initialize Q-values for this state if needed
        if state_key not in self.genome.q_table:
            self.genome.q_table[state_key] = {
                action_type.value: 0.0 for action_type in ActionType
            }
            
        # Choose the action with highest Q-value or explore
        if random.random() < exploration_rate:
            return random.choice(list(self.genome.q_table[state_key].keys()))
        else:
            return max(self.genome.q_table[state_key], key=self.genome.q_table[state_key].get)
    
    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in memory for later learning"""
        # Convert states to dictionary if they're not already
        if isinstance(state, str):
            state = self._state_string_to_dict(state)
        if isinstance(next_state, str):
            next_state = self._state_string_to_dict(next_state)
            
        # Convert action from string to index if using neural network
        if hasattr(self.genome, 'use_neural_network') and self.genome.use_neural_network:
            action_map = {'eat': 0, 'work': 1, 'rest': 2, 'mate': 3, 'search': 4}
            action_idx = action_map.get(action, 0)
            self.memory.add_experience(state, action_idx, reward, next_state, done)
        else:
            # For Q-table, just store the experience
            self.memory.add_experience(state, action, reward, next_state, done)
    
    def learn(self):
        """Learn from experiences (for neural network)"""
        if self.genome.use_neural_network and hasattr(self, 'dqn'):
            # Implement batch learning if needed
            pass
    
    def store_social_memory(self, target_id, action, successful, importance):
        """Store memory of social interaction with another agent"""
        if target_id not in self.social_memory:
            self.social_memory[target_id] = []
        
        # Store the interaction memory
        memory = {
            'action': action,
            'successful': successful,
            'importance': importance
        }
        self.social_memory[target_id].append(memory)
        
        # Keep only the most important/recent memories
        if len(self.social_memory[target_id]) > 5:
            self.social_memory[target_id].sort(key=lambda x: x['importance'], reverse=True)
            self.social_memory[target_id] = self.social_memory[target_id][:5]
    
    def get_memories_about(self, agent_id):
        """Retrieve memories about a specific agent"""
        return self.memory.get_memories_about_agent(agent_id)
    
    def _state_dict_to_string(self, state_dict):
        """Convert state dictionary to string representation"""
        energy_level = state_dict.get('energy', 'medium')
        money_level = state_dict.get('money', 'medium')
        mood_level = state_dict.get('mood', 'neutral')
        return f"{energy_level}_{money_level}_{mood_level}"
    
    def _state_string_to_dict(self, state_str):
        """Convert state string to dictionary"""
        parts = state_str.split('_')
        if len(parts) != 4:
            return {'energy': 'medium', 'money': 'medium', 'mood': 'neutral'}
        
        return {
            'energy': parts[0],
            'money': parts[1],
            'mood': parts[2]
        }

    def select_navigation_target(self, current_position, possible_targets, target_type):
        """Select a navigation target based on agent's knowledge and needs"""
        if not possible_targets:
            return None
        
        # Default to closest target if no special criteria
        closest_target = None
        closest_distance = float('inf')
        
        for target in possible_targets:
            # Calculate distance
            target_position = target[1]  # Assuming (entity_id, position) tuples
            dx = target_position[0] - current_position[0]
            dy = target_position[1] - current_position[1]
            distance = (dx*dx + dy*dy) ** 0.5
            
            # Check if this is closer than previous closest
            if distance < closest_distance:
                closest_distance = distance
                closest_target = target
        
        # For agents with neural networks, we could use more sophisticated selection
        # based on expected rewards, previous experiences, etc.
        
        return closest_target
