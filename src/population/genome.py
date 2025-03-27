from typing import Dict, List, Tuple, Optional
import random
from .q_learning import QLearningSystem
from ..constants import Gender

# Genome is used to represent the genetic information of an agent and it's evolution

class Genome:
    def __init__(self, gender=None, idx=None):
        if gender is None:
            if idx is None:
                # Randomly assign gender if neither gender nor idx is provided
                self.gender = Gender.MALE if random.random() < 0.5 else Gender.FEMALE
            else:
                self.gender = Gender.MALE if idx % 2 == 0 else Gender.FEMALE
        else:
            self.gender = gender
            
        self.metabolism = random.uniform(0.5, 1.5)
        self.stamina = random.uniform(0.5, 1.5)
        self.learning_capacity = random.uniform(0.1, 0.9)
        self.attraction_profile = random.uniform(-1, 1)
        
        # Sexual preference (0.0-1.0 range representing preference for opposite sex)
        self.sexual_preference = random.uniform(0.0, 1.0)
        
        # Flag for determining learning method
        self.use_neural_network = random.random() < 0.5
        
        # Initialize Q-learning table
        self.q_table = {}
        q_learning = QLearningSystem()
        self.q_table = q_learning.initialize_q_table()
    
    @classmethod
    def crossover(cls, parent1, parent2):
        """Create a new genome by crossing over two parent genomes"""
        child = cls()
        
        # Randomly inherit gender (slightly biased toward biological balance)
        child.gender = random.choice([parent1.gender, parent2.gender])
        
        # Crossover inherited traits
        child.metabolism = random.choice([parent1.metabolism, parent2.metabolism])
        child.stamina = random.choice([parent1.stamina, parent2.stamina])
        child.learning_capacity = random.choice([parent1.learning_capacity, parent2.learning_capacity])
        child.attraction_profile = random.choice([parent1.attraction_profile, parent2.attraction_profile])
        child.sexual_preference = random.choice([parent1.sexual_preference, parent2.sexual_preference])
        
        # Inherit partial q-table (representing learned behavior)
        child.q_table = {}
        # Mix parent Q-tables (inheriting some knowledge)
        for state in set(parent1.q_table.keys()) | set(parent2.q_table.keys()):
            if state in parent1.q_table and state in parent2.q_table:
                child.q_table[state] = {}
                for action in parent1.q_table[state]:
                    # Inherit the better learned action values (with some noise)
                    if random.random() < 0.5:
                        child.q_table[state][action] = parent1.q_table[state][action]
                    else:
                        child.q_table[state][action] = parent2.q_table[state][action]
            elif state in parent1.q_table:
                child.q_table[state] = parent1.q_table[state].copy()
            else:
                child.q_table[state] = parent2.q_table[state].copy()
        
        # Inherit neural network learning method
        child.use_neural_network = random.choice([parent1.use_neural_network, parent2.use_neural_network])
        
        return child
    
    def mutate(self, mutation_rate=0.1):
        """Apply random mutations to genome"""
        if random.random() < mutation_rate:
            self.metabolism += random.uniform(-0.2, 0.2)
            self.metabolism = max(0.1, min(2.0, self.metabolism))
            
        if random.random() < mutation_rate:
            self.stamina += random.uniform(-0.2, 0.2)
            self.stamina = max(0.1, min(2.0, self.stamina))
            
        if random.random() < mutation_rate:
            self.learning_capacity += random.uniform(-0.1, 0.1)
            self.learning_capacity = max(0.05, min(1.0, self.learning_capacity))
            
        if random.random() < mutation_rate:
            self.attraction_profile += random.uniform(-0.3, 0.3)
            self.attraction_profile = max(-1.0, min(1.0, self.attraction_profile))
            
        if random.random() < mutation_rate:
            self.sexual_preference += random.uniform(-0.2, 0.2)
            self.sexual_preference = max(0.0, min(1.0, self.sexual_preference))
            
        # Occasionally mutate a random Q-value to encourage exploration
        if random.random() < mutation_rate and self.q_table:
            state = random.choice(list(self.q_table.keys()))
            action = random.choice(list(self.q_table[state].keys()))
            self.q_table[state][action] += random.uniform(-0.5, 0.5)
        
        # Occasionally flip this trait during mutation
        if random.random() < mutation_rate:
            self.use_neural_network = not self.use_neural_network