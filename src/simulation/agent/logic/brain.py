import random
from ..memory import AgentMemory
from .network import DQNetwork
from constants import ActionType

class AgentBrain:
    def __init__(self, agent_id, genome, world=None, memory_capacity=10000, batch_size=32, target_update=100):
        # Agent identification
        self.agent_id = agent_id
        self.genome = genome
        self.world = world  # Reference to the world for context
        
        # Learning parameters
        self.learning_rate = self.genome.learning_capacity
        self.gamma = 0.99  # Discount factor
        self.batch_size = batch_size
        self.target_update_frequency = target_update
        self.update_counter = 0
        
        # State encoding parameters
        self.state_size = 19  # Updated to match actual encoded state vector size (3 energy + 3 money + 3 mood + 3 corruption + 3 food reserves + 1 farm + 1 yield farm + 1 workplace + 1 trading)
        self.action_size = len(ActionType)
        
        # Memory system
        self.memory = AgentMemory(replay_capacity=memory_capacity, episodic_capacity=100)
        
        # Neural networks for reinforcement learning - always initialize
        self.dqn = DQNetwork(self.state_size, self.action_size, learning_rate=self.learning_rate)
        
        # Initialize social memory
        self.social_memory = {}
        
        # Complete action map for consistency
        self.action_map = {
            0: 'eat', 1: 'work', 2: 'rest', 3: 'mate', 4: 'search', 
            5: 'plant-food', 6: 'harvest-food', 7: 'gift-food', 8: 'gift-money',
            9: 'invest', 10: 'buy-food', 11: 'sell-food',
            12: 'trade-food-for-money', 13: 'trade-money-for-food'
        }
        
        # Reverse action map for converting strings to indices
        self.action_idx_map = {v: k for k, v in self.action_map.items()}
    
    def select_action(self, state_dict, exploration_rate=0.1):
        """Select an action based on current state using both neural network and Q-learning"""
        # Enhance state with additional information from memory
        enhanced_state = self._enhance_state_with_memory(state_dict)
        
        # Get neural network prediction to inform Q-table
        nn_action_values = self.dqn.get_action_values(enhanced_state)
        
        # Use Q-learning with neural network guidance
        return self.hybrid_decision(enhanced_state, nn_action_values, exploration_rate)
    
    def hybrid_decision(self, state_dict, nn_action_values, exploration_rate):
        """Use both Q-learning and neural network to decide action"""
        # Create state string key with corruption included
        state_key = self._state_dict_to_string(state_dict)
        
        # Initialize Q-values for this state if needed
        if state_key not in self.genome.q_table:
            self.genome.q_table[state_key] = {
                'eat': 0.0, 'work': 0.0, 'rest': 0.0, 'mate': 0.0, 'search': 0.0,
                'plant-food': 0.0, 'harvest-food': 0.0, 'gift-food': 0.0, 'gift-money': 0.0,
                'invest': 0.0, 'buy-food': 0.0, 'sell-food': 0.0,
                'trade-food-for-money': 0.0, 'trade-money-for-food': 0.0
            }
        
        # Update Q-values based on neural network predictions
        for i, value in enumerate(nn_action_values):
            if i < len(self.action_map):
                action = self.action_map[i]
                if action in self.genome.q_table[state_key]:
                    # Blend neural network knowledge into Q-table
                    self.genome.q_table[state_key][action] = (
                        0.8 * self.genome.q_table[state_key][action] + 
                        0.2 * value
                    )
        
        # Add social considerations and other adjustments from q_learning_decision
        social_reputation = state_dict.get('social_reputation', 'neutral')
        has_enemies = state_dict.get('has_enemies', 'none')
        corruption_level = state_dict.get('corruption', 'low')
        
        # Adjust actions based on social factors
        if social_reputation == 'bad':
            boost_actions = ['gift-food', 'gift-money']
            for action in boost_actions:
                self.genome.q_table[state_key][action] += 0.4
        
        if has_enemies == 'many':
            self.genome.q_table[state_key]['work'] += 0.3
            self.genome.q_table[state_key]['harvest-food'] -= 0.2
        
        # Corruption affects action tendencies
        if corruption_level == 'high':
            self.genome.q_table[state_key]['steal-crops'] = self.genome.q_table[state_key].get('steal-crops', 0) + 0.4
            self.genome.q_table[state_key]['scam-trade'] = self.genome.q_table[state_key].get('scam-trade', 0) + 0.3
        elif corruption_level == 'medium':
            self.genome.q_table[state_key]['steal-crops'] = self.genome.q_table[state_key].get('steal-crops', 0) + 0.2
            self.genome.q_table[state_key]['gift-food'] -= 0.1
        
        # Add farm state factors to the decision logic (use memory)
        farm_yield_memories = self.memory.get_memories('found_yield_farm', min_importance=0.6)
        farm_memories = self.memory.get_memories('found_farm', min_importance=0.4)
        food_reserve_level = self._get_food_reserve_level()
        
        # Adjust probabilities based on food reserves and farm knowledge
        if food_reserve_level == 'low' and farm_yield_memories:
            boost_action = 'harvest-food'
            self.genome.q_table[state_key][boost_action] += 0.5
        elif food_reserve_level == 'low' and farm_memories:
            boost_action = 'plant-food'
            self.genome.q_table[state_key][boost_action] += 0.3
        
        # Choose the action with highest Q-value or explore
        if random.random() < exploration_rate:
            return random.choice(list(self.genome.q_table[state_key].keys()))
        else:
            return max(self.genome.q_table[state_key], key=self.genome.q_table[state_key].get)
    
    def _get_food_reserve_level(self):
        """Get the food reserve level of the agent (helper function)"""
        if not self.world:
            return 'low'
        
        agent = self.world.get_entity_by_id(self.agent_id)
        if not agent:
            return 'low'
        
        reserves = self.world.ecs.get_component(self.agent_id, "reserves")
        if not reserves:
            return 'low'
        
        if reserves.food < reserves.max_food * 0.2:
            return 'low'
        elif reserves.food < reserves.max_food * 0.7:
            return 'medium'
        else:
            return 'high'
    
    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in memory for later learning"""
        # Convert states to dictionary if they're not already
        if isinstance(state, str):
            state = self._state_string_to_dict(state)
        if isinstance(next_state, str):
            next_state = self._state_string_to_dict(next_state)
            
        # Handle action conversion consistently
        if isinstance(action, str):
            # Convert string action to index for neural network
            action_idx = self.action_idx_map.get(action, 0)
            self.memory.add_experience(state, action_idx, reward, next_state, done)
        else:
            # Already an index
            self.memory.add_experience(state, action, reward, next_state, done)
        
        # Update Q-table immediately with this experience for faster learning
        state_key = self._state_dict_to_string(state)
        if state_key not in self.genome.q_table:
            self.genome.q_table[state_key] = {
                'eat': 0.0, 'work': 0.0, 'rest': 0.0, 'mate': 0.0, 'search': 0.0,
                'plant-food': 0.0, 'harvest-food': 0.0, 'gift-food': 0.0, 'gift-money': 0.0,
                'invest': 0.0, 'buy-food': 0.0, 'sell-food': 0.0,
                'trade-food-for-money': 0.0, 'trade-money-for-food': 0.0
            }
        
        # Convert action to string if it's an index
        action_str = self.action_map.get(action, action) if isinstance(action, int) else action
        
        # Simple immediate update
        old_q = self.genome.q_table[state_key].get(action_str, 0)
        self.genome.q_table[state_key][action_str] = old_q + 0.1 * (reward - old_q)
    
    def learn(self):
        """Learn from experiences using both neural network and Q-learning with synergistic updates"""
        # Update counter for target network update
        self.update_counter += 1
        
        # Sample experiences for learning
        experiences = self.memory.sample_experiences(self.batch_size)
        if not experiences or len(experiences) == 0:
            return
        
        # Update neural network with batch learning
        self.dqn.train_batch(experiences)
        
        # Update Q-table with neural network insights
        for exp in experiences:
            state = exp.state
            action = exp.action
            reward = exp.reward
            next_state = exp.next_state
            done = exp.done
            
            # Convert state to string key for Q-table
            state_key = self._state_dict_to_string(state)
            
            # Get neural network prediction for this state
            nn_prediction = self.dqn.get_action_values(state)
            
            # Initialize Q-table entry if needed
            if state_key not in self.genome.q_table:
                self.genome.q_table[state_key] = {
                    'eat': 0.0, 'work': 0.0, 'rest': 0.0, 'mate': 0.0, 'search': 0.0,
                    'plant-food': 0.0, 'harvest-food': 0.0, 'gift-food': 0.0, 'gift-money': 0.0,
                    'invest': 0.0, 'buy-food': 0.0, 'sell-food': 0.0,
                    'trade-food-for-money': 0.0, 'trade-money-for-food': 0.0
                }
            
            # Convert action to string if it's an index
            action_str = self.action_map.get(action, action) if isinstance(action, int) else action
            
            # Q-learning update with neural network insight
            old_q = self.genome.q_table[state_key].get(action_str, 0)
            
            # Get max Q-value for next state from both sources
            next_state_key = self._state_dict_to_string(next_state)
            
            # Get neural network's Q-values for next state
            nn_next_q_values = self.dqn.get_action_values(next_state)
            nn_next_max = max(nn_next_q_values) if len(nn_next_q_values) > 0 else 0
            
            # Get Q-table's max value for next state
            if next_state_key in self.genome.q_table:
                q_next_max = max(self.genome.q_table[next_state_key].values())
            else:
                q_next_max = 0
            
            # Blend the two sources
            blended_next_max = 0.5 * nn_next_max + 0.5 * q_next_max
            
            # Update Q-table with enhanced TD target
            td_target = reward + (self.gamma * blended_next_max * (1 - done))
            new_q = old_q + self.learning_rate * (td_target - old_q)
            self.genome.q_table[state_key][action_str] = new_q
            
            # Add episodic memories for significant experiences
            if abs(reward) > 1.0:
                memory_details = {
                    'action': action_str,
                    'state': state,
                    'result': 'positive' if reward > 0 else 'negative',
                    'magnitude': abs(reward)
                }
                importance = min(0.9, abs(reward)/5.0)
                self.memory.add_memory(f'experience_{action_str}', memory_details, importance)
        
        # Update target network periodically
        if self.update_counter % self.target_update_frequency == 0:
            self.dqn.update_target_network()
    
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
        """Convert state dictionary to string representation with corruption level"""
        # Get basic state elements
        energy_level = state_dict.get('energy', 'medium')
        money_level = state_dict.get('money', 'medium')
        mood_level = state_dict.get('mood', 'neutral')
        corruption_level = state_dict.get('corruption', 'low')
        
        # Create base state key
        state_key = f"{energy_level}_{money_level}_{mood_level}_{corruption_level}"
        
        return state_key
    
    def _state_string_to_dict(self, state_str):
        """Convert state string to dictionary"""
        parts = state_str.split('_')
        if len(parts) < 3:
            return {'energy': 'medium', 'money': 'medium', 'mood': 'neutral', 'corruption': 'low'}
        
        state_dict = {
            'energy': parts[0],
            'money': parts[1],
            'mood': parts[2]
        }
        
        if len(parts) > 3:
            state_dict['corruption'] = parts[3]
        else:
            state_dict['corruption'] = 'low'
        
        return state_dict

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

    def _enhance_state_with_memory(self, state_dict):
        """Add memory-derived information to the state dictionary"""
        enhanced_state = state_dict.copy()
        
        # Add food reserves information
        enhanced_state['food_reserves'] = self._get_food_reserve_level()
        
        # Add farm knowledge from memory
        farm_memories = self.memory.get_memories('found_farm', min_importance=0.4)
        enhanced_state['knows_farm_location'] = len(farm_memories) > 0
        
        yield_memories = self.memory.get_memories('found_yield_farm', min_importance=0.6)
        enhanced_state['knows_yield_farm'] = len(yield_memories) > 0
        
        # Add social knowledge from memory
        trading_memories = self.memory.get_memories('traded_food_for_money', min_importance=0.5)
        enhanced_state['has_trading_partners'] = len(trading_memories) > 0
        
        # Add corruption level
        if self.world:
            agent = self.world.get_entity_by_id(self.agent_id)
            if agent and hasattr(agent, 'corruption_level'):
                if agent.corruption_level > 0.6:
                    enhanced_state['corruption'] = 'high'
                elif agent.corruption_level > 0.3:
                    enhanced_state['corruption'] = 'medium'
                else:
                    enhanced_state['corruption'] = 'low'
        
        # Add social reputation information
        if self.world:
            social_system = self.world.ecs.get_system("social")
            my_social = self.world.ecs.get_component(self.agent_id, "social")
            
            if social_system and my_social:
                # Check if agent has negative reputation
                agent_reputation = my_social.social_status
                
                if agent_reputation < -0.3:
                    enhanced_state['social_reputation'] = 'bad'
                elif agent_reputation < 0.3:
                    enhanced_state['social_reputation'] = 'neutral'
                else:
                    enhanced_state['social_reputation'] = 'good'
                
                # Check if agent has enemies (people who distrust them)
                enemies = len(my_social.get_distrusted_agents())
                if enemies > 3:
                    enhanced_state['has_enemies'] = 'many'
                elif enemies > 0:
                    enhanced_state['has_enemies'] = 'some'
                else:
                    enhanced_state['has_enemies'] = 'none'
        
        return enhanced_state
