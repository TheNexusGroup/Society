from typing import List, Dict, Tuple
import random
import numpy as np
from .genome import Genome
from ..entities.types.agent import Agent

class Evolution:
    def __init__(self, starting_population_count, mutation_rate=0.1, elite_percentage=0.5):
        self.mutation_rate = mutation_rate
        self.elite_percentage = elite_percentage
        self.starting_population_count = starting_population_count
    
    def evolve_population(self, previous_population: List[Agent], world) -> List[Agent]:
        """Create a new epoch using genetic algorithm approach"""
        if not previous_population:
            print("Warning: No previous population to evolve from.")
            # Create a minimum set of random agents instead of returning empty
            new_agents = []
            for i in range(10):
                agent = Agent(i, world.world_screen)
                new_agents.append(agent)
            return new_agents
            
        # Debug output    
        print(f"Evolving from {len(previous_population)} agents")
        
        # Create evaluation criteria for different fitness aspects
        fitness_scores = self._calculate_fitness_scores(previous_population)
        
        # Determine population size for new epoch
        new_population_size = self.starting_population_count
        
        # Calculate how many from elite vs random
        elite_count = int(new_population_size * self.elite_percentage)
        random_count = new_population_size - elite_count
        
        print(f"Creating {elite_count} elite offspring and {random_count} random agents")
        
        # Create new epoch
        new_population = []
        
        # Add offspring from elite performers
        for i in range(elite_count):
            # Select parents based on fitness
            parent1, parent2 = self._select_parents(previous_population, fitness_scores)
            
            # Create offspring
            offspring = self._create_offspring(parent1, parent2, len(new_population), world)
            new_population.append(offspring)
        
        # Add random new agents
        for i in range(random_count):
            idx = len(new_population)
            agent = Agent(idx, world.world_screen)
            new_population.append(agent)
        
        # Apply mutation to random subset of population
        self._apply_mutations(new_population)
        
        print(f"New population size: {len(new_population)}")
        
        return new_population
    
    def _calculate_fitness_scores(self, population: List[Agent]) -> Dict[int, Dict[str, float]]:
        """Calculate fitness scores for each agent based on multiple criteria"""
        fitness_scores = {}
        
        # Find max values for normalization
        max_generations = max((agent.offspring_generations for agent in population), default=1)
        max_offspring = max((agent.offspring_count for agent in population), default=1)
        max_age = max((agent.age for agent in population), default=1)
        max_money = max((agent.money for agent in population), default=1)
        
        for agent in population:
            # Calculate normalized scores for each criteria
            generations_score = agent.offspring_generations / max_generations if max_generations > 0 else 0
            offspring_score = agent.offspring_count / max_offspring if max_offspring > 0 else 0
            age_score = agent.age / max_age if max_age > 0 else 0
            energy_score = agent.energy / 100  # Energy is typically 0-100
            money_score = agent.money / max_money if max_money > 0 else 0
            mood_score = (agent.mood + 1) / 2  # Normalize mood from [-1,1] to [0,1]
            
            # Corruption reduces fitness (society values less corrupt individuals)
            corruption_penalty = agent.corruption_level * 0.5  # Higher corruption = bigger penalty
            
            # Combine scores with weights
            total_score = (
                generations_score * 0.2 +
                offspring_score * 0.2 +
                age_score * 0.2 +
                energy_score * 0.1 +
                money_score * 0.2 +
                mood_score * 0.1 - 
                corruption_penalty  # Apply corruption penalty
            )
            
            fitness_scores[agent.id] = {
                'total': total_score,
                'generations': generations_score,
                'offspring': offspring_score,
                'age': age_score,
                'energy': energy_score,
                'money': money_score,
                'mood': mood_score,
                'corruption': agent.corruption_level
            }
            
        return fitness_scores
    
    def _select_parents(self, population: List[Agent], fitness_scores: Dict[int, Dict[str, float]]) -> Tuple[Agent, Agent]:
        """Select parents using tournament selection"""
        tournament_size = min(4, len(population))
        
        # Tournament for first parent
        candidates1 = random.sample(population, tournament_size)
        parent1 = max(candidates1, key=lambda agent: fitness_scores[agent.id]['total'])
        
        # Tournament for second parent
        candidates2 = random.sample(population, tournament_size)
        parent2 = max(candidates2, key=lambda agent: fitness_scores[agent.id]['total'])
        
        return parent1, parent2
    
    def _create_offspring(self, parent1: Agent, parent2: Agent, idx: int, world) -> Agent:
        """Create offspring from two parents"""
        # Create new genome by crossover
        child_genome = Genome.crossover(parent1.genome, parent2.genome)
        
        # Create new agent
        child = Agent(idx, world.world_screen)
        child.genome = child_genome
        
        return child
    
    def _apply_mutations(self, population: List[Agent]) -> None:
        """Apply mutations to a random subset of the population"""
        mutation_count = int(len(population) * self.mutation_rate)
        
        # Select random agents to mutate
        agents_to_mutate = random.sample(population, mutation_count)
        
        for agent in agents_to_mutate:
            # Apply genome mutation
            agent.genome.mutate(mutation_rate=0.2)
            
            # Occasionally cause bigger mutations
            if random.random() < 0.1:
                # More significant mutation to a randomly selected trait
                trait = random.choice(['metabolism', 'stamina', 'learning_capacity', 
                                      'attraction_profile', 'sexual_preference'])
                
                if trait == 'metabolism':
                    agent.genome.metabolism = random.uniform(0.3, 2.0)
                elif trait == 'stamina':
                    agent.genome.stamina = random.uniform(0.3, 2.0)
                elif trait == 'learning_capacity':
                    agent.genome.learning_capacity = random.uniform(0.05, 1.0)
                elif trait == 'attraction_profile':
                    agent.genome.attraction_profile = random.uniform(-1.0, 1.0)
                elif trait == 'sexual_preference':
                    agent.genome.sexual_preference = random.uniform(0.0, 1.0)
