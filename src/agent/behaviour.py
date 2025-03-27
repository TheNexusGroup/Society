import random
import math
from ..constants import ActionType
from ..population.q_learning import QLearningSystem
from src.population.reproduction import ReproductionSystem

class BehaviorSystem:
    def __init__(self, world):
        self.world = world
        self.q_learning = QLearningSystem()
        
    def get_state_representation(self, agent):
        hunger_level = self._get_hunger_level(agent.hunger)
        energy_level = self._get_energy_level(agent.energy)
        money_level = self._get_money_level(agent.money)
        mood_level = self._get_mood_level(agent.mood)
        
        return f"{hunger_level}_{energy_level}_{money_level}_{mood_level}"
    
    def _get_hunger_level(self, hunger):
        if hunger < 30:
            return "low"
        elif hunger < 70:
            return "medium"
        else:
            return "high"
            
    def _get_energy_level(self, energy):
        if energy < 30:
            return "low"
        elif energy < 70:
            return "medium"
        else:
            return "high"
            
    def _get_money_level(self, money):
        if money < 20:
            return "low"
        elif money < 60:
            return "medium"
        else:
            return "high"
            
    def _get_mood_level(self, mood):
        if mood < -0.3:
            return "negative"
        elif mood < 0.3:
            return "neutral"
        else:
            return "positive"
    
    def select_action(self, agent):
        state = self.get_state_representation(agent)
        state_dict = {
            'hunger': self._get_hunger_level(agent.hunger),
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood)
        }
        
        # Exploration rate decreases with age/experience
        exploration_rate = 0.1 / (1 + agent.age/100)
        
        # Use brain to select action if available
        if hasattr(agent, 'brain') and agent.brain:
            return agent.brain.select_action(state_dict, exploration_rate)
        else:
            # Fallback to direct Q-learning
            return self.q_learning.select_action(
                agent.genome.q_table,
                state,
                exploration_rate
            )
    
    def execute_action(self, agent, action, behavior=None):
        reward = 0
        action_type = action
        
        if action == ActionType.EAT.value:
            reward = self._execute_eat(agent)
            action_type = "eat"
        elif action == ActionType.WORK.value:
            reward = self._execute_work(agent)
            action_type = "work"
        elif action == ActionType.REST.value:
            reward = self._execute_rest(agent)
            action_type = "rest"
        elif action == ActionType.MATE.value:
            reward = self._execute_mate(agent)
            action_type = "mate"
        elif action == ActionType.SEARCH.value:
            reward = self._execute_search(agent)
            # Search uses default appearance
        
        # Update the agent's appearance based on the action
        if hasattr(agent, 'update_asset_based_on_state'):
            agent.update_asset_based_on_state(action_type)
        
        return reward
    
    def _execute_eat(self, agent):
        # Find and eat food if available
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
            return reward
            
        # Check if agent has money to buy food
        food_cost = 5.0
        if agent.money < food_cost:
            # Cannot afford food, negative reward
            return -0.5
            
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
            
        # Find nearby food
        food_entities = spatial.find_by_tag(transform.position, 100, "tag", "food")
        
        if food_entities:
            # Target the closest food
            food_id = food_entities[0]
            food_entity = self.world.get_entity_by_id(food_id)
            food_transform = self.world.ecs.get_component(food_id, "transform")
            
            if food_entity and food_transform:
                # Calculate distance to food
                dx = transform.position[0] - food_transform.position[0]
                dy = transform.position[1] - food_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 20:  # Close enough to eat
                    # Pay for food
                    agent.money -= food_cost
                    
                    # Eat food and reduce hunger
                    nutrition = food_entity.nutrition_value
                    agent.hunger = max(0, agent.hunger - nutrition)
                    
                    # Remove consumed food
                    self.world.remove_entity(food_entity)
                    
                    # Update agent's behavior component
                    behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                    if behavior:
                        behavior.state = "eating"
                        behavior.properties["hunger"] = agent.hunger
                        
                    # Calculate reward based on hunger reduction
                    reward = nutrition / 10
                else:
                    # Navigate toward food
                    navigation.navigate_to_goal(agent, food_transform.position, speed_factor=1.2)
                    reward = -0.1  # Small negative reward for travel
        else:
            # No food found, initiate search
            energy_cost = navigation.move_randomly(agent)
            # Small negative reward for unsuccessful search
            reward = -energy_cost / 10
            
        return reward
    
    def _execute_work(self, agent):
        # Find workplace and work
        reward = 0
        
        # Check if agent has enough energy to work
        if agent.energy < 20:
            return -1.0  # Penalty for attempting to work with low energy
        
        # Get the spatial and navigation systems
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        
        if not spatial or not navigation:
            return reward
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find workplaces
        workplaces = spatial.find_by_tag(transform.position, 200, "tag", "work")
        
        if workplaces:
            # Get workplace and its position
            workplace_id = workplaces[0]
            workplace = self.world.get_entity_by_id(workplace_id)
            
            if workplace:
                workplace_transform = self.world.ecs.get_component(workplace_id, "transform")
                
                if workplace_transform:
                    # Calculate distance to workplace
                    dx = transform.position[0] - workplace_transform.position[0]
                    dy = transform.position[1] - workplace_transform.position[1]
                    distance = (dx*dx + dy*dy) ** 0.5
                    
                    if distance < 20:  # Close enough to work
                        # Work energy cost based on metabolism
                        work_energy_cost = 15.0 * agent.genome.metabolism
                        
                        # Check if agent has enough energy
                        if agent.energy < work_energy_cost:
                            return -0.5  # Penalty for not having enough energy to work
                        
                        # Deduct energy cost
                        agent.energy -= work_energy_cost
                        
                        # Calculate earnings based on learning capacity
                        earnings = 10.0 * (1.0 + agent.genome.learning_capacity/2)
                        agent.money += earnings
                        
                        # Update agent's behavior component
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "working"
                            behavior.target = workplace_id
                            behavior.properties["money"] = agent.money
                        
                        # Reward proportional to earnings
                        reward = earnings / 10.0
                    else:
                        # Navigate to workplace
                        navigation.navigate_to_goal(agent, workplace_transform.position)
                        reward = -0.2  # Small negative reward for travel
        else:
            # No workplace found, search for one
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward
    
    def _execute_rest(self, agent):
        # Rest to regain energy
        energy_before = agent.energy
        
        # Calculate energy gain based on stamina
        energy_gain = 10 * agent.genome.stamina
        agent.energy = min(100, agent.energy + energy_gain)
        
        # Calculate reward based on energy gained
        actual_gain = agent.energy - energy_before
        reward = actual_gain / 20
        
        # Update agent's behavior component
        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
        if behavior:
            behavior.state = "resting"
            behavior.target = None
            behavior.properties["energy"] = agent.energy
        
        return reward
    
    def _execute_mate(self, agent):
        # Attempt to find and mate with another agent
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        if not spatial:
            return reward
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby agents
        agent_entities = spatial.find_by_tag(transform.position, 150, "tag", "agent")
        
        # Remove self from potential mates
        if agent.ecs_id in agent_entities:
            agent_entities.remove(agent.ecs_id)
        
        potential_mates = []
        for entity_id in agent_entities:
            mate = self.world.get_entity_by_id(entity_id)
            if mate and hasattr(mate, 'genome'):
                # Check if this agent is compatible as a mate
                if self._is_compatible_mate(agent, mate):
                    potential_mates.append(mate)
        
        if potential_mates:
            # Select the most compatible mate
            selected_mate = self._select_mate(agent, potential_mates)
            
            if selected_mate:
                # Update agent's behavior state
                behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                if behavior:
                    behavior.state = "mating"
                    behavior.target = selected_mate.ecs_id
                    behavior.target_action = "mate"
                
                # Store memory of preferred mate
                if hasattr(agent, 'brain') and agent.brain:
                    importance = 0.7  # High importance for mate selection
                    agent.brain.store_social_memory(selected_mate.ecs_id, "preferred_mate", True, importance)
                
                # Attempt reproduction - will only succeed for male-female pairs
                reproduction_system = self.world.reproduction_system
                offspring = reproduction_system.attempt_reproduction(agent, selected_mate)
                
                if offspring:
                    # If successful reproduction, high reward
                    reward = 5.0
                else:
                    # If mating but no reproduction, medium reward (social bonding)
                    reward = 2.0
        else:
            # No compatible mates found, initiate search
            navigation = self.world.ecs.get_system("navigation")
            if navigation:
                energy_cost = navigation.move_randomly(agent)
                # Small negative reward for unsuccessful search
                reward = -energy_cost / 10
        
        return reward
    
    def _execute_search(self, agent):
        # Use navigation system for search behavior
        navigation = self.world.ecs.get_system("navigation")
        if not navigation:
            return 0
        
        # Move randomly when searching
        energy_cost = navigation.move_randomly(agent)
        
        # Update agent's behavior component
        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
        if behavior:
            behavior.state = "searching"
            behavior.target = None
        
        # Small reward for exploration (knowledge gain)
        # Higher when young, lower when older (diminishing returns)
        exploration_value = 0.2 * (1.0 / (1 + agent.age/50))
        
        # Net reward is exploration value minus energy cost
        reward = exploration_value - (energy_cost / 20)
        
        return reward - (energy_cost / 10)  # Adjust reward based on energy cost
    
    def _is_compatible_mate(self, agent, potential_mate):
        # Check if potential mate is compatible for mating (not necessarily reproduction)
        
        # Check basic requirements for any mating
        if agent.energy < 30 or potential_mate.energy < 30:
            return False
        
        if agent.hunger > 70 or potential_mate.hunger > 70:
            return False
        
        # Check sexual preference compatibility
        same_gender = agent.genome.gender == potential_mate.genome.gender
        
        if same_gender:
            # Same-sex mating requires both to have same-sex preference
            # Lower sexual_preference value = stronger preference for same sex
            agent_prefers_same = agent.genome.sexual_preference < 0.5
            mate_prefers_same = potential_mate.genome.sexual_preference < 0.5
            
            # Both must prefer same-sex or at least one must be exploratory
            if not (agent_prefers_same and mate_prefers_same):
                exploration_chance = 0.1  # Small chance of exploration
                if random.random() > exploration_chance:
                    return False
        else:
            # Opposite-sex mating check
            # Higher sexual_preference value = stronger preference for opposite sex
            ## TODO: Change this to check between the difference of the sexual preferences being great than 0.5
            agent_prefers_opposite = agent.genome.sexual_preference >= 0.5
            mate_prefers_opposite = potential_mate.genome.sexual_preference >= 0.5
            
            # Both should prefer opposite-sex or at least one must be exploratory
            if not (agent_prefers_opposite and mate_prefers_opposite):
                exploration_chance = 0.1  # Small chance of exploration
                if random.random() > exploration_chance:
                    return False
        
        # Check mutual attraction - both must be attracted to each other
        attraction_to_mate = self._calculate_attraction(agent, potential_mate)
        attraction_to_agent = self._calculate_attraction(potential_mate, agent)
        
        # Base attraction threshold
        base_threshold = 0.5
        
        # Adjust threshold based on relationship type
        if same_gender:
            # Same-gender relationships need stronger attraction if not strongly same-sex oriented
            if agent.genome.sexual_preference > 0.3 or potential_mate.genome.sexual_preference > 0.3:
                # Higher threshold needed for exploration
                attraction_threshold = base_threshold * 1.5
            else:
                attraction_threshold = base_threshold
        else:
            # Opposite-gender relationships
            if agent.genome.sexual_preference < 0.7 or potential_mate.genome.sexual_preference < 0.7:
                # Higher threshold needed for exploration
                attraction_threshold = base_threshold * 1.5
            else:
                attraction_threshold = base_threshold
        
        if attraction_to_mate < attraction_threshold or attraction_to_agent < attraction_threshold:
            return False
        
        # Passed all compatibility checks for mating
        return True
    
    def _select_mate(self, agent, potential_mates):
        # Select the most attractive mate based on agent's preferences
        if not potential_mates:
            return None
            
        # If only one potential mate, select it
        if len(potential_mates) == 1:
            return potential_mates[0]
            
        # Calculate attraction scores
        attraction_scores = []
        for mate in potential_mates:
            score = self._calculate_attraction(agent, mate)
            attraction_scores.append((mate, score))
            
        # Sort by attraction score (higher is better)
        attraction_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select the most attractive mate
        return attraction_scores[0][0]
    
    def _calculate_attraction(self, agent, potential_mate):
        # Calculate attraction score based on genetics and agent's preferences
        score = 0
        
        # Base attraction
        score += 1.0
        
        # Attraction based on stamina (higher is better)
        stamina_diff = potential_mate.genome.stamina - agent.genome.stamina
        if agent.genome.attraction_profile > 0:
            # Prefers better traits
            score += stamina_diff * agent.genome.attraction_profile
        else:
            # Prefers similar traits
            score -= abs(stamina_diff) * abs(agent.genome.attraction_profile)
            
        # Attraction based on metabolism (higher can be better or worse)
        metabolism_diff = potential_mate.genome.metabolism - agent.genome.metabolism
        if agent.genome.attraction_profile > 0:
            # Prefers better traits (but extreme metabolism isn't always better)
            optimal_metabolism = 1.0
            metabolism_optimality = 1.0 - abs(potential_mate.genome.metabolism - optimal_metabolism)
            score += metabolism_optimality * agent.genome.attraction_profile
        else:
            # Prefers similar traits
            score -= abs(metabolism_diff) * abs(agent.genome.attraction_profile)
            
        # Attraction based on learning capacity (higher is better)
        learning_diff = potential_mate.genome.learning_capacity - agent.genome.learning_capacity
        if agent.genome.attraction_profile > 0:
            # Prefers better traits
            score += learning_diff * agent.genome.attraction_profile
        else:
            # Prefers similar traits
            score -= abs(learning_diff) * abs(agent.genome.attraction_profile)
            
        return score
    
    def update_q_table(self, agent, state, action, reward, new_state):
        # Convert states to dictionaries for the brain
        state_dict = {
            'hunger': self._get_hunger_level(agent.hunger),
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood)
        }
        
        new_state_dict = {
            'hunger': self._get_hunger_level(agent.hunger),
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood)
        }
        
        # Use brain if available, otherwise fall back to standard q-learning
        if hasattr(agent, 'brain') and agent.brain:
            # Store the experience in the agent's memory
            if hasattr(agent.brain.memory, 'add_experience'):
                agent.brain.memory.add_experience(state_dict, action, reward, new_state_dict, False)
            else:
                # Traditional Q-learning fallback if memory storage not available
                agent.genome.q_table = self.q_learning.update_q_table(
                    agent.genome.q_table,
                    state,
                    action,
                    reward,
                    new_state,
                    learning_rate=agent.genome.learning_capacity
                )
            
            # Occasionally learn from experiences
            if random.random() < 0.1:  # Learn occasionally to save processing
                agent.brain.learn()
        else:
            # Traditional Q-learning fallback
            agent.genome.q_table = self.q_learning.update_q_table(
                agent.genome.q_table,
                state,
                action,
                reward,
                new_state,
                learning_rate=agent.genome.learning_capacity
            )
    
    def update(self, entity_id):
        """Update behavior for all entities with behavior components"""
        # Get the agent entity and its behavior component
        agent = self.world.get_entity_by_id(entity_id)
        behavior = self.world.ecs.get_component(entity_id, "behavior")
        
        if not agent or not hasattr(agent, 'genome') or not behavior:
            return
        
        # Initialize brain if needed
        if not hasattr(agent, 'brain') or not agent.brain:
            agent.brain = self.get_or_create_brain(agent)
        
        # Get current state
        current_state = self.get_state_representation(agent)
        current_state_dict = {
            'hunger': self._get_hunger_level(agent.hunger),
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood)
        }
        
        # Select action using agent's brain or Q-learning
        action = self.select_action(agent)
        
        # Execute action and get reward - pass behavior component
        reward = self.execute_action(agent, action, behavior)
        
        # Get new state after action
        new_state = self.get_state_representation(agent)
        new_state_dict = {
            'hunger': self._get_hunger_level(agent.hunger),
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood)
        }

        # Update Q-table or agent brain
        self.update_q_table(agent, current_state, action, reward, new_state)
        
        # If social interaction occurred, store memory
        if action == ActionType.MATE.value and hasattr(agent, 'brain'):
            if behavior and behavior.target:
                importance = (reward + 5) / 10  # Scale reward to 0-1 range for importance
                agent.brain.store_social_memory(behavior.target, "mate", reward > 0, importance)
        
        # Update agent vitals
        agent.energy -= 1.0 * agent.genome.metabolism / agent.genome.stamina
        agent.hunger += 1.0 * agent.genome.metabolism
        
        # Update mood based on action results
        self._update_mood(agent, reward)
        
        # Sync agent properties with behavior component
        self.sync_agent_with_component(agent, behavior)
        
        # Check for death conditions
        if agent.energy <= 0 or agent.hunger >= 100 or agent.age > 100:
            agent.is_alive = False
            
            # Update to show dead appearance
            if hasattr(agent, 'update_asset_based_on_state'):
                agent.update_asset_based_on_state("dead")
            
            if agent in self.world.society.population:
                self.world.society.population.remove(agent)
            self.world.remove_entity(agent)
            
            # Check if population is extinct
            if not self.world.society.population:
                self.world.society.start_new_generation()
        
        return action, reward
    
    def _update_mood(self, agent, reward):
        # Update agent mood based on action results
        mood_change = reward / 5.0  # Scale reward to appropriate mood change
        
        # Apply mood change
        agent.mood += mood_change
        
        # Clamp mood to -1.0 to 1.0 range
        agent.mood = max(-1.0, min(1.0, agent.mood))
        
        # Mood naturally decays toward neutral
        if agent.mood > 0:
            agent.mood *= 0.99  # Positive mood decays
        elif agent.mood < 0:
            agent.mood *= 0.98  # Negative mood decays slightly faster

    def get_or_create_brain(self, agent):
        """Create or retrieve agent's brain"""
        from src.agent.brain import AgentBrain
        
        if hasattr(agent, 'brain') and agent.brain:
            return agent.brain
        
        # Create a new brain based on agent's genome
        return AgentBrain(agent.id, agent.genome)

    def sync_agent_with_component(self, agent, behavior_component):
        """Sync agent properties with behavior component"""
        # Update behavior component properties with latest agent values
        behavior_component.properties.update({
            "energy": agent.energy,
            "hunger": agent.hunger,
            "money": agent.money,
            "mood": agent.mood
        })
