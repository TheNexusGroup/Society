# Q learning is used to handle the reinforcement learning aspect of the simulation
from typing import Dict, List, Tuple, Optional
import random

class QLearningSystem:
    def __init__(self, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.1):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
    
    def initialize_q_table(self):
        """Initialize an empty Q-table with default values"""
        q_table = {}
        # States: energy_money_mood
        for energy in ['low', 'medium', 'high']:
            for money in ['low', 'medium', 'high']:
                for mood in ['negative', 'neutral', 'positive']:
                    state = f"{energy}_{money}_{mood}"
                    q_table[state] = {
                        'eat': 0.0,
                        'work': 0.0,
                        'rest': 0.0,
                        'mate': 0.0,
                        'search': 0.0,
                        'plant-food': 0.0,
                        'harvest-food': 0.0,
                        'gift-food': 0.0,
                        'gift-money': 0.0,
                        'invest': 0.0,
                        'buy-food': 0.0,
                        'sell-food': 0.0,
                        'trade-food-for-money': 0.0,
                        'trade-money-for-food': 0.0
                    }
        return q_table
    
    def select_action(self, q_table, state, exploration_rate=None):
        """Select an action using epsilon-greedy policy"""
        if exploration_rate is None:
            exploration_rate = self.exploration_rate
            
        if state not in q_table:
            q_table[state] = {
                'eat': 0.0, 'work': 0.0, 'rest': 0.0, 'mate': 0.0, 'search': 0.0,
                'plant-food': 0.0, 'harvest-food': 0.0, 'gift-food': 0.0, 'gift-money': 0.0,
                'invest': 0.0, 'buy-food': 0.0, 'sell-food': 0.0,
                'trade-food-for-money': 0.0, 'trade-money-for-food': 0.0
            }
            
        if random.random() < exploration_rate:
            return random.choice(list(q_table[state].keys()))
        else:
            return max(q_table[state], key=q_table[state].get)
    
    def update_q_table(self, q_table, state, action, reward, next_state, learning_rate=None):
        """Update Q-values using Q-learning algorithm"""
        if learning_rate is None:
            learning_rate = self.learning_rate
            
        if state not in q_table:
            q_table[state] = {
                'eat': 0.0, 'work': 0.0, 'rest': 0.0, 'mate': 0.0, 'search': 0.0,
                'plant-food': 0.0, 'harvest-food': 0.0, 'gift-food': 0.0, 'gift-money': 0.0,
                'invest': 0.0, 'buy-food': 0.0, 'sell-food': 0.0,
                'trade-food-for-money': 0.0, 'trade-money-for-food': 0.0
            }
            
        if next_state not in q_table:
            q_table[next_state] = {
                'eat': 0.0, 'work': 0.0, 'rest': 0.0, 'mate': 0.0, 'search': 0.0,
                'plant-food': 0.0, 'harvest-food': 0.0, 'gift-food': 0.0, 'gift-money': 0.0,
                'invest': 0.0, 'buy-food': 0.0, 'sell-food': 0.0,
                'trade-food-for-money': 0.0, 'trade-money-for-food': 0.0
            }
            
        # Q-learning update formula
        current_q = q_table[state][action]
        max_next_q = max(q_table[next_state].values())
        new_q = current_q + learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        q_table[state][action] = new_q
        
        return q_table