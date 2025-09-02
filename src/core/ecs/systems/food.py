import random
from constants import ActionType, FarmState
from ..system import System

class FoodSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.world = world
        self.growth_cycles = {}  # Track growth for farms {farm_id: current_cycle}
        self.growth_time = 10    # Cycles needed for a farm to yield
        
    def update(self, delta_time):
        """Update all farms and process growth cycles"""
        # Process farms that are growing (in 'sewed' state)
        farm_entities = self.world.ecs.get_entities_with_components(["tag", "transform"])
        
        for entity_id in farm_entities:
            tag = self.world.ecs.get_component(entity_id, "tag")
            if tag and tag.tag == "farm":
                self.process_farm_growth(entity_id)
    
    def process_farm_growth(self, farm_id):
        """Update growth cycle for a farm"""
        farm_entity = self.world.get_entity_by_id(farm_id)
        if not farm_entity or not hasattr(farm_entity, 'farm_state'):
            return
            
        # Only process farms in 'sewed' state
        if farm_entity.farm_state == FarmState.SEWED:
            # Initialize growth cycle if needed
            if farm_id not in self.growth_cycles:
                self.growth_cycles[farm_id] = 0
                
            # Increment growth cycle
            self.growth_cycles[farm_id] += 1
            
            # Check if farm is ready to yield
            if self.growth_cycles[farm_id] >= self.growth_time:
                # Change farm state to yield
                farm_entity.farm_state = FarmState.YIELD
                if hasattr(farm_entity, 'update_asset_based_on_state'):
                    farm_entity.update_asset_based_on_state("yield")
                
                # Reset growth cycle counter
                self.growth_cycles.pop(farm_id)
    
    def plant_food(self, agent, farm_id):
        """Plant food on a farm"""
        # Find the farm entity
        farm_comp = self.world.ecs.get_component(farm_id, "farm")
        if not farm_comp:
            return False, 0
            
        # Check if farm is in tilth state
        if farm_comp.farm_state != FarmState.TILTH:
            return False, 0
            
        # Energy cost for planting
        energy_cost = 10 * agent.genome.metabolism
        
        # Check if agent has enough energy
        if agent.energy < energy_cost:
            return False, 0
            
        # Consume energy
        agent.energy -= energy_cost
        
        # Change farm state to sewed
        farm_comp.change_state(FarmState.SEWED)
        
        # Update farm entity appearance
        farm_entity = self.world.get_entity_by_id(farm_id)
        if farm_entity and hasattr(farm_entity, 'update_asset_based_on_state'):
            farm_entity.update_asset_based_on_state("sewed")
            
        # Update agent appearance
        if hasattr(agent, 'update_asset_based_on_state'):
            agent.update_asset_based_on_state("farm")
            
        # Store memory of where the agent planted
        if hasattr(agent, 'brain') and agent.brain:
            farm_transform = self.world.ecs.get_component(farm_id, "transform")
            if farm_transform:
                importance = 0.7  # High importance
                memory_details = {'position': farm_transform.position, 'farm_id': farm_id}
                agent.brain.memory.add_memory('planted_farm', memory_details, importance)
                
        # Return success and energy cost
        return True, energy_cost
    
    def harvest_food(self, agent, farm_id):
        """Harvest food from a farm"""
        # Find the farm component
        farm_comp = self.world.ecs.get_component(farm_id, "farm")
        if not farm_comp:
            return False, 0, 0
            
        # Check if farm is in yield state
        if farm_comp.farm_state != FarmState.YIELD:
            return False, 0, 0
            
        # Energy cost for harvesting
        energy_cost = 8 * agent.genome.metabolism
        
        # Check if agent has enough energy
        if agent.energy < energy_cost:
            return False, 0, 0
            
        # Consume energy
        agent.energy -= energy_cost
        
        # Calculate yield based on farm and agent traits
        agricultural_system = self.world.ecs.get_system("agricultural")
        if agricultural_system:
            food_count, nutrition_value = agricultural_system.calculate_harvest_yield(farm_id, agent.ecs_id)
        else:
            # Fallback if agricultural system not available
            base_yield = random.uniform(20, 40)
            harvesting_bonus = agent.genome.stamina * 0.5
            nutrition_value = base_yield + harvesting_bonus
            food_count = random.randint(2, 5)
        
        # Create harvested food entities
        farm_entity = self.world.get_entity_by_id(farm_id)
        farm_transform = self.world.ecs.get_component(farm_id, "transform")
        
        if farm_entity and farm_transform:
            for _ in range(food_count):
                food_position = (
                    farm_transform.position[0] + random.uniform(-20, 20),
                    farm_transform.position[1] + random.uniform(-20, 20)
                )
                food = self.world.entity_factory.create_entity(
                    "food",
                    food_position,
                    self.world.world_screen,
                    nutrition=nutrition_value
                )
                self.world.entities.append(food)
        
        # Reset farm to tilth state
        farm_comp.change_state(FarmState.TILTH)
        
        # Update farm entity appearance
        if farm_entity and hasattr(farm_entity, 'update_asset_based_on_state'):
            farm_entity.update_asset_based_on_state("tilth")
        
        # Update agent appearance
        if hasattr(agent, 'update_asset_based_on_state'):
            agent.update_asset_based_on_state("harvest")
        
        # Store memory of harvest
        if hasattr(agent, 'brain') and agent.brain:
            if farm_transform:
                importance = 0.8  # Very high importance
                memory_details = {
                    'position': farm_transform.position, 
                    'farm_id': farm_id,
                    'yield': food_count * nutrition_value
                }
                agent.brain.memory.add_memory('harvested_farm', memory_details, importance)
        
        # Return success, energy cost, and total nutrition harvested
        return True, energy_cost, food_count * nutrition_value
    
    def execute_plant_food(self, agent):
        """Handle planting food action for an agent"""
        reward = -0.5  # Default small negative reward
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
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
                    success, energy_cost = self.plant_food(agent, farm_id)
                    
                    if success:
                        # Update agent's behavior component
                        behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                        if behavior:
                            behavior.state = "farming"
                            behavior.target = farm_id
                            behavior.properties["energy"] = agent.energy
                        
                        # Store memory of where farm was found
                        if hasattr(agent, 'brain') and agent.brain:
                            importance = 0.6
                            memory_details = {'position': farm_transform.position, 'farm_id': farm_id}
                            agent.brain.memory.add_memory('found_farm', memory_details, importance)
                            
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
    
    def execute_harvest_food(self, agent):
        """Handle harvesting food action for an agent"""
        reward = -0.5  # Default small negative reward
        
        # Get the spatial system
        spatial = self.world.ecs.get_system("spatial")
        navigation = self.world.ecs.get_system("navigation")
        if not spatial or not navigation:
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
        
        if farm_entities:
            # Check farms to find ones in yield state
            for farm_id in farm_entities:
                farm_entity = self.world.get_entity_by_id(farm_id)
                farm_transform = self.world.ecs.get_component(farm_id, "transform")
                
                if farm_entity and farm_transform and hasattr(farm_entity, 'farm_state'):
                    # Store memory if farm is in yield state
                    if farm_entity.farm_state == FarmState.YIELD and hasattr(agent, 'brain') and agent.brain:
                        importance = 0.9  # Very high importance
                        memory_details = {'position': farm_transform.position, 'farm_id': farm_id}
                        agent.brain.memory.add_memory('found_yield_farm', memory_details, importance)
                    
                    # Calculate distance to farm
                    dx = transform.position[0] - farm_transform.position[0]
                    dy = transform.position[1] - farm_transform.position[1]
                    distance = (dx*dx + dy*dy) ** 0.5
                    
                    if distance < 20 and farm_entity.farm_state == FarmState.YIELD:  # Close enough to harvest
                        # Try to harvest
                        success, energy_cost, nutrition = self.harvest_food(agent, farm_id)
                        
                        if success:
                            # Update agent's behavior component
                            behavior = self.world.ecs.get_component(agent.ecs_id, "behavior")
                            if behavior:
                                behavior.state = "harvesting"
                                behavior.target = farm_id
                                behavior.properties["energy"] = agent.energy
                            
                            # Reward is proportional to nutrition harvested
                            reward = nutrition / 20
                            break  # Exit loop after successful harvest
                        else:
                            # Couldn't harvest (energy issues)
                            reward = -0.2
                    elif distance < 20:
                        # Farm not in yield state
                        reward = -0.1
                        
                        # Navigate to next farm
                        continue
                    else:
                        # Navigate toward farm
                        navigation.navigate_to_goal(agent, farm_transform.position, speed_factor=1.0)
                        reward = -0.1  # Small negative reward for travel
                        break  # Try this farm first
        elif remembered_yield_farm:
            # Navigate toward remembered yield farm
            navigation.navigate_to_goal(agent, remembered_yield_farm, speed_factor=1.2)  # Higher priority
            reward = -0.2
        else:
            # No farm found, search for one
            energy_cost = navigation.move_randomly(agent)
            reward = -energy_cost / 20
            
        return reward
