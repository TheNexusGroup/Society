"""
Evolution and Learning Visualization System
Tracks agent learning progress, genetic evolution, and skill development
"""

import numpy as np
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass
import sqlite3
from pathlib import Path

@dataclass
class AgentSnapshot:
    """Snapshot of an agent at a specific time"""
    agent_id: int
    iteration: int
    timestamp: float
    
    # Basic stats
    age: int
    energy: float
    money: float
    food: float
    generation: int
    
    # Learning metrics
    q_learning_progress: float  # Average Q-values
    neural_network_weights: np.ndarray  # Flattened weights
    decision_accuracy: float  # % of good decisions
    exploration_rate: float
    
    # Behavioral metrics
    primary_behavior: str
    behavior_distribution: Dict[str, float]
    social_connections: int
    trust_level: float
    
    # Genetic information
    genome_traits: Dict[str, float]
    fitness_score: float
    
    # Performance metrics
    wealth_accumulated: float
    food_consumed: float
    offspring_count: int
    survival_time: float

@dataclass  
class PopulationMetrics:
    """Population-level evolution metrics"""
    iteration: int
    timestamp: float
    
    # Population stats
    total_population: int
    alive_population: int
    avg_age: float
    avg_generation: float
    
    # Learning evolution
    avg_q_learning_progress: float
    avg_decision_accuracy: float
    learning_diversity: float  # Variety in learning strategies
    
    # Genetic evolution
    genetic_diversity: float
    avg_fitness: float
    trait_evolution: Dict[str, float]  # Average trait values
    
    # Economic evolution
    wealth_distribution: Dict[str, float]  # Gini, variance, etc.
    economic_complexity: float
    trade_frequency: float
    
    # Social evolution
    social_network_density: float
    cooperation_level: float
    trust_evolution: float

class EvolutionTracker:
    """Tracks learning and evolution across the simulation"""
    
    def __init__(self, db_path: str = "data/evolution.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # In-memory tracking
        self.agent_histories: Dict[int, List[AgentSnapshot]] = defaultdict(list)
        self.population_history: List[PopulationMetrics] = []
        self.generation_lineages: Dict[int, List[int]] = defaultdict(list)  # generation -> agent_ids
        
        # Real-time metrics
        self.current_metrics = {}
        self.learning_trajectories: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Analysis caches
        self.skill_evolution_cache = {}
        self.genetic_trends_cache = {}
        
        # Initialize database
        self._init_database()
        
        # Tracking configuration
        self.snapshot_interval = 100  # Take snapshot every N iterations
        self.max_agent_history = 1000  # Keep last N snapshots per agent
        self.analysis_window = 500  # Analyze trends over N iterations
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        with sqlite3.connect(self.db_path) as conn:
            # Agent snapshots table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    iteration INTEGER,
                    timestamp REAL,
                    age INTEGER,
                    energy REAL,
                    money REAL,
                    food REAL,
                    generation INTEGER,
                    q_learning_progress REAL,
                    neural_weights BLOB,
                    decision_accuracy REAL,
                    exploration_rate REAL,
                    primary_behavior TEXT,
                    behavior_data TEXT,
                    social_connections INTEGER,
                    trust_level REAL,
                    genome_data TEXT,
                    fitness_score REAL,
                    wealth_accumulated REAL,
                    food_consumed REAL,
                    offspring_count INTEGER,
                    survival_time REAL
                )
            ''')
            
            # Population metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS population_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iteration INTEGER,
                    timestamp REAL,
                    total_population INTEGER,
                    alive_population INTEGER,
                    avg_age REAL,
                    avg_generation REAL,
                    avg_q_learning_progress REAL,
                    avg_decision_accuracy REAL,
                    learning_diversity REAL,
                    genetic_diversity REAL,
                    avg_fitness REAL,
                    trait_evolution TEXT,
                    wealth_distribution TEXT,
                    economic_complexity REAL,
                    trade_frequency REAL,
                    social_network_density REAL,
                    cooperation_level REAL,
                    trust_evolution REAL
                )
            ''')
            
            # Learning events table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS learning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    iteration INTEGER,
                    timestamp REAL,
                    event_type TEXT,
                    old_value REAL,
                    new_value REAL,
                    context TEXT
                )
            ''')
    
    def take_agent_snapshot(self, world, entity_id: int, iteration: int) -> Optional[AgentSnapshot]:
        """Take a snapshot of a specific agent"""
        # Get agent components
        behavior = world.ecs.get_component(entity_id, "behavior")
        wallet = world.ecs.get_component(entity_id, "wallet")
        social = world.ecs.get_component(entity_id, "social")
        tag = world.ecs.get_component(entity_id, "tag")
        
        if not (behavior and wallet and tag):
            return None
        
        # Extract brain data
        brain_data = behavior.properties.get("brain")
        if not brain_data:
            return None
        
        # Calculate learning metrics
        q_progress = self._calculate_q_learning_progress(brain_data)
        decision_accuracy = self._calculate_decision_accuracy(brain_data, entity_id)
        
        # Neural network weights (flattened)
        nn_weights = np.array([])
        if hasattr(brain_data, 'neural_network') and brain_data.neural_network:
            weights = [
                brain_data.neural_network.weights_input_hidden.flatten(),
                brain_data.neural_network.weights_hidden_output.flatten(),
                brain_data.neural_network.bias_hidden.flatten(),
                brain_data.neural_network.bias_output.flatten()
            ]
            nn_weights = np.concatenate(weights)
        
        # Social metrics
        social_connections = len(social.relationships) if social else 0
        trust_level = self._calculate_average_trust(social) if social else 0.0
        
        # Behavioral analysis
        behavior_dist = self._analyze_behavior_distribution(entity_id)
        
        # Genetic data (if available)
        genome_traits = {}
        fitness_score = 0.0
        generation = 0
        
        if hasattr(behavior.properties, 'genome'):
            genome = behavior.properties['genome']
            genome_traits = {
                'metabolism': genome.metabolism,
                'stamina': genome.stamina,
                'learning_capacity': genome.learning_capacity
            }
            generation = getattr(genome, 'generation', 0)
            fitness_score = self._calculate_fitness_score(entity_id, world)
        
        snapshot = AgentSnapshot(
            agent_id=entity_id,
            iteration=iteration,
            timestamp=time.time(),
            age=behavior.properties.get('age', 0),
            energy=wallet.energy,
            money=wallet.money,
            food=wallet.food,
            generation=generation,
            q_learning_progress=q_progress,
            neural_network_weights=nn_weights,
            decision_accuracy=decision_accuracy,
            exploration_rate=getattr(brain_data, 'exploration_rate', 0.0),
            primary_behavior=behavior.state,
            behavior_distribution=behavior_dist,
            social_connections=social_connections,
            trust_level=trust_level,
            genome_traits=genome_traits,
            fitness_score=fitness_score,
            wealth_accumulated=wallet.money + (wallet.food * 10),  # Wealth proxy
            food_consumed=behavior.properties.get('food_consumed', 0),
            offspring_count=behavior.properties.get('offspring_count', 0),
            survival_time=behavior.properties.get('survival_time', 0)
        )
        
        # Store in memory
        self.agent_histories[entity_id].append(snapshot)
        
        # Limit history size
        if len(self.agent_histories[entity_id]) > self.max_agent_history:
            self.agent_histories[entity_id].pop(0)
        
        # Update learning trajectory
        self.learning_trajectories[entity_id].append({
            'iteration': iteration,
            'q_progress': q_progress,
            'decision_accuracy': decision_accuracy,
            'fitness': fitness_score
        })
        
        return snapshot
    
    def take_population_snapshot(self, world, iteration: int) -> PopulationMetrics:
        """Take a snapshot of the entire population"""
        agents = world.ecs.get_entities_with_components(["behavior", "wallet", "tag"])
        
        if not agents:
            return PopulationMetrics(
                iteration=iteration,
                timestamp=time.time(),
                total_population=0,
                alive_population=0,
                avg_age=0,
                avg_generation=0,
                avg_q_learning_progress=0,
                avg_decision_accuracy=0,
                learning_diversity=0,
                genetic_diversity=0,
                avg_fitness=0,
                trait_evolution={},
                wealth_distribution={},
                economic_complexity=0,
                trade_frequency=0,
                social_network_density=0,
                cooperation_level=0,
                trust_evolution=0
            )
        
        # Take snapshots of all agents
        agent_snapshots = []
        for agent_id in agents:
            snapshot = self.take_agent_snapshot(world, agent_id, iteration)
            if snapshot:
                agent_snapshots.append(snapshot)
        
        # Calculate population metrics
        alive_agents = [s for s in agent_snapshots if s.primary_behavior != "dead"]
        
        # Basic stats
        total_pop = len(agent_snapshots)
        alive_pop = len(alive_agents)
        avg_age = np.mean([s.age for s in alive_agents]) if alive_agents else 0
        avg_generation = np.mean([s.generation for s in alive_agents]) if alive_agents else 0
        
        # Learning metrics
        avg_q_progress = np.mean([s.q_learning_progress for s in alive_agents]) if alive_agents else 0
        avg_decision_accuracy = np.mean([s.decision_accuracy for s in alive_agents]) if alive_agents else 0
        learning_diversity = self._calculate_learning_diversity(alive_agents)
        
        # Genetic metrics
        genetic_diversity = self._calculate_genetic_diversity(alive_agents)
        avg_fitness = np.mean([s.fitness_score for s in alive_agents]) if alive_agents else 0
        trait_evolution = self._calculate_trait_evolution(alive_agents)
        
        # Economic metrics
        wealth_distribution = self._calculate_wealth_distribution(alive_agents)
        economic_complexity = self._calculate_economic_complexity(alive_agents)
        trade_frequency = self._calculate_trade_frequency(world, agents)
        
        # Social metrics
        social_network_density = self._calculate_social_density(alive_agents)
        cooperation_level = self._calculate_cooperation_level(alive_agents)
        trust_evolution = np.mean([s.trust_level for s in alive_agents]) if alive_agents else 0
        
        metrics = PopulationMetrics(
            iteration=iteration,
            timestamp=time.time(),
            total_population=total_pop,
            alive_population=alive_pop,
            avg_age=avg_age,
            avg_generation=avg_generation,
            avg_q_learning_progress=avg_q_progress,
            avg_decision_accuracy=avg_decision_accuracy,
            learning_diversity=learning_diversity,
            genetic_diversity=genetic_diversity,
            avg_fitness=avg_fitness,
            trait_evolution=trait_evolution,
            wealth_distribution=wealth_distribution,
            economic_complexity=economic_complexity,
            trade_frequency=trade_frequency,
            social_network_density=social_network_density,
            cooperation_level=cooperation_level,
            trust_evolution=trust_evolution
        )
        
        # Store in memory
        self.population_history.append(metrics)
        
        # Update generation lineages
        for snapshot in alive_agents:
            self.generation_lineages[snapshot.generation].append(snapshot.agent_id)
        
        return metrics
    
    def get_learning_evolution(self, agent_id: Optional[int] = None, window: int = None) -> Dict:
        """Get learning evolution data for visualization"""
        window = window or self.analysis_window
        
        if agent_id:
            # Individual agent learning curve
            history = self.agent_histories.get(agent_id, [])
            recent_history = history[-window:] if len(history) > window else history
            
            return {
                'agent_id': agent_id,
                'iterations': [s.iteration for s in recent_history],
                'q_learning_progress': [s.q_learning_progress for s in recent_history],
                'decision_accuracy': [s.decision_accuracy for s in recent_history],
                'fitness_score': [s.fitness_score for s in recent_history],
                'exploration_rate': [s.exploration_rate for s in recent_history]
            }
        else:
            # Population learning trends
            recent_pop = self.population_history[-window:] if len(self.population_history) > window else self.population_history
            
            return {
                'population_wide': True,
                'iterations': [m.iteration for m in recent_pop],
                'avg_q_learning': [m.avg_q_learning_progress for m in recent_pop],
                'avg_decision_accuracy': [m.avg_decision_accuracy for m in recent_pop],
                'learning_diversity': [m.learning_diversity for m in recent_pop],
                'avg_fitness': [m.avg_fitness for m in recent_pop]
            }
    
    def get_genetic_evolution(self, trait: Optional[str] = None, window: int = None) -> Dict:
        """Get genetic evolution data for visualization"""
        window = window or self.analysis_window
        recent_pop = self.population_history[-window:] if len(self.population_history) > window else self.population_history
        
        if trait and recent_pop:
            # Specific trait evolution
            trait_values = []
            iterations = []
            
            for metrics in recent_pop:
                if trait in metrics.trait_evolution:
                    trait_values.append(metrics.trait_evolution[trait])
                    iterations.append(metrics.iteration)
            
            return {
                'trait': trait,
                'iterations': iterations,
                'values': trait_values,
                'trend': self._calculate_trend(trait_values) if trait_values else 0
            }
        else:
            # All traits evolution
            all_traits = {}
            iterations = [m.iteration for m in recent_pop]
            
            if recent_pop:
                for trait_name in recent_pop[0].trait_evolution.keys():
                    values = [m.trait_evolution.get(trait_name, 0) for m in recent_pop]
                    all_traits[trait_name] = {
                        'values': values,
                        'trend': self._calculate_trend(values)
                    }
            
            return {
                'all_traits': True,
                'iterations': iterations,
                'traits': all_traits,
                'genetic_diversity': [m.genetic_diversity for m in recent_pop]
            }
    
    def get_skill_development(self, skill_type: str = "all", window: int = None) -> Dict:
        """Get skill development data across population"""
        window = window or self.analysis_window
        
        skill_data = {
            'economic': [],
            'social': [], 
            'survival': [],
            'learning': []
        }
        
        iterations = []
        
        for metrics in self.population_history[-window:]:
            iterations.append(metrics.iteration)
            
            # Economic skills (wealth accumulation, trade)
            skill_data['economic'].append({
                'wealth_complexity': metrics.economic_complexity,
                'trade_frequency': metrics.trade_frequency,
                'wealth_inequality': metrics.wealth_distribution.get('gini', 0)
            })
            
            # Social skills (cooperation, trust)
            skill_data['social'].append({
                'network_density': metrics.social_network_density,
                'cooperation_level': metrics.cooperation_level,
                'trust_level': metrics.trust_evolution
            })
            
            # Survival skills (fitness, longevity)
            skill_data['survival'].append({
                'avg_fitness': metrics.avg_fitness,
                'avg_age': metrics.avg_age,
                'population_stability': metrics.alive_population / max(metrics.total_population, 1)
            })
            
            # Learning skills (adaptation, decision making)
            skill_data['learning'].append({
                'decision_accuracy': metrics.avg_decision_accuracy,
                'learning_diversity': metrics.learning_diversity,
                'adaptation_rate': metrics.avg_q_learning_progress
            })
        
        if skill_type == "all":
            return {
                'iterations': iterations,
                'skills': skill_data
            }
        else:
            return {
                'iterations': iterations,
                'skill_type': skill_type,
                'data': skill_data.get(skill_type, [])
            }
    
    def get_lineage_analysis(self, generation: Optional[int] = None) -> Dict:
        """Analyze genetic lineages and family trees"""
        if generation is not None:
            # Specific generation analysis
            agents_in_gen = self.generation_lineages.get(generation, [])
            
            lineage_data = []
            for agent_id in agents_in_gen:
                history = self.agent_histories.get(agent_id, [])
                if history:
                    latest = history[-1]
                    lineage_data.append({
                        'agent_id': agent_id,
                        'fitness': latest.fitness_score,
                        'traits': latest.genome_traits,
                        'offspring': latest.offspring_count,
                        'survival_time': latest.survival_time
                    })
            
            return {
                'generation': generation,
                'population_size': len(agents_in_gen),
                'agents': lineage_data,
                'avg_fitness': np.mean([a['fitness'] for a in lineage_data]) if lineage_data else 0
            }
        else:
            # Cross-generational analysis
            generation_stats = {}
            
            for gen, agent_ids in self.generation_lineages.items():
                fitness_scores = []
                for agent_id in agent_ids:
                    history = self.agent_histories.get(agent_id, [])
                    if history:
                        fitness_scores.append(history[-1].fitness_score)
                
                generation_stats[gen] = {
                    'population': len(agent_ids),
                    'avg_fitness': np.mean(fitness_scores) if fitness_scores else 0,
                    'max_fitness': np.max(fitness_scores) if fitness_scores else 0
                }
            
            return {
                'cross_generational': True,
                'generations': generation_stats,
                'total_generations': len(generation_stats)
            }
    
    def export_evolution_data(self, format_type: str = "json") -> str:
        """Export evolution data for external analysis"""
        data = {
            'population_history': [
                {
                    'iteration': m.iteration,
                    'timestamp': m.timestamp,
                    'population': {
                        'total': m.total_population,
                        'alive': m.alive_population,
                        'avg_age': m.avg_age,
                        'avg_generation': m.avg_generation
                    },
                    'learning': {
                        'avg_q_progress': m.avg_q_learning_progress,
                        'avg_accuracy': m.avg_decision_accuracy,
                        'diversity': m.learning_diversity
                    },
                    'genetics': {
                        'diversity': m.genetic_diversity,
                        'avg_fitness': m.avg_fitness,
                        'traits': m.trait_evolution
                    },
                    'economics': {
                        'distribution': m.wealth_distribution,
                        'complexity': m.economic_complexity,
                        'trade_freq': m.trade_frequency
                    },
                    'social': {
                        'network_density': m.social_network_density,
                        'cooperation': m.cooperation_level,
                        'trust': m.trust_evolution
                    }
                } for m in self.population_history
            ],
            'generation_lineages': dict(self.generation_lineages),
            'export_timestamp': time.time()
        }
        
        if format_type == "json":
            return json.dumps(data, indent=2)
        else:
            # Could add CSV, XML, etc.
            return json.dumps(data, indent=2)
    
    # Helper methods for calculations
    def _calculate_q_learning_progress(self, brain) -> float:
        """Calculate Q-learning progress metric"""
        if not hasattr(brain, 'q_table') or not brain.q_table:
            return 0.0
        
        # Average absolute Q-values as progress indicator
        q_values = []
        for state_actions in brain.q_table.values():
            if isinstance(state_actions, dict):
                q_values.extend(state_actions.values())
        
        return np.mean(np.abs(q_values)) if q_values else 0.0
    
    def _calculate_decision_accuracy(self, brain, agent_id: int) -> float:
        """Calculate decision-making accuracy"""
        # This would need access to historical decision outcomes
        # For now, return a proxy based on Q-values and exploration
        if hasattr(brain, 'exploration_rate'):
            return 1.0 - brain.exploration_rate  # Higher accuracy = less exploration needed
        return 0.5  # Default neutral accuracy
    
    def _calculate_average_trust(self, social) -> float:
        """Calculate average trust level"""
        if not social or not social.relationships:
            return 0.0
        
        trust_values = [rel.trust for rel in social.relationships.values()]
        return np.mean(trust_values) if trust_values else 0.0
    
    def _analyze_behavior_distribution(self, agent_id: int) -> Dict[str, float]:
        """Analyze behavior distribution for an agent"""
        # This would track behavior over time
        # For now, return empty dict
        return {}
    
    def _calculate_fitness_score(self, agent_id: int, world) -> float:
        """Calculate agent fitness score"""
        wallet = world.ecs.get_component(agent_id, "wallet")
        behavior = world.ecs.get_component(agent_id, "behavior")
        
        if not (wallet and behavior):
            return 0.0
        
        # Fitness based on resources, age, offspring
        fitness = (
            wallet.money * 0.3 +
            wallet.food * 0.2 +
            wallet.energy * 0.2 +
            behavior.properties.get('age', 0) * 0.1 +
            behavior.properties.get('offspring_count', 0) * 0.2
        )
        
        return max(0.0, fitness)
    
    def _calculate_learning_diversity(self, agents: List[AgentSnapshot]) -> float:
        """Calculate diversity in learning strategies"""
        if not agents:
            return 0.0
        
        # Standard deviation of Q-learning progress as diversity measure
        q_progress = [a.q_learning_progress for a in agents]
        return np.std(q_progress) if len(q_progress) > 1 else 0.0
    
    def _calculate_genetic_diversity(self, agents: List[AgentSnapshot]) -> float:
        """Calculate genetic diversity"""
        if not agents:
            return 0.0
        
        # Calculate trait variance across population
        trait_variances = []
        
        # Get all trait names
        all_traits = set()
        for agent in agents:
            all_traits.update(agent.genome_traits.keys())
        
        for trait in all_traits:
            values = [agent.genome_traits.get(trait, 0) for agent in agents]
            trait_variances.append(np.var(values))
        
        return np.mean(trait_variances) if trait_variances else 0.0
    
    def _calculate_trait_evolution(self, agents: List[AgentSnapshot]) -> Dict[str, float]:
        """Calculate average trait values"""
        if not agents:
            return {}
        
        trait_sums = defaultdict(float)
        trait_counts = defaultdict(int)
        
        for agent in agents:
            for trait, value in agent.genome_traits.items():
                trait_sums[trait] += value
                trait_counts[trait] += 1
        
        return {
            trait: trait_sums[trait] / trait_counts[trait] 
            for trait in trait_sums.keys()
        }
    
    def _calculate_wealth_distribution(self, agents: List[AgentSnapshot]) -> Dict[str, float]:
        """Calculate wealth distribution metrics"""
        if not agents:
            return {}
        
        wealth_values = [a.wealth_accumulated for a in agents]
        
        return {
            'mean': np.mean(wealth_values),
            'median': np.median(wealth_values),
            'std': np.std(wealth_values),
            'gini': self._calculate_gini_coefficient(wealth_values),
            'range': np.max(wealth_values) - np.min(wealth_values)
        }
    
    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient for inequality"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)
        
        return (n + 1 - 2 * sum((n + 1 - i) * y for i, y in enumerate(cumsum))) / (n * sum(values))
    
    def _calculate_economic_complexity(self, agents: List[AgentSnapshot]) -> float:
        """Calculate economic complexity metric"""
        # Proxy based on wealth distribution variance
        wealth_values = [a.wealth_accumulated for a in agents]
        return np.std(wealth_values) / (np.mean(wealth_values) + 1e-6) if wealth_values else 0.0
    
    def _calculate_trade_frequency(self, world, agents: List[int]) -> float:
        """Calculate trade frequency"""
        # This would need access to trade history
        # For now, return a proxy based on agent interactions
        return len(agents) * 0.1  # Placeholder
    
    def _calculate_social_density(self, agents: List[AgentSnapshot]) -> float:
        """Calculate social network density"""
        if not agents:
            return 0.0
        
        total_connections = sum(a.social_connections for a in agents)
        max_possible = len(agents) * (len(agents) - 1)  # Fully connected network
        
        return total_connections / max_possible if max_possible > 0 else 0.0
    
    def _calculate_cooperation_level(self, agents: List[AgentSnapshot]) -> float:
        """Calculate cooperation level"""
        if not agents:
            return 0.0
        
        # Proxy based on trust levels and social connections
        cooperation_scores = []
        for agent in agents:
            score = agent.trust_level * (agent.social_connections / len(agents))
            cooperation_scores.append(score)
        
        return np.mean(cooperation_scores)
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (slope) of values"""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope