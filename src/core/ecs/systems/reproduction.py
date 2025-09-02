import random
from constants import Gender
from ..system import System

class ReproductionSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.world = world
        self.reproduction_cooldown = {}  # Track cooldown between reproduction attempts
        
    def update(self, delta_time):
        """Update method required by ECS architecture"""
        # Process reproduction cooldowns
        for agent_id in list(self.reproduction_cooldown.keys()):
            self.reproduction_cooldown[agent_id] -= delta_time
            if self.reproduction_cooldown[agent_id] <= 0:
                del self.reproduction_cooldown[agent_id]
        
        # Check for potential reproduction between nearby agents
        # This is handled by the behavior system's mate action
        # We don't need to do anything here except manage cooldowns
        pass
        
    def attempt_reproduction(self, agent1, agent2):
        """Attempt to reproduce between two agents, returns the offspring if successful"""
        
        # Only opposite-sex pairs can reproduce
        if agent1.genome.gender == agent2.genome.gender:
            return None
        
        # Check if either agent is on cooldown
        if agent1.ecs_id in self.reproduction_cooldown or agent2.ecs_id in self.reproduction_cooldown:
            return None
        
        # Ensure agents have sufficient energy and health for reproduction
        if agent1.energy < 40 or agent2.energy < 40:
            return None
            
        # Calculate reproduction chance based on health factors
        # Better health = higher chance of successful reproduction
        base_chance = 0.3  # Base 30% chance
        
        # Health modifiers
        energy_factor = (agent1.energy + agent2.energy) / 200  # 0.0-1.0
        age_factor = 1.0 - (max(agent1.age, agent2.age) / 100)  # Age penalty
        
        # Calculate final reproduction chance
        reproduction_chance = base_chance * energy_factor * age_factor
        
        # Check if reproduction is successful
        if random.random() < reproduction_chance:
            # Create offspring with genetics from both parents
            # Determine which is male/female for proper parent ordering
            if agent1.genome.gender == Gender.MALE:
                father, mother = agent1, agent2
            else:
                father, mother = agent2, agent1
                
            # Create new agent ID
            new_agent_id = len(self.world.society.population) + random.randint(1000, 9999)
            
            # Create offspring through society's agent creation mechanism
            offspring = self.world.society.create_agent(new_agent_id, father, mother)
            
            # Apply reproduction costs to parents
            energy_cost = 30  # Significant energy cost to reproduce
            agent1.energy -= energy_cost
            agent2.energy -= energy_cost
            
            # Set reproduction cooldown for both parents (24 hours in simulation time)
            self.reproduction_cooldown[agent1.ecs_id] = 24.0
            self.reproduction_cooldown[agent2.ecs_id] = 24.0
            
            # Add the new agent to the world using the entity factory
            self.world.entity_factory.register_existing_entity(offspring)
            self.world.entities.append(offspring)
            self.world.society.population.append(offspring)
            
            return offspring
            
        return None
