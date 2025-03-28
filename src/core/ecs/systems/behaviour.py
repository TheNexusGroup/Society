import random
from constants import ActionType, FarmState
from src.simulation.agent.logic.q_learning import QLearningSystem
from src.simulation.agent.logic.brain import AgentBrain
from ..system import System

class BehaviorSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.world = world
        self.q_learning = QLearningSystem()
        
    def get_state_representation(self, agent):
        energy_level = self._get_energy_level(agent.energy)
        money_level = self._get_money_level(agent.money)
        mood_level = self._get_mood_level(agent.mood)
        corruption_level = self._get_corruption_level(agent.corruption_level)

        return f"{energy_level}_{money_level}_{mood_level}_{corruption_level}"
            
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
    
    def _get_corruption_level(self, corruption):
        if corruption < 0.3:
            return "low"
        elif corruption < 0.7:
            return "medium"
        else:
            return "high"
    
    def select_action(self, agent):
        state = self.get_state_representation(agent)
        state_dict = {
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
        """Execute the selected action and return reward"""
        reward = 0
        
        # Store current state for Q-learning update
        old_state = self.get_state_representation(agent)
        
        # Track if this action was unethical
        unethical_action = False
        
        # Execute action
        if action == "eat":
            reward = self._execute_eat(agent)                   # Personal Agent Action
        elif action == "rest":
            reward = self._execute_rest(agent)                  # Personal Agent Action
        elif action == "mate":
            reward = self._execute_mate(agent)                  # Agent to Agent Action
        elif action == "search":
            reward = self._execute_search(agent)                # Personal Agent Action
        elif action == "gift-food":
            reward = self._execute_gift_food(agent)             # Agent to Agent Action
        elif action == "gift-money":
            reward = self._execute_gift_money(agent)            # Agent to Agent Action
        elif action == "trade-food-for-money":
            reward = self._execute_trade_food_for_money(agent)  # Agent to Agent Action
        elif action == "trade-money-for-food":
            reward = self._execute_trade_money_for_food(agent)  # Agent to Agent Action
        elif action == "plant-food":
            reward = self._execute_plant_food(agent)            # Agent to Farm Action
        elif action == "harvest-food":
            reward = self._execute_harvest_food(agent)          # Agent to Farm Action
        elif action == "work":
            reward = self._execute_work(agent)                  # Agent to Workplace Action
        elif action == "invest":
            reward = self._execute_invest(agent)                # Agent to Workplace Action
        elif action == "buy-food":
            reward = self._execute_buy_food(agent)              # Agent to Workplace Action
        elif action == "sell-food":
            reward = self._execute_sell_food(agent)             # Agent to Workplace Action
        
        # Update agent's mood based on reward
        self._update_mood(agent, reward)
        
        # Get new state after action
        new_state = self.get_state_representation(agent)
        
        # Update Q-table with the experience
        self.update_q_table(agent, old_state, action, reward, new_state)
        
        # Update agent's behavior component if it exists
        if behavior:
            behavior.previous_state = old_state
            behavior.current_state = new_state
        
        # Update corruption level based on action ethics
        if unethical_action:
            # Increment corruption level when performing unethical actions
            corruption_increase = 0.05  # Base increase
            agent.corruption_level = min(1.0, agent.corruption_level + corruption_increase)
            # Also update genome for potential offspring
            agent.genome.corruption = agent.corruption_level
        else:
            # Very slowly decrease corruption from ethical actions
            agent.corruption_level = max(0.0, agent.corruption_level - 0.002)
            agent.genome.corruption = agent.corruption_level
        
        return reward
    
    def _execute_eat(self, agent):
        """Handle agent eating food"""
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
            return reward
        
        # First check if agent has food in reserves
        reserves = self.world.ecs.get_component(agent.ecs_id, "reserves")
        if reserves and reserves.food > 0:
            # Consume food from reserves
            nutrition = min(30, reserves.food)  # Consume up to 30 nutrition
            removed_food = reserves.remove_food(nutrition)
            
            # Add energy based on nutrition value
            agent.energy = min(100, agent.energy + (removed_food * agent.genome.stamina))
            
            # Update agent's behavior component
            behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
            if behavior:
                behavior.state = "eating"
                behavior.properties["energy"] = agent.energy
            
            # Store memory of eating from reserves
            if hasattr(agent, 'brain') and agent.brain:
                importance = removed_food / 50  # Higher nutrition = more important memory
                memory_details = {'source': 'reserves', 'nutrition': removed_food}
                agent.brain.memory.add_memory('ate_food', memory_details, importance)
            
            return removed_food / 10  # Reward proportional to nutrition
        
        # If no food in reserves, look for food entities as before
        # (Rest of existing eat implementation)
        # Check if agent has money to buy food
        food_cost = 5.0
        if agent.money < food_cost:
            # Cannot afford food, negative reward
            return -0.5
            
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # First check if agent remembers where food was previously found
        remembered_food_location = None
        if hasattr(agent, 'brain') and agent.brain:
            memories = agent.brain.memory.get_memories('found_food', min_importance=0.4)
            if memories:
                # Use the most important/recent memory
                remembered_food_location = memories[0]['details'].get('position')
        
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
                
                if distance < 10:  # Close enough to eat
                    # Pay for food
                    agent.money -= food_cost
                    
                    # Eat food and increase energy
                    nutrition = food_entity.nutrition_value
                    agent.energy = max(0, agent.energy + (nutrition * agent.genome.stamina))
                    
                    # Remove consumed food
                    self.world.remove_entity(food_entity)
                    
                    # Update agent's behavior component
                    behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                    if behavior:
                        behavior.state = "eating"
                        behavior.properties["energy"] = agent.energy
                    
                    # Store memory of where food was found
                    if hasattr(agent, 'brain') and agent.brain:
                        importance = nutrition / 50  # Higher nutrition = more important memory
                        memory_details = {'position': food_transform.position, 'nutrition': nutrition}
                        agent.brain.memory.add_memory('found_food', memory_details, importance)
                        
                    reward = nutrition / 10
                else:
                    # Navigate toward food
                    navigation.navigate_to_goal(agent, food_transform.position, speed_factor=1.2)
                    reward = -0.1  # Small negative reward for travel
        elif remembered_food_location:
            # Navigate toward remembered food location
            navigation.navigate_to_goal(agent, remembered_food_location, speed_factor=1.0)
            reward = -0.2  # Slightly larger negative reward for traveling to remembered location
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
        
        # Check if agent remembers where workplaces were previously found
        remembered_workplace = None
        if hasattr(agent, 'brain') and agent.brain:
            memories = agent.brain.memory.get_memories('found_workplace', min_importance=0.4)
            if memories:
                # Use the most important/recent memory
                remembered_workplace = memories[0]['details'].get('position')
        
        # Find workplaces
        workplaces = spatial.find_by_tag(transform.position, 200, "tag", "workplace")
        
        if workplaces:
            # Get workplace and its position
            workplace_id = workplaces[0]
            workplace = self.world.get_entity_by_id(workplace_id)
            workplace_comp = self.world.ecs.get_component(workplace_id, "workplace")
            
            if workplace and workplace_comp:
                workplace_transform = self.world.ecs.get_component(workplace_id, "transform")
                
                if workplace_transform:
                    # Calculate distance to workplace
                    dx = transform.position[0] - workplace_transform.position[0]
                    dy = transform.position[1] - workplace_transform.position[1]
                    distance = (dx*dx + dy*dy) ** 0.5
                    
                    if distance < 20:  # Close enough to work
                        # Check if workplace can accept more workers
                        if not workplace_comp.is_full():
                            # Add agent as worker to workplace
                            if workplace_comp.add_worker(agent.ecs_id):
                                # Work energy cost based on metabolism
                                work_energy_cost = 15.0 * agent.genome.metabolism
                                
                                # Check if agent has enough energy
                                if agent.energy < work_energy_cost:
                                    return -0.5  # Penalty for not having enough energy to work
                                
                                # Deduct energy cost
                                agent.energy -= work_energy_cost
                                
                                # Calculate earnings based on workplace wage
                                earnings = workplace_comp.base_wage * 0.1 * (1.0 + agent.genome.learning_capacity/2)
                                agent.money += earnings
                                
                                # Update workplace finances
                                workplace_comp.expenses += earnings
                                
                                # Update agent's behavior component
                                behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                                if behavior:
                                    behavior.state = "working"
                                    behavior.target = workplace_id
                                    behavior.properties["money"] = agent.money
                                
                                # Store memory of workplace location
                                if hasattr(agent, 'brain') and agent.brain:
                                    importance = earnings / 20  # Higher earnings = more important memory
                                    memory_details = {'position': workplace_transform.position, 'earnings': earnings}
                                    agent.brain.memory.add_memory('found_workplace', memory_details, importance)
                                
                                # Reward proportional to earnings
                                reward = earnings / 10.0
                            else:
                                # Workplace cannot accept more workers
                                return -0.5
                        else:
                            # Workplace is full
                            return -0.5
                    else:
                        # Navigate to workplace
                        navigation.navigate_to_goal(agent, workplace_transform.position)
                        reward = -0.2  # Small negative reward for travel
        elif remembered_workplace:
            # Navigate toward remembered workplace
            navigation.navigate_to_goal(agent, remembered_workplace, speed_factor=1.0)
            reward = -0.2  # Slightly larger negative reward for traveling to remembered location
        else:
            # No workplace found, search for one
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward
    
    def _execute_rest(self, agent):
        # Rest to regain energy
        energy_before = agent.energy
        
        # Calculate energy gain based on stamina
        energy_gain = agent.genome.stamina
        agent.energy = min(1, agent.energy + energy_gain)
        
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
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood),
            'corruption': self._get_corruption_level(agent.corruption_level)
        }
        
        new_state_dict = {
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood),
            'corruption': self._get_corruption_level(agent.corruption_level)
        }
        
        # Add reserves information if available
        reserves = self.world.ecs.get_component(agent.ecs_id, "reserves")
        if reserves:
            food_level = "low"
            if reserves.food > reserves.max_food * 0.7:
                food_level = "high"
            elif reserves.food > reserves.max_food * 0.2:
                food_level = "medium"
            
            state_dict['food_reserves'] = food_level
            new_state_dict['food_reserves'] = food_level
        
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

        if behavior.state == "dead":
            return
        
        if not agent or not hasattr(agent, 'genome') or not behavior:
            return
        
        # Initialize brain if needed
        if not hasattr(agent, 'brain') or not agent.brain:
            agent.brain = self.get_or_create_brain(agent)
        
        # Get current state
        current_state = self.get_state_representation(agent)
        current_state_dict = {
            'energy': self._get_energy_level(agent.energy),
            'money': self._get_money_level(agent.money),
            'mood': self._get_mood_level(agent.mood)
        }
        
        # Select action using agent's brain or Q-learning
        action = self.select_action(agent)
        print("Action:", action)

        # Execute action and get reward - pass behavior component
        reward = self.execute_action(agent, action, behavior)
        
        # Get new state after action
        new_state = self.get_state_representation(agent)
        new_state_dict = {
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
        
        # Update agent vitals - reduce metabolism effects
        agent.energy -= 0.3 * agent.genome.metabolism / agent.genome.stamina
        
        # Update mood based on action results
        self._update_mood(agent, reward)
        
        # Sync agent properties with behavior component
        self.sync_agent_with_component(agent, behavior)
        
        # Check for death conditions - make more forgiving
        if agent.energy <= 0 or agent.age > 200:
            agent.is_alive = False
            
            # Update to show dead appearance
            if hasattr(agent, 'update_asset_based_on_state'):
                agent.update_asset_based_on_state("dead")
            
            # Don't remove immediately to allow death animation/state to be visible
            # We'll remove after a delay or in the next epoch
            # self.world.remove_entity(agent)
            
            # Check if population is extinct
            if all(not agent.is_alive for agent in self.world.society.population):
                self.world.society.start_new_epoch()
        
        # Update behavior component with latest properties including is_alive status
        behavior_component = self.world.ecs.get_component(entity_id, "behavior")
        if behavior_component and hasattr(agent, 'is_alive'):
            behavior_component.properties.update({
                "energy": agent.energy,
                "money": agent.money,
                "mood": agent.mood,
                "is_alive": agent.is_alive
            })
            
            # Set state based on alive status
            if not agent.is_alive:
                behavior_component.state = "dead"
            else:
                behavior_component.state = agent.current_action
        
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
        """Get or create a brain for this agent"""
        if hasattr(agent, 'brain') and agent.brain:
            return agent.brain
        
        # Create new brain with world reference
        brain = AgentBrain(agent.ecs_id, agent.genome, world=self.world)
        
        # Load any existing memories or knowledge
        social = self.world.ecs.get_component(agent.ecs_id, "social")
        if social:
            # Add social connections to brain
            for connection in social.connections:
                importance = 0.5
                memory_details = {
                    'target_id': connection.target_id,
                    'trust_level': connection.trust,
                    'relationship': 'friend' if connection.trust > 0.5 else 'neutral'
                }
                brain.memory.add_memory('social_connection', memory_details, importance)
        
        return brain

    def sync_agent_with_component(self, agent, behavior_component):
        """Sync agent properties with behavior component"""
        # Update behavior component properties with latest agent values
        behavior_component.properties.update({
            "energy": agent.energy,
            "money": agent.money,
            "mood": agent.mood
        })

    def _execute_plant_food(self, agent):
        """Handle agent planting food at a farm"""
        reward = 0
        
        # Check if agent has enough energy to plant
        if agent.energy < 20:
            return -0.5  # Penalty for attempting to plant with low energy
        
        # Get the spatial and navigation systems
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        food_system = self.world.ecs.get_system("food")
        
        if not spatial or not navigation or not food_system:
            return reward
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Check if agent remembers where farms were previously found
        remembered_farm = None
        if hasattr(agent, 'brain') and agent.brain:
            memories = agent.brain.memory.get_memories('found_farm', min_importance=0.4)
            if memories:
                remembered_farm = memories[0]['details'].get('position')
        
        # Find nearby farms
        farm_entities = spatial.find_by_tag(transform.position, 150, "tag", "farm")
        
        if farm_entities:
            # Target the closest farm
            farm_id = farm_entities[0]
            farm_entity = self.world.get_entity_by_id(farm_id)
            farm_transform = self.world.ecs.get_component(farm_id, "transform")
            
            if farm_entity and farm_transform:
                # Calculate distance to farm
                dx = transform.position[0] - farm_transform.position[0]
                dy = transform.position[1] - farm_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 20:  # Close enough to plant
                    # Try to plant
                    success, energy_cost = food_system.plant_food(agent, farm_id)
                    
                    if success:
                        # Update agent's behavior component
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "farming"
                            behavior.target = farm_id
                            behavior.properties["energy"] = agent.energy
                        
                        reward = 1.0  # Positive reward for successful planting
                    else:
                        # Farm not in right state or agent doesn't have energy
                        reward = -0.2
                else:
                    # Navigate toward farm
                    navigation.navigate_to_goal(agent, farm_transform.position, speed_factor=1.0)
                    reward = -0.1  # Small negative reward for travel
        elif remembered_farm:
            # Navigate toward remembered farm
            navigation.navigate_to_goal(agent, remembered_farm, speed_factor=1.0)
            reward = -0.2
        else:
            # No farm found, search for one
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward

    def _execute_harvest_food(self, agent):
        """Handle harvesting food, potentially stealing crops"""
        reward = 0
        
        # Check if agent has enough energy to harvest
        if agent.energy < 15:
            return -0.5  # Penalty for attempting to harvest with low energy
        
        # Get the spatial and navigation systems
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        food_system = self.world.ecs.get_system("food")
        
        if not spatial or not navigation or not food_system:
            return reward
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Check if agent remembers where farms with yield were previously found
        remembered_yield_farm = None
        if hasattr(agent, 'brain') and agent.brain:
            memories = agent.brain.memory.get_memories('found_yield_farm', min_importance=0.5)
            if memories:
                remembered_yield_farm = memories[0]['details'].get('position')
        
        # Find nearby farms
        farm_entities = spatial.find_by_tag(transform.position, 150, "tag", "farm")
        
        # Determine if agent will potentially steal crops based on corruption level
        will_steal = False
        for farm_id in farm_entities:
            farm_entity = self.world.get_entity_by_id(farm_id)
            farm_component = self.world.ecs.get_component(farm_id, "farm")
            farm_transform = self.world.ecs.get_component(farm_id, "transform")
            
            if farm_entity and farm_component and farm_transform:
                # Check if farm is in yield state
                if farm_component.farm_state == FarmState.YIELD:
                    # Calculate distance to farm
                    dx = transform.position[0] - farm_transform.position[0]
                    dy = transform.position[1] - farm_transform.position[1]
                    distance = (dx*dx + dy*dy) ** 0.5
                    
                    if distance < 20:  # Close enough to harvest
                        # Check if farm is owned by this agent
                        if farm_component.planted_by == agent.ecs_id:
                            # This farm is owned by this agent, no need to steal
                            target_farm = farm_entity
                            break
                        else:
                            # This farm is not owned by this agent, potential theft
                            will_steal = True
                            target_farm = farm_entity
                            break
        else:
            # No farms found, search for one
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        if will_steal:
            # If agent will potentially steal crops, handle the theft
            # ... include the agricultural system's harvest_farm code which handles theft ...
            reward = -0.5  # Negative reward for attempting to steal crops
        else:
            # If no potential theft, handle normal harvest
            # ... continue with existing logic using target_farm ...
            reward = self._execute_harvest_food_normal(agent)
        
        return reward

    def _execute_gift_food(self, agent):
        """Handle giving food to another agent"""
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
            return reward
        
        # Check if agent has food in reserves
        reserves = self.world.ecs.get_component(agent.ecs_id, "reserves")
        if not reserves or reserves.food <= 5:  # Need at least some food to gift
            return -0.2
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby agents
        nearby_agents = spatial.find_by_tag(transform.position, 50, "tag", "agent")
        
        # Filter out self from nearby agents
        nearby_agents = [a for a in nearby_agents if a != agent.ecs_id]
        
        if nearby_agents:
            # Target closest agent
            target_id = nearby_agents[0]
            target_transform = self.world.ecs.get_component(target_id, "transform")
            target_agent = self.world.get_entity_by_id(target_id)
            
            if target_transform and target_agent:
                # Calculate distance
                dx = transform.position[0] - target_transform.position[0]
                dy = transform.position[1] - target_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 15:  # Close enough to gift
                    # Gift food from reserves
                    gift_amount = min(20, reserves.food)
                    reserves.remove_food(gift_amount)
                    
                    # Add to target's reserves
                    target_reserves = self.world.ecs.get_component(target_id, "reserves")
                    if target_reserves:
                        target_reserves.add_food(gift_amount)
                        
                        # Update behavior states
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "gifting"
                            behavior.target = target_id
                        
                        # Store memory of gifting
                        if hasattr(agent, 'brain') and agent.brain:
                            importance = 0.6
                            memory_details = {'target_id': target_id, 'amount': gift_amount}
                            agent.brain.memory.add_memory('gifted_food', memory_details, importance)
                        
                        # Positive reward for altruistic action
                        reward = 0.5
                else:
                    # Navigate toward target
                    navigation.navigate_to_goal(agent, target_transform.position)
                    reward = -0.1
        else:
            # No nearby agents, search for some
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward

    def _execute_gift_money(self, agent):
        """Handle giving money to another agent"""
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
            return reward
        
        # Check if agent has enough money
        if agent.money < 10:  # Need at least some money to gift
            return -0.2
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby agents
        nearby_agents = spatial.find_by_tag(transform.position, 50, "tag", "agent")
        
        # Filter out self from nearby agents
        nearby_agents = [a for a in nearby_agents if a != agent.ecs_id]
        
        if nearby_agents:
            # Target closest agent
            target_id = nearby_agents[0]
            target_transform = self.world.ecs.get_component(target_id, "transform")
            target_agent = self.world.get_entity_by_id(target_id)
            
            if target_transform and target_agent:
                # Calculate distance
                dx = transform.position[0] - target_transform.position[0]
                dy = transform.position[1] - target_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 15:  # Close enough to gift
                    # Gift money
                    gift_amount = min(10, agent.money)
                    agent.money -= gift_amount
                    target_agent.money += gift_amount
                    
                    # Update behavior states
                    behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                    if behavior:
                        behavior.state = "gifting"
                        behavior.target = target_id
                    
                    # Store memory of gifting
                    if hasattr(agent, 'brain') and agent.brain:
                        importance = 0.6
                        memory_details = {'target_id': target_id, 'amount': gift_amount}
                        agent.brain.memory.add_memory('gifted_money', memory_details, importance)
                    
                    # Positive reward for altruistic action
                    reward = 0.5
                else:
                    # Navigate toward target
                    navigation.navigate_to_goal(agent, target_transform.position)
                    reward = -0.1
        else:
            # No nearby agents, search for some
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward

    def _execute_invest(self, agent):
        """Handle investing in a workplace"""
        reward = 0
        
        # Get the spatial and economic systems
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        economic = self.world.ecs.get_system("economic")
        if not spatial or not navigation or not economic:
            return reward
        
        # Check if agent has enough money to invest
        min_investment = 20
        if agent.money < min_investment:
            return -0.2
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby workplaces
        workplaces = spatial.find_by_tag(transform.position, 100, "tag", "workplace")
        
        if workplaces:
            # Target the closest workplace
            workplace_id = workplaces[0]
            workplace_transform = self.world.ecs.get_component(workplace_id, "transform")
            
            if workplace_transform:
                # Calculate distance
                dx = transform.position[0] - workplace_transform.position[0]
                dy = transform.position[1] - workplace_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 20:  # Close enough to invest
                    # Make investment
                    investment_amount = min(agent.money, 50)  # Invest up to 50
                    
                    # Create investor component if needed
                    investor = self.world.ecs.get_component(agent.ecs_id, "investor")
                    if not investor:
                        from ..components.investor import InvestorComponent
                        investor = InvestorComponent(agent.ecs_id)
                        self.world.ecs.add_component(agent.ecs_id, "investor", investor)
                    
                    # Record investment with return rate (handled by economic system)
                    return_rate = 0.1  # 10% return rate
                    investor.add_investment(workplace_id, investment_amount, return_rate)
                    
                    # Deduct money from agent
                    agent.money -= investment_amount
                    
                    # Update workplace funds
                    workplace = self.world.ecs.get_component(workplace_id, "workplace")
                    if workplace:
                        workplace.funds += investment_amount
                    
                    # Update behavior
                    behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                    if behavior:
                        behavior.state = "investing"
                        behavior.target = workplace_id
                    
                    # Store memory of investment
                    if hasattr(agent, 'brain') and agent.brain:
                        importance = 0.7
                        memory_details = {'workplace_id': workplace_id, 'amount': investment_amount}
                        agent.brain.memory.add_memory('invested', memory_details, importance)
                    
                    # Positive reward for investment
                    reward = 0.3
                else:
                    # Navigate toward workplace
                    navigation.navigate_to_goal(agent, workplace_transform.position)
                    reward = -0.1
        else:
            # No workplaces found, search randomly
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward

    def _execute_buy_food(self, agent):
        """Handle buying food from a workplace"""
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        economic = self.world.ecs.get_system("economic")
        if not spatial or not navigation or not economic:
            return reward
        
        # Check if agent has money
        food_cost = 5.0
        if agent.money < food_cost:
            return -0.5
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby workplaces
        workplaces = spatial.find_by_tag(transform.position, 100, "tag", "workplace")
        
        if workplaces:
            # Target the closest workplace
            workplace_id = workplaces[0]
            workplace_transform = self.world.ecs.get_component(workplace_id, "transform")
            workplace = self.world.ecs.get_component(workplace_id, "workplace")
            
            if workplace_transform and workplace:
                # Calculate distance
                dx = transform.position[0] - workplace_transform.position[0]
                dy = transform.position[1] - workplace_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 20:  # Close enough to buy
                    # Check if workplace has food stock
                    if workplace.stock > 0:
                        # Buy food
                        agent.money -= food_cost
                        workplace.funds += food_cost
                        workplace.stock -= 1
                        
                        # Add to agent's reserves
                        reserves = self.world.ecs.get_component(agent.ecs_id, "reserves")
                        if reserves:
                            nutrition_value = 30  # Standard nutrition value for purchased food
                            reserves.add_food(nutrition_value)
                        
                        # Update behavior
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "buying"
                            behavior.target = workplace_id
                        
                        # Store memory of purchase
                        if hasattr(agent, 'brain') and agent.brain:
                            importance = 0.5
                            memory_details = {'workplace_id': workplace_id, 'cost': food_cost}
                            agent.brain.memory.add_memory('bought_food', memory_details, importance)
                        
                        # Positive reward for buying food
                        reward = 0.4
                    else:
                        # Workplace out of stock
                        reward = -0.3
                else:
                    # Navigate toward workplace
                    navigation.navigate_to_goal(agent, workplace_transform.position)
                    reward = -0.1
        else:
            # No workplaces found, search randomly
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward

    def _execute_sell_food(self, agent):
        """Handle selling food to a workplace"""
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        economic = self.world.ecs.get_system("economic")
        if not spatial or not navigation or not economic:
            return reward
        
        # Check if agent has food to sell
        reserves = self.world.ecs.get_component(agent.ecs_id, "reserves")
        if not reserves or reserves.food < 10:  # Need minimum food to sell
            return -0.3
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby workplaces
        workplaces = spatial.find_by_tag(transform.position, 100, "tag", "workplace")
        
        if workplaces:
            # Target the closest workplace
            workplace_id = workplaces[0]
            workplace_transform = self.world.ecs.get_component(workplace_id, "transform")
            workplace = self.world.ecs.get_component(workplace_id, "workplace")
            
            if workplace_transform and workplace:
                # Calculate distance
                dx = transform.position[0] - workplace_transform.position[0]
                dy = transform.position[1] - workplace_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 20:  # Close enough to sell
                    # Check if workplace has funds
                    if workplace.funds >= 10:
                        # Sell food
                        food_amount = min(30, reserves.food)
                        sell_price = food_amount * 0.5  # 0.5 per unit of food
                        
                        # Transfer food and money
                        reserves.remove_food(food_amount)
                        agent.money += sell_price
                        workplace.funds -= sell_price
                        workplace.stock += int(food_amount / 10)  # Convert to stock units
                        
                        # Update behavior
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "selling"
                            behavior.target = workplace_id
                        
                        # Store memory of sale
                        if hasattr(agent, 'brain') and agent.brain:
                            importance = 0.6
                            memory_details = {'workplace_id': workplace_id, 'amount': food_amount, 'price': sell_price}
                            agent.brain.memory.add_memory('sold_food', memory_details, importance)
                        
                        # Positive reward for selling
                        reward = 0.5
                    else:
                        # Workplace doesn't have enough funds
                        reward = -0.2
                else:
                    # Navigate toward workplace
                    navigation.navigate_to_goal(agent, workplace_transform.position)
                    reward = -0.1
        else:
            # No workplaces found, search randomly
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward

    def _execute_trade_food_for_money(self, agent):
        """Handle trading food for money with another agent"""
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
            return reward
        
        # Check if agent has food to trade
        reserves = self.world.ecs.get_component(agent.ecs_id, "reserves")
        if not reserves or reserves.food < 10:  # Need minimum food to trade
            return -0.3
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby agents
        nearby_agents = spatial.find_by_tag(transform.position, 50, "tag", "agent")
        
        # Filter out self from nearby agents
        nearby_agents = [a for a in nearby_agents if a != agent.ecs_id]
        
        if nearby_agents:
            # Target closest agent
            target_id = nearby_agents[0]
            target_transform = self.world.ecs.get_component(target_id, "transform")
            target_agent = self.world.get_entity_by_id(target_id)
            
            if target_transform and target_agent:
                # Calculate distance
                dx = transform.position[0] - target_transform.position[0]
                dy = transform.position[1] - target_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < 15:  # Close enough to trade
                    # Check if target has money
                    if target_agent.money >= 10:
                        # Trade food for money
                        food_amount = min(20, reserves.food)
                        price = food_amount * 0.6  # 0.6 per unit of food
                        
                        # Cap at target's available money
                        price = min(price, target_agent.money)
                        
                        # Transfer resources
                        reserves.remove_food(food_amount)
                        agent.money += price
                        target_agent.money -= price
                        
                        # Add to target's reserves
                        target_reserves = self.world.ecs.get_component(target_id, "reserves")
                        if target_reserves:
                            target_reserves.add_food(food_amount)
                        
                        # Update behavior states
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "trading"
                            behavior.target = target_id
                        
                        # Store memory of trade
                        if hasattr(agent, 'brain') and agent.brain:
                            importance = 0.7
                            memory_details = {'target_id': target_id, 'food_amount': food_amount, 'money_received': price}
                            agent.brain.memory.add_memory('traded_food_for_money', memory_details, importance)
                        
                        # Positive reward for successful trade
                        reward = 0.6
                    else:
                        # Target doesn't have enough money
                        reward = -0.2
                else:
                    # Navigate toward target
                    navigation.navigate_to_goal(agent, target_transform.position)
                    reward = -0.1
        else:
            # No nearby agents, search for some
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward

    def _execute_trade_money_for_food(self, agent):
        """Handle trading money for food with another agent, with potential for scams"""
        reward = 0
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
            return reward
        
        # Check if agent has money to trade
        if agent.money < 10:  # Need minimum money to trade
            return -0.3
        
        # Get agent position
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return reward
        
        # Find nearby agents
        nearby_agents = spatial.find_by_tag(transform.position, 50, "tag", "agent")
        
        # Filter out self from nearby agents
        nearby_agents = [a for a in nearby_agents if a != agent.ecs_id]
        
        if nearby_agents:
            # Target closest agent
            target_id = nearby_agents[0]
            target_transform = self.world.ecs.get_component(target_id, "transform")
            target_agent = self.world.get_entity_by_id(target_id)
            
            if target_transform and target_agent:
                # Calculate distance
                dx = transform.position[0] - target_transform.position[0]
                dy = transform.position[1] - target_transform.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                # Decide if this will be a scam (based on agent's social traits and current needs)
                will_scam = False
                scam_ratio = 0.0
                
                # Get social component to check personality traits
                social = self.world.ecs.get_component(agent.ecs_id, "social")
                if social and social.agreeableness < 0.3 and random.random() < 0.4:
                    will_scam = True
                    scam_ratio = max(0.2, 1.0 - social.agreeableness)  # More disagreeable = bigger scam
                
                if distance < 15:  # Close enough to trade
                    # Check if target has food
                    target_reserves = self.world.ecs.get_component(target_id, "reserves")
                    if target_reserves and target_reserves.food >= 10:
                        # Trade money for food
                        money_amount = min(20, agent.money)
                        food_amount = money_amount * 1.5  # 1.5 food per unit of money
                        
                        # Cap at target's available food
                        food_amount = min(food_amount, target_reserves.food)
                        
                        # Transfer resources
                        agent.money -= money_amount
                        target_agent.money += money_amount
                        target_reserves.remove_food(food_amount)
                        
                        # Add to agent's reserves
                        reserves = self.world.ecs.get_component(agent.ecs_id, "reserves")
                        if reserves:
                            reserves.add_food(food_amount)
                        
                        # Update behavior states
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "trading"
                            behavior.target = target_id
                        
                        # Store memory of trade
                        if hasattr(agent, 'brain') and agent.brain:
                            importance = 0.7
                            memory_details = {'target_id': target_id, 'money_amount': money_amount, 'food_received': food_amount}
                            agent.brain.memory.add_memory('traded_money_for_food', memory_details, importance)
                        
                        # If this is a scam, reduce the actual food delivered
                        promised_food = food_amount
                        if will_scam:
                            actual_food = food_amount * (1.0 - scam_ratio)
                            food_amount = actual_food  # Reduce the actual amount transferred
                            
                            # Register this as a scam in the social system
                            social_system = self.world.ecs.get_system("social")
                            if social_system:
                                social_system.register_scam_trade(
                                    agent.ecs_id, target_id, 
                                    promised_food, actual_food, 
                                    'food'
                                )
                        
                        # Positive reward for successful trade
                        reward = 0.6
                    else:
                        # Target doesn't have enough food
                        reward = -0.2
                else:
                    # Navigate toward target
                    navigation.navigate_to_goal(agent, target_transform.position)
                    reward = -0.1
        else:
            # No nearby agents, search for some
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
        
        return reward
