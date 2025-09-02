from src.simulation.entities.types.farm import Farm
from src.simulation.entities.types.workplace import WorkPlace
from src.simulation.entities.types.agent import Agent
from src.core.ecs.core import ECS
from src.core.ecs.components.render import RenderComponent
from src.core.ecs.components.animation import AnimationComponent
from src.core.ecs.components.transform import TransformComponent
from src.core.ecs.components.behaviour import BehaviorComponent
from src.core.ecs.components.tag import TagComponent
from src.core.ecs.systems.render import RenderSystem
from src.core.ecs.systems.animation import AnimationSystem
from src.core.ecs.systems.movement import MovementSystem
from src.core.ecs.systems.behaviour import BehaviorSystem
from src.core.spatial.grid import SpatialGrid
from src.core.spatial.system import SpatialSystem
from constants import EntityType
from src.utils.pool import EntityPool
from src.simulation.entities.factory import EntityFactory
from src.simulation.society.population import Population
from src.core.ecs.systems.reproduction import ReproductionSystem
from src.core.ecs.systems.navigation import NavigationSystem
from src.data.metrics import MetricsCollector
from src.core.ecs.components.workplace import WorkplaceComponent
from src.core.ecs.components.wallet import WalletComponent
from src.core.ecs.systems.social import SocialSystem
from src.core.ecs.systems.agricultural import AgriculturalSystem
from src.core.ecs.systems.economy import EconomicSystem
from src.core.ecs.systems.food import FoodSystem
import random

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.entities = []
        self.population_size = 100
        self.farm_count = 25
        self.work_count = 15
        self.world_screen = None  # Will be set by Simulation
        
        # Initialize metrics collector
        self.metrics = MetricsCollector()
        
        # Initialize ECS world
        self.ecs = ECS()
        
        # Initialize spatial grid
        self.spatial_grid = SpatialGrid(width, height)
        
        # Initialize entity pools
        self.entity_pools = {
            Agent: EntityPool(Agent),
            Farm: EntityPool(Farm),
            WorkPlace: EntityPool(WorkPlace)
        }
        
        # Initialize entity factory
        self.entity_factory = None  # Will be set after asset_manager is available
        
        # Initialize society
        self.society = Population(self)
        
        # Initialize reproduction system
        self.reproduction_system = ReproductionSystem(self)
        
    def setup_systems(self):
        # Add systems to the ECS world
        self.ecs.add_system(RenderSystem(self.ecs, self.world_screen))
        self.ecs.add_system(AnimationSystem(self.ecs))
        self.ecs.add_system(MovementSystem(self.ecs))
        self.ecs.add_system(BehaviorSystem(self))
        
        # Add navigation system
        self.navigation_system = NavigationSystem(self)
        self.ecs.add_system(self.navigation_system)
        
        # Add Agriculture System
        self.agriculture_system = AgriculturalSystem(self)
        self.ecs.add_system(self.agriculture_system)

        # Add Economic System
        self.economic_system = EconomicSystem(self)
        self.ecs.add_system(self.economic_system)

        # Add Reproduction System
        self.reproduction_system = ReproductionSystem(self)
        self.ecs.add_system(self.reproduction_system)

        # Add Food System
        self.food_system = FoodSystem(self)
        self.ecs.add_system(self.food_system)

        # Add Social System
        self.social_system = SocialSystem(self)
        self.ecs.add_system(self.social_system)

        # Add spatial system
        self.spatial_system = SpatialSystem(self.ecs, self.spatial_grid)
        self.ecs.add_system(self.spatial_system)
        
        # Initialize entity factory now that we have asset_manager
        self.entity_factory = EntityFactory(
            self.asset_manager,
            self.ecs,
            self.spatial_grid,
            self.entity_pools
        )

    def setup_world(self):
        # Setup ECS systems first
        self.setup_systems()
        
        # Create entities
        self.create_population()
        self.create_farms()
        self.create_work()
        
    def create_population(self):
        for i in range(self.population_size):
            agent = self.entity_factory.create_entity(
                EntityType.PERSON_MALE if i % 2 == 0 else EntityType.PERSON_FEMALE, 
                (random.randint(0, self.width), random.randint(0, self.height)),
                self.world_screen,
                id=i
            )
            self.entities.append(agent)
            self.society.population.append(agent)

    def create_farms(self):
        # Only create food if we don't have enough
        current_farm_count = sum(1 for e in self.entities if e.entity_type == EntityType.FARM)
        for i in range(current_farm_count, self.farm_count):
            food = self.entity_factory.create_entity(
                EntityType.FARM,
                (random.randint(0, self.width), random.randint(0, self.height)),
                self.world_screen
            )
            self.entities.append(food)

    def create_work(self):
        # Only create workplaces if we don't have enough
        current_work_count = sum(1 for e in self.entities if e.entity_type == EntityType.WORK)
        for i in range(current_work_count, self.work_count):
            workplace = self.entity_factory.create_entity(
                EntityType.WORK,
                (random.randint(0, self.width), random.randint(0, self.height)),
                self.world_screen
            )
            self.entities.append(workplace)
        
    def add_entity(self, entity):
        self.entities.append(entity)
        
        # Create an ECS entity and add components
        entity_id = self.ecs.create_entity()
        
        # Store ECS entity ID with the entity
        entity.ecs_id = entity_id
        entity.world = self  # Add reference to world
        
        # Add transform component
        self.ecs.add_component(
            entity_id,
            "transform",
            TransformComponent(entity_id, position=entity.position)
        )
        
        # Add entity to spatial grid
        self.spatial_grid.insert(entity_id, entity.position[0], entity.position[1])
        
        # Add tag component based on entity type
        tag_value = None
        if hasattr(entity, 'genome'):
            tag_value = "agent"
            # Add wallet component for agents
            self.ecs.add_component(
                entity_id,
                "wallet",
                WalletComponent(entity_id, money=entity.money)
            )
        elif entity.entity_type == EntityType.FARM:
            tag_value = "farm"
        elif entity.entity_type == EntityType.WORK:
            tag_value = "work"
            # Add workplace component for workplaces
            self.ecs.add_component(
                entity_id,
                "workplace",
                WorkplaceComponent(
                    entity_id,
                    max_workers=entity.capacity
                )
            )
        
        if tag_value:
            self.ecs.add_component(
                entity_id,
                "tag",
                TagComponent(entity_id, tag=tag_value)
            )
        
        # Add render component for main asset
        render_component = RenderComponent(
            entity_id,
            entity.get_asset(entity.entity_type.value),
            position=entity.position,
            size=entity.size
        )
        
        # Add state-specific assets to the render component
        for name, asset in entity.assets.items():
            if name != entity.entity_type.value:
                render_component.add_asset_for_state(name, asset)
        
        self.ecs.add_component(entity_id, "render", render_component)
        
        # Add animation components if any
        for name, asset in entity.assets.items():
            if hasattr(asset, 'update'):
                self.ecs.add_component(
                    entity_id,
                    "animation",
                    AnimationComponent(
                        entity_id,
                        asset,
                        position=entity.position,
                        name=name
                    )
                )
        
        # Add behavior component for agents
        if hasattr(entity, 'genome'):
            self.ecs.add_component(
                entity_id,
                "behavior",
                BehaviorComponent(
                    entity_id,
                    state="idle",
                    properties={
                        "energy": entity.energy,
                        "money": entity.money,
                        "mood": entity.mood
                    }
                )
            )

    def remove_entity(self, entity):
        # For dead agents, don't remove from entities list immediately
        # This allows them to still be rendered with their "dead" state
        if entity in self.entities and (not hasattr(entity, 'is_alive') or entity.is_alive):
            self.entities.remove(entity)
            
            # Remove from spatial grid
            self.spatial_grid.remove(entity.ecs_id)
            
            # Remove from ECS
            self.ecs.delete_entity(entity.ecs_id)
            
            # Return to pool
            entity_type = type(entity)
            if entity_type in self.entity_pools:
                self.entity_pools[entity_type].release(entity)

    def update_world(self):
        # Update the ECS world instead of individual entities
        self.ecs.update(1.0)  # Using 1.0 as a fixed delta time
        
        # Update metrics
        self.collect_metrics()

    def collect_metrics(self):
        """Collect current world state metrics"""
        # Count males and females
        males = sum(1 for agent in self.society.population if agent.genome.gender.value == 'male' and agent.is_alive)
        females = sum(1 for agent in self.society.population if agent.genome.gender.value == 'female' and agent.is_alive)
        
        # Calculate agent averages and additional stats
        living_agents = [agent for agent in self.society.population if agent.is_alive]
        
        # Default values if no agents
        avg_age = min_age = max_age = median_age = 0
        avg_energy = min_energy = max_energy = median_energy = 0
        avg_money = min_money = max_money = median_money = 0
        avg_mood = 0
        
        if living_agents:
            # Age stats
            ages = [agent.age for agent in living_agents]
            avg_age = sum(ages) / len(living_agents)
            min_age = min(ages)
            max_age = max(ages)
            median_age = sorted(ages)[len(ages) // 2]
            
            # Energy stats
            energies = [agent.energy for agent in living_agents]
            avg_energy = sum(energies) / len(living_agents)
            min_energy = min(energies)
            max_energy = max(energies)
            median_energy = sorted(energies)[len(energies) // 2]
            
            # Money stats
            moneys = [agent.money for agent in living_agents]
            avg_money = sum(moneys) / len(living_agents)
            min_money = min(moneys)
            max_money = max(moneys)
            median_money = sorted(moneys)[len(moneys) // 2]
            
            # Mood average
            avg_mood = sum(agent.mood for agent in living_agents) / len(living_agents)
        
        # Count starving agents (very low energy)
        starving_count = sum(1 for agent in living_agents if agent.energy < 20)
        
        # Farm metrics
        farms = [e for e in self.entities if e.entity_type == EntityType.FARM]
        farm_count = len(farms)
        
        # Only collect farm yield metrics if we have farms
        avg_farm_yield = min_farm_yield = max_farm_yield = total_farmland = 0
        if farms:
            farm_yields = []
            for farm in farms:
                farm_comp = self.ecs.get_component(farm.ecs_id, "farm")
                if farm_comp:
                    farm_yields.append(farm_comp.yield_amount)
            
            if farm_yields:
                avg_farm_yield = sum(farm_yields) / len(farm_yields)
                min_farm_yield = min(farm_yields)
                max_farm_yield = max(farm_yields)
                total_farmland = len(farms)
        
        # Work metrics
        workplaces = [e for e in self.entities if e.entity_type == EntityType.WORK]
        work_count = len(workplaces)
        
        # Employment metrics
        total_workers = 0
        total_capacity = 0
        total_productivity = 0
        total_wages_paid = 0
        
        for workplace in workplaces:
            workplace_comp = self.ecs.get_component(workplace.ecs_id, "workplace")
            if workplace_comp:
                total_workers += len(workplace_comp.workers)
                total_capacity += workplace_comp.max_workers
                total_productivity += workplace_comp.productivity
                total_wages_paid += workplace_comp.expenses
        
        employment_rate = total_workers / max(1, len(living_agents))
        avg_productivity = total_productivity / max(1, len(workplaces))
        job_vacancies = total_capacity - total_workers
        
        # Count worker types
        working_count = sum(1 for agent in living_agents if agent.current_action == "work")
        farmer_count = sum(1 for agent in living_agents if agent.current_action == "farm" or agent.current_action == "harvest-food" or agent.current_action == "plant-food")
        investor_count = 0
        for agent in living_agents:
            investor_comp = self.ecs.get_component(agent.ecs_id, "investor")
            if investor_comp and investor_comp.investments:
                investor_count += 1
        
        # Action distribution
        action_counts = {
            'eat': 0, 'work': 0, 'rest': 0, 'mate': 0, 'search': 0,
            'plant_food': 0, 'harvest_food': 0, 'gift_food': 0, 
            'gift_money': 0, 'invest': 0, 'buy_food': 0, 'sell_food': 0,
            'trade_food_for_money': 0, 'trade_money_for_food': 0
        }
        
        for agent in living_agents:
            if agent.current_action:
                # Handle hyphens in action names
                action_key = agent.current_action.replace('-', '_')
                if action_key in action_counts:
                    action_counts[action_key] += 1
        
        # Update metrics collector
        self.metrics.collect({
            # Population metrics
            'population_size': len(living_agents),
            'male_count': males,
            'female_count': females,
            'birth_count': self.society.metrics['births_this_epoch'],
            'death_count': self.society.metrics['deaths_this_epoch'],
            'working_count': working_count,
            'investor_count': investor_count,
            'farmer_count': farmer_count,
            'starving_count': starving_count,
            'epoch': self.society.epoch,
            
            # Resource metrics
            'farm_count': farm_count,
            'work_count': work_count,
            
            # Agent metrics
            'avg_age': avg_age,
            'min_age': min_age,
            'max_age': max_age,
            'median_age': median_age,
            'avg_energy': avg_energy,
            'min_energy': min_energy,
            'max_energy': max_energy,
            'median_energy': median_energy,
            'avg_money': avg_money,
            'min_money': min_money,
            'max_money': max_money,
            'median_money': median_money,
            'avg_mood': avg_mood,
            
            # Farm metrics
            'avg_farm_yield': avg_farm_yield,
            'min_farm_yield': min_farm_yield,
            'max_farm_yield': max_farm_yield,
            'total_farmland': total_farmland,
            
            # Work metrics
            'employment_rate': employment_rate,
            'avg_productivity': avg_productivity,
            'total_wages_paid': total_wages_paid,
            'job_vacancies': job_vacancies,
            
            # Action distribution
            'action_eat': action_counts['eat'],
            'action_work': action_counts['work'],
            'action_rest': action_counts['rest'],
            'action_mate': action_counts['mate'],
            'action_search': action_counts['search'],
            'action_plant_food': action_counts['plant_food'],
            'action_harvest_food': action_counts['harvest_food'],
            'action_gift_food': action_counts['gift_food'],
            'action_gift_money': action_counts['gift_money'],
            'action_invest': action_counts['invest'],
            'action_buy_food': action_counts['buy_food'],
            'action_sell_food': action_counts['sell_food'],
            'action_trade_food_for_money': action_counts['trade_food_for_money'],
            'action_trade_money_for_food': action_counts['trade_money_for_food']
        })

    def get_entity_by_id(self, entity_id):
        """Find an entity by its ECS ID"""
        for entity in self.entities:
            if hasattr(entity, 'ecs_id') and entity.ecs_id == entity_id:
                return entity
        return None

    def reset_world(self):
        """Reset the world state between epochs"""
        # Clear all entities from the world
        entities_to_remove = self.entities.copy()
        for entity in entities_to_remove:
            # Force removal of all entities including dead ones
            if entity in self.entities:
                self.entities.remove(entity)
                
                # Remove from spatial grid if it has an ECS ID
                if hasattr(entity, 'ecs_id'):
                    self.spatial_grid.remove(entity.ecs_id)
                    
                    # Return to pool
                    entity_type = type(entity)
                    if entity_type in self.entity_pools:
                        self.entity_pools[entity_type].release(entity)
        
        # Reset the ECS world
        self.ecs = ECS()
        
        # Reset spatial grid
        self.spatial_grid = SpatialGrid(self.width, self.height)
        
        # Reset entity lists
        self.entities = []
        self.society.population = []
        
        # Reset entity pools
        for pool in self.entity_pools.values():
            pool.clear()
        
        # Reset systems
        self.reproduction_system = ReproductionSystem(self)
        self.navigation_system = None
        
        # Re-setup systems with the new ECS world
        self.setup_systems()