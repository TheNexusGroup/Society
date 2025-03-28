import random
from collections import deque
from typing import List, Dict, Tuple, Any
import numpy as np

class Experience:
    def __init__(self, state, action, reward, next_state, done):
        self.state = state
        self.action = action  
        self.reward = reward
        self.next_state = next_state
        self.done = done
    
    def __repr__(self):
        return f"Experience(action={self.action}, reward={self.reward:.2f}, done={self.done})"

class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def add(self, state, action, reward, next_state, done):
        experience = Experience(state, action, reward, next_state, done)
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        """Sample a random batch of experiences"""
        return random.sample(self.buffer, min(len(self.buffer), batch_size))
    
    def __len__(self):
        return len(self.buffer)

class PrioritizedReplayBuffer:
    def __init__(self, capacity: int = 10000, alpha: float = 0.6, beta: float = 0.4):
        self.capacity = capacity
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
        self.alpha = alpha  # Priority exponent (how much to prioritize)
        self.beta = beta    # Importance sampling exponent
        self.max_priority = 1.0
    
    def add(self, state, action, reward, next_state, done):
        experience = Experience(state, action, reward, next_state, done)
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
            
        # New experiences get max priority to ensure they're sampled at least once
        self.priorities[self.position] = self.max_priority
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int) -> Tuple[List[Experience], List[int], np.ndarray]:
        """Sample a batch based on priorities"""
        if len(self.buffer) == 0:
            return [], [], np.array([])
            
        # Calculate sampling probabilities
        priorities = self.priorities[:len(self.buffer)]
        probabilities = priorities ** self.alpha
        probabilities /= np.sum(probabilities)
        
        # Sample indices based on probabilities
        indices = np.random.choice(len(self.buffer), min(batch_size, len(self.buffer)), 
                                  p=probabilities, replace=False)
        
        # Calculate importance sampling weights
        weights = (len(self.buffer) * probabilities[indices]) ** -self.beta
        weights /= np.max(weights)  # Normalize
        
        # Get experiences from selected indices
        samples = [self.buffer[idx] for idx in indices]
        
        return samples, indices, weights
    
    def update_priorities(self, indices: List[int], errors: List[float]):
        """Update priorities based on TD errors"""
        for idx, error in zip(indices, errors):
            # Error can be TD error or other priority measure
            priority = (abs(error) + 1e-5) ** self.alpha
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)
    
    def __len__(self):
        return len(self.buffer)

class EpisodicMemory:
    def __init__(self, capacity: int = 100):
        self.memories = []
        self.capacity = capacity
        
    def add_memory(self, event_type: str, details: Dict[str, Any], importance: float):
        """Add a significant event memory"""
        if len(self.memories) >= self.capacity:
            # Remove least important memory if at capacity
            self.memories.sort(key=lambda x: x['importance'])
            self.memories.pop(0)
            
        memory = {
            'event_type': event_type,
            'details': details,
            'importance': importance,
            'recency': 1.0  # New memories start with high recency
        }
        
        self.memories.append(memory)
        
    def get_memories(self, event_type: str = None, min_importance: float = 0.0):
        """Retrieve memories filtered by type and importance"""
        results = []
        
        for memory in self.memories:
            if (event_type is None or memory['event_type'] == event_type) and \
               memory['importance'] >= min_importance:
                results.append(memory)
                
        # Sort by importance (most important first)
        results.sort(key=lambda x: x['importance'], reverse=True)
        return results
    
    def decay_recency(self, decay_factor: float = 0.95):
        """Decay recency of all memories"""
        for memory in self.memories:
            memory['recency'] *= decay_factor
    
    def strengthen_memory(self, index: int, amount: float = 0.1):
        """Strengthen a specific memory (increase importance)"""
        if 0 <= index < len(self.memories):
            self.memories[index]['importance'] += amount
            self.memories[index]['recency'] = 1.0  # Reset recency

class AgentMemory:
    def __init__(self, replay_capacity: int = 10000, episodic_capacity: int = 100):
        self.replay_buffer = ReplayBuffer(replay_capacity)
        self.prioritized_buffer = PrioritizedReplayBuffer(replay_capacity)
        self.episodic_memory = EpisodicMemory(episodic_capacity)
        
        # Flags to control which memory systems to use
        self.use_prioritized = False
    
    def sample_experiences(self, batch_size: int):
        """Sample a batch of experiences from the appropriate buffer"""
        return self.sample_batch(batch_size)[0]  # Just return the experiences without indices/weights
        
    def add_experience(self, state, action, reward, next_state, done):
        """Add an experience to both replay buffers"""
        self.replay_buffer.add(state, action, reward, next_state, done)
        self.prioritized_buffer.add(state, action, reward, next_state, done)
        
        # Add significant experiences to episodic memory
        if abs(reward) > 1.0:  # Significant reward threshold
            importance = abs(reward) / 3.0  # Scale importance based on reward
            details = {
                'state': state,
                'action': action,
                'reward': reward,
                'next_state': next_state
            }
            event_type = 'positive_experience' if reward > 0 else 'negative_experience'
            self.episodic_memory.add_memory(event_type, details, importance)
    
    def add_social_memory(self, agent_id, interaction_type, result, importance=0.5):
        """Add memory of social interaction with another agent"""
        details = {
            'agent_id': agent_id,
            'interaction_type': interaction_type,
            'result': result
        }
        self.episodic_memory.add_memory('social', details, importance)
    
    def sample_batch(self, batch_size):
        """Sample a batch of experiences from the appropriate buffer"""
        if self.use_prioritized:
            return self.prioritized_buffer.sample(batch_size)
        else:
            return self.replay_buffer.sample(batch_size), None, None
    
    def update_priorities(self, indices, errors):
        """Update priorities in the prioritized buffer"""
        if indices is not None and errors is not None:
            self.prioritized_buffer.update_priorities(indices, errors)
    
    def get_memories_about_agent(self, agent_id):
        """Get all memories related to a specific agent"""
        memories = self.episodic_memory.get_memories('social')
        return [m for m in memories if m['details']['agent_id'] == agent_id]
        
    def get_memories(self, event_type=None, min_importance=0.0):
        """Delegate to episodic memory's get_memories method"""
        return self.episodic_memory.get_memories(event_type, min_importance)
    
    def add_memory(self, event_type, details, importance):
        """Delegate to episodic memory's add_memory method"""
        
        # Special handling for certain memory types to enhance learning
        if event_type == 'found_farm' or event_type == 'found_yield_farm' or event_type == 'found_workplace':
            # For spatial discoveries, store the coordinates
            if 'position' in details:
                # Add as a landmark memory with higher persistence
                self.episodic_memory.add_memory('landmark', 
                    {'type': event_type, 'position': details['position']}, 
                    importance * 1.2)  # Boost importance for landmarks
        
        # Enhanced memory for social interactions
        if event_type == 'traded_money_for_food' or event_type == 'traded_food_for_money':
            if 'target_id' in details:
                # Create social memory about the trading partner
                is_successful = details.get('success', True)
                trading_importance = importance * (1.5 if is_successful else 0.7)
                self.add_social_memory(details['target_id'], event_type, is_successful, trading_importance)
