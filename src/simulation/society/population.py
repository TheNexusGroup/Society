from ..genetics.genome import Genome
from ..agent.logic.q_learning import QLearningSystem
from ..entities.types.agent import Agent
from ..agent.logic.brain import AgentBrain
from ..genetics.evolution import Evolution
import random

# Population is a collection of agents that interact with the world and other agents

class Population:
    def __init__(self, world):
        self.world = world
        self.population = []
        self.epoch = 0
        self.metrics = {
            'population_size': [],
            'average_lifespan': [],
            'average_offspring': [],
            'genetic_diversity': [],
            'deaths_this_epoch': 0,
            'births_this_epoch': 0
        }
        self.q_learning_system = QLearningSystem()
        self.evolution = Evolution(self.world.population_size, mutation_rate=0.1, elite_percentage=0.5)
    
    def initialize_population(self, size):
        """Initialize starting population with random agents"""
        for i in range(size):
            agent = self.create_agent(i)
            self.population.append(agent)
            self.world.add_entity(agent)
    
    def create_agent(self, idx, parent1=None, parent2=None):
        """Create a new agent, either randomly or from parents"""
        if parent1 and parent2:
            # Create offspring from parents
            genome = Genome.crossover(parent1.genome, parent2.genome)
            genome.mutate(mutation_rate=0.1)
            
            # Inheriting some money from parents at a cost
            inheritance = (parent1.money + parent2.money) * 0.1
            parent1.money -= inheritance / 2
            parent2.money -= inheritance / 2
            
            agent = Agent(idx, self.world.world_screen)
            agent.genome = genome
            agent.money = inheritance
            agent.generation = max(parent1.generation, parent2.generation) + 1
            
            # Update parent stats
            parent1.offspring_count += 1
            parent2.offspring_count += 1
            parent1.offspring_generations = max(parent1.offspring_generations, agent.generation)
            parent2.offspring_generations = max(parent2.offspring_generations, agent.generation)
            
            # After creating the agent
            agent.brain = AgentBrain(agent.id, agent.genome)
            self.metrics['births_this_epoch'] += 1
            
            return agent
        else:
            # Create random new agent
            agent = Agent(idx, self.world.world_screen)
            agent.brain = AgentBrain(agent.id, agent.genome)
            return agent
    
    def update(self):
        """Update society state, handle agent interactions and learning"""
        # Process agent interactions and actions
        agents_to_remove = []
        
        for agent in self.population:
            # Get current state
            state = agent.get_state_representation()
            
            # Select action using Q-learning
            action = self.q_learning_system.select_action(
                agent.genome.q_table, 
                state, 
                exploration_rate=0.1 / (1 + agent.age/100)
            )
            
            # Execute action and get reward
            reward = self.execute_action(agent, action)
            
            # Get new state
            new_state = agent.get_state_representation()
            
            # Update Q-table
            agent.genome.q_table = self.q_learning_system.update_q_table(
                agent.genome.q_table,
                state,
                action,
                reward,
                new_state,
                learning_rate=agent.genome.learning_capacity
            )
            
            # Age agent and update metrics
            agent.age += 1
            agent.energy -= 1.0 * agent.genome.metabolism / agent.genome.stamina  # Base energy consumption

            # Check for death conditions
            if agent.energy <= 0 or agent.age > 100:
                agents_to_remove.append(agent)
                self.world.remove_entity(agent)
        
        # Remove dead agents
        for agent in agents_to_remove:
            self.metrics['deaths_this_epoch'] += 1
            self.population.remove(agent)
    
    def execute_action(self, agent, action):
        """Execute an action for an agent and return the reward"""
        reward = 0
        
        if action == 'eat':
            # Find food and eat it
            # Implementation depends on your world structure
            reward = self.try_eat(agent)
            
        elif action == 'work':
            # Find work and perform it
            reward = self.try_work(agent)
            
        elif action == 'rest':
            # Rest to regain energy
            energy_gain = 10 * agent.genome.stamina
            agent.energy = min(100, agent.energy + energy_gain)
            reward = energy_gain / 20  # Small reward for maintaining energy
            
        elif action == 'mate':
            # Find mate and attempt reproduction
            reward = self.try_mate(agent)
            
        elif action == 'search':
            # Random movement/exploration
            reward = self.try_search(agent)
            
        return reward
    
    def try_eat(self, agent):
        """Try to find and eat food"""
        # Implementation will depend on your world structure
        # For now, this is a placeholder
        return 0
    
    def try_work(self, agent):
        """Try to find work and earn money"""
        # Find nearby workplaces
        workplaces = self.world.spatial_grid.get_entities_by_tag("work", agent.position[0], agent.position[1], radius=100)
        
        if not workplaces:
            return 0  # No workplaces found
        
        # Choose the first available workplace
        for workplace_id in workplaces:
            workplace_comp = self.world.ecs.get_component(workplace_id, "workplace")
            
            if workplace_comp and len(workplace_comp.workers) < workplace_comp.max_workers:
                # Add agent as worker
                if workplace_comp.add_worker(agent.ecs_id):
                    # Set the appropriate animation state
                    agent.current_action = "work"
                    
                    # Pay the agent based on base wage and work session duration
                    wallet_comp = self.world.ecs.get_component(agent.ecs_id, "wallet")
                    if wallet_comp:
                        earned = workplace_comp.base_wage * 0.1  # Small amount per work session
                        wallet_comp.add_money(earned)
                        
                        # Update workplace finances
                        workplace_comp.expenses += earned
                        
                        # Reward is proportional to money earned
                        return earned / 5
        
        return 0  # No suitable workplace found
    
    def try_mate(self, agent):
        """Try to find a compatible mate and reproduce"""
        # Find nearby agents
        nearby_agents = self.world.spatial_grid.get_entities_by_tag("agent", agent.position[0], agent.position[1], radius=100)
        
        # Filter out self
        nearby_agents = [a for a in nearby_agents if a != agent.ecs_id]
        
        if not nearby_agents:
            return 0  # No potential mates found
        
        # Find a compatible mate
        for mate_id in nearby_agents:
            mate = self.world.get_entity_by_id(mate_id)
            
            if not mate or not mate.is_alive:
                continue
            
            # Check if different gender
            if mate.genome.gender != agent.genome.gender:
                # Check if close enough
                dx = agent.position[0] - mate.position[0]
                dy = agent.position[1] - mate.position[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance <= 30:  # Close enough to mate
                    # Create offspring
                    offspring_idx = len(self.population) + 1
                    offspring = self.create_agent(offspring_idx, agent, mate)
                    
                    # Set position near parents
                    offspring.position = (
                        (agent.position[0] + mate.position[0]) // 2 + random.randint(-20, 20),
                        (agent.position[1] + mate.position[1]) // 2 + random.randint(-20, 20)
                    )
                    
                    # Add to population and world
                    self.population.append(offspring)
                    self.world.add_entity(offspring)
                    
                    # Update agent states
                    agent.current_action = "mate"
                    mate.current_action = "mate"
                    
                    # Energy cost for reproduction
                    agent.energy -= 20
                    mate.energy -= 20
                    
                    return 10  # Good reward for reproduction
                else:
                    # Move toward potential mate
                    dx_norm = dx / (distance + 0.1)  # Avoid division by zero
                    dy_norm = dy / (distance + 0.1)
                    
                    agent.position = (
                        int(agent.position[0] - dx_norm * 5),
                        int(agent.position[1] - dy_norm * 5)
                    )
                    
                    return 1  # Small reward for finding potential mate
        
        return 0  # No compatible mate found
    
    def try_search(self, agent):
        """Search the environment, moving randomly"""
        # Random movement
        dx = random.randint(-10, 10)
        dy = random.randint(-10, 10)
        
        # Stay within world bounds
        new_x = max(0, min(self.world.width, agent.position[0] + dx))
        new_y = max(0, min(self.world.height, agent.position[1] + dy))
        
        # Update position
        agent.position = (new_x, new_y)
        
        # Update spatial grid position
        self.world.spatial_grid.update(agent.ecs_id, new_x, new_y)
        
        # Set agent state
        agent.current_action = "search"
        
        # Chance to find food
        if random.random() < 0.1:
            # Create food at this location
            self.world.create_food(position=(new_x, new_y))
            return 2  # Reward for finding food
        
        # Small energy cost
        agent.energy -= 1
        
        return 0  # Neutral reward for exploration
    
    def run_epoch(self):
        """Run a complete epoch until all agents die or max time reached"""
        max_steps = 1000
        step = 0
        
        while self.population and step < max_steps:
            self.update()
            step += 1
            
            # Occasionally spawn new resources
            if step % 20 == 0:
                self.world.create_food()
                
            if step % 50 == 0:
                self.world.create_work()
            
        # Update metrics
        self.record_metrics()
        
        # Start new epoch if needed
        if not self.population:
            self.start_new_epoch()
    
    def record_metrics(self):
        """Record current population metrics"""
        # Implementation depends on how you want to track metrics
        pass
    
    def start_new_epoch(self):
        """Initialize a new epoch based on previous epoch performance"""
        # Store previous population before clearing world
        previous_population = self.population.copy() if self.population else []
        print(f"Previous population size: {len(previous_population)}")

        # Increment epoch counter
        self.epoch += 1
        
        # Record metrics for previous epoch
        self.metrics['population_size'].append(len(previous_population))
        
        # Reset the world state
        self.world.reset_world()
        
        # Create new population using genetic algorithm
        new_population = self.evolution.evolve_population(previous_population, self.world)
        
        # Add new population to world
        for agent in new_population:
            self.world.add_entity(agent)
            # Initialize agent brain
            agent.brain = AgentBrain(agent.id, agent.genome)
        
        self.create_resources()

        # Update society's population reference
        self.population = new_population
        
        print(f"Epoch {self.epoch} started with {len(self.population)} agents")

    def create_resources(self):
        # Create new resources
        for _ in range(self.world.farm_count):
            self.world.create_farms()
        
        for _ in range(self.world.work_count):
            self.world.create_work()        