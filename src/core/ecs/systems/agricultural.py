import random
from constants import FarmState
from ..system import System

class AgriculturalSystem(System):
    def __init__(self, world):
        super().__init__(world, update_frequency=4)  # Update every 4th frame - agriculture is slow
        self.world = world
        self.growth_cycles = {}  # Track growth for farms {farm_id: current_cycle}
        
    def update(self, delta_time):
        """Update all farms and process growth cycles"""
        farm_entities = self.world.ecs.get_entities_with_components(["farm", "transform"])
        
        for entity_id in farm_entities:
            farm_comp = self.world.ecs.get_component(entity_id, "farm")
            if farm_comp and farm_comp.farm_state == FarmState.SEWED:
                self.process_farm_growth(entity_id, farm_comp, delta_time)
    
    def process_farm_growth(self, farm_id, farm_comp, delta_time):
        """Update growth cycle for a farm"""
        # Initialize growth cycle if needed
        if farm_id not in self.growth_cycles:
            self.growth_cycles[farm_id] = 0
            
        # Calculate growth increment based on farm's growth speed
        growth_increment = delta_time * farm_comp.growth_speed
            
        # Increment growth cycle
        self.growth_cycles[farm_id] += growth_increment
            
        # Get growth time based on farm's state
        growth_time = 10.0  # Base growth time
            
        # Check if farm is ready to yield
        if self.growth_cycles[farm_id] >= growth_time:
            # Change farm state to yield
            farm_comp.change_state(FarmState.YIELD)
                
            # Update farm entity appearance
            farm_entity = self.world.get_entity_by_id(farm_id)
            if farm_entity and hasattr(farm_entity, 'update_asset_based_on_state'):
                farm_entity.update_asset_based_on_state("yield")
                
            # Reset growth cycle counter
            self.growth_cycles.pop(farm_id)
    
    def calculate_harvest_yield(self, farm_id, harvester_id):
        """Calculate harvest yield based on farm stats and harvester skills"""
        farm_comp = self.world.ecs.get_component(farm_id, "farm")
        harvester = self.world.get_entity_by_id(harvester_id)
        
        if not farm_comp or not harvester:
            return 0
            
        # Base yield from farm component
        base_yield = farm_comp.calculate_yield_amount()
        
        # Harvester skill bonus (if agent has genome)
        skill_bonus = 1.0
        if hasattr(harvester, 'genome'):
            # Use intelligence and stamina as factors in harvesting skill
            skill_bonus = 1.0 + (harvester.genome.intelligence * 0.3 + harvester.genome.stamina * 0.2)
            
        # Random variation (80-120% of calculated yield)
        variation = random.uniform(0.8, 1.2)
        
        # Final yield calculation
        total_yield = base_yield * skill_bonus * variation
        
        # Generate random number of food items
        food_count = max(1, int(total_yield / 20))  # 1 food per 20 yield points
        food_nutrition = total_yield / food_count  # Distribute yield evenly
        
        return food_count, food_nutrition
    
    def create_seeds_from_harvest(self, total_yield):
        """Calculate how many seeds are produced from a harvest"""
        # Base seeds is proportional to yield
        base_seeds = int(total_yield / 40)  # 1 seed per 40 yield points
        
        # Add some randomness
        random_seeds = random.randint(0, max(1, int(base_seeds / 2)))
        
        return max(1, base_seeds + random_seeds)  # Always at least 1 seed

    def harvest_farm(self, farm_id, harvester_id):
        """Harvest a farm and handle potential theft"""
        farm_comp = self.world.ecs.get_component(farm_id, "farm")
        
        if not farm_comp or farm_comp.farm_state != FarmState.YIELD:
            return 0, 0  # No yield available
        
        # Check if this is a theft (harvester is not the planter)
        is_theft = False
        if farm_comp.planted_by and farm_comp.planted_by != harvester_id:
            is_theft = True
            
            # Register theft in social system
            social_system = self.world.ecs.get_system("social")
            if social_system:
                social_system.register_crop_theft(harvester_id, farm_comp.planted_by, farm_id)
        
        # Calculate yield
        food_count, nutrition = self.calculate_harvest_yield(farm_id, harvester_id)
        
        # Reset farm state
        farm_comp.change_state(FarmState.TILTH)
        farm_comp.planted_by = None
        
        # Record theft in harvester's brain (they know they did something wrong)
        if is_theft:
            harvester = self.world.get_entity_by_id(harvester_id)
            if hasattr(harvester, 'brain') and harvester.brain:
                importance = 0.6
                memory_details = {'farm_id': farm_id, 'owner_id': farm_comp.planted_by}
                harvester.brain.memory.add_memory('stole_crops', memory_details, importance)
        
        return food_count, nutrition
